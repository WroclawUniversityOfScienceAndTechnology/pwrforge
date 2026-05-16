import os
from fnmatch import fnmatch
from pathlib import Path
from typing import List, Set

import pytest
from pytest_subprocess import FakeProcess

from pwrforge.commands.docker import get_docker_compose_command
from pwrforge.commands.new import pwrforge_new
from pwrforge.commands.update import pwrforge_update
from pwrforge.config import pwrforgeTarget
from pwrforge.global_values import PWRFORGE_DEFAULT_CONFIG_FILE
from pwrforge.utils.conan_utils import DEFAULT_PROFILES
from tests.ut.utils import get_all_files_recursively

TEST_PROJECT_NAME = "test_project"


def get_expected_files(target: List[pwrforgeTarget]) -> Set[str]:
    wheel_filename = ".devcontainer/pwrforge-*-py3-none-any.whl"

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
        wheel_filename,
    }
    source_extension = "c" if pwrforgeTarget.pic18 in target else "cpp"
    project_files.add(f"src/test_project.{source_extension}")

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

    if pwrforgeTarget.pic18 in target:
        project_files.add("config/conan/profiles/pic18_sdcc_toolchain.cmake")

    return project_files


def assert_files_match(all_files: Set[str], expected_files: Set[str]) -> None:
    wildcard_expected = {f for f in expected_files if "*" in f or "?" in f or "[" in f}
    exact_expected = expected_files - wildcard_expected

    unmatched_actual = all_files - exact_expected

    for pattern in wildcard_expected:
        matches = {f for f in all_files if fnmatch(f, pattern)}
        assert matches, f"Missing file matching pattern: {pattern}"
        unmatched_actual -= matches

    assert unmatched_actual == set()
    assert exact_expected - all_files == set()


