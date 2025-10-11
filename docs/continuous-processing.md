# Processing of Continuous Data

## Current Processing Pipeline

1. Perform Pulse Processing
2. Try tag-and-calibrate
3. If it fails, drop channels
4. Re-run tag-and-calibrate
5. Aggregate wihin dataset
6. Aggregate datasets

Following processing:

1. Fit
2. ???
3. Profit

## Data of Interest

Drew has chewed some of the data from 07-15 to 07-19 which per his set are Ta PR mask chips.

I am interested in the later data between 8-1 to 8-21 Al PR mask:

- `/data_fast/beest/6-History/2024/6ALY-2024-08-05-32Al130_7Be/in/Data-CRONOS/summer2024/magcycle-11-2024-08-14`
- `/data_fast/beest/6-History/2024/6ALY-2024-08-05-32Al130_7Be/in/Data-CRONOS/summer2024/magcycle-12-2024-08-15`
- `/data_fast/beest/6-History/2024/6ALY-2024-08-05-32Al130_7Be/in/Data-CRONOS/summer2024/magcycle-13-2024-08-16`
- `/data_fast/beest/6-History/2024/6ALY-2024-08-05-32Al130_7Be/in/Data-CRONOS/summer2024/magcycle-14-2024-08-18`
- `/data_fast/beest/6-History/2024/6ALY-2024-08-05-32Al130_7Be/in/Data-CRONOS/summer2024/magcycle-15-2024-08-19`
- `/data_fast/beest/6-History/2024/6ALY-2024-08-05-32Al130_7Be/in/Data-CRONOS/summer2024/magcycle-16-2024-08-20`

## Processing Log

- magcycle-11-2024-08-14: processed
- magcycle-12-2024-08-15: processed
- magcycle-13-2024-08-16: processed
- magcycle-14-2024-08-18: processed (date:: 2025-05-22)
- magcycle-15-2024-08-19: processed (date:: 2025-05-20)
- magcycle-16-2024-08-20: scheduled (date:: 2025-05-20)

### (date:: 30 Apr 2025)

