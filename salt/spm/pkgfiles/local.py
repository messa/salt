# -*- coding: utf-8 -*-
'''
This module allows SPM to use the local filesystem to install files for SPM.

.. versionadded:: 2015.8.0
'''

from __future__ import absolute_import
import os
import os.path
import logging
import salt.syspaths

# Get logging started
log = logging.getLogger(__name__)


def init(**kwargs):
    '''
    Initialize the directories for the files
    '''
    formula_path = __opts__['formula_path']
    pillar_path = __opts__['pillar_path']
    reactor_path = __opts__['reactor_path']
    for dir_ in (formula_path, pillar_path, reactor_path):
        if not os.path.exists(dir_):
            os.makedirs(dir_)
    return {
        'formula_path': formula_path,
        'pillar_path': pillar_path,
        'reactor_path': reactor_path,
    }


def check_existing(package, pkg_files, formula_def, conn=None):
    '''
    Check the filesystem for existing files
    '''
    if conn is None:
        conn = init()

    existing_files = []
    for member in pkg_files:
        if member.isdir():
            continue

        tld = formula_def.get('top_level_dir', package)
        new_name = member.name.replace('{0}/'.format(package), '')
        if not new_name.startswith(tld):
            continue

        if member.name.startswith('{0}/_'.format(package)):
            # Module files are distributed via _modules, _states, etc
            out_file = os.path.join(conn['formula_path'], new_name)
        elif member.name == '{0}/pillar.example'.format(package):
            # Pillars are automatically put in the pillar_path
            new_name = '{0}.sls.orig'.format(package)
            out_file = os.path.join(conn['pillar_path'], new_name)
        elif package.endswith('-conf'):
            # Configuration files go into /etc/salt/
            out_file = os.path.join(salt.syspaths.CONFIG_DIR, new_name)
        elif package.endswith('-reactor'):
            # Reactor files go into /srv/reactor/
            out_file = os.path.join(conn['reactor_path'], member.name)
        else:
            out_file = os.path.join(conn['formula_path'], member.name)

        if os.path.exists(out_file):
            existing_files.append(out_file)
            if not __opts__['force']:
                log.error('{0} already exists, not installing'.format(out_file))

    return existing_files


def install_file(package, formula_tar, member, formula_def, conn=None):
    '''
    Install a single file to the file system
    '''
    if member.name == package:
        return False

    if conn is None:
        conn = init()

    out_path = conn['formula_path']

    tld = formula_def.get('top_level_dir', package)
    new_name = member.name.replace('{0}/'.format(package), '', 1)
    if not new_name.startswith(tld) and not new_name.startswith('_') and not new_name.startswith('pillar.example'):
        log.debug('{0} not in top level directory, not installing'.format(new_name))
        return False

    if member.name.startswith('{0}/_'.format(package)):
        # Module files are distributed via _modules, _states, etc
        member.name = member.name.replace('{0}/'.format(package), '')
    elif member.name == '{0}/pillar.example'.format(package):
        # Pillars are automatically put in the pillar_path
        member.name = '{0}.sls.orig'.format(package)
        out_path = conn['pillar_path']
    elif package.endswith('-conf'):
        # Configuration files go into /etc/salt/
        member.name = member.name.replace('{0}/'.format(package), '')
        out_path = salt.syspaths.CONFIG_DIR
    elif package.endswith('-reactor'):
        # Reactor files go into /srv/reactor/
        out_path = __opts__['reactor_path']

    log.debug('Installing package file {0} to {1}'.format(member.name, out_path))
    formula_tar.extract(member, out_path)

    return out_path


def remove_file(path, conn=None):
    '''
    Remove a single file from the file system
    '''
    if conn is None:
        conn = init()

    log.debug('Removing package file {0}'.format(path))
    os.remove(path)


def hash_file(path, hashobj, conn=None):
    '''
    Get the hexdigest hash value of a file
    '''
    if os.path.isdir(path):
        return ''

    with salt.utils.fopen(path, 'r') as f:
        hashobj.update(f.read())
        return hashobj.hexdigest()


def path_exists(path):
    '''
    Check to see whether the file already exists
    '''
    return os.path.exists(path)


def path_isdir(path):
    '''
    Check to see whether the file already exists
    '''
    return os.path.isdir(path)
