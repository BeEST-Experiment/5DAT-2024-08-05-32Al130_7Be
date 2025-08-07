# %% [markdown]
# ---
# title: "Bin Listmode Data"
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     custom_cell_magics: kql
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.11.2
# ---

# %% [markdown]
# Craft a binning scheme for listmode data coming from individual files and individual channels. This can be parallelized by accessing a set of files and their respective channels in order.
#
# The input parameters are:
# - `input_files`: A list of file paths to the input data files.
# - `bins`: The bin edges or range for the histogram.
# - `a`: The column of uncalibrated data to be binned.
# - `b`: The column of calibrated data to be binned.
# - `calfunc`: Some calibration function to calibrate from `a` to `b`.
#   - `a` is required, `b` and `calfunc` are optional.
#   - If `b` is given, `calfunc` is not required.
#   - If `calfunc` is not given, it is unity and `b` becomes `a`.
#
# The outputs are an HDF file with several dataframes with columns for each file and an index for the bin centers. Each channel has its own dataframe. The tables per channel are also saved as CSV. Then, at this level, one can aggregate data by filtering on file and on channel. This defines the Histogram Data Level.

# %%
#!%load_ext autoreload
#!%autoreload 2
#!%config InlineBackend.figure_formats = ['svg']

# %%
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import traitlets.config as tlc
import glob, os
from pathlib import Path
from joblib import Parallel, delayed
import scipy.optimize as opt
from cryoant.models import gaussian
from cryoant.utils import centers_from_edges, nearest
from beest.calibration import three_pt_cal
from beest.data import load_chewed_data

plt.style.use("beest.default.plotstyle")

# %%
# -- Establish global variables
G = tlc.Config()
G.input = None
G.bins = None
G.task = "continuous-aggregation"
G.set = "magcycle-11-2024-08-14"
G.subtype = "uncalibrated"
G.a = "height"
G.b = None
G.calfunc = lambda x: x
G.channels = range(16)
# -- Example: G.calfunc = lambda x: three_pt_cal(x, (1, 2), (2, 3))
G.output = f".root/out/{G.task}/{G.set}"
G.outname = f"histograms-{G.subtype}"

# -- Import from config file if running from command line
G.kwfile = f".root/code/{G.task}/config-bin-data.py"
if Path(G.kwfile).exists():
    c = tlc.PyFileConfigLoader(G.kwfile).load_config()
    G.update(c)

# -- Create Folders as required
os.makedirs(Path(G.output).parent, exist_ok=True)

# %%
"""Global Variable Catches"""

# -- Note To Self: if bins is None, use 1-99% Quantile Range and 1000 bins
# -- Note To Self: if G.b is None, use calfunc on a to get b

if G.input is None:
    raise ValueError("global var `input` must be set to a valid input file or folder.")
elif "*" in G.input:
    G.input = list(Path().glob(G.input))
elif Path(G.input).is_dir():
    G.input = list(Path(G.input).glob("*.h5"))
elif Path(G.input).is_file():
    G.input = [Path(G.input)]
else:
    raise ValueError(f"input {G.input} is not a valid file or folder.")

# %%
"""Define Binning Function to be Parallelized

1. Load Data from a given file and channel
2. Get column b
2a. If b is None, use calfunc on a to get b
3. Bin data into histogram
4. Return Series of bin centers and counts and edges
"""


def bin_data(file, channel, a, b=None, calfunc=None, bins=None, cycle=None):
    # -- Load Data
    df = load_chewed_data(file, channel, cycle=cycle)
    # -- Get Column b
    if df is None:
        return None, None
    if callable(a):
        df["a"] = a(df)
    else:
        df["a"] = df[a]
    if calfunc is None:
        calfunc = lambda x: x
    if b is None:
        b = calfunc(df.a)
    if bins is None:
        bins = 1000
        b = b[b.between(*b.quantile([0.01, 0.99]))]
    # -- Bin Data into Histogram
    hist, edges = np.histogram(b, bins=bins)
    # -- Get Bin Centers
    centers = centers_from_edges(edges)
    return pd.Series(hist, index=centers, name=Path(file).stem), edges


# %%
"""Parallel Load and Bin Input Files.

0. Create worker pool
1a. Parallelize along files.
1b. Loop over channels.
2. Concatenate each channel's data into a channel DataFrame
"""

dfs = {}
with Parallel(n_jobs=-1) as pool:
    for channel in G.channels:
        data = pool(
            delayed(bin_data)(str(file), channel, G.a, G.b, G.bins) for file in G.input
        )
        dfs[channel] = pd.concat(data, axis=1)

# %%
"""Save Concatenated DataFrame of Histograms to HDF5

Are groups parallel safe??
If so, I can write to chX/histograms per channel in parallel!
- It is only safe in table format, which is slower than fixed format.
"""


def save_df(df, channel, output=G.output, outname=G.outname):
    # -- Save to HDF5
    df.to_hdf(
        Path(output) / f"{outname}.h5",
        key=f"ch{channel}/histograms",
        mode="a",
        format="table",
        append=True,
    )
    # -- Save to CSV
    df.to_csv(
        Path(output).parent / f"{outname}-ch{channel}.csv",
        index_label="bin_center",
    )


# Parallel(n_jobs=-1)(
#     delayed(save_df)(df, channel, G.output, G.outname) for channel, df in dfs.items()
# )

for channel in dfs.keys():
    dfs[channel].to_hdf(
        Path(G.output) / f"{G.outname}.h5",
        key=f"ch{channel}/histograms",
        mode="a",
    )
