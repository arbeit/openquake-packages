# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""Common code for the hazard calculators."""

import os
import random
import re
import StringIO

import kombu
import nhlib
import nhlib.site
import numpy

from django.db import transaction, connections
from django.db.models import Sum

from nhlib import geo as nhlib_geo
from nrml import parsers as nrml_parsers
from shapely import geometry

from openquake import engine2
from openquake import java
from openquake import kvs
from openquake import writer
from openquake.export import core as export_core
from openquake.export import hazard as hazard_export
from openquake.calculators import base
from openquake.db import models
from openquake.input import logictree
from openquake.input import source
from openquake.java import list_to_jdouble_array
from openquake.job import params as job_params
from openquake.job.validation import MAX_SINT_32
from openquake.job.validation import MIN_SINT_32
from openquake import logs
from openquake.utils import config
from openquake.utils import stats


QUANTILE_PARAM_NAME = "QUANTILE_LEVELS"
POES_PARAM_NAME = "POES"

#: Default Spectral Acceleration damping. At the moment, this is not
#: configurable.
DEFAULT_SA_DAMPING = 5.0

# NOTE: this refers to how the values are stored in KVS. In the config
# file, values are stored untransformed (i.e., the list of IMLs is
# not stored as logarithms).
IML_SCALING = {
    'PGA': numpy.log,
    'MMI': lambda iml: iml,
    'PGV': numpy.log,
    'PGD': numpy.log,
    'SA': numpy.log,
    'IA': numpy.log,
    'RSD': numpy.log,
}

# Routing key format string for communication between tasks and the control
# node.
ROUTING_KEY_FMT = 'oq.job.%(job_id)s.htasks'


def get_iml_list(imls, intensity_measure_type):
    """Build the appropriate Arbitrary Discretized Func from the IMLs,
    based on the IMT"""

    return list_to_jdouble_array(
        [IML_SCALING[intensity_measure_type](x) for x in imls])


@java.unpack_exception
def generate_erf(job_id, cache):
    """ Generate the Earthquake Rupture Forecast from the source model data
    stored in the KVS.

    :param int job_id: id of the job
    :param cache: jpype instance of `org.gem.engine.hazard.redis.Cache`
    :returns: jpype instance of
        `org.opensha.sha.earthquake.rupForecastImpl.GEM1.GEM1ERF`
    """
    src_key = kvs.tokens.source_model_key(job_id)
    job_key = kvs.tokens.generate_job_key(job_id)

    sources = java.jclass("JsonSerializer").getSourceListFromCache(
        cache, src_key)

    erf = java.jclass("GEM1ERF")(sources)

    calc = java.jclass("LogicTreeProcessor")(cache, job_key)
    calc.setGEM1ERFParams(erf)

    return erf


def generate_gmpe_map(job_id, cache):
    """ Generate the GMPE map from the GMPE data stored in the KVS.

    :param int job_id: id of the job
    :param cache: jpype instance of `org.gem.engine.hazard.redis.Cache`
    :returns: jpype instace of
        `HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>`
    """
    gmpe_key = kvs.tokens.gmpe_key(job_id)

    gmpe_map = java.jclass(
        "JsonSerializer").getGmpeMapFromCache(cache, gmpe_key)
    return gmpe_map


def store_source_model(job_id, seed, params, calc):
    """Generate source model from the source model logic tree and store it in
    the KVS.

    :param int job_id: numeric ID of the job
    :param int seed: seed for random logic tree sampling
    :param dict params: the config parameters as (dict)
    :param calc: logic tree processor
    :type calc: :class:`openquake.input.logictree.LogicTreeProcessor` instance
    """
    logs.LOG.info("Storing source model from job config")
    key = kvs.tokens.source_model_key(job_id)
    mfd_bin_width = float(params.get('WIDTH_OF_MFD_BIN'))
    calc.sample_and_save_source_model_logictree(
        kvs.get_client(), key, seed, mfd_bin_width)


def store_gmpe_map(job_id, seed, calc):
    """Generate a hash map of GMPEs (keyed by Tectonic Region Type) and store
    it in the KVS.

    :param int job_id: numeric ID of the job
    :param int seed: seed for random logic tree sampling
    :param calc: logic tree processor
    :type calc: :class:`openquake.input.logictree.LogicTreeProcessor` instance
    """
    logs.LOG.info("Storing GMPE map from job config")
    key = kvs.tokens.gmpe_key(job_id)
    calc.sample_and_save_gmpe_logictree(kvs.get_client(), key, seed)


