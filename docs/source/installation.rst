.. _installation:

Installation and Dependencies
=============================

You will need `Python 3.10 or newer <https://www.python.org/downloads/>`_ installed on your system to use the latest version of ``pwrforge``.

The latest stable pwrforge release can be installed from `PyPI <https://pypi.org/project/pwrforge/>`_ via pip:

::

   $ pip install pwrforge

With some Python installations this may not work and you’ll receive an error, try ``python -m pip install pwrforge`` or ``pip3 install pwrforge``, or consult your `Python installation manual <https://pip.pypa.io/en/stable/installation/>`_ for information about how to access pip.

`Setuptools <https://setuptools.pypa.io/en/latest/userguide/quickstart.html>`_ is also a requirement which is not available on all systems by default. You can install it by a package manager of your operating system, or by ``pip install setuptools``.

After installing, you will have ``pwrforge`` installed into the default Python executables directory and you should be able to run it with the command ``pwrforge`` or ``python -m pwrforge``. Please note that probably only ``python -m pwrforge`` will work for Pythons installed from Windows Store.

If system does not find 'pwrforge' command after installing, add the installation directory to your env paths. On Ubuntu you can find installation directory by running:

::

   $ find / -name "pwrforge"

Then add to  PATH:

::

   $ export PATH=~/.local/bin:${PATH}
