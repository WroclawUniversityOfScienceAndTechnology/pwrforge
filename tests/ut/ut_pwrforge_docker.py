import os
import re
from pathlib import Path, PurePosixPath
from typing import Any, List, Sequence
from unittest.mock import MagicMock

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from pwrforge.commands.docker import (
    get_docker_compose_command,
    pwrforge_docker_build,
    pwrforge_docker_exec,
    pwrforge_docker_run,
)
from pwrforge.config import Config
from pwrforge.utils.docker_utils import (
    STM32CUBE_CACHE_DIR,
    STM32CUBE_CACHE_VOLUME_NAME,
    get_docker_project_name,
    get_docker_volumes,
    get_host_supplementary_group_ids,
    run_command_in_docker,
)
from tests.ut.utils import get_test_project_config


@pytest.fixture
def pwrforge_docker_test_setup(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Config:
    os.chdir(tmp_path)

    test_project_config = get_test_project_config()
    test_project_config.project_root = Path()
    monkeypatch.setattr(
        "pwrforge.commands.docker.get_pwrforge_config_or_exit",
        lambda: test_project_config,
    )

    return test_project_config


def test_docker_fails_when_inside_docker(
    caplog: pytest.LogCaptureFixture,
    mock_subprocess_run: MagicMock,
    pwrforge_docker_test_setup: Config,
    fs: FakeFilesystem,
) -> None:
    Path("/.dockerenv").mkdir()
    with pytest.raises(SystemExit):
        pwrforge_docker_build([])
    assert "Cannot used docker command inside the docker container" in caplog.text


@pytest.mark.parametrize(
    "command_args",
    ([], ["--no-cache"], ["--rm"], ["--no-cache", "--parallel", "--rm"]),
)
def test_docker_build(
    command_args: List[str],
    mock_subprocess_run: MagicMock,
    pwrforge_docker_test_setup: Config,
) -> None:
    pwrforge_docker_build(command_args)
    called_subprocess_cmd = get_docker_compose_command(pwrforge_docker_test_setup.project_root)
    called_subprocess_cmd.extend(["build", *command_args])
    assert mock_subprocess_run.call_args.args[0] == called_subprocess_cmd


@pytest.mark.parametrize(
    "command_args",
    ([], ["--no-deps"], ["--rm"], ["--no-deps", "--rm"]),
)
def test_docker_run(
    command_args: List[str],
    mock_subprocess_run: MagicMock,
    pwrforge_docker_test_setup: Config,
) -> None:
    pwrforge_docker_run(command_args)

    service_name = f"{pwrforge_docker_test_setup.project.name}_dev"
    called_subprocess_cmd = get_docker_compose_command(pwrforge_docker_test_setup.project_root)
    called_subprocess_cmd.extend(["run"])

    called_subprocess_cmd.extend(command_args)
    called_subprocess_cmd.append(service_name)
    assert mock_subprocess_run.call_args.args[0] == called_subprocess_cmd


def test_docker_run_with_command(mock_subprocess_run: MagicMock, pwrforge_docker_test_setup: Config) -> None:
    rm = "--rm"
    command = 'bash -c "pwd"'

    pwrforge_docker_run(docker_opts=[rm], command=command)

    service_name = f"{pwrforge_docker_test_setup.project.name}_dev"
    called_subprocess_cmd = get_docker_compose_command(pwrforge_docker_test_setup.project_root)

    called_subprocess_cmd.extend(
        [
            "run",
            rm,
            service_name,
            "bash",
            "-c",
            command,
        ]
    )
    assert mock_subprocess_run.call_args.args[0] == called_subprocess_cmd


@pytest.mark.parametrize("port_args", [["--service-ports"], ["-P"], ["-p", "3334:3333"]])
def test_docker_run_preserves_explicit_ports(
    port_args: List[str], mock_subprocess_run: MagicMock, pwrforge_docker_test_setup: Config
) -> None:
    pwrforge_docker_run(docker_opts=[*port_args, "--rm"])

    service_name = f"{pwrforge_docker_test_setup.project.name}_dev"
    called_subprocess_cmd = get_docker_compose_command(pwrforge_docker_test_setup.project_root)
    called_subprocess_cmd.extend(["run", *port_args, "--rm", service_name])
    assert mock_subprocess_run.call_args.args[0] == called_subprocess_cmd


class FakeDockerClient:
    def __init__(self, *container_ids: str):
        self.containers = self.FakeContainerCollection(container_ids)

    class FakeContainerCollection:
        class FakeContainer:
            def __init__(self, id: str):
                self.id = id
                self.status = "running"

        def __init__(self, container_ids: Sequence[str]) -> None:
            self.container_list = [self.FakeContainer(id) for id in container_ids]

        def list(self, *args: Any, **kwargs: Any) -> List[FakeContainer]:
            return self.container_list


class FakeContainerRunResult:
    def attach(self, *args: Any, **kwargs: Any) -> List[bytes]:
        return []

    def wait(self) -> dict[str, Any]:
        return {"StatusCode": 0}

    def remove(self) -> None:
        return None


class FakeDockerRunClient:
    def __init__(self) -> None:
        self.containers = self
        self.run_args: Any = None
        self.run_kwargs: Any = None

    def run(self, *args: Any, **kwargs: Any) -> FakeContainerRunResult:
        self.run_args = args
        self.run_kwargs = kwargs
        return FakeContainerRunResult()


def test_docker_exec(
    mock_subprocess_run: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    pwrforge_docker_test_setup: Config,
) -> None:
    container_id = "some_hash"
    monkeypatch.setattr("docker.from_env", lambda: FakeDockerClient(container_id))
    pwrforge_docker_exec([])

    called_subprocess_cmd = ["docker", "exec", "-it", container_id, "bash"]
    assert mock_subprocess_run.call_args.args[0] == called_subprocess_cmd


def test_docker_exec_no_container(
    mock_subprocess_run: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    pwrforge_docker_test_setup: Config,
) -> None:
    monkeypatch.setattr("docker.from_env", lambda: FakeDockerClient())
    with pytest.raises(SystemExit):
        pwrforge_docker_exec([])


def test_get_host_supplementary_group_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("pwrforge.utils.docker_utils.os.getgid", lambda: 1000)
    monkeypatch.setattr("pwrforge.utils.docker_utils.os.getgroups", lambda: [20, 46, 1000, 20, 998])

    assert get_host_supplementary_group_ids() == ["20", "46", "998"]


def test_get_docker_volumes_adds_stm32_cache() -> None:
    volumes = get_docker_volumes(Path("/tmp/project"), use_stm32_cube_cache=True)

    assert volumes[str(Path("/tmp/project"))] == {"bind": "/workspace/", "mode": "rw"}
    assert volumes["/dev/"] == {"bind": "/dev/", "mode": "rw"}
    assert volumes[STM32CUBE_CACHE_VOLUME_NAME] == {"bind": STM32CUBE_CACHE_DIR, "mode": "rw"}


def test_run_command_in_docker_passes_host_groups() -> None:
    fake_client = FakeDockerRunClient()
    volumes = get_docker_volumes(Path("/tmp/project"), use_stm32_cube_cache=True)

    result = run_command_in_docker(
        command=["pwrforge", "flash"],
        client=fake_client,
        docker_tag="test-image:latest",
        entrypoint="",
        group_add=["20", "46"],
        volumes=volumes,
        path_in_docker=PurePosixPath("/workspace"),
    )

    assert result["StatusCode"] == 0
    assert fake_client.run_kwargs["group_add"] == ["20", "46"]
    assert fake_client.run_kwargs["volumes"] == volumes


@pytest.mark.parametrize("directory", ["My Project!", "___", "Żółć", "a" * 100])
def test_docker_project_name_is_valid_and_stable(tmp_path: Path, directory: str) -> None:
    root = tmp_path / directory
    name = get_docker_project_name(root)
    assert re.fullmatch(r"[a-z0-9][a-z0-9_-]*", name)
    assert len(name) <= 63
    assert name == get_docker_project_name(root / "nested" / "..")
    assert name != get_docker_project_name(tmp_path / "other" / directory)


def test_docker_run_isolates_projects_without_stopping_containers(
    tmp_path: Path,
    mock_subprocess_run: MagicMock,
    pwrforge_docker_test_setup: Config,
) -> None:
    for parent in ("first", "second"):
        pwrforge_docker_test_setup.project_root = tmp_path / parent / "same_name"
        pwrforge_docker_run([])

    assert mock_subprocess_run.call_count == 2
    first, second = mock_subprocess_run.call_args_list
    first_cmd, second_cmd = first.args[0], second.args[0]
    assert first_cmd[first_cmd.index("--project-name") + 1] != second_cmd[second_cmd.index("--project-name") + 1]
    for call in (first, second):
        assert call.args[0][-2:] == ["run", f"{pwrforge_docker_test_setup.project.name}_dev"]
        assert "--service-ports" not in call.args[0]
        assert "down" not in call.args[0]
    assert first.kwargs["cwd"] == tmp_path / "first" / "same_name" / ".devcontainer"
    assert second.kwargs["cwd"] == tmp_path / "second" / "same_name" / ".devcontainer"


def test_docker_exec_filters_by_project_and_service(
    mock_subprocess_run: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    pwrforge_docker_test_setup: Config,
) -> None:
    client = MagicMock()
    client.containers.list.return_value = [MagicMock(id="project_container")]
    monkeypatch.setattr("docker.from_env", lambda: client)

    pwrforge_docker_exec([])

    client.containers.list.assert_called_once_with(
        limit=1,
        filters={
            "ancestor": pwrforge_docker_test_setup.project.docker_image_tag,
            "status": "running",
            "label": [
                f"com.docker.compose.project={get_docker_project_name(pwrforge_docker_test_setup.project_root)}",
                f"com.docker.compose.service={pwrforge_docker_test_setup.project.name}_dev",
            ],
        },
    )
    assert mock_subprocess_run.call_args.args[0] == ["docker", "exec", "-it", "project_container", "bash"]
