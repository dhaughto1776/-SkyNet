# OBS README

This folder contains the OBS related scripts that I worked on for SkyNet, namely for the magnetometer. The magnetometer was something we struggled with extensively during development. The scripts included here outline my best attempt at trying to calibrate and utilise the GY271 magnetometer. The magnetometer seemed to be working in lab testing in noise free enviroments. However, on the day, calibration was performed without accoutning for the magnetic interference of the other TupperSats present on the balloon payload. 

- magneotmeter_tilt_corr.py: Script for operating the GY271 magnetometer
- custom_calib_magneto.py: Script for calibrating the GY271 magnetometer