def set_gmpe_params(gmpe_map, params):
    """Push parameters from the config file into the GMPE objects.

    :param gmpe_map: jpype instance of
        `HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>`
    :param dict params: job config params
    """
    jpype = java.jvm()

    jd_float = lambda x: jpype.JDouble(float(x))

    component = params.get('COMPONENT')
    imt = params.get('INTENSITY_MEASURE_TYPE')
    # PERIOD is not used in UHS calculations.
    period = (jd_float(params.get('PERIOD'))
              if params.get('PERIOD') is not None else None)
    damping = jd_float(params.get('DAMPING'))
    gmpe_trunc_type = params.get('GMPE_TRUNCATION_TYPE')
    trunc_level = jd_float(params.get('TRUNCATION_LEVEL'))
    stddev_type = params.get('STANDARD_DEVIATION_TYPE')

    j_set_gmpe_params = java.jclass("GmpeLogicTreeData").setGmpeParams
    for tect_region in gmpe_map.keySet():
        gmpe = gmpe_map.get(tect_region)
        # There are two overloads for this method; one with 'period'...
        if period is not None:
            j_set_gmpe_params(
                component, imt, period, damping,
                gmpe_trunc_type, trunc_level, stddev_type,
                jpype.JObject(gmpe, java.jclass("AttenuationRelationship")))
        # ... and one without.
        else:
            j_set_gmpe_params(
                component, imt, damping,
                gmpe_trunc_type, trunc_level, stddev_type,
                jpype.JObject(gmpe, java.jclass("AttenuationRelationship")))
        gmpe_map.put(tect_region, gmpe)


@transaction.commit_on_success(using='job_init')
def store_site_model(input_mdl, site_model_source):
    """Invoke site model parser and save the site-specified parameter data to
    the database.

    :param input_mdl:
        The `uiapi.input` record which the new `hzrdi.site_model` records
        reference. This `input` record acts as a container for the site model
        data.
    :param site_model_source:
        Filename or file-like object containing the site model XML data.
    :returns:
        `list` of :class:`openquake.db.models.SiteModel` objects. These
        represent to newly-inserted `hzrdi.site_model` records.
    """
    parser = nrml_parsers.SiteModelParser(site_model_source)

    sm_data = []

    inserter = writer.BulkInserter(models.SiteModel)

    for node in parser.parse():
        sm = dict()
        # sm = models.SiteModel()
        sm['vs30'] = node.vs30
        sm['vs30_type'] = node.vs30_type
        sm['z1pt0'] = node.z1pt0
        sm['z2pt5'] = node.z2pt5
        sm['location'] = node.wkt
        sm['input_id'] = input_mdl.id
        # sm.save()
        # sm_data.append(sm)
        inserter.add_entry(**sm)

    inserter.flush()

    return sm_data


def validate_site_model(sm_nodes, mesh):
    """Given the geometry for a site model and the geometry of interest for the
    calculation (``mesh``, make sure the geometry of interest lies completely
    inside of the convex hull formed by the site model locations.

    If a point of interest lies directly on top of a vertex or edge of the site
    model area (a polygon), it is considered "inside"

    :param sm_nodes:
        Sequence of :class:`~openquake.db.models.SiteModel` objects.
    :param mesh:
        A :class:`nhlib.geo.mesh.Mesh` which represents the calculation points
        of interest.

    :raises:
        :exc:`RuntimeError` if the area of interest (given as a mesh) is not
        entirely contained by the site model.
    """
    sm_mp = geometry.MultiPoint(
        [(n.location.x, n.location.y) for n in sm_nodes]
    )
    sm_poly = nhlib_geo.Polygon(
        [nhlib_geo.Point(*x) for x in sm_mp.convex_hull.exterior.coords]
    )

    # "Intersects" is the correct operation (not "contains"), since we're just
    # checking a collection of points (mesh). "Contains" would tell us if the
    # points are inside the polygon, but would return `False` if a point was
    # directly on top of a polygon edge or vertex. We want these points to be
    # included.
    intersects = sm_poly.intersects(mesh)

    if not intersects.all():
        raise RuntimeError(
            ['Sites of interest are outside of the site model coverage area.'
             ' This configuration is invalid.']
        )


def get_site_model(hc_id):
    """Get the site model :class:`~openquake.db.models.Input` record for the
    given job id.

    :param int hc_id:
        The id of a :class:`~openquake.db.models.HazardCalculation`.

    :returns:
        The site model :class:`~openquake.db.models.Input` record for this job.
    :raises:
        :exc:`RuntimeError` if the job has more than 1 site model.
    """
    site_model = models.inputs4hcalc(hc_id, input_type='site_model')

    if len(site_model) == 0:
        return None
    elif len(site_model) > 1:
        # Multiple site models for 1 job are not allowed.
        raise RuntimeError("Only 1 site model per job is allowed, found %s."
                           % len(site_model))

    # There's only one site model.
    return site_model[0]


