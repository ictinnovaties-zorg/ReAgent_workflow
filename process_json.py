import json

# TODO;
# - Add reading and dumping of json config files

def replace_value_in_dict(input_dict, replace_key, new_value):
    '''
    Function to search and replace the value in a mixed list/dict structure

    The function iterates over the list/dict structure `input_dict`, iterates over all the
    dicts it finds, and replaces the values belonging to `replace_key` with
    `new_value`. 

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
