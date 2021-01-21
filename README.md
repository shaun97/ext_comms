# CG4002 External Comms

External communication portion of CG4002 Capstone project. Handles the connection between 3 laptops, Ultra96, dashboard server and evaluation server. All socket connections are encrypted and features 2 way communication to control the blunos from the Ultra96. Ultra96 features multi-threading to handle each socket connection and the ML code.

## ./laptop
* This folder contains the ```laptop_client.py``` code to run on each of the dancer's laptop.
* Run ```requirements.txt``` for dependencies.
* ```config.py``` to set relevant parameters. Include Sunfire account to tunnel into the Ultra96.
* Run the program using ```python3 laptop_client.py```

## ./dashboard
* This folder contains the dashboard_server.py code to run on the dashboard server.
* Run requirements.txt for dependencies.
* Starts an SSH tunnel and attempts to connect to the Ultra96
* Run the program using ```python3 dashboard_client.py```

## ./ultra96
* This folder contains the codes for the Ultra96 to run.
* Contains 4 main scripts. ```ultra96_client.py```, ```ultra96_server.py```, ```dashboard_server.py``` and ```main.py```.
* The first 3 contains the code to handle the connection to the respective devices. main.py contains the main driver of the whole program. Imports the other classes.
* Use ```config.py``` to set the relevant parameters for the program.
* Helper scripts - ```move_eval.py```, ```ml.py``` and ```driver_hardware_ml.py``` contains the helper scripts for evaluating moves, ml code and FPGA ml code respectively.
* Run requirements.txt for dependencies.
* Run the program using ```python3 main.py```
