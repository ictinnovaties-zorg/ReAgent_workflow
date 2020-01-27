# Copyright 2020 Research group ICT innovations in Health Care, Windesheim University of Applied Sciences.
"""
This submodule contains all the code that runs each of the subcommands. Currently these are `init` to initialize a run and `run` to actually run ReAgent. These are executed using the `reagent_init` and `reagent_run` Python functions respectively. 

The main usage I see is to write Python scripts that use `reagent_init` and `reagent_run` to run batches of runs. You could use this to run a hyper parameter optimisation in a python loop. 

**NOTE** this programmable interface is very experimental, use at your own peril. The main interface is the commandline interface. 
"""

import subprocess
import shutil
import logging
import os
import json
from pandas.io.json import json_normalize
import glob
from .process_json import replace_multiple_value_in_dict, dump_json_and_log_content
from .logging_subprocess import logged_check_call

def reagent_init(run_name, training_data_path, reagent_location, delete_old_run=False):
    '''
    Initialize a reagent_run. This clones the git ReAgent repo, builds the preprocessing JAR and finally copies the `run_activity.log` file to the run directory. 

    Args:
       run_name (string): name of the run. This is mainly used for git cloning. Note that this is not allowed to be a full path, just one string. This to reduce risk of someone accidently deleting a directory they do not want. This is caused by the fact that via `delete_old_run` this path can be deleted. 
       training_data_path (path): the path to the training data file that contains the raw training data.
       reagent_location (path): location where ReAgent is installed. This is needed as a clone of this repo is made for each new run. 
       delete_old_run (bool): in case a run with the given name already exists, should this be deleted or not. 
    '''
    # TODO:
    # - Add check if git is installed and provide good error message
    # - Expand docstring
    logging.info('Setting up new ReAgent run in %s' % run_name)
    if delete_old_run and os.path.isdir(run_name):
        logging.info('Deleting old run in "%s"' % run_name)
        shutil.rmtree(run_name)

    logging.info('Calling git: git clone %s %s' % (reagent_location, run_name))
    # Note I skip logging the git output, it is not really needed and for some reason git 
    # writes a lot to stderr, even if things go right. This would probably lead to confusion.
    subprocess.check_call(['git', 'clone', reagent_location, run_name])

    # I use the try here not to catch the exception (notice the lack of except)
    # but to ensure the log file is always copied into the generated run directory,
    # even if an error occurs. This is really handy in case you generate a bunch
    # of runs of which some fail to initialize. git has succeeded at this moment, 
    # so the directory should always be there.
    try:
        logging.info('Creating directory for training data: %s/raw_data' % run_name)
        os.mkdir('%s/raw_data' % run_name)

        logging.info('Copying training data %s to %s/raw_data' % (training_data_path, run_name))
        shutil.copyfile(training_data_path, "%s/raw_data/%s" % (run_name, os.path.basename(training_data_path)))

        logging.info('Building preprocessing JAR using Maven')
        logged_check_call(['mvn', '-f', 'preprocessing/pom.xml', 'clean', 'package'], cwd=run_name)

        logging.info('Done building JAR')

        logging.info('Done setting up run in %s' % run_name)
    finally:
        logging.info('Copying log file to the run')
        shutil.move('run_activity.log', '%s/run_activity.log' % run_name)

def is_reagent_run():
    '''
    Check if the current directory is a valid reagent run. Return True if is, False if not. This function acutally calls the `check_run` function and checks for exceptions.
    '''
    try:
        check_run()
    except Exception:
        return False
    return True

