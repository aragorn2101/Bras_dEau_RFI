#!/usr/bin/env python3

from sys import argv
from os import path
from time import time
from random import seed,randint
from datetime import datetime,timedelta
from numpy import loadtxt,append,zeros,subtract,mean
import matplotlib.pyplot as plt
from matplotlib.ticker import EngFormatter


###
###  Subsidiary Functions
###

###  BEGIN Function: Construct filename  ###
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

###  END Function: Construct filename  ###



###  BEGIN Function: Find files and make list  ###
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

    if len(List) <= 1:
        raise IndexError

    EndTime = LastOne
    return(StartTime,EndTime)

###  END Function: Find files and make list  ###



###  BEGIN Function: Print help  ###
def print_help(ScriptName):
    print()
    print("Usage: {:s} STARTDATE ENDDATE BAND DATADIR".format(ScriptName))
    print("\nSTARTDATE: initial date for averaging in format YYYYMMDD")
    print("ENDDATE: closing date for range of data to be considered in format YYYYMMDD")
    print("BAND: frequency band of measurements, the accepted inputs for this parameter")
    print("      are only 0, 1 or 2. The meaning of each label are as follows:\n")
    print("      0 :       1 MHz --       1 GHz (bandwidth: 999 MHz)")
    print("      1 :     325 MHz --     329 MHz (bandwidth:   4 MHz)")
    print("      2 : 327.275 MHz -- 327.525 MHz (bandwidth: 250 KHz)\n")
    print("DATADIR: path of the directory holding the .TXT data files\n")
    print("Example:")
    print("{:s} 20190415 20190430 1 ./txtDataFiles\n".format(ScriptName))
    print("The above command will look for data in directory txtDataFiles found in current")
    print("directory. Data files should range from 07:00, April 15th, 2019 to 22:45, May")
    print("5th 2019. The script will look for both H and V polarisations and also data")
    print("for all three directions, i.e. Azimuth = {0, 120, 240}.")
    print()

    return(0)
###  END Function: Print help  ###



###  BEGIN Function: Print runtime configurations  ###
def print_runconfig(List, StartTime, EndTime, Band):


    # String to describe frequency bandwidth
    if Band == "0":
        sBand = "1 MHz -- 1 GHz (bandwidth: 999 MHz)"
    elif Band == "1":
        sBand = "325 MHz -- 329 MHz (bandwidth: 4 MHz)"
    else:
        sBand = "327.275 MHz -- 327.525 MHz (bandwidth: 250 KHz)"


    print()
    print("--------------------------------------------")
    print("Frequency band: {:s}".format(sBand))
    print()
    print("\t\tTime interval\tNumber of files")
    for i in range(0,2):  # Pol
        # String to describe polarisation
        if Pol[i] == "H":
            sPol = "horizontal"
        else:
            sPol = "vertical"

        for j in range(0,3):  # Az
            TimeRange = EndTimes[i*3 + j] - StartTimes[i*3 + j]

            print()
            print("--------------------------------------------")
            print("Polarisation: {:s}; Azimuth: {:s} deg".format(sPol, Az[j]))
            print("{:s}  -->  {:s}\t{:.2f} day(s)\t{:d}".format(StartTimes[i*3 + j].strftime("%H:%M, %d %B %Y"), EndTimes[i*3 + j].strftime("%H:%M, %d %B %Y"), TimeRange / timedelta(hours=24), len(List[i*3 + j])))

    return(0)
###  END Function: Print runtime configurations  ###



###
###  Main Function
###

###  BEGIN Parsing of command line arguments  ###
try:
    if len(argv) <= 4:
        raise OSError
except OSError:
    print_help(argv[0])
    exit(1)


# Check validity of STARTDATE (argv[1]) and STARTTIME (argv[2])
try:
    if len(argv[1]) < 8:
        raise ValueError

    year = int(argv[1][:4])
    month = int(argv[1][4:6])
    day = int(argv[1][6:])
    hour = 0
    minute = 0

    StartTime = datetime(year, month, day, hour, minute)

except ValueError:
    print("Invalid start date/time!")
    exit(2)


# Check validity of ENDDATE (argv[3]) and ENDTIME (argv[4])
try:
    if len(argv[2]) < 8:
        raise ValueError

    year = int(argv[2][:4])
    month = int(argv[2][4:6])
    day = int(argv[2][6:])
    hour = 0
    minute = 0

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


# Check validity of BAND (argv[3])
try:
    if argv[3] not in {"0", "1", "2"}:
        raise ValueError
except ValueError:
    print("Invalid frequency band label!")
    exit(4)

Band = argv[3]


# Check validity of DATADIR (argv[4])
try:
    if not path.isdir(argv[4]):
        raise ValueError
except ValueError:
    print("Cannot access {:s}".format(argv[4]))
    exit(5)

DataPath = argv[4]


# Check if amplifier gain data files are accessible
try:
    if not path.isfile("AmpGain_band"+Band+".csv"):
        raise FileNotFoundError
except FileNotFoundError:
    print("Amplifier gain data file {:s} missing!".format("AmpGain_band"+Band+".csv"))
    exit(6)

###  END Parsing of command line arguments  ###



# Array for Polarisations and Azimuth angles
Pol = ["H", "V"]
Az = ["0", "120", "240"]



###  BEGIN Browse through file names  ###

try:
    # Search for files in time range and fill array of file names
    Files = []
    StartTimes = []
    EndTimes = []
    for i in range(0,2):  # Pol
        for j in range(0,3):  # Az
            tmp_Files = []
            tmp_Start,tmp_End = find_files(StartTime, EndTime, Pol[i], Az[j], Band, DataPath, tmp_Files)
            StartTimes.append(tmp_Start)
            EndTimes.append(tmp_End)
            Files.append(tmp_Files)

except FileNotFoundError:
    print("Error: Cannot find data files within input time interval with corresponding parameters.")
    exit(90)
except IndexError:
    print("Error: Time range contains only 1 file for corresponding parameters, cannot average!")
    exit(91)

###  END Browse through file names  ###



# Print runtime configurations/statistics
print_runconfig(Files, StartTimes, EndTimes, Band)


exit(0)
