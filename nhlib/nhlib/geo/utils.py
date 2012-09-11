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
Module :mod:`nhlib.geo.utils` contains functions that are common to several
geographical primitives and some other low-level spatial operations.
"""
import numpy
import shapely.geometry

from nhlib.geo import geodetic
from nhlib.geo.geodetic import EARTH_RADIUS


def clean_points(points):
    """
    Given a list of :class:`~nhlib.geo.point.Point` objects, return a new list
    with adjacent duplicate points removed.
    """
    if not points:
        return points

    result = [points[0]]
    for point in points:
        if point != result[-1]:
            result.append(point)
    return result


def line_intersects_itself(lons, lats, closed_shape=False):
    """
    Return ``True`` if line of points intersects itself.
    Line with the last point repeating the first one considered
    intersecting itself.

    The line is defined by lists (or numpy arrays) of points'
    longitudes and latitudes (depth is not taken into account).

    :param closed_shape:
        If ``True`` the line will be checked twice: first time with
        its original shape and second time with the points sequence
        being shifted by one point (the last point becomes first,
        the first turns second and so on). This is useful for
        checking that the sequence of points defines a valid
        :class:`~nhlib.geo.polygon.Polygon`.
    """
    assert len(lons) == len(lats)

    if len(lons) <= 3:
        # line can not intersect itself unless there are
        # at least four points
        return False

    west, east, north, south = get_spherical_bounding_box(lons, lats)
    proj = get_orthographic_projection(west, east, north, south)

    xx, yy = proj(lons, lats)
    if not shapely.geometry.LineString(zip(xx, yy)).is_simple:
        return True

    if closed_shape:
        xx, yy = proj(numpy.roll(lons, 1), numpy.roll(lats, 1))
        if not shapely.geometry.LineString(zip(xx, yy)).is_simple:
            return True

    return False


def get_longitudinal_extent(lon1, lon2):
    """
    Return the distance between two longitude values as an angular measure.
    Parameters represent two longitude values in degrees.

    :return:
        Float, the angle between ``lon1`` and ``lon2`` in degrees. Value
        is positive if ``lon2`` is on the east from ``lon1`` and negative
        otherwise. Absolute value of the result doesn't exceed 180 for
        valid parameters values.
    """
    return (lon2 - lon1 + 180) % 360 - 180


def get_spherical_bounding_box(lons, lats):
    """
    Given a collection of points find and return the bounding box,
    as a pair of longitudes and a pair of latitudes.

    Parameters define longitudes and latitudes of a point collection
    respectively in a form of lists or numpy arrays.

    :return:
        A tuple of four items. These items represent western, eastern,
        northern and southern borders of the bounding box respectively.
        Values are floats in decimal degrees.
    :raises ValueError:
        If points collection has the longitudinal extent of more than
        180 degrees (it is impossible to define a single hemisphere
        bound to poles that would contain the whole collection).
    """
    north, south = numpy.max(lats), numpy.min(lats)
    west, east = numpy.min(lons), numpy.max(lons)
    assert (-180 <= west <= 180) and (-180 <= east <= 180)
    if get_longitudinal_extent(west, east) < 0:
        # points are lying on both sides of the international date line
        # (meridian 180). the actual west longitude is the lowest positive
        # longitude and east one is the highest negative.
        west = min(lon for lon in lons if lon > 0)
        east = max(lon for lon in lons if lon < 0)
        if not all((get_longitudinal_extent(west, lon) >= 0
                    and get_longitudinal_extent(lon, east) >= 0)
                   for lon in lons):
            raise ValueError('points collection has longitudinal extent '
                             'wider than 180 deg')
    return west, east, north, south


def get_orthographic_projection(west, east, north, south):
    """
    Create and return a projection object for a given bounding box.

    :returns:
        Function that can perform both forward and reverse projection
        (converting from longitudes and latitudes to x and y values
        on 2d-space and vice versa). Function takes three arguments:
        first two are numpy arrays of longitudes and latitudes *or*
        abscissae and ordinates of points to project and the third one
        is a boolean that allows to choose what operation is requested --
        is it forward or reverse one. ``True`` value given to third
        positional argument (or keyword argument "reverse") indicates
        that the projection of points in 2d space back to earth surface
        is needed. The default value for "reverse" argument is ``False``,
        which means forward projection (degrees to kilometers).

        Resulting function raises ``ValueError`` in forward projection
        mode if any of the target points is further than 90 degree
        (along the great circle arc) from the projection center.

    Parameters are given as floats, representing decimal degrees (first two
    are longitudes and last two are latitudes). They define a bounding box
    in a spherical coordinates of the collection of points that is about
    to be projected. The center point of the projection (coordinates (0, 0)
    in Cartesian space) is set to the middle point of that bounding box.
    The resulting projection is defined for spherical coordinates that are
    not further from the bounding box center than 90 degree on the great
    circle arc.

    The result projection is of type `Orthographic
    <http://mathworld.wolfram.com/OrthographicProjection.html>`_.
    This projection is prone to distance, area and angle distortions
    everywhere outside of the center point, but still can be used for
    checking shapes: verifying if line intersects itself (like in
    :func:`line_intersects_itself`) or if point is inside of a polygon
    (like in :meth:`nhlib.geo.polygon.Polygon.discretize`). It can be also
    used for measuring distance to an extent of around 700 kilometers (error
    doesn't exceed 1 km up until then).
    """
    lambda0, phi0 = numpy.radians(get_middle_point(west, north, east, south))
    cos_phi0 = numpy.cos(phi0)
    sin_phi0 = numpy.sin(phi0)
    sin_pi_over_4 = (2 ** 0.5) / 2
    def proj(lons, lats, reverse=False):
        if not reverse:
            lambdas, phis = numpy.radians(lons), numpy.radians(lats)
            cos_phis = numpy.cos(phis)
            lambdas -= lambda0
            # calculate the sine of the distance between projection center
            # and each of the points to project
            sin_dist = numpy.sqrt(
                numpy.sin((phi0 - phis) / 2.0) ** 2.0
                + cos_phi0 * cos_phis * numpy.sin(lambdas / 2.0) ** 2.0
            )
            if (sin_dist > sin_pi_over_4).any():
                raise ValueError('some points are too far from the projection '
                                 'center lon=%s lat=%s' %
                                 (numpy.degrees(lambda0), numpy.degrees(phi0)))
            xx = numpy.cos(phis) * numpy.sin(lambdas)
            yy = cos_phi0 * numpy.sin(phis) \
                 - sin_phi0 * cos_phis * numpy.cos(lambdas)
            return xx * EARTH_RADIUS, yy * EARTH_RADIUS
        else:
            # "reverse" mode, arguments are actually abscissae
            # and ordinates in 2d space
            xx, yy = lons / EARTH_RADIUS, lats / EARTH_RADIUS
            cos_c = numpy.sqrt(1 - (xx ** 2 + yy ** 2))
            phis = numpy.arcsin(cos_c * sin_phi0 + yy * cos_phi0)
            lambdas = numpy.arctan2(xx, cos_phi0 * cos_c - yy * sin_phi0)
            return numpy.degrees(lambda0 + lambdas), numpy.degrees(phis)
    return proj


def get_middle_point(lon1, lat1, lon2, lat2):
    """
    Given two points return the point exactly in the middle lying on the same
    great circle arc.

    Parameters are point coordinates in degrees.

    :returns:
        Tuple of longitude and latitude of the point in the middle.
    """
    if lon1 == lon2 and lat1 == lat2:
        return lon1, lat1
    dist = geodetic.geodetic_distance(lon1, lat1, lon2, lat2)
    azimuth = geodetic.azimuth(lon1, lat1, lon2, lat2)
    return geodetic.point_at(lon1, lat1, azimuth, dist / 2.0)


def spherical_to_cartesian(lons, lats, depths):
    """
    Return the position vectors (in Cartesian coordinates) of list of spherical
    coordinates.

    For equations see: http://mathworld.wolfram.com/SphericalCoordinates.html.

    Parameters are components of spherical coordinates in a form of scalars,
    lists or numpy arrays. ``depths`` can be ``None`` in which case it's
    considered zero for all points.

    :returns:
        ``numpy.array`` of 3d vectors representing points' coordinates in
        Cartesian space. The array has the same shape as parameter arrays.
        In particular it means that if ``lons`` and ``lats`` are scalars,
        the result is a single 3d vector. Vector of length ``1`` represents
        distance of 1 km.

    See also :func:`cartesian_to_spherical`.
    """
    phi = numpy.radians(lons)
    theta = numpy.radians(lats)
    if depths is None:
        rr = EARTH_RADIUS
    else:
        rr = EARTH_RADIUS - numpy.array(depths)
    cos_theta_r = rr * numpy.cos(theta)
    xx = cos_theta_r * numpy.cos(phi)
    yy = cos_theta_r * numpy.sin(phi)
    zz = rr * numpy.sin(theta)
    vectors = numpy.array([xx.transpose(), yy.transpose(), zz.transpose()]) \
                   .transpose()
    return vectors


def cartesian_to_spherical(vectors):
    """
    Return the spherical coordinates for coordinates in Cartesian space.

    This function does an opposite to :func:`spherical_to_cartesian`.

    :param vectors:
        Array of 3d vectors in Cartesian space.
    :returns:
        Tuple of three arrays of the same shape as ``vectors`` representing
        longitude (decimal degrees), latitude (decimal degrees) and depth (km)
        in specified order.
    """
    rr = numpy.sqrt(numpy.sum(vectors * vectors, axis=-1))
    xx, yy, zz = vectors.transpose()
    xx = xx.transpose()
    yy = yy.transpose()
    zz = zz.transpose()
    lats = numpy.degrees(numpy.arcsin((zz / rr).clip(-1., 1.)))
    lons = numpy.degrees(numpy.arctan2(yy, xx))
    depths = EARTH_RADIUS - rr
    return lons, lats, depths


def triangle_area(e1, e2, e3):
    """
    Get the area of triangle formed by three vectors.

    Parameters are three three-dimensional numpy arrays representing
    vectors of triangle's edges in Cartesian space.

    :returns:
        Float number, the area of the triangle in squared units of coordinates,
        or numpy array of shape of edges with one dimension less.

    Uses Heron formula, see http://mathworld.wolfram.com/HeronsFormula.html.
    """
    # calculating edges length
    e1_length = numpy.sqrt(numpy.sum(e1 * e1, axis=-1))
    e2_length = numpy.sqrt(numpy.sum(e2 * e2, axis=-1))
    e3_length = numpy.sqrt(numpy.sum(e3 * e3, axis=-1))
    # calculating half perimeter
    s = (e1_length + e2_length + e3_length) / 2.0
    # applying Heron's formula
    return numpy.sqrt(s * (s - e1_length) * (s - e2_length) * (s - e3_length))


def normalized(vector):
    """
    Get unit vector for a given one.

    :param vector:
        Numpy vector as coordinates in Cartesian space, or an array of such.
    :returns:
        Numpy array of the same shape and structure where all vectors are
        normalized. That is, each coordinate component is divided by its
        vector's length.
    """
    length = numpy.sum(vector * vector, axis=-1)
    length = numpy.sqrt(length.reshape(length.shape + (1, )))
    return vector / length


def point_to_polygon_distance(polygon, pxx, pyy):
    """
    Calculate the distance to polygon for each point of the collection
    on the 2d Cartesian plane.

    :param polygon:
        Shapely "Polygon" geometry object.
    :param pxx:
        List or numpy array of abscissae values of points to calculate
        the distance from.
    :param pyy:
        Same structure as ``pxx``, but with ordinate values.
    :returns:
        Numpy array of distances in units of coordinate system. Points
        that lie inside the polygon have zero distance.
    """
    pxx = numpy.array(pxx)
    pyy = numpy.array(pyy)
    assert pxx.shape == pyy.shape
    if pxx.ndim == 0:
        pxx = pxx.reshape((1, ))
        pyy = pyy.reshape((1, ))
    result = numpy.array([
        polygon.distance(shapely.geometry.Point(pxx.item(i), pyy.item(i)))
        for i in xrange(pxx.size)
    ])
    return result.reshape(pxx.shape)


try:
    from nhlib.geo import _utils_speedups
except ImportError:
    # speedups extension is not available
    import warnings
    warnings.warn("geoutils speedups are not available", RuntimeWarning)
else:
    from nhlib import speedups

    def _c_point_to_polygon_distance(polygon, pxx, pyy):
        pxx = numpy.array(pxx, float)
        pyy = numpy.array(pyy, float)
        cxx, cyy = numpy.array(polygon.exterior).transpose()
        return _utils_speedups.point_to_polygon_distance(
            cxx, cyy, pxx, pyy
        )

    speedups.register(point_to_polygon_distance, _c_point_to_polygon_distance)
    del _c_point_to_polygon_distance