def get_closest_site_model_data(input_model, point):
    """Get the closest available site model data from the database for a given
    site model :class:`~openquake.db.models.Input` and
    :class:`nhlib.geo.point.Point`.

    :param input_model:
        :class:`openquake.db.models.Input` with `input_type` of 'site_model'.
    :param site:
        :class:`nhlib.geo.point.Point` instance.

    :returns:
        The closest :class:`openquake.db.models.SiteModel` for the given
        ``input_model`` and ``point`` of interest.

        This function uses the PostGIS `ST_Distance_Sphere
        <http://postgis.refractions.net/docs/ST_Distance_Sphere.html>`_
        function to calculate distance.

        If there is no site model data, return `None`.
    """
    query = """
    SELECT
        hzrdi.site_model.*,
        min(ST_Distance_Sphere(location, %s))
            AS min_distance
    FROM hzrdi.site_model
    WHERE input_id = %s
    GROUP BY id
    ORDER BY min_distance
    LIMIT 1;"""

    raw_query_set = models.SiteModel.objects.raw(
        query, ['SRID=4326; %s' % point.wkt2d, input_model.id]
    )

    site_model_data = list(raw_query_set)

    assert len(site_model_data) <= 1, (
        "This query should return at most 1 record.")

    if len(site_model_data) == 1:
        return site_model_data[0]
    else:
        return None


def store_site_data(hc_id, site_model_inp, mesh):
    """
    Given a ``mesh`` of points (calculation points of interest) and a
    site model (``site_model_inp``), get the closest site model data
    for each points and store the mesh point location plus the site parameters
    as a single record in the `htemp.site_data` table.

    NOTE: This should only be necessary for calculations which specify a site
    model. Otherwise, the same 4 reference site parameters are used for all
    sites.

    :param int hc_id:
        ID of a :class:`~openquake.db.models.HazardCalculation`.
    :param site_model_inp:
        An :class:`~openquake.db.models.Input` with an
        `input_type`=='site_model'. This tells us which site model dataset to
        query.
    :param mesh:
        Calculation points of interest, as a :class:`nhlib.geo.mesh.Mesh`.
    :returns:
        The :class:`openquake.db.models.SiteData` object that was created to
        store computation points of interest with associated site parameters.
    """
    lons = []
    lats = []
    vs30s = []
    vs30_types = []
    z1pt0s = []
    z2pt5s = []

    for pt in mesh:
        smd = get_closest_site_model_data(site_model_inp, pt)

        lons.append(pt.longitude)
        lats.append(pt.latitude)

        vs30s.append(smd.vs30)
        vs30_types.append(smd.vs30_type)
        z1pt0s.append(smd.z1pt0)
        z2pt5s.append(smd.z2pt5)

    site_data = models.SiteData(hazard_calculation_id=hc_id)
    site_data.lons = numpy.array(lons)
    site_data.lats = numpy.array(lats)
    site_data.vs30s = numpy.array(vs30s)
    # We convert from strings to booleans here because this is what a nhlib
    # SiteCollection expects for the vs30 type. If we do the conversion here,
    # we only do it once and we can directly consume the data on the worker
    # side without having to convert inside each task.
    site_data.vs30_measured = numpy.array(vs30_types) == 'measured'
    site_data.z1pt0s = numpy.array(z1pt0s)
    site_data.z2pt5s = numpy.array(z2pt5s)
    site_data.save()

    return site_data


def set_java_site_parameters(jsite, sm_data):
    """Given a site model node and an OpenSHA `Site` object,
    set vs30, vs30, z2pt5, and z1pt0 parameters.

    :param jsite:
        A `org.opensha.commons.data.Site` jpype object.
    :param sm_data:
        :class:`openquake.db.models.SiteModel` instance.
    :returns:
        The ``jsite`` input object (so this function can be chained).
    """
    vs30_param = java.jclass("DoubleParameter")("Vs30")
    vs30_param.setValue(sm_data.vs30)

    vs30_type_param = java.jclass("StringParameter")("Vs30 Type")
    vs30_type_param.setValue(sm_data.vs30_type)

    z1pt0_param = java.jclass("DoubleParameter")("Depth 1.0 km/sec")
    z1pt0_param.setValue(sm_data.z1pt0)

    z2pt5_param = java.jclass("DoubleParameter")("Depth 2.5 km/sec")
    z2pt5_param.setValue(sm_data.z2pt5)

    jsite.addParameter(vs30_param)
    jsite.addParameter(vs30_type_param)
    jsite.addParameter(z1pt0_param)
    jsite.addParameter(z2pt5_param)

    return jsite


