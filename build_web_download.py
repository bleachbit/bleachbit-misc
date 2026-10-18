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


import gzip
import os
import subprocess
import urllib.request, urllib.error, urllib.parse
import sys
import re
import traceback
import xml.etree.ElementTree as ET


# https://en.wikipedia.org/wiki/Linux_Mint_version_history
UBUNTU_TO_MINT = {
    'Ubuntu 24.04 LTS (Noble Numbat)': ['Linux Mint 22 - 22.3 (Wilma - Zena)'],
    'Ubuntu 22.04 LTS (Jammy Jellyfish)': ['Linux Mint 21 - 21.3 (Vanessa - Virginia)'],
    'Ubuntu 20.04 LTS (Focal Fossa)': ['Linux Mint 20 - 20.3 (Ulyana - Una)'],
}

DISTRO_CODE_TO_NAME = {
    'alma9': 'AlmaLinux 9',
    'centos9': 'CentOS 9 Stream',
    'ubuntu2004': 'Ubuntu 20.04 LTS (Focal Fossa)',
    'ubuntu2204': 'Ubuntu 22.04 LTS (Jammy Jellyfish)',
    'ubuntu2404': 'Ubuntu 24.04 LTS (Noble Numbat)',
    'ubuntu2510': 'Ubuntu 25.10 (Questing Quokka)',
    'ubuntu2604': 'Ubuntu 26.04 (Resolute Raccoon)',
    'debian11': 'Debian 11 (Bullseye)',
    'debian12': 'Debian 12 (Bookworm)',
    'debian13': 'Debian 13 (Trixie)',
    'opensuse156' : 'openSUSE Leap 15.6',
    'opensuse160' : 'openSUSE Leap 16.0',
}


def tag_to_distro(tag):
    """Map a package tag to a pretty distribution name"""
    if tag in DISTRO_CODE_TO_NAME:
        return DISTRO_CODE_TO_NAME[tag]
    # Auto-generate for known patterns to avoid hardcoding every version
    m = re.match(r'^fc(\d+)$', tag)
    if m:
        return f'Fedora {m.group(1)}'
    m = re.match(r'^alma(\d+)$', tag)
    if m:
        return f'AlmaLinux {m.group(1)}'
    m = re.match(r'^centos(\d+)$', tag)
    if m:
        return f'CentOS {m.group(1)} Stream'
    m = re.match(r'^opensuse(\d+)(\d)$', tag)
    if m:
        return f'openSUSE Leap {m.group(1)}.{m.group(2)}'
    raise KeyError(f"Unknown distro tag '{tag}'")

# download.opensuse.org redirects to mirrors that can lag for hours after a
# republish. downloadcontentcdn.opensuse.org fronts the origin server directly,
# so use it for fetching metadata and binaries.
OBS_REDIRECT_HOST = 'https://download.opensuse.org'
OBS_CDN_HOST = 'https://downloadcontentcdn.opensuse.org'


def url_to_distro(url: str) -> (str, str):
    """Given a URL, return the distribution and version"""
    assert url.startswith((OBS_REDIRECT_HOST, OBS_CDN_HOST)), f"not an OBS URL: {url}"
    distro_ver = url.split("/")[6]

    # Handle openSUSE Leap versions (e.g., 15.6, 16.0)
    if re.match(r'^\d+\.\d+$', distro_ver):
        return ('openSUSE', distro_ver.replace('.', ''))

    if re.match(r'CentOS_\d+_Stream', distro_ver):
        distro_ver = re.sub('_Stream$', '', distro_ver)
    if distro_ver.find('RedHat_') == 0:
        # example: RedHat_RHEL-6
        (_, distrover) = distro_ver.split("_")
        (distro, ver) = distrover.split("-")
    else:
        try:
            (distro, ver) = distro_ver.split("_")
        except ValueError:
            raise Exception(f"Unknown distro ver {distro_ver} from {url}")
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
    if distro == 'AlmaLinux':
        assert int(ver) >= 9
        return 'alma' + ver
    if distro == 'Debian':
        # unofficial
        if not (11 <= int(ver) <= 99):
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
        return tag_to_distro(tag[0])
    tag = re.findall(r"_([a-z]*[0-9]*)\.deb$", filename)
    if len(tag) == 1:
        return tag_to_distro(tag[0])

    if filename.endswith('.exe'):
        return 'Microsoft Windows'

    if filename.endswith('.AppImage'):
        return 'Linux (AppImage)'

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