@pytest.mark.parametrize(
    "target",
    [pwrforgeTarget.x86, pwrforgeTarget.esp32, pwrforgeTarget.stm32, pwrforgeTarget.atsam, pwrforgeTarget.pic18],
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
    assert_files_match(all_files, expected_files)


def test_update_multitarget_project_content(tmp_path: Path) -> None:
    os.chdir(tmp_path)
    targets = [
        pwrforgeTarget.x86,
        pwrforgeTarget.esp32,
        pwrforgeTarget.stm32,
        pwrforgeTarget.atsam,
        pwrforgeTarget.pic18,
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
    assert_files_match(all_files, expected_files)


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


def test_update_project_with_docker_adds_host_groups(
    tmp_path: Path, fp: FakeProcess, monkeypatch: pytest.MonkeyPatch
) -> None:
    os.chdir(tmp_path)
    pwrforge_new(TEST_PROJECT_NAME, None, None, [pwrforgeTarget.x86], True, False, [])
    os.chdir(TEST_PROJECT_NAME)
    called_subprocess_cmd = get_docker_compose_command()
    called_subprocess_cmd.extend(["pull"])
    fp.register(called_subprocess_cmd)
    fp.register(["conan", "profile", "list"])
    fp.register(["conan", "profile", "detect"])
    fp.register(["pip", "show", "pwrforge"])
    monkeypatch.setattr("pwrforge.file_generators.docker_gen.get_host_supplementary_group_ids", lambda: ["20", "46"])

    pwrforge_update(Path(PWRFORGE_DEFAULT_CONFIG_FILE))

    docker_compose_text = Path(".devcontainer/docker-compose.yaml").read_text(encoding="utf-8")
    dockerfile_text = Path(".devcontainer/Dockerfile").read_text(encoding="utf-8")
    env_text = Path(".devcontainer/.env").read_text(encoding="utf-8")
    devcontainer_text = Path(".devcontainer/devcontainer.json").read_text(encoding="utf-8")

    assert "group_add:" in docker_compose_text
    assert '      - "20"' in docker_compose_text
    assert '      - "46"' in docker_compose_text
    assert "USER_NAME:" not in docker_compose_text
    assert "USER_PASSWORD:" not in docker_compose_text
    assert "ARG DEV_USER=ubuntu" in dockerfile_text
    assert 'echo "$DEV_USER ALL=(ALL) NOPASSWD:ALL"' in dockerfile_text
    assert 'groupadd -g "20" "hostgrp_20"' in dockerfile_text
    assert 'groupadd -g "46" "hostgrp_46"' in dockerfile_text
    assert "ARG USER_NAME" not in dockerfile_text
    assert "ARG USER_PASSWORD" not in dockerfile_text
    assert "USER_NAME=" not in env_text
    assert "USER_PASSWORD=" not in env_text
    assert "UID_NUMBER=" in env_text
    assert "GID_NUMBER=" in env_text
    assert '"remoteUser": "ubuntu"' in devcontainer_text


def test_update_project_stm32_uses_named_volume_cache(tmp_path: Path, fp: FakeProcess) -> None:
    os.chdir(tmp_path)
    pwrforge_new(TEST_PROJECT_NAME, None, None, [pwrforgeTarget.stm32], True, False, [])
    os.chdir(TEST_PROJECT_NAME)
    called_subprocess_cmd = get_docker_compose_command()
    called_subprocess_cmd.extend(["pull"])
    fp.register(called_subprocess_cmd)
    fp.register(["conan", "profile", "list"])
    fp.register(["conan", "profile", "detect"])
    fp.register(["pip", "show", "pwrforge"])

    pwrforge_update(Path(PWRFORGE_DEFAULT_CONFIG_FILE))

    docker_compose_text = Path(".devcontainer/docker-compose.yaml").read_text(encoding="utf-8")
    dockerfile_text = Path(".devcontainer/Dockerfile").read_text(encoding="utf-8")
    openocd_script_text = Path(".devcontainer/openocd-script.cfg").read_text(encoding="utf-8")
    vscode_tasks_text = Path(".vscode/tasks.json").read_text(encoding="utf-8")
    toolchain_text = Path("config/conan/profiles/stm32_gcc_toolchain.cmake").read_text(encoding="utf-8")

    assert "pwrforge_stm32cube_cache:/home/ubuntu/.cache/pwrforge/stm32cube" in docker_compose_text
    assert "name: pwrforge_stm32cube_cache" in docker_compose_text
    assert '      - "3333:3333"' in docker_compose_text
    assert '      - "4444:4444"' in docker_compose_text
    assert '      - "6666:6666"' in docker_compose_text
    assert "source [find interface/stlink.cfg]" in openocd_script_text
    assert '"command": "pwrforge"' in vscode_tasks_text
    assert '"debug"' in vscode_tasks_text
    assert '"--openocd"' in vscode_tasks_text
    assert '"command": "pkill"' in vscode_tasks_text
    assert "https://github.com/STMicroelectronics/STM32CubeL4.git" in dockerfile_text
    assert "/opt/pwrforge-cache/stm32cube/stm32cubel4-src" in dockerfile_text
    assert "install -d -m 0775 /home/ubuntu/.cache/pwrforge/stm32cube" in dockerfile_text
    assert (
        "chown -R ${DEV_USER}:$GID_NUMBER /home/ubuntu/.cache/pwrforge/stm32cube /opt/pwrforge-cache/stm32cube"
        in dockerfile_text
    )
    assert "ENV HOME=/home/${DEV_USER}" in dockerfile_text
    assert 'set(FETCHCONTENT_BASE_DIR "$ENV{HOME}/.cache/pwrforge/stm32cube")' in toolchain_text
    assert (
        'set(PWRFORGE_STM32_CUBE_SOURCE_DIR "${FETCHCONTENT_BASE_DIR}/stm32cube${STM32_FAMILY_LOWER}-src")'
        in toolchain_text
    )
    assert (
        'set(PWRFORGE_STM32_CUBE_IMAGE_SOURCE_DIR "/opt/pwrforge-cache/stm32cube/stm32cube${STM32_FAMILY_LOWER}-src")'
        in toolchain_text
    )
    assert 'set("STM32_CUBE_${STM32_FAMILY}_PATH" "${PWRFORGE_STM32_CUBE_SOURCE_DIR}")' in toolchain_text
    assert (
        'message(STATUS "Using preloaded stm32 cube for stm32 ${STM32_FAMILY} '
        'family from ${PWRFORGE_STM32_CUBE_SOURCE_DIR}")' in toolchain_text
    )
    assert 'set("STM32_CUBE_${STM32_FAMILY}_PATH" "${PWRFORGE_STM32_CUBE_IMAGE_SOURCE_DIR}")' in toolchain_text
    assert (
        'message(STATUS "Using image stm32 cube for stm32 ${STM32_FAMILY} '
        'family from ${PWRFORGE_STM32_CUBE_IMAGE_SOURCE_DIR}")' in toolchain_text
    )
    assert 'set(FETCHCONTENT_BASE_DIR "$ENV{pwrforge_PROJECT_ROOT}/build/.cmake_fetch_cache")' in toolchain_text
    assert 'set(FETCHCONTENT_BASE_DIR "${CMAKE_SOURCE_DIR}/build/.cmake_fetch_cache")' in toolchain_text


def test_update_project_pic18_generates_sdcc_environment(tmp_path: Path, fp: FakeProcess) -> None:
    os.chdir(tmp_path)
    pwrforge_new(TEST_PROJECT_NAME, None, None, [pwrforgeTarget.pic18], True, False, [])
    os.chdir(TEST_PROJECT_NAME)
    called_subprocess_cmd = get_docker_compose_command()
    called_subprocess_cmd.extend(["pull"])
    fp.register(called_subprocess_cmd)
    fp.register(["conan", "profile", "list"])
    fp.register(["conan", "profile", "detect"])
    fp.register(["pip", "show", "pwrforge"])

    pwrforge_update(Path(PWRFORGE_DEFAULT_CONFIG_FILE))

    dockerfile_text = Path(".devcontainer/Dockerfile").read_text(encoding="utf-8")
    profile_text = Path("config/conan/profiles/pic18_Debug").read_text(encoding="utf-8")
    toolchain_text = Path("config/conan/profiles/pic18_sdcc_toolchain.cmake").read_text(encoding="utf-8")
    source_cmake_text = Path("src/CMakeLists.txt").read_text(encoding="utf-8")
    root_cmake_text = Path("CMakeLists.txt").read_text(encoding="utf-8")

    assert "FROM cpp AS pic18" in dockerfile_text
    assert "sdcc sdcc-libraries gputils" in dockerfile_text
    assert "pwrforge_BUILD_TARGET=pic18" in profile_text
    assert "PIC18_CHIP=pic18f4580" in profile_text
    assert "PIC18_SDCC_PROCESSOR=18f4580" in profile_text
    assert 'pic18_sdcc_toolchain.cmake")' in profile_text
    assert "find_program(PIC18_SDCC sdcc REQUIRED)" in toolchain_text
    assert "set(CMAKE_EXECUTABLE_SUFFIX \".hex\")" in toolchain_text
    assert "set(PIC18_SDCC_FLAGS -mpic16 -p${PIC18_SDCC_PROCESSOR})" in toolchain_text
    assert "test_project.c" in source_cmake_text
    assert "set(pwrforge_PROJECT_LANGUAGES C)" in root_cmake_text


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
