import os
import signal
from pathlib import Path
from unittest.mock import ANY, MagicMock

import pytest
from pytest_mock import MockerFixture

from pwrforge.commands.debug import (
    EMEDDED_GDB_SETTINGS,
    GDB_COMMON_SETTINGS,
    OPENOCD_LOG_PATH,
    _restore_default_sigint,
    _run_interactive_command,
    pwrforge_debug,
)
from tests.ut.utils import get_log_data, get_test_project_config


@pytest.fixture
def mock_debug_config(request: pytest.FixtureRequest, tmpdir: Path, mocker: MockerFixture) -> MagicMock:
    os.chdir(tmpdir)

    mocker.patch("os.system")

    target_id = request.param if hasattr(request, "param") else "x86"
    test_config = get_test_project_config(target_id)
    test_config.project_root = Path(tmpdir)

    return mocker.patch("pwrforge.commands.debug.prepare_config", return_value=test_config)


def test_debug_x86(mock_debug_config: MagicMock, mocker: MockerFixture) -> None:
    config = mock_debug_config.return_value
    target = config.project.default_target
    bin_path = Path(target.get_bin_path(config.project.name.lower()))
    bin_path.parent.mkdir(parents=True)
    bin_path.touch()

    interactive_mock = mocker.patch("pwrforge.commands.debug._run_interactive_command")

    pwrforge_debug(None, None)

    interactive_mock.assert_called_once_with(["gdb", *GDB_COMMON_SETTINGS, bin_path.absolute()], check=False)


def test_debug_gdb_x86(mock_debug_config: MagicMock, mocker: MockerFixture) -> None:
    config = mock_debug_config.return_value
    target = config.project.default_target
    bin_path = Path(target.get_bin_path(config.project.name.lower()))
    bin_path.parent.mkdir(parents=True)
    bin_path.touch()

    interactive_mock = mocker.patch("pwrforge.commands.debug._run_interactive_command")

    pwrforge_debug(None, None, gdb_only=True)

    interactive_mock.assert_called_once_with(["gdb", *GDB_COMMON_SETTINGS, bin_path.absolute()], check=False)
    mock_debug_config.assert_called_once_with(run_in_docker=False)


def test_run_interactive_command_restores_terminal_state(mocker: MockerFixture) -> None:
    stdin_mock = mocker.Mock()
    stdin_mock.isatty.return_value = True
    stdin_mock.fileno.return_value = 0
    mocker.patch("pwrforge.commands.debug.sys.stdin", stdin_mock)

    tcgetattr_mock = mocker.patch("pwrforge.commands.debug.termios.tcgetattr", return_value=["saved"])
    tcsetattr_mock = mocker.patch("pwrforge.commands.debug.termios.tcsetattr")
    process_mock = mocker.Mock()
    process_mock.wait.return_value = 0
    popen_mock = mocker.patch("pwrforge.commands.debug.subprocess.Popen", return_value=process_mock)
    getsignal_mock = mocker.patch("pwrforge.commands.debug.signal.getsignal", return_value=signal.default_int_handler)
    signal_mock = mocker.patch("pwrforge.commands.debug.signal.signal")

    _run_interactive_command(["gdb", "--quiet"], check=True)

    popen_mock.assert_called_once_with(["gdb", "--quiet"], preexec_fn=_restore_default_sigint)
    getsignal_mock.assert_called_once_with(signal.SIGINT)
    signal_mock.assert_any_call(signal.SIGINT, signal.SIG_IGN)
    signal_mock.assert_any_call(signal.SIGINT, signal.default_int_handler)
    tcgetattr_mock.assert_called_once_with(0)
    tcsetattr_mock.assert_called_once_with(0, ANY, ["saved"])


@pytest.mark.parametrize("mock_debug_config", ["stm32"], indirect=True)
def test_debug_arm_fails_when_openocd_server_is_not_ready(
    mock_debug_config: MagicMock,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
) -> None:
    config = mock_debug_config.return_value
    target = config.project.default_target
    bin_path = Path(target.get_bin_path(config.project.name.lower()))
    bin_path.parent.mkdir(parents=True)
    bin_path.touch()

    mocker.patch("pwrforge.commands.debug.find_program_path", return_value=Path("openocd"))
    openocd_process = mocker.Mock()
    openocd_process.poll.return_value = 1
    mocker.patch("pwrforge.commands.debug.subprocess.Popen", return_value=openocd_process)
    wait_mock = mocker.patch("pwrforge.commands.debug._wait_for_gdb_server", return_value=False)
    interactive_mock = mocker.patch("pwrforge.commands.debug._run_interactive_command")

    with pytest.raises(SystemExit):
        pwrforge_debug(None, None)

    wait_mock.assert_called_once_with(openocd_process)
    interactive_mock.assert_not_called()
    log_data = get_log_data(caplog.records)
    assert ("ERROR", "OpenOCD exited before the GDB server became ready.") in log_data
    assert ("INFO", f"See {config.project_root / OPENOCD_LOG_PATH} for OpenOCD output.") in log_data


