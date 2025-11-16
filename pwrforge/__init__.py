# pwrforge/__init__.py
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version

try:
    _installed_version = pkg_version("pwrforge")
except PackageNotFoundError:
    _installed_version = None

__version__ = _installed_version or "0.0.0"
