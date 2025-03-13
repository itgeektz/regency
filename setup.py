from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in regency/__init__.py
from regency import __version__ as version

setup(
	name="regency",
	version=version,
	description="Regency Specific Customization",
	author="Aakvatech",
	author_email="info@aakvatech.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
