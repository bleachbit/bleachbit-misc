#!/usr/bin/env python
# vim: ts=4:sw=4:expandtab

# Copyright (C) 2008-2015 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
#

"""
Build a list of URLs to download from OpenSUSE Build Service (OBS) and make
an HTML snippet of download links
"""


import os
import subprocess
import urllib2
import pdb
import sys
import re
import time
import traceback


def url_to_distro(url):
    """Given a URL, return the distribution and version"""
    if 'RedHat_RHEL-6' == url:
        return ('RHEL', '6')
    d = url.split("/")[6]
    if 0 == d.find('RedHat_'):
        # example: RedHat_RHEL-6
        (dummy, distrover) = d.split("_")
        (distro, ver) = distrover.split("-")
    else:
        (distro, ver) = d.split("_")
    if "xUbuntu" == distro:
        distro = "Ubuntu"
    return (distro, ver)


def make_tag(distro, ver):
    """Given a distribution, return a short suffix for the package filename"""
    ver = ver.replace(".", "")
    if 'CentOS' == distro:
        # unofficial
        return 'centos' + ver
    if 'Debian' == distro:
        # unofficial
        if ver in ('40', '4', 'Etch'):
            ver = '4'
        elif ver in ('Lenny', '5', '50'):
            ver = '5'
        elif ver in ('60'):
            ver = '6'
        elif ver in ('70'):
            ver = '7'
        elif ver in ('80'):
            ver = '8'
        else:
            raise Exception("Unknown debian ver %s" % (ver,))
        return 'debian' + ver
    if 'Fedora' == distro:
        # official
        return 'fc' + ver
    if 'Mandriva' == distro:
        # official
        return 'mdv' + ver
    if 'openSUSE' == distro:
        # unofficial
        return 'opensuse' + ver
    if 'SLES' == distro:
        # is there an official?
        return 'sles' + ver
    if 'SLE' == distro:
        # is there an official?
        return 'sle' + ver
    if 'RHEL' == distro:
        return 'el' + ver
    if 'Ubuntu' == distro:
        return 'ubuntu' + ver
    raise Exception("Unknown distro %s" % (distro,))


