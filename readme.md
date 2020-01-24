# What is this repo
This repo contains a set of common tasks that you need in order to run [ReAgent](https://reagent.ai/) effectively from the command line. This script is useful as this is not straightforward using ReAgent out of the box. 

A number of parts of a ReAgent workflow steps are provided:

- `init` initialize a ReAgent run
- `run` run ReAgent, with or without preprocessing and allowing you to change the settings of the workflow (e.g. learning rate)

The rest of this introduction will show how to setup ReAgent in order to work effectively with this script. 

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
    
    Once this environment is activated, you can run commands such as `conda install` or `pip install` to install all the required software. 

- I installed pytorch using `conda`:

        conda install pytorch torchvision cudatoolkit=10.1 -c pytorch 

- The installation manual mentions not having to run pip again after updating the package, but this did not seems to work for me. So after:

        git pull origin master
    
    run:

        pip install .

- This ReAgent script depends on having ReAgent downloaded and ready on your system. The script finds the install via the `REAGENT_LOCATION` environment variable. Under bash this is done by adding:

	    export REAGENT_LOCATION="/path/to/ReAgent"

    to your `~/.bashrc` file.


## ReAgent gebruiken
Setting up a new ReAgent run is done using the `init` subcommand:

    reagent init run_name bla.json

where:

- `run_name` the name of the run, this is also the directory where the run will be stored. 
- `bla.json` the input data for the run. See the [ReAgent usage page](https://reagent.ai/usage.html#offline-rl-training-batch-rl) for the needed format. 

Deze cloned de versie van ReAgent die onder de `REAGENT_LOCATION` environment variable staat. Ook wordt het preprocessing package gebouwd. De aanname is hier dat je de installatie van ReAgent al hebt gedaan, dus Spark en PyTorch staan al geinstalleerd. 

Als je een nieuwe run klaar hebt staan kun je daadwerkelijk de run gaan starten: 

    reagent run --agent=dqn --base-run-config=ml/rl/etc/config.json --skip-preprocessing --[param-name]='valid json'

waarbij:

- `--agent` het soort agent wat je gaat draaien. Dit bepaald welke config file als uitgangspunt voor de run gaat dienen. 
- `--base-run-config` een alternatief voor `--agent`. Hierbij geef je zelf op welke config file als uitgangspunt dient voor de run. Als je deze zet, dan wordt `--agent` genegeerd. 
- `--skip-preprocessing` sla het preprocess gedeelte wat gebruik maakt van Spark over. Dit is handig als je alleen het trainen van het model opnieuw wil doen. 
- `--[param-name]='valid json'` van alle toplevel elementen die in het config bestand staan kun je alternatieve waardes opgeven. Dit is in de vorm van valide JSON. Als je bijvoorbeeld kijkt naar het standaard DQN config bestand (`ml/rl/workflow/sample_configs/discrete_action/dqn_example.json`), dan kun je de `learning_rate` op deze manier aanpassen:

        --training='{"learning_rate": 0.05}'

    let op dat de andere elementen in `training` niet aangepast worden.  


Run bestaat uit:

- Oude outputs opruimen: oude spark tussenproducten, oude outputs. 

    reagent tensorboard

### REAGENT_LOCATION environment variable instellen
In Bash (ubuntu) doe je dit door:


toe te voegen aan je `.bashrc`.

### Logging
ReAgent slaat alle commando's op die je runt. Op die manier kun je later zien wat er allemaal in volgorde gebeurt is met een repo.

# Notes
De `export` commandos moeten in je aan het conda env toevoegen. Hoe je dit doet [staat hier](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#macos-and-linux), de locatie van het env is bijvoorbeeld `/home/paul/anaconda3/envs/ReAgent`. 

    - De `JAVA_HOME` heeft standaard al een waarde. Voorlopig laat ik die even staan. 
