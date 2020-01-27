# Copyright 2020 Research group ICT innovations in Health Care, Windesheim University of Applied Sciences.
'''
Implements a number of functions that read, dump and update the various json files. Mainly used to work with ReAgent config files.
'''

import json
import logging

# TODO;
# - Add reading and dumping of json config files

def dump_json_and_log_content(config, path, prefix = 'Config'):
    '''
    Dump the content of a json file to disk, but also print it to the root logger. The main use is to both dump config files for ReAgent, but also show them in the `run_activity.log`. This makes it easy to track what exactly happened during a run. 

    Args:
       config (dict): a nested dict and list structure to dump. It is best to build this by reading config files from ReAgent using `json.load`. 
       path (string): where to dump the file
       prefix (string): prefix to add to log messages. This makes it easier to identify in the log file what config file was dumped. 
    '''
    logging.info('%s settings saved in %s.' % (prefix, path))
    # Showing the settings in the log file
    for line in json.dumps(config, indent=2).split('\n'):
        logging.info(line)
    with open(path, "w") as write_file:
        json.dump(config, write_file, indent=2)


def replace_value_in_dict(input_dict, replace_key, new_value):
    '''
    Function to search and replace the value in a mixed list/dict structure

    The function iterates over the list/dict structure `input_dict`, iterates over all the
    dicts it finds, and replaces the values belonging to `replace_key` with
    `new_value`. This makes it easy to just replace `learning_rate` anywhere in the config structure
    without having to specify where exactly it is. 

    Args:
       input_dict (dict): a mixed dict and list structure in which we will replace values at the given keys
       replace_key (string): the key for which to replace the value
       new_value (varies): the new value which is to be substituted 

    The function runs a sanity check to see if the type of the value you replace is equal to the old value. 

    Note that this function is specifically meant to replace values in ReAgent config
    list/dicts's and that the following limitations apply:

      - The function does not iterate into lists containing dicts. Lists should be 
        replaced as a whole.
      - The implementation is *not* meant to be fast. So do not use this for replacing
        values in large list/dict structures. In our case this is not really a problem
        as the ReAgent config files are quite limited in sie. 
    '''
    output_dict = {}
    for k, old_value in input_dict.items():
        if isinstance(old_value, dict):
            output_dict[k] = replace_value_in_dict(old_value, replace_key, new_value)
        else: 
            if k == replace_key:
                if not isinstance(new_value, type(old_value)):
                    raise ValueError('The new value is not the same object type as the old value')
                output_dict[k] = new_value
            else:
                output_dict[k] = old_value
    return output_dict

def replace_multiple_value_in_dict(input_dict, replace_dict):
    '''
    A convenient wrapper around `replace_multiple_value_in_dict` that allows you to pass a dict of key-value pairs to replace

    Args:
       input_dict (dict): the nested mixed list-dict structure to replace values in. 
       replace_dict: a 1d dictionary with key-value pairs to replace. 
    '''
    for k, v in replace_dict.items():
        input_dict = replace_value_in_dict(input_dict, k, v)
    return input_dict

if __name__ == '__main__':

    def run_test(input_dict, key, new_value):
        print('##### TEST on key %s replace by %s ######' % (key, str(new_value)))
        print(json.dumps(input_dict, indent=2))
        print('Replaced:')
        print(json.dumps(replace_value_in_dict(input_dict, key, new_value), indent=2))
        print('\n')

    simple_dict = {'a': 20, 'b': 30}
    nested_dict = {'a': 20, 'b': {'c': 20}}
    nested_nested_dict = {'a': {'a': {'c': 0.1, 'd': 50}, 'b': 30}, 'b': 30}
    nested_dict_list = {'a': [20, 30, 40], 'b': 30}

    run_test(simple_dict, 'a', 999)
    run_test(nested_dict, 'c', 999)
    run_test(nested_nested_dict, 'b', 999)
    run_test(nested_nested_dict, 'c', 0.01)
    run_test(nested_dict_list, 'a', [999, 999])
