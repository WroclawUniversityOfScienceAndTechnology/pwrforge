.. _pwrforge_test:

Test C/C++ project source code
------------------------------
.. image:: ../_static/pwrforge_flow_docker.svg
   :alt: pwrforge x86 flow
   :align: center

Usage
^^^^^
::

    pwrforge test [OPTIONS]

Description
^^^^^^^^^^^

Compile and run all tests in directory test.

Options
^^^^^^^
::

    -v, --verbose

Verbose output.

This should run
::

    ctest --verbose.

::
    -p, --profile PROFILE

CMake profile to use. Default: Debug

::
    --detailed-coverage / --no-detailed-coverage        [default: no-detailed-coverage]

Generate detailed coverage HTML files.

::

    -B, --base-dir DIRECTORY

Specify the base project path. Allows running pwrforge commands from any directory.

Example
^^^^^^^
The project is compiled with a compiler for the target system, but tests must be compiled with the system compiler on the developer's computer. For example, a project could be compiled with arm-none-eabi-gcc but tests must be compiled with a system compiler, which is usually gcc. Programs compiled with ARM's compiler cannot be executed on desktop PC.

CMake does not support multiple compilers in the project. You have to stick to one compiler and use it to compile everything.

How to overcome this problem?

We could have a dedicated section in pwrforge.toml to define compiler and flags for building tests:

::

    [test]
    cc = "gcc"     # C compiler for tests
    cxx = "g++"    # C++ compiler for tests

    cflags = "-Wall -Wextra -Werror"    # Flags for C compiler
    cxxflags = "-Wall -Wextra -Werror"  # Flags for C++ compiler

    additional-cmake-flag1 = "first"
    additional-cmake-flag2 = "second"

Command pwrforge update would generate two CMakeLists.txt files:

Top-level CMakeLists.txt in the project's root directory (as before).
Top-level CMakeLists.txt in directory test.

The project structure would look something like this:

::

    $ tree
    .
    ├── CMakeLists.txt
    ├── pwrforge.toml
    ├── src
    │   ├── CMakeLists.txt
    │   └── foo.cpp
    └── test
        ├── CMakeLists.txt
        ├── it
        ├── mock
        └── ut

File ./test/CMakeLists.txt is not included into ./CMakeLists.txt

Command pwrforge test would do the following:

::

    $ cd test
    $ mkdir build
    $ cd build
    $ cmake ..
    $ cmake --build .
    $ ctest


