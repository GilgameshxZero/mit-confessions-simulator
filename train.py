import configparser
import json
import textgenrnn
import tensorflow as tf

# parse configuration
config = configparser.ConfigParser()
config.read("config.ini")
config = config["train"]

# proportion of all datapoints to use to train + validate network; useful for testing network on small dataset
DATA_PROPORTION = float(config["data-prop"])

# proportion of all datapoints to use for training; the rest is used for validation
TRAIN_PROPORTION = float(config["train-prop"])

# length of inputs to RNN while training; maximum memory of the RNN
INPUT_LEN = int(config["input-len"])

# batch size during training
BATCH_SIZE = int(config["batch-size"])

# epochs to train for
TRAIN_EPOCHS = int(config["train-epochs"])

SAVE_EPOCHS = int(config["save-epochs"])
RNN_LAYERS = int(config["rnn-layers"])
RNN_NODES = int(config["rnn-nodes"])
EMBEDDINGS = int(config["embeddings"])

# memory settings
MEMORY_PROPORTION = float(config["memory-prop"])
MEMORY_GROWTH = (config["memory-growth"] == "true")

# set memory usage limits
config = tf.compat.v1.ConfigProto()
config.gpu_options.per_process_gpu_memory_fraction = MEMORY_PROPORTION
config.gpu_options.allow_growth = True
session = tf.compat.v1.Session(config=config)

# load scraped data
with open("assets/confessions.json", "r") as infile:
    data = json.loads(infile.read())

# summarize data and create vocabulary
texts = []
for key, value in data.items():
    # add the unicode escaped string and train on that to avoid a large vocab of emojis
    texts.append(value["text"]
                 .replace("‘", "'")
                 .replace("’", "'")
                 .replace("“", "\"")
                 .replace("”", "\"")
                 .encode("unicode-escape")
                 .decode("ascii"))

print("Using", DATA_PROPORTION, "of all", len(texts), "datapoints.")
texts = texts[:int(DATA_PROPORTION * len(texts))]

model = textgenrnn.textgenrnn(
    name="cache/" + str(INPUT_LEN) + "-" + str(EMBEDDINGS) +
    "-" + str(RNN_LAYERS) + "-" + str(RNN_NODES)
)
model.train_on_texts(
    texts,
    num_epochs=TRAIN_EPOCHS,
    batch_size=BATCH_SIZE,
    train_size=TRAIN_PROPORTION,
    save_epochs=SAVE_EPOCHS,
    gen_epochs=SAVE_EPOCHS * 16,
    new_model=True,
    max_length=INPUT_LEN,
    rnn_layers=RNN_LAYERS,
    rnn_size=RNN_NODES,
    dim_embeddings=EMBEDDINGS
)
print(model.model.summary())
session.close()
