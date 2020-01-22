import subprocess
import shutil
import logging
import os
import json
from pandas.io.json import json_normalize
import glob
from process_json import replace_multiple_value_in_dict

def reagent_init(run_name, training_data_path, reagent_location, delete_old_run=False):
    '''
    TODO:
    - Add check if git is installed and provide good error message
    - Expand docstring
    '''
    if delete_old_run and os.path.isdir(run_name):
        logging.info('Deleting old run in "%s"' % run_name)
        shutil.rmtree(run_name)

    logging.info('Calling git: git clone %s %s' % (reagent_location, run_name))
    subprocess.check_call(['git', 'clone', reagent_location, run_name])

    logging.info('Creating directory for training data: %s/raw_data' % run_name)
    os.mkdir('%s/raw_data' % run_name)

    logging.info('Copying training data %s to %s/raw_data' % (training_data_path, run_name))
    shutil.copyfile(training_data_path, "%s/raw_data/%s" % (run_name, os.path.basename(training_data_path)))

    logging.info('Building preprocessing JAR using Maven')
    subprocess.check_call(['mvn', '-f', 'preprocessing/pom.xml', 'clean', 'package'], cwd=run_name)

    logging.info('Copying log file to the run')
    shutil.move('run_activity.log', '%s/run_activity.log' % run_name)

    logging.info('Done setting up run in %s' % run_name)

def reagent_run(skip_preprocess):
    '''
    Start a reagent run. 

    TODO:
    - Add check for spark and provide meaningful error message
    - Expand docstring
    - Find out what the 'tableSample' argument does
    '''
    # From the tutorial
    # Reset the environment
    # - IF NOT skip_preprocess
    #    - Delete generated timeline data
    if not skip_preprocess:
        logging.info('PREPROCESS: remove previously generated timeline data (training and eval)')
        #shutil.rmtree('spark_raw_timeline_training')
        #shutil.rmtree('spark_raw_timeline_evaluation')
        #shutil.rmtree('training_data')
    # - Delete previous outputs
    # - Delete previous spark artifacts
    #
    # Create timeline stuff
    #   + configure timeline json
    if not skip_preprocess:
        logging.info('Reading timeline preprocessing config template from ml/rl/workflow/sample_configs/discrete_action/timeline.json')
        with open('ml/rl/workflow/sample_configs/discrete_action/timeline.json') as timeline_config_json:
            timeline_config = json.load(timeline_config_json)

        # Update the config
        # The base config is:
        # {
        #   "timeline": {
        #     "startDs": "2019-01-01",
        #     "endDs": "2019-01-01",
        #     "addTerminalStateRow": true,
        #     "actionDiscrete": true,
        #     "inputTableName": "cartpole_discrete",
        #     "outputTableName": "cartpole_discrete_training",
        #     "evalTableName": "cartpole_discrete_eval",
        #     "numOutputShards": 1
        #   },
        #   "query": {
        #     "tableSample": 100,
        #     "actions": [
        #       "0",
        #       "1"
        #     ]
        #   }
        # }
        # 
        # - NOT CHANGE addTerminalStateRow: add the terminal state at the end of the episode.
        #   afaik this should always be true. 
        # - NOT CHANGE: actionDiscrete: whether or not to use discrete action space. For now keep this to
        #   true. 
        # 
        # We need to change some stuff
        # 
        # - startDs/endDs: start/stop unique identifier. Not entirely sure
        #     what to use this for as a already have an episode counter and
        #     it is not clear what is done with ds. For now just keep it constant
        #     in the file and in the input data.
        #        ----> Comes from the raw input file, I assume that this always has 1 single ds value
        raw_data_file = glob.glob("raw_data/*json")
        if len(raw_data_file) == 0:
            raise ValueError('Could not find any raw data in raw_data/')
        if len(raw_data_file) > 1:
            raise ValueError('Found multiple raw input files, not really sure what todo')
        with open(raw_data_file[0]) as raw_training_string:
            # Note that we get the ds from the first 100 lines of data. We do not read
            # the whole dataset to save time. 
            raw_training_first100 = [json.loads(next(raw_training_string)) for line in range(100)]
            ds_values = json_normalize(raw_training_first100)['ds']
            if len(ds_values.unique()) > 1:
                raise ValueError('Found multiple different ds values in the first 100 lines of data, not sure how to handle this')
            ds_value = ds_values[0]
        logging.info('Replacing the ds value by the value found in the raw data: %s' % ds_value)
        timeline_config = replace_multiple_value_in_dict(timeline_config, {'startDs':ds_value, 'endDs':ds_value})

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
        # - NOT CHANGE numOutputShards: we are going to run stuff locally, stick to 1 shard for 
    #   spark
    #      - query:
    #         - tableSample: ???. 
    #             ---> Keep constant until we know what this is
    #         - actions: possible actions, in case of cartpole 0 and 1. 
    #             ---> Should be taken from input file
    #       - After changing all the settings, dump the new json file as `current_timeline_config.json`
    #    - run spark
    #    - aggregate spark results into a single file (note that this does not seem to be needed in my case).
    #      dump the result in `training_data/training_data.json` and `training_data/evaluation_data.json`.
    #   + Create normalisation params
    #
    # Train model
    #
    # Evaluate model
    logging.info('Done with run!')


