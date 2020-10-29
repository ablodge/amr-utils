import setuptools

with open("README.md", "r") as f:
    long_description = f.read()


setuptools.setup(
     name='amr-utils',
     version='1.0',
     scripts=[] ,
     author="Austin Blodgett",
     description="A toolkit of operations for AMRs",
     long_description=long_description,
     long_description_content_type="text/markdown",
     url="https://github.com/ablodge/amr-utils",
     packages=setuptools.find_packages(),
     classifiers=[
         "Programming Language :: Python :: 3",
     ],

 )
