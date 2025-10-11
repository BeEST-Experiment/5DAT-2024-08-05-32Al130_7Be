"""Tag and Calibrate One Set of Data (For Parallelization)"""

import click

# import lib.process.laser as laser
# import lib.process.tag as tag

from lib.process.laser import main as laser
from lib.process.tag import main as tag

import cryoant.apps.repacker as rep
import sys
import time
from pathlib import Path
from traitlets.config import Config
from tables.exceptions import HDF5ExtError


def null(*args, **kwargs):
    """A null function to replace the original `main` function in the modules."""
    pass


# blc = laser.run.callback or null
# blt = tag.run.callback or null

C = Config()
# -- I could just call main directly...
# -- OK the callback allows for sys.argv interpretation, so that has to go into the main call manually
# C.KWArgs.Main.dev = True
# -- For an old version of the helper which relies on K-peak
# C.KWArgs.GetCalibrationHelper.rough_k_peak_tmp = 0.01
C.KWArgs.GetCalibrationHelper.reqd_tolerance = 0.3  # Bump tolerance to 0.3
C.KWArgs.GetUncalibratedEnergy.scaleFactor = 1000  # Scale factor for height in mV to V


@click.command("main")
@click.option("--file", "-f", required=True, help="The file to process")
def main(file, fail_max=10, cfg=C):
    # -- LASER TAG
    fail_count = 0
    try:
        laser(file, mode="tagging", cfg=cfg)
    except HDF5ExtError as e:
        if fail_count > fail_max:
            print("!!!X Too Many Failures")
            raise e
        print("!!! HDF5 Error Caught - waiting 15seconds")
        time.sleep(15)
        fail_count += 1
        laser(file, mode="tagging", cfg=cfg)
    except IOError as e:
        if "acquire lock" not in str(e):
            raise e
        print("!!! SafeHDFStore failed to acquire lock. Deleting lockfile...")
        Path(file.replace(".h5", ".lock")).unlink(missing_ok=True)
        laser(file, mode="tagging", cfg=cfg)
    fail_tag = fail_count

    # -- COINCIDENCE
    fail_count = 0
    sys.argv = ["", "-d", f"{file}"]
    try:
        tag(cfg=cfg)
    except HDF5ExtError as e:
        if fail_count > fail_max:
            print("!!!X Too Many Failures")
            raise e
        print("!!! HDF5 Error Caught - waiting 15seconds")
        time.sleep(15)
        fail_count += 1
        tag(cfg=cfg)
    fail_coinc = fail_count

    # -- CALIBRATION
    fail_count = 0
    try:
        laser(
            file, mode="calibration", numfile=7, energy_estimator=7, plot=True, cfg=cfg
        )
    except HDF5ExtError as e:
        if fail_count > fail_max:
            print("!!!X Too Many Failures")
            raise e
        print("!!! HDF5 Error Caught - waiting 15seconds")
        time.sleep(15)
        fail_count += 1
        laser(
            file, mode="calibration", numfile=7, energy_estimator=7, plot=True, cfg=cfg
        )
    except IOError as e:
        if "acquire lock" not in str(e):
            raise e
        print("!!! SafeHDFStore failed to acquire lock. Deleting lockfile...")
        Path(file.replace(".h5", ".lock")).unlink(missing_ok=True)
        laser(
            file, mode="calibration", numfile=7, energy_estimator=7, plot=True, cfg=cfg
        )
    fail_laser = fail_count

    # -- REPACKER
    sys.argv = ["", "-f", f"{file}"]
    rep.main()

    print("======DONE======")
    if fail_coinc > 0 or fail_laser > 0 or fail_tag > 0:
        print(f"Total Failures: {fail_coinc + fail_laser + fail_tag}")
        print(f".....Laser Tag: {fail_tag}")
        print(f"...Coincidence: {fail_coinc}")
        print(f"...Calibration: {fail_laser}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.argv = [
            "",
            "-f",
            ".root/out/process/cycle11-2024-08-14/processed/chewed_metadata_20240815-020101.775106_Sig_A.h5",
        ]
    main()
