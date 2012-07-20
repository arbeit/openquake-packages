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
Module :mod:`nhlib.scalerel.wc1994` implements :class:`WC1994`.
"""
from math import log10
from nhlib.scalerel.base import BaseMSR, BaseASR


class WC1994(BaseMSR, BaseASR):
    """
    Wells and Coppersmith magnitude -- rupture area relationships,
    see 1994, Bull. Seism. Soc. Am., pages 974-2002.

    Implements both magnitude-area and area-magnitude scaling relationships.
    """
    def get_median_area(self, mag, rake):
        """
        The values are a function of both magnitude and rake.

        Setting the rake to ``None`` causes their "All" rupture-types
        to be applied.
        """
        assert rake is None or -180 <= rake <= 180
        if rake is None:
            # their "All" case
            return 10.0 ** (-3.49 + 0.91 * mag)
        elif (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            # strike slip
            return 10.0 ** (-3.42 + 0.90 * mag)
        elif rake > 0:
            # thrust/reverse
            return 10.0 ** (-3.99 + 0.98 * mag)
        else:
            # normal
            return 10.0 ** (-2.87 + 0.82 * mag)

    def get_std_dev_area(self, mag, rake):
        """
        Standard deviation for WC1994. Magnitude is ignored.
        """
        assert rake is None or -180 <= rake <= 180
        if rake is None:
            # their "All" case
            return 0.24
        elif (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            # strike slip
            return 0.22
        elif rake > 0:
            # thrust/reverse
            return 0.26
        else:
            # normal
            return 0.22

    def get_std_dev_mag(self, rake):
        """
        Standard deviation on the magnitude for the WC1994 area relation.
        """
        assert rake is None or -180 <= rake <= 180
        if rake is None:
            # their "All" case
            return 0.24
        elif (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            # strike slip
            return 0.23
        elif rake > 0:
            # thrust/reverse
            return 0.25
        else:
            # normal
            return 0.25

    def get_median_mag(self, area, rake):
        """
        Return magnitude (Mw) given the area and rake.

        Setting the rake to ``None`` causes their "All" rupture-types
        to be applied.

        :param area:
            Area in square km.
        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        """
        assert rake is None or -180 <= rake <= 180
        if rake is None:
            # their "All" case
            return 4.07 + 0.98 * log10(area)
        elif (-45 <= rake <= 45) or (rake > 135) or (rake < -135):
            # strike slip
            return 3.98 + 1.02 * log10(area)
        elif rake > 0:
            # thrust/reverse
            return 4.33 + 0.90 * log10(area)
        else:
            # normal
            return 3.93 + 1.02 * log10(area)
