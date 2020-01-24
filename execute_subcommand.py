import subprocess
import shutil
import logging
import os
import json
from pandas.io.json import json_normalize
import glob
from process_json import replace_multiple_value_in_dict
from logging_subprocess import logged_check_call

def reagent_init(run_name, training_data_path, reagent_location, delete_old_run=False):
    '''
    Initialize a reagent_run

    TODO:
    - Add check if git is installed and provide good error message
    - Expand docstring
    '''
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
    Check if the current directory is a valid reagent run. Return True if is, False if not. 
    '''
    try:
        check_run()
    except Exception:
        return False
    return True

def check_run():
    '''
    Perform a number of sanity checks on the run

    TODO:
    - Rewrite checks
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

def update_timeline_config(timeline_config, preprocessing_setting):
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
    if os.path.isdir(path):
        logging.info('Found directory %s, removing...' % path)
        shutil.rmtree(path)

def remove_file_if_exists(path):
    if os.path.isfile(path):
        logging.info('Found file %s, removing...' % path)
        os.remove(path)

def cleanup_preprocessing_artifacts():
    logging.info('PREPROCESS: remove previously generated timeline data (training and eval)')
    # Note that we ignore any errors, primarily due to the directories not existing. 
    remove_dir_if_exists('spark_raw_timeline_training')
    remove_dir_if_exists('spark_raw_timeline_evaluation')
    remove_dir_if_exists('training_data')
    # - Delete previous spark artifacts
    #rm -Rf spark-warehouse derby.log metastore_db preprocessing/spark-warehouse preprocessing/metastore_db preprocessing/derby.log
    remove_dir_if_exists('spark-warehouse')
    remove_file_if_exists('derby.log')
    remove_dir_if_exists('metastore_db')
    remove_dir_if_exists('preprocessing/spark-warehouse')
    remove_dir_if_exists('preprocessing/metastore_db')
    remove_file_if_exists('preprocessing/derby.log')

def cleanup_training_artifacts():
    shutil.rmtree('outputs', ignore_errors=True)

def read_timeline_config_template():
    logging.info('Reading timeline preprocessing config template from ml/rl/workflow/sample_configs/discrete_action/timeline.json')
    with open('ml/rl/workflow/sample_configs/discrete_action/timeline.json') as timeline_config_json:
        timeline_config = json.load(timeline_config_json)
    return timeline_config

def generate_timeline_data(preprocessing_settings, timeline_config_template):
    timeline_config = update_timeline_config(timeline_config_template, preprocessing_settings)

    logging.info('Timeline preprocessing settings saved in current_timeline_config.json.')
    # Showing the settings in the log file
    for line in json.dumps(timeline_config, indent=2).split('\n'):
        logging.info(line)
    with open("current_timeline_config.json", "w") as write_file:
        json.dump(timeline_config, write_file, indent=2)

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
    logging.info('Reading normalisation preprocessing and training config template from ml/rl/workflow/sample_configs/discrete_action/dqn_example.json')
    with open('ml/rl/workflow/sample_configs/discrete_action/dqn_example.json') as config_json:
        config = json.load(config_json)
    return config

def generate_normalisation_params(config_template):
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
    logging.info('Normalisation preprocessing settings saved in current_normalisation_config.json.')
    # Showing the settings in the log file
    for line in json.dumps(normalisation_config, indent=2).split('\n'):
        logging.info(line)
    with open("current_normalisation_config.json", "w") as write_file:
        json.dump(normalisation_config, write_file, indent=2)

    logging.info('Running normalisation')
    logged_check_call(['python', 'ml/rl/workflow/create_normalization_metadata.py', '-p', 'current_normalisation_config.json'])

def train_model(config_template):
    pass

def reagent_run(run_settings, skip_preprocess):
    '''
    Start a reagent run. 

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
    '''

    # Perform a set of sanity checks before moving on. A failed check will throw an exception
    check_run()

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
    train_model(training_normalisation_config_template)
    #
    # Evaluate model
    logging.info('=========== END OF RUN ===============')


