"""Drop channels from h5 files and rewrite files.

Takes a kw file in for config: this is a python file with `c` pre-defined as a Config object.
Attributes may be added (see _parse_kwdict)
"""

import click, os
import traitlets.config as tlc
from joblib import Parallel, delayed
from pathlib import Path
import pandas as pd
import warnings

#: Silence pickle warning when saving metadata dataframe
warnings.filterwarnings("ignore", category=pd.io.pytables.PerformanceWarning)  # type: ignore


@click.command()
@click.option(
    "-f",
    "--kwfile",
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
    default=["*.h5"],
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
def main(kwfile, directory, filethreads, multithread, patterns, channels):
    """Run the drop_channels function."""
    c = tlc.Config()
    #: default values. kw file should look like this:
    c.directory = directory
    c.filethreads = filethreads
    c.multithread = multithread
    c.patterns = patterns
    c.channels = channels

    if kwfile is not None:
        c.update(tlc.PyFileConfigLoader(kwfile).load_config())

    c.directory = Path(c.directory)
    print(f" Dropping channels: {c.channels}")

    paths = []
    for pattern in c.patterns:
        paths.extend(c.directory.glob(pattern))

    Parallel(n_jobs=c.filethreads)(delayed(drop_channels)(f, c.channels) for f in paths)
    # [drop_channels(f, c.channels) for f in paths]


def drop_channels(path, channels):
    """Drop channels from a file."""
    chs = list(channels)
    file = Path(path).name
    parent = Path(path).parent
    print(f"Dropping channels and rewriting file: {file}")

    datakeys, metakeys = _verify_file(path)

    #: Must be specified inside subshell to avoid warnings
    warnings.filterwarnings("ignore", category=pd.io.pytables.PerformanceWarning)  # type: ignore
    tmppath = Path(parent, f"tmp_{file}")
    for key in datakeys:
        channel = int(key.removeprefix("/data_channel"))
        if channel not in chs:
            pd.read_hdf(path, key=key).to_hdf(tmppath, key=key, mode="a", complevel=1)

    for key in metakeys:
        channel = int(key.removeprefix("/metadata_channel"))
        if channel not in chs:
            pd.read_hdf(path, key=key).to_hdf(tmppath, key=key, mode="a", complevel=1)

    _verify_file(tmppath)
    os.remove(path)
    os.rename(tmppath, path)
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


if __name__ == "__main__":
    main()
