# Processing of Continuous Data

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
- magcycle-14-2024-08-18
- magcycle-15-2024-08-19
- magcycle-16-2024-08-20

## Tag and Calibrate Log

- magcycle-11-2024-08-14 - bad channels: [9, 10, 11, 13, 14, 15]
  - (date:: 2025-05-01) - Processing got about halfway through before tdms repair failed.
    - `20240815-112132.234131_Laser_A.tdms`: improperly formatted file
    - `chewed_metadata_20240815-020101.775106_Sig_B.h5`, `ch10`: no KGS peak found
  - (date:: 2025-05-08) - Processed successfully after dropping bad channels.
- magcycle-12-2024-08-15 - bad channels: [9, 10, 11, 13, 14, 15]
  - (date:: 2025-05-01) - Got all the way through the tagging and tagger, but also failed on a `ch10` with no K-GS.
    - `chewed_metadata_20240816-003746.228601_Sig_B.h5`
- magcycle-13-2024-08-16 - bad channels: [9, 10, 11, 13, 14, 15]
  - (date:: 2025-05-01) - Same thing: channel 10 is bad.
    - `chewed_metadata_20240816-235931.762934_Sig_B.h5`
- magcycle-14-2024-08-18
- magcycle-15-2024-08-19
- magcycle-16-2024-08-20

## Laser Tagging and Calibration

Tagging and calibration are done by the `BeEST_laser_calibration.py` and `BeEST_coincidence_tagger.py` scripts. The calibration script is run first in tagging mode, followed by the tagger, and finally the calibration script is run again in calibration mode. The `-e 4` flag specifies the use of the substrate correction. These scripts can be run in bulk via:

```sh
sleep 7h; dir=magcycle-15-2024-08-19; python BeEST_laser_calibration.py -m tagging -d $dir/processed; python BeEST_coincidence_tagger.py -d $dir/processed; python BeEST_laser_calibration.py -m calibration -e 4 -d $dir/processed -p;
```

### Tagging Mode

In tagging mode, the script reads h5 file(s) and uses the existing `Laser_<A/B>` file to identify events relative to the laser tagging signal. It can check within a standard identification window and an extended (`is_calibration_long`) window. Finally, it adds two new columns to the processed dataframe: `ig_laser` and `ig_laser_pileup`. The `ig_laser` column is a positive mask for tagged laser events, and the `ig_laser_pileup` column is a positive mask for pileup events (potential nuclear events within the longer window following an event).

### Tagger

The tagger identifies coincident channels within a window which should be sufficient for laser events, as well as a delayed window to identify potential pielup. It adds the `multiplicity`, `sumV`, `coincident_channels`, and `coincident_positions` columns to identify these laser coincidences. It also adds `delayed` versions of all four of these which are used for identifying if a channel has pileup with other nuclear events.

### Calibration Mode