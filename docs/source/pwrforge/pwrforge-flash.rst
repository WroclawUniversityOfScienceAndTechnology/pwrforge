.. _pwrforge_flash:

Flash using generated C/C++ project
-----------------------------------

Usage
^^^^^

::

    pwrforge flash [OPTIONS]

Description
^^^^^^^^^^^

Flash what is available to be flashed. This option is the default if no other options are specified.

For projects configured with ``build-env = "docker"``, ``pwrforge flash`` runs natively on Windows and macOS
instead of re-entering Docker, because Docker Desktop does not expose serial/debug USB devices reliably on those
hosts. Linux keeps the existing Docker execution path.

Options
^^^^^^^

::

-p, --profile PROFILE           [default: Debug]


Flash base on previously built profile  [default: Debug]

::

--port DEVICE

(esp32 only) port where the target device of the command is connected to, e.g. /dev/ttyUSB0

::

-t, --target [atsam|esp32|stm32|x86]

Flash specified target. Releavant only for multitarget projects.

::

--app           [default: false]

Flash app only. Releavant only for esp32 projects.

::

--fs           [default: false]

Flash filesystem only. Relevant only for esp32 projects

::

--no-erase           [default: false]

Don't erase target memory. Relevant only for stm32 projects

::

--bank

Switch between app flash banks. If the bank is not defined then no switch action will be done. Relevant only for stm32 projects
Example usage:  pwrforge flash --bank 0

::

-B, --base-dir DIRECTORY

Specify the base project path. Allows running pwrforge commands from any directory.
