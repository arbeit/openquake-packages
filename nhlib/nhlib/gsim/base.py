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
Module :mod:`nhlib.gsim.base` defines base classes for different kinds
of :class:`ground shaking intensity models <GroundShakingIntensityModel>`.
"""
from __future__ import division

import abc
import math

import scipy.stats
from scipy.special import ndtr
import numpy

from nhlib import const
from nhlib import imt as imt_module


class GroundShakingIntensityModel(object):
    """
    Base class for all the ground shaking intensity models.

    A Ground Shaking Intensity Model (GSIM) defines a set of equations
    for computing mean and standard deviation of a Normal distribution
    representing the variability of an intensity measure (or of its logarithm)
    at a site given an earthquake rupture.

    This class is not intended to be subclassed directly, instead
    the actual GSIMs should subclass either :class:`GMPE` or :class:`IPE`.

    Subclasses of both must implement :meth:`get_mean_and_stddevs`
    and all the class attributes with names starting from ``DEFINED_FOR``
    and ``REQUIRES``.
    """
    __metaclass__ = abc.ABCMeta

    #: Reference to a :class:`tectonic region type <nhlib.const.TRT>` this GSIM
    #: is defined for. One GSIM can implement only one tectonic region type.
    DEFINED_FOR_TECTONIC_REGION_TYPE = abc.abstractproperty()

    #: Set of :mod:`intensity measure types <nhlib.imt>` this GSIM can
    #: calculate. A set should contain classes from module :mod:`nhlib.imt`.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = abc.abstractproperty()

    #: Reference to a :class:`intensity measure component type
    #: <nhlib.const.IMC>` this GSIM can calculate mean and standard
    #: deviation for.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = abc.abstractproperty()

    #: Set of :class:`standard deviation types <nhlib.const.StdDev>`
    #: this GSIM can calculate.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = abc.abstractproperty()

    #: Set of site parameters names this GSIM needs. The set should include
    #: strings that match names of the attributes of a :class:`site
    #: <nhlib.site.Site>` object. Those attributes are then available in the
    #: :class:`SitesContext` object with the same names.
    REQUIRES_SITES_PARAMETERS = abc.abstractproperty()

    #: Set of rupture parameters (excluding distance information) required
    #: by GSIM. Supported parameters are:
    #:
    #: ``mag``
    #:     Magnitude of the rupture.
    #: ``dip``
    #:     Rupture's surface dip angle in decimal degrees.
    #: ``rake``
    #:     Angle describing the slip propagation on the rupture surface,
    #:     in decimal degrees. See :mod:`~nhlib.geo.nodalplane` for more
    #:     detailed description of dip and rake.
    #: ``ztor``
    #:     Depth of rupture's top edge in km. See
    #:     :meth:`~nhlib.geo.surface.base.BaseSurface.get_top_edge_depth`.
    #:
    #: These parameters are available from the :class:`RuptureContext` object
    #: attributes with same names.
    REQUIRES_RUPTURE_PARAMETERS = abc.abstractproperty()

    #: Set of types of distance measures between rupture and sites. Possible
    #: values are:
    #:
    #: ``rrup``
    #:     Closest distance to rupture surface.
    #:     See :meth:`~nhlib.geo.surface.base.BaseSurface.get_min_distance`.
    #: ``rjb``
    #:     Distance to rupture's surface projection. See
    #:     :meth:`~nhlib.geo.surface.base.BaseSurface.get_joyner_boore_distance`.
    #: ``rx``
    #:     Perpendicular distance to rupture top edge projection.
    #:     See :meth:`~nhlib.geo.surface.base.BaseSurface.get_rx_distance`.
    #:
    #: All the distances are available from the :class:`DistancesContext`
    #: object attributes with same names. Values are in kilometers.
    REQUIRES_DISTANCES = abc.abstractproperty()

    @abc.abstractmethod
    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        Calculate and return mean value of intensity distribution and it's
        standard deviation.

        Method must be implemented by subclasses.

        :param sites:
            Instance of :class:`SitesContext` with parameters of sites
            collection assigned to respective values as numpy arrays.
            Only those attributes that are listed in class'
            :attr:`REQUIRES_SITES_PARAMETERS` set are available.
        :param rup:
            Instance of :class:`RuptureContext` with parameters of a rupture
            assigned to respective values. Only those attributes that are
            listed in class' :attr:`REQUIRES_RUPTURE_PARAMETERS` set are
            available.
        :param dists:
            Instance of :class:`DistancesContext` with values of distance
            measures between the rupture and each site of the collection
            assigned to respective values as numpy arrays. Only those
            attributes that are listed in class' :attr:`REQUIRES_DISTANCES`
            set are available.
        :param imt:
            An instance (not a class) of intensity measure type.
            See :mod:`nhlib.imt`.
        :param stddev_types:
            List of standard deviation types, constants from
            :class:`nhlib.const.StdDev`. Method result value should include
            standard deviation values for each of types in this list.

        :returns:
            Method should return a tuple of two items. First item should be
            a numpy array of floats -- mean values of respective component
            of a chosen intensity measure type, and the second should be
            a list of numpy arrays of standard deviation values for the same
            single component of the same single intensity measure type, one
            array for each type in ``stddev_types`` parameter, preserving
            the order.

        Combining interface to mean and standard deviation values in a single
        method allows to avoid redoing the same intermediate calculations
        if there are some shared between stddev and mean formulae without
        resorting to keeping any sort of internal state (and effectively
        making GSIM not reenterable).

        However it is advised to split calculation of mean and stddev values
        and make ``get_mean_and_stddevs()`` just combine both (and possibly
        compute interim steps).
        """

    def get_poes(self, sctx, rctx, dctx, imt, imls, truncation_level):
        """
        Calculate and return probabilities of exceedance (PoEs) of one or more
        intensity measure levels (IMLs) of one intensity measure type (IMT)
        for one or more pairs "site -- rupture".

        :param sctx:
            An instance of :class:`SitesContext` with sites information
            to calculate PoEs on.
        :param rctx:
            An instance of :class:`RuptureContext` with a single rupture
            information.
        :param dctx:
            An instance of :class:`DistancesContext` with information about
            the distances between sites and a rupture.

            All three contexts (``sctx``, ``rctx`` and ``dctx``) must conform
            to each other. The easiest way to get them is to call
            :meth:`make_contexts`.
        :param imt:
            An intensity measure type object (that is, an instance of one
            of classes from :mod:`nhlib.imt`).
        :param imls:
            List of interested intensity measure levels (of type ``imt``).
        :param truncation_level:
            Can be ``None``, which means that the distribution of intensity
            is treated as Gaussian distribution with possible values ranging
            from minus infinity to plus infinity.

            When set to zero, the mean intensity is treated as an exact
            value (standard deviation is not even computed for that case)
            and resulting array contains 0 in places where IMT is strictly
            lower than the mean value of intensity and 1.0 where IMT is equal
            or greater.

            When truncation level is positive number, the intensity
            distribution is processed as symmetric truncated Gaussian with
            range borders being ``mean - truncation_level * stddev`` and
            ``mean + truncation_level * stddev``. That is, the truncation
            level expresses how far the range borders are from the mean
            value and is defined in units of sigmas. The resulting PoEs
            for that mode are values of complementary cumulative distribution
            function of that truncated Gaussian applied to IMLs.

        :returns:
            A dictionary of the same structure as parameter ``imts`` (see
            above). Instead of lists of IMLs values of the dictionaries
            have 2d numpy arrays of corresponding PoEs, first dimension
            represents sites and the second represents IMLs.

        :raises ValueError:
            If truncation level is not ``None`` and neither non-negative
            float number, and if ``imts`` dictionary contain wrong or
            unsupported IMTs (see :attr:`DEFINED_FOR_INTENSITY_MEASURE_TYPES`).
        """
        if truncation_level is not None and truncation_level < 0:
            raise ValueError('truncation level must be zero, positive number '
                             'or None')
        self._check_imt(imt)

        if truncation_level == 0:
            # zero truncation mode, just compare imls to mean
            imls = self.to_distribution_values(imls)
            mean, _ = self.get_mean_and_stddevs(sctx, rctx, dctx, imt, [])
            mean = mean.reshape(mean.shape + (1, ))
            return (imls <= mean).astype(float)
        else:
            # use real normal distribution
            assert (const.StdDev.TOTAL
                    in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES)
            imls = self.to_distribution_values(imls)
            mean, [stddev] = self.get_mean_and_stddevs(sctx, rctx, dctx, imt,
                                                       [const.StdDev.TOTAL])
            mean = mean.reshape(mean.shape + (1, ))
            stddev = stddev.reshape(stddev.shape + (1, ))
            values = (imls - mean) / stddev
            if truncation_level is None:
                return _norm_sf(values)
            else:
                return _truncnorm_sf(truncation_level, values)

    def disaggregate_poe(self, sctx, rctx, dctx, imt, iml,
                         truncation_level, n_epsilons):
        """
        Disaggregate (separate) PoE of ``iml`` in different contributions
        each coming from ``n_epsilons`` distribution bins.

        If ``truncation_level = 3``, ``n_epsilons = 3``, bin edges are
        ``-3 .. -1``, ``-1 .. +1`` and ``+1 .. +3``.

        :param n_epsilons:
            Integer number of bins to split truncated Gaussian distribution to.

        Other parameters are the same as for :meth:`get_poes`, with
        differences that ``iml`` is only one single intensity level
        and ``truncation_level`` is required to be positive.

        :returns:
            Contribution to probability of exceedance of ``iml`` coming
            from different sigma bands in a form of 1d numpy array with
            ``n_epsilons`` floats between 0 and 1.
        """
        if not truncation_level > 0:
            raise ValueError('truncation level must be positive')
        self._check_imt(imt)

        # compute mean and standard deviations
        mean, [stddev] = self.get_mean_and_stddevs(sctx, rctx, dctx, imt,
                                                   [const.StdDev.TOTAL])

        # compute iml value with respect to standard (mean=0, std=1)
        # normal distributions
        iml = self.to_distribution_values(iml)
        standard_imls = (iml - mean) / stddev

        distribution = scipy.stats.truncnorm(- truncation_level,
                                             truncation_level)
        epsilons = numpy.linspace(- truncation_level, truncation_level,
                                  n_epsilons + 1)
        # compute epsilon bins contributions
        contribution_by_bands = distribution.cdf(epsilons[1:]) \
                                - distribution.cdf(epsilons[:-1])

        # take the minimum epsilon larger than standard_iml
        iml_bin_indices = numpy.searchsorted(epsilons, standard_imls)

        return numpy.array([
            # take full disaggregated distribution for the case of
            # ``iml <= mean - truncation_level * stddev``
            contribution_by_bands
            if idx <= 0 else

            # take zeros if ``iml >= mean + truncation_level * stddev``
            numpy.zeros(n_epsilons)
            if idx >= n_epsilons else

            # for other cases (when ``iml`` falls somewhere in the
            # histogram):
            numpy.concatenate((
                # take zeros for bins that are on the left hand side
                # from the bin ``iml`` falls into,
                numpy.zeros(idx - 1),
                # ... area of the portion of the bin containing ``iml``
                # (the portion is limited on the left hand side by
                # ``iml`` and on the right hand side by the bin edge),
                [distribution.sf(standard_imls[i])
                 - contribution_by_bands[idx:].sum()],
                # ... and all bins on the right go unchanged.
                contribution_by_bands[idx:]
            ))

            for i, idx in enumerate(iml_bin_indices)
        ])

    @abc.abstractmethod
    def to_distribution_values(self, values):
        """
        Convert a list or array of values in units of IMT to a numpy array
        of values of intensity measure distribution (like taking the natural
        logarithm for :class:`GMPE`).

        This method is implemented by both :class:`GMPE` and :class:`IPE`
        so there is no need to override it in actual GSIM implementations.
        """

    @abc.abstractmethod
    def to_imt_unit_values(self, values):
        """
        Convert a list or array of values of intensity measure distribution
        (like ones returned from :meth:`get_mean_and_stddevs`) to values
        in units of IMT. This is the opposite operation
        to :meth:`to_distribution_values`.

        This method is implemented by both :class:`GMPE` and :class:`IPE`
        so there is no need to override it in actual GSIM implementations.
        """

    def make_contexts(self, site_collection, rupture):
        """
        Create context objects for given site collection and rupture.

        :param site_collection:
            Instance of :class:`nhlib.site.SiteCollection`.
        :param rupture:
            Instance of :class:`~nhlib.source.rupture.Rupture` (or its subclass
            :class:`~nhlib.source.rupture.ProbabilisticRupture`).

        :returns:
            Tuple of three items: sites context, rupture context and
            distances context, that is, instances of :class:`SitesContext`,
            :class:`RuptureContext` and :class:`DistancesContext` in a specified
            order. Only those values that are required by GSIM are filled in
            in contexts.

        :raises ValueError:
            If any of declared required parameters (that includes site, rupture
            and distance parameters) is unknown.
        """
        dctx = DistancesContext()
        for param in self.REQUIRES_DISTANCES:
            if param == 'rrup':
                dist = rupture.surface.get_min_distance(site_collection.mesh)
            elif param == 'rx':
                dist = rupture.surface.get_rx_distance(site_collection.mesh)
            elif param == 'rjb':
                dist = rupture.surface.get_joyner_boore_distance(
                    site_collection.mesh
                )
            elif param == 'rhypo':
                dist = rupture.hypocenter.distance_to_mesh(
                    site_collection.mesh
                )
            elif param == 'repi':
                dist = rupture.hypocenter.distance_to_mesh(
                    site_collection.mesh, with_depths=False
                )
            else:
                raise ValueError('%s requires unknown distance measure %r' %
                                 (type(self).__name__, param))
            setattr(dctx, param, dist)

        sctx = SitesContext()
        for param in self.REQUIRES_SITES_PARAMETERS:
            try:
                value = getattr(site_collection, param)
            except AttributeError:
                raise ValueError('%s requires unknown site parameter %r' %
                                 (type(self).__name__, param))
            setattr(sctx, param, value)

        rctx = RuptureContext()
        for param in self.REQUIRES_RUPTURE_PARAMETERS:
            if param == 'mag':
                value = rupture.mag
            elif param == 'dip':
                value = rupture.surface.get_dip()
            elif param == 'rake':
                value = rupture.rake
            elif param == 'ztor':
                value = rupture.surface.get_top_edge_depth()
            elif param == 'hypo_depth':
                value = rupture.hypocenter.depth
            elif param == 'width':
                value = rupture.surface.get_width()
            else:
                raise ValueError('%s requires unknown rupture parameter %r' %
                                 (type(self).__name__, param))
            setattr(rctx, param, value)

        return sctx, rctx, dctx

    def _check_imt(self, imt):
        """
        Make sure that ``imt`` is valid and is supported by this GSIM.
        """
        if not issubclass(type(imt), imt_module._IMT):
            raise ValueError('imt must be an instance of IMT subclass')
        if not type(imt) in self.DEFINED_FOR_INTENSITY_MEASURE_TYPES:
            raise ValueError('imt %s is not supported by %s' %
                             (type(imt).__name__, type(self).__name__))


