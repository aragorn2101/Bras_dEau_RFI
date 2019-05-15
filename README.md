# Bras_dEau_RFI

Radio Frequency Interference measurements at Bras d'Eau (site for ex-MRT and
MDT instruments) and script to visualise the data. Data is in the csv format.

**Usage:**
./RFI_average_v1.0.py STARTDATE STARTTIME ENDDATE ENDTIME POL DIR BAND SOURCEDIR
or
python3 RFI_average_v1.0.py STARTDATE STARTTIME ENDDATE ENDTIME POL DIR BAND SOURCEDIR

STARTDATE: initial date for averaging in format YYYYMMDD </br>
STARTTIME: starting time on the initial date in format HHmm </br>
ENDDATE: closing date for range of data to be considered in format YYYYMMDD </br>
ENDTIME: last time on the closing date in format HHmm </br>
POL: polarisation (only parameters \'H\' or \'V\' are accepted </br>
DIR: direction in terms of Azimuth angle (only 0, 120 or 240 are valid </br>
BAND: frequency band of measurements, the accepted inputs for this parameter") are only 0, 1 or 2. </br>
The meaning of each label are as follows: </br>
    + 0 :       1 MHz --       1 GHz (bandwidth: 999 MHz) </br>
    + 1 :     325 MHz --     329 MHz (bandwidth:   4 MHz) </br>
    + 2 : 327.275 MHz -- 327.525 MHz (bandwidth: 250 KHz) </br>
