import os
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name = "openquake",
    version = "0.6.1",
    author = "The OpenQuake team",
    author_email = "info@openquake.org",
    description = ("Computes hazard, risk and socio-economic impact of "
                   "earthquakes."),
    license = "AGPL3",
    keywords = "earthquake seismic hazard risk",
    url = "http://openquake.org/",
    long_description=read('README'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
    ],
    packages = find_packages(),
    include_package_data=True,
    scripts = [
        "bin/openquake", "bin/oq_create_db", "bin/oq_cache_gc",
        "bin/oq_restart_workers", "bin/oq_monitor", "bin/oq_log_sink",
        "bin/oq_check_monitors"],
)
