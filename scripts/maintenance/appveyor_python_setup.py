#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Ensure the right version of Python and pip are installed on AppVeyor."""
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

from io import open
from os import getenv, listdir
from os.path import exists
from subprocess import CalledProcessError, check_call
try:
    from urllib.request import urlretrieve
except ImportError:  # Python 2
    from urllib import urlretrieve


def get_installer_info(version, arch64):
    """Return the download url and filename for given version and arch."""
    # See https://www.python.org/downloads/windows/
    msi_installer = version < '3.5.0'
    filename = 'python-{version}{amd64}{extension}'.format(
        amd64=(('.' if msi_installer else '-')
               + 'amd64' if arch64 else ''),
        extension=('.msi' if msi_installer else '.exe'),
        **locals())
    url = 'https://www.python.org/ftp/python/{version}/{filename}'.format(
        **locals())
    return filename, url


def download_python(version, arch64):
    """Download Python installer and return its filename."""
    filename, download_url = get_installer_info(version, arch64)
    print('Downloading Python installer from', download_url)
    urlretrieve(download_url, filename)
    return filename


def print_python_install_log(version):
    """Print the log for Python installation."""
    # appveyor's %temp% points to "C:\Users\appveyor\AppData\Local\Temp\1"
    # but python log files are stored in "C:\Users\appveyor\AppData\Local\Temp
    temp_dir = 'C:/Users/appveyor/AppData/Local/Temp/'
    for file in listdir(temp_dir):
        if file[-4:] == '.log' and file.startswith('Python ' + version):
            with open(temp_dir + file, encoding='utf-8') as log:
                print(file + ':\n' + log.read())
            break
    else:
        print('There was no Python log file.')


def install_python(installer, python_dir, python_ver):
    """Install Python using specified installer file."""
    common_args = [
        installer, '/quiet', 'TargetDir=' + python_dir, 'AssociateFiles=0',
        'Shortcuts=0', 'Include_doc=0', 'Include_launcher=0',
        'InstallLauncherAllUsers=0', 'Include_tcltk=0', 'Include_test=0']
    try:
        if installer[-4:] == '.msi':
            check_call(['msiexec', '/norestart', '/i'] + common_args)
        else:  # executable installer
            # uninstall first, otherwise the install won't do anything
            check_call(common_args)
    except CalledProcessError:
        print_python_install_log(python_ver)
        raise SystemExit('install_python failed')


def download_packages(packages, python_dir):
    """Download packages and return their paths."""
    preinstalled_py_dir = python_dir[:11] + python_dir[12:] \
        if len(python_dir) in (16, 12) else python_dir
    preinstalled_pip = preinstalled_py_dir + '/scripts/pip.exe'
    # It is not possible to use --python-version due to cryptography
    # requirements on py2.7 which leads to
    # https://stackoverflow.com/questions/46287077/
    check_call([
        preinstalled_pip, 'download', '--dest', '.pip_downloads',
        '--disable-pip-version-check'] + packages)
    downloads = listdir('.pip_downloads')
    assert downloads, 'pip did not download anything'
    return ['.pip_downloads/' + fn for fn in downloads]


def install_packages(python_dir, python_ver):
    """Install/upgrade pip, setuptools, and other packages if required."""
    python = python_dir + '/python.exe'
    packages = ['pip', 'setuptools']
    pip_installer = [python, '-m', 'pip', 'install', '-U']
    if python_ver < '2.7.9':
        check_call([python, 'ez_setup.py'])  # bootstrap setuptools
        urlretrieve('https://bootstrap.pypa.io/get-pip.py', 'get-pip.py')
        pip_installer = [python, '-m', 'get-pip', '-U']
        packages.remove('setuptools')  # can't upgrade bootstrapped setuptools
        packages.extend(('wheel', 'pip'))
        packages = download_packages(packages, python_dir)
    check_call(pip_installer + packages)


def main():
    python_ver = getenv('PYTHON_VERSION')
    python_dir = getenv('PYTHON')
    if not python_ver[-2:] == '.x':  # .x is for pre-installed Python versions
        arch64 = getenv('PYTHON_ARCH') == '64'
        filename = download_python(python_ver, arch64)
        install_python(filename, python_dir, python_ver)
    if not exists(python_dir + r'\python.exe'):
        print_python_install_log(python_ver)
        raise SystemExit(python_dir + r'\python.exe not found')
    install_packages(python_dir, python_ver)


if __name__ == '__main__':
    main()
