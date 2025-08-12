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
3.  Profit

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

(date:: 30 Apr 2025) ``parallel -v -j36 "`realpath chewOneFile.sh` 0 {}" :::: <(basename -a .root/in/Data-CRONOS/summer2024/magcycle-11-2024-08-14/*Sig_A.tdms)``

(date:: 2025-05-22) `nice -n10 ./chewerJobA.sh magcycle-14-2024-08-18`

- magcycle-11-2024-08-14: processed
- magcycle-12-2024-08-15: processed
- magcycle-13-2024-08-16: processed
- magcycle-14-2024-08-18: processed (date:: 2025-05-22)
- magcycle-15-2024-08-19: processed (date:: 2025-05-20) 
- magcycle-16-2024-08-20: scheduled (date:: 2025-05-20)


## Tag and Calibrate Log

(date:: 2025-05-01)

- magcycle-11-2024-08-14: Processing got about halfway through before tdms repair failed.
  - `20240815-112132.234131_Laser_A.tdms`: improperly formatted file
  - `chewed_metadata_20240815-020101.775106_Sig_B.h5`, `ch10`: no KGS peak found
- magcycle-12-2024-08-15: bad channels = [9, 10, 11, 13, 14, 15]
  - Got all the way through the tagging and tagger, but also failed on a `ch10` with no K-GS.
  - `chewed_metadata_20240816-003746.228601_Sig_B.h5`
- magcycle-13-2024-08-16: bad channels = [9, 10, 11, 13, 14, 15]
  - Same thing: channel 10 is bad.
  - `chewed_metadata_20240816-235931.762934_Sig_B.h5`

(date:: 2025-05-08)

- magcycle-11-2024-08-14: Processed successfully after dropping bad channels.

(date:: 2025-08-12) 

- Re-dropped bad channels. See `config-drop-channels.py` for the channels dropped.

## Laser Tagging and Calibration

Tagging and calibration are done by the `BeEST_laser_calibration.py` and `BeEST_coincidence_tagger.py` scripts.
The calibration script is run first in tagging mode, followed by the tagger, and finally the calibration script is run again in calibration mode.
The `-e 4` flag specifies the use of the substrate correction.
These scripts can be run in bulk via th [tag and calibrate script](../code/continuous-processing/tag-and-calibrate.py).

or by using `tag-and-calibrate.py`

> (date:: 2025-08-11) I have made progress creating a parallelized version of the tagger/calibrator. Further, I am debugging why the calibration is failing because I need the laser calibration of the nuclear data to work out, otherwise my paper will reference data that was calibrated by hand.
> I am running
> 
> ```bash
> python tag-and-calibrate-oneset.py -f .root/out/process/cycle11-2024-08-14/processed/chewed_metadata_20240815-020101.775106_Sig_A.h5;
> ```
> 
> as my debug example, and am noticing
> 
> 1. The calibration is failing because the tolerance for the peak fit is bigger than 0.2 (default). I can configure that in tag-and-calibrate-oneset as a Config key
> 2. The drift correction is giving mean of empty slice and divide issue warnings - I need to move my print statement into there to see what is bad when calibration fails
> 3. Channel 9 of the data above doesn't have any nuclear data - I either need more files or to simply mandate that the K-GS is around 0.01 regardless of if there's data
>
> The parallelized processing is working [using this](../code/continuous-processing/tag-and-calibrate-oneset.py). A key discovery was that the values passed to the FFT have to be greater than 1, otherwise the FFT frequencies will be off. A boon of getting this working is that the calibration no longer relies on nuclear data because it can use the laser FFT to find an initial guess for the comb fit.
>
> It appears channel 9 data - which comes from a bad channel presumably already removed around (date:: 2025-05-01) - has made its way back into the dataset. I intend to try removing it again. Now that I have my calibration code fail on any error, I must resolve these issues one-by-one before I can check off a file as successfully processed.
>
> The rest of the processing threads also failed giving a resource temporarily unavailable error. Could this be from reading or actually writing? Further, if the laser script gets multiple files to look in and then concatenates those files, how is it that data from those files isn't ending up in the current file? If it was I would be expecting to see more than one unique filename in each file. So somehow this contamination isn't happening, but I don't trust it, especially given this unavailable error.

(date:: 2025-08-12)

- Updated the `drop_channels.py` script to allow for a channel map to be passed in, which allows for dropping channels based on the cycle. This allows parallelization over cycles, though the better way would be to parallelize over chunks of files within a directory. Dropping works elegantly regardless of the channels in a given file per volume because all channels are written back to file by default if not in the channel drop list. So, I think I can parallelize by using a parallel within a parallel where the outer passes a number of files as arguments to the inner.


### Tagging Mode

In tagging mode, the script reads h5 file(s) and uses the existing `Laser_<A/B>` file to identify events relative to the laser tagging signal.
It can check within a standard identification window and an extended (`is_calibration_long`) window.
Finally, it adds two new columns to the processed dataframe: `ig_laser` and `ig_laser_pileup`.
The `ig_laser` column is a positive mask for tagged laser events, and the `ig_laser_pileup` column is a positive mask for pileup events (potential nuclear events within the longer window following an event).

### Coincidence Tagger

The tagger identifies coincident channels within a window which should be sufficient for laser events, as well as a delayed window to identify potential pielup. It adds the `multiplicity`, `sumV`, `coincident_channels`, and `coincident_positions` columns to identify these laser coincidences. It also adds `delayed` versions of all four of these which are used for identifying if a channel has pileup with other nuclear events.

### Calibration Mode