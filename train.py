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
import configparser
import json

#read config
config = configparser.ConfigParser()
config.read(toRelPath("config.ini"))

#get model name from input
modelName = input("Name this model: ")

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
dataX = []
dataY = []
for i in range(0, cChrs - seqLen):
	seq_in = text[i:i + seqLen]
	seq_out = text[i + seqLen]
	dataX.append([char_to_int[char] for char in seq_in])
	dataY.append(char_to_int[seq_out])
cPatterns = len(dataX)
print("Datapoint count: ", cPatterns)

#reshape X to be [samples, time steps, features]
X = np.reshape(dataX, (cPatterns, seqLen, 1))
#normalize
X = X / float(cAlphabet)
#one hot encode the output variable
#char-RNN uses one-hot as well
Y = keras.utils.to_categorical(dataY)

#define the LSTM model
model = keras.models.Sequential()
model.add(keras.layers.GRU(512, input_shape=(X.shape[1], X.shape[2]), return_sequences=True))
model.add(keras.layers.BatchNormalization())
model.add(keras.layers.Dropout(0.4))
model.add(keras.layers.GRU(512))
model.add(keras.layers.BatchNormalization())
model.add(keras.layers.Dropout(0.4))

#do not train with temperature
#model.add(keras.layers.Lambda(lambda x: x / float(config["common"]["model-temp"])))

model.add(keras.layers.Dense(Y.shape[1], activation='softmax'))

optimizer = keras.optimizers.adam(lr=0.0003)
model.compile(loss='categorical_crossentropy', optimizer=optimizer, metrics=['accuracy'])

#define the checkpoint
filepath=toRelPath(config["train"]["train-models"] + modelName + "-{epoch}-{loss:.3f}-{val_loss:.3f}.hdf5")
checkpoint = keras.callbacks.ModelCheckpoint(filepath, monitor='loss', verbose=1, mode='min')

#check if a checkpoint is specified to continue from
epochStart = 0
if config["train"]["train-resume"] != "":
	model.load_weights(toRelPath(config["train"]["train-resume"]))
	epochStart = int(config["train"]["train-resume-epoch"])

#fit the model
model.fit(X, Y, epochs=int(config["train"]["train-epochs"]), batch_size=int(config["train"]["train-batch-size"]), callbacks=[checkpoint], initial_epoch=epochStart, validation_split=0.1)