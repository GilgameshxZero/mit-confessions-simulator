import os

def toRelPath(origPath):
	"""Converts path to path relative to current script

	origPath:	path to convert
	"""
	if not hasattr(toRelPath, "__location__"):
		toRelPath.__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
	return os.path.join(toRelPath.__location__, origPath)

####end of rain library

import configparser
import json
import random

#read config
config = configparser.ConfigParser()
config.read(toRelPath("config.ini"))

#read in data
srcs = config["concatenate"]["concat-srcs"].split()
clist = []
nrlist = []
for src in srcs:
	data = json.loads(open(toRelPath(config[src]["parsed-posts"])).read())
	for post in data:
		#\0 is special end character
		clist.append(post["text"] + "\0")
		nrlist.append(post["nr-text"] + "\0")

#scramble confessions
random.shuffle(clist)
random.shuffle(nrlist)

f = open(toRelPath(config["concatenate"]["concat-full-out"]), "w")
f.write("".join(clist))
f.close()

f = open(toRelPath(config["concatenate"]["concat-nr-out"]), "w")
f.write("".join(nrlist))
f.close()