def _truncnorm_sf(truncation_level, values):
    """
    Survival function for truncated normal distribution.

    Assumes zero mean, standard deviation equal to one and symmetric
    truncation.

    :param truncation_level:
        Positive float number representing the truncation on both sides
        around the mean, in units of sigma.
    :param values:
        Numpy array of values as input to a survival function for the given
        distribution.
    :returns:
        Numpy array of survival function results in a range between 0 and 1.

    >>> from scipy.stats import truncnorm
    >>> truncnorm(-3, 3).sf(0.12345) == _truncnorm_sf(3, 0.12345)
    True
    """
    # notation from http://en.wikipedia.org/wiki/Truncated_normal_distribution.
    # given that mu = 0 and sigma = 1, we have alpha = a and beta = b.

    # "CDF" in comments refers to cumulative distribution function
    # of non-truncated distribution with that mu and sigma values.

    # assume symmetric truncation, that is ``a = - truncation_level``
    # and ``b = + truncation_level``.

    # calculate CDF of b
    phi_b = ndtr(truncation_level)

    # calculate Z as ``Z = CDF(b) - CDF(a)``, here we assume that
    # ``CDF(a) == CDF(- truncation_level) == 1 - CDF(b)``
    z = phi_b * 2 - 1

    # calculate the result of survival function of ``values``,
    # and restrict it to the interval where probability is defined --
    # 0..1. here we use some transformations of the original formula
    # that is ``SF(x) = 1 - (CDF(x) - CDF(a)) / Z`` in order to minimize
    # number of arithmetic operations and function calls:
    # ``SF(x) = (Z - CDF(x) + CDF(a)) / Z``,
    # ``SF(x) = (CDF(b) - CDF(a) - CDF(x) + CDF(a)) / Z``,
    # ``SF(x) = (CDF(b) - CDF(x)) / Z``.
    return ((phi_b - ndtr(values)) / z).clip(0.0, 1.0)


