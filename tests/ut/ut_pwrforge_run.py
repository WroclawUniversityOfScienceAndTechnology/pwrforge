from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture
from pytest_subprocess import FakeProcess

from pwrforge.commands.run import pwrforge_run
from pwrforge.config import Config, pwrforgeTarget
from tests.ut.ut_pwrforge_build import (  # noqa: F401
    mock_prepare_config as mock_prepare_config_build,
)
from tests.ut.utils import get_test_project_config


def test_pwrforge_run_bin_path(fp: FakeProcess, mock_prepare_config: MagicMock) -> None:
    bin_path = Path("test", "bin_path")
    bin_file_name = bin_path.name
    fp_bin = fp.register(f"./{bin_file_name}")
    pwrforge_run(bin_path, profile="Debug", params=[], prebuild=False, force_native=True)
    assert fp_bin.call_count() == 1


def test_pwrforge_run(fp: FakeProcess, mock_prepare_config: MagicMock) -> None:
    config = mock_prepare_config.return_value
    target = config.project.default_target
    bin_path = Path(target.get_bin_path(config.project.name.lower(), "Debug"))
    bin_path.parent.mkdir(parents=True)
    bin_path.touch()

    fp_bin = fp.register(f"./{bin_path.name}", stdout="Response")
    pwrforge_run(None, profile="Debug", params=[], prebuild=False, force_native=True)
    assert fp_bin.calls[0].returncode == 0


def test_pwrforge_run_with_build(
    fp: FakeProcess,
    mock_prepare_config: MagicMock,
    mock_prepare_config_build: MagicMock,  # noqa: F811
) -> None:
    bin_path = Path("test", "bin_path")
    bin_file_name = bin_path.name
    fp_bin = fp.register(f"./{bin_file_name}")
    Path("CMakeLists.txt").touch()

    profile_path = "./config/conan/profiles/x86_Debug"
    build_path = "build/x86/Debug"
    fp.register(["conan", "profile", "list"])
    fp.register(["conan", "profile", "detect"])
    fp.register(["conan", "remote", "list-users"])
    fp.register(["conan", "source", "."])
    fp.register(
        [
            "conan",
            "install",
            ".",
            "-pr",
            profile_path,
            "-of",
            build_path,
            "-b",
            "missing",
        ]
    )
    fp.register(["conan", "build", ".", "-pr", profile_path, "-of", build_path])
    fp.register(["cp", "-r", "-f", "build/x86/Debug/build/Debug/*", "."])
    pwrforge_run(bin_path, profile="Debug", params=[], prebuild=True, force_native=True)

    assert fp_bin.calls[0].returncode == 0


def test_pwrforge_run_in_docker_mode(mocker: MockerFixture, mock_prepare_config: MagicMock) -> None:
    mock_prepare_config.return_value.project.build_env = "docker"
    docker_run = mocker.patch(f"{pwrforge_run.__module__}.pwrforge_docker_run")

    pwrforge_run(None, profile="Debug", params=["john"], prebuild=False)

    docker_run.assert_called_once()
    assert docker_run.call_args.kwargs["docker_opts"] == []
    assert docker_run.call_args.kwargs["command"] == "pwrforge run --profile Debug -- john"


def test_pwrforge_run_force_native(mocker: MockerFixture, fp: FakeProcess, mock_prepare_config: MagicMock) -> None:
    mock_prepare_config.return_value.project.build_env = "docker"
    docker_run = mocker.patch(f"{pwrforge_run.__module__}.pwrforge_docker_run")
    bin_path = Path("test", "bin_path")
    fp_bin = fp.register(f"./{bin_path.name}")

    pwrforge_run(bin_path, profile="Debug", params=[], prebuild=False, force_native=True)

    docker_run.assert_not_called()
    assert fp_bin.call_count() == 1


def test_pwrforge_run_docker_native_conflict(
    mocker: MockerFixture, caplog: pytest.LogCaptureFixture, mock_prepare_config: MagicMock
) -> None:
    docker_run = mocker.patch(f"{pwrforge_run.__module__}.pwrforge_docker_run")

    with pytest.raises(SystemExit):
        pwrforge_run(None, profile="Debug", params=[], prebuild=False, force_docker=True, force_native=True)

    docker_run.assert_not_called()
    assert "Options --docker and --native cannot be used together." in caplog.text


@pytest.mark.parametrize("target", [pwrforgeTarget.stm32, pwrforgeTarget.esp32, pwrforgeTarget.atsam])
def test_pwrforge_run_parametrized(
    target: pwrforgeTarget, mocker: MockerFixture, caplog: pytest.LogCaptureFixture
) -> None:
    config = get_test_project_config(target.value)
    mocker.patch(f"{pwrforge_run.__module__}.prepare_config", return_value=config)
    with pytest.raises(SystemExit):
        pwrforge_run(None, profile="Debug", params=[], prebuild=False)
    assert "Running non x86 projects on x86 architecture is not implemented yet" in caplog.text


@pytest.fixture
def mock_prepare_config(mocker: MockerFixture, config: Config) -> MagicMock:
    return mocker.patch(f"{pwrforge_run.__module__}.prepare_config", return_value=config)
