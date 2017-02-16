#!/usr/bin/env python
# vim: ts=4:sw=4:expandtab

# Copyright (C) 2014 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
#


"""Import translated .po files from Launchpad to Git"""

from BeautifulSoup import BeautifulSoup
from polib import pofile
from urllib import urlencode
import os
import re
import sys
import HTMLParser


# example : translations['es']['Preview'] =
# https://translations.launchpad.net/bleachbit/trunk/+pots/bleachbit/es/159/+translate
translations = {}


def read_http(url):
    import urllib2
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'lp2git')]
    return opener.open(url).read()


def parse_search_html(lang_id, msgctxt, msgid, start):
    param = urlencode({'show': 'all',
                       'search': msgid,
                       'start': start})
    url = 'https://translations.launchpad.net/bleachbit/trunk/+pots/bleachbit/%s/+translate?%s' \
        % (lang_id, param)
    print 'debug: fetch url %s ' % url
    doc = read_http(url)
    soup = BeautifulSoup(doc)
    h = HTMLParser.HTMLParser()
    for tr in soup.findAll('tr', attrs={'class': 'translation'}):
        en_div = tr.find('div', attrs={'id': re.compile("^msgset_[0-9]+_")})
        en_txt = h.unescape(en_div.text)
                            # unescape for example for "environment&#x27;s"
        en_div_id = [x[1] for x in en_div.attrs if x[0] == 'id'][0]
        en_ctxt_div = soup.findAll(
            id=en_div_id.replace('singular', 'context'))
        if en_ctxt_div:
            en_ctxt = en_ctxt_div[0].text
        else:
            en_ctxt = "none"
        for attr in tr.find('a').attrs:
            if attr[0] == 'href':
                href = attr[1]
        if not en_ctxt in translations[lang_id].keys():
            # initialize the context
            translations[lang_id][en_ctxt] = {}
        translations[lang_id][en_ctxt][en_txt] = href
    more = soup.findAll('a', attrs={'class': 'next'})
    if more:
        # more results
        ret = re.search('start=([0-9]+)', more[0]['href'])
        if ret:
            return int(ret.groups()[0])
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
    td_tr = soup.find('td', attrs={'id': 'translated_and_reviewed_by'})
    if td_tr:
        ret.append(td_tr.a.text)
    td_t = soup.find('td', attrs={'id': 'translated_by'})
    if td_t:
        ret.append(td_t.a.text)
    td_r = soup.find('td', attrs={'id': 'reviewed_by'})
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
        msgctxt_key = "none" if msgctxt is None else msgctxt
        if msgctxt_key in translations[lang_id]:
            if msgid2 in translations[lang_id][msgctxt_key]:
                url = translations[lang_id][msgctxt_key][msgid2]
                return parse_detail_html(url)
        if None == start:
            raise RuntimeError('not found "%s"' % msgid)


def get_lang_name(po, lang_id):
    """Given a pofile, return the human-readable language name"""
    # workaround inconsistent data
    if 'sr' == lang_id:
        return 'Serbian'
    if 'pl' == lang_id:
        return 'Polish'
    if 'bg' == lang_id:
        return 'Bulgarian'
    return po.metadata['Language-Team'].split('<')[0].strip()


def process_po(lang_id):
    new_fn = lang_id + '_new.po'
    old_fn = lang_id + '.po'
    po_new = pofile(new_fn)
    po_old = pofile(old_fn)
    msgids = []
    for new_entry in po_new.translated_entries():
        msgids.append([new_entry.msgctxt, new_entry.msgid])
        for old_entry in po_old.translated_entries():
            if 'translator-credits' == new_entry.msgid:
                msgids.pop()
                break
            if new_entry.msgctxt == old_entry.msgctxt and \
                new_entry.msgid == old_entry.msgid and \
                    new_entry.msgstr == old_entry.msgstr:
                msgids.pop()
                break

    if not msgids:
        print 'No changes for language %s' % lang_id
        return None

    names = []
    for (msgctxt, msgid) in msgids:
        print "looking for msgctxt '%s' msgid '%s' for lang '%s'" % \
            (msgctxt, msgid, lang_id)
        names = names + who_translated(lang_id, msgctxt, msgid)
    lang_name = get_lang_name(po_new, lang_id)
    if len(set(names)) == 1:
        author = po_new.metadata['Last-Translator']
    else:
        author = ', '.join(set(names)) + ' <multiple-authors>'
    cmd = 'git commit %s.po -m "Update %s translation thanks to %s" --author "%s" -m "[skip ci]"' % \
        (lang_id, lang_name, ', '.join(set(names)), author)
    return cmd


def download_po_files(urls):
    """Download .po files from Launchpad and prepare for Git"""
    langs = {}

    for url in urls:
        ret = re.search('-([a-z]{2,3}(_[A-Z]{2})?).po$', url, re.I)
        lang_id = ret.groups(0)[0]
        if not os.path.exists('%s.po' % lang_id):
            raise RuntimeError('file %s.po does not exist' % lang_id)

    for url in urls:
        print 'debug: downloading url %s' % url
        doc = read_http(url)
        ret = re.search('-([a-z]{2,3}(_[A-Z]{2})?).po$', url, re.I)
        lang_id = ret.groups(0)[0]
        f = file(lang_id + '_new.po', 'w')
        f.write(doc)
        f.close()
        cmd = process_po(lang_id)
        if cmd:
            langs[lang_id] = cmd

    for lang_id, cmd in langs.iteritems():
        print 'mv %s_new.po %s.po' % (lang_id, lang_id)
        os.rename('%s_new.po' % lang_id, '%s.po' % lang_id)
        print cmd
        # cmd is a Unicode, so encode to bytestring to avoid
        # UnicodeEncodeError: 'ascii' codec can't encode character u'\xf6' in position 49: ordinal not in range(128)
        os.system(cmd.encode('utf-8'))

download_po_files(sys.argv[1:])
