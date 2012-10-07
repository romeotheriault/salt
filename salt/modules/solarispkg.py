'''
Package support for Solaris
'''
# Todo:
# Test with states to make sure it works.
# How to we deal with upgrade?
# Have it looked over.

import tempfile
import os
import shutil


def __virtual__():
    '''
    Set the virtual pkg module if the os is Solaris
    '''
    if __grains__['os'] == 'Solaris':
        return 'pkg'
    return False


def _list_removed(old, new):
    '''
    List the packages which have been removed between the two package objects
    '''
    pkgs = []
    for pkg in old:
        if pkg not in new:
            pkgs.append(pkg)

    return pkgs


def _compare_versions(old, new):
    '''
    Returns a dict that that displays old and new versions for a package after
    install/upgrade of package.
    '''
    pkgs = {}
    for npkg in new:
        if npkg in old:
            if old[npkg] == new[npkg]:
                # no change in the package
                continue
            else:
                # the package was here before and the version has changed
                pkgs[npkg] = {'old': old[npkg],
                              'new': new[npkg]}
        else:
            # the package is freshly installed
            pkgs[npkg] = {'old': '',
                          'new': new[npkg]}
    return pkgs


def _get_pkgs():
    '''
    Get a full list of the package installed on the machine
    '''
    pkg = {}
    cmd = '/usr/bin/pkginfo -x'

    line_count = 0
    for line in __salt__['cmd.run'](cmd).split('\n'):
        if line_count % 2 == 0:
            namever = line.split()[0].strip()
        if line_count % 2 == 1:
            pkg[namever] = line.split()[1].strip()
        line_count = line_count + 1
    return pkg


def list_pkgs():
    '''
    List the packages currently installed as a dict::

        {'<package_name>': '<version>'}

    CLI Example::

        salt '*' pkg.list_pkgs
    '''
    return _get_pkgs()


def version(name):
    '''
    Returns a version if the package is installed, else returns an empty string

    CLI Example::

        salt '*' pkg.version <package name>
    '''
    cmd = '/usr/bin/pkgparam {0} VERSION 2> /dev/null'.format(name)
    namever = __salt__['cmd.run'](cmd)
    if namever:
        return namever
    return ''


def install(name, refresh=False, **kwargs):
    '''
    Install the passed package. Can install packages from the following sources::
        
        * Locally (package already exists on the minion 
        * HTTP/HTTPS server
        * FTP server
        * Salt master

    Returns a dict containing the new package names and versions::

        {'<package>': {'old': '<old-version>',
                   'new': '<new-version>']}

    CLI Example, installing a datastream pkg that already exists on the minion::

        salt '*' pkg.install <package name> source=/dir/on/minion/<package name>
        salt '*' pkg.install gcc-3.3.2-sol10-sparc-local.pkg source=/var/spool/pkg/gcc-3.3.2-sol10-sparc-local.pkg

    CLI Example, installing a datastream pkg that exists on the salt master::

        salt '*' pkg.install <package name> source='salt://srv/prod/<package name>'

    CLI Example, installing a datastream pkg that exists on a HTTP server::

        salt '*' pkg.install <package name> source='http://packages.server.com/<package name>'
    
    By default salt automatically provides an adminfile, to automate package installation, with these options set:

        email=
        instance=quit
        partial=nocheck
        runlevel=nocheck
        idepend=nocheck
        rdepend=nocheck
        space=nocheck
        setuid=nocheck
        conflict=nocheck
        action=nocheck
        basedir=default

    You can override any of these options in two ways. First you can optionally pass any of
    the options as a kwarg to the module/state to override the default value or you can
    optionally pass the 'admin_source' option providing your own adminfile to the minions.

    Note: You can find all of the possible options to provide to the adminfile by reading the admin man page:

        man -s 4 admin

    CLI Example - Overriding the 'instance' adminfile option when calling the module directly:

        salt '*' pkg.install <package name> source='salt://srv/salt/<pkgname>' instance="overwrite"  

    CLI Example - Overriding the 'instance' adminfile option when used in a state:

        <pkgname>:
          pkg.installed:
            - source: salt://pkgs/<pkgname>
            - instance: overwrite

    CLI Example - Providing your own adminfile when calling the module directly:

        salt '*' pkg.install <package name> source='salt://srv/salt/<pkgname>' admin_source='salt://srv/salt/adminfile'
    
    CLI Example - Providing your own adminfile when using states:

        <pkgname>:
          pkg.installed:
            - source: salt://srv/salt/<pkgname>
            - admin_source: salt://srv/salt/adminfile
    '''

    if not 'source' in kwargs:
        return 'source option required with solaris pkg installs'
    else:
        if (kwargs['source']).startswith('salt://') or (kwargs['source']).startswith('http://') or (kwargs['source']).startswith('https://') or (kwargs['source']).startswith('ftp://'):
            pkgname = __salt__['cp.cache_file'](kwargs['source'])
        else:
            pkgname = (kwargs['source'])

    if 'admin_source' in kwargs:
        adminfile = __salt__['cp.cache_file'](kwargs['admin_source'])
    else:
        # Set the adminfile default variables
        email=kwargs.get('email', '')
        instance=kwargs.get('instance', 'quit')
        partial=kwargs.get('partial', 'nocheck')
        runlevel=kwargs.get('runlevel', 'nocheck')
        idepend=kwargs.get('idepend', 'nocheck')
        rdepend=kwargs.get('rdepend', 'nocheck')
        space=kwargs.get('space', 'nocheck')
        setuid=kwargs.get('setuid', 'nocheck')
        conflict=kwargs.get('conflict', 'nocheck')
        action=kwargs.get('action', 'nocheck')
        basedir=kwargs.get('basedir', 'default')

        # Make tempfile to hold the adminfile contents.
        fd, adminfile = tempfile.mkstemp(prefix="salt-")
   
        # Write to file then close it.
        os.write(fd, "email=%s\n" % email)
        os.write(fd, "instance=%s\n" % instance)
        os.write(fd, "partial=%s\n" % partial)
        os.write(fd, "runlevel=%s\n" % runlevel)
        os.write(fd, "idepend=%s\n" % idepend)
        os.write(fd, "rdepend=%s\n" % rdepend)
        os.write(fd, "space=%s\n" % space)
        os.write(fd, "setuid=%s\n" % setuid)
        os.write(fd, "conflict=%s\n" % conflict)
        os.write(fd, "action=%s\n" % action)
        os.write(fd, "basedir=%s\n" % basedir)
        os.close(fd)

    # Get a list of the packages before install so we can diff after to see 
    # what got installed.
    old = _get_pkgs()

    # Install the package
    cmd = '/usr/sbin/pkgadd -n -a {0} -d {1} \'all\''.format(adminfile, pkgname)
    __salt__['cmd.retcode'](cmd)

    # Get a list of the packages again, including newly installed ones.
    new = _get_pkgs()

    # Remove the temp adminfile 
    if not 'admin_source' in kwargs:
        os.unlink(adminfile)

    # Return a list of the new package installed.
    return _compare_versions(old, new)


