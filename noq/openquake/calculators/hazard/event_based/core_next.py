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

"""
Core calculator functionality for computing stochastic event sets and ground
motion fields using the 'event-based' method.

Stochastic events sets (which can be thought of as collections of ruptures) are
computed iven a set of seismic sources and investigation time span (in years).

For more information on computing stochastic event sets, see
:mod:`nhlib.calc.stochastic`.

One can optionally compute a ground motion field (GMF) given a rupture, a site
collection (which is a collection of geographical points with associated soil
parameters), and a ground shaking intensity model (GSIM).

For more information on computing ground motion fields, see
:mod:`nhlib.calc.gmf`.
"""

import random

import nhlib.imt
import nhlib.source
import numpy.random

from django.db import transaction
from nhlib import correlation
from nhlib.calc import filters
from nhlib.calc import gmf as gmf_calc
from nhlib.calc import stochastic

from openquake import logs
from openquake import writer
from openquake.calculators.hazard import general as haz_general
from openquake.db import models
from openquake.input import logictree
from openquake.job.validation import MAX_SINT_32
from openquake.utils import stats
from openquake.utils import tasks as utils_tasks

#: Ground motion correlation model map
GM_CORRELATION_MODEL_MAP = {
    'JB2009': correlation.JB2009CorrelationModel,
}

#: Always 1 for the computation of ground motion fields in the event-based
#: hazard calculator.
DEFAULT_GMF_REALIZATIONS = 1


