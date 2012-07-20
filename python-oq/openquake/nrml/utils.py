# Copyright (c) 2010-2012, GEM Foundation.
#
# NRML is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# NRML is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with NRML.  If not, see <http://www.gnu.org/licenses/>.


"""NRML utilities"""

import os

NRML_SCHEMA_FILE = 'nrml.xsd'


def nrml_schema_file():
    """Returns the absolute path to the NRML schema file"""
    return os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'schema', NRML_SCHEMA_FILE)