``parallel -v -j36 "`realpath chewOneFile.sh` 0 {}" :::: <(basename -a .root/in/Data-CRONOS/summer2024/magcycle-11-2024-08-14/*Sig_A.tdms)``

### (date:: 2025-05-22)

`nice -n10 ./chewerJobA.sh magcycle-14-2024-08-18`

## Tag and Calibrate Log

### (date:: 2025-05-01)

- magcycle-11-2024-08-14: Processing got about halfway through before tdms repair failed.
  - `20240815-112132.234131_Laser_A.tdms`: improperly formatted file
  - `chewed_metadata_20240815-020101.775106_Sig_B.h5`, `ch10`: no KGS peak found
- magcycle-12-2024-08-15: bad channels = [9, 10, 11, 13, 14, 15]
  - Got all the way through the tagging and tagger, but also failed on a `ch10` with no K-GS.
  - `chewed_metadata_20240816-003746.228601_Sig_B.h5`
- magcycle-13-2024-08-16: bad channels = [9, 10, 11, 13, 14, 15]
  - Same thing: channel 10 is bad.
  - `chewed_metadata_20240816-235931.762934_Sig_B.h5`

### (date:: 2025-05-08)

- magcycle-11-2024-08-14: Processed successfully after dropping bad channels.

### (date:: 2025-08-12)

- Re-dropped bad channels. See `config-drop-channels.py` for the channels dropped.

### (date:: 2025-08-14)

```bash
parallel --lb -k python -u tag-and-calibrate-oneset.py -f {} ::: *Sig_A.h5
```

### (date:: 2025-08-11)

I have made progress creating a parallelized version of the tagger/calibrator.
Further, I am debugging why the calibration is failing because I need the laser calibration of the nuclear data to work out, otherwise my paper will reference data that was calibrated by hand.
I am running

```bash
python tag-and-calibrate-oneset.py -f .root/out/process/cycle11-2024-08-14/processed/chewed_metadata_20240815-020101.775106_Sig_A.h5;
```

as my debug example, and am noticing

1. The calibration is failing because the tolerance for the peak fit is bigger than 0.2 (default). I can configure that in tag-and-calibrate-oneset as a Config key
2. The drift correction is giving mean of empty slice and divide issue warnings - I need to move my print statement into there to see what is bad when calibration fails
3. Channel 9 of the data above doesn't have any nuclear data - I either need more files or to simply mandate that the K-GS is around 0.01 regardless of if there's data

The parallelized processing is working [using this](../code/continuous-processing/tag-and-calibrate-oneset.py). A key discovery was that the values passed to the FFT have to be greater than 1, otherwise the FFT frequencies will be off. A boon of getting this working is that the calibration no longer relies on nuclear data because it can use the laser FFT to find an initial guess for the comb fit.

It appears channel 9 data - which comes from a bad channel presumably already removed around (date:: 2025-05-01) - has made its way back into the dataset. I intend to try removing it again. Now that I have my calibration code fail on any error, I must resolve these issues one-by-one before I can check off a file as successfully processed.

The rest of the processing threads also failed giving a resource temporarily unavailable error. Could this be from reading or actually writing? Further, if the laser script gets multiple files to look in and then concatenates those files, how is it that data from those files isn't ending up in the current file? If it was I would be expecting to see more than one unique filename in each file. So somehow this contamination isn't happening, but I don't trust it, especially given this unavailable error.  (unique filename solved, [c.f.](</home/sfretwell/beest/6-History/2024/6ALY-2024-08-05-32Al130_7Be/bin/process/dev-laser-calibration.ipynb>))

### (date:: 2025-08-12)

Updated the `drop_channels.py` script to allow for a channel map to be passed in, which allows for dropping channels based on the cycle. This allows parallelization over cycles, though the better way would be to parallelize over chunks of files within a directory. Dropping works elegantly regardless of the channels in a given file per volume because all channels are written back to file by default if not in the channel drop list. So, I think I can parallelize by using a parallel within a parallel where the outer passes a number of files as arguments to the inner.

I ran:

```bash
parallel --dr -j10 -k --lb python -u drop_channels.py -f config-drop-channels.py -m -d {} ::: .root/out/process/cycle11-2024-08-14/processed/*
```

### (date:: 2025-08-14)

[debug tag and calibrate oneset script](</code/ni6356-process/tag-and-calibrate-oneset.py>)

Data appears to be failing to scale or the substrate correction is failing, leading to data with 90th percentile values below 1 (i.e. subsequent FFT is failing for the calibration).

I am running the following:

```bash
parallel -j3 --lb -k python -u tag-and-calibrate-oneset.py -f {} ::: .root/out/process/cycle11-2024-08-14/processed/chewed_metadata_20240815-020101.775106_Sig_A.h5 .root/out/process/cycle11-2024-08-14/processed/chewed_metadata_20240815-021102.152250_Sig_A.h5 .root/out/process/cycle11-2024-08-14/processed/chewed_metadata_20240815-022102.522131_Sig_A.h5
```

which can be updated to just use `*Sig_A.h5` once working. Now, I'd like to run it here so I can look into the Config object.

In the back of my mind, I am also considering if a past problem involving H5 file availability is yet solved.
So far what I've seen of the tagging and calibration code simply reads the files in e.g. `files_to_look` during the loop over `filelist`, which I've made to skip all but the desired prefix.
Further, I found where in the code the dataframe is filtered of other files' info: it happens at the end of the loop right before saving where it takes only rows where the filename matches the current file being processed.
This resolves my worry when `--numfile` is greater than 1.

I also found out of bounds errors related to there being *other files' content* in a given file.
Basically, the above *happened!* but I don't know how - I haven't changed that part of the code.
I wrote a dropper to drop the content of one file from another: [`drop_channels.py -> clean_data.py`](../code/ni6356-process/clean_data.py).
This is now a click script with two commands: `drop-channels` and `clean-data`.
Before I run it I want to verify that the data being dropped is still in the file it should be in.

Damn, I should have just checked the file sizes before doing this, it ended up being just the first file.
That file also had a corrupt channel 3, so I just restored it.
Now to run the processing scripts again and hope it was a fluke.

```bash
sleep 4h; find .root/out/process/cycle16-2024-08-20/processed/ -name "*Sig_A.h5" -print0 | shuf -z | nice -n10 parallel -j10 --lb -k -0 python -u tag-and-calibrate-oneset.py -f {}
```

Processing has failed several times due to lock errors despite a new safe HDF loader class.
I've updated the class to await the lock freeing up for a few tries before failing,
and updated the runner to catch IOError exceptions (from the class) and the tables HDFext exception and try again.
I've also added above the shuf to randomize the files processed at a time, which will hopefully make files read in and saved to at the same time less likely to conflict.

Processing begins on sets (10 threads, ~14.9min/file)

- cycle11: 300 files ==> ~7.45h
- cycle12: 202 files ==> ~5h
- cycle13: 158 files ==> ~3.92h
- cycle14(sleep): 468 files ==>
- cycle15(sleep): 206 files ==>
- cycle16(sleep): 230 files ==>

### (date:: 2025-08-15)

Processing completed for the first three sets fairly well. Although not perfectly:

1. The scrollback buffer was not large enough to capture all output for analysis of how the processing went.
2. While my except captured a few errors, the error messages still printed so I am unsure if those threads died irrecoverably. However, all files processed so we may have been okay.
3. In general it's hard to separate each thread's output. Maybe there's a way to send parallel output to individual files per thread run so I can have a per-file log.

The latter three failed at the assertion of >1 for the FFT. Specifically it was for channel 11 on each thread, which caused each thread to fail.
I need to add a catch to the assertion error to skip a channel if it fails this check, and possibly improve the error message to display the percentile range at the given scale factor just to verify.
Regardless, I need to move on, so I will be plotting what data I do have and hoping for the best.

## Laser Tagging and Calibration

Tagging and calibration are done by the `BeEST_laser_calibration.py` and `BeEST_coincidence_tagger.py` scripts.
The calibration script is run first in tagging mode, followed by the tagger, and finally the calibration script is run again in calibration mode.
The `-e 4` flag specifies the use of the substrate correction.
The `-e 7` flag allows for a scaleFactor to be applied since my data is in units of V.
These scripts can be run in bulk via the [tag and calibrate script](../code/continuous-processing/tag-and-calibrate.py).

### Tagging Mode

In tagging mode, the script reads h5 file(s) and uses the existing `Laser_<A/B>` file to identify events relative to the laser tagging signal.
It can check within a standard identification window and an extended (`is_calibration_long`) window.

Added Parameters:

- `ig_laser`: Positive mask for events falling within TTL of laser signal. Default timing resolution is 7 samples of either edge of the TTL
- `ig_laser_pileup`: Positive mask for events falling within extended TTL range. Default resolution is 90 samples.

### Calibration Mode

In calibration mode, the script uses the laser events to calculate a calibration for the laser and nuclear data.
It assumes a three-parameter quadratic calibration for the laser, and sets the offset to zero for the nuclear,
as motivated by the theory that the simultaneous laser shot leads to an energy offset (bias) in the laser data that is not present in the nuclear data.
As a result, the combination effect of intensity dependence and offset due to substrate heating and crosstalk can also be called the "laser shot bias".

Added Parameters:

-

## Signal Coincidence

The tagger identifies coincident channels within a window which should be sufficient for laser events, as well as a delayed window to identify potential pielup. It adds the `multiplicity`, `sumV`, `coincident_channels`, and `coincident_positions` columns to identify these laser coincidences. It also adds `delayed` versions of all four of these which are used for identifying if a channel has pileup with other nuclear events.
