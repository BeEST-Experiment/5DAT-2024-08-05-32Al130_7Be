import numpy as np
from lib.calibrate import height
import traitlets.config as tlc

# -- Define Global Config object
G = tlc.Config()

G.set = "magcycle-11-2024-08-14"
# G.set = "magcycle-13-2024-08-16"
G.bins = np.linspace(0, 0.025, 1000)
G.input = f".root/out/continuous-processing/{G.set}/processed/chewed*Sig*.h5"

G.a = height
# G.calfunc = lambda x: three_pt_cal(x, (1, 2), (2, 3))

# -- If this is being loaded by tlc.PyFileConfigLoader, update the global config
globals().get("c", tlc.Config()).update(G)