# Disabling pylint for 'Too many local variables'
# pylint: disable=R0914
@utils_tasks.oqtask
@stats.count_progress('h')
def ses_and_gmfs(job_id, src_ids, lt_rlz_id, task_seed):
    """
    Celery task for the stochastic event set calculator.

    Samples logic trees and calls the stochastic event set calculator.

    Once stochastic event sets are calculated, results will be saved to the
    database. See :class:`openquake.db.models.SESCollection`.

    Optionally (specified in the job configuration using the
    `ground_motion_fields` parameter), GMFs can be computed from each rupture
    in each stochastic event set. GMFs are also saved to the database.

    Once all of this work is complete, a signal will be sent via AMQP to let
    the control noe know that the work is complete. (If there is any work left
    to be dispatched, this signal will indicate to the control node that more
    work can be enqueued.)

    :param int job_id:
        ID of the currently running job.
    :param src_ids:
        List of ids of parsed source models from which we will generate
        stochastic event sets/ruptures.
    :param lt_rlz_id:
        Id of logic tree realization model to calculate for.
    :param int task_seed:
        Value for seeding numpy/scipy in the computation of stochastic event
        sets and ground motion fields.
    """
    logs.LOG.debug(('> starting `stochastic_event_sets` task: job_id=%s, '
                    'lt_realization_id=%s') % (job_id, lt_rlz_id))
    numpy.random.seed(task_seed)

    hc = models.HazardCalculation.objects.get(oqjob=job_id)

    cmplt_lt_ses = None
    if hc.complete_logic_tree_ses:
        cmplt_lt_ses = models.SES.objects.get(
            ses_collection__output__oq_job=job_id,
            complete_logic_tree_ses=True)

    cmplt_lt_gmf = None
    if hc.complete_logic_tree_gmf:
        cmplt_lt_gmf = models.GmfSet.objects.get(
            gmf_collection__output__oq_job=job_id,
            complete_logic_tree_gmf=True)

    if hc.ground_motion_fields:
        # For ground motion field calculation, we need the points of interest
        # for the calculation.
        points_to_compute = hc.points_to_compute()

    lt_rlz = models.LtRealization.objects.get(id=lt_rlz_id)
    ltp = logictree.LogicTreeProcessor(hc.id)

    apply_uncertainties = ltp.parse_source_model_logictree_path(
            lt_rlz.sm_lt_path)
    gsims = ltp.parse_gmpe_logictree_path(lt_rlz.gsim_lt_path)

    sources = list(haz_general.gen_sources(
        src_ids, apply_uncertainties, hc.rupture_mesh_spacing,
        hc.width_of_mfd_bin, hc.area_source_discretization))

    logs.LOG.debug('> creating site collection')
    site_coll = haz_general.get_site_collection(hc)
    logs.LOG.debug('< done creating site collection')

    if hc.ground_motion_fields:
        imts = [haz_general.imt_to_nhlib(x)
                for x in hc.intensity_measure_types]

        correl_model = None
        if hc.ground_motion_correlation_model is not None:
            correl_model = _get_correl_model(hc)

    # Compute stochastic event sets
    # For each rupture generated, we can optionally calculate a GMF
    for ses_rlz_n in xrange(1, hc.ses_per_logic_tree_path + 1):
        logs.LOG.debug('> computing stochastic event set %s of %s'
                       % (ses_rlz_n, hc.ses_per_logic_tree_path))

        # This is the container for all ruptures for this stochastic event set
        # (specified by `ordinal` and the logic tree realization).
        # NOTE: Many tasks can contribute ruptures to this SES.
        ses = models.SES.objects.get(
            ses_collection__lt_realization=lt_rlz, ordinal=ses_rlz_n)

        sources_sites = ((src, site_coll) for src in sources)
        ssd_filter = filters.source_site_distance_filter(hc.maximum_distance)
        # Get the filtered sources, ignore the site collection:
        filtered_sources = (src for src, _ in ssd_filter(sources_sites))
        # Calculate stochastic event sets:
        logs.LOG.debug('> computing stochastic event sets')
        if hc.ground_motion_fields:
            logs.LOG.debug('> computing also ground motion fields')
            # This will be the "container" for all computed ground motion field
            # results for this stochastic event set.
            gmf_set = models.GmfSet.objects.get(
                gmf_collection__lt_realization=lt_rlz, ses_ordinal=ses_rlz_n)

        ses_poissonian = stochastic.stochastic_event_set_poissonian(
            filtered_sources, hc.investigation_time)

        logs.LOG.debug('> looping over ruptures')
        rupture_ctr = 0
        for rupture in ses_poissonian:
            # Prepare and save SES ruptures to the db:
            logs.LOG.debug('> saving SES rupture to DB')
            _save_ses_rupture(ses, rupture, cmplt_lt_ses)
            logs.LOG.debug('> done saving SES rupture to DB')

            # Compute ground motion fields (if requested)
            logs.LOG.debug('compute ground motion fields?  %s'
                           % hc.ground_motion_fields)
            if hc.ground_motion_fields:
                # Compute and save ground motion fields

                gmf_calc_kwargs = {
                    'rupture': rupture,
                    'sites': site_coll,
                    'imts': imts,
                    'gsim': gsims[rupture.tectonic_region_type],
                    'truncation_level': hc.truncation_level,
                    'realizations': DEFAULT_GMF_REALIZATIONS,
                    'correlation_model': correl_model,
                    'rupture_site_filter':
                        filters.rupture_site_distance_filter(
                            hc.maximum_distance),
                }
                logs.LOG.debug('> computing ground motion fields')
                gmf_dict = gmf_calc.ground_motion_fields(**gmf_calc_kwargs)
                logs.LOG.debug('< done computing ground motion fields')

                logs.LOG.debug('> saving GMF results to DB')
                _save_gmf_nodes(
                    gmf_set, gmf_dict, points_to_compute, cmplt_lt_gmf)
                logs.LOG.debug('< done saving GMF results to DB')
            rupture_ctr += 1

        logs.LOG.debug('< Done looping over ruptures')
        logs.LOG.debug('%s ruptures computed for SES realization %s of %s'
                       % (rupture_ctr, ses_rlz_n, hc.ses_per_logic_tree_path))
        logs.LOG.debug('< done computing stochastic event set %s of %s'
                       % (ses_rlz_n, hc.ses_per_logic_tree_path))

    logs.LOG.debug('< task complete, signalling completion')
    haz_general.signal_task_complete(job_id, len(src_ids))


def _get_correl_model(hc):
    """
    Helper function for constructing the appropriate correlation model.

    :param hc:
        A :class:`openquake.db.models.HazardCalculation` instance.

    :returns:
        A correlation object. See :mod:`nhlib.correlation` for more info.
    """
    correl_model_cls = getattr(
        correlation,
        '%sCorrelationModel' % hc.ground_motion_correlation_model,
        None)
    if correl_model_cls is None:
        raise RuntimeError("Unknown correlation model: '%s'"
                           % hc.ground_motion_correlation_model)

    return correl_model_cls(**hc.ground_motion_correlation_params)