def check_run(skip_preprocess):
    '''
    Perform a number of sanity checks on a run. Note that this is performed in the current working directory. 

    Args:
       skip_preprocess (bool): whether or not the skip_process will be used. This performs an additional check to see if the run can be started without preprocess. 

    TODO:

    - Add option to pass path, allowing someone to check any path they want.  
    '''
    logging.info('Performing basic sanity check on the current run')

    raw_data_file = glob.glob("raw_data/*json")
    if len(raw_data_file) == 0:
        raise ValueError('INVALID RUN: Could not find any raw data in raw_data/')
    if len(raw_data_file) > 1:
        raise ValueError('INVALID RUN: Found multiple raw input files, not really sure what todo')
    with open(raw_data_file[0]) as raw_training_string:
        # Note that we get the ds from the first 100 lines of data. We do not read
        # the whole dataset to save time. 
        raw_training_first100 = [json.loads(next(raw_training_string)) for line in range(100)]
        ds_values = json_normalize(raw_training_first100)['ds']
        if len(ds_values.unique()) > 1:
            raise ValueError('INVALID RUN: Found multiple different ds values in the first 100 lines of data, not sure how to handle this')
    if skip_preprocess:
        if not os.path.isfile('training_data/state_features_norm.json') or \
           not os.path.isfile('training_data/training_data.json') or \
           not os.path.isfile('training_data/evaluation_data.json'):
               raise ValueError('INVALID RUN: some files missing to start run without running preprocessing')


def _update_timeline_config(timeline_config, preprocessing_setting):
    '''
    Update timeline config with the required settings. 
    
    Input is a list/dict, output is an updated list/dict 

    The base config is:

        {
          "timeline": {
            "startDs": "2019-01-01",
            "endDs": "2019-01-01",
            "addTerminalStateRow": true,
            "actionDiscrete": true,
            "inputTableName": "cartpole_discrete",
            "outputTableName": "cartpole_discrete_training",
            "evalTableName": "cartpole_discrete_eval",
            "numOutputShards": 1
          },
          "query": {
            "tableSample": 100,
            "actions": [
              "0",
              "1"
            ]
          }
        }
    
    - NOT CHANGE addTerminalStateRow: add the terminal state at the end of the episode.
      afaik this should always be true. 
    - NOT CHANGE: actionDiscrete: whether or not to use discrete action space. For now keep this to
      true. 
    - NOT CHANGE numOutputShards: we are going to run stuff locally, stick to 1 shard for 
    '''
    # - startDs/endDs: start/stop unique identifier. Not entirely sure
    #     what to use this for as a already have an episode counter and
    #     it is not clear what is done with ds. For now just keep it constant
    #     in the file and in the input data.
    #        ----> Comes from the raw input file, I assume that this always has 1 single ds value
    #              ** Chose to get this from a config file now, much more robust and explicit. 
    # - inputTableName: data with the input for the timeline
    #   is a directory with the json input file. The name of the
    #   is not important, spark will read whatever json file is 
    #   there (I tested this). 
    #       ---> Is fixed name:  'raw_data'
    # - outputTableName: the name of the directory where spark
    #   should dump the training data
    #       ---> Can be named 'spark_raw_timeline_training'
    # - evalTableName: the name of the directory where spark should
    #   dump the evaluation data
    #       ---> Can be 'spark_raw_timeline_evaluation'
    #   spark
    #      - query:
    #         - tableSample: ???. 
    #             ---> Keep constant until we know what this is
    #         - actions: possible actions, in case of cartpole 0 and 1. 
    #             ---> Should be taken from input file, although the really dont to read all data for this
    #                  **The solution is to start using a config file where the user specifies the value. 
    #                    Making this explicit carries the least amount of risk and the greatest performance. 
    replace_dict = {'startDs':preprocessing_setting['ds_value'], 
                    'endDs':preprocessing_setting['ds_value'],
                    'inputTableName': 'raw_data',
                    'outputTableName': 'spark_raw_timeline_training',
                    'evalTableName': 'spark_raw_timeline_evaluation',
                    'actions': preprocessing_setting['actions']}
    return replace_multiple_value_in_dict(timeline_config, replace_dict)

def remove_dir_if_exists(path):
    '''
    Check if a directory exists, and remove if it does.  This also logs any action to the root logger.

    Args:
       path (string): the path to the directory to check and/or remove. 
    '''
    if os.path.isdir(path):
        logging.info('Found directory %s, removing...' % path)
        shutil.rmtree(path)

