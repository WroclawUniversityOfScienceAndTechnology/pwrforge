import os
from pathlib import Path
from typing import List, Set

import pytest
from pytest_subprocess import FakeProcess

from pwrforge import __version__
from pwrforge.commands.docker import get_docker_compose_command
from pwrforge.commands.new import pwrforge_new
from pwrforge.commands.update import pwrforge_update
from pwrforge.config import pwrforgeTarget
from pwrforge.global_values import PWRFORGE_DEFAULT_CONFIG_FILE
from pwrforge.utils.conan_utils import DEFAULT_PROFILES
from tests.ut.utils import get_all_files_recursively

TEST_PROJECT_NAME = "test_project"


def get_expected_files(target: List[pwrforgeTarget]) -> Set[str]:
    wheel_filename = f".devcontainer/pwrforge-{__version__}-py3-none-any.whl"

    project_files = {
        "LICENSE",
        "CMakeLists.txt",
        "pwrforge.toml",
        "pwrforge.lock",
        ".clang-tidy",
        "conanfile.py",
        ".clang-format",
        "README.md",
        ".gitignore",
        ".gitlab-ci.yml",
        "setup.sh",
        "tests/CMakeLists.txt",
        "tests/conanfile.py",
        "tests/mocks/CMakeLists.txt",
        "tests/mocks/static_mock/CMakeLists.txt",
        "tests/mocks/static_mock/static_mock.h",
        "tests/it/CMakeLists.txt",
        "tests/ut/CMakeLists.txt",
        ".vscode/tasks.json",
        ".devcontainer/.env",
        ".devcontainer/Dockerfile",
        ".devcontainer/.gitlab-ci-custom.yml",
        ".devcontainer/docker-compose.yaml",
        ".devcontainer/devcontainer.json",
        ".devcontainer/Dockerfile-custom",
        ".devcontainer/requirements.txt",
        "src/CMakeLists.txt",
        "src/test_project.cpp",
        wheel_filename,
    }

    for t in target:
        if len(target) > 1:
            project_files.add(f"src/{t.value}-src.cmake")
        for profile in DEFAULT_PROFILES:
            project_files.add(f"config/conan/profiles/{t.value}_{profile}")

    if pwrforgeTarget.atsam in target:
        project_files.update(
            {
                ".devcontainer/openocd-script.cfg",
                "config/conan/profiles/arm_gcc_toolchain.cmake",
            }
        )

    if pwrforgeTarget.esp32 in target:
        project_files.update({"version.txt", "partitions.csv"})

    if pwrforgeTarget.stm32 in target:
        project_files.update(
            {
                ".devcontainer/openocd-script.cfg",
                "config/conan/profiles/stm32_gcc_toolchain.cmake",
            }
        )

    return project_files


@pytest.mark.parametrize(
    "target",
    [pwrforgeTarget.x86, pwrforgeTarget.esp32, pwrforgeTarget.stm32, pwrforgeTarget.atsam],
)
def test_update_project_content(target: pwrforgeTarget, tmp_path: Path) -> None:
    os.chdir(tmp_path)
    pwrforge_new(
        TEST_PROJECT_NAME,
        bin_name=None,
        lib_name=None,
        targets=[target],
        create_docker=False,
        git=False,
        chip=[],
    )
    os.chdir(TEST_PROJECT_NAME)

    pwrforge_update(Path(PWRFORGE_DEFAULT_CONFIG_FILE))

    all_files = get_all_files_recursively()
    expected_files = get_expected_files([target])
    assert all_files - expected_files == set()
    assert expected_files - all_files == set()


def test_update_multitarget_project_content(tmp_path: Path) -> None:
    os.chdir(tmp_path)
    targets = [
        pwrforgeTarget.x86,
        pwrforgeTarget.esp32,
        pwrforgeTarget.stm32,
        pwrforgeTarget.atsam,
    ]
    pwrforge_new(
        TEST_PROJECT_NAME,
        bin_name=None,
        lib_name=None,
        targets=targets,
        create_docker=False,
        git=False,
        chip=[],
    )
    os.chdir(TEST_PROJECT_NAME)

    pwrforge_update(Path(PWRFORGE_DEFAULT_CONFIG_FILE))

    all_files = get_all_files_recursively()
    expected_files = get_expected_files(targets)
    assert all_files - expected_files == set()
    assert expected_files - all_files == set()


def test_update_project_with_docker(tmp_path: Path, fp: FakeProcess) -> None:
    os.chdir(tmp_path)
    pwrforge_new(TEST_PROJECT_NAME, None, None, [pwrforgeTarget.x86], True, False, [])
    os.chdir(TEST_PROJECT_NAME)
    called_subprocess_cmd = get_docker_compose_command()
    called_subprocess_cmd.extend(["pull"])
    fp.register(called_subprocess_cmd)
    fp.register(["conan", "profile", "list"])
    fp.register(["conan", "profile", "detect"])
    fp.register(["pip", "show", "pwrforge"])

    pwrforge_update(Path(PWRFORGE_DEFAULT_CONFIG_FILE))


def test_update_project_docker_pull_fails(tmp_path: Path, fp: FakeProcess) -> None:
    os.chdir(tmp_path)
    project_name = "test_project_with_docker"
    pwrforge_new(project_name, None, None, [pwrforgeTarget.x86], True, False, [])
    os.chdir(project_name)
    cmd_pull = get_docker_compose_command()
    cmd_pull.extend(["pull"])
    fp.register(cmd_pull, returncode=1)
    cmd_build = get_docker_compose_command()
    fp.register(["conan", "profile", "list"])
    fp.register(["conan", "profile", "detect"])
    fp.register(["pip", "show", "pwrforge"])

    cmd_build.extend(["build"])
    fp.register(cmd_build)
    pwrforge_update(Path(PWRFORGE_DEFAULT_CONFIG_FILE))
