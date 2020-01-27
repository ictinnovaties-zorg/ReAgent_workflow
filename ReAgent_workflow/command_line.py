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
'''
This submodule hosts the command line interface of ReAgent_workflow. It uses the functions defined in the other submodules to actually control ReAgent. 

This is the main interface that controls ReAgent. This is also a good place to start if you want to create your own workflow scripts in Python. 
'''

# TODO: 
# - Expand usage documentation of the main and subcommands
# - Add unit tests
# - Refactor cmd line interface so the individual commands can be run seperate from 
#   the cmd line interface. 

import sys
import logging
import os
import json
import argparse
from pathlib import Path

from ReAgent_workflow import reagent_init, reagent_run

# =========== LOGGER ============
# Setting up the logging for this script
# We have two destinations for logging: 
#  - The console
#  - A log file
# Note that all the code dumps messages to the root logger. So use that
# if you want the log info of the underlying functions that do the work.
logging.basicConfig(level=logging.INFO, filename='run_activity.log', 
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M', filemode='a+')
# Adding the secondary logger for console
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

# =========== Support functions =============
def resolve_path(path):
    '''
    Interpret paths Bash style. This takes care of things like `..` and `~`, expanding those like Bash would do. This is very useful when processing paths received from the command line. 

    Args:
      path: the path you want to resolve

    Returns:
      path: The resolved path
     
    '''
    return Path(path).expanduser().resolve()

def _get_run_settings(args):
    # Note that I put the run in a separate try/except statement so I can give a 
    # specific error message when the config file is not found. The run can also generate
    # a host of errors, so we treat those more generically. 
    if args.run_settings is not None:
        try:
            with open(resolve_path(args.run_settings)) as run_settings_json:
                run_settings = json.load(run_settings_json)
        except FileNotFoundError:
            logging.error('Could not find run settings config file %s' % args.run_settings)
            exit(1)
    else:
        # Empty placeholder is no settings file is passed
        run_settings = {'preprocessing': {}, 'training': {}}
    # merge --ts and --ps
    if args.ts is not None:
        # Merge settings from settings file with those passed via --ts on the command line
        # the settings from --ts get preference. 
        # Also notice the use of json.loads. This is to transform the string we get from the command
        # line to the appropriate data type. '0.001' becomes float, '1' becomes int and 'bla' 
        # becomes str. The nice thing of json.loads is that it matches all the other json loading
        # conventions that the other tooling in ReAgent uses. 
        ts_dict = {val[0]:json.loads(val[1]) for val in args.ts}
        run_settings['training'] = {**run_settings['training'], **ts_dict}
    if args.ps is not None:
        ps_dict = {val[0]:json.loads(val[1]) for val in args.ps}
        run_settings['preprocessing'] = {**run_settings['preprocessing'], **ps_dict}

    return run_settings

#====== PARSING INPUT ARGUMENTS =========
init_ld = '''This clones the repository in REAGENT_LOCATION, copies in 
the training data and builds the preprocessing JAR file using 
Maven. Finally, it copies the run log into the directory 
created by git. This log, run_activity.log, contains all 
the activity that took place in the run.'''
example_init='''Example usage:

    reagent init cartpole_run generated_cartpole_data.json --delete-old-run 
'''
def _parse_init(args):
    parser = argparse.ArgumentParser(description=init_ld, usage="reagent init [-h] [-o] [-d] name training_data",
            epilog=example_init,
            formatter_class=argparse.RawDescriptionHelpFormatter
            )
    parser.add_argument('name', help='Name of the run')
    parser.add_argument('training_data', help='Training data used for the run')
    parser.add_argument('-o', '--delete-old-run', help='Delete the run in `name` if it already exists. ', action='store_true')
    parser.add_argument('-d', '--debug', help='Do not buffer the Python errors, useful during development', action='store_true')
    init_args = parser.parse_args(args)
    
    if os.path.isabs(init_args.name):
        logging.error('The name of the ReAgent run should be a single string, not an absolute path: %s' % init_args.name)
        exit(1)
    if os.path.split(init_args.name)[0] != '':
        logging.error('The name of the ReAgent run should be a single string, not a relative path: %s' % init_args.name)
        exit(1)

    return init_args

run_ld = '''Run ReAgent from the command line. 

Note that if you want to pass multiple preprocessing 
or training settings, you can call `--ps/ts` multiple times. '''
example_run='''Example usage: 

    reagent run -r config.json --skip-preprocessing
    reagent run -r config.json --s --ts learning_rate 0.1
    reagent run -r config.json --s --ts learning_rate 0.1 --ts epochs 999
'''
def _parse_run(args):
    parser = argparse.ArgumentParser(description=run_ld, 
            usage='reagent run [-h] [-r RUN_SETTINGS] [-s] [-d] [--ps key value] [--ts key value]',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=example_run)
    parser.add_argument('-r', '--run_settings', help='Path to a settings file containing the global settings for this run')
    parser.add_argument('-s', '--skip-preprocessing', help='Skip preprocessing, and immediately launch the run ', action='store_true')
    parser.add_argument('-d', '--debug', help='Do not buffer the Python errors, useful during development', action='store_true')
    parser.add_argument('--ps', help='Pass preprocessing setting', nargs='+', action='append', metavar=('key','value'))
    parser.add_argument('--ts', help='Pass traininging settings', nargs='+', action='append', metavar=('key','value'))
    run_args = parser.parse_args(args)

    return run_args

subcommand_mapping = {'init': _parse_init, 'run': _parse_run}

main_ld='''A command line workflowmanager for ReAgent.'''
extra_info='''For more information, please see the help pages for the subcommands:
    
    reagent init -h
    reagent run -h'''
def parse_arguments(args):
    '''
    Parses the arguments passed from the command line. 

    Args:
       args: the raw input args, most probably generated by `sys.argv`
    '''
    parser = argparse.ArgumentParser(description=main_ld,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=extra_info)
    parser.add_argument('command', help='Subcommand to run, options are `init` or `run`.')
    subcommand = parser.parse_args(args[1:2])
    if subcommand.command not in subcommand_mapping.keys():
        print('Unknown subcommand: %s' % subcommand.command)
        parser.print_help()
        exit(1)

    parsing_function = subcommand_mapping[subcommand.command]
    return subcommand.command, parsing_function(args[2:])

def main():
    '''
    The main function that actually runs the script. 
    '''
    if not 'REAGENT_LOCATION' in os.environ:
        logging.error("The 'REAGENT_LOCATION' environment variable is not set.")
        exit(1)

    subcommand, args = parse_arguments(sys.argv)
    if subcommand == 'init':
        if not args.debug:
            # Catch errors and provide nice message is not in debug mode
            try:
                reagent_init(args.name, args.training_data, os.environ['REAGENT_LOCATION'], args.delete_old_run)
            except Exception as e:
                logging.error('Failed to initialize run: %s' % e)
                exit(1)
        else:
            # Simply give me the raw Python errors in debug mode
            reagent_init(args.name, args.training_data, os.environ['REAGENT_LOCATION'], args.delete_old_run)
    elif subcommand == 'run':
        run_settings = _get_run_settings(args)
        if not args.debug:
            try:
                reagent_run(run_settings, args.skip_preprocessing)
            except Exception as e:
                logging.error('Failed to complete run: %s' % e)
                exit(1)
        else:
            reagent_run(run_settings, args.skip_preprocessing)
    else:
        logging.error('Unknown subcommand %s' % subcommand)
        exit(1)

# =========== Command line interface ========
if __name__ == '__main__':
    main()
