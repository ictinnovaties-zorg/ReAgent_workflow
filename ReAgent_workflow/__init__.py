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
"""
The main ReAgent_scipts module wraps a number of submodules. Below I list the function and content of each of these submodules. 

The main supported interface is the commandline interface in the command line submodule. However, you could laternatively use the interface in the `execute_subcommand` submodule to build your own ReAgent runs. A good place to start would be the commandline interface, as this shows how to use all the parts. Just reading the docs will not suffice though, you really need to read the full source code.

Do note that this alternative interface is a very experimental feature, but potentially provides a more powerful interface. For example, running a 100 run gridsearch hyperparameter optimisation is more easy with this programmable interface. Just using `reagent_init` and `reagent_run` is more safe than delving into the other functions in the `execute_subcommand` submodule. 
"""

# This is done to expose these functions at the top-level of the package
from .execute_subcommand import reagent_init, reagent_run
