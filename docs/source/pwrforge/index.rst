.. _pwrforge:

pwrforge commands
=================

Use ``pwrforge -h`` to see a summary of all available commands and command line options.

To see all options for a particular command, append ``-h`` to the command name. ie ``pwrforge build -h``.
::

   Usage: pwrforge [OPTIONS] COMMAND [ARGS]...

   C/C++ package and software development life cycle manager based on RUST
   cargo idea.

   Options:
   --install-completion Install completion for the current shell.
   --show-completion    Show completion for the current shell, to copy it or
                        customize the installation.
   -h, --help           Show this message and exit.

   Commands:
   build               Compile sources.
   check               Check source code in the directory `src`.
   clean               Remove directory `build`.
   debug               Use gdb CLI to debug
   doc                 Create project documentation
   docker              Manage the docker environment for the project
   fix                 Fix violations reported by the command `check`.
   flash               Flash the target.
   monitor             Connect and monitor the serial interface.
   gen                 Manage the auto file generator
   new                 Create a new project template.
   publish             Upload conan pkg to repo
   run                 Build and run project
   setup_autocomplete  Setup pwrforge autocomplete for shell
   test                Compile and run all tests in directory `test`.
   update              Read .toml config file and generate `CMakeLists.txt`.
   version             Get pwrforge version


pwrforge commands reference
---------------------------

.. toctree::
   :maxdepth: 1

   Build command <pwrforge-build>
   Check command <pwrforge-check>
   Clean command <pwrforge-clean>
   Debug command <pwrforge-debug>
   Doc command <pwrforge-documentation>
   Docker command <pwrforge-docker>
   Fix command <pwrforge-fix>
   Flash command <pwrforge-flash>
   Monitor command <pwrforge-monitor>
   Gen command <pwrforge-gen>
   New command <pwrforge-new>
   Publish command <pwrforge-publish>
   Run command <pwrforge-run>
   Test command <pwrforge-test>
   Update command <pwrforge-update>
   Version command <pwrforge-version>


See also
--------

.. toctree::
   :maxdepth: 1

   pwrforge Toml file configuration <pwrforge-toml>

