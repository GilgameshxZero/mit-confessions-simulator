import os

def toRelPath(origPath):
	"""Converts path to path relative to current script

	origPath:	path to convert
	"""
	if not hasattr(toRelPath, "__location__"):
		toRelPath.__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
	return os.path.join(toRelPath.__location__, origPath)

####end of library

import configparser
import json
import requests
import time

import selenium
import logging
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.remote_connection import LOGGER

#read config
config = configparser.ConfigParser()
config.read(toRelPath("config.ini"))

configCfd = configparser.ConfigParser()
configCfd.read(toRelPath("config.confidential.ini"))

def makePost(pageUrl, post):
	retry = True
	while retry:
		LOGGER.setLevel(logging.WARNING) #disable most logging from selenium
		chrome_options = Options()
		chrome_options.add_argument("--disable-notifications --mute-audio --log-level=3 --silent")
		driver = webdriver.Chrome(toRelPath(config["fetch"]["webdriver-loc"]), chrome_options=chrome_options, service_log_path="NUL")
		driver.implicitly_wait(0) #blocks for pages to load completely before

		try:
			retry = False

			#login
			driver.get("https://www.facebook.com/login.php")
			driver.find_element_by_id("email").send_keys(configCfd["confidential"]["email"])
			driver.find_element_by_id("pass").send_keys(configCfd["confidential"]["password"])
			driver.find_element_by_id("loginbutton").click()
			driver.get(pageUrl)

			#post
			driver.execute_script("arguments[0].click();", driver.find_element_by_css_selector("div._3nd0"))
			actions = ActionChains(driver)
			actions.send_keys(post)
			actions.perform()
			driver.execute_script("arguments[0].click();", driver.find_element_by_css_selector("button._1mf7"))

			#TODO: wait for a bit for publish to go through
			time.sleep(15)
		except:
			print("Exception encountered, retrying...")
			retry = True
		finally:
			try:
				driver.close()
			except:
				pass

#read post samples
samples = json.loads(open(toRelPath(config["post-fb"]["post-samples"])).read())
postInterval = int(config["post-fb"]["post-interval"])

for a in range(len(samples)):
	sample = samples[a]
	r = makePost(config["post-fb"]["page-url"], sample)
	print(sample)
	samplesLeft = len(samples) - a - 1
	print(samplesLeft, "samples left to post; ~" + str(postInterval * samplesLeft / 60 / 60 / 24), "days.\n\n")
	time.sleep(postInterval)

	#update the file with the post removed everytime we post one
	with open(toRelPath(config["post-fb"]["post-samples"]), "w") as outfile:
		json.dump(samples[a + 1:], outfile)

print("Done.")