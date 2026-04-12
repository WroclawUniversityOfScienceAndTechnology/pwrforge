import os
import platform
import signal
import socket
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from time import monotonic
from typing import Iterator, List, Optional, Sequence

try:
    import termios
except ImportError:  # pragma: no cover
    termios = None  # type: ignore[assignment]

from pwrforge.config import Config, pwrforgeTarget
from pwrforge.config_utils import get_target_or_default, prepare_config
from pwrforge.logger import get_logger
from pwrforge.utils.sys_utils import find_program_path

logger = get_logger()


GDB_COMMON_SETTINGS = [
    "--quiet",
    "--eval-command=set pagination off",
    "--eval-command=set height 0",
    "--eval-command=set width 0",
]
EMBEDDED_GDB_HOST = "127.0.0.1"
EMBEDDED_GDB_PORT = 3333
EMEDDED_GDB_SETTINGS = f"--eval-command=target extended-remote {EMBEDDED_GDB_HOST}:{EMBEDDED_GDB_PORT}"
OPENOCD_LOG_PATH = Path(".devcontainer/openocd-debug.log")
OPENOCD_STARTUP_TIMEOUT_S = 10.0
OPENOCD_STARTUP_POLL_INTERVAL_S = 0.1


@contextmanager
def _preserve_terminal_state() -> Iterator[None]:
    if termios is None or not sys.stdin.isatty():
        yield
        return

    try:
        stdin_fd = sys.stdin.fileno()
        terminal_state = termios.tcgetattr(stdin_fd)
    except (AttributeError, OSError, ValueError, termios.error):
        yield
        return

    try:
        yield
    finally:
        try:
            termios.tcsetattr(stdin_fd, termios.TCSADRAIN, terminal_state)
        except (OSError, ValueError, termios.error):
            pass


def _restore_default_sigint() -> None:
    signal.signal(signal.SIGINT, signal.SIG_DFL)


# pylint: disable=consider-using-with,subprocess-popen-preexec-fn
def _run_interactive_command(command: Sequence[str], check: bool) -> None:
    with _preserve_terminal_state():
        if platform.system() == "Windows":
            subprocess.run(command, check=check)
            return

        previous_sigint_handler = signal.getsignal(signal.SIGINT)
        try:
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            process = subprocess.Popen(
                command,
                preexec_fn=_restore_default_sigint,
            )
            returncode = process.wait()
        finally:
            signal.signal(signal.SIGINT, previous_sigint_handler)

        if check and returncode:
            raise subprocess.CalledProcessError(returncode, command)


def _wait_for_gdb_server(openocd: subprocess.Popen) -> bool:  # type: ignore[type-arg]
    deadline = monotonic() + OPENOCD_STARTUP_TIMEOUT_S

    while monotonic() < deadline:
        if openocd.poll() is not None:
            return False

        try:
            with socket.create_connection(
                (EMBEDDED_GDB_HOST, EMBEDDED_GDB_PORT),
                timeout=OPENOCD_STARTUP_POLL_INTERVAL_S,
            ):
                return True
        except OSError:
            continue

    return False


