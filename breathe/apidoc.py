# -*- coding: utf-8 -*-
"""
    breathe.apidoc
    ~~~~~~~~~~~~~~

    Parses doxygen XML tree looking for C/C++ modules and creates ReST files
    appropriately to create code documentation with Sphinx. It also creates a
    modules index (See TYPEDICT below.).

    This is derived from the "sphinx-autopackage" script, which is:
    Copyright 2008 Société des arts technologiques (SAT),
    http://www.sat.qc.ca/

    :copyright: Originally by Sphinx Team, C++ modifications by Tatsuyuki Ishi
    :license: BSD, see LICENSE for details.
"""
from __future__ import print_function

import os
import sys
import argparse
import errno
import xml.etree.ElementTree

from breathe import __version__


# Reference: Doxygen XSD schema file, CompoundKind only
# Only what breathe supports are included
# Translates identifier to English
TYPEDICT = {'class': 'Class',
            'struct': 'Struct',
            'union': 'Union',
            'file': 'File',
            'namespace': 'Namespace',
            'group': 'Group'}


def write_file(name, text, args):
    """Write the output file for module/package <name>."""
    fname = os.path.join(args.destdir, '%s.%s' % (name, args.suffix))
    if args.dryrun:
        print('Would create file %s.' % fname)
        return
    if not args.force and os.path.isfile(fname):
        print('File %s already exists, skipping.' % fname)
    else:
        print('Creating file %s.' % fname)
        if not os.path.exists(os.path.dirname(fname)):
            try:
                os.makedirs(os.path.dirname(fname))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        target = open(fname, 'r')
        try:
            orig = target.read()
        finally:
            target.close()
        if orig == text:
            print('File %s up to date, skipping.' % fname)
            return
        target = open(fname, 'w')
        try:
            target.write(text)
        finally:
            target.close()


def format_heading(level, text):
    """Create a heading of <level> [1, 2 or 3 supported]."""
    underlining = ['=', '-', '~', ][level - 1] * len(text)
    return '%s\n%s\n\n' % (text, underlining)


def format_directive(package_type, package):
    """Create the breathe directive and add the options."""
    directive = '.. doxygen%s:: %s\n' % (package_type, package)
    return directive


def create_package_file(package, package_type, package_id, args):
    """Build the text of the file and write the file."""
    # Some types are unsupported by breathe
    if package_type not in TYPEDICT:
        return
    text = format_heading(1, '%s %s' % (TYPEDICT[package_type], package))
    text += format_directive(package_type, package)

    write_file(os.path.join(package_type, package_id), text, args)


def create_modules_toc_file(key, value, args):
    """Create the module's index."""
    if not os.path.isdir(os.path.join(args.destdir, key)):
        return
    text = format_heading(1, '%s list' % value)
    text += '.. toctree::\n'
    text += '   :glob:\n\n'
    text += '   %s/*\n' % key

    write_file('%slist' % key, text, args)


def recurse_tree(args):
    """
    Look for every file in the directory tree and create the corresponding
    ReST files.
    """
    index = xml.etree.ElementTree.parse(os.path.join(args.rootpath, 'index.xml'))

    # Assuming this is a valid Doxygen XML
    for compound in index.getroot():
        create_package_file(compound.findtext('name'), compound.get('kind'),
                            compound.get('refid'), args)


def main():
    """Parse and check the command line arguments."""
    parser = argparse.ArgumentParser(
        description="""\
Parse XML created by Doxygen in <rootpath> and create one reST file with
breathe generation directives per definition in the <DESTDIR>.

Note: By default this script will not overwrite already created files.""",
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-o', '--output-dir', action='store', dest='destdir',
                        help='Directory to place all output', required=True)
    parser.add_argument('-f', '--force', action='store_true', dest='force',
                        help='Overwrite existing files')
    parser.add_argument('-n', '--dry-run', action='store_true', dest='dryrun',
                        help='Run the script without creating files')
    parser.add_argument('-T', '--no-toc', action='store_true', dest='notoc',
                        help='Don\'t create a table of contents file')
    parser.add_argument('-s', '--suffix', action='store', dest='suffix',
                        help='file suffix (default: rst)', default='rst')
    parser.add_argument('--version', action='version',
                        version='Breathe (breathe-apidoc) %s' % __version__)
    parser.add_argument('rootpath', type=str,
                        help='The directory contains index.xml')
    args = parser.parse_args()

    if args.suffix.startswith('.'):
        args.suffix = args.suffix[1:]
    if not os.path.isdir(args.rootpath):
        print('%s is not a directory.' % args.rootpath, file=sys.stderr)
        sys.exit(1)
    if 'index.xml' not in os.listdir(args.rootpath):
        print('%s does not contain a index.xml' % args.rootpath, file=sys.stderr)
        sys.exit(1)
    if not os.path.isdir(args.destdir):
        if not args.dryrun:
            os.makedirs(args.destdir)
    args.rootpath = os.path.abspath(args.rootpath)
    recurse_tree(args)
    if not args.notoc:
        for key, value in TYPEDICT.items():
            create_modules_toc_file(key, value, args)

# So program can be started with "python -m breathe.apidoc ..."
if __name__ == "__main__":
    main()
