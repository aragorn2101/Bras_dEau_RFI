#!/usr/bin/env python3
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
# -----------------------------------------------------------------------------
#
#  Changelog
#
#  1.1: 26.12.2019
#       * Used more sensible indices for Pol and Az in loops to avoid
#         conflict with the common i,j
#       * Reduced the quadruple loops for writing output results to
#         only 2 loops
#       * Function find_files() returns List
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
# This is the number of frequency values at which power was measured.
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
#
#  Returns full path of the expected data file with the appropriate name.
#
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
#
#  Returns list of files, start time (time stamp for the first data file),
#  and end time (time stamp for last data file)
#  The list is of length NumFiles - the number of data files available for the
#  input parameters.
#
def find_files(StartTime, EndTime, Pol, Az, Band, DataPath):
    dt1 = timedelta(minutes = 1)
    dt2 = timedelta(minutes = 15)

    # Create list
    List = []

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
                print("For configuration -- Pol: {:s}; Az = {:s}".format(Pol, Az))
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
        print("For configuration -- Pol: {:s}; Az = {:s}".format(Pol, Az))
        raise IndexError

    EndTime = LastOne
    return(List, StartTime, EndTime)

###  END Function: Find files and make list  ###



###  BEGIN Function: Check if amplifier was working correctly  ###
#
#  Returns: 0 if data valid,
#           1 if invalid data values due to amplifier malfunction.
#
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
#
#  Returns a list of length 6 (2 Pol x 3 Az)
#  Each element in the list is a numpy array of shape (NumRows x NumFiles),
#  and holds the power data in dBm.
#  Function also returns an array holding the frequency values; this is of
#  length NumRows.
#
def LoadData(List):

    # list of numpy arrays
    Data = []

    try:
        for p in range(0,2):  # Pol
            for a in range(0,3):  # Az
                # List for rejected files
                Rejected = []

                # First file
                fileIdx = 0
                while fileIdx < len(List[p*3 + a]):
                    RawData = loadtxt(fname=List[p*3 + a][fileIdx], delimiter=',')
                    fileIdx += 1

                    if CheckAmp(RawData) == 0:
                        # Copy frequencies
                        FreqArray = RawData[:,0]
                        # Copy magnitudes
                        PowArray = RawData[:,1].reshape(NumRows, 1)
                        break
                    else:
                        Rejected.append(List[p*3 + a][fileIdx-1])

                # Loop through the rest of the list of files, copy data into array
                while fileIdx < len(List[p*3 + a]):
                    RawData = loadtxt(fname=List[p*3 + a][fileIdx], delimiter=',')

                    if CheckAmp(RawData) == 0:
                        PowArray = append(PowArray, RawData[:,1].reshape(NumRows,1), axis=1)
                    else:
                        Rejected.append(List[p*3 + a][fileIdx])

                    fileIdx += 1

                # Print the list of rejected files, if any
                if (len(Rejected) != 0):
                    print()
                    print("-> For configuration -- Polarisation: {:s}; Azimuth: {:s} deg,".format(Pol[p], Az[a]))
                    print("-> There were  {:d}  rejected file(s):-".format(len(Rejected)))
                    for i in range(0, len(Rejected)):
                        print("{:s}".format(Rejected[i].replace(DataPath+"/", "")))
                    print("-----------------------------------------------------------------------")


                # Add numpy power array to list
                Data.append(PowArray)


        # Return data
        return(FreqArray, Data)


    except OSError:
        raise OSError("Error when loading file {:s}".format(List[p*3 + a][fileIdx]))
    except IndexError:
        raise IndexError("Error when loading data from file {:s} into array.".format(List[p*3 + a][fileIdx]))

###  END Function: Access files and load data into arrays  ###



###  BEGIN Function: Subtract amplifier gain from raw data  ###
#
#  Returns array of shape (NumRows x NumFiles), same shape as
#  the InputData array passed to function.
#
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
#
#  Prints message and returns 0
#
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
    print("directory. Data files will range from 00:00, April 15th, 2019 to 23:59, May 5th")
    print("2019. The script will look for both H and V polarisations and also data for all")
    print("three directions, i.e. Azimuth = {0, 120, 240}. The results of the average for")
    print("each of the 6 combinations are calculated. Two plots are made for each")
    print("polarisations with all 3 directions displayed on the same plot. The results are")
    print("also written to two different files, one for each polarisation.")
    print()

    return(0)

###  END Function: Print help  ###



