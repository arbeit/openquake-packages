from setuptools import setup, find_packages
setup(
    name = "python-openquake",
    version = "1.0",
    author = "The OpenQuake team",
    author_email = "info@openquake.org",
    description = ("Computes hazard, risk and socio-economic impact of "
                   "earthquakes."),
    license = "LGPL3",
    keywords = "earthquakes seismic hazard risk",
    url = "http://openquake.org/",
    packages = find_packages(),
)
