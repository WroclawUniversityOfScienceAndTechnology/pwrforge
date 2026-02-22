"""Run feature depending on provided args"""

import shlex
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from pwrforge.commands.build import pwrforge_build
from pwrforge.commands.docker import pwrforge_docker_run
from pwrforge.config import Target, pwrforgeTarget
from pwrforge.config_utils import prepare_config
from pwrforge.logger import get_logger

logger = get_logger()


def pwrforge_run(  # pylint: disable=too-many-locals,too-many-branches
    bin_path: Optional[Path],
    profile: str,
    params: List[str],
    prebuild: bool,
    force_docker: bool = False,
    force_native: bool = False,
) -> None:
    """
    Run command from CLI

    :param str bin_path: path to bin file
    :param Path profile: build profile name
    :param str params: params for bin file
    :param bool prebuild: build project before running binary
    :param bool force_docker: force running command in docker interactive mode
    :param bool force_native: force running command in native mode
    :return: None
    """
    logger.info('Running binary for "%s" profile', profile)
    # `run` should execute the binary like a native console program.
    # Do not re-run the command in docker, otherwise stdin interaction (e.g. `cin`) is lost.
    config = prepare_config(run_in_docker=False)

    if not config.project.is_x86():
        logger.info("Running non x86 projects on x86 architecture is not implemented yet.")
        sys.exit(1)

    if params is None:
        params = []

    if force_docker and force_native:
        logger.error("Options --docker and --native cannot be used together.")
        sys.exit(1)

    should_run_in_docker = force_docker or (config.project.is_docker_buildenv() and not force_native)
    if should_run_in_docker and not Path("/.dockerenv").exists():
        logger.info("Running `pwrforge run` in docker interactive mode.")
        docker_cmd = ["pwrforge", "run", "--profile", profile]
        if bin_path:
            docker_cmd.extend(["--bin", str(bin_path)])

        if prebuild:
            preferred_cmd = [*docker_cmd, "--build"]
        else:
            preferred_cmd = [*docker_cmd]

        fallback_cmd = docker_cmd
        if params:
            preferred_cmd.extend(["--", *params])
            fallback_cmd.extend(["--", *params])
        # For build=False, preferred and fallback are identical; keep a single command
        # to avoid printing shell fallback noise.
        if preferred_cmd == fallback_cmd:
            docker_shell_cmd = shlex.join(preferred_cmd)
        else:
            docker_shell_cmd = f"{shlex.join(preferred_cmd)} || {shlex.join(fallback_cmd)}"
        pwrforge_docker_run(docker_opts=[], command=docker_shell_cmd)
        return

    if prebuild:
        pwrforge_build(profile, pwrforgeTarget.x86)

    if bin_path:
        bin_file_name = bin_path.name
        bin_file_path = bin_path.parent
        try:
            subprocess.run(
                [f"./{bin_file_name}"] + params,
                cwd=bin_file_path,
                check=True,
                stdin=sys.stdin,
                stdout=sys.stdout,
                stderr=sys.stderr,
            )
        except subprocess.CalledProcessError:
            logger.error(f"Bin file '{bin_path}' not found!")
    else:
        x86_target = Target.get_target_by_id(pwrforgeTarget.x86.value)
        bin_dir = config.project_root / x86_target.get_profile_build_dir(profile) / "bin"
        if bin_dir.is_dir():
            first_bin = next(bin_dir.iterdir())
            # Run project
            try:
                subprocess.run(
                    [f"./{first_bin.name}"] + params,
                    cwd=bin_dir,
                    check=True,
                    stdin=sys.stdin,
                    stdout=sys.stdout,
                    stderr=sys.stderr,
                )
            except subprocess.CalledProcessError:
                logger.error("Unable to run bin file")
        else:
            logger.error(f"Bin dir '{bin_dir}' not found!")
