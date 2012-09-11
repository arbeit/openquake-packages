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
Module :mod:`nhlib.correlation` defines correlation models for spatially-\
distributed ground-shaking intensities.
"""
import abc
import numpy

from nhlib.imt import SA, PGA


class BaseCorrelationModel(object):
    """
    Base class for correlation models for spatially-distributed ground-shaking
    intensities.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_lower_triangle_correlation_matrix(self, sites, imt):
        """
        Get lower-triangle matrix as a result of Cholesky-decomposition
        of correlation matrix.

        The resulting matrix should have zeros on values above
        the main diagonal.

        The actual implementations of :class:`BaseCorrelationModel` interface
        might calculate the matrix considering site collection and IMT (like
        :class:`JB2009CorrelationModel` does) or might have it pre-constructed
        for a specific site collection and IMT, in which case they will need
        to make sure that parameters to this function match parameters that
        were used to pre-calculate decomposed correlation matrix.

        :param sites:
            :class:`~nhlib.site.SiteCollection` to create
            correlation matrix for.
        :param imt:
            Intensity measure type object, see :mod:`nhlib.imt`.
        """

    def apply_correlation(self, sites, imt, residuals):
        """
        Apply correlation to randomly sampled residuals.

        :param sites:
            :class:`~nhlib.site.SiteCollection` residuals were sampled for.
        :param imt:
            Intensity measure type object, see :mod:`nhlib.imt`.
        :param residuals:
            2d numpy array of sampled residuals, where first dimension
            represents sites (the length as ``sites`` parameter) and
            second one represents different realizations (samples).
        :returns:
            Array of the same structure and semantics as ``residuals``
            but with correlations applied.
        """
        # intra-event residual for a single relization is a product
        # of lower-triangle decomposed correlation matrix and vector
        # of N random numbers (where N is equal to number of sites).
        # we need to do that multiplication once per realization
        # with the same matrix and different vectors.
        corma = self.get_lower_triangle_correlation_matrix(sites, imt)
        return numpy.dot(corma, residuals)


class JB2009CorrelationModel(BaseCorrelationModel):
    """
    "Correlation model for spatially distributed ground-motion intensities"
    by Nirmal Jayaram and Jack W. Baker. Published in Earthquake Engineering
    and Structural Dynamics 2009; 38, pages 1687-1708.

    :param vs30_clustering:
        Boolean value to indicate whether "Case 1" or "Case 2" from page 1700
        should be applied. ``True`` value means that Vs 30 values show or are
        expected to show clustering ("Case 2"), ``False`` means otherwise.
    """
    def __init__(self, vs30_clustering):
        self.vs30_clustering = vs30_clustering
        super(JB2009CorrelationModel, self).__init__()

    def _get_correlation_matrix(self, sites, imt):
        """
        Calculate correlation matrix for a given sites collection.

        Correlation depends on spectral period, Vs 30 clustering behaviour
        and distance between sites.

        Parameters are the same as for
        :meth:`BaseCorrelationModel.get_lower_triangle_correlation_matrix`.
        """
        if isinstance(imt, SA):
            period = imt.period
        else:
            assert isinstance(imt, PGA)
            period = 0

        distances = sites.mesh.get_distance_matrix()

        # formulae are from page 1700
        if period < 1:
            if not self.vs30_clustering:
                # case 1, eq. (17)
                b = 8.5 + 17.2 * period
            else:
                # case 2, eq. (18)
                b = 40.7 - 15.0 * period
        else:
            # both cases, eq. (19)
            b = 22.0 + 3.7 * period

        # eq. (20)
        return numpy.exp((- 3.0 / b) * distances)

    def get_lower_triangle_correlation_matrix(self, sites, imt):
        """
        See :meth:`BaseCorrelationModel.get_lower_triangle_correlation_matrix`.
        """
        return numpy.linalg.cholesky(self._get_correlation_matrix(sites, imt))
