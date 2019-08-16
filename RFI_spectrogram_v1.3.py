#!/usr/bin/env python3
#
#  Script to make spectrogram plots of the RFI data for the Mauritius Deuterium
#  Telescope (MDT) location at Bras d'Eau.
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
# Changelog
#
# 1.1: 07.08.2019
#      * Moved creation of numpy arrays to hold data into the function, which
#        also corrected for the numpy.append() malfunction.
# 1.2: 13.08.2019
#      * Plot frequency on y-axis and time on x-axis to better conform to
#        standards for spectrogram plots.
#
# 1.3: 16.08.2019
#      * Added correction for amplifier gains.
#


from sys import argv
from os import path
from time import time
from random import seed,randint
from datetime import datetime,timedelta
from numpy import loadtxt,append,ones,subtract,mean,arange,meshgrid
import matplotlib.pyplot as plt
from matplotlib.ticker import EngFormatter,MaxNLocator
from matplotlib.colors import BoundaryNorm


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

# Amplifiers gain in each band
# +20 dB in band 0
# +40 dB in bands 1 and 2
global Gain
Gain = [20, 40, 40]
#        0   1   2

# Seed RNG
seed(time())


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
    DateTime = StartTime  # temporary storage

    # Find the first file
    while True:
        Filename = construct_filename(StartTime, Pol, Az, Band, DataPath)

        if path.isfile(Filename):

            # If there is a big gap between start of the day to the start
            # of the data, fill the gap with null
            if StartTime > DateTime + dt2:
                while DateTime < StartTime:
                    List.append("0")
                    DateTime += dt2

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

            LastOne = DateTime

            # If there is a big gap between previous file's timestamp and
            # the next file, fill the gap with null
            if DateTime > LastOne + dt2:
                while LastOne < DateTime:
                    List.append("0")
                    LastOne += dt2

            List.append(Filename)
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

    # If there is a big gap between the last file's timestamp and
    # the end of the day, fill the gap with null
    if EndTime > LastOne + dt2:
        while LastOne < EndTime:
            List.append("0")
            LastOne += dt2

    EndTime = LastOne - dt2

    return(StartTime,EndTime)

###  END Find files and make list  ###



###  BEGIN Check if amplifier was working correctly  ###
def CheckAmp(RawData):
    Mean = 0.0

    # Choose 40 random data points, sum and divide by 40
    for i in range(0,40):
        Mean += RawData[randint(0, NumRows-1), 1]

    Mean *= 0.025

    if Mean <= SpectrumFloor:
        return(1)
    else:
        return(0)

###  END Check if amplifier was working correctly  ###



###  BEGIN Access files and load data into arrays  ###
def LoadData(List, Ideal_NFiles):

    # List for rejected files
    Rejected = []

    try:
        # First file
        fileIdx = 0
        if List[fileIdx] == "0":
            PowArray = SpectrumFloor * ones((NumRows,1))
        else:
            RawData = loadtxt(fname=List[0], delimiter=',')

            # Copy frequencies
            FreqArray = RawData[:,0]

            if CheckAmp(RawData) == 0:
                # Copy magnitudes
                PowArray = RawData[:,1].reshape(NumRows,1)
            else:
                PowArray = SpectrumFloor * ones((NumRows,1))
                Rejected.append(List[0])


        # Loop through the rest of the list of files, copy data into array
        fileIdx += 1
        while fileIdx < len(List):
            if List[fileIdx] == "0":
                PowArray = append(PowArray, SpectrumFloor * ones((NumRows,1)), axis=1)
            else:
                RawData = loadtxt(fname=List[fileIdx], delimiter=',')

                if "FreqArray" not in dir():
                    FreqArray = RawData[:,0]

                if CheckAmp(RawData) == 0:
                    PowArray = append(PowArray, RawData[:,1].reshape(NumRows,1), axis=1)
                else:
                    PowArray = append(PowArray, SpectrumFloor * ones((NumRows,1)), axis=1)
                    Rejected.append(List[fileIdx])

            fileIdx += 1


        if len(Rejected) != 0:
            print()
            print("-> These files had invalid values of signal power:")
            print("-> (possibly indicating amplifier malfunction)")
            for i in range(0, len(Rejected)):
                print("{:s}".format(Rejected[i].replace(DataPath+"/", "")))

            print("\n-> Total number of useful files therefore: {:d}".format(len(List) - len(Rejected)))

            if (len(List) - len(Rejected))/Ideal_NFiles < 1.0:
                print("-> Number of files expected in time interval: {:d}".format(Ideal_NFiles))
                print("-> Percentage completeness: {:6.2f}%".format((len(List) - len(Rejected))/Ideal_NFiles * 100))
            print()


        # Return numpy arrays
        return(FreqArray, PowArray)


    except OSError:
        raise OSError("Error when loading file {:s}.".format(List[fileIdx]))
    except IndexError:
        raise IndexError("Error when loading data from file {:s} into array.".format(List[fileIdx]))