def _save_ses_rupture(ses, rupture, complete_logic_tree_ses):
    """
    Helper function for saving stochastic event set ruptures to the database.

    :param ses:
        A :class:`openquake.db.models.SES` instance. This will be DB
        'container' for the new rupture record.
    :param rupture:
        A :class:`nhlib.source.rupture.Rupture` instance.
    :param complete_logic_tree_ses:
        :class:`openquake.db.models.SES` representing the `complete logic tree`
        stochastic event set.
        If not None, save a copy of the input `rupture` to this SES.
    """
    is_from_fault_source = rupture.source_typology in (
        nhlib.source.ComplexFaultSource,
        nhlib.source.SimpleFaultSource)

    if is_from_fault_source:
        # for simple and complex fault sources,
        # rupture surface geometry is represented by a mesh
        surf_mesh = rupture.surface.get_mesh()
        lons = surf_mesh.lons
        lats = surf_mesh.lats
        depths = surf_mesh.depths
    else:
        # For area or point source,
        # rupture geometry is represented by a planar surface,
        # defined by 3D corner points
        surface = rupture.surface
        lons = numpy.zeros((4))
        lats = numpy.zeros((4))
        depths = numpy.zeros((4))

        # NOTE: It is important to maintain the order of these corner
        # points.
        for i, corner in enumerate((surface.top_left,
                                    surface.top_right,
                                    surface.bottom_right,
                                    surface.bottom_left)):
            lons[i] = corner.longitude
            lats[i] = corner.latitude
            depths[i] = corner.depth

    # TODO: Possible future optimiztion:
    # Refactor this to do bulk insertion of ruptures
    models.SESRupture.objects.create(
        ses=ses,
        magnitude=rupture.mag,
        strike=rupture.surface.get_strike(),
        dip=rupture.surface.get_dip(),
        rake=rupture.rake,
        tectonic_region_type=rupture.tectonic_region_type,
        is_from_fault_source=is_from_fault_source,
        lons=lons,
        lats=lats,
        depths=depths,
    )
    if complete_logic_tree_ses is not None:
        models.SESRupture.objects.create(
            ses=complete_logic_tree_ses,
            magnitude=rupture.mag,
            strike=rupture.surface.get_strike(),
            dip=rupture.surface.get_dip(),
            rake=rupture.rake,
            tectonic_region_type=rupture.tectonic_region_type,
            is_from_fault_source=is_from_fault_source,
            lons=lons,
            lats=lats,
            depths=depths,
        )


@transaction.commit_on_success(using='reslt_writer')
def _save_gmf_nodes(gmf_set, gmf_dict, points_to_compute,
                    complete_logic_tree_gmf_set):
    """
    Helper function for saving ground motion field results to the database.

    :param gmf_set:
        :class:`openquake.db.models.GmfSet` record with which the input ground
        motion field data will be associated.
    :param dict gmf_dict:
        The result of the GMF calculation, performed by nhlib. For more info,
        view the documentation for :func:`nhlib.calc.gmf.ground_motion_fields`.
    :param points_to_compute:
        A :class:`nhlib.geo.mesh.Mesh` object representing all of the points of
        interest.
    :param complete_logic_tree_gmf_set:
        :class:`openquake.db.models.GmfSet` representing the `complete logic
        tree` GMF set.
        If not None, save a copy of the input GMFs (in ``gmf_dict``) to this
        GMF set.

        The indices of this mesh are used in relation to the indices of results
        in the GMF matrices to determine where the GMFs are located.
    """
    for imt, gmf_matrix in gmf_dict.iteritems():
        # NOTE: The values of each `gmf_matrix` are numpy.matrix types.
        # We need to convert them to numpy.array types before saving.
        # (The ORM doesn't like numpy.matrix types.)
        gmf_matrix = numpy.array(gmf_matrix)
        gmf = _create_gmf_record(gmf_set, imt)

        clt_gmf = None
        if complete_logic_tree_gmf_set is not None:
            clt_gmf = _create_gmf_record(complete_logic_tree_gmf_set, imt)

        gmf_bulk_inserter = writer.BulkInserter(models.GmfNode)

        for i, location in enumerate(points_to_compute):
            gmf_bulk_inserter.add_entry(
                gmf_id=gmf.id,
                # GMF results are a 2D array; in the case of the
                # event-based calculator, we only compute 1
                # realization (in the scenario calculator it can be
                # many). Thus, we take the one and only value for
                # the point of interest (`i`).
                iml=gmf_matrix[i][0],
                location=location.wkt2d)

            # If the option is specified, save a copy to the complete logic
            # tree GMF:
            if clt_gmf is not None:
                gmf_bulk_inserter.add_entry(
                    gmf_id=clt_gmf.id,
                    iml=gmf_matrix[i][0],
                    location=location.wkt2d)
        gmf_bulk_inserter.flush()


