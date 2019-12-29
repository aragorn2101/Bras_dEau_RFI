#!/usr/bin/env python3
#
#  Script to average and plot RFI data obtained for Bras d'Eau, the location
#  of the Mauritius Deuterium Telescope (MDT).
#  The plot is made for only one direction and one polarisation. The result of
#  the average is output to a file named according to the period concerned.
#  Version 1.3
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
#  Changelog
#
#  1.1: 03.06.2019
#       * Added flagging of data for malfunctioned amplifier.
#  1.2: 07.08.2019
#       * Moved creation of numpy arrays to hold data into the function, which
#         also corrected for the numpy.append() malfunction.
#  1.3: 03.12.2019
#       * Added output to text file for average.
#       * Subtract amplifier gain according to experimental data.
#  1.4: 29.12.2019
#       * find_files() returns the list of files.
#       * Upgraded plotting to use Matplotlib Axes to prevent errors caused
#         by tight_layout().
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

    # Create empty list
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
#  Returns a numpy array of shape (NumRows x NumFiles) holding the power data.
#  Function also returns an array holding the frequency values; this is of
#  length NumRows.
#
def LoadData(List, Ideal_NFiles):

    # List for rejected files
    Rejected = []

    try:
        # First file
        fileIdx = 0
        while fileIdx < len(List):
            RawData = loadtxt(fname=List[fileIdx], delimiter=',')
            fileIdx += 1

            if CheckAmp(RawData) == 0:
                # Copy frequencies
                FreqArray = RawData[:,0]
                # Copy magnitudes
                PowArray = RawData[:,1].reshape(NumRows, 1)
                break
            else:
                Rejected.append(List[fileIdx-1])


        # Loop through the rest of the list of files, copy data into array
        while fileIdx < len(List):
            RawData = loadtxt(fname=List[fileIdx], delimiter=',')

            if CheckAmp(RawData) == 0:
                PowArray = append(PowArray, RawData[:,1].reshape(NumRows,1), axis=1)
            else:
                Rejected.append(List[fileIdx])

            fileIdx += 1

        # Print the list of rejected files, if any
        if len(Rejected) != 0:
            print()
            print("-> The following file(s) had invalid values of signal power:")
            print("-> (possibly indicating amplifier malfunction)")
            for i in range(0, len(Rejected)):
                print("{:s}".format(Rejected[i].replace(DataPath+"/", "")))

            print("\n-> Total number of useful files therefore: {:d}".format(len(List) - len(Rejected)))

            if (len(List) - len(Rejected))/Ideal_NFiles < 1.0:
                print("-> Number of files expected in time interval: {:d}".format(Ideal_NFiles))
                print("-> Percentage completeness: {:6.2f}%".format((len(Files) - len(Rejected))/Ideal_NFiles * 100))
            print()


        # Return numpy arrays
        return(FreqArray, PowArray)


    except OSError:
        raise OSError("Error when loading file {:s}".format(List[fileIdx]))
    except IndexError:
        raise IndexError("Error when loading data from file {:s} into array.".format(List[fileIdx]))

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
    print("Usage: {:s} STARTDATE STARTTIME ENDDATE ENDTIME POL AZ BAND DATADIR".format(ScriptName))
    print("\nSTARTDATE: initial date for averaging in format YYYYMMDD")
    print("STARTTIME: starting time on the initial date in format HHmm")
    print("ENDDATE: closing date for range of data to be considered in format YYYYMMDD")
    print("ENDTIME: last time on the closing date in format HHmm")
    print("POL: polarisation (only parameters \'H\' or \'V\' are accepted)")
    print("AZ: direction along which measurements were taken, in terms of Azimuth angle)")
    print("    (only 0, 120 or 240 are valid)\n");
    print("BAND: frequency band of measurements, the accepted inputs for this parameter")
    print("      are only 0, 1 or 2. The meaning of each label are as follows:\n")
    print("      0 :       1 MHz --       1 GHz (bandwidth: 999 MHz)")
    print("      1 :     325 MHz --     329 MHz (bandwidth:   4 MHz)")
    print("      2 : 327.275 MHz -- 327.525 MHz (bandwidth: 250 KHz)\n")
    print("DATADIR: path of the directory holding the .TXT data files\n")
    print("Example:")
    print("{:s} 20190415 0700 20190430 2245 H 0 1 ./txtDataFiles\n".format(ScriptName))
    print("The above command will look for data in directory txtDataFiles found in current")
    print("directory. Data files should range from 07:00, April 15th, 2019 to 22:45, May")
    print("5th 2019. The measured polarisation sought is horizontal (H), for direction")
    print("Azimuth = 0 degrees, in the frequency band 1, i.e.  325 MHz -- 329 MHz.")
    print()

    return(0)
###  END Function: Print help  ###



