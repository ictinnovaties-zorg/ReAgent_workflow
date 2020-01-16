#! /usr/bin/env python

# TODO: 
# - Expand usage documentation of the main and subcommands
# - Add unit tests
# - Refactor cmd line interface so the individual commands can be run seperate from 
#   the cmd line interface. 

import sys
import logging
import os

from parse_input_args import parse_arguments
from execute_subcommand import reagent_init, reagent_run

# =========== LOGGER ============
# Setting up the logging for this script
# We have two destinations for logging: 
#  - The console
#  - A log file
logging.basicConfig(level=logging.INFO, filename='run_activity.log', 
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M', filemode='a+')
# Adding the secondary logger
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

if __name__ == '__main__':
    if not 'REAGENT_LOCATION' in os.environ:
        logging.error("The 'REAGENT_LOCATION' environment variable is not set.")
        exit(1)

    subcommand, args = parse_arguments(sys.argv)
    if subcommand == 'init':
        try:
            reagent_init(args.name, args.training_data, os.environ['REAGENT_LOCATION'], args.delete_old_run)
        except Exception as e:
            logging.error('Failed to initialize run: %s' % e)
            exit(1)
    elif subcommand == 'run':
        pass
    else:
        logging.error('Unknown subcommand %s' % subcommand)
        exit(1)

    
