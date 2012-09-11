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
:mod:`nhlib.calc.stochastic` contains :func:`stochastic_event_set_poissonian`.
"""
from nhlib.tom import PoissonTOM


def stochastic_event_set_poissonian(sources, time_span):
    """
    The Poissonian Stochastic Event Set calculator generates a 'Stochastic
    Event Set' (that is a collection of earthquake ruptures) by randomly
    sampling a source model whose rupture follow a Poissonian temporal
    occurrence model. The Stochastic Event Set represent a possible
    *realization* of the seismicity as described by the source model,
    in the given time span.

    The calculator assumes :class:`Poissonian <nhlib.tom.PoissonTOM>`
    temporal occurrence model.

    :param sources:
        An iterator of seismic sources objects (instances of subclasses
        of :class:`~nhlib.source.base.SeismicSource`).
    :param time_span:
        An investigation period for Poissonian temporal occurrence model,
        floating point number in years.

    :returns:
        Generator of :class:`~nhlib.source.rupture.Rupture` objects that
        are contained in an event set. Some ruptures can be missing from
        it, others can appear one or more times in a row.
    """
    tom = PoissonTOM(time_span)

    for source in sources:
        for rupture in source.iter_ruptures(tom):
            for i in xrange(rupture.sample_number_of_occurrences()):
                yield rupture
