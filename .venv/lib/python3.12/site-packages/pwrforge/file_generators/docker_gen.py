import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict

from pwrforge import __version__
from pwrforge.config import Config
from pwrforge.file_generators.base_gen import create_file_from_template
from pwrforge.global_values import pwrforge_PKG_PATH
from pwrforge.logger import get_logger
from pwrforge.target_helpers import atsam_helper, stm32_helper

logger = get_logger()


class _DockerComposeTemplate:
    """
    This class is a container for docker compose yaml files creation with multilayer approach
    """

    def __init__(self, config: Config, docker_path: Path):
        self.docker_path = docker_path
        self._config = config

    def get_pwrforge_path(self) -> Path:
        try:
            result = subprocess.run(["pip", "show", "pwrforge"], capture_output=True, text=True, check=True)
            for line in result.stdout.splitlines():
                if line.startswith("Location:"):
                    pwrforge_path = Path(line.split("Location:")[1].strip()) / "pwrforge"
                    if pwrforge_path.exists():
                        return pwrforge_path
                    logger.error(f"Error: The pwrforge path {pwrforge_path} does not exist.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Subprocess error while retrieving pwrforge path: {e}")
        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
        except OSError as e:
            logger.error(f"OS error occurred: {e}")

        return Path()

    def generate_docker_env(self) -> None:
        """Generate dirs and files"""
        self._create_file_from_template(
            "docker/Dockerfile-custom.j2",
            "Dockerfile-custom",
            template_params={"project": self._config.project},
            overwrite=False,
        )

        pwrforge_path = self.get_pwrforge_path()
        self._create_file_from_template(
            "docker/docker-compose.yaml.j2",
            "docker-compose.yaml",
            template_params={
                "config": self._config,
                "pwrforge_path": pwrforge_path,
            },
        )
        self._create_file_from_template(
            "docker/devcontainer.json.j2",
            "devcontainer.json",
            template_params={"project": self._config.project},
        )
        if self._config.project.is_stm32():
            stm32_helper.generate_openocd_script(self.docker_path, self._config)
        if self._config.project.is_atsam():
            atsam_helper.generate_openocd_script(self.docker_path, self._config)

        custom_docker = self._get_dockerfile_custom_content()
        pwrforge_package_version = self._set_up_package_version()

        self._create_file_from_template(
            "docker/requirements.txt.j2",
            "requirements.txt",
            template_params={},
            overwrite=True,
        )

        self._create_file_from_template(
            "docker/Dockerfile.j2",
            "Dockerfile",
            template_params={
                "project": self._config.project,
                "pwrforge_package_version": pwrforge_package_version,
                "custom_docker": custom_docker,
            },
        )

    def _create_file_from_template(
        self,
        template_path: str,
        output_filename: str,
        template_params: Dict[str, Any],
        overwrite: bool = True,
    ) -> None:
        create_file_from_template(
            template_path,
            self.docker_path / output_filename,
            template_params=template_params,
            config=self._config,
            overwrite=overwrite,
        )

    def _get_dockerfile_custom_content(self) -> str:
        project_root = self._config.project_root
        custom_docker_path = project_root / self._config.project.docker_file
        if custom_docker_path.is_file():
            return custom_docker_path.read_text()
        return ""

    def _set_up_package_version(self) -> str:
        if whl_path_str := os.getenv("pwrforge_DOCKER_INSTALL_LOCAL"):
            repo_root = pwrforge_PKG_PATH.parent
            whl_path = repo_root / whl_path_str
            shutil.copy(whl_path, self.docker_path)
            return whl_path.name
        return f"pwrforge=={__version__}"


def generate_docker_compose(docker_path: Path, config: Config) -> None:
    docker_compose_template = _DockerComposeTemplate(config, docker_path)
    docker_compose_template.generate_docker_env()
