import time
import BaseHTTPServer, SimpleHTTPServer
from urlparse import urlparse
import ssl
import json
import gtk.gdk
import os
import math
import numpy
import time
import sys
import random
import serial
import requests
import subprocess, os
import bluetooth
from defines import *
import urllib
from google_images_download import google_images_download   #importing the library
from multiprocessing import Process
from lex_token import * 
from led import * 
from devices import * 
from num2words import num2words
from yeelight import Bulb
from tinydb import TinyDB, Query
from urlparse import urlparse

random.seed()

equalize_thread = {}
capture_thread = {}
bluetooth_sock = {}
bulb = Bulb(BULB_IP)

db = TinyDB('./db.json')
Devices = Query()

def answer(s, devices, data):
    res = dict()
    res["request_id"] = s.headers.getheader("X-Request-Id")
    if devices != None:
        res["payload"] = {}
        if data == None:
            res["payload"]["user_id"] = "orangebyte256"
        res["payload"]["devices"] = devices
    s.send_response(200)
    s.send_header("Content-type", "application/json; charset=utf-8")
    s.end_headers()
    s.wfile.write(json.dumps(res))

def devices(s):
    result = []
    for item in db:
        device = item
        result.append(device)
    answer(s, result, None)

    
def devices_state(s, set_state):
    content_len = int(s.headers.getheader('content-length', 0))
    post_body = s.rfile.read(content_len)
    data = json.loads(post_body)
    result = []
    items = None
    if "payload" in data:
        items = data["payload"]["devices"]
    else:
        items = data["devices"]
    for item in items:
        query_item = db.search(Devices.id == item["id"])
        device = {}
        device["id"] = item["id"]
        device["capabilities"] = []
        for capabilitie in query_item[0]["capabilities"]:
            capabilitie_item = query_item[0]["custom_data"][capabilitie["type"]]
            capabilitie_item["type"] = capabilitie["type"]
            if set_state:
                capabilitie_item["state"].pop("value")
                capabilitie_item["state"]["action_result"] = {"status": "DONE"}
            device["capabilities"].append(capabilitie_item)
        result.append(device)
    answer(s, result, data)


class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_HEAD(s):
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()
    def do_GET(s):
        print s.path
        if s.path == '/init':
            db.purge()
            db.insert({'id': '1', 'name': 'jalousie', 'room': 'living_room', 'type': 'devices.types.switch', 'capabilities': [{"type": "devices.capabilities.on_off"}], 'custom_data': {'devices.capabilities.on_off': {'state': {"instance": "on", "value": True}}}})
            db.insert({'id': '2', 'name': 'switch', 'room': 'living_room', 'type': 'devices.types.switch', 'capabilities': [{"type": "devices.capabilities.on_off"}], 'custom_data': {'devices.capabilities.on_off': {'state': {"instance": "on", "value": True}}}})
            s.send_response(200)
            s.send_header("Content-type", "text/html")
            s.end_headers()
        elif s.path.find('/authorize') != -1:
            query = urllib.unquote(s.path).decode('utf8')
            query = query.split("?")[1]
            query_components = dict(qc.split("=") for qc in query.split("&"))
            result = urllib.urlencode({'code': '7737244', 'state': query_components['state']})
            result = query_components['redirect_uri'] + '?' + result
            print query_components
            print result
            s.send_response(301)
            s.send_header('Location',result)
            s.end_headers()
        elif s.path == '/v1.0/user/devices':
            devices(s)
    def do_POST(s):
        print s.path
        if s.path == '/v1.0/user/unlink':
            answer(s, None, None)
        elif s.path == '/v1.0/user/devices/query':
            devices_state(s, False)
        elif s.path == '/v1.0/user/devices/action':
            devices_state(s, True)
        elif s.path == '/token':
            s.send_response(200)
            s.send_header("Content-type", "application/json; charset=utf-8")
            s.end_headers()
            res = {
                "token_type": "bearer",
                "access_token": "AQAAAACy1C6ZAAAAfa6vDLuItEy8pg-iIpnDxIs",
                "expires_in": 124234123534,
                "refresh_token": "1:GN686QVt0mmakDd9:A4pYuW9LGk0_UnlrMIWklkAuJkUWbq27loFekJVmSYrdfzdePBy7:A-2dHOmBxiXgajnD-kYOwQ"
            }
            s.wfile.write(json.dumps(res))
if __name__ == '__main__':
    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)
    httpd.socket = ssl.wrap_socket (httpd.socket, certfile=CERT_PATH, server_side=True)
    print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)
    httpd.serve_forever()
    httpd.server_close()
    print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER)