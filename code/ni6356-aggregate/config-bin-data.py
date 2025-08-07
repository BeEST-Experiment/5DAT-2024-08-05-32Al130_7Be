from beest.calibration import three_pt_cal
import pandas as pd
import numpy as np
import traitlets.config as tlc

# -- Define Global Config object
G = tlc.Config()

G.set = "magcycle-11-2024-08-14"
# G.set = "magcycle-13-2024-08-16"
G.bins = np.linspace(0, 0.025, 1000)
G.input = f".root/out/continuous-processing/{G.set}/processed/chewed*Sig*.h5"


def height(df: pd.DataFrame):
    """Height definition"""
    #: See continuous-aggregation/config-bin-data.py
    # h = df.fp5.sub(df.head2.add(df.tail2).div(2))
    h = df.fp5.copy()
    h.loc[df.head2.add(df.tail2).div(2).gt(df.fp5)] = None
    h.loc[df.sumV.gt(df.sumV.quantile(0.1))] = None
    return h


G.a = height
# G.calfunc = lambda x: three_pt_cal(x, (1, 2), (2, 3))

# -- If this is being loaded by tlc.PyFileConfigLoader, update the global config
globals().get("c", tlc.Config()).update(G)