###  BEGIN Function: Print runtime configurations  ###
#
#  Prints message and returns 0
#
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
    for p in range(0,2):  # Pol
        for a in range(0,3):  # Az
            TimeRange = ActualTimeRanges[p*3 + a] / timedelta(hours=24)

            # Assume that between StartTime and EndTime, files should be uniformly
            # distributed with 15 minutes interval between them. The division by 9
            # is done because there are 9 different possible configurations.
            Ideal_numfiles = (ActualTimeRanges[p*3 + a] / 9) // timedelta(minutes=15)

            print()
            print("Polarisation: {:s}; Azimuth: {:s} deg".format(Pol[p], Az[a]))
            print("{:s}  -->  {:s}\t{:.2f} day(s)\t\t{:d}\t\t{:d}".format(StartTimes[p*3 + a].strftime("%H:%M, %d %B %Y"), EndTimes[p*3 + a].strftime("%H:%M, %d %B %Y"), TimeRange, Ideal_numfiles, len(List[p*3 + a])))
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
###  Main program
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
    for p in range(0,2):  # Pol
        for a in range(0,3):  # Az
            tmp_Files, tmp_Start, tmp_End = find_files(StartTime, EndTime, Pol[p], Az[a], Band, DataPath)

            # Calculate actual time range for each (Pol, Az) combination
            ActualTimeRanges.append(tmp_End - tmp_Start)

            # Append list of files and times to the relevant arrays
            Files.append(tmp_Files)
            StartTimes.append(tmp_Start)
            EndTimes.append(tmp_End)

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
for i in range(0,6):  # 2 Pol x 3 Az
    # Subtract amplifier gain from data values for relevant band
    CorrectedData = subtract_AmpGain(InputData[i], Band)

    # Calculate mean of amplitudes for each frequency
    # (across columns/along rows: axis = 1)
    Mean.append(mean(CorrectedData, axis=1))


# Output results to csv file
print()
print("Writing output results for Polarisation H to {:s} and Polarisation V to {:s}".format(outfilenameH, outfilenameV))
for i in range(0, len(Frequency)):
    # Write frequency values
    fout_H.write("{:f}".format(Frequency[i]))
    fout_V.write("{:f}".format(Frequency[i]))

    # Write averages for each direction
    for a in range(0,3):  # Az
        fout_H.write(",{:f}".format(Mean[a][i]))
        fout_V.write(",{:f}".format(Mean[3 + a][i]))

    fout_H.write("\n")
    fout_V.write("\n")

fout_H.close()
fout_V.close()


# Plot
print("Generating plots ...")

xLowerLim = Frequency[0]
xUpperLim = Frequency[-1]

fig = [[],[]]
ax  = [[],[]]
colours = ["orange", "blue", "green"]

for p in range(0,2):  # Pol

    fig[p], ax[p] = plt.subplots(1,1)
    plt.tight_layout()

    ax[p].set_title("{:s} -- {:s} (Pol: {:s}, Band {:s})".format(StartTime.strftime("%d %B %Y"), EndTime.strftime("%d %B %Y"), Pol[p], Band))
    ax[p].set_xlabel("Frequency", fontsize=12)

# Custom labels on the frequency axis, since different frequency bands
# are strictly defined.
    if Band == "0":
        ax[p].set_xlim(1e6, 1e9)
        ax[p].set_xticks([1e6, 125e6, 250e6, 375e6, 500e6, 625e6, 750e6, 875e6, 1e9])
        formatter = EngFormatter(unit="Hz", places=0)
    elif Band == "1":
        ax[p].set_xlim(325.0e6, 329.0e6)
        ax[p].set_xticks([325.0e6, 325.5e6, 326.0e6, 326.5e6, 327.0e6, 327.5e6, 328.0e6, 328.5e6, 329.0e6])
        formatter = EngFormatter(unit="Hz", places=1)
    else:
        ax[p].set_xlim(327.275e6, 327.525e6)
        ax[p].set_xticks([327.275e6, 327.350e6, 327.400e6, 327.450e6, 327.525e6])
        formatter = EngFormatter(unit="Hz", places=3)

    ax[p].xaxis.set_major_formatter(formatter)
    ax[p].tick_params(labelsize=14)
    ax[p].set_ylabel("Mean Amplitude / dBm", fontsize=12)
    ax[p].grid(True)
    for a in range(0,3):  # Az
        ax[p].plot(Frequency, Mean[p*3 + a], color=colours[a], label="Az = "+Az[a]+chr(176))

    # Legend
    ax[p].legend(loc="upper right", bbox_to_anchor=(0.93,0.97), frameon=True)

plt.show()

###  END Averaging and plotting  ###

exit(0)
