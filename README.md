# Bras_dEau_RFI

Scripts to visualise Radio Frequency Interference (RFI) data stored in csv
format. The measurements were done at Bras d'Eau (site of ex-MRT and the future
MDT). A sample of the data is found in directories csvDataFiles and
txtDataFiles. The set consists of all the data measured in April 2019. The .CSV
files in csvDataFiles contain the raw data files from the spectrum analyser.
These include a header at the beginning of each data file indicating
configurations. The txtDataFiles contains .TXT files with the raw frequency and
power measurements in a comma separated format. It is the **.TXT files** which
must be passed to the scripts. The filenames are coded. E.g.
```
MRT_20190405_2230H000_2.CSV
```
MRT: site at which measurements were taken - Bras d'Eau </br>
20190405_2230: time and date at which file was written - 22:30, April 5th, 2019 </br>
H: polarisation - horizontal </br>
000: direction along which measurement was done - Azimuth = 0 degrees </br>
\_2: frequency band - Band 2: 327.275 MHz -- 327.525 MHz

**Script usage:**
```
./RFI_average_vx.x.py STARTDATE STARTTIME ENDDATE ENDTIME POL AZ BAND DATADIR
or
python3 RFI_average_vx.x.py STARTDATE STARTTIME ENDDATE ENDTIME POL AZ BAND DATADIR

STARTDATE: initial date for averaging in format YYYYMMDD
STARTTIME: starting time on the initial date in format HHmm
ENDDATE: closing date for range of data to be considered in format YYYYMMDD
ENDTIME: last time on the closing date in format HHmm
POL: polarisation (only parameters \'H\' or \'V\' are accepted
AZ: direction along which measurements were taken, in terms of Azimuth angle
    (only 0, 120 or 240 are valid)

BAND: frequency band of measurements, the accepted inputs for this parameter") are only 0, 1 or 2.
The meaning of each label are as follows:
	0 :       1 MHz --       1 GHz (bandwidth: 999 MHz)
	1 :     325 MHz --     329 MHz (bandwidth:   4 MHz)
	2 : 327.275 MHz -- 327.525 MHz (bandwidth: 250 KHz)

DATADIR: path of the directory holding the .TXT data files.
```
e.g.
```
./RFI_average_vx.x.py 20190415 0700 20190515 2359 V 0 1 ./txtDataFiles
```
The above command will look for data between 7:00 a.m, April 15th, 2019 and
11:59 p.m, May 15th, 2019. The measured polarisation sought is vertical (V),
for direction Azimuth = 0 degrees, in the frequency band 1, i.e.
325 MHz -- 329 MHz.

Command line output from script for this example:
```
First file:     MRT_20190503_0649V000_2.TXT
Last file:      MRT_20190504_0619V000_2.TXT

Actual time range (corrected w.r.t available files)
and current parameters:

06:49, 03 May 2019  -->  06:19, 04 May 2019

Length of time interval:  0.98 day(s)
Polarisation: vertical
Azimuth: 0 deg
Frequency band: 327.275 MHz -- 327.525 MHz (bandwidth: 250 KHz)

Total number of files in time range: 95

Do you wish to proceed with calculations? (y/n)  y

-> Could not open the following files:
MRT_20190503_1404V000_2.TXT
MRT_20190503_1404V000_2.TXT

-> Total number of useful files therefore: 93
```

There were 2 rejected files because the script detected that for two of the
data files, the amplifier was not working properly. The noise floor of the
spectrum analyzer was observed to be at -120dB. So, the script flags all the
data files containing average amplitudes below -120dB, as this will indicate
that the amplifier was not working during this observation. The amplifier level
for bandwidth 0 is +20dB, while it is +40dB for bandwidths 1 and 2.
