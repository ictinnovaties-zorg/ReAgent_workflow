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
Implements a number of functions that read, dump and update the various json files. Mainly used to work with ReAgent config files.
'''

import json
import logging
import numpy as np
import pandas as pd
from tqdm.notebook import tqdm

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


# --------- The functions below can be used to generate JSON input data from a Pandas DataFrame ---------
def _get_funcs_for_var(df, grouping_vars, var, funcs):
    res = df[grouping_vars + [var]].groupby(grouping_vars).agg(funcs)
    res.columns = ['_'.join(feature) for feature in res.columns.to_series()]
    return res

def create_features(df, grouping_vars, var_func_combos):
    '''
    Create a set of features by taking `df`, grouping by `grouping_vars` and applying the functions and variabeles in `var_func_combos`
    
    For example:
    
        grouping_vars = ['path', 'timechunk_id']
        var_func_combos = {'base_plasma_insuline': ['mean', 'max'], 
                           'base_plasma_glucose': ['mean', 'min'],  
                           'exogeneous_insuline': ['max']           
                           }
        all_vars_and_funcs = create_features(all_vip, grouping_vars, var_func_combos)
    '''
    return pd.concat([_get_funcs_for_var(
                                        df, grouping_vars, var, funcs
                                    ) for var, funcs in var_func_combos.items()], 
                               axis='columns')

# Calculate the possible actions
def _find_nearest(array, value):
    '''
    From https://stackoverflow.com/a/2566508
    '''
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]

def discretize_action_space(action_vector, possible_actions = None):
    '''
    Round the actions in `action_vector` to the nearest one in `possible_actions`. 
    
    If possible actions is not given, this will be calculate based on the 0.0-1.0 quantiles in steps of 0.1. 
    '''
    if possible_actions is None:
        dummy_data, possible_actions = pd.qcut(action_vector, q = np.linspace(0,1,num=10), retbins=True)
    rounded_action_vector = [_find_nearest(possible_actions, action) for action in action_vector]
    if possible_actions is None:
        return rounded_action_vector
    else:
        return possible_actions, rounded_action_vector

def _create_reagent_state_vector(tuple_row, feature_names):
    return {'state_features': dict(zip(feature_names, tuple_row[1:]))}

def _create_reagent_record(row, feature_names, index_names, ds_value, mdp_id_var, 
                           sequence_number_var, possible_actions, action_var, reward_var, 
                           action_probability, indent=None):
    dictlist = _create_reagent_state_vector(row, feature_names)
    dictlist['ds'] = ds_value
    index = row[0]
    dictlist['mdp_id'] = index[index_names.index(mdp_id_var)]
    dictlist['sequence_number'] = index[index_names.index(sequence_number_var)]
    
    dictlist['possible_actions'] = possible_actions
    dictlist['action'] = str(index[index_names.index(action_var)])
    assert dictlist['action'] in dictlist['possible_actions'], 'Action %s is not found in the list of possible actions' % dictlist['action']
    
    dictlist['reward'] = index[index_names.index(reward_var)]
    dictlist['metrics'] = {"reward": dictlist['reward']}
    
    dictlist['action_probability'] = action_probability
    return json.dumps(dictlist, indent=indent)

def reagent_df_to_json_lines(df, ds_value, mdp_id_var, sequence_number_var, 
                             possible_actions, action_var, reward_var, action_probability,  
                             indent=None, progress=False, json_path=None):
    '''
    Convert the dataframe to the appropriate jsonlines data needed for ReAgent
    
    The goal is to produce something like the following JSON for each timestamp:
    
            {
                "ds": "2019-01-01",
                "mdp_id": "0",
                "sequence_number": 0,
                "state_features": {
                    "0": -0.04456399381160736,
                    "1": 0.04653909429907799,
                    "2": 0.013269094750285149,
                    "3": -0.020998265594244003
                },
                "action": "0",
                "reward": 1.0,
                "action_probability": 0.975,
                "possible_actions": [
                    "0",
                    "1"
                ],
                "metrics": {
                    "reward": 1.0
                }
            }
    
    where:
    
    - `ds` a unique id
    - `mdp_id` episode id. A complete run of the 'game'
    - `sequence_number` timestamp within the episode
    - `state_features` state feature values for this timestamp
    - `action` the action that was taken this timestamp
    - `reward` the short term reward the given action yielded
    
    Args:
        df (DataFrame): a pandas dataframe which contains the state per timestamp
        ds_value (string): a string providing the unique ID of the dataset
        mdp_id_var (string): which variable in the **index** of df provides the episode id
        sequence_number_var (string): which variable in the **index** of df provides the timestamp
        possible_actions (list): list of possible actions. This is static, not deduced from df.
        action_var (string): which variable in the **index** of df provides the action. Note that this should be a value listed in `possible_actions`. 
        indent (int): should newlines be introduced to nicely format the json. Primarily useful for debugging, not for dumping the data for ReAgent. 
        progress (bool): should a progress bar be drawn
        json_path (string): which path should the json be saved to. Default is `None`, which returns an array with jsonlines. 

    TODO:
    - _create_reagent_record now creates the string needed for dumping. Maybe a cleaner approach would be to let
      that function generate a dictlist, and convert to string just before dumping. 
    '''
    possible_actions = [str(action) for action in possible_actions]
    if progress:
        json_lines = [_create_reagent_record(
                row, df.columns, df.index.names, ds_value, mdp_id_var, sequence_number_var, possible_actions, action_var, reward_var, action_probability, indent=indent
           ) for row in tqdm(df.itertuples(), total=len(all_vars_and_funcs))]
    else:
        json_lines = [_create_reagent_record(
                row, df.columns, df.index.names, ds_value, mdp_id_var, sequence_number_var, possible_actions, action_var, reward_var, action_probability, indent=indent
           ) for row in df.itertuples()]
    if json_path is None:
        return json_lines
    else:
        with open(json_path, 'w') as json_file:
            for json_line in json_lines:
                json_file.write(json_line + '\n')
        return 'Dumped json data in %s' % json_path

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
