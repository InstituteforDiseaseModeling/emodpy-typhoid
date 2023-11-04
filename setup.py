import setuptools
from setuptools.extension import Extension
import version

with open("README.md", "r") as fh:
    long_description = fh.read()
    ext_name = "emodpy_typhoid"

with open('requirements_2018.txt') as requirements_file:
    requirements = requirements_file.read().split("\n")

setuptools.setup(
    name=ext_name,
    version=version.__version__,
    author="Jonathan Bloedow",
    author_email="jbloedow@idmod.org",
    description="IDM's TYPHOID_SIM EMOD API support scripts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/InstituteforDiseaseModeling/emodpy-typhoid",
    packages=setuptools.find_packages(),
    include_package_data=True,
    setup_requires=['wheel'],
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)
