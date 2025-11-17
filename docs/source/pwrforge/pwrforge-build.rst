.. _pwrforge_build:

Build C/C++ project: build
---------------------------
.. image:: ../_static/pwrforge_clean_build_docker.svg
   :alt: pwrforge clean and build example
   :align: center

Usage
^^^^^
::

    pwrforge build [OPTIONS]

Description
^^^^^^^^^^^
Compile sources.

Options
^^^^^^^
::

-p, --profile PROFILE           [default: Debug]

This option specifies the profile. PROFILE can be Debug, Release, RelWIthDebugInfo, MinSizeRel or custom profile specified in toml.
Custom user profiles should be added under the ``[profile.(custom tag)]`` section in pwrforge.toml file.

If this option is not used, then the default profile is Debug.

::

-t, --target [atsam|esp32|stm32|x86]

Build project for specified target. Releavant only for multitarget projects.


::

-a, --all                      [default: False]

Build project for all targets.


::

-B, --base-dir DIRECTORY

Specify the base project path. Allows running pwrforge commands from any directory.

Example 1
^^^^^^^^^
Command:
::

    pwrforge build

**Effects:**

It will use conan to download all dependencies and build the project in build/Debug dir

NOTES: This command has the same effects as pwrforge build --profile Debug

Example 2
^^^^^^^^^
Command:
::

    pwrforge build --profile Release

**Effects:**

It will use conan to download all dependencies and build the project in build/Release dir


Note 1
^^^^^^^
pwrforge by default defines four profiles:

- Debug
- Release
- RelWithDebugInfo
- MinSizeRel

The user can define their own profiles.
