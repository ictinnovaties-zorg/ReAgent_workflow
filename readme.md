# What is this repo
This repo contains a set of common tasks that you need in order to run [ReAgent](https://reagent.ai/) effectively from the command line. This script is useful as this is not straightforward using ReAgent out of the box. 

A number of parts of a ReAgent workflow steps are provided:

- `init` initialize a ReAgent run
- `run` run ReAgent, with or without preprocessing and allowing you to change the settings of the workflow (e.g. learning rate)

The rest of this introduction will show how to setup ReAgent in order to work effectively with this script. 

# TL;DR
Short example run:

    reagent init cartpole_run generated_cartpole_data.json --delete-old-run 
    cp example_full_run_config.json cartpole_run
    cd cartpole_run
    reagent run -r example_full_run_config.json

Help for init:

    usage: reagent [-h] [--delete-old-run] [--debug] name training_data
    
    Initialize new ReAgent run
    
    positional arguments:
      name              Name of the run
      training_data     Training data used for the run
    
    optional arguments:
      -h, --help        show this help message and exit
      --delete-old-run  Delete the run in `name` if it already exists.
      --debug           Do not buffer the Python errors, useful during development

Help for run:

    usage: reagent [-h] [-r RUN_SETTINGS] [-s] [-d] [--ps key [value ...]]
                      [--ts key [value ...]]
    
    Run ReAgent
    
    optional arguments:
      -h, --help            show this help message and exit
      -r RUN_SETTINGS, --run_settings RUN_SETTINGS
                            Path to a settings file containing the global settings
                            for this run
      -s, --skip-preprocessing
                            Skip preprocessing, and immediately launch the run
      -d, --debug           Do not buffer the Python errors, useful during
                            development
      --ps key [value ...]  Pass preprocessing setting
      --ts key [value ...]  Pass traininging settings

# Setting up ReAgent
By and large you can following the [installation guide](https://reagent.ai/installation.html#installation) provided with ReAgent. I do present a number of additional steps below. 

## Getting ReAgent
The best way to get ReAgent is to simply clone the git repo:

    git clone --recurse-submodules https://github.com/facebookresearch/ReAgent.git

If you run into a problem with one of the submodules not loading properly, [you can find the solution here](https://github.com/facebookresearch/ReAgent/issues/204). 

## Installation tweaks
- I created a conda environment for ReAgent, although you could also use `virtualenv` if you don't run Anaconda as I do. Before following the install guide, create and activate the conda env:

        conda create --name ReAgent
        conda activate ReAgent
    
    Once this environment is activated, you can run commands such as `conda install` or `pip install` to install all the required software. Note that before running ReAgent, you always need to activate the environment. 

- I installed pytorch using `conda`:

        conda install pytorch torchvision cudatoolkit=10.1 -c pytorch 

- The installation manual mentions not having to run pip again after updating the package, but this did not seems to work for me. So after:

        git pull origin master
    
    run:

        pip install .

- This ReAgent script depends on having ReAgent downloaded and ready on your system. The script finds the install via the `REAGENT_LOCATION` environment variable. Under bash this is done by adding:

	    export REAGENT_LOCATION="/path/to/ReAgent"

    to your `~/.bashrc` file.

## Installing ReAgent scripts
In order to get the scripts working you need to:

- Clone the repo
- Install the package using:

    cd ReAgent_scripts
    pip install .

This will install the package and the command line script called `reagent`. 

## Running ReAgent
Setting up a new ReAgent run is done using the `init` subcommand:

    reagent init run_name bla.json

where:

- `run_name` the name of the run, this is also the directory where the run will be stored. 
- `bla.json` the input data for the run. See the [ReAgent usage page](https://reagent.ai/usage.html#offline-rl-training-batch-rl) for the needed format. 

This clones the repository in `REAGENT_LOCATION`, copies in the training data and builds the preprocessing JAR file using Maven. Finally, it copies the run log into the directory created by git. This log, `run_activity.log`, contains all the activity that took place in the run. 

After setting up an new run, you can start training models:

    reagent run --skip-preprocessing -r settings_config.json 

For now this runs a discrete action DQN as is used in the example on the ReAgent site. 

Below I describe the basic working of `reagent run`, the full detailed technical documentation can be had via `reagent run -h`. 

- `--skip-preprocessing` skip processing and directly start training a model. You can use this to repeatedly retrain a model with the need of having to rerun the preprocessing (generate timeline data, generate normalisation params). 
- `-r settings_config.json` optional settings file that enables you to change preprocessing and training settings in the run. For more details see the section below. 

In addition to the settings file, `reagent` also allows you to pass settings on the command line. This is done vvia the `--ts` and `--ps` for training settings and preprocessing settings respectively. For example:

    reagent run -r settings_config.json --ts learning_rate 0.0001

reads the settings from the file, but replaces the learning rate by `0.0001`. You case pass multiple values by simply calling `--ts` multiple times

    reagent run -r settings_config.json --ts learning_rate 0.0001 --ts epochs 300

will read the file and replace learning rate and number of epochs. **NOTE** you can pass settings via `--ts`and `--ps` that are not in `settings_config.json`. You can even omit the settings file completely and pass everything via the commandline.  

## Contents of a run
The resulting run contains a number of of key files that tell you about the settings and the results:

- `outputs`
- `current_etc` etc
- etc

## ReAgent run settings file
The following is an example of a settings file:

    {
      "preprocessing": {
         "ds_value": "2019-01-01",
         "actions": ["0", "1"] 
      },
      "training": {
         "epochs": 99,
         "learning_rate": 0.1
      }
    }

it contains two sections: `preprocessing` and `training`. 

- The first allows you to change preprocessing settings in the `preprocessing` template (`ml/rl/workflow/sample_configs/discrete_action/timeline.json`). The two settings, `ds_value` and `actions`, are things you probably need to change for your run.  
- The second allows you to change settings for the training phase. Any setting 

Note that it does not matter how deeply nested any of the settings are, the replacement algorithm will recursively go through the entire config tree and replace the value. For example, `learning_rate` is actually one level deep (`training > learning_rate`), but there is no need to mimic this depth. Simply pass `learning_rate` and the script will do the rest. 

## Full run example
First we set up an new run and perform one training run:

    reagent init cartpole_run generated_cartpole_data.json --delete-old-run 
    cp example_full_run_config.json cartpole_run
    cd cartpole_run
    reagent run -r example_full_run_config.json

Note that `example_full_run_config.json` and `generated_cartpole_data.json` are included in this repo in the `example_data` subdirectory.

If we want to run the exact same run, but with a learning rate of `0.001`, you can edit the config file and:

    reagent run -r edited_config.json --skip-preprocessing

This will not run the preprocessing, and retrain the model with the new learning rate. Alternatively, you could have not edited the file, but passed the new value via the command line:

    reagent run -r example_full_run_config.json --ts learning_rate 0.001

which yields the exact same result. 

# Notes
De `export` commandos moeten in je aan het conda env toevoegen. Hoe je dit doet [staat hier](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#macos-and-linux), de locatie van het env is bijvoorbeeld `/home/paul/anaconda3/envs/ReAgent`. 

    - De `JAVA_HOME` heeft standaard al een waarde. Voorlopig laat ik die even staan. 