class _pwrforgeDebug:
    SUPPORTED_TARGETS = ["x86", "stm32", "esp32", "atsam"]
    OPENOCD_SUPPORTED_TARGETS = ["stm32", "esp32", "atsam"]

    def __init__(
        self,
        config: Config,
        bin_path: Optional[Path],
        target: Optional[pwrforgeTarget],
        command_name: str = "debug",
        require_bin: bool = True,
        supported_targets: Optional[List[str]] = None,
    ):
        self._config = config
        self._target = get_target_or_default(config, target)
        self._command_name = command_name
        self._supported_targets = supported_targets or self.SUPPORTED_TARGETS
        self._bin_path: Optional[Path] = None

        logger.info("Running pwrforge %s for %s target", self._command_name, self._target.id)
        if self._target.id not in self._supported_targets:
            logger.error("%s currently not supported for %s", self._command_name.capitalize(), self._target.id)
            logger.info("pwrforge currently supports %s for %s", self._command_name, self._supported_targets)
            sys.exit(1)

        if require_bin:
            self._bin_path = bin_path or config.project_root / self._target.get_bin_path(config.project.name.lower())
            if not self._bin_path.exists():
                logger.error("Binary %s does not exist", self._bin_path)
                logger.info("Did you run pwrforge build --profile Debug --target %s?", self._target.id)
                sys.exit(1)

    def run_debugger(self) -> None:
        """Run debugger for target"""
        if self._target.id == pwrforgeTarget.x86:
            self.run_gdb()
            return

        openocd_log_path = self._config.project_root / OPENOCD_LOG_PATH
        openocd_log_path.parent.mkdir(parents=True, exist_ok=True)

        with open(openocd_log_path, "w", encoding="utf-8") as openocd_log:
            openocd = subprocess.Popen(  # pylint: disable=consider-using-with
                self.get_openocd_command(),
                stdout=openocd_log,
                stderr=subprocess.STDOUT,
            )
            try:
                if not _wait_for_gdb_server(openocd):
                    if openocd.poll() is not None:
                        logger.error("OpenOCD exited before the GDB server became ready.")
                    else:
                        logger.error(
                            "Timed out waiting for OpenOCD GDB server on %s:%d.",
                            EMBEDDED_GDB_HOST,
                            EMBEDDED_GDB_PORT,
                        )
                    logger.info("See %s for OpenOCD output.", openocd_log_path)
                    sys.exit(1)

                self.run_gdb()
            finally:
                if openocd is not None:
                    if platform.system() == "Windows":
                        openocd.terminate()
                    else:
                        os.system("pkill -9 -P " + str(openocd.pid))

    def run_gdb(self) -> None:
        _run_interactive_command(self.get_gdb_command(), check=False)

    def run_openocd(self) -> None:
        _run_interactive_command(self.get_openocd_command(), check=False)

    def get_gdb_command(self) -> list[str]:
        if self._target.id == pwrforgeTarget.x86:
            return ["gdb", *GDB_COMMON_SETTINGS, str(self._require_bin_path())]

        return [
            self._get_gdb_bin(),
            *GDB_COMMON_SETTINGS,
            str(self._require_bin_path()),
            EMEDDED_GDB_SETTINGS,
        ]

    def get_openocd_command(self) -> list[str]:
        return [str(find_program_path("openocd")), *self._get_openocd_args()]

    def _get_gdb_bin(self) -> str:
        if self._target.id in [pwrforgeTarget.stm32, pwrforgeTarget.atsam]:
            return "gdb-multiarch"
        if self._target.id == pwrforgeTarget.esp32:
            return "xtensa-esp32-elf-gdb"
        return "gdb"

    def _get_openocd_args(self) -> list[str]:
        if self._target.id in [pwrforgeTarget.stm32, pwrforgeTarget.atsam]:
            return ["-f", ".devcontainer/openocd-script.cfg"]
        if self._target.id == pwrforgeTarget.esp32:
            return [
                "-f",
                "interface/ftdi/esp32_devkitj_v1.cfg",
                "-f",
                "board/esp-wroom-32.cfg",
            ]
        raise RuntimeError(f"OpenOCD not supported for target {self._target.id}")

    def _require_bin_path(self) -> Path:
        if self._bin_path is None:
            raise RuntimeError(f"Binary path not initialized for command {self._command_name}")
        return self._bin_path


def pwrforge_debug(
    bin_path: Optional[Path],
    target: Optional[pwrforgeTarget],
    openocd_only: bool = False,
    gdb_only: bool = False,
) -> None:
    config = prepare_config()
    if openocd_only and gdb_only:
        logger.error("Options --openocd and --gdb are mutually exclusive.")
        sys.exit(1)

    if openocd_only:
        debug = _pwrforgeDebug(
            config,
            None,
            target,
            command_name="debug --openocd",
            require_bin=False,
            supported_targets=_pwrforgeDebug.OPENOCD_SUPPORTED_TARGETS,
        )
        debug.run_openocd()
        return

    if gdb_only:
        debug = _pwrforgeDebug(
            config,
            bin_path,
            target,
            command_name="debug --gdb",
        )
        debug.run_gdb()
        return

    debug = _pwrforgeDebug(config, bin_path, target)
    debug.run_debugger()
