#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim: ts=4:sw=4:expandtab
#
#
# Copyright (C) 2018 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
"""

Download avatars

Based on:
https://code.google.com/p/gource/wiki/GravatarExample
https://gist.github.com/macagua/5c2f5e4e38df92aae7fe
https://gist.github.com/openp2pdesign/15db406825a4b35783e2

Usage with Gource: gource --user-image-dir .git/avatar/
 
Get list of authors + email with git log
git log --format='%aN|%aE' | sort -u

Get list of authors + email with hg log (todo)
hg log --template 'author: {author}\n'
"""


import requests
import getpass
import os
import subprocess
import hashlib
from time import sleep
import sys

username = ""
password = ""

work_dir = os.path.expandvars('~/tmp/gource')
avatar_dir = os.path.join(work_dir, 'avatar')
committer_filename = os.path.join(work_dir, 'committer2')


def md5_hex(text):
  m = hashlib.md5()
  m.update(text.encode('ascii', errors='ignore'))
  return m.hexdigest()


def get_data(api_request):
  global username
  global password

  r = requests.get(api_request, auth=(username, password))
  data = r.json()

  if "message" in data.keys():
    print data['message']
    if data['message'] == 'Must specify two-factor authentication OTP code.':
        sys.exit(1)
    # Countdown
    # http://stackoverflow.com/questions/3249524/print-in-one-line-dynamically-python
    for k in range(1, 60 * 15):
      remaining = 60 * 15 - k
      sys.stdout.write("\r%d seconds remaining   " % remaining)
      sys.stdout.flush()
      sleep(1)
    sys.stdout.write("\n")
    # Another request
    r = requests.get(api_request, auth=(username, password))
    data = r.json()
  else:
    pass

  # Return data
  return data

if __name__ == "__main__":
  print 'starting'
  global username
  global password

  # Clear screen
  #os.system('cls' if os.name == 'nt' else 'clear')

  # Login to the GitHub API
  username = raw_input("Enter your GitHub username: ")
  password = getpass.getpass("Enter your GitHub password: ")

  # Create the folder for storing the images. It's in the .git folder, so it won't be tracked by git
  output_dir = os.path.expanduser(avatar_dir)
  if not os.path.exists(output_dir):
    os.makedirs(output_dir)

  # Get the authors from the Git log
  committer_filename = os.path.expanduser(log_path)
  print 'Committer filename', committer_filename
  authors = []
  with open(committer_filename) as cf:
    for line in cf:
        authors.append(line.replace('\n',''))
  print ""
  print "USERS:"
  print(authors)

  # Check each author
  for author in authors:
    # Get e-mail and name from log
    email, name = author.split('|')
    print ""
    print "Checking", name, email
    # Try to find the user on GitHub with the e-mail
    api_request = "https://api.github.com/search/users?utf8=%E2%9C%93&q=" + \
        email + "+in%3Aemail&type=Users"
    data = get_data(api_request)

    # Check if the user was found
    if "items" in data.keys():
      if len(data["items"]) == 1:
        url = data["items"][0]["avatar_url"]
        print "Avatar url:", url
      else:
        # Try to find the user on GitHub with the name
        api_request = "https://api.github.com/search/users?utf8=%E2%9C%93&q=" + \
            name + "+in%3Aname&type=Users"
        data = get_data(api_request)

        # Check if the user was found
        if "items" in data.keys():
          if len(data["items"]) == 1:
            url = data["items"][0]["avatar_url"]
            print "Avatar url:", url
          # Eventually try to find the user with Gravatar
          else:
            # d=404 returns no file if user not found
            url = "http://www.gravatar.com/avatar/" + \
                md5_hex(email) + "?d=404&s=" + str(90)
            print "Avatar url:", url

    # Finally retrieve the image
    try:
      output_file = os.path.join(output_dir, name + '.png')
      if not os.path.exists(output_file):
        r = requests.get(url)
        if r.ok:
          with open(output_file, 'wb') as img:
            img.write(r.content)
    except:
      print "There was an error with", name, email
