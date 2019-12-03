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
MRT_20190405_2230H000_2.TXT
```
**MRT:** site at which measurements were taken - Bras d'Eau </br>
**20190405_2230:** time and date at which file was written - 22:30, April 5th, 2019 </br>
**H:** polarisation - horizontal </br>
**000:** direction along which measurement was done - Azimuth = 0 degrees </br>
**_2:** frequency band - Band 2: 327.275 MHz -- 327.525 MHz


## Dependencies

- Python 3
- Numpy
- Matplotlib


## RFI_average script usage

The script accumulates RFI spectral data over a user-input time interval and
plots a graph of RFI power in dBm against frequency. The script also outputs
the results in a csv file with two columns, namely frequency in Hz and average
power in dBm.

```
./RFI_average_vx.x.py STARTDATE STARTTIME ENDDATE ENDTIME POL AZ BAND DATADIR
or
python3 RFI_average_vx.x.py STARTDATE STARTTIME ENDDATE ENDTIME POL AZ BAND DATADIR

STARTDATE: initial date for averaging in format YYYYMMDD
STARTTIME: starting time on the initial date in format HHmm
ENDDATE: closing date for range of data to be considered in format YYYYMMDD
ENDTIME: last time on the closing date in format HHmm
POL: polarisation (only parameters 'H' or 'V' are accepted
AZ: direction along which measurements were taken, in terms of Azimuth angle
    (only 0, 120 or 240 are valid)

BAND: frequency band of measurements, the accepted inputs for this parameter are only 0, 1 or 2.
The meaning of each label are as follows:
	0 :       1 MHz --       1 GHz (bandwidth: 999 MHz)
	1 :     325 MHz --     329 MHz (bandwidth:   4 MHz)
	2 : 327.275 MHz -- 327.525 MHz (bandwidth: 250 KHz)

DATADIR: path of the directory holding the .TXT data files.
```

**Example:**
```
$ ./RFI_average_v1.3.py 20190415 0700 20190430 2245 H 0 1 ./txtDataFiles
```
The above command will look for data in directory txtDataFiles found in current
directory. Data files should range from 07:00, April 15th, 2019 to 22:45, May
5th 2019. The measured polarisation sought is horizontal (H), for direction
Azimuth = 0 degrees, in the frequency band 1, i.e.  325 MHz -- 329 MHz.

Command line output from script for this example:
```
First file:     MRT_20190424_0648H000_1.TXT
Last file:      MRT_20190425_0618H000_1.TXT

Actual time range (corrected w.r.t available files)
and current parameters:

06:48, 24 April 2019  -->  06:18, 25 April 2019

Length of time interval:  0.98 day(s)
Polarisation: horizontal
Azimuth: 0 deg
Frequency band: 325 MHz -- 329 MHz (bandwidth: 4 MHz)

Total number of files in time range: 95

Do you wish to proceed with calculations? (y/n)  y

-> Could not open the following files:
TXT/MRT_20190424_0818H000_1.TXT
TXT/MRT_20190424_0833H000_1.TXT
TXT/MRT_20190424_1133H000_1.TXT

-> Total number of useful files therefore: 92
```

The output informs the user that, according to available data files, the range
will be restricted to *06:48, 24 April 2019  -->  06:18, 25 April 2019*.
There were 2 rejected files within this range because the script detected that
these 2 files, the amplifier was not working properly. The noise floor of the
spectrum analyzer was observed to be around -120dB. So, the script flags all
the data files containing average amplitudes below -117dB, as this will
indicate that the amplifier was not working during this observation. A value of
-118dB is used because in certain data files the amplitudes were at this level.
The amplifier level for bandwidth 0 is +20dB, while it is +40dB for bandwidths
1 and 2.


## RFI_spectrogram script usage

This script produces a spectrogram of the RFI data for a single day. Thus, it
takes as input only a date and will consider data between 00:00 and 23:59 of
that day.
```
Usage: ./RFI_spectrogram_vx.x.py DATE POL AZ BAND DATADIR

DATE: date in format YYYYMMDD for which spectrogram will be plotted
POL: polarisation (only parameters 'H' or 'V' are accepted)
AZ: direction along which measurements were taken, in terms of Azimuth angle)
    (only 0, 120 or 240 are valid)

BAND: frequency band of measurements, the accepted inputs for this parameter
      are only 0, 1 or 2. The meaning of each label are as follows:

      0 :       1 MHz --       1 GHz (bandwidth: 999 MHz)
      1 :     325 MHz --     329 MHz (bandwidth:   4 MHz)
      2 : 327.275 MHz -- 327.525 MHz (bandwidth: 250 KHz)

DATADIR: path of the directory holding the .TXT data files

Example:
./RFI_spectrogram_v1.3.py 20190307 H 240 1 ./txtDataFiles

The above command will look for data in directory txtDataFiles found in current
directory. Data files searched will be in the range 00:00 -- 23:59, January
15th, 2019.  The measured polarisation sought is vertical (V), for direction
Azimuth = 240 degrees, in the frequency band 1, i.e.  325 MHz -- 329 MHz.
```
**Example:**
```
$ ./RFI_average_v1.3.py 20190424 H 0 1 ./txtDataFiles

First file:     MRT_20190424_0648H000_1.TXT
Last file:      MRT_20190424_2348H000_1.TXT

Time range and current parameters:

00:00, 24 April 2019  -->  23:59, 24 April 2019

Length of time interval:  1.00 day(s)
Polarisation: horizontal
Azimuth: 0 deg
Frequency band: 325 MHz -- 329 MHz (bandwidth: 4 MHz)

Total number of files in time range: 69
Number of files expected in time interval: 95
Percentage completeness:  72.63%

Do you wish to proceed with calculations? (y/n)  y

-> These files had invalid values of signal power:
-> (possibly indicating amplifier malfunction)
MRT_20190424_0818H000_1.TXT
MRT_20190424_0833H000_1.TXT
MRT_20190424_1133H000_1.TXT

-> Total number of useful files therefore: 66
-> Number of files expected in time interval: 95
-> Percentage completeness:  66.32%
```

The output from the example informs the user that, according to available data
files, the range will be restricted to *00:00 -->  23:59, 24
April 2019*.  There were 3 rejected files within this range according to the
power levels indicating an amplifier malfunction, as explained before.
