#!/usr/bin/env python

from __future__ import print_function

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen
import xml.etree.ElementTree as etree

SCRIPTS_URL = "http://www.unicode.org/Public/UNIDATA/Scripts.txt"
JOININGTYPES_URL = "http://www.unicode.org/Public/UNIDATA/ArabicShaping.txt"
IDNATABLES_URL = "http://www.iana.org/assignments/idna-tables-{version}/idna-tables-{version}.xml"
IDNATABLES_NS = "http://www.iana.org/assignments"

SCRIPT_WHITELIST = sorted(['Greek', 'Han', 'Hebrew', 'Hiragana', 'Katakana'])


def print_optimised_list(d):

    codepoint_list = sorted(d)
    set_elements = []
    last_write = -1
    for i in range(0, len(codepoint_list)):
        if i+1 < len(codepoint_list):
            if codepoint_list[i] == codepoint_list[i+1]-1:
                continue
        codepoint_range = codepoint_list[last_write+1:i+1]
        if len(codepoint_range) == 1:
            set_elements.append("[{0}]".format(hex(codepoint_range[0])))
        else:
            set_elements.append("list(range({0},{1}))".format(hex(codepoint_range[0]), hex(codepoint_range[-1]+1)))
        last_write = i

    print("frozenset(")
    print("        " + " +\n        ".join(set_elements))
    print("    ),")


def build_idnadata(version):

    print("# This file is automatically generated by build-idnadata.py\n")

    #
    # Script classifications are used by some CONTEXTO rules in RFC 5891
    #
    print("scripts = {")
    scripts = {}
    for line in urlopen(SCRIPTS_URL).readlines():
        line = line.decode('utf-8')
        line = line.strip()
        if not line or line[0] == '#':
            continue
        if line.find('#'):
            line = line.split('#')[0]
        (codepoints, scriptname) = [x.strip() for x in line.split(';')]
        if not scriptname in scripts:
            scripts[scriptname] = set()
        if codepoints.find('..') > 0:
            (begin, end) = [int(x, 16) for x in codepoints.split('..')]
            for cp in range(begin, end+1):
                scripts[scriptname].add(cp)
        else:
            scripts[scriptname].add(int(codepoints, 16))

    for script in SCRIPT_WHITELIST:
        print("    '{0}':".format(script), end=' ')
        print_optimised_list(scripts[script])

    print("}")

    #
    # Joining types are used by CONTEXTJ rule A.1
    #
    print("joining_types = {")
    scripts = {}
    for line in urlopen(JOININGTYPES_URL).readlines():
        line = line.decode('utf-8')
        line = line.strip()
        if not line or line[0] == '#':
            continue
        (codepoint, name, joiningtype, group) = [x.strip() for x in line.split(';')]
        print("    {0}: '{1}',".format(hex(int(codepoint, 16)), joiningtype))
    print("}")

    #
    # These are the classification of codepoints into PVALID, CONTEXTO, CONTEXTJ, etc.
    #
    print("codepoint_classes = {")
    classes = {}

    namespace = "{{{0}}}".format(IDNATABLES_NS)
    idntables_data = urlopen(IDNATABLES_URL.format(version=version)).read()
    root = etree.fromstring(idntables_data)

    for record in root.findall('{0}registry[@id="idna-tables-properties"]/{0}record'.format(namespace)):
        codepoint = record.find("{0}codepoint".format(namespace)).text
        prop = record.find("{0}property".format(namespace)).text
        if prop in ('UNASSIGNED', 'DISALLOWED'):
            continue
        if not prop in classes:
            classes[prop] = set()
        if codepoint.find('-') > 0:
            (begin, end) = [int(x, 16) for x in codepoint.split('-')]
            for cp in range(begin, end+1):
                classes[prop].add(cp)
        else:
            classes[prop].add(int(codepoint, 16))

    for prop in classes:
        print("    '{0}':".format(prop), end=' ')
        print_optimised_list(classes[prop])

    print("}")


build_idnadata('6.3.0')