###  BEGIN Function: Print runtime configurations  ###
#
#  Prints message and returns 0
#
def print_runconfig(List, Ideal_NFiles, StartTime, EndTime, TimeRange, Pol, Az, Band, DataPath):

    # String to describe frequency bandwidth
    if Band == "0":
        sBand = "1 MHz -- 1 GHz (bandwidth: 999 MHz)"
    elif Band == "1":
        sBand = "325 MHz -- 329 MHz (bandwidth: 4 MHz)"
    else:
        sBand = "327.275 MHz -- 327.525 MHz (bandwidth: 250 KHz)"

    print()
    print("First file:\t{:s}".format(List[0].replace(DataPath+"/", "")))
    print("Last file:\t{:s}".format(List[-1].replace(DataPath+"/", "")))

    print()
    print("Actual time range (corrected w.r.t available files)")
    print("and current parameters:")
    print()
    print("{:s}  -->  {:s}".format(StartTime.strftime("%H:%M, %d %B %Y"), EndTime.strftime("%H:%M, %d %B %Y")))
    print()
    print("Length of time interval:  {:.2f} day(s)".format(TimeRange / timedelta(hours=24)))
    print("Polarisation: {:s}".format(Pol))
    print("Azimuth: {:s} deg".format(Az))
    print("Frequency band: {:s}".format(sBand))

    print()
    print("Total number of files in time range: {:d}".format(len(List)))
    if len(List)/Ideal_NFiles < 1.0:
        print("Number of files expected in time interval: {:d}".format(Ideal_NFiles))
        print("Percentage completeness: {:6.2f}%".format(len(List)/Ideal_NFiles * 100))
    print()

    return(0)
###  END Function: Print runtime configurations  ###



###
###  Main Function
###

###  BEGIN Parsing of command line arguments  ###
try:
    if len(argv) <= 8:
        raise OSError
except OSError:
    print_help(argv[0])
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
    if argv[5] not in {"H", "V"}:
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


# Check if amplifier gain data files are accessible
try:
    if not path.isfile("AmpGain_band"+Band+".csv"):
        raise FileNotFoundError
except FileNotFoundError:
    print("Amplifier gain data file {:s} missing!".format("AmpGain_band"+Band+".csv"))
    exit(8)

###  END Parsing of command line arguments  ###



###  BEGIN Browse through file names  ###

try:
    # Search for files in time range and fill array of file names
    Files, StartTime, EndTime = find_files(StartTime, EndTime, Pol, Az, Band, DataPath)

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
ActualTimeRange = EndTime - StartTime

# Assume that between StartTime and EndTime, files should be uniformly
# distributed with 15 minutes interval between them. The division by 9
# is done because there are 9 different possible configurations.
Ideal_numfiles = (ActualTimeRange / 9) // timedelta(minutes=15)

# Print runtime configurations/statistics
print_runconfig(Files, Ideal_numfiles, StartTime, EndTime, ActualTimeRange, Pol, Az, Band, DataPath)

# Prompt user
print()
Ans = input("Do you wish to proceed with calculations? (y/n)  ")
if Ans != "Y" and Ans != "y":
    exit(100)
else:
    # Proceed with normal execution of script
    try:
        Frequency, InputData = LoadData(Files, Ideal_numfiles)
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
outfilename = argv[1] + "_" + argv[2] + "-" + argv[3] + "_" + argv[4] + "_" + Pol + Az + "_" + Band + ".csv"

try:
    fout = open(outfilename, 'w')
except OSError:
    print("Cannot write file {:s} for output results!".format(outfilename))
    exit(111)

###  END Creating file to output results  ###



###  BEGIN Averaging and plotting  ###

# Subtract amplifier gain for the relevant band
InputData = subtract_AmpGain(InputData, Band)

# Calculate mean of amplitudes for each frequency
# (across columns/along rows: axis = 1)
Mean = mean(InputData, axis=1)


# Output results to csv file
print("Writing output results to {:s}".format(outfilename))
for i in range(0, len(Frequency)):
    fout.write("{:f},{:f}\n".format(Frequency[i], Mean[i]))

fout.close()


# Plot
print("Generating plot ...")

xLowerLim = Frequency[0]
xUpperLim = Frequency[-1]

fig, ax = plt.subplots(1,1)
plt.tight_layout()

ax.set_title("{:s} -- {:s} (Pol {:s}, Az {:s}{:s}, Band {:s})".format(StartTime.strftime("%H:%M, %d %B %Y"), EndTime.strftime("%H:%M, %d %B %Y"), Pol, Az, chr(176), Band))
ax.set_xlabel("Frequency", fontsize=12)

# Custom labels on the frequency axis, since different frequency bands
# are strictly defined.
if Band == "0":
    ax.set_xlim(1e6, 1e9)
    ax.set_.xticks([1e6, 125e6, 250e6, 375e6, 500e6, 625e6, 750e6, 875e6, 1e9])
    formatter = EngFormatter(unit="Hz", places=0)
elif Band == "1":
    ax.set_xlim(325.0e6, 329.0e6)
    ax.set_xticks([325.0e6, 325.5e6, 326.0e6, 326.5e6, 327.0e6, 327.5e6, 328.0e6, 328.5e6, 329.0e6])
    formatter = EngFormatter(unit="Hz", places=1)
else:
    ax.set_xlim(327.275e6, 327.525e6)
    ax.set_xticks([327.275e6, 327.325e6, 327.400e6, 327.475e6, 327.525e6])
    formatter = EngFormatter(unit="Hz", places=3)

ax.xaxis.set_major_formatter(formatter)
ax.tick_params(labelsize=14)
ax.set_ylabel("Mean power / dBm", fontsize=12)
ax.grid(True)
ax.plot(Frequency, Mean, color="brown")

plt.show()

###  END Averaging and plotting  ###

exit(0)
