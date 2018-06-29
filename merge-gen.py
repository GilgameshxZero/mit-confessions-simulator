import os

def toRelPath(origPath):
	"""Converts path to path relative to current script

	origPath:	path to convert
	"""
	if not hasattr(toRelPath, "__location__"):
		toRelPath.__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
	return os.path.join(toRelPath.__location__, origPath)

####end of library

import random
import configparser
import json

#read config
config = configparser.ConfigParser()
config.read(toRelPath("config.ini"))

#read in data
srcs = config["merge-gen"]["merge-srcs"].split()
posts = []
for src in srcs:
	data = json.loads(open(toRelPath(config[src]["gen-posts-json"])).read())
	posts.extend(data)

#randomize and output
random.shuffle(posts)

with open(toRelPath(config["merge-gen"]["merge-out"]), "w") as outfile:
    json.dump(posts, outfile)