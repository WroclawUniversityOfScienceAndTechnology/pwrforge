import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from typer import Argument, Option, Typer

from pwrforge.commands.build import pwrforge_build
from pwrforge.commands.check import pwrforge_check
from pwrforge.commands.clean import pwrforge_clean
from pwrforge.commands.debug import pwrforge_debug
from pwrforge.commands.doc import pwrforge_doc
from pwrforge.commands.docker import (
    pwrforge_docker_build,
    pwrforge_docker_exec,
    pwrforge_docker_run,
)
from pwrforge.commands.fix import pwrforge_fix
from pwrforge.commands.flash import pwrforge_flash
from pwrforge.commands.gen import pwrforge_gen
from pwrforge.commands.license_check import pwrforge_license_check
from pwrforge.commands.monitor import pwrforge_monitor
from pwrforge.commands.new import pwrforge_new
from pwrforge.commands.publish import pwrforge_publish
from pwrforge.commands.run import pwrforge_run
from pwrforge.commands.test import pwrforge_test
from pwrforge.commands.update import pwrforge_update
from pwrforge.commands.version import pwrforge_version
from pwrforge.config import pwrforgeTarget
from pwrforge.global_values import DESCRIPTION, PWRFORGE_DEFAULT_CONFIG_FILE
from pwrforge.logger import get_logger
from pwrforge.utils.path_utils import get_config_file_path

logger = get_logger()

###############################################################################


cli = Typer(context_settings={"help_option_names": ["-h", "--help"]}, help=DESCRIPTION)


BASE_DIR_OPTION = Option(
    None,
    "--base-dir",
    "-B",
    exists=True,
    file_okay=False,
    help="Base directory of the project",
)


###############################################################################


@cli.command()
def build(
    profile: str = Option("Debug", "-p", "--profile", metavar="PROFILE"),
    target: Optional[pwrforgeTarget] = Option(
        None,
        "-t",
        "--target",
        help="Target device. Defaults to first one from toml if not specified.",
    ),
    all_targets: bool = Option(False, "-a", "--all", help="Build all targets."),
    base_dir: Optional[Path] = BASE_DIR_OPTION,
) -> None:
    """Compile sources."""
    if base_dir:
        os.chdir(base_dir)
    pwrforge_build(profile, target, all_targets)


###############################################################################


@cli.command()
def check(
    clang_format: bool = Option(False, "--clang-format", help="Run clang-format."),
    clang_tidy: bool = Option(False, "--clang-tidy", help="Run clang-tidy."),
    copy_right: bool = Option(False, "--copyright", help="Run copyright check."),
    cppcheck: bool = Option(False, "--cppcheck", help="Run cppcheck."),
    cyclomatic: bool = Option(False, "--cyclomatic", help="Run python-lizard."),
    pragma: bool = Option(False, "--pragma", help="Run pragma check."),
    todo: bool = Option(False, "--todo", help="Run TODO check."),
    silent: bool = Option(False, "--silent", "-s", help="Show less output."),
    base_dir: Optional[Path] = BASE_DIR_OPTION,
) -> None:
    """Check source code in directory `src`."""
    if base_dir:
        os.chdir(base_dir)
    pwrforge_check(
        clang_format,
        clang_tidy,
        copy_right,
        cppcheck,
        cyclomatic,
        pragma,
        todo,
        verbose=not silent,
    )


###############################################################################


@cli.command()
def clean(base_dir: Optional[Path] = BASE_DIR_OPTION) -> None:
    """Remove directory `build`."""
    if base_dir:
        os.chdir(base_dir)
    pwrforge_clean()


###############################################################################


