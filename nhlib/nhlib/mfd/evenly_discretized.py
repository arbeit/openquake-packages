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
Module :mod:`nhlib.mfd.evenly_discretized` defines an evenly discretized MFD.
"""
from nhlib.mfd.base import BaseMFD


class EvenlyDiscretizedMFD(BaseMFD):
    """
    Evenly discretized MFD is defined as a precalculated histogram.

    :param min_mag:
        Positive float value representing the middle point of the first
        bin in the histogram.
    :param bin_width:
        A positive float value -- the width of a single histogram bin.
    :param occurrence_rates:
        The list of non-negative float values representing the actual
        annual occurrence rates. The resulting histogram has as many bins
        as this list length.
    """

    PARAMETERS = ('min_mag', 'bin_width', 'occurrence_rates')

    MODIFICATIONS = set()

    def check_constraints(self):
        """
        Checks the following constraints:

        * Bin width is positive.
        * Occurrence rates list is not empty.
        * Each number in occurrence rates list is non-negative.
        * Minimum magnitude is positive.
        """
        if not self.bin_width > 0:
            raise ValueError('bin width must be positive')

        if not self.occurrence_rates:
            raise ValueError('at least one bin must be specified')

        if not all(value >= 0 for value in self.occurrence_rates):
            raise ValueError('all occurrence rates must not be negative')

        if not any(value > 0 for value in self.occurrence_rates):
            raise ValueError('at least one occurrence rate must be positive')

        if not self.min_mag >= 0:
            raise ValueError('minimum magnitude must be non-negative')

    def get_annual_occurrence_rates(self):
        """
        Returns the predefined annual occurrence rates.
        """
        return [(self.min_mag + i * self.bin_width, occurrence_rate)
                for i, occurrence_rate in enumerate(self.occurrence_rates)]

    def get_min_mag(self):
        """
        Returns the ``min_mag`` parameter.
        """
        return self.min_mag
