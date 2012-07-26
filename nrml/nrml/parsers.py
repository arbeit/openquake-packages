# Copyright (c) 2010-2012, GEM Foundation.
#
# NRML is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# NRML is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with NRML.  If not, see <http://www.gnu.org/licenses/>.


"""These parsers read NRML XML files and produce object representations of the
data.

See :module:`nrml.models`.
"""

import decimal

from lxml import etree

import nrml

from nrml import models
from nrml import utils


def _xpath(elem, expr):
    """Helper function for executing xpath queries on an XML element. This
    function uses the default mapping of namespaces (which includes NRML and
    GML).

    :param str expr:
        XPath expression.
    :param elem:
        A :class:`lxml.etree._Element` instance.
    """
    return elem.xpath(expr, namespaces=nrml.PARSE_NS_MAP)


class SourceModelParser(object):
    """NRML source model parser. Reads point sources, area sources, simple
    fault sources, and complex fault sources from a given source.

    :param source:
        Filename or file-like object containing the XML data.
    :param bool schema_validation:
        If set to `True`, validate the input source against the current XML
        schema. Otherwise, we will try to parse the ``source``, even if the
        document structure or content is incorrect.
    """

    _SM_TAG = '{%s}sourceModel' % nrml.NAMESPACE
    _PT_TAG = '{%s}pointSource' % nrml.NAMESPACE
    _AREA_TAG = '{%s}areaSource' % nrml.NAMESPACE
    _SIMPLE_TAG = '{%s}simpleFaultSource' % nrml.NAMESPACE
    _COMPLEX_TAG = '{%s}complexFaultSource' % nrml.NAMESPACE

    def __init__(self, source, schema_validation=True):
        self.source = source
        self.schema_validation = schema_validation

        self._parse_fn_map = {
            self._PT_TAG: self._parse_point,
            self._AREA_TAG: self._parse_area,
            self._SIMPLE_TAG: self._parse_simple,
            self._COMPLEX_TAG: self._parse_complex,
        }

    def _source_gen(self, tree):
        """Returns a generator which yields source model objects."""
        for event, element in tree:
            # We only want to parse data from the 'end' tag, otherwise there is
            # no guarantee the data will actually be present. We've run into
            # this issue in the past. See http://bit.ly/lxmlendevent for a
            # detailed description of the issue.
            if event == 'end':
                parse_fn = self._parse_fn_map.get(element.tag, None)
                if parse_fn is not None:
                    yield parse_fn(element)
                    element.clear()
                    while element.getprevious() is not None:
                        # Delete previous sibling elements.
                        # We need to loop here in case there are comments in
                        # the input file which are considered siblings to
                        # source elements.
                        del element.getparent()[0]

    @classmethod
    def _set_common_attrs(cls, model, src_elem):
        """Given a source object and a source XML element, set common
        attributes on the model, such as id, name, trt, mag_scale_rel, and
        rupt_aspect_ratio.

        :param model:
            Instance of a source class from :module:`nrml.models`.
        :param src_elem:
            :class:`lxml.etree._Element` instance representing a source.
        """
        model.id = src_elem.get('id')
        model.name = src_elem.get('name')
        model.trt = src_elem.get('tectonicRegion')

        model.mag_scale_rel = _xpath(
            src_elem, './nrml:magScaleRel')[0].text.strip()
        model.rupt_aspect_ratio = float(_xpath(
            src_elem, './nrml:ruptAspectRatio')[0].text)

    @classmethod
    def _parse_mfd(cls, src_elem):
        """
        :param src_elem:
            :class:`lxml.etree._Element` instance representing a source.
        """
        [mfd_elem] = _xpath(src_elem, ('.//nrml:truncGutenbergRichterMFD | '
                                       './/nrml:incrementalMFD'))

        if mfd_elem.tag == '{%s}truncGutenbergRichterMFD' % nrml.NAMESPACE:
            mfd = models.TGRMFD()
            mfd.a_val = float(mfd_elem.get('aValue'))
            mfd.b_val = float(mfd_elem.get('bValue'))
            mfd.min_mag = float(mfd_elem.get('minMag'))
            mfd.max_mag = float(mfd_elem.get('maxMag'))

        elif mfd_elem.tag == '{%s}incrementalMFD' % nrml.NAMESPACE:
            mfd = models.IncrementalMFD()
            mfd.min_mag = float(mfd_elem.get('minMag'))
            mfd.bin_width = float(mfd_elem.get('binWidth'))

            [occur_rates] = _xpath(mfd_elem, './nrml:occurRates')
            mfd.occur_rates = [float(x) for x in occur_rates.text.split()]

        return mfd

    @classmethod
    def _parse_nodal_plane_dist(cls, src_elem):
        """
        :param src_elem:
            :class:`lxml.etree._Element` instance representing a source.
        :returns:
            `list` of :class:`nrml.models.NodalPlane` objects.
        """
        npd = []

        for elem in _xpath(src_elem, './/nrml:nodalPlane'):
            nplane = models.NodalPlane()
            nplane.probability = decimal.Decimal(elem.get('probability'))
            nplane.strike = float(elem.get('strike'))
            nplane.dip = float(elem.get('dip'))
            nplane.rake = float(elem.get('rake'))

            npd.append(nplane)

        return npd

    @classmethod
    def _parse_hypo_depth_dist(cls, src_elem):
        """
        :param src_elem:
            :class:`lxml.etree._Element` instance representing a source.
        :returns:
            `list` of :class:`nrml.models.HypocentralDepth` objects.
        """
        hdd = []

        for elem in _xpath(src_elem, './/nrml:hypoDepth'):
            hdepth = models.HypocentralDepth()
            hdepth.probability = decimal.Decimal(elem.get('probability'))
            hdepth.depth = float(elem.get('depth'))

            hdd.append(hdepth)

        return hdd

    @classmethod
    def _parse_point(cls, src_elem):
        """
        :param src_elem:
            :class:`lxml.etree._Element` instance representing a source.
        :returns:
            Fully populated :class:`nrml.models.PointSource` object.
        """
        point = models.PointSource()
        cls._set_common_attrs(point, src_elem)

        point_geom = models.PointGeometry()
        point.geometry = point_geom

        [gml_pos] = _xpath(src_elem, './/gml:pos')
        coords = gml_pos.text.split()
        point_geom.wkt = 'POINT(%s)' % ' '.join(coords)

        point_geom.upper_seismo_depth = float(
            _xpath(src_elem, './/nrml:upperSeismoDepth')[0].text)
        point_geom.lower_seismo_depth = float(
            _xpath(src_elem, './/nrml:lowerSeismoDepth')[0].text)

        point.mfd = cls._parse_mfd(src_elem)
        point.nodal_plane_dist = cls._parse_nodal_plane_dist(src_elem)
        point.hypo_depth_dist = cls._parse_hypo_depth_dist(src_elem)

        return point

    @classmethod
    def _parse_area(cls, src_elem):
        """
        :param src_elem:
            :class:`lxml.etree._Element` instance representing a source.
        :returns:
            Fully populated :class:`nrml.models.AreaSource` object.
        """
        area = models.AreaSource()
        cls._set_common_attrs(area, src_elem)

        area_geom = models.AreaGeometry()
        area.geometry = area_geom

        [gml_pos_list] = _xpath(src_elem, './/gml:posList')
        coords = gml_pos_list.text.split()
        # Area source polygon geometries are always 2-dimensional and on the
        # Earth's surface (depth == 0.0).
        area_geom.wkt = utils.coords_to_poly_wkt(coords, 2)

        area_geom.upper_seismo_depth = float(
            _xpath(src_elem, './/nrml:upperSeismoDepth')[0].text)
        area_geom.lower_seismo_depth = float(
            _xpath(src_elem, './/nrml:lowerSeismoDepth')[0].text)

        area.mfd = cls._parse_mfd(src_elem)
        area.nodal_plane_dist = cls._parse_nodal_plane_dist(src_elem)
        area.hypo_depth_dist = cls._parse_hypo_depth_dist(src_elem)

        return area

    @classmethod
    def _parse_simple(cls, src_elem):
        """
        :param src_elem:
            :class:`lxml.etree._Element` instance representing a source.
        :returns:
            Fully populated :class:`nrml.models.SimpleFaultSource` object.
        """
        simple = models.SimpleFaultSource()
        cls._set_common_attrs(simple, src_elem)

        simple_geom = models.SimpleFaultGeometry()
        simple.geometry = simple_geom

        [gml_pos_list] = _xpath(src_elem, './/gml:posList')
        coords = gml_pos_list.text.split()
        simple_geom.wkt = utils.coords_to_linestr_wkt(coords, 2)

        simple_geom.dip = float(
            _xpath(src_elem, './/nrml:dip')[0].text)
        simple_geom.upper_seismo_depth = float(
            _xpath(src_elem, './/nrml:upperSeismoDepth')[0].text)
        simple_geom.lower_seismo_depth = float(
            _xpath(src_elem, './/nrml:lowerSeismoDepth')[0].text)

        simple.mfd = cls._parse_mfd(src_elem)
        simple.rake = float(
            _xpath(src_elem, './/nrml:rake')[0].text)

        return simple

    @classmethod
    def _parse_complex(cls, src_elem):
        """
        :param src_elem:
            :class:`lxml.etree._Element` instance representing a source.
        :returns:
            Fully populated :class:`nrml.models.ComplexFaultSource` object.
        """
        complx = models.ComplexFaultSource()
        cls._set_common_attrs(complx, src_elem)

        complex_geom = models.ComplexFaultGeometry()
        complx.geometry = complex_geom

        [top_edge] = _xpath(src_elem, './/nrml:faultTopEdge//gml:posList')
        top_coords = top_edge.text.split()
        complex_geom.top_edge_wkt = utils.coords_to_linestr_wkt(top_coords, 3)

        [bottom_edge] = _xpath(
            src_elem, './/nrml:faultBottomEdge//gml:posList')
        bottom_coords = bottom_edge.text.split()
        complex_geom.bottom_edge_wkt = utils.coords_to_linestr_wkt(
            bottom_coords, 3)

        # Optional itermediate edges:
        int_edges = _xpath(src_elem, './/nrml:intermediateEdge//gml:posList')
        for edge in int_edges:
            coords = edge.text.split()
            complex_geom.int_edges.append(
                utils.coords_to_linestr_wkt(coords, 3))

        complx.mfd = cls._parse_mfd(src_elem)
        complx.rake = float(
            _xpath(src_elem, './/nrml:rake')[0].text)

        return complx

    def parse(self):
        """Parse the source XML content and generate a source model in object
        form.

        :returns:
            :class:`nrml.models.SourceModel` instance.
        """
        src_model = models.SourceModel()

        if self.schema_validation:
            schema = etree.XMLSchema(etree.parse(nrml.nrml_schema_file()))
        else:
            schema = None
        tree = etree.iterparse(self.source, events=('start', 'end'),
                               schema=schema)

        for event, element in tree:
            # Find the <sourceModel> element and get the 'name' attr.
            if event == 'start':
                if element.tag == self._SM_TAG:
                    src_model.name = element.get('name')
                    break
            else:
                # If we get to here, we didn't find the <sourceModel> element.
                raise ValueError('<sourceModel> element not found.')

        src_model.sources = self._source_gen(tree)

        return src_model


