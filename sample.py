import textgenrnn
import configparser

# parse configuration
config = configparser.ConfigParser()
config.read("config.ini")
config = config["sample"]

model_name = config["model"]
model = textgenrnn.textgenrnn(weights_path=model_name + "-weights.hdf5",
                              vocab_path=model_name + "-vocab.json",
                              config_path=model_name + "-config.json")

# for each temperature between 0 and 1, with 0.01 step, generate 25 sample confessions and store them into a text file
with open("cache/sample.txt", "w", encoding="utf-8") as outfile:
    for a in range(0, 101):
        temperature = a / 100
        posts = model.generate(n=5, return_as_list=True,
                               temperature=temperature, max_gen_length=300, progress=False)
        print("--------")
        print("Temperature:", temperature)
        outfile.write("--------\nTemperature:" + str(temperature) + "\n")
        for b in range(len(posts)):
            post = posts[b].encode("ascii").decode("unicode-escape")
            print(post)
            outfile.write(post + "\n")
