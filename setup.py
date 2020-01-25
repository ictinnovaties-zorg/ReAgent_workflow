import setuptools

with open("readme.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ReAgent_scripts", # Replace with your own username
    version="0.0.1",
    author="Paul Hiemstra",
    author_email="p.h.hiemstra@windesheim.nl",
    description="A package to efficiently run ReAgent",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PaulHiemstra/ReAgent_scripts",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points = {
         'console_scripts': ['reagent=command_line.reagent:main'],
    },
    python_requires='>=3.6',
)