def remove_file_if_exists(path):
    '''
    Check if a file exists, and remove if it does.  This also logs any action to the root logger.

    Args:
       path (string): the path to the file to check and/or remove. 
    '''
    if os.path.isfile(path):
        logging.info('Found file %s, removing...' % path)
        os.remove(path)

def cleanup_preprocessing_artifacts():
    '''
    Remove all preprocessing artifacts related to preprocessing. This includes generated timeline data and spark artifacts. 
    '''
    logging.info('PREPROCESS: remove previously generated timeline data (training and eval)')
    # Note that we ignore any errors, primarily due to the directories not existing. 
    remove_dir_if_exists('spark_raw_timeline_training')
    remove_dir_if_exists('spark_raw_timeline_evaluation')
    remove_dir_if_exists('training_data')
    # - Delete previous spark artifacts
    remove_dir_if_exists('spark-warehouse')
    remove_file_if_exists('derby.log')
    remove_dir_if_exists('metastore_db')
    remove_dir_if_exists('preprocessing/spark-warehouse')
    remove_dir_if_exists('preprocessing/metastore_db')
    remove_file_if_exists('preprocessing/derby.log')

def cleanup_training_artifacts():
    '''
    Remove all training artifacts.
    '''
    remove_dir_if_exists('outputs')

def read_timeline_config_template():
    '''
    Read the timeline config template that will form the basis for the timeline data generation. 

    This file is read from ` ml/rl/workflow/sample_configs/discrete_action/timeline.json`
    '''
    logging.info('Reading timeline preprocessing config template from ml/rl/workflow/sample_configs/discrete_action/timeline.json')
    with open('ml/rl/workflow/sample_configs/discrete_action/timeline.json') as timeline_config_json:
        timeline_config = json.load(timeline_config_json)
    return timeline_config

def generate_timeline_data(preprocessing_settings, timeline_config_template):
    '''
    Generate timeline data based on the config template and the preprocessing settings. Note that these are merged and that the preprocessing settings take precedent. 
    '''
    timeline_config = _update_timeline_config(timeline_config_template, preprocessing_settings)
    dump_json_and_log_content(timeline_config, 'current_timeline_config.json', 'Timeline preprocessing')

    logging.info('Calling Spark to generate timeline data')
    logged_check_call(['spark-submit', 
           '--class', 'com.facebook.spark.rl.Preprocessor', 'preprocessing/target/rl-preprocessing-1.1.jar',
           '%s' % json.dumps(timeline_config)])
    logging.info('Success generating timeline data')

    os.mkdir('training_data')
    # - aggregate spark results into a single file (note that this does not seem to be needed in my case).
    #   dump the result in `training_data/training_data.json` and `training_data/evaluation_data.json`.
    training_parts = glob.glob('spark_raw_timeline_training/part*')
    evaluation_parts = glob.glob('spark_raw_timeline_evaluation/part*')
    if (len(training_parts) > 1) or (len(evaluation_parts) > 1):
        # For now spark always drops 1 file, so I chose not to implement this yet. See:
        #     https://stackoverflow.com/questions/24528278/stream-multiple-files-into-a-readable-object-in-python
        # for a Python based way of doing this. 
        logging.error('Found multiple part files from Spark, not yet implemented')
        raise ValueError
    else:
        logging.info('Copying Spark part files to training and evaluation data')
        shutil.copyfile(training_parts[0], 'training_data/training_data.json')
        shutil.copyfile(evaluation_parts[0], 'training_data/evaluation_data.json')

def read_normalisation_training_config_template():
    '''
    Read the normalisation parameters required. 
    '''
    logging.info('Reading normalisation preprocessing and training config template from ml/rl/workflow/sample_configs/discrete_action/dqn_example.json')
    with open('ml/rl/workflow/sample_configs/discrete_action/dqn_example.json') as config_json:
        config = json.load(config_json)
    return config

