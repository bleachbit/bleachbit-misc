#!/usr/bin/env python
# vim: ts=4:sw=4:expandtab

# Copyright (C) 2009 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
#


"""Import translated .po files from Launchpad to SVN"""

from BeautifulSoup import BeautifulSoup
from polib import pofile
from urllib import urlencode
from urllib2 import urlopen
import os
import re
import sys


# example : translations['es']['Preview'] = https://translations.launchpad.net/bleachbit/trunk/+pots/bleachbit/es/159/+translate
translations = {}

def parse_search_html(lang_id, search, start):
    param = urlencode( { 'show' : 'all', \
        'search' : search, \
        'start' : start } )
    url = 'https://translations.launchpad.net/bleachbit/trunk/+pots/bleachbit/%s/+translate?%s' \
        % (lang_id, param)
    #print 'debug: fetch url %s ' % url
    doc = urlopen(url).read()
    soup = BeautifulSoup(doc)
    for tr in soup.findAll('tr', attrs={'class': 'translation'}):
        div = tr.find('div', attrs={'id' : re.compile("^msgset_[0-9]+_")})
        english = div.text
        for attr in tr.find('a').attrs:
            if attr[0] == 'href':
                href = attr[1]
        translations[lang_id][english] = href
    ret = re.search('rel="next".*start=([0-9]+)"', doc, re.MULTILINE & re.DOTALL)
    if ret:
        # more results
        next_n = ret.groups(0)
        return int(next_n)
    else:
        # no more results
        return None


def parse_detail_html(url):
    """Parse a Launchpad page for an individual translation message"""
    print 'debug: fetch url %s ' % url
    doc = urlopen(url).read()
    soup = BeautifulSoup(doc)
    label = soup.find('label', 'no-translation')
    if label:
        raise RuntimeError('not translated')
    ret = []
    td_tr = soup.find('td', attrs = { 'id' : 'translated_and_reviewed_by' } )
    if td_tr:
        ret.append(td_tr.a.text)
    td_t = soup.find('td', attrs = { 'id' : 'translated_by' } )
    if td_t:
        ret.append(td_t.a.text)
    td_r = soup.find('td', attrs = { 'id' : 'reviewed_by' } )
    if td_r:
        ret.append(td_r.a.text)
    if 0 == len(ret):
        raise RuntimeError('translated but no translators found')
    return ret


def who_translated(lang_id, msgctxt, msgid):
    """Returns name of person who translated a particular string"""

    if not lang_id in translations.keys():
        # initialize the language
        translations[lang_id] = {}

    if msgctxt:
        raise RuntimeError('msgctxt not suppirted')

    start = 0
    while True:
        start = parse_search_html(lang_id, msgid, start)
        if translations[lang_id].has_key(msgid):
            url = translations[lang_id][msgid]
            return parse_detail_html(url)
        if None == start:
            raise RuntimeError('not found "%s"' % msgid)

def process_po(lang_id):
    new_fn = lang_id + '_new.po'
    old_fn = lang_id + '.po'
    po_new = pofile(new_fn)
    po_old = pofile(old_fn)
    msgids = []
    for new_entry in po_new.translated_entries():
        msgids.append([ new_entry.msgctxt, new_entry.msgid ])
        for old_entry in po_old.translated_entries():
            if new_entry.msgctxt == old_entry.msgctxt and \
                new_entry.msgid == old_entry.msgid and \
                new_entry.msgstr == old_entry.msgstr:
                msgids.pop()
                break
    names = []
    for (msgctxt, msgid) in msgids:
        print "looking for msgctxt '%s' msgid '%s' for lang '%s'" % \
            (msgctxt, msgid, lang_id)
        names = names + who_translated(lang_id, msgctxt, msgid)
    lang_name = po_new.metadata['Language-Team'].split('<')[0].strip()
    cmd = 'svn ci %s.po -m "Updated %s thanks to %s"' % \
        (lang_id, lang_name, ','.join(set(names)))
    print cmd
    return cmd


def download_po_files(urls):
    """Download .po files from Launchpad and prepare for SVN"""
    for url in urls:
        print 'debug: downloading url %s' % url
        doc = urlopen(url).read()
        ret = re.search('-([a-z]{2,3}(_[A-Z}{2}))', url, re.I)
        lang_id = ret.groups(0)
        f = file(lang_id + '_new.po')
        f.write(doc)
        f.close()
        process_po(lang_id)

download_po_files(sys.argv[1:])