def to_cdn_url(url):
    """Rewrite an OBS mirror redirect URL to the CDN origin endpoint"""
    return url.replace(OBS_REDIRECT_HOST, OBS_CDN_HOST, 1)


def fetch_bytes(url):
    """Return the raw response body for a URL"""
    return urllib.request.urlopen(url).read()


def decompress(data):
    """Decompress data by magic bytes; the CDN serves gzip or zstd variants"""
    if data[:2] == b'\x1f\x8b':
        return gzip.decompress(data)
    if data[:4] == b'\x28\xb5\x2f\xfd':
        # Lazy import: the compression package requires Python 3.14+
        from compression import zstd  # pylint: disable=import-outside-toplevel
        return zstd.decompress(data)
    return data


def get_deb_checksums(base_url):
    """Return {rel_path: ('sha256', sha256)} from a deb repository's Packages index"""
    try:
        data = fetch_bytes(base_url + 'Packages')
    except urllib.error.HTTPError:
        data = fetch_bytes(base_url + 'Packages.gz')
    data = decompress(data)
    sums = {}
    for stanza in data.decode('utf-8').split('\n\n'):
        fname = re.search(r'^Filename: (\S+)', stanza, re.MULTILINE)
        sha = re.search(r'^SHA256: ([0-9a-f]{64})', stanza, re.MULTILINE)
        if fname and sha and re.fullmatch(r'all/bleachbit[a-z0-9_.-]+\.deb', fname.group(1)):
            sums[fname.group(1)] = ('sha256', sha.group(1))
    return sums


def get_rpm_checksums(base_url):
    """Return {rel_path: (algo, hash)} from an rpm repository's repodata"""
    repo_ns = '{http://linux.duke.edu/metadata/repo}'
    common_ns = '{http://linux.duke.edu/metadata/common}'
    repomd = ET.fromstring(fetch_bytes(base_url + 'repodata/repomd.xml'))
    loc = None
    for data in repomd.findall(f'{repo_ns}data'):
        if data.get('type') == 'primary':
            loc = data.find(f'{repo_ns}location').get('href')
    assert loc, f'no primary data in {base_url}repodata/repomd.xml'
    primary = decompress(fetch_bytes(base_url + loc))
    sums = {}
    for pkg in ET.fromstring(primary).findall(f'{common_ns}package'):
        loc_el = pkg.find(f'{common_ns}location')
        cksum = pkg.find(f'{common_ns}checksum')
        if loc_el is not None and cksum is not None:
            href = loc_el.get('href', '')
            if not re.fullmatch(r'noarch/bleachbit[a-z0-9_.-]+\.rpm', href):
                continue
            algo = cksum.get('type')
            digest = (cksum.text or '').strip()
            assert algo in ('sha256', 'sha512'), f'unexpected checksum type {algo} in {base_url}'
            assert re.fullmatch(r'[0-9a-f]+', digest), f'invalid checksum {digest} in {base_url}'
            sums[href] = (algo, digest)
    return sums


def get_files_in_repo(repourl):
    """Return {fileurl: (algo, hash)} for packages in an OBS repository via CDN metadata"""
    pos = repourl.rfind("/")
    baseurl = to_cdn_url(repourl[0:pos + 1])
    if not baseurl.startswith('http'):
        raise RuntimeError(f'not a valid url {baseurl}')
    print(f"opening url '{baseurl}'")
    try:
        if repourl.find("buntu") >= 0 or repourl.find("ebian") >= 0:
            rel_sums = get_deb_checksums(baseurl)
        else:
            rel_sums = get_rpm_checksums(baseurl)
    except urllib.error.URLError as exc:
        print(exc)
        return {}
    files = {}
    for rel_path, cksum in rel_sums.items():
        fileurl = baseurl + rel_path
        print(f"found fileurl '{fileurl}'")
        files[fileurl] = cksum
    if not files:
        print(f'WARNING: no files found in {baseurl}')
    return files


