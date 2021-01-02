#!/usr/bin/env python3
# vim: ts=4:sw=4:expandtab

# Copyright (C) 2014-2019 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
#


"""Import translated .po files from Launchpad to Git"""

from bs4 import BeautifulSoup
from polib import pofile
from urllib.parse import urlencode
import os
import re
import sys


# example : translations['es']['Preview'] =
# https://translations.launchpad.net/bleachbit/trunk/+pots/bleachbit/es/159/+translate
translations = {}


def read_http(url):
    from urllib.request import build_opener
    opener = build_opener()
    opener.addheaders = [('User-agent', 'lp2git')]
    return opener.open(url).read().decode()


def parse_search_html(lang_id, msgid, start):
    """
    Query Launchpad for a message, and add its URL to the
    global dictionary.

    Parameters
    ----------
    lang_id: language code such as en_GB
    msgid: message (i.e.g, English string)
    start: index for pagination

    Returns
    -------
    integer: value of start indicating to get more results
    None: there are no more search results
    """
    param = urlencode({'show': 'all',
                       'search': msgid,
                       'start': start})
    url = 'https://translations.launchpad.net/bleachbit/trunk/+pots/bleachbit/%s/+translate?%s' \
        % (lang_id, param)
    print ('debug: fetch url %s ' % url)
    doc = read_http(url)
    soup = BeautifulSoup(doc, features="lxml")
    for tr in soup.findAll('tr', attrs={'class': 'translation'}):
        # en_div: div element that contains the English translation
        en_div = tr.find('div', attrs={'id': re.compile("^msgset_[0-9]+_")})
        if not en_div:
            continue
        from html import unescape
        # en_txt: English version of the message (i.e., untranslated)
        # unescape for example for "environment&#x27;s"
        en_txt = unescape(en_div.text)
        en_div_id = en_div.attrs['id']
        en_ctxt_div = soup.findAll(
            id=en_div_id.replace('singular', 'context'))
        if en_ctxt_div:
            # Specific (i.e., non-default) context of the message.
            en_ctxt = en_ctxt_div[0].text
        else:
            # Default context. This is the most common.
            en_ctxt = "none"
        if not tr.find('a'):
            continue
        # href: link to page with just one message
        href = tr.find('a').attrs['href']
        if not en_ctxt in translations[lang_id].keys():
            # initialize the context
            translations[lang_id][en_ctxt] = {}
        translations[lang_id][en_ctxt][en_txt] = href
        del href
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
    print ('debug: fetch url %s ' % url)
    doc = read_http(url)
    soup = BeautifulSoup(doc, features="lxml")
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
        start = parse_search_html(lang_id, msgid, start)
        msgctxt_key = "none" if msgctxt is None else msgctxt
        if msgctxt_key in translations[lang_id]:
            if msgid in translations[lang_id][msgctxt_key]:
                url = translations[lang_id][msgctxt_key][msgid]
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
    if 'id' == lang_id:
        return 'Indonesian'
    return po.metadata['Language-Team'].split('<')[0].strip()


def process_po(lang_id):
    new_fn = lang_id + '_new.po'
    old_fn = lang_id + '.po'
    po_new = pofile(new_fn)
    po_old = pofile(old_fn)
    msgids = []
    # Build list of new messages
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

    print('Count of new messages:', len(msgids))

    if not msgids:
        print ('No changes for language %s' % lang_id)
        return None

    names = []
    for (msgctxt, msgid) in msgids:
        print ("looking for msgctxt '%s' msgid '%s' for lang '%s'" % \
            (msgctxt, msgid, lang_id))
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
        print ('debug: downloading url %s' % url)
        doc = read_http(url)
        ret = re.search('-([a-z]{2,3}(_[A-Z]{2})?).po$', url, re.I)
        lang_id = ret.groups(0)[0]
        with open(lang_id + '_new.po', 'w') as f:
            f.write(doc)
        cmd = process_po(lang_id)
        if cmd:
            langs[lang_id] = cmd

    for lang_id, cmd in langs.items():
        print ('mv %s_new.po %s.po' % (lang_id, lang_id))
        os.rename('%s_new.po' % lang_id, '%s.po' % lang_id)
        print (cmd)
        # cmd is a Unicode, so encode to bytestring to avoid
        # UnicodeEncodeError: 'ascii' codec can't encode character u'\xf6' in position 49: ordinal not in range(128)
        os.system(cmd.encode('utf-8'))

def go():
    """Main program"""
    download_po_files(sys.argv[1:])

if __name__ == '__main__':
    go()
