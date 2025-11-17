.. _pwrforge_new:

Create new C/C++ project : new
------------------------------
.. image:: ../_static/pwrforge_flow_docker.svg
   :alt: pwrforge x86 flow
   :align: center

Usage
^^^^^
::

    pwrforge new [OPTIONS] PROJECT_NAME

Description
^^^^^^^^^^^

Create new project template.

Options
^^^^^^^^
::

    --bin BIN_NAME


::
Creates binary target template project with "[BIN_NAME].cpp" in directory "src".

    --lib LIB_NAME

Creates library target template project file "[LIB_NAME].cpp" in directory "src"
and "[LIB_NAME].h" in directory "include".

::

    -t, --target [atsam|esp32|stm32|x86]           [default: x86]


Chose the target on which you would like to build and manage the project.
 - ESP32 support: Presently following models are supported 'esp32'. Specify chip using --chip or use default (esp32).
 - STM32 support: Specify chip using --chip or use default (STM32L496AG).
 - Atmel SAM series support: Presently pwrforge supports Atmel SAM series. Specify chip using --chip or use default (ATSAML10E16A).


This options can be specified multiple times to create mulittarget project.
e.g. ``pwrforge new -t esp32 --t stm32 -t atsam hello_world``

::

    --chip CHIP_LABEL

Specify chip for a target. Defaults chip will be used if not used.
Defaults:

* esp32: esp32
* stm32: STM32L496AG
* atsam: ATSAML10E16A

::

    -d, --docker / -nd, --no-docker           [default: docker]

Initialize docker environment (default true).

::

    --git / --no-git           [default: git]

Initialize git repository (default true).

::

    -B, --base-dir DIRECTORY

Specify the base project path. Allows running pwrforge commands from any directory.

Notes
^^^^^
Each target must have an unique name. Error if two targets have the same name.

Example 1
^^^^^^^^^
Command:
::

    pwrforge new hello_world --bin foo --lib bar

**Effects:**


Creates project template. The project name is hello_world. Also creates a template for a binary target named foo and creates the template for the library target name bar.
Creates new directory hello_world. This is the root directory of the project.
Enters directory hello_world.
Creates template of README.md.
Creates template of pwrforge.toml.
For a full list of options in pwrforge.toml please look at the description of the command pwrforge update.
The project name in section [project] must be the same as the project name provided to command pwrforge new. In this example project name is hello_world.
Creates directory src.
Creates file src/foo.cpp

::

    int main()
    {
    }

Creates file src/bar.cpp

::

    void bar()
    {
    }

Creates file src/CMakeLists.txt

::

    add_executable(foo foo.cpp)
    add_library(bar STATIC bar.cpp)

Initializes git repository.
