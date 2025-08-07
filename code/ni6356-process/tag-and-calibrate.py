import beestp3.processors.BeEST_laser_calibration as blc
import beestp3.processors.BeEST_coincidence_tagger as blt
import cryoant.apps.repacker as rep
import sys, os


def main():
    """Tag and Calibrate Data

    This script is used to tag and calibrate data using the BeEST_laser_calibration and BeEST_coincidence_tagger packages.
    It requires the environment variable 'dir' to be set to the directory containing the processed data.
    """
    dir = os.getenv("dir")
    if dir is None:
        print(
            "Please set the environment variable 'dir' to the directory containing the processed data."
        )
        return
    #: LASER TAG
    try:
        sys.argv = ["", "-m", "tagging", "-d", f"{dir}/processed"]
        blc.main()
    except Exception as e:
        print(f"Error: {e}")
    #: COINCIDENCE
    try:
        sys.argv = ["", "-d", f"{dir}/processed"]
        blt.main()
    except Exception as e:
        print(f"Error: {e}")
    #: CALIBRATION
    try:
        sys.argv = [
            "",
            "-m",
            "calibration",
            "--numfile",
            "5",
            "-e",
            "4",
            "-d",
            f"{dir}/processed",
            "-p",
        ]
        blc.main()
    except Exception as e:
        print(f"Error: {e}")
    #: REPACKER
    try:
        sys.argv = ["", "-f", f"{dir}/processed"]
        rep.main()
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
