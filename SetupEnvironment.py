"""
   OriginalAuthor: Thurston Stone
   Description: Creates the appropriate python virtual environment needed.
   Usage: See SetupEnvironment.py --help for details
"""

cmdDesc = """
    Creates the appropriate python virtual environment needed.
    """

import sys
import os
import argparse
import logging
#-------------------
import glob
import shutil
import subprocess

INVALID_USAGE_RETURN_CODE = 2
UNCAUGHT_EXCEPTION = 3

SCRIPT_FILE = os.path.basename(os.path.abspath(__file__))
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PIP_PACKAGE_FILE = os.path.join(SCRIPT_DIR, "pipPackages.txt")

try:
    execfile
except NameError:
    def execfile(afile, globalz=None, localz=None):
        with open(afile, "r") as fh:
            exec(fh.read(), globalz, localz)


class UsageError(Exception):
    """ Exception class when the file is used incorrectly on the command line
    """
    def __init__(self, parser, error):
        self.parser = parser
        self.error = error

    def __str__(self):
        return self.error

    def PrintError(self):
        self.parser.print_usage()
        print("ERROR: %s" % self.error)


def ValidateArgs(argv):
    """
    Function: validateArgs():
    will validate the command line arguments and options passed.
    it returns opts,args
    """

    parser = argparse.ArgumentParser(description=cmdDesc)
    #general options

    parser.add_argument("-v",
                        "--verbose",
                        default="ERROR",
                        const="INFO",
                        nargs="?",
                        help="Level of verbose output to Display to stdout"
                             "(DEBUG, INFO, WARNING, ERROR, CRITICAL, FATAL)")

    parser.add_argument("--pip-packages-file",
                        default=None,
                        help="File containing a list of packages to install.")
    parser.add_argument("-i",
                        "--install",
                        default=False,
                        action="store_true",
                        help="Install the necessary software.  This "
                             "installs into the current environment.")

    parser.add_argument("-p",
                        "--python",
                        default=None,
                        help="Path to the python executable to use")

    parser.add_argument("-l",
                        "--location",
                        default=None,
                        help="Location of the new python environment")

    args = parser.parse_args(argv[1:])
    error = None
    """
    Place any error checking here.  If an error occurred, set the error
    variable.
    """

    if error is not None:
        raise UsageError(parser, error)
    return args


def which(name, flags=os.X_OK):
    # Copyright (c) 2001-2004 Twisted Matrix Laboratories.
    # See LICENSE for details.
    """Search PATH for executable files with the given name.

    On newer versions of MS-Windows, the PATHEXT environment variable will be
    set to the list of file extensions for files considered executable. This
    will normally include things like ".EXE". This fuction will also find files
    with the given name ending with any of these extensions.

    On MS-Windows the only flag that has any meaning is os.F_OK. Any other
    flags will be ignored.

    @type name: C{str}
    @param name: The name for which to search.

    @type flags: C{int}
    @param flags: Arguments to L{os.access}.

    @rtype: C{list}
    @param: A list of the full paths to files found, in the
    order in which they were found.
    """
    result = []
    exts = filter(None, os.environ.get('PATHEXT', '').split(os.pathsep))
    path = os.environ.get('PATH', None)
    if path is None:
        return []
    for p in os.environ.get('PATH', '').split(os.pathsep):
        p = os.path.join(p, name)
        if os.access(p, flags):
            result.append(p)
        for e in exts:
            pext = p + e
            if os.access(pext, flags):
                result.append(pext)
    return result


