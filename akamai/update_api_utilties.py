import configparser
import json
import os
import requests
import sys
import yaml
from akamai.edgegrid import EdgeGridAuth, EdgeRc
from urllib.parse import urljoin

# These are simply local file helpers.
def getYMLFromFile(path="../main.yml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def getJSONFromFile(path):
    with open(path, "r") as f:
        return json.load(f)

def getYMLFromUrl(url):
    return yaml.safe_load(s.get(url).content.decode('utf-8'))

# Initializes the EdgeGrid auth using the .edgerc file (or some passed-in config).
def initEdgeGridAuth(path="~/.edgerc"):
    # If the config file was passed in, use that.
    if len(sys.argv) > 1:
        path = sys.argv[1]
    config = configparser.RawConfigParser()
    config.read(os.path.expanduser(path))

    # TODO: We might actually be able to authenticate without EdgeGridAuth,
    # which would reduce the number of dependencies.
    s.auth = EdgeGridAuth(
        client_token=config.get("default", "client_token"),
        client_secret=config.get("default", "client_secret"),
        access_token=config.get("default", "access_token")
    )

# Gets the hostname from the .edgerc file (or some passed-in config).
def getHostFromConfig(path="~/.edgerc"):
    # If the config file was passed in, use that.
    if len(sys.argv) > 1:
        path = sys.argv[1]
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
