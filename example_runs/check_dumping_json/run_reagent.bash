# The standard example run
reagent init cart_pole_vanilla_run generated_cartpole_data.json --delete-old-run
cd cart_pole_vanilla_run
reagent run -r ../example_full_run_config.json --ts learning_rate 0.1
cd ..

# The run with the newly generated json using ReAgent_workflow
reagent init cart_pole_generated_json_RWFL_run reagent_workflow_generated_cartpole_data.json --delete-old-run
cd cart_pole_generated_json_RWFL_run
reagent run -r ../example_full_run_config.json --ts learning_rate 0.1
cd ..
