import os

def toRelPath(origPath):
	"""Converts path to path relative to current script

	origPath:	path to convert
	"""
	if not hasattr(toRelPath, "__location__"):
		toRelPath.__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
	return os.path.join(toRelPath.__location__, origPath)

####end of rain library

import configparser
import json

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

#get input for which config set to use
configSet = input("Configuration set to use: ")
if configSet == "":
	configSet = config["fetch"]["default-config"]
if not configSet in config.sections():
	print("Configuration set does not exist. Exiting...")
	exit()

#set options
LOGGER.setLevel(logging.WARNING) #disable most logging from selenium
chrome_options = Options()
chrome_options.add_argument("--disable-notifications --mute-audio --log-level=3 --silent")
driver = webdriver.Chrome(config["fetch"]["webdriver-loc"], chrome_options=chrome_options, service_log_path="NUL")
driver.implicitly_wait(0) #blocks for pages to load completely before

#login & navigate to page
driver.get(config[configSet]["posts-page-url"])

#continuously scroll and parse elements on page, deleting them afterwards
data = []
while len(driver.find_elements_by_id("www_pages_reaction_see_more_unitwww_pages_posts")) > 0:
	#process all posts on the page
	postElems = driver.find_elements_by_css_selector("div._5pbx.userContent")
	for postElem in postElems:
		#parse postElem for text
		postText = ""

		#click on any see more links
		seeMoreLinks = postElem.find_elements_by_css_selector("* a.see_more_link")
		for link in seeMoreLinks:
			#this click does not require element to be in view
			driver.execute_script("arguments[0].click();", link)

		#* p selects p children recursively
		relevantChildren = postElem.find_elements_by_css_selector("* p")
		for child in relevantChildren:
			#after clicking see more, outertext should contain all text
			textContent = child.get_attribute("outerText")

			#sometimes textContent begins with an extra space
			sliceBegin = 0
			if textContent[0] == " ":
				sliceBegin = 1
			postText += textContent[sliceBegin:] + "\n"

		#also fetch date of post
		dateElems = postElem.parent.find_elements_by_css_selector("* abbr._5ptz")

		#sometimes date doesn't get fetched?
		if len(dateElems) > 0:
			date = dateElems[0].get_attribute("title")
			utime = dateElems[0].get_attribute("data-utime")
		else:
			date = ""
			utime = ""

		data.append({
			"text": postText,
			"date": date,
			"utime": utime
			})

		#output to stdout for light logging
		#print(data[-1] + "\n")

		#delete this element from the page to free up page space and memory as well
		driver.execute_script("arguments[0].remove();", postElem.find_element_by_xpath("../../../../../../.."))

	#scroll to the top, then the bottom of page
	#this usually guarantees new elements to load in
	driver.execute_script("window.scrollTo(0, 0);")
	driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

#useful for debugging what's wrong; disable to close browser at program end
driver.close()

#dump data into json
with open(toRelPath(config[configSet]["fetch-dump"]), "w") as outfile:
    json.dump(data, outfile)