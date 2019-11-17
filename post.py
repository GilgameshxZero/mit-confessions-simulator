import configparser
import selenium
from selenium import webdriver
import time
import requests
import traceback
import textgenrnn
import zipfile
import io
import json

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

# if we need to, dynamically generate post as the shortest one of several
CHOOSE_FROM_N = int(config["choose-from-n"])
CACHED_POSTS_N = int(config["cached-posts-n"])
# posts = ["#0 TEST"]
posts = []

# check the cache to see if we have posts already generated
try:
    with open("cache/cached-posts.json", "r", encoding="utf-8") as cache_fp:
        posts = json.load(cache_fp)
    print("Loaded", len(posts), "cached posts.")
except:
    print("Could not locate cached posts.")

if len(posts) == 0:
    print("Generating new cache with n =", CACHED_POSTS_N, "; choose =", CHOOSE_FROM_N)
    choose_from_posts = model.generate(n=CACHED_POSTS_N * CHOOSE_FROM_N, return_as_list=True,
                                       temperature=float(config["temperature"]), max_gen_length=1000)
    for a in range(0, CACHED_POSTS_N * CHOOSE_FROM_N, CHOOSE_FROM_N):
        post_to_add = None
        for b in range(a, a + CHOOSE_FROM_N):
            if post_to_add == None or len(choose_from_posts[b]) < len(post_to_add):
                post_to_add = choose_from_posts[b].encode(
                    "ascii").decode("unicode-escape")
        posts.append(post_to_add)
    print("Cache:", posts)

post = posts[0]
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

    # success, remove post from cache
    posts.remove(post)
except:
    traceback.print_exc()
    print("Exception encountered while using chromedriver; aborting...")
finally:
    try:
        driver.close()
    except:
        pass

# write the posts we haven't used back to the cache file
print("Writing remaining posts back to cache...")
with open("cache/cached-posts.json", "w", encoding="utf-8") as cache_fp:
    json.dump(posts, cache_fp)