###  END Access files and load data into arrays  ###



###  BEGIN Print help  ###
def print_help(ScriptName):
    print()
    print("Usage: {:s} DATE POL AZ BAND DATADIR".format(ScriptName))
    print("\nDATE: date in format YYYYMMDD for which spectrogram will be plotted")
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
    print("{:s} 20190307 H 240 1 ./txtDataFiles\n".format(ScriptName))
    print("The above command will look for data in directory txtDataFiles found in current")
    print("directory. Data files searched will be in the range 00:00 -- 23:59, March 7th,")
    print("2019.  The measured polarisation sought is vertical (V), for direction")
    print("Azimuth = 240 degrees, in the frequency band 1, i.e.  325 MHz -- 329 MHz.")
    print()

    return(0)
###  END Print help  ###



###  BEGIN Print runtime configurations  ###
def print_runconfig(List, Ideal_NFiles, StartTime, EndTime, TimeRange, Pol, Az, Band, DataPath):

    # Look for first file, last file and total number of potentially valid
    # file in the array
    firstfileIdx = 0
    lastfileIdx = 0
    NumFiles = 0
    for i in range(0, len(List)):
        if List[i] == "0":
            continue
        else:
            if firstfileIdx == 0:
                firstfileIdx = i

            lastfileIdx = i
            NumFiles += 1

    # String to describe polarisation
    if Pol == "H":
        sPol = "horizontal"
    else:
        sPol = "vertical"

    # String to describe frequency bandwidth
    if Band == "0":
        sBand = "1 MHz -- 1 GHz (bandwidth: 999 MHz)"
    elif Band == "1":
        sBand = "325 MHz -- 329 MHz (bandwidth: 4 MHz)"
    else:
        sBand = "327.275 MHz -- 327.525 MHz (bandwidth: 250 KHz)"

    print()
    print("First file:\t{:s}".format(List[firstfileIdx].replace(DataPath+"/", "")))
    print("Last file:\t{:s}".format(List[lastfileIdx].replace(DataPath+"/", "")))

    print()
    print("Time range and current parameters:")
    print()
    print("{:s}  -->  {:s}".format(StartTime.strftime("%H:%M, %d %B %Y"), EndTime.strftime("%H:%M, %d %B %Y")))
    print()
    print("Length of time interval:  {:.2f} day(s)".format(TimeRange / timedelta(hours=24)))
    print("Polarisation: {:s}".format(sPol))
    print("Azimuth: {:s} deg".format(Az))
    print("Frequency band: {:s}".format(sBand))

    print()
    print("Total number of files in time range: {:d}".format(NumFiles))
    if NumFiles/Ideal_NFiles < 1.0:
        print("Number of files expected in time interval: {:d}".format(Ideal_NFiles))
        print("Percentage completeness: {:6.2f}%".format(NumFiles/Ideal_NFiles * 100))
    print()

    return(0)
###  END Print runtime configurations  ###



###
###  Main Function
###

###  BEGIN Parsing of command line arguments  ###
try:
    if len(argv) <= 5:
        raise OSError
except OSError:
    print_help(argv[0])
    exit(1)


# Check validity of DATE (argv[1])
try:
    if len(argv[1]) < 8:
        raise ValueError

    year = int(argv[1][:4])
    month = int(argv[1][4:6])
    day = int(argv[1][6:])

    StartTime = datetime(year, month, day, 0, 0)
    EndTime   = datetime(year, month, day, 23, 59)

except ValueError:
    print("Invalid start date/time!")
    exit(2)


# Check validity of POL (argv[2])
try:
    if argv[2] not in {"H", "V"}:
        raise ValueError
except ValueError:
    print("Invalid polarisation!")
    exit(3)

Pol = argv[2]


# Check validity of DIR (argv[3])
try:
    if argv[3] not in {"0", "120", "240"}:
        raise ValueError
