.. _pwrforge_run:

Run C/C++ project binary (x86 only)
-----------------------------------
.. image:: ../_static/pwrforge_flow_docker.svg
   :alt: pwrforge x86 flow
   :align: center

Usage
^^^^^

::

    pwrforge run [OPTIONS] [BIN_PARAMS]...

Description
^^^^^^^^^^^

Run the generated binary file for x86 target.

By default, this command does not build. Use ``--build`` to build before run.
By default, run environment follows ``build-env`` from ``pwrforge.toml``.
Use ``--docker`` or ``--native`` to override the environment for this invocation.

Parameters passed after "--" will be passed to the binary.

Options
^^^^^^^

::

-b, --bin FILE

Relative path to a binary file to run.

::

-p, --profile PROFILE     [default: Debug]

Profile to run  [default: Debug]
This option specifies which profile binary should be run.

::

--build

Run pwrforge build before running the binary.

::

--docker

Force running ``pwrforge run`` inside docker in interactive mode.

::

--native

Force running ``pwrforge run`` in native environment.

::

-B, --base-dir DIRECTORY

Specify the base project path. Allows running pwrforge commands from any directory.
