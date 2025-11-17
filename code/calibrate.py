from .clean import cut_negative, cut_high_intensity
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from joblib import Parallel, delayed
from beest.data import load_chewed_data
from traitlets.config import Config
from cryoant.models import gaussian
from beest.utils import to_centers, to_bins
from scipy.optimize import curve_fit
from beest.calibration import apply_calibration


def height(df: pd.DataFrame, cut_laser=True):
    """Pulse height definition.

    Per clean/define-pulse-height.ipynb,
    the best height definition is flatAvg,
    defined as PSP flattop2_mean.
    """
    h = df.flattop2_mean.copy()
    h = cut_negative(h, df.head2, df.tail2)
    if cut_laser:
        h.loc[df.ig_laser] = cut_high_intensity(h[df.ig_laser], df.sumV[df.ig_laser])
    return h


# -- c.f. bin/calibrate/ni6356-approx-cycleX.ipynb
def cal_approx(G: Config, bin_rng=(0, 120.1, 0.2)):
    """Apply approximate calibration and histogram.

    Bin to bin_rng (np.arange) in Energy units.
    Requires:
    - G.set
    - G.channels
    - G.Cal.ChX.params: calibration parameters via calibrate()

    Saves hist (1col frame) to .root/out/calibrate/ni6356-approx-G.set-tmp.csv,
    which should be concatenated into a full frame (of datasets).
    """
    files = list(
        Path(f"./.root/in/5DAT-Data.lnk/out/process/{G.set}/processed/").glob(
            "chewed_*_Sig_*.h5"
        )
    )
    dfs = Parallel(n_jobs=32, verbose=10, backend="multiprocessing")(
        delayed(load_chewed_data)(f, G.channels) for f in files[:100]
    )

    dfs = [df for df in dfs if df is not None]
    df = pd.concat(dfs, ignore_index=True)
    del dfs

    for channel in df.channel.unique():
        cfg = G.Cal[f"Ch{channel}"]
        if not cfg:
            continue
        df["energy"] = apply_calibration(cfg.params, df.flattop2_mean)

    # -- Bin
    bins = np.arange(bin_rng[0], bin_rng[1], bin_rng[2])
    h, _ = np.histogram(df.energy[~df.ig_laser.astype(bool)], bins=bins)
    out = pd.DataFrame({G.set: h}, index=to_centers(bins))
    out.to_csv(
        f".root/out/calibrate/ni6356-approx-{G.set}-{int(bin_rng[2]*1e3)}meVbins-nuclear-tmp.csv"
    )

    out = pd.DataFrame(index=to_centers(bins))
    for channel in df.channel.unique():
        h, _ = np.histogram(
            df.energy[df.ig_laser.astype(bool) & df.channel.eq(channel)], bins=bins
        )
        out = pd.DataFrame({G.set: h}, index=to_centers(bins))
    out.to_csv(
        f".root/out/calibrate/ni6356-approx-{G.set}-{int(bin_rng[2]*1e3)}meVbins-laserPerChannel-tmp.csv"
    )

    out = pd.DataFrame(index=to_centers(bins))
    for channel in df.channel.unique():
        h, _ = np.histogram(
            df.energy[df.channel.eq(channel) & ~df.ig_laser.astype(bool)], bins=bins
        )
        out[f"Ch{channel}"] = h
    out.to_csv(
        f".root/out/calibrate/ni6356-approx-{G.set}-{int(bin_rng[2]*1e3)}meVbins-nuclearPerChannel-tmp.csv"
    )

    print(
        f"Saved to: .root/out/calibrate/ni6356-approx-{G.set}-{int(bin_rng[2]*1e3)}meVbins-...-tmp.csv"
    )


