"""Handle docker for project"""

import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Sequence

import docker

from pwrforge.config_utils import get_pwrforge_config_or_exit
from pwrforge.logger import get_logger
from pwrforge.utils.docker_utils import get_docker_project_name

logger = get_logger()


def pwrforge_docker_build(docker_opts: Sequence[str], project_root: Optional[Path] = None) -> None:
    """
    Build docker

    :param docker_opts: additional docker options
    :param project_root: pwrforge project root path
    :raises CalledProcessError: if docker build fail
    """
    logger.debug("Build docker environment.")
    if not project_root:
        project_root = get_pwrforge_config_or_exit().project_root
    docker_path = _get_docker_path(project_root)

    if docker_opts is None:
        docker_opts = []

    cmd = get_docker_compose_command(project_root)
    cmd.extend(["build", *docker_opts])

    try:
        subprocess.run(cmd, cwd=docker_path, check=True)
        logger.info("Initialize docker environment.")
    except subprocess.CalledProcessError:
        logger.error("Build docker fail.")
        sys.exit(1)


def pwrforge_docker_run(
    docker_opts: Sequence[str],
    command: Optional[str] = None,
) -> None:
    """
    Run docker

    :param docker_opts: additional docker options
    :param command: command to run in the container
    :raises CalledProcessError: if docker did not start
    """
    logger.debug("Run docker environment.")

    config = get_pwrforge_config_or_exit()
    docker_path = _get_docker_path(config.project_root)
    project_config_name = config.project.name

    if not docker_opts:
        docker_opts = []

    cmd = get_docker_compose_command(config.project_root)
    cmd.extend(
        [
            "run",
            *docker_opts,
            f"{project_config_name}_dev",
        ]
    )
    if command:
        cmd.extend(["bash", "-c", command])

    try:
        subprocess.run(cmd, cwd=docker_path, check=True)
        logger.info("Stop docker environment.")
    except subprocess.CalledProcessError:
        sys.exit(1)


def pwrforge_docker_exec(docker_opts: List[str]) -> None:
    """
    Exec docker

    :param docker_opts: additional docker options
    :raises CalledProcessError: if docker did not start
    """
    logger.debug("Exec docker environment.")

    config = get_pwrforge_config_or_exit()
    image = config.project.docker_image_tag

    if docker_opts is None:
        docker_opts = []

    if not image:
        logger.error("docker-image-tag not defined in .toml under project section")
        sys.exit(1)

    client = docker.from_env()
    newest_container = client.containers.list(
        limit=1,
        filters={
            "ancestor": image,
            "status": "running",
            "label": [
                f"com.docker.compose.project={get_docker_project_name(config.project_root)}",
                f"com.docker.compose.service={config.project.name}_dev",
            ],
        },
    )
    if not newest_container:
        logger.error("No running containers for this project using image `%s` to attach to!", image)
        logger.info("Use pwrforge docker run to run container.")
        sys.exit(1)

    bash_command = ["bash"]
    cmd = ["docker", "exec", "-it", *docker_opts, newest_container[0].id, *bash_command]
    try:
        subprocess.run(cmd, check=True)
        logger.info("Stop exec docker environment.")
    except subprocess.CalledProcessError:
        sys.exit(1)


def _get_docker_path(project_path: Path) -> Path:
    # do not rebuild dockers in the docker
    if Path("/.dockerenv").exists():
        logger.error("Cannot used docker command inside the docker container.")
        sys.exit(1)
    return Path(project_path, ".devcontainer")


def get_docker_compose_command(project_root: Optional[Path] = None) -> List[str]:
    """Get docker command

    Returns:
        List[str]: _description_
    """
    command = ["docker-compose"]
    # Check if docker-compose or docker compose is available
    if shutil.which("docker-compose"):
        command = ["docker-compose"]
    elif shutil.which("docker"):
        command = ["docker", "compose"]
    else:
        logger.error("Neither docker-compose nor docker compose are available.")
        sys.exit(1)

    if project_root is not None:
        command.extend(["--project-name", get_docker_project_name(project_root)])
    return command
