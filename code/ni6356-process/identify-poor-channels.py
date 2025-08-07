# %% [markdown]
"""
---
date: 2025-05-20
author: "S. Fretwell"
purpose: "Identify poor channels in pulse processed data"
title: "Identify Poor Channels"
---
"""

# %% [markdown]
# # Processing Analysis: magcycle-12-2024-08-15

# %%
#!%load_ext autoreload
#!%autoreload 2

# %%
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import traitlets.config as tlc
import glob, os
from joblib import Parallel, delayed
import scipy.optimize as opt
from cryoant.models import gaussian
from cryoant.utils import centers_from_edges, argmax_part

#!%config InlineBackend.figure_formats = ['svg']

plt.style.use("beest.default.plotstyle")

G = tlc.Config()
G.task = "continuous-processing"
G.set = "magcycle-12-2024-08-15"
G.kwfile = "kw-id-poor-channels.py"

#: Import from config file if running from command line
if os.path.exists(G.kwfile):
    c = tlc.Config()
    c.update(tlc.PyFileConfigLoader(G.kwfile).load_config())
    G.update(c)

os.makedirs(f".root/out/{G.task}/{G.set}/nuclear-precal-by-channel", exist_ok=True)


# %%
def load_isolated_data(f, channel, cycle=None):
    if "Sig_A" in f:
        if channel > 7:
            return None
    else:
        if channel < 8:
            return None
    d = pd.HDFStore(f, "r")
    if f"/data_channel{channel}" not in d.keys():
        d.close()
        print(f"No ch {channel} in {os.path.basename(f)}")
        return None
    d.close()
    df = pd.read_hdf(f, f"data_channel{channel}")
    df["channel"] = channel

    if cycle is None:
        #: bla/bla/magcycle-XX-YYYY-MM-DD/...
        cycle = [w for w in f.split("/") if w.startswith("magcycle")]
        if cycle:
            cycle = cycle[-1]
            print(f"Assuming magcycle: {cycle}")
        else:
            print(f"Could not identify cycle!")
            return None

    df["cycle"] = cycle
    print(f"Loaded ch {channel} from {os.path.basename(f)}")
    return df


# %%
L = tlc.Config()
G.cpath = f".root/out/{G.task}/{G.set}"
L.cycle = G.cpath.split("/")[-1]
print(f"Processing cycle {L.cycle}")

L.dfs = Parallel(n_jobs=-1)(
    delayed(load_isolated_data)(L.file, L.channel, G.cpath)
    for L.file in glob.glob(G.cpath + "/processed/chewed*Sig*.h5")[:10]
    for L.channel in range(16)
)
L.df = pd.concat(L.dfs, ignore_index=True)
del L.dfs

# %% [markdown]
"""
## Delete Poor Channels

- Prior: Process Data
- Primary: Delete Poor Channels from processed data
- Posterior: Tag and Calibrate Data
"""

# %%
L.df["height"] = L.df.flattop2_mean.sub(L.df.head2.add(L.df.tail2).div(2))
L.df.loc[L.df.head2.add(L.df.tail2).div(2).gt(L.df.flattop2_mean), "height"] = None

# %%
goodchannels = L.df.channel.unique()
# goodchannels = [0, 1, 2, 3, 5, 6, 7, 8, 12]
# goodchannels = [9]
# goodchannels = [5, 7] #: Odd
# badchannels = [9, 10, 11, 13, 14, 15]
# badchannels = [4, 10]

# %%
"""Plot raw data individually
"""
bins = np.linspace(0, 0.012, 400)
ma = (
    L.df.channel.isin(goodchannels)
    & ~L.df.ig_laser.astype(bool)
    #: Multiplicity must follow tagging, can we deduce good channel prior to tagging?
    # & L.df.multiplicity.eq(1)
)
for channel in goodchannels:
    fig, ax = plt.subplots(figsize=(10, 6))
    mai = ma & L.df.channel.eq(channel)
    h, e = np.histogram(
        L.df[mai].height,
        bins=bins,
    )
    ax.stairs(h, e, label=f"Channel {channel}", alpha=0.5, fill=True)
    ax.set(
        yscale="log",
        xlabel="Height [A.U.]",
        ylabel="Counts",
        title=f"{G.set}",
    )
    ax.legend(title="Nuclear Data", loc="upper right")
    fig.savefig(f".root/out/{G.task}/{G.set}/nuclear-precal-by-channel/ch{channel}.svg")

# %%
#: Plot raw data
# fig, ax = plt.subplots(figsize=(10, 6))
# bins = np.linspace(0, 0.012, 400)
# ma = (
#     L.df.channel.isin(goodchannels)
#     & ~L.df.ig_laser.astype(bool)
#     & L.df.multiplicity.eq(1)
# )
# for channel in goodchannels:
#     mai = ma & L.df.channel.eq(channel)
#     h, e = np.histogram(
#         L.df[mai].height,
#         bins=bins,
#     )
#     ax.stairs(h, e, label=f"Channel {channel}", alpha=0.5, fill=True)
# h, e = np.histogram(
#     L.df[ma].height,
#     bins=bins,
# )
# ax.stairs(h, e, label="All", color="C0", alpha=0.5, lw=2, zorder=-1, fill=True)
# ax.set(
#     yscale="log",
#     xlabel="Height [A.U.]",
#     ylabel="Counts",
#     title=f"{G.set}",
# )
# ax.legend(title="Nuclear Data", loc="upper right")