except ValueError:
    print("Invalid Azimuth angle for direction!")
    exit(4)

Az = argv[3]


# Check validity of BAND (argv[4])
try:
    if argv[4] not in {"0", "1", "2"}:
        raise ValueError
except ValueError:
    print("Invalid frequency band label!")
    exit(5)

Band = argv[4]


# Check validity of DATADIR (argv[5])
try:
    if not path.isdir(argv[5]):
        raise ValueError
except ValueError:
    print("Cannot access {:s}".format(argv[5]))
    exit(6)

DataPath = argv[5]

###  END Parsing of command line arguments  ###



###  BEGIN Browse through file names  ###

Files = []
try:
    # Search for files in time range and fill array of file names
    find_files(StartTime, EndTime, Pol, Az, Band, DataPath, Files)

except FileNotFoundError:
    print("Error: Cannot find data files within input time interval with corresponding parameters.")
    exit(80)
except IndexError:
    print("Error: Time range contains only 1 file for corresponding parameters, cannot average!")
    exit(81)

###  END Browse through file names  ###



###  BEGIN Opening files and loading data in array  ###

# First print runtime configuration settings and ask user for
# confirmation before proceeding.
TimeRange = EndTime - StartTime

# Assume that between StartTime and EndTime, files should be uniformly
# distributed with 15 minutes interval between them.
Ideal_numfiles = TimeRange // timedelta(minutes=15)


# Print runtime configurations/statistics
print_runconfig(Files, Ideal_numfiles, StartTime, EndTime, TimeRange, Pol, Az, Band, DataPath)

# Prompt user
Ans = input("Do you wish to proceed with calculations? (y/n)  ")
if Ans != "Y" and Ans != "y":
    exit(90)
else:
    # Proceed with normal execution of script
    try:
        Frequency, InputData = LoadData(Files, Ideal_numfiles)
    except OSError as error1:
        msg = str(error1)
        print(msg.replace(DataPath+"/", ""))
        exit(91)
    except IndexError as error2:
        msg = str(error2)
        print(msg.replace(DataPath+"/", ""))
        exit(92)

###  END Opening files and loading data in array  ###



###  BEGIN Plotting  ###

# Subtract amplifier gain
InputData = subtract(InputData, Gain[int(Band)])

# Colour map and spectrum representing range of dB
cmap = plt.get_cmap('jet')
levels = MaxNLocator(nbins=64).tick_values(InputData.min(), InputData.max())
norm = BoundaryNorm(levels, ncolors=cmap.N, clip=True)

# Define figure
fig = plt.figure(1)
ax = plt.subplot(1,1,1)
ax.set_title("RFI spectrogram -- {:s} (Pol {:s}, Az {:s}{:s}, Band {:s})".format(StartTime.strftime("%d %B %Y"), Pol, Az, chr(176), Band))

# x-axis parameters
x = arange(0, len(Files), 1)
ax.set_xlabel("Time (Mauritius local time - hh:mm)")
ax.set_xticks(arange(0, len(Files), 8))  # a tick every 2 hours
datelist = [(StartTime + i*timedelta(minutes = 60)).strftime("%H:%M") for i in range(0,24,2)]
ax.set_xticklabels(datelist)

# y-axis parameters
y = arange(0, 461, 1)
ax.set_ylabel("Frequency")

if Band == "0":
    plt.ylim(1e6, 1e9)
    plt.yticks([1e6, 125e6, 250e6, 375e6, 500e6, 625e6, 750e6, 875e6, 1e9])
    formatter = EngFormatter(unit="Hz", places=0)
elif Band == "1":
    plt.ylim(325.0e6, 329.0e6)
    plt.yticks([325.0e6, 325.5e6, 326.0e6, 326.5e6, 327.0e6, 327.5e6, 328.0e6, 328.5e6, 329.0e6])
    formatter = EngFormatter(unit="Hz", places=1)
else:
    plt.ylim(327.275e6, 327.525e6)
    plt.yticks([327.275e6, 327.350e6, 327.400e6, 327.450e6, 327.525e6])
    formatter = EngFormatter(unit="Hz", places=3)

ax.yaxis.set_major_formatter(formatter)

# Create image
img = ax.pcolormesh(x, Frequency, InputData, cmap=cmap, norm=norm)
fig.colorbar(img, ax=ax, label="dB", aspect=40)

plt.tight_layout()
plt.show()

###  END Plotting  ###

exit(0)
