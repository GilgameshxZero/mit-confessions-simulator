import configparser
import selenium
from selenium import webdriver
import time
import requests
import traceback
import textgenrnn
import zipfile
import io

# parse configuration
config = configparser.ConfigParser()
config.read("config.ini")
config = config["post"]

# download chromedriver
try:
    request = requests.get(config["chromedriver"])
    file = zipfile.ZipFile(io.BytesIO(request.content))
    file.extractall("cache/")
    file.close()
except:
    traceback.print_exc()
    print("Exception while extracting downloaded chromedriver...")

model_name = config["model"]
model = textgenrnn.textgenrnn(weights_path=model_name + "-weights.hdf5",
                              vocab_path=model_name + "-vocab.json",
                              config_path=model_name + "-config.json")

# dynamically generate post as the shortest one of several
CHOOSE_FROM_N = int(config["choose-from-n"])

posts = model.generate(n=CHOOSE_FROM_N, return_as_list=True,
                       temperature=float(config["temperature"]), max_gen_length=1000)

# posts = ["#0 TEST"]
post = ""
for a in range(len(posts)):
    if post == "" or len(posts[a]) < len(post):
        post = posts[a].encode("ascii").decode("unicode-escape")
print("Posting:", post)

# publish post
try:
    chrome_options = selenium.webdriver.chrome.options.Options()
    if "user-dir" in config and config["user-dir"] != "":
        chrome_options.add_argument(
            "--user-data-dir=" + config["user-dir"])
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--silent")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--allow-insecure-localhost")
    chrome_options.add_argument("--disable-extensions")
    if config["headless"] == "true":
        chrome_options.add_argument("--headless")
    driver = selenium.webdriver.Chrome(
        "cache/chromedriver.exe", options=chrome_options)
    driver.implicitly_wait(0)

    try:
        # login
        driver.get("https://www.facebook.com/login.php")
        driver.find_element_by_id("email").send_keys(config["username"])
        driver.find_element_by_id("pass").send_keys(config["password"])
        driver.find_element_by_id("loginbutton").click()
    except:
        # if profile is being used, then we won't need to login
        print("Failed to login; is user already logged in?")

    driver.get(
        "https://www.facebook.com/pg/mitconfessionssimulator/posts/")

    # post
    # input()
    driver.execute_script(
        "arguments[0].click();", driver.find_element_by_xpath("//div[.='Write a post...']"))
    time.sleep(5)
    actions = selenium.webdriver.common.action_chains.ActionChains(driver)
    actions.send_keys(post)
    actions.perform()
    driver.execute_script(
        "arguments[0].click();", driver.find_element_by_xpath("//button[@type='submit' and contains(., 'Share Now')]"))

    # wait for a bit for publish to go through
    time.sleep(10)
    retries_left = 0
except:
    traceback.print_exc()
    print("Exception encountered; aborting...")
finally:
    try:
        driver.close()
    except:
        pass