class BaseHazardCalculator(base.Calculator):
    """Contains common functionality for Hazard calculators"""

    def initialize(self):
        """Read the raw site model from the database and populate the
        `uiapi.site_model`.
        """
        site_model = get_site_model(self.job_ctxt.oq_job.id)

        if site_model is not None:
            # Explicit cast to `str` here because the XML parser doesn't like
            # unicode. (More specifically, lxml doesn't like unicode.)
            site_model_content = str(site_model.model_content.raw_content)
            store_site_model(site_model, StringIO.StringIO(site_model_content))

            site_model_data = models.SiteModel.objects.filter(input=site_model)

            validate_site_model(
                site_model_data, self.job_ctxt.sites_to_compute()
            )

    def pre_execute(self):
        basepath = self.job_ctxt.params.get('BASE_PATH')
        if not self.job_ctxt['CALCULATION_MODE'] in (
                'Scenario', 'Scenario Damage'):
            source_model_lt = self.job_ctxt.params.get(
                'SOURCE_MODEL_LOGIC_TREE_FILE_PATH')
            gmpe_lt = self.job_ctxt.params.get('GMPE_LOGIC_TREE_FILE_PATH')
            self.calc = logictree.LogicTreeProcessor(
                basepath, source_model_lt, gmpe_lt)

    def execute(self):
        """Calculation logic goes here; subclasses must implement this."""
        raise NotImplementedError()

    def store_source_model(self, seed):
        """Generates a source model from the source model logic tree."""
        if getattr(self, "calc", None) is None:
            self.pre_execute()
        store_source_model(self.job_ctxt.job_id, seed,
                           self.job_ctxt.params, self.calc)

    def store_gmpe_map(self, seed):
        """Generates a hash of tectonic regions and GMPEs, using the logic tree
        specified in the job config file."""
        if getattr(self, "calc", None) is None:
            self.pre_execute()
        store_gmpe_map(self.job_ctxt.job_id, seed, self.calc)

    def generate_erf(self):
        """Generate the Earthquake Rupture Forecast from the currently stored
        source model logic tree."""
        return generate_erf(self.job_ctxt.job_id, self.cache)

    def set_gmpe_params(self, gmpe_map):
        """Push parameters from configuration file into the GMPE objects"""
        set_gmpe_params(gmpe_map, self.job_ctxt.params)

    def generate_gmpe_map(self):
        """Generate the GMPE map from the stored GMPE logic tree."""
        gmpe_map = generate_gmpe_map(self.job_ctxt.job_id, self.cache)
        self.set_gmpe_params(gmpe_map)
        return gmpe_map

    def parameterize_sites(self, site_list):
        """Set vs30, vs30 type, z1pt0, z2pt5, and sadigh site type parameters
        on all input sites, returning a jpype `ArrayList` of OpenSHA `Site`
        objects.

        For vs30, vs30 type, z1pt0, and z2pt5:
        These params can be defined in general for the entire calculation.
        Alternatively, the calculation can define a `SITE_MODEL`, which supply
        site-specific parameters. This method handles both cases.

        NOTE: If a `SITE_MODEL` is used, it needs to be properly stored first.
        See :func:`~openquake.calculators.hazard.general.store_site_model`.

        :param site_list:
            `list` of :class:`~openquake.shapes.Site` objects.
        :returns:
            jpype `ArrayList` of `org.opensha.commons.data.Site` objects (with
            the above parameters set).
        """
        # make sure the JVM is started
        java.jvm()

        # the return value
        jsite_list = java.jclass("ArrayList")()

        job_profile = self.job_ctxt.oq_job_profile

        # The `sadigh site type` is the same in any case
        sadigh_param = java.jclass("StringParameter")("Sadigh Site Type")
        sadigh_param.setValue(
            job_params.REVERSE_ENUM_MAP[job_profile.sadigh_site_type]
        )

        site_model = get_site_model(self.job_ctxt.oq_job.id)

        if site_model is not None:
            # set site-specific parameters:
            for site in site_list:
                jsite = site.to_java()

                sm_data = get_closest_site_model_data(site_model, site)
                set_java_site_parameters(jsite, sm_data)
                # The sadigh site type param is not site specific, but we need
                # to set it anyway.
                jsite.addParameter(sadigh_param)

                jsite_list.add(jsite)
        else:
            # use the same parameters for all sites
            vs30_param = java.jclass("DoubleParameter")("Vs30")
            vs30_param.setValue(job_profile.reference_vs30_value)

            vs30_type_param = java.jclass("StringParameter")("Vs30 Type")
            vs30_type_param.setValue(job_profile.vs30_type)

            z1pt0_param = java.jclass("DoubleParameter")("Depth 1.0 km/sec")
            z1pt0_param.setValue(job_profile.depth_to_1pt_0km_per_sec)

            z2pt5_param = java.jclass("DoubleParameter")("Depth 2.5 km/sec")
            z2pt5_param.setValue(
                job_profile.reference_depth_to_2pt5km_per_sec_param
            )

            for site in site_list:
                jsite = site.to_java()

                jsite.addParameter(vs30_param)
                jsite.addParameter(vs30_type_param)
                jsite.addParameter(z1pt0_param)
                jsite.addParameter(z2pt5_param)
                jsite.addParameter(sadigh_param)

                jsite_list.add(jsite)

        return jsite_list


