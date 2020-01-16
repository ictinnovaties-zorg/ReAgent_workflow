import subprocess
import shutil
import logging
import os

def reagent_init(run_name, training_data_path, reagent_location, delete_old_run=False):
    if delete_old_run and os.path.isdir(run_name):
        logging.info('Deleting old run in "%s"' % run_name)
        shutil.rmtree(run_name)

    logging.info('Calling git: git clone %s %s' % (reagent_location, run_name))
    subprocess.check_call(['git', 'clone', reagent_location, run_name])

    logging.info('Creating directory for training data: %s/training_data' % run_name)
    os.mkdir('%s/training_data' % run_name)

    logging.info('Copying training data %s to %s/training_data' % (training_data_path, run_name))
    shutil.copyfile(training_data_path, "%s/training_data/%s" % (run_name, os.path.basename(training_data_path)))

    logging.info('Building preprocessing JAR using Maven')
    subprocess.check_call(['mvn', '-f', 'preprocessing/pom.xml', 'clean', 'package'], cwd=run_name)

    logging.info('Copying log file to the run')
    shutil.move('run_activity.log', '%s/run_activity.log' % run_name)

    logging.info('Done setting up run in %s' % run_name)

def reagent_run(args):
    pass

