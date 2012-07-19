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
Module :mod:`nhlib.const` defines various constants.
"""


class ConstantContainer(object):
    """
    Class that doesn't support instantiation.

    >>> ConstantContainer()
    Traceback (most recent call last):
        ...
    AssertionError: do not create objects ConstantContainer, \
use class properties instead
    """
    def __init__(self):
        raise AssertionError('do not create objects %s, '
                             'use class properties instead'
                             % type(self).__name__)


class TRT(ConstantContainer):
    """
    Container for constants that define some of the common Tectonic Region
    Types.
    """
    # Constant values correspond to the NRML schema definition.
    ACTIVE_SHALLOW_CRUST = 'Active Shallow Crust'
    STABLE_CONTINENTAL = 'Stable Shallow Crust'
    SUBDUCTION_INTERFACE = 'Subduction Interface'
    SUBDUCTION_INTRASLAB = 'Subduction IntraSlab'
    VOLCANIC = 'Volcanic'


class IMC(ConstantContainer):
    """
    The intensity measure component is the component of interest
    of ground shaking for an :mod:`intensity measure <nhlib.imt>`.
    """
    #: Usually defined as the geometric average of the maximum
    #: of the two horizontal components (which may not occur
    #: at the same time).
    AVERAGE_HORIZONTAL = 'Average horizontal'
    #: An orientation-independent alternative to :attr:`AVERAGE_HORIZONTAL`.
    #: Defined at Boore et al. (2006, Bull. Seism. Soc. Am. 96, 1502-1511)
    #: and is used for all the NGA GMPEs.
    GMRotI50 = 'Average Horizontal (GMRotI50)'
    #: A randomly chosen horizontal component.
    RANDOM_HORIZONTAL = 'Random horizontal'
    #: The largest value obtained from two perpendicular horizontal
    #: components.
    GREATER_OF_TWO_HORIZONTAL = 'Greater of two horizontal'
    #: The vertical component.
    VERTICAL = 'Vertical'


class StdDev(ConstantContainer):
    """
    GSIM standard deviation represents ground shaking variability at a site.
    """
    #: Standard deviation representing ground shaking variability
    #: within different events.
    INTER_EVENT = 'Inter event'
    #: Standard deviation representing ground shaking variability
    #: within a single event.
    INTRA_EVENT = 'Intra event'
    #: Total standard deviation, defined as the square root of the sum
    #: of inter- and intra-event squared standard deviations, represents
    #: the total ground shaking variability, and is the only one that
    #: is used for calculating a probability of intensity exceedance
    #: (see :meth:`nhlib.gsim.base.GroundShakingIntensityModel.get_poes`).
    TOTAL = 'Total'
