.. _pwrforge_pic18:

PIC18 support in pwrforge
=========================

Creating a project
------------------
::

    pwrforge new --target pic18 --chip <pic18...> [project_name]

The default PIC18 chip is ``PIC18F4580``. The generated Docker image installs
``sdcc``, ``sdcc-libraries``, and ``gputils`` and builds PIC18 firmware with the
SDCC PIC16 backend.

Configure PIC18 project
-----------------------
To configure your project for a chosen PIC18 chip use ``--chip`` when
initializing the project. It's also possible to change it in *pwrforge.toml* in
the **[pic18]** section and run ``pwrforge update``.

Flashing and debugging
----------------------
PIC18 flashing and debugging are not wired into pwrforge yet. Use your existing
PIC programmer tooling for the generated ``.hex`` artifact.
