import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name='amr-utils',
    version='2.0',
    scripts=[],
    author="Austin Blodgett",
    description="A toolkit of operations for AMRs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ablodge/amr-utils",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    include_package_data=True,
    package_data={'': ['resources/*.json']},
)
