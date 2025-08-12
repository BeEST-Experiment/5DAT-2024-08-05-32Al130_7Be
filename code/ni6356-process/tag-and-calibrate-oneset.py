"""Tag and Calibrate One Set of Data (For Parallelization)"""

import click
import lib.process.laser as laser
import lib.process.tag as tag
import cryoant.apps.repacker as rep
import sys
from traitlets.config import Config


def null(*args, **kwargs):
    """A null function to replace the original `main` function in the modules."""
    pass


blc = laser.run.callback or null
blt = tag.run.callback or null

C = Config()
# -- I could just call main directly...
C.KWArgs.Main.dev = True
# -- For an old version of the helper which relies on K-peak
# C.KWArgs.GetCalibrationHelper.rough_k_peak_tmp = 0.01
C.KWArgs.GetCalibrationHelper.reqd_tolerance = 0.3  # Bump tolerance to 0.3
C.KWArgs.GetUncalibratedEnergy.scaleFactor = 1000  # Scale factor for height in mV to V


@click.command("main")
@click.option("--file", "-f", required=True, help="The file to process")
def main(file):
    #: LASER TAG
    # try:
    sys.argv = ["", "-m", "tagging", "-d", f"{file}"]
    blc(cfg=C)
    # except Exception as e:
    #     print(f"Error: {e}")
    #: COINCIDENCE
    # try:
    sys.argv = ["", "-d", f"{file}"]
    blt(cfg=C)
    # except Exception as e:
    # print(f"Error: {e}")
    #: CALIBRATION
    # try:
    sys.argv = [
        "",
        "-m",
        "calibration",
        "--numfile",
        "7",
        "-e",
        "7",
        "-d",
        f"{file}",
        "-p",
    ]
    blc(cfg=C)
    # except Exception as e:
    # print(f"Error: {e}")
    #: REPACKER
    # try:
    sys.argv = ["", "-f", f"{file}"]
    rep.main()
    # except Exception as e:
    # print(f"Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.argv = [
            "",
            "-f",
            ".root/out/process/cycle11-2024-08-14/processed/chewed_metadata_20240815-020101.775106_Sig_A.h5",
        ]
    main()
