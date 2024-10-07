#!/usr/bin/env python3
# vim: ts=4:sw=4:expandtab

# Copyright (C) 2008-2024 by Andrew Ziem.  All rights reserved.
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
import urllib.request, urllib.error, urllib.parse
import sys
import re
import traceback


# https://en.wikipedia.org/wiki/Linux_Mint_version_history
UBUNTU_TO_MINT = {
    'Ubuntu 24.04 LTS (Noble Numbat)': ['Linux Mint 22 (Wilma)'],
    'Ubuntu 22.04 LTS (Jammy Jellyfish)': ['Linux Mint 21 - 21.3 (Vanessa - Virginia)'],
    'Ubuntu 20.04 LTS (Focal Fossa)': ['Linux Mint 20 - 20.3 (Ulyana - Una)'],
    'Ubuntu 18.04 LTS (Bionic Beaver)': ['Linux Mint 19 - 19.2 (Tara - Tina)']
}

DISTRO_CODE_TO_NAME = {
    'centos9': 'CentOS 9 Stream',    
    'fc39': 'Fedora 39',
    'fc40': 'Fedora 40',        
    'ubuntu1804': 'Ubuntu 18.04 LTS (Bionic Beaver)',
    'ubuntu2004': 'Ubuntu 20.04 LTS (Focal Fossa)',
    'ubuntu2204': 'Ubuntu 22.04 LTS (Jammy Jellyfish)',
    'ubuntu2310': 'Ubuntu 23.10 (Mantic Minitaur)',
    'ubuntu2404': 'Ubuntu 24.04 LTS (Noble Numbat)',
    'ubuntu2410': 'Ubuntu 24.10 (Oracular Oriole)',    
    'debian11': 'Debian 11 (Bullseye)',
    'debian12': 'Debian 12 (Bookworm)'
}

def url_to_distro(url : str) -> (str, str):
    """Given a URL, return the distribution and version"""
    assert url.startswith('https://download.opensuse.org'), f"not an OBS URL: {url}"
    distro_ver = url.split("/")[6]
    if re.match(r'CentOS_\d+_Stream', distro_ver):
        distro_ver = re.sub('_Stream$', '', distro_ver)
    if distro_ver.find('RedHat_') == 0:
        # example: RedHat_RHEL-6
        (dummy, distrover) = distro_ver.split("_")
        (distro, ver) = distrover.split("-")
    else:
        (distro, ver) = distro_ver.split("_")        
    if distro == "xUbuntu":
        distro = "Ubuntu"
    return (distro, ver)


def make_tag(distro, ver):
    """Given a distribution, return a short suffix for the package filename"""
    ver = ver.replace(".", "")
    if distro == 'Fedora':
        # official
        return 'fc' + ver
    if distro in ('CentOS', 'Ubuntu'):
        return distro.lower() + ver
    if distro == 'Debian':
        # unofficial        
        if not ver in ('11','12'):
            raise Exception("Unknown debian ver %s" % (ver,))
        return 'debian' + ver
    if distro == 'openSUSE':
        # unofficial
        return 'opensuse' + ver    
    raise Exception("Unknown distro %s" % (distro,))



def filename_to_distro(filename):
    """Given a filename, return a pretty distribution name"""
    if 'opensuseTumbleweed' in filename:
        # example: bleachbit-3.9.0-5.1.opensuseTumbleweed.noarch.rpm
        return 'openSUSE Tumbleweed'
    if 'opensuseSlowroll' in filename:
        return 'openSUSE Slowroll'
    tag = re.findall(r"\.([a-z]*[0-9]*)\.noarch.rpm$", filename)
    if len(tag) == 1:
        return DISTRO_CODE_TO_NAME[tag[0]]
    tag = re.findall(r"_([a-z]*[0-9]*)\.deb$", filename)
    if len(tag) == 1:
        return DISTRO_CODE_TO_NAME[tag[0]]

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
    if old_fn.find("noarch") >= 0:
        return old_fn.split(".noarch")[0] + "." + tag + ".noarch.rpm"
    if old_fn.endswith(".deb"):
        return old_fn.replace(".deb", "") + "_" + tag + ".deb"
    raise Exception(f"Unexpected filename '{old_fn}'")