def exchange_and_conn_args():
    """
    Helper method to setup an exchange for task communication and the args
    needed to create a broker connection.
    """

    exchange = kombu.Exchange(
        config.get_section('hazard')['task_exchange'], type='direct')

    amqp_cfg = config.get_section('amqp')
    conn_args = {
        'hostname': amqp_cfg['host'],
        'userid': amqp_cfg['user'],
        'password': amqp_cfg['password'],
        'virtual_host': amqp_cfg['vhost'],
    }

    return exchange, conn_args


def gen_sources(src_ids, apply_uncertainties, rupture_mesh_spacing,
                width_of_mfd_bin, area_source_discretization):
    """
    Nhlib source objects generator for a given set of sources.

    Performs lazy loading, converting and processing of sources.

    :param src_ids:
        A list of IDs for :class:`openquake.db.models.ParsedSource` records.
    :param apply_uncertainties:
        A function to be called on each generated source. See
        :meth:`openquake.input.logictree.LogicTreeProcessor.\
parse_source_model_logictree_path`

    For information about the other parameters, see
    :func:`openquake.input.source.nrml_to_nhlib`.
    """
    for src_id in src_ids:
        parsed_source = models.ParsedSource.objects.get(id=src_id)

        nhlib_source = source.nrml_to_nhlib(
            parsed_source.nrml, rupture_mesh_spacing, width_of_mfd_bin,
            area_source_discretization)

        apply_uncertainties(nhlib_source)
        yield nhlib_source


def get_site_collection(hc):
    """
    Create a `SiteCollection`, which is needed by nhlib to perform various
    calculation tasks (such computing hazard curves and GMFs).

    :param hc:
        Instance of a :class:`~openquake.db.models.HazardCalculation`. We need
        this in order to get the points of interest for a calculation as well
        as load pre-computed site data or access reference site parameters.

    :returns:
        :class:`nhlib.site.SiteCollection` instance.
    """
    site_data = models.SiteData.objects.filter(hazard_calculation=hc.id)
    if len(site_data) > 0:
        site_data = site_data[0]
        sites = zip(site_data.lons, site_data.lats, site_data.vs30s,
                    site_data.vs30_measured, site_data.z1pt0s,
                    site_data.z2pt5s)
        sites = [nhlib.site.Site(
            nhlib.geo.Point(lon, lat), vs30, vs30m, z1pt0, z2pt5)
            for lon, lat, vs30, vs30m, z1pt0, z2pt5 in sites]
    else:
        # Use the calculation reference parameters to make a site collection.
        points = hc.points_to_compute()
        measured = hc.reference_vs30_type == 'measured'
        sites = [
            nhlib.site.Site(pt, hc.reference_vs30_value, measured,
                            hc.reference_depth_to_2pt5km_per_sec,
                            hc.reference_depth_to_1pt0km_per_sec)
            for pt in points]

    return nhlib.site.SiteCollection(sites)


def im_dict_to_nhlib(im_dict):
    """
    Given the dict of intensity measure types and levels, convert them to a
    dict with the same values, except create :mod:`mhlib.imt` objects for the
    new keys.

    :returns:
        A dict of intensity measure level lists, keyed by an IMT object. See
        :mod:`nhlib.imt` for more information.
    """
    # TODO: file a bug about  SA periods in nhlib imts.
    # Why are values of 0.0 not allowed? Technically SA(0.0) means PGA, but
    # there must be a reason why we can't do this.
    nhlib_im = {}

    for imt, imls in im_dict.items():
        nhlib_imt = imt_to_nhlib(imt)
        nhlib_im[nhlib_imt] = imls

    return nhlib_im


def imt_to_nhlib(imt):
    """Covert an IMT string to an nhlib object.

    :param str imt:
        Given the IMT string (defined in the job config file), convert it to
        equivlent nhlib object. See :mod:`nhlib.imt`.
    """
    if 'SA' in imt:
        match = re.match(r'^SA\(([^)]+?)\)$', imt)
        period = float(match.group(1))
        return nhlib.imt.SA(period, DEFAULT_SA_DAMPING)
    else:
        imt_class = getattr(nhlib.imt, imt)
        return imt_class()


def signal_task_complete(job_id, num_sources):
    """
    Send a signal back through a dedicated queue to the 'control node' to
    notify of task completion and the number of sources computed.

    Signalling back this metric is needed to tell the control node when it can
    conclude its `execute` phase.

    :param int job_id:
        ID of a currently running :class:`~openquake.db.models.OqJob`.
    :param int num_sources:
        Number of sources computed in the completed task.
    """
    # The job ID may be redundant (since it's in the routing key), but
    # we can put this here for a sanity check on the receiver side.
    # Maybe we can remove this
    msg = dict(job_id=job_id, num_sources=num_sources)

    exchange, conn_args = exchange_and_conn_args()

    routing_key = ROUTING_KEY_FMT % dict(job_id=job_id)

    with kombu.BrokerConnection(**conn_args) as conn:
        with conn.Producer(exchange=exchange,
                           routing_key=routing_key) as producer:
            producer.publish(msg)


