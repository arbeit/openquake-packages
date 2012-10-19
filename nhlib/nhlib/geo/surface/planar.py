# coding: utf-8
# nhlib: A New Hazard Library
# Copyright (C) 2012 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Module :mod:`nhlib.geo.surface.planar` contains :class:`PlanarSurface`.
"""
import numpy

from nhlib.geo import Point
from nhlib.geo.surface.base import BaseSurface
from nhlib.geo.mesh import Mesh, RectangularMesh
from nhlib.geo import geodetic
from nhlib.geo.nodalplane import NodalPlane
from nhlib.geo import utils as geo_utils


class PlanarSurface(BaseSurface):
    """
    Planar rectangular surface with two sides parallel to the Earth surface.

    :param mesh_spacing:
        The desired distance between two adjacent points in the surface mesh
        in both horizontal and vertical directions, in km.
    :param strike:
        Strike of the surface is the azimuth from ``top_left`` to ``top_right``
        points.
    :param dip:
        Dip is the angle between the surface itself and the earth surface.

    Other parameters are points (instances of :class:`~nhlib.geo.point.Point`)
    defining the surface corners in clockwise direction starting from top
    left corner. Top and bottom edges of the polygon must be parallel
    to earth surface and to each other.

    See :class:`~nhlib.geo.nodalplane.NodalPlane` for more detailed definition
    of ``strike`` and ``dip``. Note that these parameters are supposed
    to match the factual surface geometry (defined by corner points), but
    this is not enforced or even checked.

    :raises ValueError:
        If either top or bottom points differ in depth or if top edge
        is not parallel to the bottom edge, if top edge differs in length
        from the bottom one, or if mesh spacing is not positive.
    """
    #: Maximum difference in surface's rectangle side lengths, maximum offset
    #: of a bottom right corner from a plane that contains other corners,
    #: as well as maximum offset of a bottom left corner from a line drawn
    #: downdip perpendicular to top edge from top left corner, expressed
    #: as a fraction of the surface's area.
    IMPERFECT_RECTANGLE_TOLERANCE = 0.0008

    def __init__(self, mesh_spacing, strike, dip,
                 top_left, top_right, bottom_right, bottom_left):
        super(PlanarSurface, self).__init__()
        if not (top_left.depth == top_right.depth
                and bottom_left.depth == bottom_right.depth):
            raise ValueError("top and bottom edges must be parallel "
                             "to the earth surface")

        if not mesh_spacing > 0:
            raise ValueError("mesh spacing must be positive")
        self.mesh_spacing = mesh_spacing

        NodalPlane.check_dip(dip)
        NodalPlane.check_strike(strike)
        self.dip = dip
        self.strike = strike

        self.corner_lons = numpy.array([
            top_left.longitude, top_right.longitude,
            bottom_left.longitude, bottom_right.longitude
        ])
        self.corner_lats = numpy.array([
            top_left.latitude, top_right.latitude,
            bottom_left.latitude, bottom_right.latitude
        ])
        self.corner_depths = numpy.array([
            top_left.depth, top_right.depth,
            bottom_left.depth, bottom_right.depth
        ])
        self._init_plane()

        # now we can check surface for validity
        dists, xx, yy = self._project(self.corner_lons, self.corner_lats,
                                      self.corner_depths)
        # "length" of the rupture is measured along the top edge
        length1, length2 = xx[1] - xx[0], xx[3] - xx[2]
        # "width" of the rupture is measured along downdip direction
        width1, width2 = yy[2] - yy[0], yy[3] - yy[1]
        self.width = (width1 + width2) / 2.0
        self.length = (length1 + length2) / 2.0
        # calculate the imperfect rectangle tolerance
        # relative to surface's area
        tolerance = self.width * self.length \
                    * self.IMPERFECT_RECTANGLE_TOLERANCE
        if numpy.max(numpy.abs(dists)) > tolerance:
            raise ValueError("corner points do not lie on the same plane")
        if length2 < 0:
            raise ValueError("corners are in the wrong order")
        if abs(length1 - length2) > tolerance:
            raise ValueError("top and bottom edges have different lengths")
        if abs(xx[0] - xx[2]) > tolerance:
            raise ValueError("surface's angles are not right")

    def _init_plane(self):
        """
        Prepare everything needed for projecting arbitrary points on a plane
        containing the surface.
        """
        tl, tr, bl, br = geo_utils.spherical_to_cartesian(
            self.corner_lons, self.corner_lats, self.corner_depths
        )
        # these two parameters define the plane that contains the surface
        # (in 3d Cartesian space): a normal unit vector,
        self.normal = geo_utils.normalized(numpy.cross(tl - tr, tl - bl))
        # ... and scalar "d" parameter from the plane equation (uses
        # an equation (3) from http://mathworld.wolfram.com/Plane.html)
        self.d = - (self.normal * tl).sum()
        # these two 3d vectors together with a zero point represent surface's
        # coordinate space (the way to translate 3d Cartesian space with
        # a center in earth's center to 2d space centered in surface's top
        # left corner with basis vectors directed to top right and bottom left
        # corners. see :meth:`_project`.
        self.uv1 = geo_utils.normalized(tr - tl)
        self.uv2 = numpy.cross(self.normal, self.uv1)
        self.zero_zero = tl

    def translate(self, p1, p2):
        """
        Translate the surface for a specific distance along a specific azimuth
        direction.

        Parameters are two points (instances of :class:`nhlib.geo.point.Point`)
        representing the direction and an azimuth for translation. The
        resulting surface corner points will be that far along that azimuth
        from respective corner points of this surface as ``p2`` is located
        with respect to ``p1``.

        :returns:
            A new :class:`PlanarSurface` object with the same mesh spacing,
            dip, strike, width, length and depth but with corners longitudes
            and latitudes translated.
        """
        azimuth = geodetic.azimuth(p1.longitude, p1.latitude,
                                   p2.longitude, p2.latitude)
        distance = geodetic.geodetic_distance(p1.longitude, p1.latitude,
                                              p2.longitude, p2.latitude)
        # avoid calling PlanarSurface's constructor
        nsurf = object.__new__(PlanarSurface)
        # but do call BaseSurface's one
        BaseSurface.__init__(nsurf)
        nsurf.mesh_spacing = self.mesh_spacing
        nsurf.dip = self.dip
        nsurf.strike = self.strike
        nsurf.corner_lons, nsurf.corner_lats = geodetic.point_at(
            self.corner_lons, self.corner_lats, azimuth, distance
        )
        nsurf.corner_depths = self.corner_depths.copy()
        nsurf._init_plane()
        nsurf.width = self.width
        nsurf.length = self.length
        return nsurf

    @property
    def top_left(self):
        return Point(self.corner_lons[0], self.corner_lats[0],
                     self.corner_depths[0])

    @property
    def top_right(self):
        return Point(self.corner_lons[1], self.corner_lats[1],
                     self.corner_depths[1])

    @property
    def bottom_left(self):
        return Point(self.corner_lons[2], self.corner_lats[2],
                     self.corner_depths[2])

    @property
    def bottom_right(self):
        return Point(self.corner_lons[3], self.corner_lats[3],
                     self.corner_depths[3])

    def _create_mesh(self):
        """
        See :meth:`nhlib.geo.surface.base.BaseSurface._create_mesh`.
        """
        llons, llats, ldepths = geodetic.intervals_between(
            self.top_left.longitude, self.top_left.latitude,
            self.top_left.depth,
            self.bottom_left.longitude, self.bottom_left.latitude,
            self.bottom_left.depth,
            self.mesh_spacing
        )
        rlons, rlats, rdepths = geodetic.intervals_between(
            self.top_right.longitude, self.top_right.latitude,
            self.top_right.depth,
            self.bottom_right.longitude, self.bottom_right.latitude,
            self.bottom_right.depth,
            self.mesh_spacing
        )
        mlons, mlats, mdepths = [], [], []
        for i in xrange(len(llons)):
            lons, lats, depths = geodetic.intervals_between(
                llons[i], llats[i], ldepths[i], rlons[i], rlats[i], rdepths[i],
                self.mesh_spacing
            )
            mlons.append(lons)
            mlats.append(lats)
            mdepths.append(depths)
        return RectangularMesh(numpy.array(mlons), numpy.array(mlats),
                               numpy.array(mdepths))

    def get_strike(self):
        """
        Return strike value that was provided to the constructor.
        """
        return self.strike

    def get_dip(self):
        """
        Return dip value that was provided to the constructor.
        """
        return self.dip

    def _project(self, lons, lats, depths):
        """
        Project points to a surface's plane.

        Parameters are lists or numpy arrays of coordinates of points
        to project.

        :returns:
            A tuple of three items: distances between original points
            and surface's plane in km, "x" and "y" coordinates of points'
            projections to the plane (in a surface's coordinate space).
        """
        points = geo_utils.spherical_to_cartesian(lons, lats, depths)

        # uses method from http://www.9math.com/book/projection-point-plane
        dists = (self.normal * points).sum(axis=-1) + self.d
        t0 = - dists
        projs = points + self.normal * t0.reshape(t0.shape + (1, ))

        # translate projected points' to surface's coordinate space
        vectors2d = projs - self.zero_zero
        xx = (vectors2d * self.uv1).sum(axis=-1)
        yy = (vectors2d * self.uv2).sum(axis=-1)
        return dists, xx, yy

    def _project_back(self, dists, xx, yy):
        """
        Convert coordinates in plane's Cartesian space back to spherical
        coordinates.

        Parameters are numpy arrays, as returned from :meth:`_project`, which
        this method does the opposite to.

        :return:
            Tuple of longitudes, latitudes and depths numpy arrays.
        """
        vectors = self.zero_zero \
                  + self.uv1 * xx.reshape(xx.shape + (1, )) \
                  + self.uv2 * yy.reshape(yy.shape + (1, )) \
                  + self.normal * dists.reshape(dists.shape + (1, ))
        return geo_utils.cartesian_to_spherical(vectors)

    def get_min_distance(self, mesh):
        """
        See :meth:`superclass' method
        <nhlib.geo.surface.base.BaseSurface.get_min_distance>`.

        This is an optimized version specific to planar surface that doesn't
        make use of the mesh.
        """
        # we project all the points of the mesh on a plane that contains
        # the surface (translating coordinates of the projections to a local
        # 2d space) and at the same time calculate the distance to that
        # plane.
        dists, xx, yy = self._project(mesh.lons, mesh.lats, mesh.depths)
        # the actual resulting distance is a square root of squares
        # of a distance from a point to a plane that contains the surface
        # and a distance from a projection of that point on that plane
        # and a surface rectangle. we have former (``dists``), now we need
        # to find latter.
        #
        # we process separately two coordinate components of the point
        # projection. for abscissa we consider three possible cases:
        #
        #  I  . III .  II
        #     .     .
        #     0-----+                → x axis direction
        #     |     |
        #     +-----+
        #     .     .
        #     .     .
        #
        mxx = numpy.select(
            condlist=[
                # case "I": point on the left hand side from the rectangle
                xx < 0,
                # case "II": point is on the right hand side
                xx > self.length
                # default -- case "III": point is in between vertical sides
            ],
            choicelist=[
                # case "I": we need to consider distance between a point
                # and a line containing left side of the rectangle
                xx,
                # case "II": considering a distance between a point and
                # a line containing the right side
                xx - self.length
            ],
            # case "III": abscissa doesn't have an effect on a distance
            # to the rectangle
            default=0
        )
        # for ordinate we do the same operation (again three cases):
        #
        #    I
        #  - - - 0---+ - - -         ↓ y axis direction
        #   III  |   |
        #  - - - +---+ - - -
        #    II
        #
        myy = numpy.select(
            condlist=[
                # case "I": point is above the rectangle top edge
                yy < 0,
                # case "II": point is below the rectangle bottom edge
                yy > self.width
                # default -- case "III": point is in between lines containing
                # top and bottom edges
            ],
            choicelist=[
                # case "I": considering a distance to a line containing
                # a top edge
                yy,
                # case "II": considering a distance to a line containing
                # a bottom edge
                yy - self.width
            ],
            # case "III": ordinate doesn't affect the distance
            default=0
        )
        # distance between a point project and a rectangle combines from
        # both components
        dists2d_squares = mxx ** 2 + myy ** 2
        # finding a resulting distance combining a distance on a plane
        # with a distance to a plane
        return numpy.sqrt(dists ** 2 + dists2d_squares)

    def get_closest_points(self, mesh):
        """
        See :meth:`superclass' method
        <nhlib.geo.surface.base.BaseSurface.get_closest_points>`.

        This is an optimized version specific to planar surface that doesn't
        make use of the mesh.
        """
        dists, xx, yy = self._project(mesh.lons, mesh.lats, mesh.depths)
        mxx = xx.clip(0, self.length)
        myy = yy.clip(0, self.width)
        dists.fill(0)
        lons, lats, depths = self._project_back(dists, mxx, myy)
        return Mesh(lons, lats, depths)

    def _get_top_edge_centroid(self):
        """
        Overrides :meth:`superclass' method
        <nhlib.geo.surface.base.BaseSurface._get_top_edge_centroid>`
        in order to avoid creating a mesh.
        """
        lon, lat = geo_utils.get_middle_point(
            self.corner_lons[0], self.corner_lats[0],
            self.corner_lons[1], self.corner_lats[1]
        )
        return Point(lon, lat, self.corner_depths[0])

    def get_top_edge_depth(self):
        """
        Overrides :meth:`superclass' method
        <nhlib.geo.surface.base.BaseSurface.get_top_edge_depth>`
        in order to avoid creating a mesh.
        """
        return self.corner_depths[0]

    def get_joyner_boore_distance(self, mesh):
        """
        See :meth:`superclass' method
        <nhlib.geo.surface.base.BaseSurface.get_joyner_boore_distance>`.

        This is an optimized version specific to planar surface that doesn't
        make use of the mesh.
        """
        # we define four great circle arcs that contain four sides
        # of projected planar surface:
        #
        #       ↓     II    ↓
        #    I  ↓           ↓  I
        #       ↓     +     ↓
        #  →→→→→TL→→→→1→→→→TR→→→→→     → azimuth direction →
        #       ↓     -     ↓
        #       ↓           ↓
        # III  -3+   IV    -4+  III             ↓
        #       ↓           ↓            downdip direction
        #       ↓     +     ↓                   ↓
        #  →→→→→BL→→→→2→→→→BR→→→→→
        #       ↓     -     ↓
        #    I  ↓           ↓  I
        #       ↓     II    ↓
        #
        # arcs 1 and 2 are directed from left corners to right ones (the
        # direction has an effect on the sign of the distance to an arc,
        # as it shown on the figure), arcs 3 and 4 are directed from top
        # corners to bottom ones.
        #
        # then we measure distance from each of the points in a mesh
        # to each of those arcs and compare signs of distances in order
        # to find a relative positions of projections of points and
        # projection of a surface.
        #
        # then we consider four special cases (labeled with Roman numerals)
        # and either pick one of distances to arcs or a closest distance
        # to corner.
        #
        # indices 0, 2 and 1 represent corners TL, BL and TR respectively.
        arcs_lons = self.corner_lons.take([0, 2, 0, 1])
        arcs_lats = self.corner_lats.take([0, 2, 0, 1])
        downdip_azimuth = (self.strike + 90) % 360
        arcs_azimuths = [self.strike, self.strike,
                         downdip_azimuth, downdip_azimuth]
        mesh_lons = mesh.lons.reshape((-1, 1))
        mesh_lats = mesh.lats.reshape((-1, 1))
        # calculate distances from all the target points to all four arcs
        dists_to_arcs = geodetic.distance_to_arc(
            arcs_lons, arcs_lats, arcs_azimuths, mesh_lons, mesh_lats
        )
        # ... and distances from all the target points to each of surface's
        # corners' projections (we might not need all of those but it's
        # better to do that calculation once for all).
        dists_to_corners = geodetic.min_geodetic_distance(
            self.corner_lons, self.corner_lats, mesh.lons, mesh.lats
        )

        # extract from ``dists_to_arcs`` signs (represent relative positions
        # of an arc and a point: +1 means on the left hand side, 0 means
        # on arc and -1 means on the right hand side) and minimum absolute
        # values of distances to each pair of parallel arcs.
        ds1, ds2, ds3, ds4 = numpy.sign(dists_to_arcs).transpose()
        dists_to_arcs = numpy.abs(dists_to_arcs).reshape(-1, 2, 2).min(axis=-1)

        return numpy.select(
            # consider four possible relative positions of point and arcs:
            condlist=[
                # signs of distances to both parallel arcs are the same
                # in both pairs, case "I" on a figure above
                (ds1 == ds2) & (ds3 == ds4),
                # sign of distances to two parallels is the same only
                # in one pair, case "II"
                ds1 == ds2,
                # ... or another (case "III")
                ds3 == ds4
                # signs are different in both pairs (this is a "default"),
                # case "IV"
            ],

            choicelist=[
                # case "I": closest distance is the closest distance to corners
                dists_to_corners,
                # case "II": closest distance is distance to arc "1" or "2",
                # whichever is closer
                dists_to_arcs[:, 0],
                # case "III": closest distance is distance to either
                # arc "3" or "4"
                dists_to_arcs[:, 1]
            ],

            # default -- case "IV"
            default=0
        )

    def get_width(self):
        """
        Return surface's width value (in km) as computed in the constructor
        (that is mean value of left and right surface sides).
        """
        return self.width
