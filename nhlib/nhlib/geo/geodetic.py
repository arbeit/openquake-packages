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
Module :mod:`nhlib.geo.geodetic` contains functions for geodetic
transformations, optimized for massive calculations.
"""
import numpy


#: Earth radius in km.
EARTH_RADIUS = 6371.0


def geodetic_distance(lons1, lats1, lons2, lats2):
    """
    Calculate the geodetic distance between two points or two collections
    of points.

    Parameters are coordinates in decimal degrees. They could be scalar
    float numbers or numpy arrays, in which case they should "broadcast
    together".

    Implements http://williams.best.vwh.net/avform.htm#Dist

    :returns:
        Distance in km, floating point scalar or numpy array of such.
    """
    lons1 = numpy.radians(lons1)
    lats1 = numpy.radians(lats1)
    assert lons1.shape == lats1.shape
    lons2 = numpy.radians(lons2)
    lats2 = numpy.radians(lats2)
    assert lons2.shape == lats2.shape
    distance = numpy.arcsin(numpy.sqrt(
        numpy.sin((lats1 - lats2) / 2.0) ** 2.0
        + numpy.cos(lats1) * numpy.cos(lats2)
          * numpy.sin((lons1 - lons2) / 2.0) ** 2.0
    ).clip(-1., 1.))
    return (2.0 * EARTH_RADIUS) * distance


def azimuth(lons1, lats1, lons2, lats2):
    """
    Calculate the azimuth between two points or two collections of points.

    Parameters are the same as for :func:`geodetic_distance`.

    Implements an "alternative formula" from
    http://williams.best.vwh.net/avform.htm#Crs

    :returns:
        Azimuth as an angle between direction to north from first point and
        direction to the second point measured clockwise in decimal degrees.
    """
    lons1 = numpy.radians(lons1)
    lats1 = numpy.radians(lats1)
    assert lons1.shape == lats1.shape
    lons2 = numpy.radians(lons2)
    lats2 = numpy.radians(lats2)
    assert lons2.shape == lats2.shape
    cos_lat2 = numpy.cos(lats2)
    true_course = numpy.degrees(numpy.arctan2(
        numpy.sin(lons1 - lons2) * cos_lat2,
        numpy.cos(lats1) * numpy.sin(lats2)
        - numpy.sin(lats1) * cos_lat2 * numpy.cos(lons1 - lons2)
    ))
    return (360 - true_course) % 360


def distance(lons1, lats1, depths1, lons2, lats2, depths2):
    """
    Calculate a distance between two points (or collections of points)
    considering points' depth.

    Calls :func:`geodetic_distance`, finds the "vertical" distance between
    points by subtracting one depth from another and combine both using
    Pythagoras theorem.

    :returns:
        Distance in km, a square root of sum of squares of :func:`geodetic
        <geodetic_distance>` distance and vertical distance, which is just
        a difference between depths.
    """
    hdist = geodetic_distance(lons1, lats1, lons2, lats2)
    vdist = depths1 - depths2
    return numpy.sqrt(hdist ** 2 + vdist ** 2)


def min_distance(mlons, mlats, mdepths, slons, slats, sdepths):
    """
    Calculate the minimum distance between a collection of points and a point.

    This function allows to calculate a closest distance to a collection
    of points for each point in another collection. Both collection can be
    of any shape, although it doesn't make sense to use scalars for the first
    one.

    Implements the same formula as in :func:`geodetic_distance` for distance
    along great circle arc and the same approach as in :func:`distance`
    for combining it with depth distance.

    :param array mlons, mlats, mdepths:
        Numpy arrays of the same shape representing a first collection
        of points, the one distance to which is of interest -- longitudes,
        latitudes (both in decimal degrees) and depths (in km).
    :param array slons, slats, sdepths:
        Scalars, python lists or tuples or numpy arrays of the same shape,
        representing a second collection: a list of points to find a minimum
        distance from for.
    :returns:
        Minimum distance in km, a scalar if ``slons``, ``slats``
        and ``sdepths`` are scalars and numpy array of the same shape
        of those three otherwise.
    """
    assert mlons.shape == mlats.shape == mdepths.shape
    slons, slats = numpy.array(slons), numpy.array(slats)
    sdepths = numpy.array(sdepths)
    assert slons.shape == slats.shape == sdepths.shape
    orig_shape = slons.shape
    mlons = numpy.radians(mlons.flat)
    mlats = numpy.radians(mlats.flat)
    mdepths = mdepths.reshape(-1)
    slons = numpy.radians(slons.flat)
    slats = numpy.radians(slats.flat)
    sdepths = sdepths.reshape(-1)
    cos_mlats = numpy.cos(mlats)
    cos_slats = numpy.cos(slats)
    distance = numpy.array([
        numpy.sqrt(numpy.min(
            # next five lines are the same as in geodetic_distance()
            (numpy.arcsin(numpy.sqrt(
                numpy.sin((mlats - slats[i]) / 2.0) ** 2.0
                + cos_mlats * cos_slats[i]
                  * numpy.sin((mlons - slons[i]) / 2.0) ** 2.0
            ).clip(-1., 1.)) * 2 * EARTH_RADIUS) ** 2
            + (mdepths - sdepths[i]) ** 2
        ))
        for i in xrange(len(slats))
    ])
    if not orig_shape:
        # original target point was a scalar, so return scalar as well
        [distance] = distance
        return distance
    else:
        return distance.reshape(orig_shape)


def intervals_between(lon1, lat1, depth1, lon2, lat2, depth2, length):
    """
    Find a list of points between two given ones that lie on the same
    great circle arc and are equally spaced by ``length`` km.

    :param float lon1, lat1, depth1:
        Coordinates of a point to start placing intervals from. The first
        point in the resulting list has these coordinates.
    :param float lon2, lat2, depth2:
        Coordinates of the other end of the great circle arc segment
        to put intervals on. The last resulting point might be closer
        to the first reference point than the second one or further,
        since the number of segments is taken as rounded division of
        length between two reference points and ``length``.
    :param length:
        Required distance between two subsequent resulting points, in km.
    :returns:
        Tuple of three 1d numpy arrays: longitudes, latitudes and depths
        of resulting points respectively.

    Rounds the distance between two reference points with respect
    to ``length`` and calls :func:`npoints_towards`.
    """
    assert length > 0
    hdist = geodetic_distance(lon1, lat1, lon2, lat2)
    vdist = depth2 - depth1
    total_distance = numpy.sqrt(hdist ** 2 + vdist ** 2)
    num_intervals = int(round(total_distance / length))
    if num_intervals == 0:
        return numpy.array([lon1]), numpy.array([lat1]), numpy.array([depth1])
    dist_factor = (length * num_intervals) / total_distance
    return npoints_towards(
        lon1, lat1, depth1, azimuth(lon1, lat1, lon2, lat2),
        hdist * dist_factor, vdist * dist_factor, num_intervals + 1
    )


def npoints_between(lon1, lat1, depth1, lon2, lat2, depth2, npoints):
    """
    Find a list of specified number of points between two given ones that are
    equally spaced along the great circle arc connecting given points.

    :param float lon1, lat1, depth1:
        Coordinates of a point to start from. The first point in a resulting
        list has these coordinates.
    :param float lon2, lat2, depth2:
        Coordinates of a point to finish at. The last point in a resulting
        list has these coordinates.
    :param npoints:
        Integer number of points to return. First and last points count,
        so if there have to be two intervals, ``npoints`` should be 3.
    :returns:
        Tuple of three 1d numpy arrays: longitudes, latitudes and depths
        of resulting points respectively.

    Finds distance between two reference points and calls
    :func:`npoints_towards`.
    """
    hdist = geodetic_distance(lon1, lat1, lon2, lat2)
    vdist = depth2 - depth1
    rlons, rlats, rdepths = npoints_towards(
        lon1, lat1, depth1, azimuth(lon1, lat1, lon2, lat2),
        hdist, vdist, npoints
    )
    # the last point should be left intact
    rlons[-1] = lon2
    rlats[-1] = lat2
    rdepths[-1] = depth2
    return rlons, rlats, rdepths


def npoints_towards(lon, lat, depth, azimuth, hdist, vdist, npoints):
    """
    Find a list of specified number of points starting from a given one
    along a great circle arc with a given azimuth measured in a given point.

    :param float lon, lat, depth:
        Coordinates of a point to start from. The first point in a resulting
        list has these coordinates.
    :param azimuth:
        A direction representing a great circle arc together with a reference
        point.
    :param hdist:
        Horizontal (geodetic) distance from reference point to the last point
        of the resulting list, in km.
    :param vdist:
        Vertical (depth) distance between reference and the last point, in km.
    :param npoints:
        Integer number of points to return. First and last points count,
        so if there have to be two intervals, ``npoints`` should be 3.
    :returns:
        Tuple of three 1d numpy arrays: longitudes, latitudes and depths
        of resulting points respectively.

    Implements "completely general but more complicated algorithm" from
    http://williams.best.vwh.net/avform.htm#LL
    """
    assert npoints > 1
    rlon, rlat = numpy.radians(lon), numpy.radians(lat)
    tc = numpy.radians(360 - azimuth)
    hdists = numpy.arange(npoints, dtype=float)
    hdists *= (hdist / EARTH_RADIUS) / (npoints - 1)
    vdists = numpy.arange(npoints, dtype=float)
    vdists *= vdist / (npoints - 1)

    sin_dists = numpy.sin(hdists)
    cos_dists = numpy.cos(hdists)
    sin_lat = numpy.sin(rlat)
    cos_lat = numpy.cos(rlat)

    sin_lats = sin_lat * cos_dists + cos_lat * sin_dists * numpy.cos(tc)
    sin_lats = sin_lats.clip(-1., 1.)
    lats = numpy.degrees(numpy.arcsin(sin_lats))

    dlon = numpy.arctan2(numpy.sin(tc) * sin_dists * cos_lat,
                         cos_dists - sin_lat * sin_lats)
    lons = numpy.mod(rlon - dlon + numpy.pi, 2 * numpy.pi) - numpy.pi
    lons = numpy.degrees(lons)

    depths = vdists + depth

    # the first point should be left intact
    lons[0] = lon
    lats[0] = lat
    depths[0] = depth

    return lons, lats, depths


def point_at(lon, lat, azimuth, distance):
    """
    Perform a forward geodetic transformation: find a point lying at a given
    distance from a given one on a great circle arc defined by azimuth.

    :param float lon, lat:
        Coordinates of a reference point, in decimal degrees.
    :param azimuth:
        An azimuth of a great circle arc of interest measured in a reference
        point in decimal degrees.
    :param distance:
        Distance to target point in km.
    :returns:
        Tuple of two float numbers: longitude and latitude of a target point
        in decimal degrees respectively.

    Implements the same approach as :func:`npoints_towards`.
    """
    # this is a simplified version of npoints_towards().
    # code duplication is justified by performance reasons.
    lon, lat = numpy.radians(lon), numpy.radians(lat)
    tc = numpy.radians(360 - azimuth)
    sin_dists = numpy.sin(distance / EARTH_RADIUS)
    cos_dists = numpy.cos(distance / EARTH_RADIUS)
    sin_lat = numpy.sin(lat)
    cos_lat = numpy.cos(lat)

    sin_lats = sin_lat * cos_dists + cos_lat * sin_dists * numpy.cos(tc)
    sin_lats = sin_lats.clip(-1., 1.)
    lats = numpy.degrees(numpy.arcsin(sin_lats))

    dlon = numpy.arctan2(numpy.sin(tc) * sin_dists * cos_lat,
                         cos_dists - sin_lat * sin_lats)
    lons = numpy.mod(lon - dlon + numpy.pi, 2 * numpy.pi) - numpy.pi
    lons = numpy.degrees(lons)

    return lons, lats


def distance_to_arc(alon, alat, aazimuth, plons, plats):
    """
    Calculate a closest distance between a great circle arc and a point
    (or a collection of points).

    :param float alon, alat:
        Arc reference point longitude and latitude, in decimal degrees.
    :param azimuth:
        Arc azimuth (an angle between direction to a north and arc in clockwise
        direction), measured in a reference point, in decimal degrees.
    :param float plons, plats:
        Longitudes and latitudes of points to measure distance. Either scalar
        values or numpy arrays of decimal degrees.
    :returns:
        Distance in km, a scalar value or numpy array depending on ``plons``
        and ``plats``. A distance is negative if the target point lies on the
        right hand side of the arc.

    Solves a spherical triangle formed by reference point, target point and
    a projection of target point to a reference great circle arc.
    """
    azimuth_to_target = azimuth(alon, alat, plons, plats)
    distance_to_target = geodetic_distance(alon, alat, plons, plats)

    # find an angle between an arc and a great circle arc connecting
    # arc's reference point and a target point
    t_angle = (azimuth_to_target - aazimuth + 360) % 360

    # in a spherical right triangle cosine of the angle of a cathetus
    # augmented to pi/2 is equal to sine of an opposite angle times
    # sine of hypotenuse, see
    # http://en.wikipedia.org/wiki/Spherical_trigonometry#Napier.27s_Pentagon
    angle = numpy.arccos(
        (numpy.sin(numpy.radians(t_angle))
         * numpy.sin(distance_to_target / EARTH_RADIUS)).clip(-1, 1)
    )
    return (numpy.pi / 2 - angle) * EARTH_RADIUS
