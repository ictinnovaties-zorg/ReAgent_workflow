# ReAgent
## Ophalen
Het ophalen van ReAgent doe je door het repo met Git te clonen:

    git clone --recurse-submodules https://github.com/facebookresearch/ReAgent.git

Het kan zijn dat er een probleem optreed met de submodule, [hier staat de oplossing](https://github.com/facebookresearch/ReAgent/issues/204). 

## Installatie
Voor de ReAgent installatie heb ik deels [de instructies](https://github.com/facebookresearch/ReAgent/blob/master/docs/installation.rst) gevolgd. Ik heb wel een aantal zaken anders aangepakt:

- Ik heb een conda environemnt (ReAgent) gemaakt voor het installeren van de dependencies. 

        conda create --name ReAgent
        conda activate ReAgent
    
    hierna kun je de requirements installeren via `conda install`. 
- De `export` commandos moeten in je aan het conda env toevoegen. Hoe je dit doet [staat hier](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#macos-and-linux), de locatie van het env is bijvoorbeeld `/home/paul/anaconda3/envs/ReAgent`. 

    - De `JAVA_HOME` heeft standaard al een waarde. Voorlopig laat ik die even staan. 

- Het installeren van PyTorch heb ik via conda gedaan:

        conda install pytorch torchvision cudatoolkit=10.1 -c pytorch 

- Ik heb de scripts in de `ml/rl/workflow` directory aan `$PATH` toegevoegd. Dan kan ik overal op de console deze scripts starten. 
- In de installatie handleiding staat dat je bij updates niet opnieuw `pip` hoeft te draaien, maar in mijn ervaring is dat wel nodig. Dus na: 

        git pull origin master
    
    moet je nog wel even:

        pip install .
    
    doen. 


## ReAgent gebruiken
Het gebruik van ReAgent was een beetje clunky, dus ik het een set aan scripts rondom ReAgent geschreven. 

Een verse run van ReAgent kun je opzetten met:

    reagent init run_name bla.json

waarbij:

- het eerste argument de naam van de run. Dit wordt ook de directory waarin de run staat. 
- en het tweede argument de JSON file waar de training data in klaar staat. Deze wordt in de run klaar gezet. 

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

    export REAGENT_LOCATION="/path/to/ReAgent"

toe te voegen aan je `.bashrc`.

### Logging
ReAgent slaat alle commando's op die je runt. Op die manier kun je later zien wat er allemaal in volgorde gebeurt is met een repo.
