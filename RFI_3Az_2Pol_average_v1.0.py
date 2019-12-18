#!/usr/bin/env python3
#
#  --  UNDER CONSTRUCTION  --
#
#  Script to average and plot RFI data obtained for Bras d'Eau, the location
#  of the Mauritius Deuterium Telescope (MDT).
#  A plot is made for each polarisation (H and V). Each plot contains the
#  average for the 3 distinct directions Az = 0, 120, 240 degrees. The results
#  are output to 2 different files, one for each polarisation.
#  Version 1.0
#
#  Copyright (c) 2019 Nitish Ragoomundun, Mauritius
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# ------------------------------------------------------------------------------
#


from sys import argv
from os import path
from random import seed,randint
from datetime import datetime,timedelta
from numpy import loadtxt,append,zeros,subtract,mean
import matplotlib.pyplot as plt
from matplotlib.ticker import EngFormatter


###
###  Constants
###

# Number of data values in each TXT data file
global NumRows
NumRows = 461

# Noise floor level of the spectrum analyzer was at -120dB
# So, we assumed that if on average, signal was below -118 dB,
# it means that amplifier was not functioning properly.
global SpectrumFloor
SpectrumFloor = -118.0

# Seed RNG
seed(21)


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



###  BEGIN Function: Check if amplifier was working correctly  ###
def CheckAmp(RawData):
    Mean = 0.0

    # Choose 40 random data points
    for i in range(0,40):
        Mean += RawData[randint(0, NumRows-1), 1]

    Mean *= 0.025

    if Mean <= SpectrumFloor:
        return(1)
    else:
        return(0)

###  END Function: Check if amplifier was working correctly  ###



###  BEGIN Function: Access files and load data into arrays  ###
def LoadData(List):

    # list of numpy arrays
    InputData = []

    try:
        for i in range(0,2):  # Pol
            for j in range(0,3):  # Az
                # List for rejected files
                Rejected = []

                # First file
                fileIdx = 0
                while fileIdx < len(List[i*3 + j]):
                    RawData = loadtxt(fname=List[i*3 + j][fileIdx], delimiter=',')
                    fileIdx += 1

                    if CheckAmp(RawData) == 0:
                        # Copy frequencies
                        FreqArray = RawData[:,0]
                        # Copy magnitudes
                        PowArray = RawData[:,1].reshape(NumRows, 1)
                        break
                    else:
                        Rejected.append(List[i*3 + j][fileIdx-1])

                # Loop through the rest of the list of files, copy data into array
                while fileIdx < len(List[i*3 + j]):
                    RawData = loadtxt(fname=List[i*3 + j][fileIdx], delimiter=',')

                    if CheckAmp(RawData) == 0:
                        PowArray = append(PowArray, RawData[:,1].reshape(NumRows,1), axis=1)
                    else:
                        Rejected.append(List[i*3 + j][fileIdx])

                    fileIdx += 1

                # Print the list of rejected files, if any
                if (len(Rejected) != 0):
                    print()
                    print("-> For configuration -- Polarisation: {:s}; Azimuth: {:s} deg,".format(Pol[i], Az[j]))
                    print("-> There were  {:d}  rejected files:-".format(len(Rejected)))
                    for i in range(0, len(Rejected)):
                        print("{:s}".format(Rejected[i].replace(DataPath+"/", "")))
                    print("-----------------------------------------------------------------------")


                # Add numpy power array to list
                InputData.append(PowArray)


        # Return data
        return(FreqArray, InputData)


    except OSError:
        raise OSError("Error when loading file {:s}".format(List[fileIdx]))
    except IndexError:
        raise IndexError("Error when loading data from file {:s} into array.".format(List[fileIdx]))

###  END Function: Access files and load data into arrays  ###



###  BEGIN Function: Subtract amplifier gain from raw data  ###
def subtract_AmpGain(InputData, Band):

    # Open amplifier gain data
    AmpGain = loadtxt(fname="AmpGain_band"+Band+".csv", delimiter=',')

    # Subtract
    Corrected = InputData
    for col in range(0, InputData.shape[1]):
        Corrected[:,col] = subtract(InputData[:,col], AmpGain[:,1])

    return(Corrected)