def _norm_sf(values):
    """
    Survival function for normal distribution.

    Assumes zero mean and standard deviation equal to one.

    ``values`` parameter and the return value are the same
    as in :func:`_truncnorm_sf`.

    >>> from scipy.stats import norm
    >>> norm.sf(0.12345) == _norm_sf(0.12345)
    True
    """
    # survival function by definition is ``SF(x) = 1 - CDF(x)``,
    # which is equivalent to ``SF(x) = CDF(- x)``, since (given
    # that the normal distribution is symmetric with respect to 0)
    # the integral between ``[x, +infinity]`` (that is the survival
    # function) is equal to the integral between ``[-infinity, -x]``
    # (that is the CDF at ``- x``).
    return ndtr(- values)


class GMPE(GroundShakingIntensityModel):
    """
    Ground-Motion Prediction Equation is a subclass of generic
    :class:`GroundShakingIntensityModel` with a distinct feature
    that the intensity values are log-normally distributed.

    Method :meth:`~GroundShakingIntensityModel.get_mean_and_stddevs`
    of actual GMPE implementations is supposed to return the mean
    value as a natural logarithm of intensity.
    """
    def to_distribution_values(self, values):
        """
        Returns numpy array of natural logarithms of ``values``.
        """
        return numpy.log(values)

    def to_imt_unit_values(self, values):
        """
        Returns numpy array of exponents of ``values``.
        """
        return numpy.exp(values)


