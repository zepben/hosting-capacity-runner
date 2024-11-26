# hosting-capacity-runner

Python script to request run for hosting capacity work package.

## Setup

1. Run 'pip install -r requirements.txt' to install dependencies.

## Usage

1. Update the **auth_config.json** file to hold your configuration for authentication.
2. Update the **config.json file** with the feeders, years, and scenarios you want to run.
3. Run the **run_hc_work_package.py** python script passing the directory where the **auth_config.json** and **config.json** files
   are located (If no config directory is passed it will look for the config files in the current directory).

   ```shell
       ./run_hc_work_package.py ./config
   ```
