from setuptools import find_packages, setup

with open("README.md") as fh:
    long_description = fh.read()

setup(
    name="easyeda2kicad",
    description="A Python script that convert any electronic components from LCSC or EasyEDA to a Kicad library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    version="0.2.0",
    author="uPesy",
    author_email="contact@upesy.com",
    url="https://github.com/uPesy/easyeda2kicad.py",
    project_urls={
        "Code": "https://github.com/uPesy/easyeda2kicad.py",
    },
    # download_url='',
    license="AGPL-3.0",
    py_modules=["easyeda2kicad"],
    platforms="any",
    packages=find_packages(exclude=["tests", "utils"]),
    package_dir={"easyeda2kicad": "easyeda2kicad"},
    entry_points={"console_scripts": ["easyeda2kicad = easyeda2kicad.__main__:main"]},
    python_requires=">=3.6",
    install_requires=["pydantic"],
    extras_require={"dev": ["pre-commit"]},
    zip_safe=False,
    keywords="easyeda kicad library conversion",
    classifiers=[
        # More information at https://pypi.org/classifiers/.
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
    ],
)
