import os

def toRelPath(origPath):
	"""Converts path to path relative to current script

	origPath:	path to convert
	"""
	if not hasattr(toRelPath, "__location__"):
		toRelPath.__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
	return os.path.join(toRelPath.__location__, origPath)

####end of library

import numpy as np
import keras
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Dropout
from keras.layers import LSTM
from keras.layers import Lambda
from keras.callbacks import ModelCheckpoint
import configparser
import json
import sys

#read config
config = configparser.ConfigParser()
config.read(toRelPath("config.ini"))

print("Using model:", config["sample"]["gen-model"])

#get amount of characters to generate
genChars = input("Number of characters to generate: ")
if genChars == "":
	genChars = int(config["sample"]["gen-len-default"])
else:
	genChars = int(genChars)

#read in data
text = open(toRelPath(config["char-rnn"]["model-data"])).read()

#create mapping of unique chars to integers
chars = sorted(list(set(text)))
char_to_int = dict((c, i) for i, c in enumerate(chars))
int_to_char = dict((i, c) for i, c in enumerate(chars))
print("Char mapping: ", char_to_int)

#summarize the loaded data
cChrs = len(text)
cAlphabet = len(chars)
print("Text length: ", cChrs)
print("Alphabet size: ", cAlphabet)

#prepare the dataset of input to output pairs encoded as integers
#use data here
seqLen = int(config["char-rnn"]["model-timesteps"])
cPatterns = cChrs - seqLen
print("Datapoint count: ", cPatterns)

#define the LSTM model
model = Sequential()
model.add(keras.layers.GRU(512, input_shape=(seqLen, 1), return_sequences=True))
model.add(keras.layers.BatchNormalization())
model.add(keras.layers.Dropout(0.4))
model.add(keras.layers.GRU(512))
model.add(keras.layers.BatchNormalization())
model.add(keras.layers.Dropout(0.4))

#sample with temperature
model.add(Lambda(lambda x: x / float(config["sample"]["model-temp"])))

model.add(Dense(cAlphabet, activation='softmax'))

# load the network weights
model.load_weights(toRelPath(config["sample"]["gen-model"]))

# pick a random seed
generated = ""

start = np.random.randint(0, cPatterns - 1)
pattern = [char_to_int[char] for char in text[start:start + seqLen]]
print("Seed:")
print(''.join([int_to_char[value] for value in pattern]))
print("Sample: \n", end="")
# generate characters
for i in range(genChars):
	x = np.reshape(pattern, (1, len(pattern), 1))
	x = x / float(cAlphabet)
	prediction = model.predict(x, verbose=0)

	#sample from output distribution
	index = np.random.choice(len(prediction[0]), p=prediction[0])
	result = int_to_char[index]
	
	#save the generated char
	generated += result

	if result != "\0":
		print(result, end="")
	else:
		print("\n----------------\n", end="")
	sys.stdout.flush()
	pattern.append(index)
	pattern = pattern[1:len(pattern)]

print("\n\nDone.\n")

#json the generated text into specified file after parsing it
posts = generated.split("\0")
posts = posts[1:-1]
with open(toRelPath(config["char-rnn"]["gen-posts-json"]), "w") as outfile:
    json.dump(posts, outfile)

#print posts in plaintext for easy showcasing
f = open(toRelPath(config["char-rnn"]["gen-posts-txt"]), "w")
for post in posts:
	f.write(post + "\n----------------\n")
f.close()