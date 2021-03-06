# Copyright 2020 Research group ICT innovations in Health Care, Windesheim University of Applied Sciences
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import setuptools

with open("readme.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ReAgent_workflow", # Replace with your own username
    version="0.0.1",
    author="Paul Hiemstra",
    author_email="p.h.hiemstra@windesheim.nl",
    description="A package to efficiently run ReAgent",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PaulHiemstra/ReAgent_workflow",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points = {
         'console_scripts': ['reagent=ReAgent_workflow.command_line:main'],
    },
    python_requires='>=3.6',
)
