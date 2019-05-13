#!/usr/bin/env python3
#
#  Copyright (c) 2019 Nitish Ragoomundun, Mauritius
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
#

from sys import argv
from os import path
from datetime import datetime,timedelta
#import numpy as np
#import matplotlib.pyplot as plt


###
###  Subsidiary Functions
###

###  BEGIN Construct filename  ###

def construct_filename(DateTime, Pol, Az, Band, DataPath):
    MiddleName = DateTime.strftime("%Y%m%d_%H%M") + Pol

    if Az == "0":
        MiddleName += "000"
    else:
        MiddleName += Az

    if Band != "0":
        MiddleName += "_" + Band

    if DataPath[-1] == "/":
        return(DataPath + "MRT_" + MiddleName + ".TXT")
    else:
        return(DataPath + "/MRT_" + MiddleName + ".TXT")


###  END Construct filename  ###



###  BEGIN Find files and make list  ###

def find_files(StartTime, EndTime, Pol, Az, Band, DataPath, List):
    # Clean list
    List.clear()

    dt1 = timedelta(minutes = 1)
    dt2 = timedelta(minutes = 15)

    # Find the first file
    while True:
        Filename = construct_filename(StartTime, Pol, Az, Band, DataPath)
        if path.isfile(Filename):
            List.append(Filename)
            break
        else:
            if StartTime < EndTime - dt1:
                StartTime += dt1
            else:
                raise FileNotFoundError


    DateTime = StartTime + dt2

    while DateTime <= EndTime:
        Filename = construct_filename(DateTime, Pol, Az, Band, DataPath)
        if path.isfile(Filename):
            List.append(Filename)
            LastOne = DateTime
            DateTime += dt2
        else:
            DateTime -= (dt2 - dt1)
            while True:
                Filename = construct_filename(DateTime, Pol, Az, Band, DataPath)
                if path.isfile(Filename):
                    break
                else:
                    if DateTime <= EndTime:
                        DateTime += dt1
                    else:
                        break

    if len(List) == 1:
        raise IndexError

    EndTime = LastOne

###  END Find files and make list  ###


###
###  Parameter Parsing
###

###  BEGIN Check validity of command line arguments  ###
try:
    if len(argv) <= 8:
        raise OSError
except OSError:
    print("Usage: {:s} STARTDATE STARTTIME ENDDATE ENDTIME POL DIR BAND SOURCEDIR".format(argv[0]))
    print("\nSTARTDATE: initial date for averaging in format YYYYMMDD")
    print("STARTTIME: starting time on the initial date in format HHmm")
    print("ENDDATE: closing date for range of data to be considered in format YYYYMMDD")
    print("ENDTIME: last time on the closing date in format HHmm")
    print("POL: polarisation (only parameters \'H\' or \'V\' are accepted)")
    print("DIR: direction in terms of Azimuth angle (only 0, 120 or 240 are valid)")
    print("BAND: frequency band of measurements, the accepted inputs for this parameter")
    print("      are only 0, 1 or 2. The meaning of each label are as follows:\n")
    print("      0 :       1 MHz --       1 GHz (bandwidth: 999 MHz)")
    print("      1 :     325 MHz --     329 MHz (bandwidth:   4 MHz)")
    print("      2 : 327.275 MHz -- 327.525 MHz (bandwidth: 250 KHz)")
    print()
    exit(1)


# Check validity of STARTDATE (argv[1]) and STARTTIME (argv[2])
try:
    if len(argv[1]) < 8 or len(argv[2]) < 4:
        raise ValueError

    year = int(argv[1][:4])
    month = int(argv[1][4:6])
    day = int(argv[1][6:])
    hour = int(argv[2][:2])
    minute = int(argv[2][2:])

    StartTime = datetime(year, month, day, hour, minute)

except ValueError:
    print("Invalid start date/time!")
    exit(2)


# Check validity of ENDDATE (argv[3]) and ENDTIME (argv[4])
try:
    if len(argv[3]) < 8 or len(argv[4]) < 4:
        raise ValueError

    year = int(argv[3][:4])
    month = int(argv[3][4:6])
    day = int(argv[3][6:])
    hour = int(argv[4][:2])
    minute = int(argv[4][2:])

    EndTime = datetime(year, month, day, hour, minute)

    if EndTime == StartTime:
        print("Start date/time is equal to end date/time!")
        raise ValueError
    if EndTime < StartTime:
        print("Start date/time is after end date/time!")
        raise ValueError

except ValueError:
    print("Invalid end date/time!")
    exit(3)


# Check validity of POL (argv[5])
try:
    if argv[5] not in {'H', 'V'}:
        raise ValueError
except ValueError:
    print("Invalid polarisation!")
    exit(4)

Pol = argv[5]


# Check validity of DIR (argv[6])
try:
    if argv[6] not in {"0", "120", "240"}:
        raise ValueError
except ValueError:
    print("Invalid Azimuth angle for direction!")
    exit(5)

Az = argv[6]


# Check validity of BAND (argv[7])
try:
    if argv[7] not in {"0", "1", "2"}:
        raise ValueError
except ValueError:
    print("Invalid frequency band label!")
    exit(6)

Band = argv[7]


# Check validity of DATADIR (argv[8])
try:
    if not path.isdir(argv[8]):
        raise ValueError
except ValueError:
    print("Cannot access {:s}".format(argv[8]))
    exit(7)

DataPath = argv[8]

###  END Check validity of command line arguments  ###



###
###  Main Function
###

###  BEGIN Browse through files  ###

Files = []
try:
    find_files(StartTime, EndTime, Pol, Az, Band, DataPath, Files)
    print("First file is {:s}".format(Files[0]))
    print("len(Files) = {:d}".format(len(Files)))
    print("Last file is {:s}".format(Files[-1]))
    print("Actual StartTime = {:s}".format(StartTime.strftime("%Y%m%d_%H%M")))
    print("Actual EndTime = {:s}".format(EndTime.strftime("%Y%m%d_%H%M")))
except FileNotFoundError:
    print("Error: Cannot find data files within input time interval with corresponding parameters.")
    exit(81)
except IndexError:
    print("Error: Time range contains only 1 file for corresponding parameters, cannot average!")
    exit(82)

# Assume that between StartTime and EndTime, files should be uniformly
# distributed with 15 minutes interval between them.



###  END Browse through files  ###



#  Loading file into numpy array
#  Open file containing dates and titles
"""
try:
    data = np.loadtxt(fname=argv[1], delimiter=",")
except OSError:
    print("Cannot open {:s}: No such file.\n".format(argv[1]))
    exit(2)
"""

exit(0)
