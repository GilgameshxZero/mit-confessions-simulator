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
import re

#read config
config = configparser.ConfigParser()
config.read(toRelPath("config.ini"))

#get input for which config set to use
configSet = input("Configuration set to use: ")
if configSet == "":
	configSet = config["fetch"]["default-config"]
if not configSet in config.sections():
	print("Configuration set does not exist. Exiting...")
	exit()

#read in data
uniqueChars = set()

data = json.loads(open(toRelPath(config[configSet]["fetch-dump"])).read())
dataNew = []
for post in data:
	#if text doesn't start with #, just discard it
	if post["text"][0] != "#":
		continue

	#save the original text
	post["orig-text"] = post["text"]

	post["src"] = configSet
	if post["utime"].isdigit():
		post["utime"] = int(post["utime"])

	#process text for training
	#standardize to space after #
	#particularily a problem for MIT Confessions data
	ispl = post["text"].split(maxsplit=1)
	firstIspl = len(ispl[0])
	if post["text"][firstIspl] == "\n":
		post["text"] = post["text"][0:firstIspl] + " " + post["text"][firstIspl + 1:]
		if post["text"][firstIspl + 1] == "\"" and post["text"][-2] == "\"":
			post["text"] = post["text"][0:firstIspl + 1] + post["text"][firstIspl + 2:-2] + post["text"][-1:]

	#lowercase
	post["text"] = post["text"].lower()

	#restrict alphabet
	post["text"] = re.sub("[^a-z \n\'\.,?!0-9@#<>/:;\-\"()]", "", post["text"])

	#modify text even further in a new field by removing the number
	ispl = post["text"].split(maxsplit = 1)
	idn = ispl[0][1:]

	#these are also conditions for a valid confession
	if (not idn.isdigit()) or (ispl[0][0] != "#"):
		continue
	
	post["id"] = int(idn)
	post["nr-text"] = ispl[1]

	#add post to a new structure which we will save
	dataNew.append(post)

	#display processed text
	uniqueChars = uniqueChars.union(set(post["text"]))
	print(post["orig-text"], end = "")
	print(post["text"])

print("Unique characters: ", list(uniqueChars))
print("Count: ", len(uniqueChars))

with open(toRelPath(config[configSet]["parsed-posts"]), "w") as outfile:
    json.dump(dataNew, outfile)