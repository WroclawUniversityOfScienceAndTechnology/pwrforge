import subprocess
from pathlib import Path

from pwrforge.file_generators.base_gen import write_template
from tests.ut.utils import get_test_project_config


def test_x86_cmake_defaults_to_the_project_target_and_generates_elf(tmp_path: Path) -> None:
    config = get_test_project_config("x86")
    config.project_root = tmp_path

    write_template(tmp_path / "CMakeLists.txt", "CMakeLists.txt.j2", {"config": config})
    write_template(tmp_path / "src/CMakeLists.txt", "cpp/cmake-src-x86.j2", {"config": config})
    write_template(
        tmp_path / "src/testproject.cpp",
        "cpp/main.cpp.j2",
        {"project": config.project, "bin_name": "testproject"},
    )

    root_cmake = (tmp_path / "CMakeLists.txt").read_text(encoding="utf-8")
    source_cmake = (tmp_path / "src/CMakeLists.txt").read_text(encoding="utf-8")

    assert 'set(ENV{pwrforge_BUILD_TARGET} "x86")' in root_cmake
    assert 'set_target_properties(${PROJECT_NAME} PROPERTIES SUFFIX ".elf")' in source_cmake
    assert config.project.default_target.get_bin_path("testproject") == "build/x86/Debug/bin/testproject.elf"

    subprocess.run(["cmake", "-S", str(tmp_path), "-B", str(tmp_path / "build")], check=True)
    subprocess.run(["cmake", "--build", str(tmp_path / "build")], check=True)

    assert (tmp_path / "build/bin/testproject.elf").is_file()
