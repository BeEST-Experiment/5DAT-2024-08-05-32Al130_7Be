# %%
import os, glob
from cryoant.daq.xia.listmode import load_and_process
import matplotlib.pyplot as plt
import cryoant as ct
import numpy as np
import pandas as pd
from beest.laser import correct_substrate_heating

plt.style.use(f"{list(ct.__path__)[0]}/plot.mpl")

DPI_VIS, DPI_SV = 200, 50

# %%
directory = "/beest_data/summer2024/Be7_Ta_PR_Mask_listmode_ben/d/"
files = glob.glob(os.path.join(directory, "*_Al_*/*.bin"))

# Sort files by filesize
files.sort(key=os.path.getsize)
files = [file for file in files if os.path.getsize(file) > 0]

dev_file = files[
    0
]  # for this file, which is currently 7-22 chunk34, the best channel for spectrum seems to be 28, and tpz is 250.5

# %% [markdown]
# ## Spectrum from single 2 GB listmode output file


# %%
def main(file):
    #: Load and Process a File
    df, header, opt_tpzs = load_and_process(file, multithread=True)

    fig, ax = plt.subplots(figsize=(10, 10), dpi=200, constrained_layout=True)
    ax.scatter(df.height_mV, df.otherV, s=0.1, alpha=0.5, lw=0)
    fname = os.path.basename(file)
    ax.set(xlabel="Height [mV]", ylabel="Voltage [mV]", title=f"{fname}\n{file}")
    fig.savefig(f"dev/{fname}.png", dpi=200)


if __name__ == "__main__":
    [main(file) for file in files]
