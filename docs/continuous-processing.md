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

## Pulse Processing Log

- magcycle-11-2024-08-14: processed
- magcycle-12-2024-08-15: processed
- magcycle-13-2024-08-16: processed
- magcycle-14-2024-08-18: processed (date:: 2025-05-22)
- magcycle-15-2024-08-19: processed (date:: 2025-05-20) 
- magcycle-16-2024-08-20: scheduled (date:: 2025-05-20)


## Tag and Calibrate Log

Tag Laser -> Tag Coincidence -> Calibrate -> Repack

- `magcycle-11-2024-08-14` - bad channels: [9, 10, 11, 13, 14, 15]
  - Calibration got about halfway through before tdms repair failed. (date:: 2025-05-01)
  - Runs to completion after dropping bad channels. (date:: 2025-05-08)
- `magcycle-12-2024-08-15` - bad channels: [9, 10, 11, 13, 14, 15]
  - (date:: 2025-05-01) - Got all the way through the laser+coinc taggers, but also failed on a `ch10` with no K-GS.
- `magcycle-13-2024-08-16` - bad channels: [9, 10, 11, 13, 14, 15]
  - (date:: 2025-05-01) - Same thing: channel 10 is bad.
- `magcycle-14-2024-08-18` - processing, expecting calibration to fail. Just need tagging. (date:: 2025-05-26)
  - Calibration failed because the calibration_figures file exists??
  - `Error: [Errno 17] File exists: '/data_fast/beest/6-History/2024/6ALY-2024-08-05-32Al130_7Be/in/5DAT/code/continuous-processing/magcycle-14-2024-08-18/calibration_figures'`
- `magcycle-15-2024-08-19` - processing, expecting calibration to fail. Just need tagging. (date:: 2025-05-26)
  - Calibration failed because the calibration_figures file exists??
- `magcycle-16-2024-08-20` - processing, expecting calibration to fail. Just need tagging. (date:: 2025-05-26)
  - Calibration failed because the calibration_figures file exists??

## Laser Tagging and Calibration

Tagging and calibration are done by the `BeEST_laser_calibration.py` and `BeEST_coincidence_tagger.py` scripts.
The calibration script is run first in tagging mode, followed by the tagger, and finally the calibration script is run again in calibration mode.
The `-e 4` flag specifies the use of the substrate correction.
These scripts can be run in bulk via th [tag and calibrate script](../code/continuous-processing/tag-and-calibrate.py).

### Tagging Mode

In tagging mode, the script reads h5 file(s) and uses the existing `Laser_<A/B>` file to identify events relative to the laser tagging signal.
It can check within a standard identification window and an extended (`is_calibration_long`) window.
Finally, it adds two new columns to the processed dataframe: `ig_laser` and `ig_laser_pileup`.
The `ig_laser` column is a positive mask for tagged laser events, and the `ig_laser_pileup` column is a positive mask for pileup events (potential nuclear events within the longer window following an event).

### Coincidence Tagger

The tagger identifies coincident channels within a window which should be sufficient for laser events, as well as a delayed window to identify potential pielup. It adds the `multiplicity`, `sumV`, `coincident_channels`, and `coincident_positions` columns to identify these laser coincidences. It also adds `delayed` versions of all four of these which are used for identifying if a channel has pileup with other nuclear events.

### Calibration Mode