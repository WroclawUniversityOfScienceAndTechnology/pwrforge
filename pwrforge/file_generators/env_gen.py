import getpass
import os
from dataclasses import dataclass
from pathlib import Path

from pwrforge.config import Config
from pwrforge.file_generators.base_gen import create_file_from_template
from pwrforge.global_values import ENV_DEFAULT_NAME


@dataclass
class _EnvironmentDescriptor:
    user_name: str = getpass.getuser()
    user_passwd: str = "user"
    user_gid: int = 1000 if os.name == "nt" else os.getgid()
    user_uid: int = 1000 if os.name == "nt" else os.getuid()
    ssh_port: int = 2000
    base_docker_image: str = "ubuntu:24.04"
    conan_username: str = ""
    conan_passwd: str = ""


def generate_env(output_dir_path: Path, config: Config) -> None:
    """
    Generate .env file which is used by docker compose
    providing environmental variables
    """
    env_output_path = output_dir_path / ENV_DEFAULT_NAME
    create_file_from_template(
        "docker/env.txt.j2",
        env_output_path,
        overwrite=False,
        template_params={"env": _EnvironmentDescriptor()},
        config=config,
    )