class IPE(GroundShakingIntensityModel):
    """
    Intensity Prediction Equation is a subclass of generic
    :class:`GroundShakingIntensityModel` which is suitable for
    intensity measures that are normally distributed. In particular,
    for :class:`~nhlib.imt.MMI`.
    """
    def to_distribution_values(self, values):
        """
        Returns numpy array of ``values`` without any conversion.
        """
        return numpy.array(values, dtype=float)

    def to_imt_unit_values(self, values):
        """
        Returns numpy array of ``values`` without any conversion.
        """
        return numpy.array(values, dtype=float)


class SitesContext(object):
    """
    Sites calculation context for ground shaking intensity models.

    Instances of this class are passed into
    :meth:`GroundShakingIntensityModel.get_mean_and_stddevs`. They are
    intended to represent relevant features of the sites collection.
    Every GSIM class is required to declare what :attr:`sites parameters
    <GroundShakingIntensityModel.REQUIRES_SITES_PARAMETERS>` does it need.
    Only those required parameters are made available in a result context
    object.
    """
    __slots__ = ('vs30', 'vs30measured', 'z1pt0', 'z2pt5')


class DistancesContext(object):
    """
    Distances context for ground shaking intensity models.

    Instances of this class are passed into
    :meth:`GroundShakingIntensityModel.get_mean_and_stddevs`. They are
    intended to represent relevant distances between sites from the collection
    and the rupture. Every GSIM class is required to declare what
    :attr:`distance measures <GroundShakingIntensityModel.REQUIRES_DISTANCES>`
    does it need. Only those required values are calculated and made available
    in a result context object.
    """
    __slots__ = ('rrup', 'rx', 'rjb', 'rhypo', 'repi')


