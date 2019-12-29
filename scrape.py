import selenium
from selenium import webdriver
import requests
import time
import configparser
import zipfile
import json
import io
import traceback
import copy


def get_chrome_driver():
    driver = selenium.webdriver.Chrome(
        "cache/chromedriver.exe", options=chrome_options)
    driver.implicitly_wait(0)
    return driver


def login_driver(driver):
    driver.get("https://www.facebook.com/login.php")
    driver.find_element_by_id("email").send_keys(config["username"])
    driver.find_element_by_id("pass").send_keys(config["password"])
    driver.find_element_by_id("loginbutton").click()


# parse configuration
config = configparser.ConfigParser()
config.read("config.ini")
config = config["scrape"]

# download chromedriver
try:
    request = requests.get(config["chromedriver"])
    file = zipfile.ZipFile(io.BytesIO(request.content))
    file.extractall("cache/")
    file.close()
except:
    pass

# setup options
chrome_options = selenium.webdriver.chrome.options.Options()
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--mute-audio")
chrome_options.add_argument("--log-level=3")
chrome_options.add_argument("--silent")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--allow-insecure-localhost")
chrome_options.add_argument("--disable-extensions")

child_options = copy.deepcopy(chrome_options)
if config["headless"] == "true":
    chrome_options.add_argument("--headless")
if config["child-headless"] == "true":
    child_options.add_argument("--headless")

# setup drivers
driver = get_chrome_driver()
child_driver = get_chrome_driver()

# login to prevent being blocked by FB
login_driver(driver)
login_driver(child_driver)

# for each page, scrape all possible posts
PAGES = [
    "https://www.facebook.com/timelybeaverconfessions/posts/",
    "https://www.facebook.com/beaverconfessions/posts/"
]

# if posts have been scraped before, don't scrape them again
with open("assets/confessions.json", "r") as infile:
    data = json.loads(infile.read())

for page in PAGES:
    # a number of consecutive searches without results will terminate scraping
    no_search_results = 0

    a = 0
    while no_search_results < 1000:
        a += 1
        try:
            driver.get(page)

            # search for post `#a`, and add all search results to data if they aren't there already
            search = driver.find_elements_by_css_selector(
                "label._3fbp > input")[0]
            search.send_keys("#" + str(a))
            search.send_keys(selenium.webdriver.common.keys.Keys.ENTER)

            # show all results
            waits = 0
            while waits < 50:
                no_results = driver.find_elements_by_css_selector("div._26l")
                if len(no_results) > 0:
                    break
                try:
                    end = driver.find_element_by_xpath(
                        "//div[text() = 'End of Results']")
                    break
                except:
                    try:
                        see_more = driver.find_element_by_xpath(
                            "//a[text() = 'See More Results']")
                        see_more.click()
                    except:
                        time.sleep(1)
                        waits += 1
            if waits >= 50:
                raise Exception("Timeout waiting for search results.")
            if len(no_results) > 0:
                no_search_results += 1
                continue
            else:
                no_search_results = 0

            # scrape each post in the search results, and add it to data if it doesn't exist already
            results = driver.find_elements_by_css_selector("div._5zwe > a")
            for result in results:
                url = result.get_attribute("href")

                # log the post in console for visibility
                if not url in data:
                    child_driver.get(url)
                    post = child_driver.find_elements_by_css_selector("div._5pbx")[
                        0]
                    text = post.get_attribute("innerText")
                    date = child_driver.find_elements_by_css_selector("abbr._5ptz")[
                        0].get_attribute("data-utime")
                    try:
                        reacts = int(child_driver.find_elements_by_css_selector(
                            "div._5pcr")[0].find_elements_by_css_selector("span._3dlh")[0].get_attribute("innerText"))
                    except:
                        reacts = 0
                    try:
                        comments = int(child_driver.find_elements_by_css_selector(
                            "div._5pcr")[0].find_elements_by_css_selector("a._3hg-")[0].get_attribute("innerText").split(" ")[0])
                    except:
                        comments = 0
                    try:
                        shares = int(child_driver.find_elements_by_css_selector(
                            "div._5pcr")[0].find_elements_by_css_selector("a._3rwx")[0].get_attribute("innerText").split(" ")[0])
                    except:
                        shares = 0
                    data[url] = {
                        "text": text,
                        "utime": date,
                        "reacts": reacts,
                        "comments": comments,
                        "shares": shares
                    }

                    print(text, "[" + str(len(data)), date,
                          reacts, comments, str(shares) + "]")
        except:
            traceback.print_exc()
            print(
                "Unhandled exception encountered while scraping page; resetting drivers and trying again...")
            try:
                driver.close()
                child_driver.close()
            except:
                print("Could not close drivers; resetting them anyway...")

            try:
                driver = get_chrome_driver()
                child_driver = get_chrome_driver()
                login_driver(driver)
                login_driver(child_driver)
                continue
            except:
                break

    print("Finished scraping", page)
try:
    driver.close()
    child_driver.close()
except:
    pass

# save all post data once we're done
print("Saving data...")
with open("assets/confessions.json", "w") as outfile:
    json.dump(data, outfile)
