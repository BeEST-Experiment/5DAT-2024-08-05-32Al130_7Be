"""Drop channels from h5 files and rewrite files.

Takes a kw file in for config: this is a python file with `c` pre-defined as a Config object.
Attributes may be added (see _parse_kwdict)
"""

import click
import traitlets.config as tlc
from joblib import Parallel, delayed
from pathlib import Path
import pandas as pd
import warnings
from beest.utils import Configured, save_artefacts
from traitlets.config import Config

#: Silence pickle warning when saving metadata dataframe
warnings.filterwarnings("ignore", category=pd.io.pytables.PerformanceWarning)  # type: ignore


def main(
    directory=".",
    filethreads=4,
    multithread=True,
    patterns=("*.h5",),
    channels=None,
    outdir=None,
    ckey=None,
    cfg=Config(),
    fname="Main",
):
    """Run the drop_channels function."""
    if not channels:
        channels = []

    # -- Use a channel map to specify channels per set for parallel op
    if cfg.ChannelMap:
        [channels.extend(cfg.ChannelMap[k]) for k in cfg.ChannelMap if k in directory]

    directory = Path(directory)
    if directory.is_dir():
        paths = []
        for pattern in patterns:
            paths.extend(directory.glob(pattern))
    else:
        paths = [directory]

    print(f" Dropping channels: {channels}")
    if multithread and filethreads > 1:
        Parallel(n_jobs=filethreads)(delayed(drop_channels)(f, channels) for f in paths)
    else:
        print("   in single-thread mode")
        for f in paths:
            drop_channels(f, channels)

    if outdir:
        save_artefacts(cfg, "drop-channels-artefacts.dill", dev=bool(ckey))


def drop_channels(path, channels):
    """Drop channels from a file."""
    chs = list(channels)
    file = Path(path).name
    parent = Path(path).parent
    print(f"Dropping channels and rewriting file: {file}")

    datakeys, metakeys = _verify_file(path)

    #: Must be specified inside subshell to avoid warnings
    # warnings.filterwarnings("ignore", category=pd.io.pytables.PerformanceWarning)  # type: ignore
    tmppath = Path(parent, f"tmp_{file}")
    for key in datakeys:
        channel = int(key.removeprefix("/data_channel"))
        if channel not in chs:
            pd.read_hdf(path, key=key).infer_objects().to_hdf(
                tmppath, key=key, mode="a", complevel=1
            )

    for key in metakeys:
        channel = int(key.removeprefix("/metadata_channel"))
        if channel not in chs:
            pd.read_hdf(path, key=key).infer_objects().to_hdf(
                tmppath, key=key, mode="a", complevel=1
            )

    _verify_file(tmppath)
    Path(path).unlink()
    # -- Remember that Path rename actually moves files!!
    Path(tmppath).rename(path)
    _verify_file(path)
    print(f"Finished file {file}")


def _verify_file(path):
    f = pd.HDFStore(path, mode="r")
    keys = f.keys()
    f.close()
    datakeys = [k for k in keys if k.startswith("/data_channel")]
    metakeys = [k for k in keys if k.startswith("/metadata_channel")]
    assert len(datakeys) == len(
        metakeys
    ), f"not every channel in {path} has data+metadata {keys}"
    ekeys = [k for k in keys if k not in datakeys and k not in metakeys]
    assert len(ekeys) == 0, f"extraneous keys in {path}! {ekeys}"
    return datakeys, metakeys


@click.command()
@click.option(
    "-f",
    "--cfg",
    type=str,
    help="(traitlet config pyfile) file with config options",
)
@click.option(
    "-d",
    "--directory",
    type=str,
    default=".",
    show_default=True,
    help="chewed h5 file(s). It can be either a directory or a file",
)
@click.option(
    "-t",
    "--filethreads",
    type=int,
    default=4,
    show_default=True,
    help="number of threads for multiprocessing",
)
@click.option(
    "-m",
    "--multithread",
    is_flag=True,
    default=True,
    show_default=True,
    help="use multithreading",
)
@click.option(
    "-p",
    "--patterns",
    multiple=True,
    default=("*.h5",),
    show_default=True,
    help="file patterns to match",
)
@click.option(
    "-c",
    "--channels",
    multiple=True,
    default=[],
    show_default=True,
    help="channels to drop",
)
@click.option(
    "-k",
    "--ckey",
    type=str,
    default=None,
    show_default=True,
    help="custom key for the dev artefacts in the config, if desired to be saved",
)
@click.option(
    "-o",
    "--outdir",
    type=str,
    default=None,
    show_default=True,
    help="output directory for the artefacts file. Must be unique per ckey and merged later (parallel-safe).",
)
def run(
    directory=".",
    filethreads=4,
    multithread=True,
    patterns=("*.h5",),
    channels=(),
    outdir=None,
    ckey=None,
    cfg=None,
):
    """
    Do I wanna specify the ckey in the Config file or at runtime?
    I think runtime because the Config file should be static.
    Thus, to parallelize, the ckey must be passed per call.
    """
    # -- To allow config by option or by Config file
    C = Config()
    C.KWArgs.Main.directory = directory
    C.KWArgs.Main.filethreads = filethreads
    C.KWArgs.Main.multithread = multithread
    C.KWArgs.Main.patterns = patterns
    C.KWArgs.Main.channels = list(channels)
    C.KWArgs.Main.outdir = outdir
    if cfg:
        # -- Configs in file take precedence
        C.update(tlc.PyFileConfigLoader(cfg).load_config())
    Configured(main, C)(ckey=ckey)


if __name__ == "__main__":
    run()