def filename_to_distro(filename):
    """Given a filename, return a pretty distribution name"""
    if filename.find('centosCentOS-6') > -1:
    # bleachbit-0.9.0beta-1.1.centosCentOS-6.noarch.rpm
        return 'CentOS 6'
    tag = re.findall("\.([a-z]*[0-9]*)\.noarch.rpm$", filename)
    if 1 == len(tag):
        distros = {
            'centos5': 'CentOS 5',
            'centos6': 'CentOS 6',
            'centos7': 'CentOS 7',
            'fc8': 'Fedora 8 (Werewolf)',
            'fc9': 'Fedora 9 (Sulphur)',
            'fc10': 'Fedora 10 (Cambridge)',
            'fc11': 'Fedora 11 (Leonidas)',
            'fc12': 'Fedora 12 (Constantine)',
            'fc13': 'Fedora 13 (Goddard)',
            'fc14': 'Fedora 14 (Laughlin)',
            'fc15': 'Fedora 15 (Lovelock)',
            'fc16': 'Fedora 16 (Verne)',
            'fc17': 'Fedora 17 (Beefy Miracle)',
            'fc18': 'Fedora 18 (Spherical Cow)',
            'fc19': 'Fedora 19 (Schrodinger\'s Cat)',
            'fc20': 'Fedora 20 (Heisenbug)',
            'fc21': 'Fedora 21',
            'mdv2008': 'Mandriva 2008',
            'mdv2009': 'Mandriva 2009',
            'mdv20091': 'Mandriva 2009.1',
            'mdv2010': 'Mandriva 2010',
            'mdv20101': 'Mandriva 2010.1',
            'opensuse103': 'openSUSE 10.3',
            'opensuse110': 'openSUSE 11.0',
            'opensuse111': 'openSUSE 11.1',
            'opensuse112': 'openSUSE 11.2',
            'opensuse113': 'openSUSE 11.3',
            'opensuse114': 'openSUSE 11.4',
            'opensuse121': 'openSUSE 12.1',
            'opensuse122': 'openSUSE 12.2',
            'opensuse123': 'openSUSE 12.3',
            'opensuse131': 'openSUSE 13.1',
            'opensuse132': 'openSUSE 13.2',
            'el4': '<acronym title="Red Hat Enterprise Linux">RHEL</acronym> 4',
            'el5': 'RHEL 5',
            'el6': 'RHEL 6',
            'el7': 'RHEL 7',
            'sles9': '<acronym title="SUSE Linux Enterprise Server">SLES</acronym> 9',
            'sle10': '<acronym title="SUSE Linux Enterprise">SLE</acronym> 10',
            'sle11': '<acronym title="SUSE Linux Enterprise">SLE</acronym> 11'
        }
        return distros[tag[0]]
    tag = re.findall("_([a-z]*[0-9]*)\.deb$", filename)
    if 1 == len(tag):
        distros = {
            'ubuntu606': 'Ubuntu 6.06 LTS (Dapper Drake)',
            'ubuntu710': 'Ubuntu 7.10 (Feisty Fawn)',
            'ubuntu804': 'Ubuntu 8.04 LTS (Hardy Heron)',
            'ubuntu810': 'Ubuntu 8.10 (Intrepid Ibex)',
            'ubuntu904': 'Ubuntu 9.04 (Jaunty Jackalope)',
            'ubuntu910': 'Ubuntu 9.10 (Karmic Koala)',
            'ubuntu1004': 'Ubuntu 10.04 LTS (Lucid Lynx)',
            'ubuntu1010': 'Ubuntu 10.10 (Maverick Meerkat)',
            'ubuntu1104': 'Ubuntu 11.04 (Natty Narwhal)',
            'ubuntu1110': 'Ubuntu 11.10 (Oneiric Ocelot)',
            'ubuntu1204': 'Ubuntu 12.04 (Precise Pangolin)',
            'ubuntu1210': 'Ubuntu 12.10 (Quantal Quetzal)',
            'ubuntu1304': 'Ubuntu 13.04 (Raring Ringtail)',
            'ubuntu1310': 'Ubuntu 13.10 (Saucy Salamander)',
            'ubuntu1404': 'Ubuntu 14.04 LTS (Trusty Tahr)',
            'ubuntu1410': 'Ubuntu 14.10 (Utopic Unicorn)',
            'ubuntu1504': 'Ubuntu 15.04 (Vivid Vervet)',
            'debian4': 'Debian 4 (Etch)',
            'debian5': 'Debian 5 (Lenny)',
            'debian6': 'Debian 6 (Squeeze)',
            'debian7': 'Debian 7 (Wheezy)',
            'debian8': 'Debian 8 (Jessie)'
        }
        return distros[tag[0]]

    if filename.endswith('.exe'):
        return 'Microsoft Windows'

    raise Exception("unknown distro for '%s'" % filename)


def url_to_filename(url):
    """Given a URL of a package on OBS, return a filename that adds the distribution"""
    (distro, ver) = url_to_distro(url)
    try:
        tag = make_tag(distro, ver)
    except:
        traceback.print_exc()
        sys.stderr.flush()
        sys.stderr.write(
            "url = '%s', distro = '%s', ver=%s\n" % (url, distro, ver))
        raise
    # print "distro = '%s', ver = '%s', tag = '%s', url = '%s'" % (distro,
    # ver, tag, url[57:])
    old_fn = url[url.rfind("/") + 1:]
    if 0 <= old_fn.find("noarch"):
        return old_fn.split(".noarch")[0] + "." + tag + ".noarch.rpm"
    if old_fn.endswith(".deb"):
        return old_fn.replace(".deb", "") + "_" + tag + ".deb"
    raise Exception("Unexpected filename '%s'" % (old_fn,))


def process_url(url):
    fn = url_to_filename(url)
    print ("wget -nv -nc -O %s %s" % (fn, url))


