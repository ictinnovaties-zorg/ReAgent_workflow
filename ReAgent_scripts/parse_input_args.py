import os
import argparse

#====== PARSING INPUT ARGUMENTS =========
def parse_init(args):
    parser = argparse.ArgumentParser(description='Initialize new ReAgent run')
    parser.add_argument('name', help='Name of the run')
    parser.add_argument('training_data', help='Training data used for the run')
    parser.add_argument('--delete-old-run', help='Delete the run in `name` if it already exists. ', action='store_true')
    parser.add_argument('--debug', help='Do not buffer the Python errors, useful during development', action='store_true')
    init_args = parser.parse_args(args)
    
    if os.path.isabs(init_args.name):
        logging.error('The name of the ReAgent run should be a single string, not an absolute path: %s' % init_args.name)
        exit(1)
    if os.path.split(init_args.name)[0] != '':
        logging.error('The name of the ReAgent run should be a single string, not a relative path: %s' % init_args.name)
        exit(1)

    return init_args

def parse_run(args):
    parser = argparse.ArgumentParser(description='Run ReAgent')
    parser.add_argument('-r', '--run_settings', help='Path to a settings file containing the global settings for this run')
    parser.add_argument('-s', '--skip-preprocessing', help='Skip preprocessing, and immediately launch the run ', action='store_true')
    parser.add_argument('-d', '--debug', help='Do not buffer the Python errors, useful during development', action='store_true')
    parser.add_argument('--ps', help='Pass preprocessing setting', nargs='+', action='append', metavar=('key','value'))
    parser.add_argument('--ts', help='Pass traininging settings', nargs='+', action='append', metavar=('key','value'))
    run_args = parser.parse_args(args)

    return run_args

subcommand_mapping = {'init': parse_init, 'run': parse_run}

def parse_arguments(args):
    parser = argparse.ArgumentParser(description='Interact with ReAgent: an offline Reinforcement Learning library')
    parser.add_argument('command', help='Subcommand to run')
    subcommand = parser.parse_args(args[1:2])
    if subcommand.command not in subcommand_mapping.keys():
        print('Unknown subcommand: %s' % subcommand.command)
        parser.print_help()
        exit(1)

    parsing_function = subcommand_mapping[subcommand.command]
    return subcommand.command, parsing_function(args[2:])
