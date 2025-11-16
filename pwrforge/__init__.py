# pwrforge/__init__.py
from importlib.metadata import version as pkg_version, PackageNotFoundError
from pathlib import Path
import tomllib


def _get_poetry_version() -> str | None:
    # działa w dev, gdy odpalasz z repo
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    if pyproject.exists():
        with pyproject.open("rb") as f:
            data = tomllib.load(f)
        # U Ciebie wersja jest w [project]
        return data["project"]["version"]
    return None


try:
    _installed_version = pkg_version("pwrforge")
except PackageNotFoundError:
    _installed_version = None

_poetry_version = _get_poetry_version()

__version__ = _installed_version or _poetry_version or "0.0.0"
