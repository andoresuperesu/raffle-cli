"""raffle-cli: a transparent terminal raffle for meetup giveaways."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("raffle-cli")
except PackageNotFoundError:  # running from a source tree that isn't installed
    __version__ = "0.0.0"

from .cli import app, main_cli  # noqa: E402

__all__ = ["app", "main_cli", "__version__"]
