from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in frappe_face_recognition/__init__.py
from frappe_face_recognition import __version__ as version

setup(
	name="frappe_face_recognition",
	version=version,
	description="frappe module for doing face recognition task",
	author="Thunderlab Indonesia",
	author_email="Budi@thunderlab.id",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
