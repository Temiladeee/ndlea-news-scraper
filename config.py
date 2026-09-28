!pip install -q requests beautifulsoup4 lxml python-dateutil

import re, time, random, urllib.parse
from datetime import datetime, timedelta
from urllib.robotparser import RobotFileParser

import requests
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

BASE_URL = "https://ndlea.gov.ng"
NEWS_LIST_URL = f"{BASE_URL}/news"
ARTICLE_URL_PREFIX = f"{BASE_URL}/blog/"
HEADERS = {"User-Agent": "Mozilla/5.0 (research-scraper; contact: mariamtemilade88@gmail.com)"}
REQUEST_DELAY_RANGE = (2.0, 4.5)   # be polite; do not remove

def polite_sleep():
    time.sleep(random.uniform(*REQUEST_DELAY_RANGE))