class BaseHazardCalculatorNext(base.CalculatorNext):
    """
    Abstract base class for hazard calculators. Contains a bunch of common
    functionality, including initialization procedures and the core
    distribution/execution logic.
    """

    #: In subclasses, this would be a reference to the task function
    core_calc_task = None
    #: Generator function for creating the arguments for each task
    task_arg_gen = None

    def initialize_sources(self):
        """
        Parse and validation logic trees (source and gsim). Then get all
        sources referenced in the the source model logic tree, create
        :class:`~openquake.db.models.Input` records for all of them, parse
        then, and save the parsed sources to the `parsed_source` table
        (see :class:`openquake.db.models.ParsedSource`).
        """
        logs.log_progress("initializing sources", 2)
        hc = self.job.hazard_calculation

        [smlt] = models.inputs4hcalc(hc.id, input_type='lt_source')
        [gsimlt] = models.inputs4hcalc(hc.id, input_type='lt_gsim')
        source_paths = logictree.read_logic_trees(
            hc.base_path, smlt.path, gsimlt.path)

        src_inputs = []
        for src_path in source_paths:
            full_path = os.path.join(hc.base_path, src_path)

            # Get or reuse the 'source' Input:
            inp = engine2.get_input(
                full_path, 'source', hc.owner, hc.force_inputs)
            src_inputs.append(inp)

            # Associate the source input to the calculation:
            models.Input2hcalc.objects.get_or_create(
                input=inp, hazard_calculation=hc)

            # Associate the source input to the source model logic tree input:
            models.Src2ltsrc.objects.get_or_create(
                hzrd_src=inp, lt_src=smlt, filename=src_path)

        # Now parse the source models and store `pared_source` records:
        for src_inp in src_inputs:
            src_content = StringIO.StringIO(src_inp.model_content.raw_content)
            sm_parser = nrml_parsers.SourceModelParser(src_content)
            src_db_writer = source.SourceDBWriter(
                src_inp, sm_parser.parse(), hc.rupture_mesh_spacing,
                hc.width_of_mfd_bin, hc.area_source_discretization)
            src_db_writer.serialize()

    def initialize_site_model(self):
        """
        If a site model is specified in the calculation configuration. parse
        it and load it into the `hzrdi.site_model` table. This includes a
        validation step to ensure that the area covered by the site model
        completely envelops the calculation geometry. (If this requirement is
        not satisfied, an exception will be raised. See
        :func:`openquake.calculators.hazard.general.validate_site_model`.)

        Then, take all of the points/locations of interest defined by the
        calculation geometry. For each point, do distance queries on the site
        model and get the site parameters which are closest to the point of
        interest. This aggregation of points to the closest site parameters
        is what we store in `htemp.site_data`. (Computing this once prior to
        starting the calculation is optimal, since each task will need to
        consider all sites.)
        """
        logs.log_progress("initializing site model", 2)
        hc_id = self.job.hazard_calculation.id

        site_model_inp = get_site_model(hc_id)
        if site_model_inp is not None:
            # Explicit cast to `str` here because the XML parser doesn't like
            # unicode. (More specifically, lxml doesn't like unicode.)
            site_model_content = str(site_model_inp.model_content.raw_content)

            # Store `site_model` records:
            store_site_model(
                site_model_inp, StringIO.StringIO(site_model_content))

            mesh = self.job.hazard_calculation.points_to_compute()

            # Get the site model records we stored:
            site_model_data = models.SiteModel.objects.filter(
                input=site_model_inp)

            validate_site_model(site_model_data, mesh)

            store_site_data(hc_id, site_model_inp, mesh)

    # Silencing 'Too many local variables'
    # pylint: disable=R0914
    @transaction.commit_on_success(using='reslt_writer')
    def initialize_realizations(self, rlz_callbacks=None):
        """
        Create records for the `hzrdr.lt_realization` and
        `htemp.source_progress` records.

        This function works either in random sampling mode (when lt_realization
        models get the random seed value) or in enumeration mode (when weight
        values are populated). In both cases we record the logic tree paths
        for both trees in the `lt_realization` record, as well as ordinal
        number of the realization (zero-based).

        Then we create `htemp.source_progress` records for each source
        in the source model chosen for each realization,
        see :meth:`initialize_source_progress`.

        :param rlz_callbacks:
            Optionally, you can specify a list of callbacks for each
            realization.  In the case of the classical hazard calculator, for
            example, we would include a callback function to create initial
            records for temporary hazard curve result data.

            Callbacks should accept a single argument:
            A :class:`~openquake.db.models.LtRealization` object.
        """
        logs.log_progress("initializing realizations", 2)
        if self.job.hazard_calculation.number_of_logic_tree_samples > 0:
            # random sampling of paths
            self._initialize_realizations_montecarlo(
                rlz_callbacks=rlz_callbacks)
        else:
            # full paths enumeration
            self._initialize_realizations_enumeration(
                rlz_callbacks=rlz_callbacks)

    def initialize_pr_data(self):
        """Record the total/completed number of work items.

        This is needed for the purpose of providing an indication of progress
        to the end user."""
        stats.pk_set(self.job.id, "lvr", 0)
        rs = models.LtRealization.objects.filter(
            hazard_calculation=self.job.hazard_calculation)
        total = rs.aggregate(Sum("total_sources"))
        done = rs.aggregate(Sum("completed_sources"))
        stats.pk_set(self.job.id, "nhzrd_total", total.values().pop())
        if done > 0:
            stats.pk_set(self.job.id, "nhzrd_done", done.values().pop())

    def _initialize_realizations_enumeration(self, rlz_callbacks=None):
        """
        Perform full paths enumeration of logic trees and populate
        lt_realization table.

        :param rlz_callbacks:
            See :meth:`initialize_realizations` for more info.
        """
        hc = self.job.hazard_calculation
        [smlt] = models.inputs4hcalc(hc.id, input_type='lt_source')
        ltp = logictree.LogicTreeProcessor(hc.id)
        hzrd_src_cache = {}

        for i, path_info in enumerate(ltp.enumerate_paths()):
            sm_name, weight, sm_lt_path, gsim_lt_path = path_info

            lt_rlz = models.LtRealization(
                hazard_calculation=hc,
                ordinal=i,
                seed=None,
                weight=weight,
                sm_lt_path=sm_lt_path,
                gsim_lt_path=gsim_lt_path,
                # we will update total_sources in initialize_source_progress()
                total_sources=-1)
            lt_rlz.save()

            if not sm_name in hzrd_src_cache:
                # Get the source model for this sample:
                hzrd_src = models.Src2ltsrc.objects.get(
                    lt_src=smlt.id, filename=sm_name).hzrd_src
                # and cache it
                hzrd_src_cache[sm_name] = hzrd_src
            else:
                hzrd_src = hzrd_src_cache[sm_name]

            # Create source_progress objects
            self.initialize_source_progress(lt_rlz, hzrd_src)

            # Run realization callback (if any) to do additional initialization
            # for each realization:
            if rlz_callbacks is not None:
                for cb in rlz_callbacks:
                    cb(lt_rlz)

    def _initialize_realizations_montecarlo(self, rlz_callbacks=None):
        """
        Perform random sampling of both logic trees and populate lt_realization
        table.

        :param rlz_callbacks:
            See :meth:`initialize_realizations` for more info.
        """
        hc = self.job.hazard_calculation

        # Each realization will have two seeds:
        # One for source model logic tree, one for GSIM logic tree.
        rnd = random.Random()
        seed = hc.random_seed
        rnd.seed(seed)

        [smlt] = models.inputs4hcalc(hc.id, input_type='lt_source')

        ltp = logictree.LogicTreeProcessor(hc.id)

        hzrd_src_cache = {}

        # The first realization gets the seed we specified in the config file.
        for i in xrange(hc.number_of_logic_tree_samples):
            # Sample source model logic tree branch paths:
            sm_name, sm_lt_path = ltp.sample_source_model_logictree(
                    rnd.randint(MIN_SINT_32, MAX_SINT_32))

            # Sample GSIM logic tree branch paths:
            gsim_lt_path = ltp.sample_gmpe_logictree(
                    rnd.randint(MIN_SINT_32, MAX_SINT_32))

            lt_rlz = models.LtRealization(
                hazard_calculation=hc,
                ordinal=i,
                seed=seed,
                weight=None,
                sm_lt_path=sm_lt_path,
                gsim_lt_path=gsim_lt_path,
                # we will update total_sources in initialize_source_progress()
                total_sources=-1
            )
            lt_rlz.save()

            if not sm_name in hzrd_src_cache:
                # Get the source model for this sample:
                hzrd_src = models.Src2ltsrc.objects.get(
                    lt_src=smlt.id, filename=sm_name).hzrd_src
                # and cache it
                hzrd_src_cache[sm_name] = hzrd_src
            else:
                hzrd_src = hzrd_src_cache[sm_name]

            # Create source_progress objects
            self.initialize_source_progress(lt_rlz, hzrd_src)

            # Run realization callback (if any) to do additional initialization
            # for each realization:
            if rlz_callbacks is not None:
                for cb in rlz_callbacks:
                    cb(lt_rlz)

            # update the seed for the next realization
            seed = rnd.randint(MIN_SINT_32, MAX_SINT_32)
            rnd.seed(seed)

    @staticmethod
    def initialize_source_progress(lt_rlz, hzrd_src):
        """
        Create ``source_progress`` models for given logic tree realization
        and set total sources of realization.

        :param lt_rlz:
            :class:`openquake.db.models.LtRealization` object to initialize
            source progress for.
        :param hztd_src:
            :class:`openquake.db.models.Input` object that needed parsed
            sources are referencing.
        """
        cursor = connections['reslt_writer'].cursor()
        src_progress_tbl = models.SourceProgress._meta.db_table
        parsed_src_tbl = models.ParsedSource._meta.db_table
        lt_rlz_tbl = models.LtRealization._meta.db_table
        cursor.execute("""
            INSERT INTO "%s" (lt_realization_id, parsed_source_id, is_complete)
            SELECT %%s, id, FALSE
            FROM "%s" WHERE input_id = %%s
            ORDER BY id
            """ % (src_progress_tbl, parsed_src_tbl),
            [lt_rlz.id, hzrd_src.id])
        cursor.execute("""
            UPDATE "%s" SET total_sources = (
                SELECT count(1) FROM "%s" WHERE lt_realization_id = %%s
            )""" % (lt_rlz_tbl, src_progress_tbl),
            [lt_rlz.id])
        transaction.commit_unless_managed()

    def execute(self):
        """
        Calculation work is parallelized over sources, which means that each
        task will compute hazard for all sites but only with a subset of the
        seismic sources defined in the input model.

        The general workflow is as follows:

        1. Fill the queue with an initial set of tasks. The number of initial
        tasks is configurable using the `concurrent_tasks` parameter in the
        `[hazard]` section of the OpenQuake config file.

        2. Wait for tasks to signal completion (via AMQP message) and enqueue a
        new task each time another completes. Once all of the job work is
        enqueued, we just wait until all of the tasks conclude.
        """
        job = self.job
        hc = job.hazard_calculation
        sources_per_task = int(config.get('hazard', 'block_size'))
        concurrent_tasks = int(config.get('hazard', 'concurrent_tasks'))

        progress = dict(total=0, computed=0)
        # The following two counters are in a dict so that we can use them in
        # the closures below.
        # When `progress['compute']` becomes equal to `progress['total']`,
        # `execute` can conclude.

        task_gen = self.task_arg_gen(hc, job, sources_per_task, progress)

        def task_complete_callback(body, message):
            """
            :param dict body:
                ``body`` is the message sent by the task. The dict should
                contain 2 keys: `job_id` and `num_sources` (to indicate the
                number of sources computed).

                Both values are `int`.
            :param message:
                A :class:`kombu.transport.pyamqplib.Message`, which contains
                metadata about the message (including content type, channel,
                etc.). See kombu docs for more details.
            """
            job_id = body['job_id']
            num_sources = body['num_sources']

            assert job_id == job.id
            progress['computed'] += num_sources

            logs.log_percent_complete(job_id, "hazard")

            # Once we receive a completion signal, enqueue the next
            # piece of work (if there's anything left to be done).
            try:
                self.core_calc_task.apply_async(task_gen.next())
            except StopIteration:
                # There are no more tasks to dispatch; now we just need
                # to wait until all tasks signal completion.
                pass

            message.ack()

        exchange, conn_args = exchange_and_conn_args()

        routing_key = ROUTING_KEY_FMT % dict(job_id=job.id)
        task_signal_queue = kombu.Queue(
            'htasks.job.%s' % job.id, exchange=exchange,
            routing_key=routing_key, durable=False, auto_delete=True)

        with kombu.BrokerConnection(**conn_args) as conn:
            task_signal_queue(conn.channel()).declare()
            with conn.Consumer(task_signal_queue,
                               callbacks=[task_complete_callback]):
                # First: Queue up the initial tasks.
                for _ in xrange(concurrent_tasks):
                    try:
                        self.core_calc_task.apply_async(task_gen.next())
                    except StopIteration:
                        # If we get a `StopIteration` here, that means we have
                        # a number of tasks < concurrent_tasks.
                        # This basically just means that we could be
                        # under-utilizing worker node resources.
                        break

                while (progress['computed'] < progress['total']):
                    # This blocks until a message is received.
                    # Once we receive a completion signal, enqueue the next
                    # piece of work (if there's anything left to be done).
                    # (The `task_complete_callback` will handle additional
                    # queuing.)
                    conn.drain_events()
        logs.log_progress("hazard calculation 100% complete", 2)

    def export(self, *args, **kwargs):
        """
        If requested by the user, automatically export all result artifacts to
        the specified format. (NOTE: The only export format supported at the
        moment is NRML XML.

        :returns:
            A list of the export filenames, including the absolute path to each
            file.
        """
        exported_files = []

        logs.LOG.debug('> starting exports')
        if 'exports' in kwargs and 'xml' in kwargs['exports']:
            outputs = export_core.get_outputs(self.job.id)

            for output in outputs:
                exported_files.extend(hazard_export.export(
                    output.id, self.job.hazard_calculation.export_dir))

            for exp_file in exported_files:
                logs.LOG.debug('exported %s' % exp_file)
        logs.LOG.debug('< done with exports')

        return exported_files
