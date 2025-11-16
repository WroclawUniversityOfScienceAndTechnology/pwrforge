.. _pwrforge_clean:

Clean C/C++ project artifacts
-----------------------------
.. image:: ../_static/pwrforge_clean_build_docker.svg
   :alt: pwrforge clean and build example
   :align: center

Usage
^^^^^
::

    pwrforge clean [OPTIONS]

Description
^^^^^^^^^^^

Clean build directory. Keeps cmake fetched content in build/.cmake_fetch_cache.

Options
^^^^^^^

::

-B, --base-dir DIRECTORY

Specify the base project path. Allows running pwrforge commands from any directory.

Example
^^^^^^^

Command:
::

    pwrforge clean

**Effects:**

Cleans directory build

Cleans directory test/build