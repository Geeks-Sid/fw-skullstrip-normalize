"""The fw_skullstrip_normalize package."""
from importlib.metadata import PackageNotFoundError, version

pkg_name = __package__
__version__ = "0.0.1"
try:
    __version__ = version(pkg_name.replace("_", "-"))
except PackageNotFoundError:  # pragma: no cover
    pass