def get_files_in_repos(repourls):
    """Return {fileurl: (algo, hash)} for packages across OBS repositories"""
    print("* Getting files and checksums in repos")
    files = {}
    for repourl in repourls:
        if len(repourl) < 3:
            break
        files.update(get_files_in_repo(repourl))
    print(list(files.keys()))
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
                or re.search(r'((tar.(bz2|lzma|gz)|zip|txt|txt.asc|html|sh|sig)$)', filename):
            continue
        distro = filename_to_distro(filename)
        # this url works as of 9/14/2010
        #url = "http://sourceforge.net/projects/bleachbit/files/%s" % filename
        url = f"https://download.bleachbit.org/get/{filename}"
        records.extend(add_package(distro, url, filename))

    # sort by distribution name
    import operator
    records = sorted(records, key=operator.itemgetter(0))

    # write to file
    f = open("snippet_%s.html" % (header.lower().replace(" ", "_"),), "w")
    f.write("<ul>\n")
    for (distro_txt, distro, url, filename) in records:
        f.write("<li><a rel=\"nofollow dns-prefetch\" href=\"%(url)s\">%(distro)s</a></li>\n" %
                {'url': url, 'distro': distro})

    f.write("</ul>\n")


def write_download_urls(checksum_map):
    """Build a shell script that downloads URLs, verifies checksums, and renames"""
    assert len(checksum_map) > 0
    with open('download_from_obs.sh', 'w', encoding='utf-8') as f:
        f.write('#!/bin/bash\n')
        f.write('# Download script for BleachBit packages from OBS\n')
        f.write('# Downloads via the CDN origin to avoid stale mirrors, and verifies\n')
        f.write('# each file against the checksum in the repository metadata\n\n')
        f.write('verify_checksum() {\n')
        f.write('  local algo="$1" hash="$2" fn="$3"\n')
        f.write('  echo "$hash  $fn" | "${algo}sum" --status --check -\n')
        f.write('}\n\n')
        f.write('download_file() {\n')
        f.write('  local fn="$1" url="$2" algo="$3" hash="$4"\n')
        f.write('  if [ -f "$fn" ]; then\n')
        f.write('    if verify_checksum "$algo" "$hash" "$fn"; then\n')
        f.write('      echo "Skipping $fn (exists and checksum verified)"\n')
        f.write('      return 0\n')
        f.write('    fi\n')
        f.write('    echo "Warning: existing $fn failed checksum, re-downloading"\n')
        f.write('    rm -f "$fn"\n')
        f.write('  fi\n')
        f.write('  wget -O "$fn.tmp" "$url" || {\n')
        f.write('    rc=$?\n')
        f.write('    rm -f "$fn.tmp"\n')
        f.write('    echo "Error downloading $fn: exit code $rc"\n')
        f.write('    sleep 5\n')
        f.write('    exit $rc\n')
        f.write('  }\n')
        f.write('  if ! verify_checksum "$algo" "$hash" "$fn.tmp"; then\n')
        f.write('    rm -f "$fn.tmp"\n')
        f.write('    echo "ERROR: checksum mismatch for $fn"\n')
        f.write('    echo "OBS may have republished since this script was '
                'generated; regenerate it."\n')
        f.write('    exit 1\n')
        f.write('  fi\n')
        f.write('  mv "$fn.tmp" "$fn"\n')
        f.write('  echo "Verified $fn"\n')
        f.write('}\n\n')
        for url, (algo, checksum) in checksum_map.items():
            assert url.startswith('http')
            local_fn = url_to_filename(url)
            f.write(f'download_file "{local_fn}" "{to_cdn_url(url)}" "{algo}" "{checksum}"\n\n')
        f.write('\necho "Download completed successfully"\n')


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