def remove(name, **kwargs):
    '''
    Remove a single package with pkgrm

    By default salt automatically provides an adminfile, to automate package removal, with these options set:

        email=
        instance=quit
        partial=nocheck
        runlevel=nocheck
        idepend=nocheck
        rdepend=nocheck
        space=nocheck
        setuid=nocheck
        conflict=nocheck
        action=nocheck
        basedir=default

    You can override any of these options in two ways. First you can optionally pass any of
    the options as a kwarg to the module/state to override the default value or you can
    optionally pass the 'admin_source' option providing your own adminfile to the minions.

    Note: You can find all of the possible options to provide to the adminfile by reading the admin man page:

        man -s 4 admin

    CLI Example::

        salt '*' pkg.remove <package name>
        salt '*' pkg.remove SUNWgit
    '''

    # Check to see if the package is installed before we proceed
    if version(name) == '':
        return '' 

    if 'admin_source' in kwargs:
        adminfile = __salt__['cp.cache_file'](kwargs['admin_source'])
    else:
        # Set the adminfile default variables
        email=kwargs.get('email', '')
        instance=kwargs.get('instance', 'quit')
        partial=kwargs.get('partial', 'nocheck')
        runlevel=kwargs.get('runlevel', 'nocheck')
        idepend=kwargs.get('idepend', 'nocheck')
        rdepend=kwargs.get('rdepend', 'nocheck')
        space=kwargs.get('space', 'nocheck')
        setuid=kwargs.get('setuid', 'nocheck')
        conflict=kwargs.get('conflict', 'nocheck')
        action=kwargs.get('action', 'nocheck')
        basedir=kwargs.get('basedir', 'default')

        # Make tempfile to hold the adminfile contents.
        fd, adminfile = tempfile.mkstemp(prefix="salt-")
   
        # Write to file then close it.
        os.write(fd, "email=%s\n" % email)
        os.write(fd, "instance=%s\n" % instance)
        os.write(fd, "partial=%s\n" % partial)
        os.write(fd, "runlevel=%s\n" % runlevel)
        os.write(fd, "idepend=%s\n" % idepend)
        os.write(fd, "rdepend=%s\n" % rdepend)
        os.write(fd, "space=%s\n" % space)
        os.write(fd, "setuid=%s\n" % setuid)
        os.write(fd, "conflict=%s\n" % conflict)
        os.write(fd, "action=%s\n" % action)
        os.write(fd, "basedir=%s\n" % basedir)
        os.close(fd)

    # Get a list of the currently installed pkgs.
    old = _get_pkgs()

    # Remove the package
    cmd = '/usr/sbin/pkgrm -n -a {0} {1}'.format(adminfile, name)
    __salt__['cmd.retcode'](cmd)

    # Remove the temp adminfile 
    if not 'admin_source' in kwargs:
        os.unlink(adminfile)

    # Get a list of the packages after the uninstall
    new = _get_pkgs()
     
    # Compare the pre and post remove package objects and report the uninstalled pkgs.
    return _list_removed(old, new)



def purge(name, **kwargs):
    '''
    Remove a single package with pkgrm

    Returns a list containing the removed packages.

    CLI Example::

        salt '*' pkg.purge <package name>
    '''
    return remove(name, **kwargs)



def available_version(name):
    '''
    The available version of the package in the repository
    On Solaris with the pkg module this always returns the
    version that is installed since pkgadd does not have
    the concept of a repository.

    CLI Example::

        salt '*' pkg.available_version <package name>
    '''
    return version(name) 