def _create_gmf_record(gmf_set, imt):
    """
    Helper function to create :class:`openquake.db.models.Gmf` records. The
    record will be saved to the DB and returned.

    :param gmf_set:
        :class:`openquake.db.models.GmfSet` instance.
    :param imt:
        An instance of one of the IMT classes defined in :mod:`nhlib.imt`.

    :returns:
        The newly created :class:`openquake.db.models.Gmf` object.
    """
    gmf = models.Gmf(
        gmf_set=gmf_set, imt=imt.__class__.__name__)

    if isinstance(imt, nhlib.imt.SA):
        gmf.sa_period = imt.period
        gmf.sa_damping = imt.damping

    gmf.save()
    return gmf


@staticmethod
def event_based_task_arg_gen(hc, job, sources_per_task, progress):
    """
    Loop through realizations and sources to generate a sequence of
    task arg tuples. Each tuple of args applies to a single task.

    Yielded results are quadruples of (job_id, realization_id,
    source_id_list, random_seed). (random_seed will be used to seed
    numpy for temporal occurence sampling.)

    :param hc:
        :class:`openquake.db.models.HazardCalculation` instance.
    :param job:
        :class:`openquake.db.models.OqJob` instance.
    :param int sources_per_task:
        The (max) number of sources to consider for each task.
    :param dict progress:
        A dict containing two integer values: 'total' and 'computed'. The task
        arg generator will update the 'total' count as the generator creates
        arguments.
    """

    rnd = random.Random()
    rnd.seed(hc.random_seed)

    realizations = models.LtRealization.objects.filter(
            hazard_calculation=hc, is_complete=False)

    for lt_rlz in realizations:
        source_progress = models.SourceProgress.objects.filter(
                is_complete=False, lt_realization=lt_rlz).order_by('id')
        source_ids = source_progress.values_list('parsed_source_id',
                                                 flat=True)
        progress['total'] += len(source_ids)

        for offset in xrange(0, len(source_ids), sources_per_task):
            # Since this seed will used for numpy random seeding, it needs to
            # positive (since numpy will convert it to a unsigned long).
            task_seed = rnd.randint(0, MAX_SINT_32)
            task_args = (job.id, source_ids[offset:offset + sources_per_task],
                         lt_rlz.id, task_seed)
            yield task_args


