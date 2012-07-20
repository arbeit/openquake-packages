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
Module :mod:`~nhlib.calc.gmf` exports :func:`ground_motion_fields`.
"""
import numpy
import scipy.stats

from nhlib.const import StdDev
from nhlib.calc import filters


def ground_motion_fields(rupture, sites, imts, gsim, truncation_level,
                         realizations,
                         rupture_site_filter=filters.rupture_site_noop_filter):
    """
    Given an earthquake rupture, the ground motion field calculator computes
    ground shaking over a set of sites, by randomly sampling a ground shaking
    intensity model. A ground motion field represents a possible 'realization'
    of the ground shaking due to an earthquake rupture.

    .. note::
        This calculator is using random numbers. In order to reproduce the
        same results numpy random numbers generator needs to be seeded, see
        http://docs.scipy.org/doc/numpy/reference/generated/numpy.random.seed.html

    :param nhlib.source.rupture.Rupture rupture:
        Rupture to calculate ground motion fields radiated from.
    :param nhlib.site.SiteCollection sites:
        Sites of interest to calculate GMFs.
    :param imts:
        List of intensity measure type objects (see :mod:`nhlib.imt`).
    :param gsim:
        Ground-shaking intensity model, instance of subclass of either
        :class:`~nhlib.gsim.base.GMPE` or :class:`~nhlib.gsim.base.IPE`.
    :param trunctation_level:
        Float, number of standard deviations for truncation of the intensity
        distribution, or ``None``.
    :param realizations:
        Integer number of GMF realizations to compute.
    :param rupture_site_filter:
        Optional rupture-site filter function. See :mod:`nhlib.calc.filters`.

    :returns:
        Dictionary mapping intensity measure type objects (same
        as in parameter ``imts``) to 2d numpy arrays of floats,
        representing different realizations of ground shaking intensity
        for all sites in the collection. First dimension represents
        sites and second one is for realizations.
    """
    ruptures_sites = list(rupture_site_filter([(rupture, sites)]))
    if not ruptures_sites:
        return dict((imt, numpy.zeros((len(sites), realizations)))
                    for imt in imts)

    total_sites = len(sites)
    [(rupture, sites)] = ruptures_sites

    sctx, rctx, dctx = gsim.make_contexts(sites, rupture)
    result = {}

    if truncation_level == 0:
        for imt in imts:
            mean, _stddevs = gsim.get_mean_and_stddevs(sctx, rctx, dctx, imt,
                                                       stddev_types=[])
            mean.shape += (1, )
            mean = mean.repeat(realizations, axis=1)
            result[imt] = sites.expand(mean, total_sites, placeholder=0)
        return result

    if truncation_level is None:
        distribution = scipy.stats.norm()
    else:
        assert truncation_level > 0
        distribution = scipy.stats.truncnorm(- truncation_level,
                                             truncation_level)

    for imt in imts:
        mean, [stddev_inter, stddev_intra] = gsim.get_mean_and_stddevs(
            sctx, rctx, dctx, imt, [StdDev.INTER_EVENT, StdDev.INTRA_EVENT]
        )
        stddev_intra.shape += (1, )
        stddev_inter.shape += (1, )
        mean.shape += (1, )
        intra_residual = stddev_intra * distribution.rvs(size=realizations)
        inter_residual = stddev_inter * distribution.rvs(size=(len(sites),
                                                               realizations))
        gmf = mean + intra_residual + inter_residual
        result[imt] = sites.expand(gmf, total_sites, placeholder=0)

    return result
