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

def get_run_settings(args):
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
        run_settings = get_run_settings(args)
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

    