@pytest.mark.parametrize("mock_debug_config", ["atsam", "stm32"], indirect=True)
def test_debug_arm_starts_gdb_after_openocd_is_ready(
    mock_debug_config: MagicMock,
    mocker: MockerFixture,
) -> None:
    config = mock_debug_config.return_value
    target = config.project.default_target
    bin_path = Path(target.get_bin_path(config.project.name.lower()))
    bin_path.parent.mkdir(parents=True)
    bin_path.touch()

    mocker.patch("pwrforge.commands.debug.find_program_path", return_value=Path("openocd"))
    openocd_process = mocker.Mock()
    openocd_process.poll.return_value = None
    mocker.patch("pwrforge.commands.debug.subprocess.Popen", return_value=openocd_process)
    wait_mock = mocker.patch("pwrforge.commands.debug._wait_for_gdb_server", return_value=True)
    interactive_mock = mocker.patch("pwrforge.commands.debug._run_interactive_command")

    pwrforge_debug(None, None)

    wait_mock.assert_called_once_with(openocd_process)
    interactive_mock.assert_called_once_with(
        [
            "gdb-multiarch",
            *GDB_COMMON_SETTINGS,
            bin_path.absolute(),
            EMEDDED_GDB_SETTINGS,
        ],
        check=False,
    )
    assert (config.project_root / OPENOCD_LOG_PATH).exists()


@pytest.mark.parametrize(
    ("mock_debug_config", "expected_gdb_bin"),
    [("stm32", "gdb-multiarch"), ("atsam", "gdb-multiarch"), ("esp32", "xtensa-esp32-elf-gdb")],
    indirect=["mock_debug_config"],
)
def test_debug_gdb_embedded(
    mock_debug_config: MagicMock,
    expected_gdb_bin: str,
    mocker: MockerFixture,
) -> None:
    config = mock_debug_config.return_value
    target = config.project.default_target
    bin_path = Path(target.get_bin_path(config.project.name.lower()))
    bin_path.parent.mkdir(parents=True)
    bin_path.touch()

    interactive_mock = mocker.patch("pwrforge.commands.debug._run_interactive_command")

    pwrforge_debug(None, None, gdb_only=True)

    interactive_mock.assert_called_once_with(
        [
            expected_gdb_bin,
            *GDB_COMMON_SETTINGS,
            bin_path.absolute(),
            EMEDDED_GDB_SETTINGS,
        ],
        check=False,
    )


@pytest.mark.parametrize("mock_debug_config", ["esp32"], indirect=True)
def test_debug_esp32(mock_debug_config: MagicMock, mocker: MockerFixture) -> None:
    config = mock_debug_config.return_value
    target = config.project.default_target
    bin_path = Path(target.get_bin_path(config.project.name.lower()))

    bin_path.parent.mkdir(parents=True)
    bin_path.touch()

    mocker.patch("pwrforge.commands.debug.find_program_path", return_value=Path("openocd"))
    openocd_process = mocker.Mock()
    openocd_process.poll.return_value = None
    popen_mock = mocker.patch("pwrforge.commands.debug.subprocess.Popen", return_value=openocd_process)
    wait_mock = mocker.patch("pwrforge.commands.debug._wait_for_gdb_server", return_value=True)
    interactive_mock = mocker.patch("pwrforge.commands.debug._run_interactive_command")

    pwrforge_debug(None, None)

    popen_mock.assert_called_once_with(
        [
            Path("openocd"),
            "-f",
            "interface/ftdi/esp32_devkitj_v1.cfg",
            "-f",
            "board/esp-wroom-32.cfg",
        ],
        stdout=ANY,
        stderr=ANY,
    )
    wait_mock.assert_called_once_with(openocd_process)
    interactive_mock.assert_called_once_with(
        [
            "xtensa-esp32-elf-gdb",
            *GDB_COMMON_SETTINGS,
            bin_path.absolute(),
            EMEDDED_GDB_SETTINGS,
        ],
        check=False,
    )
    assert (config.project_root / OPENOCD_LOG_PATH).exists()


@pytest.mark.parametrize("mock_debug_config", ["stm32", "atsam"], indirect=True)
def test_debug_openocd_arm(mock_debug_config: MagicMock, mocker: MockerFixture) -> None:
    mocker.patch("pwrforge.commands.debug.find_program_path", return_value=Path("openocd"))
    interactive_mock = mocker.patch("pwrforge.commands.debug._run_interactive_command")

    pwrforge_debug(None, None, openocd_only=True)

    interactive_mock.assert_called_once_with(
        [Path("openocd"), "-f", ".devcontainer/openocd-script.cfg"],
        check=False,
    )


@pytest.mark.parametrize("mock_debug_config", ["esp32"], indirect=True)
def test_debug_openocd_esp32(mock_debug_config: MagicMock, mocker: MockerFixture) -> None:
    mocker.patch("pwrforge.commands.debug.find_program_path", return_value=Path("openocd"))
    interactive_mock = mocker.patch("pwrforge.commands.debug._run_interactive_command")

    pwrforge_debug(None, None, openocd_only=True)

    interactive_mock.assert_called_once_with(
        [
            Path("openocd"),
            "-f",
            "interface/ftdi/esp32_devkitj_v1.cfg",
            "-f",
            "board/esp-wroom-32.cfg",
        ],
        check=False,
    )


def test_debug_openocd_unsupported_target(mock_debug_config: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
    with pytest.raises(SystemExit):
        pwrforge_debug(None, None, openocd_only=True)

    log_data = get_log_data(caplog.records)
    assert ("ERROR", "Debug --openocd currently not supported for x86") in log_data


def test_debug_mode_flags_are_mutually_exclusive(
    mock_debug_config: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with pytest.raises(SystemExit):
        pwrforge_debug(None, None, openocd_only=True, gdb_only=True)

    log_data = get_log_data(caplog.records)
    assert ("ERROR", "Options --openocd and --gdb are mutually exclusive.") in log_data


def test_debug_bin_not_exists(mock_debug_config: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
    config = mock_debug_config.return_value
    target = config.project.default_target
    bin_path = Path(target.get_bin_path(config.project.name.lower()))
    with pytest.raises(SystemExit):
        pwrforge_debug(None, None)
    log_data = get_log_data(caplog.records)
    assert ("ERROR", f"Binary {bin_path.absolute()} does not exist") in log_data
