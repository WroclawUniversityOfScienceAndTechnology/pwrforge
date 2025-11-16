"""Global values for pwrforge"""

import importlib.util
from pathlib import Path

DESCRIPTION = "C/C++ package and software development life cycle manager based on RUST cargo idea."

spec = importlib.util.find_spec("pwrforge")
PWRFORGE_PKG_PATH = Path(spec.origin).parent if spec and spec.origin else Path(__file__).parent
PWRFORGE_DEFAULT_BUILD_ENV = "docker"
PWRFORGE_DOCKER_ENV = "docker"

PWRFORGE_LOCK_FILE = "pwrforge.lock"
PWRFORGE_DEFAULT_CONFIG_FILE = "pwrforge.toml"
ENV_DEFAULT_NAME = ".env"

PWRFORGE_HEADER_EXTENSIONS_DEFAULT = (".h", ".hpp", ".hxx", ".hh", ".inc", ".inl")
PWRFORGE_SRC_EXTENSIONS_DEFAULT = (".c", ".cpp", ".cxx", ".cc", ".s", ".S", ".asm")

PWRFORGE_UT_COV_FILES_PREFIX = "ut-coverage"
