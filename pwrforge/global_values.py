"""Global values for pwrforge"""

import importlib.util
from pathlib import Path

DESCRIPTION = "C/C++ package and software development life cycle manager based on RUST cargo idea."

spec = importlib.util.find_spec("pwrforge")
pwrforge_PKG_PATH = Path(spec.origin).parent if spec and spec.origin else Path(__file__).parent
pwrforge_DEFAULT_BUILD_ENV = "docker"
pwrforge_DOCKER_ENV = "docker"

pwrforge_LOCK_FILE = "pwrforge.lock"
pwrforge_DEFAULT_CONFIG_FILE = "pwrforge.toml"
ENV_DEFAULT_NAME = ".env"

pwrforge_HEADER_EXTENSIONS_DEFAULT = (".h", ".hpp", ".hxx", ".hh", ".inc", ".inl")
pwrforge_SRC_EXTENSIONS_DEFAULT = (".c", ".cpp", ".cxx", ".cc", ".s", ".S", ".asm")

pwrforge_UT_COV_FILES_PREFIX = "ut-coverage"
