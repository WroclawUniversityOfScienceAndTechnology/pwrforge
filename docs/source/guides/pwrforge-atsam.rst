.. _pwrforge_atsam:

Atmel SAM support in pwrforge
===========================

Creating a project
------------------
::

    pwrforge new --target atsam --chip <atsam...> [project_name]


When building the project for the first time pwrforge will fetch CMSIS and DFP packs for your chip.
It's also possible to change the chip in *pwrforge.toml* file and run pwrforge update command to update project accordingly.

Flashing
--------
Flashing the Atmel SAM series is currently supported by using openocd in the background.
Run the :doc:`pwrforge flash command </pwrforge/pwrforge-flash>` to flash the board.

This flashing procedure might not work for all boards.
If you have any problems you can  `open issue on github <https://github.com/Spyro-Soft/pwrforge/issues/new/choose>`_.

Debugging
---------
If you plan on debugging make sure that your board has debugger or you are connected to the board using debugger.
First build the project in Debug and then you can run :doc:`pwrforge debug command </pwrforge/pwrforge-debug>`: ::

    pwrforge build --profile Debug
    pwrforge debug