# -- c.f. ni6356-approx-calibration-cycleX.ipynb
def prelim_approx(channels, set):
    """Load data from the set and plot each uncalibrated channel so I can see what to calibrate to"""

    files = list(
        Path(f"./.root/in/5DAT-Data.set/out/process/{set}/processed/").glob(
            "chewed_*_Sig_*.h5"
        )
    )
    dfs = Parallel(n_jobs=32, verbose=10, backend="multiprocessing")(
        delayed(load_chewed_data)(f, channels) for f in files[:100]
    )

    dfs = [df for df in dfs if df is not None]
    df = pd.concat(dfs, ignore_index=True)
    del dfs

    df["height"] = df.flattop2_mean

    # -- NUCLEAR
    figs = {}
    vals = {}
    for channel in df.channel.unique():
        figs[channel], ax = plt.subplots(figsize=(12, 6))
        ma = df.channel.eq(channel) & ~df.ig_laser.astype(bool)
        h, e = np.histogram(
            df[ma].height,
            bins=250,
            range=tuple(df.height.quantile([0.01, 0.99])),
        )
        x = to_centers(e)
        fit_ma = 0.008 > x
        fit_ma_e = 0.008 > e
        fit_h = np.ma.array(h, mask=fit_ma)
        fit_e = np.ma.array(e, mask=fit_ma_e)
        fit_x = np.ma.array(x, mask=fit_ma)
        maxi = np.ma.argmax(fit_h)
        poptK, _ = curve_fit(
            gaussian,
            fit_x.compressed(),
            fit_h.compressed(),
            [1, fit_x[maxi], 5 * fit_x[maxi] / 108],
            maxfev=5000,
        )
        ax.stairs(h, e, label=f"Channel {channel}", alpha=0.5, fill=True)
        # if len(to_bins(fit_x)) != (len(fit_h)+1):
        #     print("to_bins(fit_x) didn't work")
        #     ax.step(fit_x, fit_h, where='mid')
        # else:
        ax.stairs(fit_h.compressed(), to_bins(fit_x), alpha=0.5, color="red")
        ax.axvline(poptK[1], color="red", linestyle="--", label=f"K-GS: {poptK[1]:.5f}")
        gain = poptK[1] / 108
        # h, e = np.histogram(
        #     df[ma].height,
        #     bins=90,
        #     range=tuple(df.height.quantile([0.01, 0.99])),
        # )
        # x = to_centers(e)
        fit_ma = (x < (gain * 50)) | (x > (gain * 62))
        fit_ma_e = (e < (gain * 50)) | (e > (gain * 62))
        fit_h = np.ma.array(h, mask=fit_ma)
        fit_e = np.ma.array(e, mask=fit_ma_e)
        fit_x = np.ma.array(x, mask=fit_ma)
        try:
            poptL, _ = curve_fit(
                gaussian,
                fit_x.compressed(),
                fit_h.compressed(),
                [1, gain * 50, 5 * gain],
                maxfev=10000,
            )
        except RuntimeError:
            poptL = [0, -1, 0]
        ax.stairs(fit_h.compressed(), to_bins(fit_x), alpha=0.5, color="green")
        if poptL[1] > 0:
            ax.axvline(
                poptL[1], color="green", linestyle="--", label=f"L-GS: {poptL[1]:.5f}"
            )
        ax.legend(title="Nuclear Data", loc="upper right")
        vals[channel] = (
            f"G.Cal.Ch{channel}.Raw.kgs, G.Cal.Ch{channel}.Raw.lgs = {poptK[1]}, {poptL[1]}"
        )

    # -- Fig All wasn't very informative for diagnosing why cycle11 is offset
    # fig_all, ax = plt.subplots(figsize=(12, 6))
    # for channel in df.channel.unique():
    #     ma = df.channel.eq(channel) & ~df.ig_laser.astype(bool)
    #     h, e = np.histogram(
    #         df[ma].height,
    #         bins=150,
    #         range=tuple(df.height.quantile([0.01, 0.99])),
    #     )
    #     ax.stairs(h, e, label=f"Channel {channel}", alpha=0.5, fill=True)
    # ax.legend(title="Nuclear Data", loc="upper right")

    for val in vals.values():
        print(val)
    for fig in figs.values():
        plt.show(fig)
        plt.close(fig)
    # plt.show(fig_all)
    # plt.close(fig_all)
    return df


