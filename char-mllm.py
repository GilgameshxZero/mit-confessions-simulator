import os

def toRelPath(origPath):
	"""Converts path to path relative to current script

	origPath:	path to convert
	"""
	if not hasattr(toRelPath, "__location__"):
		toRelPath.__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
	return os.path.join(toRelPath.__location__, origPath)

####end of library

import numpy
import configparser
import json

#read config
config = configparser.ConfigParser()
config.read(toRelPath("config.ini"))

data = open(toRelPath(config["char-mllm"]["model-data"])).read()
timesteps = int(config["char-mllm"]["model-timesteps"])
model = {}

dataLen = len(data)

for a in range(0, dataLen - timesteps):
	key = data[a:a + timesteps]
	value = data[a + timesteps]

	if not key in model:
		model[key] = {}
	if not value in model[key]:
		model[key][value] = 0
	model[key][value] += 1

#normalize
probModel = {}
for key in model:
	total = 0
	probModel[key] = [[], []]
	for value in model[key]:
		total += model[key][value]
	total = float(total)
	for value in model[key]:
		probModel[key][0].append(value)
		probModel[key][1].append((float)(model[key][value]) / total)

#get gen-len
genLen = input("Length of text to generate: ")
if genLen == "":
	genLen = int(config["char-mllm"]["gen-len-default"])
else:
	genLen = int(genLen)

#get random seed
seedInd = numpy.random.randint(0, dataLen - timesteps)
curGen = data[seedInd:seedInd + timesteps]
generated = ""

for a in range(0, genLen):
	dist = probModel[curGen][1]
	choice = numpy.random.choice(len(dist), p = dist)
	nextChar = probModel[curGen][0][choice]
	curGen = curGen[1:] + nextChar
	generated += nextChar

	if nextChar != "\0":
		print(nextChar, end = "")
	else:
		print("\n----------------\n", end = "")

		#the data necessitates us adding a number to the beginning
		postNum = numpy.random.randint(1, int(config["char-mllm"]["post-num-max"]))
		prefix = "#" + str(postNum) + " "
		generated += prefix
		print(prefix, end = "")

posts = generated.split("\0")
posts = posts[1:-1]

#walk through generated posts and make sure none of them match the actual posts
actualPosts = set(data.split("\0"))
postsFinal = []
samePosts = 0
for post in posts:
	if not post.split(maxsplit = 1)[1] in actualPosts:
		postsFinal.append(post)
	else:
		samePosts += 1
print("\n\nDiscarded posts:", samePosts)

#json the generated text into specified file after parsing it
with open(toRelPath(config["char-mllm"]["gen-posts-json"]), "w") as outfile:
    json.dump(postsFinal, outfile)

#print posts in plaintext for easy showcasing
f = open(toRelPath(config["char-mllm"]["gen-posts-txt"]), "w")
for post in postsFinal:
	f.write(post + "\n----------------\n")
f.close()