"""Find optimized shaping by grid search

Loads a small amount of data for the day/chunk and then performs a grid search
to find the optimal shaping parameters. This includes:
- The shaping times (rise, flat)
- The fast shaping time (rise)
The grid search produces a dataframe of data which then needs to be substrate corrected.
Finally, a gaussian width of the laser data is reflective of the resolution.
"""

import click
import os
import glob
from cryoant.daq.xia.listmode import find_optimum_processing
from beest.laser import correct_substrate_heating
import matplotlib.pyplot as plt
import cryoant as ct
import numpy as np
import pandas as pd
from joblib import Parallel, delayed
import gc


class ScatterHistogramPlot:
    def __init__(self, x, y, name, settings, axis="x"):
        self.x = x
        self.y = y
        self.name = name
        self.settings = settings
        self.axis = axis

    def plot(self):
        if self.axis == "x":
            fig, (ax_scatter, ax_hist) = plt.subplots(
                2,
                1,
                sharex=True,
                gridspec_kw={"height_ratios": [3, 1]},
                figsize=(5, 5),
                dpi=500,
                constrained_layout=True,
            )
        else:
            fig, (ax_hist, ax_scatter) = plt.subplots(
                1,
                2,
                sharey=True,
                gridspec_kw={"width_ratios": [1, 3]},
                figsize=(5, 5),
                dpi=500,
                constrained_layout=True,
            )

        # Scatter plot
        ax_scatter.scatter(self.x, self.y, lw=0, s=0.1, alpha=0.2)
        ax_scatter.set(**self.settings)

        # Histogram
        if self.axis == "x":
            h, e = np.histogram(self.x, bins=1000)
            ax_hist.step(e[:-1], h, color="blue")
            ax_hist.set(ylabel="Count", yscale="log")
        else:
            h, e = np.histogram(self.y, bins=1000)
            ax_hist.step(h, e[:-1], color="blue")
            ax_hist.set(xlabel="Count", xscale="log")

        return fig


def file_processor(file, multithread=True):
    dfi, header, _ = find_optimum_processing(file, multithread=multithread)
    size = os.path.getsize(file)
    print(f"Size: {size / 1024 / 1024 / 1024} GB")
    if len(dfi) == 0:
        print(f"Skipping {file}")
        return dfi, header, size
    dfi["ig_laser"] = np.abs(
        (dfi.time % 0.1)
        - (dfi.time % 0.1).rolling(min([1000, int(0.01 * len(dfi))])).median()
    ) < 0.01 * np.mean(dfi.time % 0.1)
    dfi["fname"] = os.path.basename(file)
    gc.collect()
    return dfi, header, size


def process_chunk(files_chunk, no_parallel):
    if no_parallel:
        return [file_processor(file, multithread=False) for file in files_chunk]
    else:
        return Parallel(n_jobs=8)(delayed(file_processor)(file) for file in files_chunk)


@click.command()
@click.argument("date", type=str)
@click.option(
    "-n", "--no-parallel", is_flag=True, help="Do not use parallel processing"
)
def main(date, no_parallel=False):
    """Generate scatter from listmode data.

    date is in YYMMDD format. Gets all files in setup with 20{date} in path.
    Identify laser by rolling median filter.
    Scatter laser data for investigation of substrate heating correction.
    """
    plt.style.use(f"{list(ct.__path__)[0]}/plot.mpl")

    DPI_VIS, DPI_SV = 200, 50
    DATE = date

    directory = "/beest_data/summer2024/Be7_Ta_PR_Mask_listmode_ben/d/"
    files = glob.glob(os.path.join(directory, "*_Al_*/*.bin"))

    # Sort files by filesize
    files.sort(key=os.path.getsize)
    files = [file for file in files if os.path.getsize(file) > 0][:10]

    chunk_size = 8  # Define the chunk size for processing
    df = pd.DataFrame()
    total, skip = 0, 0
    files = [file for file in files if f"20{DATE}" in os.path.dirname(file)]
    headers = []
    for i in range(0, len(files), chunk_size):
        files_chunk = files[i : i + chunk_size]
        print(f"Processing chunk {1 + i // chunk_size}/{-(-len(files)//chunk_size)}")
        results = process_chunk(files_chunk, no_parallel)
        for result in results:
            if result is None:
                skip += 1
                continue
            dfi, header, size = result
            if len(dfi) == 0:
                skip += 1
                continue
            headers.append(header)
            df = pd.concat([df, dfi])
            del dfi  # Explicitly delete dfi to free memory
            total += size
        del results  # Discard the processed chunk
        gc.collect()  # Trigger garbage collection
        print(f"Chunk {1 + i // chunk_size}/{-(-len(files)//chunk_size)} processed")
    print(
        f"Processed {len(files) - skip} files, total size: {total / 1024 / 1024 / 1024} GB"
    )

    testcols = [col for col in df.columns if "h_" == col[:2]]
    for col in testcols:
        fig = ScatterHistogramPlot(
            df[f"hmV_{col}"],
            df[f"omV_{col}"],
            f"Shaping: {col}",
            {
                "xlabel": f"hmV_{col}",
                "ylabel": f"omV_{col}",
                "title": f"Shaping: {col}",
            },
        ).plot()
        fig.savefig(f"out/shapetest_precorrected_{DATE}_{col}.png")
        df[f"corrected_hmV_{col}"] = correct_substrate_heating(
            df[f"hmV_{col}"], df.ig_laser, df[f"smV_{col}"]
        )
        fig = ScatterHistogramPlot(
            df[f"corrected_hmV_{col}"],
            df[f"omV_{col}"],
            f"Shaping: {col}",
            {
                "xlabel": f"corrected_hmV_{col}",
                "ylabel": f"omV_{col}",
                "title": f"Shaping: {col}",
            },
        ).plot()
        fig.savefig(f"out/shapetest_corrected_{DATE}_{col}.png")

    print("Saving data to HDF5")
    df.to_hdf(f"out/processed/shapetest_{DATE}.h5", key="data", mode="a")
    [
        pd.Series(header).to_hdf(
            f"out/processed/shapetest_{DATE}.h5", key="metadata", mode="a"
        )
        for header in headers
    ]
    print(
        f"Data Saved. File size: {os.path.getsize(f'out/processed/shapetest_{DATE}.h5') / 1024 / 1024 / 1024} GB"
    )


if __name__ == "__main__":
    main()