def hexbin_height_time(G: Config, gridsize=500):
    """Create hexbin plot of time versus height for all events.

    Loads chewed data, extracts height values, and plots using hexbin
    with time on x-axis (in days with 2024-08-XX labels) and height on y-axis
    (within 0-99 percentile range).

    Args:
        G: Configuration object with G.set and G.channels attributes
        gridsize: Number of hexagons for hexbin plot (default 500)
    """
    files = list(
        Path(f"./.root/in/5DAT-Data.lnk/out/process/{G.set}/processed/").glob(
            "chewed_*_Sig_*.h5"
        )
    )
    dfs = Parallel(n_jobs=32, verbose=10, backend="multiprocessing")(
        delayed(load_chewed_data)(f, G.channels) for f in files[:100]
    )

    dfs = [df for df in dfs if df is not None]
    df = pd.concat(dfs, ignore_index=True)
    del dfs

    # Extract height values using the existing height function
    df["height_vals"] = height(df, cut_laser=True)

    # Calculate time in days relative to first event
    # Assuming realtime column exists, if not we need to add it
    if "realtime" not in df.columns:
        # Add wall clock time similar to what's done in tagging.py
        unique_fnames = df.fname.unique()
        timestamps = pd.Series(
            {
                k: pd.to_datetime(
                    "_".join(k.split("_")[-3:-1]), format="%Y-%m-%d_%H.%M.%S"
                )
                for k in unique_fnames
            }
        )
        chunks = pd.Series(
            {
                k: int(k.split("_")[-1].split(".")[0].removeprefix("chunk"))
                for k in unique_fnames
            }
        )

        df["timestamp"] = df["fname"].map(timestamps)
        df["chunk"] = df["fname"].map(chunks)

        # Filter zero chunks and sort by timestamp
        zero_timestamps = timestamps[chunks == 0].sort_values()

        # Assign runs based on zero chunks
        runs = {fname: idx for idx, fname in enumerate(zero_timestamps.index)}
        for fname, timestamp in timestamps.items():
            if fname not in zero_timestamps.index:
                runs[fname] = runs[
                    zero_timestamps.index[zero_timestamps <= timestamp][-1]
                ]

        df["run"] = df["fname"].map(runs)
        run_start = zero_timestamps.rename(runs).sort_index()
        df["run_start"] = df["run"].map(run_start)

        # Compute realtime (simplified without trigger correction)
        df["realtime"] = pd.to_timedelta(df["time"], unit="s") + pd.to_datetime(
            df["run_start"]
        )

    # Convert realtime to days since start
    start_time = df["realtime"].min()
    df["time_days"] = (df["realtime"] - start_time).dt.total_seconds() / (24 * 3600)

    # Filter height to 0-99 percentile range
    height_low, height_high = df["height_vals"].quantile([0.0, 0.99])
    mask = (df["height_vals"] >= height_low) & (df["height_vals"] <= height_high)

    # Create the hexbin plot
    fig, ax = plt.subplots(figsize=(12, 8))

    hb = ax.hexbin(
        df[mask]["time_days"],
        df[mask]["height_vals"],
        gridsize=gridsize,
        cmap="viridis",
        mincnt=1,
    )

    # Set up x-axis labels in 2024-08-XX format
    time_range = df["time_days"].max() - df["time_days"].min()
    if time_range > 7:  # More than a week, show every few days
        day_interval = max(1, int(time_range / 10))
    else:
        day_interval = 1

    # Create day labels
    day_ticks = np.arange(0, df["time_days"].max() + 1, day_interval)
    day_labels = []
    for day_tick in day_ticks:
        actual_date = start_time + pd.Timedelta(days=day_tick)
        if actual_date.month == 8 and actual_date.year == 2024:
            day_labels.append(f"2024-08-{actual_date.day:02d}")
        else:
            day_labels.append(
                f"{actual_date.year}-{actual_date.month:02d}-{actual_date.day:02d}"
            )

    ax.set_xticks(day_ticks)
    ax.set_xticklabels(day_labels, rotation=45)

    # Labels and formatting
    ax.set_xlabel("Date")
    ax.set_ylabel("Height")
    ax.set_title(
        f"Time vs Height Hexbin Plot - {G.set}\n(0-99th percentile height range)"
    )

    # Add colorbar
    cb = plt.colorbar(hb, ax=ax)
    cb.set_label("Event Count")

    # Tight layout to prevent label cutoff
    plt.tight_layout()

    # Save the plot
    output_path = f".root/out/calibrate/hexbin-time-height-{G.set}.png"
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"Hexbin plot saved to: {output_path}")

    plt.show()
    plt.close(fig)

    return df