class RuptureContext(object):
    """
    Rupture calculation context for ground shaking intensity models.

    Instances of this class are passed into
    :meth:`GroundShakingIntensityModel.get_mean_and_stddevs`. They are
    intended to represent relevant features of a single rupture. Every
    GSIM class is required to declare what :attr:`rupture parameters
    <GroundShakingIntensityModel.REQUIRES_RUPTURE_PARAMETERS>` does it need.
    Only those required parameters are made available in a result context
    object.
    """
    __slots__ = ('mag', 'dip', 'rake', 'ztor', 'hypo_depth', 'width')


class CoeffsTable(object):
    r"""
    Instances of :class:`CoeffsTable` encapsulate tables of coefficients
    corresponding to different IMTs.

    Tables are defined in a space-separated tabular form in a simple string
    literal (heading and trailing whitespace does not matter). The first column
    in the table must be named "IMT" (or "imt") and thus should represent IMTs:

    >>> CoeffsTable(table='''imf z
    ...                      pga 1''')
    Traceback (most recent call last):
        ...
    ValueError: first column in a table must be IMT

    Names of other columns are used as coefficients dicts keys. The values
    in the first column should correspond to real intensity measure types,
    see :mod:`nhlib.imt`:

    >>> CoeffsTable(table='''imt  z
    ...                      pgx  2''')
    Traceback (most recent call last):
        ...
    ValueError: unknown IMT 'PGX'

    Note that :class:`CoeffsTable` only accepts keyword argumets:

    >>> CoeffsTable()
    Traceback (most recent call last):
        ...
    TypeError: CoeffsTable requires "table" kwarg
    >>> CoeffsTable(table='', foo=1)
    Traceback (most recent call last):
        ...
    TypeError: CoeffsTable got unexpected kwargs: {'foo': 1}

    If there are :class:`~nhlib.imt.SA` IMTs in the table, they are not
    referenced by name, because they require parametrization:

    >>> CoeffsTable(table='''imt  x
    ...                      sa   15''')
    Traceback (most recent call last):
        ...
    ValueError: specify period as float value to declare SA IMT
    >>> CoeffsTable(table='''imt  x
    ...                      0.1  20''')
    Traceback (most recent call last):
        ...
    TypeError: attribute "sa_damping" is required for tables defining SA

    So proper table defining SA looks like this:

    >>> ct = CoeffsTable(sa_damping=5, table='''
    ...     imt   a    b     c   d
    ...     pga   1    2.4  -5   0.01
    ...     pgd  7.6  12     0  44.1
    ...     0.1  10   20    30  40
    ...     1.0   1    2     3   4
    ...     10    2    4     6   8
    ... ''')

    Table objects could be indexed by IMT objects (this returns a dictionary
    of coefficients):

    >>> from nhlib import imt
    >>> ct[imt.PGA()] == dict(a=1, b=2.4, c=-5, d=0.01)
    True
    >>> ct[imt.PGD()] == dict(a=7.6, b=12, c=0, d=44.1)
    True
    >>> ct[imt.SA(damping=5, period=0.1)] == dict(a=10, b=20, c=30, d=40)
    True
    >>> ct[imt.PGV()]
    Traceback (most recent call last):
        ...
    KeyError: PGV()
    >>> ct[imt.SA(1.0, 4)]
    Traceback (most recent call last):
        ...
    KeyError: SA(period=1.0, damping=4)

    Table of coefficients for spectral acceleration could be indexed
    by instances of :class:`nhlib.imt.SA` with period value that is not specified
    in the table. The coefficients then get interpolated between the ones for
    closest higher and closest lower period. That scaling of coefficients works
    in a logarithmic scale of periods and only within the same damping:

    >>> '%.5f' % ct[imt.SA(period=0.2, damping=5)]['a']
    '7.29073'
    >>> '%.5f' % ct[imt.SA(period=0.9, damping=5)]['c']
    '4.23545'
    >>> '%.5f' % ct[imt.SA(period=5, damping=5)]['c']
    '5.09691'
    >>> ct[imt.SA(period=0.9, damping=15)]
    Traceback (most recent call last):
        ...
    KeyError: SA(period=0.9, damping=15)

    Extrapolation is not possible:

    >>> ct[imt.SA(period=0.01, damping=5)]
    Traceback (most recent call last):
        ...
    KeyError: SA(period=0.01, damping=5)
    """
    def __init__(self, **kwargs):
        if not 'table' in kwargs:
            raise TypeError('CoeffsTable requires "table" kwarg')
        table = kwargs.pop('table').strip().splitlines()
        sa_damping = kwargs.pop('sa_damping', None)
        if kwargs:
            raise TypeError('CoeffsTable got unexpected kwargs: %r' % kwargs)
        header = table.pop(0).split()
        if not header[0].upper() == "IMT":
            raise ValueError('first column in a table must be IMT')
        coeff_names = header[1:]
        self.sa_coeffs = {}
        self.non_sa_coeffs = {}
        for row in table:
            row = row.split()
            imt_name = row[0].upper()
            if imt_name == 'SA':
                raise ValueError('specify period as float value '
                                 'to declare SA IMT')
            imt_coeffs = dict(zip(coeff_names, map(float, row[1:])))
            try:
                sa_period = float(imt_name)
            except:
                if not hasattr(imt_module, imt_name):
                    raise ValueError('unknown IMT %r' % imt_name)
                imt = getattr(imt_module, imt_name)()
                self.non_sa_coeffs[imt] = imt_coeffs
            else:
                if sa_damping is None:
                    raise TypeError('attribute "sa_damping" is required '
                                    'for tables defining SA')
                imt = imt_module.SA(sa_period, sa_damping)
                self.sa_coeffs[imt] = imt_coeffs

    def __getitem__(self, imt):
        """
        Return a dictionary of coefficients corresponding to ``imt``
        from this table (if there is a line for requested IMT in it),
        or the dictionary of interpolated coefficients, if ``imt``
        is of type :class:`~nhlib.imt.SA` and interpolation is possible.

        :raises KeyError:
            If ``imt`` is not available in the table and no interpolation
            can be done.
        """
        if not isinstance(imt, imt_module.SA):
            return self.non_sa_coeffs[imt]

        try:
            return self.sa_coeffs[imt]
        except KeyError:
            pass

        max_below = min_above = None
        for unscaled_imt in self.sa_coeffs.keys():
            if unscaled_imt.damping != imt.damping:
                continue
            if unscaled_imt.period > imt.period:
                if min_above is None or unscaled_imt.period < min_above.period:
                    min_above = unscaled_imt
            elif unscaled_imt.period < imt.period:
                if max_below is None or unscaled_imt.period > max_below.period:
                    max_below = unscaled_imt
        if max_below is None or min_above is None:
            raise KeyError(imt)

        # ratio tends to 1 when target period tends to a minimum
        # known period above and to 0 if target period is close
        # to maximum period below.
        ratio = ((math.log(imt.period) - math.log(max_below.period))
                 / (math.log(min_above.period) - math.log(max_below.period)))
        max_below = self.sa_coeffs[max_below]
        min_above = self.sa_coeffs[min_above]
        return dict(
            (co, (min_above[co] - max_below[co]) * ratio + max_below[co])
            for co in max_below.keys()
        )
