import configparser
import yaml
import os
import json
import requests
from akamai.edgegrid import EdgeGridAuth, EdgeRc
from urllib.parse import urljoin

def getYMLFromFile(path="../main.yml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def getJSONFromFile(path):
    with open(path, "r") as f:
        return json.load(f)

def initEdgeGridAuth(path="~/.edgerc"):
    config = configparser.RawConfigParser()
    config.read(os.path.expanduser(path))
    s.auth = EdgeGridAuth(
        client_token=config.get("default", "client_token"),
        client_secret=config.get("default", "client_secret"),
        access_token=config.get("default", "access_token")
    )

def getHostFromConfig(path="~/.edgerc"):
    config = configparser.RawConfigParser()
    config.read(os.path.expanduser(path))
    return config.get("default", "host")

# HTTP Helper Functions 
def akamaiGet(url):
    return s.get(urljoin(base_url, url)).content

def akamaiPost(url, body):
    return s.post(urljoin(base_url, url), json=body).content

def akamaiPut(url, body):
    return s.put(urljoin(base_url, url), json=body).content

# Set up connectivity. Global var because it's a session that's used in multiple functions.
s = requests.Session()

# Get the base url using the provided config
base_url = "https://" + getHostFromConfig()