def SetupEnvironment(pythonPath=None, envLocation=None,
                     pipPackagesFile=None):
    """
    """
    debugMessage = "SetupEnvironment(pythonPath=%s, envLocation=%s, "
    debugMessage += "pipPackagesFile=%s)"
    logging.debug(debugMessage % (
                  str(pythonPath),
                  str(envLocation),
                  str(pipPackagesFile)))

    if pythonPath is None:
        pythons = which("python")
        if len(pythons) == 0:
            raise IOError("python executable not found")
        else:
            pythonPath = pythons[0]

    if envLocation is None:
        envLocation = "venv"
    if not os.path.exists(envLocation):
        file = os.path.join(SCRIPT_DIR, "virtualenv.py")
        cmdArgs = [pythonPath, file, envLocation]
        popen = subprocess.Popen(cmdArgs)
        if popen.wait():
            #an error occurred
            raise RuntimeError("Failed running process: %s" % " ".join(cmdArgs))
    pythonExe = os.path.join(envLocation, GetBinDir(), "python")
    logLevel = logging._levelNames[logging.getLogger().getEffectiveLevel()]
    installArgs = ["-v", logLevel,
                   "--install",
                   "--show-traceback",
                   "-l", envLocation]
    if pipPackagesFile is not None:
        installArgs += ["--pip-packages-file", pipPackagesFile]
    cmdArgs = [pythonExe, __file__] + installArgs
    logging.debug("Running command: %s" % " ".join(cmdArgs))
    popen = subprocess.Popen(cmdArgs)
    if popen.wait():
        #an error occurred
        raise RuntimeError("Failed running process: %s" % " ".join(cmdArgs))
    GenerateStartupScript()
    Cleanup()


def GenerateStartupScript():
    if sys.platform == "win32":
        startFile = os.path.join(SCRIPT_DIR, "startEnv.bat")
        if not os.path.exists(startFile):
            logging.debug("Creating startup script: %s" % startFile)
            fileContent = r"""
@setlocal
@set ENV=venv
@if not _%1_ == __ set ENV=%1
@start %ENV%\Scripts\activate.bat
            """
            with open(startFile,"w") as f:
                f.write(fileContent)
        
            
    else:
        if not os.path.exists("startEnv.sh"):
            raise NotImplementedError()


def Cleanup():
    logging.debug("Cleaning up")
    globExpression = os.path.join(SCRIPT_DIR, "distribute-*")
    for file in glob.iglob(globExpression):
        logging.debug("Removing %s" % file)
        os.unlink(file)
    pycacheDir = os.path.join(SCRIPT_DIR,"__pycache__")
    if os.path.isdir(pycacheDir):
        logging.debug("Removing %s" % pycacheDir)
        shutil.rmtree(pycacheDir)

    #remove __pycache__


def GetBinDir():
    if sys.platform == "win32":
        binDir = "Scripts"
    else:
        binDir = "bin"
    return binDir


def InstallEnvironment(envLocation, pipPackageFile):
    import pip
    logging.debug("Installing...")
    activatePath = os.path.join(envLocation, GetBinDir(), "activate_this.py")
    execfile(activatePath, dict(__file__=activatePath))
    if pipPackageFile is None:
        pipPackageFile = DEFAULT_PIP_PACKAGE_FILE
    packages = []
    if os.path.isfile(pipPackageFile):
        logging.debug("Reading Packages from: %s" % pipPackageFile)
        with open(pipPackageFile) as f:
            for line in f.readlines():
                logging.debug("Found Package: %s" % line.rstrip("\n"))
                packages.append(line.rstrip("\n"))
        if len(packages) > 0:
            cmdArgs = ["install"] + packages
            logging.debug("Pip command: %s" % " ".join(cmdArgs))
            pip.main(cmdArgs)


def Main(argv):
    """
    The main function.  This function will run if the command line is called as
    opposed to this file being imported.
    """
    args = ValidateArgs(argv)
    level = getattr(logging, args.verbose.upper())
    logging.basicConfig(level=level,
                        format='%(module)s(%(lineno)d)|[%(asctime)s]|' +
                               '[%(levelname)s]| %(message)s')
    logging.debug("Python %s" % sys.version)
    if (args.install):
        InstallEnvironment(args.location, args.pip_packages_file)
    else:
        SetupEnvironment(args.python, args.location, args.pip_packages_file)

# if this program is run on the command line, run the main function
if __name__ == '__main__':
    showTraceback = False
    if '--show-traceback' in sys.argv:
        showTraceback = True
        del sys.argv[sys.argv.index('--show-traceback')]
    try:
        retval = Main(sys.argv)
        if exit:
            sys.exit(retval)
    except UsageError as e:
        if showTraceback:
            raise
        e.PrintError()
        returnCode = INVALID_USAGE_RETURN_CODE
    except Exception as e:
        if showTraceback:
            raise
        print("Uncaught Exception: %s: %s" % (type(e), e))
        returnCode = UNCAUGHT_EXCEPTION
    sys.exit(returnCode)