def generate_normalisation_params(config_template):
    '''
    Generate normalisation parameters

    Args:
        config_template (dict): nested dict structure. Provides the basis for the preprocessing. Note that this is the same template that is used for training the model. 
    '''
    # Change some settings in the config template
    # NOTE this is the same template as used for training, but I don't think we need
    # to replace all settings such as learning rate. 
    #
    # Some settings to discuss are:
    # -  "training_data_path": "training_data/cartpole_discrete_timeline.json",
    #      --> needs to be set to "training_data/training_data.json"
    # -  "eval_data_path": "training_data/cartpole_discrete_timeline_eval.json",
    #      --> needs to be set to "training_data/training_data.json"
    # -  "state_norm_data_path": "training_data/state_features_norm.json",
    #      --> Fine
    # -  "model_output_path": "outputs/",
    #      ---> Fine
    # -  "norm_params": {
    #     "output_dir": "training_data/",
    #     "cols_to_norm": [
    #       "state_features"
    #     ],
    #       --> Settings seem to be OK
    normalisation_config = replace_multiple_value_in_dict(config_template, {'training_data_path': "training_data/training_data.json", 
                                                                            "eval_data_path": "training_data/evaluation_data.json"})
    dump_json_and_log_content(normalisation_config, 'current_normalisation_config.json', 'Normalisation config')

    logging.info('Running normalisation')
    logged_check_call(['python', 'ml/rl/workflow/create_normalization_metadata.py', '-p', 'current_normalisation_config.json'])

def train_model(config_template, training_settings):
    '''
    Run ReAgent based on the given config template and the training settings that are merged into that. The training settings take precedent. 

    Currently only a DQN with discrete action is supported. 
    '''
    # Merge the given settings with a few that always need to be set. Notice that the
    # order of the addition means that any settings in the training settings file will
    # be overwritten by the hardcoded ones. 
    update_dict = {**training_settings, **{'training_data_path': "training_data/training_data.json", 
                    "eval_data_path": "training_data/evaluation_data.json"}}
    training_config = replace_multiple_value_in_dict(config_template, update_dict)
                                                                            
    dump_json_and_log_content(training_config, 'current_training_config.json', 'Training config')
    logged_check_call(["python", "ml/rl/workflow/dqn_workflow.py", "-p", "current_training_config.json"])


def reagent_run(run_settings, skip_preprocess):
    '''
    Start a reagent run. 

    Args:
        run_settings (dict): a nested dict that provides the settings for this run. See [the readme file] for a description of the kind of parameters that can be passed here. The dict syntax should be very similar to the json syntax. Another good trick would be to read the settings from a file using `json.load`, this will yield the correct input for this function.  
        skip_preprocess (bool): skip preprocessing or not. 

    TODO:

    - Add check for spark and provide meaningful error message
    - Expand docstring
    - Find out what the 'tableSample' argument does
    - Set a number of settings program wide instead of hardcoding, such as:
        - The name of the raw data directory
        - etc
    - Add option to disable normalisation. This can supposedly be done by setting the 
      mean and stdev to 0 and 1 respectively. 
    - Allow setting of templates. Right now we can change any params we want, but that could
      clutter the input run_settings quite a bit
    - Add evaluation component. This needs to be custom for each type of data, bit harder
      to implement generically. 
    '''

    # Perform a set of sanity checks before moving on. A failed check will throw an exception
    check_run(skip_preprocess)

    logging.info('========= START OF RUN ===============')

    # All cleanup is done before all other actions. This is the only way I could get a 
    # stable run. 

    if not skip_preprocess:
        cleanup_preprocessing_artifacts()
    cleanup_training_artifacts()

    timeline_config_template = read_timeline_config_template()
    training_normalisation_config_template = read_normalisation_training_config_template()

    if not skip_preprocess:
        generate_timeline_data(run_settings["preprocessing"], timeline_config_template)

        #   + Create normalisation params
        generate_normalisation_params(training_normalisation_config_template)
    #
    # Train model
    train_model(training_normalisation_config_template, run_settings["training"])
    #
    # Evaluate model
    logging.info('=========== END OF RUN ===============')


