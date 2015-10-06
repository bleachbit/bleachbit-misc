#!/usr/bin/python2

# Looks up all three letter iso 639-3 langcodes either given as argument or
# in all installed locales

from urllib2 import urlopen
from sys import argv
from os import listdir, path

langcodes = argv[1:] or [dir for dir in listdir('/usr/share/locale') if len(dir) == 3]

if not langcodes:
	print('Nothing to do...')
	exit(0)

response = urlopen('http://www-01.sil.org/iso639-3/iso-639-3_Name_Index.tab')
rows = (line.split('\t') for line in response.read().splitlines())
langdict = {cell[0] : cell[1] for cell in rows}

for langcode in langcodes:
	langname = langdict[langcode]
	if not langname:
		print('Unknown code '+langcode)
	else:
		print("'{}': '{}',".format(langcode, langname))
