import os
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List

import docker as dock
from docker import DockerClient

from pwrforge.config import ProjectConfig
from pwrforge.logger import get_logger

logger = get_logger()

STM32CUBE_CACHE_DIR = "/home/ubuntu/.cache/pwrforge/stm32cube"
STM32CUBE_CACHE_VOLUME_NAME = "pwrforge_stm32cube_cache"


def get_host_supplementary_group_ids() -> List[str]:
    """
    Return host supplementary group IDs as strings.

    Docker bind-mounts host device nodes with their original numeric ownership,
    so the container process needs the same supplemental groups as the invoking
    user to access USB serial/debug devices without sudo.
    """

    if os.name == "nt":
        return []

    primary_gid = os.getgid()
    group_ids = {group_id for group_id in os.getgroups() if group_id != primary_gid}
    return [str(group_id) for group_id in sorted(group_ids)]


def get_docker_volumes(project_path: Path, use_stm32_cube_cache: bool = False) -> Dict[str, Dict[str, str]]:
    volumes = {
        str(project_path): {"bind": "/workspace/", "mode": "rw"},
        "/dev/": {"bind": "/dev/", "mode": "rw"},
    }
    if use_stm32_cube_cache:
        volumes[STM32CUBE_CACHE_VOLUME_NAME] = {"bind": STM32CUBE_CACHE_DIR, "mode": "rw"}
    return volumes


def prepare_docker(project_config: ProjectConfig, project_path: Path) -> Dict[str, Any]:
    relative_path = Path.cwd().relative_to(project_path)
    path_in_docker = PurePosixPath("/workspace", relative_path)

    entrypoint = ""
    if project_config.is_esp32():
        entrypoint = "/opt/esp/entrypoint.sh"

    docker_tag = project_config.docker_image_tag
    client = dock.from_env()

    return {
        "client": client,
        "path_in_docker": path_in_docker,
        "entrypoint": entrypoint,
        "docker_tag": docker_tag,
        "group_add": get_host_supplementary_group_ids(),
        "volumes": get_docker_volumes(project_path, project_config.is_stm32()),
    }


def run_pwrforge_again_in_docker(project_config: ProjectConfig, project_path: Path) -> None:
    """
    Run command in docker

    :param dict project_config: project configuration
    :param Path project_path: path to project root
    :return: None
    """

    if not project_config.is_docker_buildenv() or Path("/.dockerenv").exists():
        return

    cmd_args = sys.argv[1:]
    for idx, val in enumerate(cmd_args):
        if val in ("-B", "--base-dir"):
            cmd_args[idx + 1] = "."

    result = run_command_in_docker(command=["pwrforge", *cmd_args], **prepare_docker(project_config, project_path))
    sys.exit(result["StatusCode"])


def run_command_in_docker(  # type: ignore[no-any-unimported]
    command: List[str],
    client: DockerClient,
    docker_tag: str,
    entrypoint: str,
    group_add: List[str],
    volumes: Dict[str, Dict[str, str]],
    path_in_docker: PurePosixPath,
) -> Dict[str, Any]:
    logger.info(f"Running '{' '.join(command)}' command in docker.")
    container = client.containers.run(
        docker_tag,
        command,
        volumes=volumes,
        entrypoint=entrypoint,
        group_add=group_add,
        privileged=True,
        detach=True,
        working_dir=str(path_in_docker),
    )
    output = container.attach(stdout=True, stream=True, logs=True, stderr=True)
    output_str = ""
    for line in output:
        # INFO: IT tests and their checks rely on stdout value and this cannot be removed.
        # INFO: tests/it/it_pwrforge_commands_flow.py should be rewritten, to not rely on stdout.
        print(line.decode(), end="")
        output_str += line.decode()
    result = container.wait()
    container.remove()
    return {"StatusCode": result["StatusCode"], "output": output_str}