@cli.command()
def debug(
    bin_path: Optional[Path] = Option(
        None,
        "--bin",
        "-b",
        exists=True,
        dir_okay=False,
        resolve_path=True,
        help="Path to bin file",
    ),
    target: Optional[pwrforgeTarget] = Option(
        None,
        "-t",
        "--target",
        help="Target device. Defaults to first one from toml if not specified.",
    ),
    base_dir: Optional[Path] = BASE_DIR_OPTION,
) -> None:
    """Use gdb cli to debug"""
    if base_dir:
        os.chdir(base_dir)
    pwrforge_debug(bin_path, target)


###############################################################################


@cli.command()
def doc(
    open_doc: bool = Option(False, "--open", help="Open html documentation"),
    base_dir: Optional[Path] = BASE_DIR_OPTION,
) -> None:
    """Create project documentation"""
    if base_dir:
        os.chdir(base_dir)
    pwrforge_doc(open_doc)


###############################################################################


docker = Typer(help="Manage the docker environment for the project")


@docker.command("build", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def docker_build(docker_opts: List[str] = Argument(None), base_dir: Optional[Path] = BASE_DIR_OPTION) -> None:
    """Build docker layers for this project depending on the target"""
    if base_dir:
        os.chdir(base_dir)
    pwrforge_docker_build(docker_opts)


@docker.command("run", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def docker_run(
    command: str = Option(
        "bash",
        "-c",
        "--command",
        metavar="COMMAND",
        help="Select command to be used with docker run.",
    ),
    base_dir: Optional[Path] = BASE_DIR_OPTION,
    docker_opts: List[str] = Argument(None),
) -> None:
    """Run project in docker environment"""
    if base_dir:
        os.chdir(base_dir)
    pwrforge_docker_run(docker_opts=docker_opts, command=command)


@docker.command("exec", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def docker_exec(base_dir: Optional[Path] = BASE_DIR_OPTION, docker_opts: List[str] = Argument(None)) -> None:
    """Attach to existing docker environment"""
    if base_dir:
        os.chdir(base_dir)
    pwrforge_docker_exec(docker_opts)


cli.add_typer(docker, name="docker")


###############################################################################


@cli.command()
def fix(
    clang_format: bool = Option(False, "--clang-format", help="Fix clang-format violations"),
    copy_right: bool = Option(False, "--copyright", help="Fix copyrights violations"),
    pragma: bool = Option(False, "--pragma", help="Fix pragma violations"),
    base_dir: Optional[Path] = BASE_DIR_OPTION,
) -> None:
    """Fix violations reported by command `check`."""
    if base_dir:
        os.chdir(base_dir)
    pwrforge_fix(pragma, copy_right, clang_format)


###############################################################################


@cli.command()
def flash(
    flash_profile: str = Option(
        "Debug",
        "-p",
        "--profile",
        metavar="PROFILE",
        help="Flash base on previously built profile",
    ),
    port: Optional[str] = Option(
        None,
        help="(esp32 only) port where the target device of the command is" " connected to, e.g. /dev/ttyUSB0",
    ),
    target: Optional[pwrforgeTarget] = Option(
        None,
        "-t",
        "--target",
        help="Target device. Defaults to first one from toml if not specified.",
    ),
    app: bool = Option(False, "--app", help="Flash app only"),
    file_system: bool = Option(False, "--fs", help="Flash filesystem only"),
    no_erase: bool = Option(False, help="(stm32 only) Don't erase target memory"),
    bank: Optional[int] = Option(
        None,
        "--bank",
        help="(esp32 only) Provide app flasg bank number for chosen target e.g. --bank 0",
    ),
    base_dir: Optional[Path] = BASE_DIR_OPTION,
) -> None:
    """Flash the target."""
    if base_dir:
        os.chdir(base_dir)
    pwrforge_flash(flash_profile, port, target, app, file_system, not no_erase, bank)


###############################################################################


@cli.command()
def monitor(
    port: str = Option(
        ...,
        "-p",
        "--port",
        help="port where the serial monitor will be run" " connected to, e.g. /dev/ttyUSB0",
    ),
    baudrate: Optional[int] = Option(
        None,
        "-b",
        "--baudrate",
        help="baudrate, default is 115200",
    ),
    base_dir: Optional[Path] = BASE_DIR_OPTION,
) -> None:
    """Monitor the target over serial port"""
    if base_dir:
        os.chdir(base_dir)
    pwrforge_monitor(port, baudrate)


###############################################################################
@cli.command()
def gen(
    profile: str = Option("Debug", "--profile", "-p"),
    gen_ut: Optional[Path] = Option(
        None,
        "--unit-test",
        "-u",
        exists=True,
        resolve_path=True,
        help="Generate unit test for chosen file or all headers in directory",
    ),
    gen_mock: Optional[Path] = Option(
        None,
        "--mock",
        "-m",
        exists=True,
        dir_okay=False,
        resolve_path=True,
        help="Generate mock of chosen file",
    ),
    certs: Optional[str] = Option(
        None,
        "--certs",
        "-c",
        metavar="<DEVICE ID>",
        help="Generate cert files for azure based on device ID.",
    ),
    certs_mode: Optional[str] = Option(
        None,
        "--type",
        "-t",
        metavar="[all, device]",
        help="Mode for generating certificates.",
    ),
    certs_input: Optional[Path] = Option(
        None,
        "--in",
        "-i",
        dir_okay=True,
        resolve_path=True,
        help="Directory with root and intermediate certificates.",
    ),
    certs_passwd: Optional[str] = Option(
        None,
        "--passwd",
        "-p",
        metavar="<PASSWORD>",
        help="Password to be set for generated certificates",
    ),
    file_system: bool = Option(False, "--fs", "-f", help="Build the filesystem, base on spiffs dir content."),
    single_bin: bool = Option(False, "--bin", "-b", help="Generate single binary image."),
    base_dir: Optional[Path] = BASE_DIR_OPTION,
) -> None:
    """Manage the auto file generator"""
    if base_dir:
        os.chdir(base_dir)
    if gen_ut is None and gen_mock is None and certs is None and not (file_system or single_bin):
        logger.warning("Please add one of the following options to the command:")
        logger.warning("--unit-test\n--mock\n--certs\n--fs\n--bin")
        sys.exit(1)

    pwrforge_gen(
        profile,
        gen_ut,
        gen_mock,
        certs,
        certs_mode,
        certs_input,
        certs_passwd,
        file_system,
        single_bin,
    )


###############################################################################


@cli.command()
def new(
    project_name: str,
    bin_name: Optional[str] = Option(
        None,
        "--bin",
        help="Create binary target template.",
        metavar="BIN_NAME",
        prompt=True,
        prompt_required=False,
    ),
    lib_name: Optional[str] = Option(
        None,
        "--lib",
        help="Create library target template.",
        metavar="LIB_NAME",
        prompt=True,
        prompt_required=False,
    ),
    targets: List[pwrforgeTarget] = Option([], "-t", "--target", help="Specify targets for a project."),
    chip: List[str] = Option(
        [],
        "-c",
        "--chip",
        help="Specify full chip label for a target (Uses default if not specified)",
        metavar="[stm32...|atsam...|esp32...]",
        prompt=True,
        prompt_required=False,
    ),
    create_docker: bool = Option(True, "-d/-nd", "--docker/--no-docker", help="Initialize docker environment."),
    git: bool = Option(True, "--git/--no-git", help="Initialize git repository."),
    base_dir: Optional[Path] = BASE_DIR_OPTION,
) -> None:
    """Create new project template."""
    if base_dir:
        os.chdir(base_dir)

    pwrforge_new(
        project_name,
        bin_name,
        lib_name,
        targets,
        create_docker,
        git,
        chip,
    )
    project_dir = Path(project_name).absolute()
    pwrforge_update(project_dir / PWRFORGE_DEFAULT_CONFIG_FILE)
    jump_to_project_shell(project_dir)


def jump_to_project_shell(project_dir: Path) -> None:
    """
    Open an interactive subshell in the current project directory.
    This is the closest possible behavior to "cd" from a CLI command.
    """
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        logger.info("Project is ready in: %s", project_dir)
        logger.info("Run `cd %s` to enter it.", project_dir)
        return

    shell = os.environ.get("SHELL")
    if not shell:
        logger.info("Project is ready in: %s", project_dir)
        logger.info("SHELL is not set. Run `cd %s` to enter it.", project_dir)
        return

    logger.info("Entering project shell in %s", project_dir)
    subprocess.call([shell], cwd=project_dir)


###############################################################################


@cli.command()
def publish(
    repo: str = Option("", "-r", "--repo", metavar="CONAN_REPO_NAME", help="Repo name"),
    profile: str = Option("Release", "-p", "--profile", metavar="PROFILE"),
    base_dir: Optional[Path] = BASE_DIR_OPTION,
) -> None:
    """Upload conan pkg to repo"""
    if base_dir:
        os.chdir(base_dir)
    pwrforge_publish(repo, profile)


###############################################################################


@cli.command()
def run(
    bin_path: Optional[Path] = Option(
        None,
        "--bin",
        "-b",
        exists=True,
        dir_okay=False,
        resolve_path=True,
        help="Path to bin file",
    ),
    profile: str = Option("Debug", "-p", "--profile", metavar="PROFILE"),
    prebuild: bool = Option(False, "--build", help="Call pwrforge build before run"),
    force_docker: bool = Option(False, "--docker", help="Force running command in docker (interactive mode)"),
    force_native: bool = Option(False, "--native", help="Force running command in native environment"),
    bin_params: List[str] = Argument(None),
    base_dir: Optional[Path] = BASE_DIR_OPTION,
) -> None:
    """Run project bin file"""
    if base_dir:
        os.chdir(base_dir)
    pwrforge_run(bin_path, profile, bin_params, prebuild, force_docker, force_native)


###############################################################################


@cli.command()
def test(
    verbose: bool = Option(False, "--verbose", "-v", help="Verbose mode."),
    profile: str = Option("Debug", "-p", "--profile", metavar="PROFILE", help="CMake profile to use"),
    detailed_coverage: bool = Option(False, help="Generate detailed coverage HTML files"),
    base_dir: Optional[Path] = BASE_DIR_OPTION,
) -> None:
    """Compile and run all tests in directory `test`."""
    if base_dir:
        os.chdir(base_dir)
    pwrforge_test(verbose, profile, detailed_coverage)


###############################################################################


@cli.command()
def update(
    config_file_path: Optional[Path] = Option(
        None,
        "-c",
        "--config-file",
        exists=True,
        dir_okay=False,
        resolve_path=True,
        help="Path to .toml configuration file.",
    ),
    base_dir: Optional[Path] = BASE_DIR_OPTION,
) -> None:
    """Read config file and update project files"""
    if base_dir:
        os.chdir(base_dir)
    if config_file_path is None:
        config_file_path = get_config_file_path(PWRFORGE_DEFAULT_CONFIG_FILE)
        if not config_file_path:
            logger.error("Config file not found.")
            sys.exit(1)
    pwrforge_update(config_file_path)


###############################################################################


@cli.command()
def license_check(
    path: Optional[Path] = Option(
        None,
        "--path",
        "-p",
        exists=True,
        resolve_path=True,
        help="Optional path to scan (default: src/ or main/).",
    ),
    base_dir: Optional[Path] = BASE_DIR_OPTION,
) -> None:
    """Check project licenses against license policy."""
    if base_dir:
        os.chdir(base_dir)

    pwrforge_license_check(path)


###############################################################################


@cli.command()
def version() -> None:
    """Get pwrforge version"""
    pwrforge_version()


###############################################################################

if __name__ == "__main__":
    cli()
