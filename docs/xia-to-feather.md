# XIA Laser Preparation: From Raw Data to Calibrated Spectra

There are several days of XIA data.

## Trace Chewing (`trace-chewing`)

Data are processed day-by-day. Sometimes the data includes multiple collections, or "runs".
The data from one day is a day-set and is assumed to be from one cooldown and have similar STJ performance across runs.

## Laser Preparation

In pursuit of energy calibration, one needs to take the processed data and:

- Separate data into "runs" by chunk number
- Assign a real timestamp to every event using the file timestamp
    - Run onset is `chunk0`'s timestamp plus event time in seconds (20ns precision)
- Filter "bad" events using flags calculated during processing (e.g. `ib_flat`)
- Per channel, per run: tag laser events using a moving median filter
- Tag nuclear events as remaining events.
- Per channel, per run: perform laser substrate heating correction

### Wall-Clock Time

The first step is getting the wall-clock time from the file itself: this adds to the inherent time in the processed file which is relative to the run start time.

### Laser Identification

Laser identification is done by modulo time selection of events. This depends on the laser periodicity, which may change within a day-set if there are multiple "runs", and must be manually identified.

Verification plots include the laser event timing (modulo the chosen frequency), which should look like a line/sawtooth with correctly identified laser data in red following this line.

The second verification plot is the laser spectra. Once the laser data is identified, we should be able to see a periodicity in the laser spectra, and in particular, a spectrum of laser event filtered height versus the sum of all laser event filtered heights across channels per event. If we cannot see the laser periodicity, we cannot calibrate the energy for that channel. It is then better to discard these channels, which affects both the calculation of this "sum of laser" intensity metric and the nuclear data statistics.

The third verification plot sums the runs together to show the entire statistics of the laser data. Using really good channels, we can identify any runs which might be poor and neglect these runs. Then, if the sum of the laser data across runs is still poor for a channel, we can exclude that channel entirely for that day-set as inoperative.

## Laser Calibration

With good runs and good channels identified, we can apply the substrate heating correction to the remaining data. This will produce good laser data which can be used to calibrate the energy.

### Substrate Heating Correction

Substrate heating requires manual intervention during the FFT correction. This is because the gain for every channel is slightly different, and there can be some low-intensity channels/runs where the laser FFT periodicity peak is rather small (See below):

![FFTs](/out/spectra_calibration/20240811-setup/substrateCorrection-run0-ch12-FFTs.jpeg)

The cutoff for the low region can dynamically be set using keword argument `mVmin` (units of per millivolt i.e. "laser peak spacing per millivolt pulse height") below which will be ignored for finding the max height in the FFT spectrum (the laser peak frequency per millivolt pulse height).

Once a proper cutoff is set, the frequency of greatest periodicity (the substrate heating correction gradient) is found automatically with great success.

### Energy Calibration

The laser data must be fit with a multi gaussian function whose centroids and widths follow quadratic functions of energy.

The centroids are a quadratic function of bin number with the offset representing the remaining uncorrected substrate heating. The linear and quadratic nature of the centroid spacing is a measure of the quenching of the STJs.

The widths are a quadratic function of energy, with the offset representing the intrinsic resolution of the STJs. As a function of energy, it depends on the calibration of the STJs moreso than the raw bin number.

## Nuclear Calibration

The same energy calibration identified in the laser data is applied to the nuclear data. However, the calibration offset is not applied to the nuclear data, as the nuclear data is not affected by the substrate heating.

## Dataset Aggregation

Calibrated spectra may presumably be aggregated across day-sets to accrue statistics.