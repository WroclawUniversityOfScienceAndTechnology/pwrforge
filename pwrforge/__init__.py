# pwrforge/__init__.py
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version

try:
    _installed_version = pkg_version("pwrforge")
    print(f"Installed version [{_installed_version}]")
except PackageNotFoundError:
    _installed_version = "0.0.2"

__version__ = _installed_version or "0.0.2"