def get_repo_urls(osc_dir):
    """Return repository URLs returned by "osc repourls" """
    print("* Getting list of URLs")
    old_cwd = os.getcwd()
    os.chdir(osc_dir)
    repourls = subprocess.Popen(
        ["osc", "repourls"], stdout=subprocess.PIPE).communicate()[0]
    repourls_txt = repourls.decode()
    repourls = re.findall(r"https?://[^\s]+", repourls_txt)
    os.chdir(old_cwd)
    return repourls


def get_files_in_repo_sub(url):
    """Return a list of files in an OBS repository sub-directory"""
    if not url.startswith('http'):
        raise RuntimeError(f'not a valid url {url}')
    print(f"opening url '{url}'")
    try:
        dir = urllib.request.urlopen(url).read(100000)
    except:
        print(str(sys.exc_info()[1]))
        return []
    files = []
    for (file, ext) in re.findall(r"([a-z0-9_.-]+)(rpm|deb)", dir.decode()):
        fn = file + ext
        fileurl = url + fn
        print(f"found fileurl '{fileurl}'")
        files.append(fileurl)
    # make the list unique
    files = list(set(files))
    if not files:
        print(f'WARNING: no files found in {url}')
    return files


def get_files_in_repo(repourl):
    """Return a list of files in an OBS repository directory"""
    # strip off the filename
    pos = repourl.rfind("/")
    baseurl = repourl[0:pos + 1]
    if repourl.find("buntu") >= 0 or repourl.find("ebian") >= 0:
        return get_files_in_repo_sub(baseurl + "all/")
    else:
        return get_files_in_repo_sub(baseurl + "noarch/")


def get_files_in_repos(repourls):
    """Return a list of files in an OBS repository"""
    print("* Getting files in repos")
    files = []
    for repourl in repourls:
        if len(repourl) < 3:
            break
        files += get_files_in_repo(repourl)
    print(files)
    return files


def strip_tags(value):
    """Return the given HTML with all tags stripped."""
    # http://smitbones.blogspot.com/2008/01/python-strip-html-tags-function.html
    return re.sub(r'<[^>]*?>', '', value)

def add_package(distro, url, filename):
    """Add package to HTML snippet

    distro: human name of Linux distribution

    returns a list of tuples (distro_txt, distro, url, filename)
    """
    distro_txt = strip_tags(distro)  # for sorting
    ret = [(distro_txt, distro, url, filename)]
    # Users often ask for Mint packages, so for convenience provide
    # a link to the compatible Ubuntu package.
    if distro in UBUNTU_TO_MINT:
        for d in UBUNTU_TO_MINT[distro]:
            ret.append((strip_tags(d), d, url, filename))
    if 'Ubuntu' in distro and ' LTS ' in distro and len(ret) == 1:
        raise RuntimeError(f'Add {distro} to add_package()')
    return ret

def create_html_snippet(filenames, header):
    """Create an HTML snippet with links to download packages"""
    print("* Creating HTML snippet")

    # collect list of download packages
    records = []

    for filename in filenames:
        if len(filename) < 5 \
                or re.search(r'((tar.(bz2|lzma|gz)|zip|txt|txt.asc|html|sh)$)', filename):
            continue
        distro = filename_to_distro(filename)
        # this url works as of 9/14/2010
        #url = "http://sourceforge.net/projects/bleachbit/files/%s" % filename
        url = "/download/file/t?file=%s" % filename
        records.extend(add_package(distro, url, filename))

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
        assert len(urls) > 0
        for url in urls:
            assert url.startswith('http')
            local_fn = url_to_filename(url)
            cmd = 'wget -nv -nc -O %s %s' % (local_fn, url)
            f.write('%s\n' % cmd)


def main():
    if len(sys.argv) == 1:
        print('invoke with either --make-download (OSC directory) or --make-html')
        sys.exit(1)
    elif sys.argv[1] == '--make-download':
        print("getting URLs from OpenSUSE Build Service")
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
