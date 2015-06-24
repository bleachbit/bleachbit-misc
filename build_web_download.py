#!/usr/bin/env python
# vim: ts=4:sw=4:expandtab

# Copyright (C) 2008-2015 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
#

"""
Build a shell script to download packages from OpenSUSE Build Service (OBS) and make
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
        if ver in ('60'):
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
    if 'openSUSE' == distro:
        # unofficial
        return 'opensuse' + ver
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
            'centos6': 'CentOS 6',
            'centos7': 'CentOS 7',
            'fc20': 'Fedora 20 (Heisenbug)',
            'fc21': 'Fedora 21',
            'opensuse131': 'openSUSE 13.1',
            'opensuse132': 'openSUSE 13.2',
            'el6': 'RHEL 6',
            'el7': 'RHEL 7',
            'sle11': '<acronym title="SUSE Linux Enterprise">SLE</acronym> 11'
        }
        return distros[tag[0]]
    tag = re.findall("_([a-z]*[0-9]*)\.deb$", filename)
    if 1 == len(tag):
        distros = {
            'ubuntu1204': 'Ubuntu 12.04 (Precise Pangolin)',
            'ubuntu1404': 'Ubuntu 14.04 LTS (Trusty Tahr)',
            'ubuntu1410': 'Ubuntu 14.10 (Utopic Unicorn)',
            'ubuntu1504': 'Ubuntu 15.04 (Vivid Vervet)',
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
    old_fn = url[url.rfind("/") + 1:]
    if 0 <= old_fn.find("noarch"):
        return old_fn.split(".noarch")[0] + "." + tag + ".noarch.rpm"
    if old_fn.endswith(".deb"):
        return old_fn.replace(".deb", "") + "_" + tag + ".deb"
    raise Exception("Unexpected filename '%s'" % (old_fn,))


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


def strip_tags(value):
    """Return the given HTML with all tags stripped."""
    # http://smitbones.blogspot.com/2008/01/python-strip-html-tags-function.html
    return re.sub(r'<[^>]*?>', '', value)


def create_html_snippet(filenames, header):
    """Create an HTML snippet with links to download packages"""
    print "* Creating HTML snippet"

    # collect list of download packages
    records = []

    def add_package(distro, url, filename):
        distro_txt = strip_tags(distro) # for sorting
        records.append((distro_txt, distro, url, filename))
        if distro == 'Ubuntu 14.04 LTS (Trusty Tahr)':
            # Users often ask for Mint packages, so for convenience provide
            # a link to the compatible Ubuntu package.
            # Linux Mint 17 is based off of Ubuntu Trusty
            # http://www.linuxmint.com/oldreleases.php
            distro = distro_txt = 'Linux Mint 17 (Qiana/Rebecca/Rafaela)'
            records.append((distro_txt, distro, url, filename))

    for filename in filenames:
        if len(filename) < 5 \
                or re.search('(bonus|(tar.(bz2|lzma|gz)|zip|txt|txt.asc|html)$)', filename):
            continue
        distro = filename_to_distro(filename)
        # this url works as of 9/14/2010
        url = "http://sourceforge.net/projects/bleachbit/files/%s" % filename
        add_package(distro, url, filename)

    # sort by distribution name
    import operator
    records = sorted(records, key=operator.itemgetter(0))

    # write to file
    f = open("snippet_%s.html" % (header.lower().replace(" ", "_"),), "w")
    f.write("<ul>\n")
    for (distro_txt, distro, url, filename) in records:
        f.write("<li><a rel=\"external nofollow\" href=\"%(url)s\">%(distro)s</a></li>\n" %
                {'url': url, 'distro': distro})

    f.write("</ul>\n")


def write_download_urls(urls):
    """"Build a shell script that downloads URLs and renames the files"""
    with open('download_from_obs.sh', 'w') as f:
        for url in urls:
            local_fn = url_to_filename(url)
            cmd = 'wget -nv -nc -O %s %s' % (local_fn, url)
            f.write('%s\n' % cmd)


def main():
    import sys
    if len(sys.argv) == 1:
        print 'invoke with either --make-download (OSC directory) or --make-html'
        sys.exit(1)
    elif sys.argv[1] == '--make-download':
        print "getting URLs from OpenSUSE Build Service"
        repourls = get_repo_urls(sys.argv[2])
        fileurls = get_files_in_repos(repourls)
        write_download_urls(fileurls)
    elif sys.argv[1] == '--make-html':
        filenames = sorted(os.listdir('files'))
        create_html_snippet(filenames, "Installation package")
    else:
        raise RuntimeError('Unknown command line' + sys.argv[1])


if __name__ == '__main__':
    main()
