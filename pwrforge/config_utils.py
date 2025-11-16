import os
import sys
from pathlib import Path
from typing import Optional

import tomlkit

from pwrforge import __version__
from pwrforge.config import Config, ConfigError, Target, parse_config, pwrforgeTarget
from pwrforge.global_values import PWRFORGE_LOCK_FILE
from pwrforge.logger import get_logger
from pwrforge.utils.docker_utils import run_pwrforge_again_in_docker
from pwrforge.utils.path_utils import get_config_file_path

logger = get_logger()


def set_up_environment_variables(config: Config) -> None:
    os.environ["pwrforge_PROJECT_ROOT"] = str(config.project_root.absolute())
    if config.project.in_repo_conan_cache:
        os.environ["CONAN_HOME"] = f"{config.project_root}/.conan2"


def get_pwrforge_config_or_exit(
    config_file_path: Optional[Path] = None,
) -> Config:
    """
    :param config_file_path
    :return: project configuration as dict
    """
    if config_file_path is None:
        config_file_path = get_config_file_path(PWRFORGE_LOCK_FILE)
    if config_file_path is None or not config_file_path.exists():
        logger.error("File `%s` does not exist.", PWRFORGE_LOCK_FILE)
        logger.info("Did you run `pwrforge update`?")
        sys.exit(1)

    try:
        config = parse_config(config_file_path)
    except ConfigError as e:
        logger.error(e.args[0])
        sys.exit(1)
    except Exception as e:  # pylint: disable=W0718
        logger.error("Error while parsing config file %s: %s", config_file_path, e)
        sys.exit(1)

    return config


def prepare_config(run_in_docker: bool = True) -> Config:
    """
    Prepare configuration file and set up eniromnent variables

    :return: project configuration
    """
    config = get_pwrforge_config_or_exit()
    check_pwrforge_version(config)
    set_up_environment_variables(config)
    if run_in_docker:
        run_pwrforge_again_in_docker(config.project, config.project_root)
    return config


def check_pwrforge_version(config: Config) -> None:
    """
    Check pwrforge version

    :param Config config: project configuration
    :return: None
    """
    version_lock = config.pwrforge.version
    if __version__ != version_lock:
        logger.warning("Warning: pwrforge package is different then in lock file")
        logger.info("Run pwrforge update")


def add_version_to_pwrforge_lock(pwrforge_lock: Path) -> None:
    """
    :return: project configuration as dict
    """
    with open(pwrforge_lock, encoding="utf-8") as pwr_lock_file:
        config = tomlkit.load(pwr_lock_file)

    config.setdefault("pwrforge", tomlkit.table())["version"] = __version__
    with open(pwrforge_lock, "w", encoding="utf-8") as pwr_lock_file:
        tomlkit.dump(config, pwr_lock_file)


def get_target_or_default(config: Config, target: Optional[pwrforgeTarget]) -> Target:
    if target:
        if target.value not in config.project.target_id:
            logger.error("Target %s not defined in pwrforge toml", target.value)
            sys.exit(1)
        return Target.get_target_by_id(target.value)
    return config.project.default_target
