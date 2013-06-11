pyVenvSetup
===========

Script to create consistent virtual environments.

Usage:

    DoubleClick on SetupEnvironment.py
    - or -
    See SetupEnvironment.py --help

What it does:

    1. runs virtualenv.py with an option python executable and an optional
       environment name.
    2. activates the newly created virtual environment and installs the
       packages found in the pipPackages text file.
    3. generates a helper script to activate the python environment
    4. cleans up the installation artifacts

