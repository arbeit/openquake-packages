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
Package :mod:`nhlib.source` deals with various types of seismic sources.
"""
from nhlib.source.rupture import Rupture, ProbabilisticRupture
from nhlib.source.point import PointSource
from nhlib.source.area import AreaSource
from nhlib.source.simple_fault import SimpleFaultSource
from nhlib.source.complex_fault import ComplexFaultSource