class SiteModelParser(object):
    """NRML site model parser. Reads site-specific parameters from a given
    source.

    :param source:
        Filename or file-like object containing the XML data.
    :param bool schema_validation:
        If set to `True`, validate the input source against the current XML
        schema. Otherwise, we will try to parse the ``source``, even if the
        document structure or content is incorrect.
    """

    def __init__(self, source, schema_validation=True):
        self.source = source
        self.schema_validation = schema_validation

    def parse(self):
        """Parse the site model XML content and generate
        :class:`nrml.model.SiteModel` objects.

        :returns:
            A iterable of :class:`nrml.model.SiteModel` objects.
        """
        if self.schema_validation:
            schema = etree.XMLSchema(etree.parse(nrml.nrml_schema_file()))
        else:
            schema = None
        tree = etree.iterparse(self.source, events=('start',),
                               schema=schema)

        for _, element in tree:
            if element.tag == '{%s}site' % nrml.NAMESPACE:
                site = models.SiteModel()
                site.vs30 = float(element.get('vs30'))
                site.vs30_type = element.get('vs30Type').strip()
                site.z1pt0 = float(element.get('z1pt0'))
                site.z2pt5 = float(element.get('z2pt5'))
                lonlat = dict(lon=element.get('lon').strip(),
                              lat=element.get('lat').strip())
                site.wkt = 'POINT(%(lon)s %(lat)s)' % lonlat

                yield site

                # Now do some clean up to free memory.
                while element.getprevious() is not None:
                    # Delete previous sibling elements.
                    # We need to loop here in case there are comments in
                    # the input file which are considered siblings to
                    # source elements.
                    del element.getparent()[0]