###  END Function: Subtract amplifier gain from raw data  ###



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
def print_runconfig(List, StartTimes, EndTimes, ActualTimeRanges, Band):

    # String to describe frequency bandwidth
    if Band == "0":
        sBand = "1 MHz -- 1 GHz (bandwidth: 999 MHz)"
    elif Band == "1":
        sBand = "325 MHz -- 329 MHz (bandwidth: 4 MHz)"
    else:
        sBand = "327.275 MHz -- 327.525 MHz (bandwidth: 250 KHz)"

    print()
    print("=> Frequency band: {:s}".format(sBand))
    print()
    print("Polarisation, direction, time range\t\t\tTime interval\tNumFiles expected  NumFiles available")
    print("-------------------------------------------------------------------------------------------------------------")
    for i in range(0,2):  # Pol
        for j in range(0,3):  # Az
            TimeRange = ActualTimeRanges[i*3 + j] / timedelta(hours=24)

            # Assume that between StartTime and EndTime, files should be uniformly
            # distributed with 15 minutes interval between them. The division by 9
            # is done because there are 9 different possible configurations.
            Ideal_numfiles = (ActualTimeRanges[i*3 + j] / 9) // timedelta(minutes=15)

            print()
            print("Polarisation: {:s}; Azimuth: {:s} deg".format(Pol[i], Az[j]))
            print("{:s}  -->  {:s}\t{:.2f} day(s)\t\t{:d}\t\t{:d}".format(StartTimes[i*3 + j].strftime("%H:%M, %d %B %Y"), EndTimes[i*3 + j].strftime("%H:%M, %d %B %Y"), TimeRange, Ideal_numfiles, len(List[i*3 + j])))
            print("-------------------------------------------------------------------------------------------------------------")

    StartTimes.sort()
    EndTimes.sort()
    print()
    print("Actual time span:  {:s}  -->  {:s}".format(StartTimes[0].strftime("%H:%M, %d %B %Y"), EndTimes[-1].strftime("%H:%M, %d %B %Y")))
    print("-----------------------------------------------------------------------")
    print()

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
    hour = 23
    minute = 59

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
    ActualTimeRanges = []
    Ideal_numfiles = []
    for i in range(0,2):  # Pol
        for j in range(0,3):  # Az
            tmp_Files = []
            tmp_Start,tmp_End = find_files(StartTime, EndTime, Pol[i], Az[j], Band, DataPath, tmp_Files)
            StartTimes.append(tmp_Start)
            EndTimes.append(tmp_End)

            # Calculate actual time range for each (Pol, Az) combination
            ActualTimeRanges.append(tmp_End - tmp_Start)


            # Add list of files to main array
            Files.append(tmp_Files)

except FileNotFoundError:
    print("Error: Cannot find data files within input time interval with corresponding parameters.")
    exit(90)
except IndexError:
    print("Error: Time range contains only 1 file for corresponding parameters, cannot average!")
    exit(91)

###  END Browse through file names  ###



###  BEGIN Opening files and loading data in array  ###

# First print runtime configuration settings and ask user for
# confirmation before proceeding.
print_runconfig(Files, StartTimes, EndTimes, ActualTimeRanges, Band)
Ans = input("\nDo you wish to proceed with calculations? (y/n)  ")
if Ans != "Y" and Ans != "y":
    exit(100)
else:
    # Proceed with normal execution of script
    try:
        Frequency, InputData = LoadData(Files)
        print()
        print(Frequency.shape)
        print()
        for i in range(0,2):
            for j in range(0,3):
                print("{:d},{:d} -- ({:d},{:d})".format(i, j, InputData[i*3 + j].shape[0], InputData[i*3 + j].shape[1]))

    except OSError as error1:
        msg = str(error1)
        print(msg.replace(DataPath+"/", ""))
        exit(101)
    except IndexError as error2:
        msg = str(error2)
        print(msg.replace(DataPath+"/", ""))
        exit(102)

###  END Opening files and loading data in array  ###



###  BEGIN Creating file to output results  ###

outfilenameH = argv[1] + "-" + argv[2] + "_H_" + Band + ".csv"
try:
    fout_H = open(outfilenameH, 'w')
except OSError:
    print("Cannot write file {:s} for output results!".format(outfilenameH))
    exit(111)

outfilenameV = argv[1] + "-" + argv[2] + "_V_" + Band + ".csv"
try:
    fout_V = open(outfilenameV, 'w')
except OSError:
    print("Cannot write file {:s} for output results!".format(outfilenameV))
    exit(112)

###  END Creating file to output results  ###




###  BEGIN Averaging and plotting  ###

Mean = []
for i in range(0, len(InputData)):
    # Subtract amplifier gain for the relevant band
    InputData[i] = subtract_AmpGain(InputData[i], Band)

    # Calculate mean of amplitudes for each frequency
    # (across columns/along rows: axis = 1)
    Mean.append(mean(InputData[i], axis=1))


# Output results to csv file
print("Writing output results for Polarisation H to {:s}".format(outfilenameH))
for k in range(0, len(Frequency)):
    fout_H.write("{:f}".format(Frequency[k]))
    for j in range(0,3):  # Az
        fout_H.write(",{:f}".format(Mean[j][k]))
    fout_H.write("\n")

fout_H.close()

print("Writing output results for Polarisation V to {:s}".format(outfilenameV))
for k in range(0, len(Frequency)):
    fout_V.write("{:f}".format(Frequency[k]))
    for j in range(0,3):  # Az
        fout_V.write(",{:f}".format(Mean[3 + j][k]))
    fout_V.write("\n")

fout_V.close()



exit(0)
