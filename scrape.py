"""
Fetch posts from MIT confessions pages and store them in JSON format to
"""

import selenium
from selenium import webdriver
import configparser
import zipfile
import json
import traceback
import getpass
import threading
import time
import io
import requests
import getopt
import sys


def open_chromedriver(file, options):
    driver = selenium.webdriver.Chrome(
        file, options=options)
    driver.implicitly_wait(0)
    return driver


def login_to_fb(driver, username, password):
    driver.get("https://www.facebook.com/login.php")
    driver.find_element_by_id("email").send_keys(username)
    driver.find_element_by_id("pass").send_keys(password)
    driver.find_element_by_id("loginbutton").click()


def autosave_confessions_json(finished_event, confessions_file, confessions):
    AUTOSAVE_INTERVAL_S = 300

    while True:
        # conditionally wait to allow main thread to terminate if finished
        event_state = finished_event.wait(AUTOSAVE_INTERVAL_S)

        with open(confessions_file, "w") as file:
            json.dump(confessions, file)
        print("Saved confessions JSON.")

        if event_state:
            break


def run():
    # parse configuration
    config = configparser.ConfigParser()
    config.read("config.ini")
    config = config["scrape"]
    print("Read configuration.")

    # confessions is of the following format
    """
    {
        post_url: {
            "text": string,
            "utime": int,
            "reacts": int,
            "comments": int,
            "shares": int,
        },
    }
    """
    # load confessions if exists
    CONFESSIONS_FILE = ".cache/confessions.json"
    try:
        with open(CONFESSIONS_FILE, "r") as file:
            confessions = json.loads(file.read())
    except:
        confessions = {}
    # maintain a set of post_urls so that we don't scrape posts twice
    print("Found", len(confessions), "previously scraped posts.")

    # get username and password from command line or prompt
    username = None
    password = None
    try:
        opts, args = getopt.getopt(
            sys.argv[1:], "", ["username=", "password="])
        for opt in opts:
            if opt[0] == "--username":
                username = opt[1]
            if opt[0] == "--password":
                password = opt[1]
    except:
        traceback.print_exc()
    if username is None:
        username = input("Facebook username: ")
    if password is None:
        password = getpass.getpass("Facebook password: ")

    # download chromedriver
    CHROMEDRIVER_DIR = ".cache/"
    chromedriver_file = CHROMEDRIVER_DIR + "chromedriver.exe"
    try:
        request = requests.get(config["chromedriver"])
        archive = zipfile.ZipFile(io.BytesIO(request.content))

        # extract first file from the archive
        file = archive.namelist()[0]
        chromedriver_file = archive.extract(file, CHROMEDRIVER_DIR)
        archive.close()
        print("Downloaded and extracted chromedriver to", chromedriver_file + ".")
    except:
        traceback.print_exc()
        print("Exception while extracting chromedriver. Using default location of",
              chromedriver_file + ".")

    # set options from config
    chromedriver_options = selenium.webdriver.chrome.options.Options()
    chromedriver_options.add_argument("--disable-notifications")
    chromedriver_options.add_argument("--mute-audio")
    chromedriver_options.add_argument("--log-level=3")
    chromedriver_options.add_argument("--silent")
    chromedriver_options.add_argument("--disable-gpu")
    chromedriver_options.add_argument("--allow-insecure-localhost")
    chromedriver_options.add_argument("--disable-extensions")
    if config["headless"] == "true":
        chromedriver_options.add_argument("--headless")

    # launch autosave thread
    finished_event = threading.Event()
    autosave_thread = threading.Thread(target=autosave_confessions_json, args=(
        finished_event,
        CONFESSIONS_FILE,
        confessions,
    ))
    autosave_thread.start()
    print("Launched autosave thread.")

    # scrape
    PAGES = [
        "timelybeaverconfessions",
        "beaverconfessions",
    ]
    MAX_SHOW_RESULT_WAIT = 50
    MAX_CONSEC_NO_RESULT = 1000

    main = open_chromedriver(chromedriver_file, chromedriver_options)
    child = open_chromedriver(chromedriver_file, chromedriver_options)

    try:
        login_to_fb(main, username, password)
        login_to_fb(child, username, password)
        print("Successfully logged into FB.")

        for page in PAGES:
            main.get("https://www.facebook.com/" + page + "/posts/")
            search_query = 0
            consec_no_result = 0

            while consec_no_result < MAX_CONSEC_NO_RESULT:
                # make sure page/query is in confessions dict
                if page not in confessions.keys():
                    confessions[page] = {}
                if search_query not in confessions[page].keys():
                    confessions[page][search_query] = {}

                # search for post `#a`, and add all search results to data if they aren't there already
                try:
                    search = main.find_elements_by_css_selector(
                        "label._3fbp > input")[0]
                    for a in range(10):
                        try:
                            search.send_keys(selenium.webdriver.common.keys.Keys.BACKSPACE)
                        except:
                            pass
                    search.send_keys("#" + str(search_query))
                    search.send_keys(selenium.webdriver.common.keys.Keys.ENTER)
                    time.sleep(5)
                except:
                    traceback.print_exc()
                    print("Failed during search. Retrying...")
                    main.get("https://www.facebook.com/" + page + "/posts/")
                    continue

                # automate scroll to show all results
                waits = 0
                while waits < MAX_SHOW_RESULT_WAIT:
                    no_results = main.find_elements_by_css_selector(
                        "div._26l")
                    if len(no_results) > 0:
                        break
                    try:
                        end = main.find_element_by_xpath(
                            "//div[text() = 'End of Results']")
                        break
                    except:
                        try:
                            see_more = main.find_element_by_xpath(
                                "//a[text() = 'See More Results']")
                            see_more.click()
                        except:
                            time.sleep(1)
                            waits += 1
                if waits >= MAX_SHOW_RESULT_WAIT:
                    print("Timeout waiting for search results. Getting next task...")
                    continue

                # are there any results? if none, then get next task
                if len(no_results) > 0:
                    consec_no_result += 1
                    print("No results during search for #" + str(search_query) + "!")
                    search_query += 1
                    continue
                else:
                    consec_no_result = 0

                try:
                    results = main.find_elements_by_css_selector("div._5zwe > a")
                except:
                    traceback.print_exc()
                    print("Failed during result collection. Retrying...")
                    continue
                print("Searching", page, "with", "#" +
                      str(search_query), "returned", len(results), "results.")

                # scrape each post in search results
                for result in results:
                    try:
                        post_url = result.get_attribute("href")
                    except:
                        traceback.print_exc()
                        print("Failed during getting post URL. Skipping...")
                        continue

                    # don't scrape if previous search already found this post
                    if post_url in confessions.keys():
                        continue

                    # get the post data
                    try:
                        child.get(post_url)
                        post = child.find_elements_by_css_selector("div._5pbx")[
                            0]
                        text = post.get_attribute("innerText")
                        date = child.find_elements_by_css_selector(
                            "abbr._5ptz")[0].get_attribute("data-utime")
                    except:
                        traceback.print_exc()
                        raise Exception(
                            "Failed to fetch post from post URL. Are we being rate limited?")

                    try:
                        reacts = int(child.find_elements_by_css_selector(
                            "div._5pcr")[0].find_elements_by_css_selector("span._3dlh")[0].get_attribute("innerText"))
                    except:
                        reacts = 0
                    try:
                        comments = int(child.find_elements_by_css_selector(
                            "div._5pcr")[0].find_elements_by_css_selector("a._3hg-")[0].get_attribute("innerText").split(" ")[0])
                    except:
                        comments = 0
                    try:
                        shares = int(child.find_elements_by_css_selector(
                            "div._5pcr")[0].find_elements_by_css_selector("a._3rwx")[0].get_attribute("innerText").split(" ")[0])
                    except:
                        shares = 0
                    post_data = {
                        "text": text,
                        "utime": date,
                        "reacts": reacts,
                        "comments": comments,
                        "shares": shares,
                    }

                    confessions[post_url] = post_data
                    print(post_url, "[", date, reacts, comments, shares, "]", text)

                # prep for next search
                search_query += 1
    except:
        traceback.print_exc()
        print("Terminating...")

        try:
            main.close()
            child.close()
        except:
            print("Could not close drivers. Continuing...")

    # exit autosave thread regardless of status
    finished_event.set()
    autosave_thread.join()
    print("Autosave thread joined.")


if __name__ == "__main__":
    run()
