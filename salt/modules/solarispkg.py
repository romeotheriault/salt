'''
Package support for Solaris
'''

import tempfile
import os


def __virtual__():
    '''
    Set the virtual pkg module if the os is Solaris
    '''
    if __grains__['os'] == 'SunOS':
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


def _get_pkgs():
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


def install(name, **kwargs):
    '''
    Install the passed package

    # pkgadd -n -a /root/admin.file -d /root/testing/ZABagent2.pkg 'all'
    # Does this work with non-datastream packages?

    Return a dict containing the new package names and versions::

        {'<package>': {'old': '<old-version>',
                   'new': '<new-version>']}

    CLI Example::

        salt '*' pkg.install <package name>
    '''

    if 'source' in kwargs:
         pkgfile = __salt__['file.cache'](kwargs['source'])
    else:
         pkgfile = name

    if 'admin_source' in kwargs:
        adminfile = __salt__['file.cache'](kwargs['admin_source'])
    else:
        # Set the adminfile default variables
        email=kwargs.get('email', '')
        instance=kwargs.get('instance', 'overwrite')
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


    cmd = '/usr/sbin/pkgadd -n -a {0} -d {1} \'all\''.format(adminfile, pkgfile)
    __salt__['cmd.retcode'](cmd)

    #new = _format_pkgs(_get_pkgs())
    #return name{new} = version(name)

    # Remove the temp adminfile 
    os.unlink(adminfile)

    return [name] 


def remove(name, **kwargs):
    '''
    Remove a single package with pkgrm

    Returns a list containing the removed packages. Since pkgrm on solaris 
    does not support dependency management. This will always be just one
    package.

    CLI Example::

        salt '*' pkg.remove <package name>
    '''

    # Check to see if the package is installed before we proceed
    if version(name) == '':
        return '' 

    # Set the adminfile default variables
    email=kwargs.get('email', '')
    instance=kwargs.get('instance', 'overwrite')
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

    # Remove the package
    cmd = '/usr/sbin/pkgrm -n -a {0} {1}'.format(adminfile, name)
    __salt__['cmd.retcode'](cmd)

    # Remove the temp adminfile 
    os.unlink(adminfile)

    # Since pkgrm only removes one pkg at a time just return the package name
    return [name] 


def purge(name, **kwargs):
    '''
    Remove a single package with pkgrm

    Returns a list containing the removed packages.

    CLI Example::

        salt '*' pkg.purge <package name>
    '''
    return remove(name, **kwargs)