def get_repo_urls(osc_dir):
    """Return repository URLs returned by "osc repourls" """
    print "* Getting list of URLs"
    old_cwd = os.getcwd()
    os.chdir(osc_dir)
    repourls = subprocess.Popen(
        ["osc", "repourls"], stdout=subprocess.PIPE).communicate()[0]
    repourls = repourls.split("\n")
    os.chdir(old_cwd)
    return repourls


def get_files_in_repo_sub(url):
    """Return a list of files in an OBS repository sub-directory"""
    print "opening url '%s'" % (url,)
    try:
        dir = urllib2.urlopen(url).read(100000)
    except:
        print str(sys.exc_info()[1])
        return []
    files = []
    for (file, ext) in re.findall('"([a-z0-9_.-]*)(rpm|deb)"', dir):
        fn = file + ext
        fileurl = url + fn
        print "found fileurl '%s'" % (fileurl,)
        files.append(fileurl)
    return files


def get_files_in_repo(repourl):
    """Return a list of files in an OBS repository directory"""
    # strip off the filename
    pos = repourl.rfind("/")
    baseurl = repourl[0:pos + 1]
    if 0 <= repourl.find("buntu") or 0 <= repourl.find("ebian"):
        # files = []
        # for file in get_files_in_repo_sub(baseurl + "i386/"):
        #    files.append(file)
        # for file in get_files_in_repo_sub(baseurl + "amd64/"):
        #    files.append(file)
        # return files
        return get_files_in_repo_sub(baseurl + "all/")
    else:
        return get_files_in_repo_sub(baseurl + "noarch/")


def get_files_in_repos(repourls):
    """Return a list of files in an OBS repository"""
    print "* Getting files in repos"
    files = []
    for repourl in repourls:
        if len(repourl) < 3:
            break
        files += get_files_in_repo(repourl)
    print files
    return files


def distro_to_target(distro):
    if distro.startswith("Fedora") or distro.startswith("Cent") or distro.startswith("RHEL"):
        return "/etc/yum.repos.d/"
    return ""


def strip_tags(value):
    """Return the given HTML with all tags stripped."""
    # http://smitbones.blogspot.com/2008/01/python-strip-html-tags-function.html
    return re.sub(r'<[^>]*?>', '', value)


def create_html_snippet(filenames, header):
    """Create an HTML snippet with links to download packages"""
    print "* Creating HTML snippet"
    f = open("snippet_%s.html" % (header.lower().replace(" ", "_"),), "w")
    f.write("<ul>\n")
    target = 0 <= header.find("epo")
    records = []
    for filename in filenames:
        if len(filename) < 5 \
                or re.search('(bonus|(tar.(bz2|lzma|gz)|zip|txt|txt.asc|html)$)', filename):
            continue
        distro = filename_to_distro(filename)
        # this url works as of 9/14/2010
        url = "http://sourceforge.net/projects/bleachbit/files/%s" % filename

        distro_txt = strip_tags(distro)
        records.append((distro_txt, distro, url, filename))


#    print records
    import operator
#    records = sorted(records, key=map(operator.itemgetter(0), records))
    records = sorted(records, key=operator.itemgetter(0))
#    print records

    for (distro_txt, distro, url, filename) in records:
        f.write("<li><a rel=\"external nofollow\" href=\"%(url)s\">%(distro)s</a></li>\n" %
                {'url': url, 'distro': distro})

    f.write("</ul>\n")


def dump_file_urls(fileurls):
    """Dump URLs to a file"""
    print "* Dumping file URLs"
    f = open("file_urls.txt", "w")
    for url in fileurls:
        f.write("%s\n" % (url,))


def main():
    import sys
    if len(sys.argv) == 1:
        print 'invoke with either --get-urls or --make-html'
        sys.exit(1)
    elif sys.argv[1] == '--get-urls':
        print "getting URLs"
        repourls = get_repo_urls(sys.argv[2])
        fileurls = get_files_in_repos(repourls)
        dump_file_urls(fileurls)
    elif sys.argv[1] == '--make-html':
        filenames = sorted(os.listdir('files'))
        create_html_snippet(filenames, "Installation package")
    else:
        raise RuntimeError('Unknown command line' + sys.argv[1])


if __name__ == '__main__':
    main()
