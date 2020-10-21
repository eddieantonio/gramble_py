import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="grable", 
    version="0.0.1",
    author="Patrick Littell",
    author_email="Patrick.Littell@nrc-cnrc.gc.ca",
    description="An interpreter for a simple tabular language for grammatical description",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/littell/grable",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)