#! /usr/bin/env python

# TODO: 
# - Expand usage documentation of the main and subcommands
# - Add unit tests
# - Refactor cmd line interface so the individual commands can be run seperate from 
#   the cmd line interface. 

import sys
import logging
import os
import json
from pathlib import Path

from parse_input_args import parse_arguments
from execute_subcommand import reagent_init, reagent_run

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
    return Path(path).expanduser().resolve()

# =========== Command line interface ========
if __name__ == '__main__':
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
        # Note that I put the run in a separate try/except statement so I can give a 
        # specific error message when the config file is not found. The run can also generate
        # a host of errors, so we treat those more generically. 
        try:
            with open(resolve_path(args.run_settings)) as run_settings_json:
                run_settings = json.load(run_settings_json)
        except FileNotFoundError:
            logging.error('Could not find run settings config file %s' % args.run_settings)
            exit(1)
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

    
