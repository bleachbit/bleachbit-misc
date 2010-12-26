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
import os
import re
import sys


# example : translations['es']['Preview'] = https://translations.launchpad.net/bleachbit/trunk/+pots/bleachbit/es/159/+translate
translations = {}


def read_http(url):
    import urllib2
    opener = urllib2.build_opener()
    opener.addheaders = [ ('User-agent', 'lp2svn') ]
    return opener.open(url).read()

def parse_search_html(lang_id, msgctxt, msgid, start):
    param = urlencode( { 'show' : 'all', \
        'search' : msgid, \
        'start' : start } )
    url = 'https://translations.launchpad.net/bleachbit/trunk/+pots/bleachbit/%s/+translate?%s' \
        % (lang_id, param)
    print 'debug: fetch url %s ' % url
    doc = read_http(url)
    soup = BeautifulSoup(doc)
    for tr in soup.findAll('tr', attrs={'class': 'translation'}):
        en_div = tr.find('div', attrs={'id' : re.compile("^msgset_[0-9]+_")})
        en_txt = en_div.text
        en_div_id = [x[1] for x in en_div.attrs if x[0]=='id'][0]
        en_ctxt_div = soup.findAll(id = en_div_id.replace('singular', 'context'))
        if en_ctxt_div:
            en_ctxt = en_ctxt_div[0].text
        else:
            en_ctxt = "none"
        for attr in tr.find('a').attrs:
            if attr[0] == 'href':
                href = attr[1]
        if not en_ctxt  in translations[lang_id].keys():
            # initialize the context
            translations[lang_id][en_ctxt] = {}
        translations[lang_id][en_ctxt][en_txt] = href
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
    doc = read_http(url)
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

    start = 0
    while True:
        start = parse_search_html(lang_id, msgctxt, msgid, start)
        msgid2 = msgid.replace('\n', '').rstrip()
        msgctxt_key = "none" if msgctxt == None else msgctxt
        if translations[lang_id].has_key(msgctxt_key):
            if translations[lang_id][msgctxt_key].has_key(msgid2):
                url = translations[lang_id][msgctxt_key][msgid2]
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
            if 'translator-credits' == new_entry.msgid:
                msgids.pop()
                break
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
    cmd = 'svn ci %s.po -m "Update %s thanks to %s"' % \
        (lang_id, lang_name, ', '.join(set(names)))
    return cmd


def download_po_files(urls):
    """Download .po files from Launchpad and prepare for SVN"""
    langs = {}
    for url in urls:
        print 'debug: downloading url %s' % url
        doc = read_http(url)
        ret = re.search('-([a-z]{2,3}(_[A-Z]{2})?).po$', url, re.I)
        lang_id = ret.groups(0)[0]
        f = file(lang_id + '_new.po', 'w')
        f.write(doc)
        f.close()
        cmd = process_po(lang_id)
        langs[lang_id] = cmd

    for lang_id, cmd in langs.iteritems():
        print 'mv %s_new.po %s.po' % (lang_id, lang_id)
        print cmd

download_po_files(sys.argv[1:])