class EventBasedHazardCalculator(haz_general.BaseHazardCalculatorNext):
    """
    Probabilistic Event-Based hazard calculator. Computes stochastic event sets
    and (optionally) ground motion fields.
    """

    core_calc_task = ses_and_gmfs
    task_arg_gen = event_based_task_arg_gen

    def initialize_ses_db_records(self, lt_rlz):
        """
        Create :class:`~openquake.db.models.Output`,
        :class:`~openquake.db.models.SESCollection` and
        :class:`~openquake.db.models.SES` "container" records for a single
        realization.

        Stochastic event set ruptures computed for this realization will be
        associated to these containers.
        """
        hc = self.job.hazard_calculation

        output = models.Output.objects.create(
            owner=self.job.owner,
            oq_job=self.job,
            display_name='ses-coll-rlz-%s' % lt_rlz.id,
            output_type='ses')

        ses_coll = models.SESCollection.objects.create(
            output=output, lt_realization=lt_rlz)

        for i in xrange(1, hc.ses_per_logic_tree_path + 1):
            models.SES.objects.create(
                ses_collection=ses_coll,
                investigation_time=hc.investigation_time,
                ordinal=i)

    def initialize_complete_lt_ses_db_records(self):
        """
        Optional; if the user has requested to collect a `complete logic tree`
        stochastic event set (containing all ruptures from all realizations),
        initialize DB records for those results here.

        Throughout the course of the calculation, computed ruptures will be
        copied into this collection. See :func:`_save_ses_rupture` for more
        info.
        """
        hc = self.job.hazard_calculation

        # `complete logic tree` SES
        clt_ses_output = models.Output.objects.create(
            owner=self.job.owner,
            oq_job=self.job,
            display_name='complete logic tree SES',
            output_type='complete_lt_ses')

        clt_ses_coll = models.SESCollection.objects.create(
            output=clt_ses_output, complete_logic_tree_ses=True)

        investigation_time = self._compute_investigation_time(hc)

        models.SES.objects.create(
            ses_collection=clt_ses_coll,
            investigation_time=investigation_time,
            complete_logic_tree_ses=True)

    def initialize_complete_lt_gmf_db_records(self):
        """
        Optional; if the user has requested to collect a `complete logic tree`
        GMF set (containing all ground motion fields from all realizations),
        initialize DB records for those results here.

        Throughout the course of the calculation, computed GMFs will be copied
        into this collection. See :func:`_save_gmf_nodes` for more info.
        """
        hc = self.job.hazard_calculation

        # `complete logic tree` GMF
        clt_gmf_output = models.Output.objects.create(
            owner=self.job.owner,
            oq_job=self.job,
            display_name='complete logic tree GMF',
            output_type='complete_lt_gmf')

        gmf_coll = models.GmfCollection.objects.create(
            output=clt_gmf_output, complete_logic_tree_gmf=True)

        investigation_time = self._compute_investigation_time(hc)

        models.GmfSet.objects.create(
            gmf_collection=gmf_coll,
            investigation_time=investigation_time,
            complete_logic_tree_gmf=True)

    @staticmethod
    def _compute_investigation_time(haz_calc):
        """
        Helper method for :meth:`initialize_complete_lt_ses_db_records` and
        :meth:`initialize_complete_lt_gmf_db_records` to compute the
        investigation time for a given set of results.

        :param haz_calc:
            :class:`openquake.db.models.HazardCalculation` object for the
            current job.
        """
        if haz_calc.number_of_logic_tree_samples > 0:
            # The calculation is set to do Monte-Carlo sampling of logic trees
            # The number of logic tree realizations is specified explicitly in
            # job configuration.
            n_lt_realizations = haz_calc.number_of_logic_tree_samples
        else:
            # The calculation is set do end-branch enumeration of all logic
            # tree paths
            # We can get the number of logic tree realizations by counting
            # initialized lt_realization records.
            n_lt_realizations = models.LtRealization.objects.filter(
                hazard_calculation=haz_calc.id).count()

        investigation_time = (haz_calc.investigation_time
                              * haz_calc.ses_per_logic_tree_path
                              * n_lt_realizations)

        return investigation_time

    def initialize_gmf_db_records(self, lt_rlz):
        """
        Create :class:`~openquake.db.models.Output`,
        :class:`~openquake.db.models.GmfCollection` and
        :class:`~openquake.db.models.GmfSet` "container" records for a single
        realization.

        GMFs for this realization will be associated to these containers.
        """
        hc = self.job.hazard_calculation

        output = models.Output.objects.create(
            owner=self.job.owner,
            oq_job=self.job,
            display_name='gmf-rlz-%s' % lt_rlz.id,
            output_type='gmf')

        gmf_coll = models.GmfCollection.objects.create(
            output=output, lt_realization=lt_rlz)

        for i in xrange(1, hc.ses_per_logic_tree_path + 1):
            models.GmfSet.objects.create(
                gmf_collection=gmf_coll,
                investigation_time=hc.investigation_time,
                ses_ordinal=i)

    def pre_execute(self):
        """
        Do pre-execution work. At the moment, this work entails: parsing and
        initializing sources, parsing and initializing the site model (if there
        is one), and generating logic tree realizations. (The latter piece
        basically defines the work to be done in the `execute` phase.)
        """

        # Parse logic trees and create source Inputs.
        self.initialize_sources()

        # Deal with the site model and compute site data for the calculation
        # If no site model file was specified, reference parameters are used
        # for all sites.
        self.initialize_site_model()

        # Now bootstrap the logic tree realizations and related data.
        # This defines for us the "work" that needs to be done when we reach
        # the `execute` phase.
        rlz_callbacks = [self.initialize_ses_db_records]
        if self.job.hazard_calculation.ground_motion_fields:
            rlz_callbacks.append(self.initialize_gmf_db_records)

        self.initialize_realizations(rlz_callbacks=rlz_callbacks)

        if self.job.hazard_calculation.complete_logic_tree_ses:
            self.initialize_complete_lt_ses_db_records()

        if self.job.hazard_calculation.complete_logic_tree_gmf:
            self.initialize_complete_lt_gmf_db_records()

        self.initialize_pr_data()
