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
from defines import *
import urllib
from multiprocessing import Process
from lex_token import * 
from led import * 
from utils import * 
from num2words import num2words
from tinydb import TinyDB, Query
from urlparse import urlparse

random.seed()

JALOUSIE_LINK = "http://" + get_device_ip(JALOUSIE_MAC) + '/'
LED_LINK = "http://" + get_device_ip(LED_MAC) + '/'
SENSORS_LINK = "http://" + get_device_ip(LED_MAC) + '/'
MIROBO_LINK = "http://" + get_device_ip(MIROBO_MAC) + '/'
BULB_IP = get_device_ip(BULB_MAC)
SWITCH_IP = get_device_ip(SWITCH_MAC)


equalize_thread = {}
capture_thread = {}
bluetooth_sock = {}

db = TinyDB('./db.json')
Devices = Query()

JALOUSIE = '1'
SWITCH = '2'
LED = '3'
SENSOR_TEMPERATURE = '4'
VEHICLE_ENGINE = '5'

functions = {
    'devices.capabilities.on_off': 
    {
        "on" : {
            SWITCH : lambda state : set_switch(SWITCH_IP, SWITCH_ID, SWITCH_KEY, state), 
            VEHICLE_ENGINE : lambda state : set_engine(SLNET),
            JALOUSIE : lambda state : set_jalousie(JALOUSIE_LINK, state),
            LED : lambda state : set_led(LED_LINK, state, 
                db.search(Devices.id == LED)[0]["custom_data"]["devices.capabilities.color_setting"]["state"]["value"])
        }
    },
    'devices.capabilities.color_setting': 
    {
        "hsv": {
            LED : lambda state : set_led_color(LED_LINK, state)
        },
        "temperature_k": {
            LED : lambda state : set_led_color(LED_LINK, {'h':0, 's':0, 'v':state / 65 })
        }

    },
    'devices.capabilities.range': 
    {
        "brightness": {
            LED : lambda range : set_led_range(LED_LINK, db.search(Devices.id == LED)[0]["custom_data"]["devices.capabilities.color_setting"]["state"]["value"], range)
        },
        "temperature": {
            SENSOR_TEMPERATURE: lambda range : {}
        }
    }
}

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

    
def devices_state(s):
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
            if device["id"] == SENSOR_TEMPERATURE:
                val = -1
                while val == -1:
                    val = int(read_temperature(SENSORS_LINK))
                capabilitie_item["state"]["value"] = val
            device["capabilities"].append(capabilitie_item)
        result.append(device)
    answer(s, result, data)

def devices_set_state(s):
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
        query_item = query_item[0]
        device = {}
        device["id"] = item["id"]
        device["capabilities"] = []
        for capabilitie in item["capabilities"]:
            forward_end = False
            if capabilitie["type"] == "devices.capabilities.on_off" and capabilitie["state"]["value"] == False:
                forward_end = True
            capabilitie_result = capabilitie
            if capabilitie["state"]["value"] != query_item["custom_data"][capabilitie["type"]]["state"]["value"]:
                functions[capabilitie["type"]][capabilitie["state"]["instance"]][item["id"]](capabilitie["state"]["value"])
                set_value = capabilitie["state"]["value"]
                if capabilitie["state"]["instance"] == "temperature_k":
                    set_value = {'h':0, 's':0, 'v':set_value / 65 }
                query_item["custom_data"][capabilitie["type"]]["state"]["value"] = set_value
                db.update(query_item, Devices.id == item["id"])
                capabilitie_result["state"]["action_result"] = {"status": "DONE"}
            else:
                capabilitie_result["state"]["action_result"] = {"status": "ERROR", "error_code": "INVALID_ACTION", "error_message": "Value the same"}
            capabilitie_result["state"].pop("value")
            device["capabilities"].append(capabilitie_result)
            if forward_end:
                break
        result.append(device)
    answer(s, result, data)

def send_ok(s):
    s.send_response(200)
    s.send_header("Content-type", "text/html")
    s.end_headers()

def item_not_exist(id):
    return len(db.search(Devices.id == str(id))) == 0

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_HEAD(s):
        send_ok(s)
    def do_GET(s):
        print s.path
        if s.path == '/clean':
            db.purge()
            send_ok(s)
        if s.path == '/init':
            if item_not_exist(JALOUSIE):
                db.insert({'id': JALOUSIE, 'name': 'jalousie', 'room': 'living_room', 'type': 'devices.types.switch', 'capabilities': [{"type": "devices.capabilities.on_off"}], 'custom_data': {'devices.capabilities.on_off': {'state': {"instance": "on", "value": True}}}})
            if item_not_exist(SWITCH):
                db.insert({'id': SWITCH, 'name': 'switch', 'room': 'living_room', 'type': 'devices.types.switch', 'capabilities': [{"type": "devices.capabilities.on_off"}], 'custom_data': {'devices.capabilities.on_off': {'state': {"instance": "on", "value": True}}}})
            if item_not_exist(VEHICLE_ENGINE):
                db.insert({'id': VEHICLE_ENGINE, 'name': 'vehicle_engine', 'room': 'living_room', 'type': 'devices.types.switch', 'capabilities': [{"type": "devices.capabilities.on_off"}], 'custom_data': {'devices.capabilities.on_off': {'state': {"instance": "on", "value": False}}}})
            if item_not_exist(LED):
                db.insert({'id': LED, 'name': 'led', 'room': 'living_room', 'type': 'devices.types.light', 'capabilities': [{"type": "devices.capabilities.on_off"}, {"type": "devices.capabilities.color_setting", "parameters": { "color_model": "hsv", "temperature_k": {"min": 2700, "max": 9000, "precision": 1}}}, {"type": "devices.capabilities.range", "parameters": { "instance": "brightness", "unit": "unit.percent", "range": {"min": 0, "max": 100, "precision": 10}}}], 'custom_data': {'devices.capabilities.on_off': {'state': {"instance": "on", "value": True}}, 'devices.capabilities.color_setting': {'state': {"instance": "hsv","value": {"h": 0,"s": 0,"v": 0}}}, 'devices.capabilities.range': {'state': {"instance": "brightness","value": 0}}}})                
            if item_not_exist(SENSOR_TEMPERATURE):
                db.insert({'id': SENSOR_TEMPERATURE, 'name': 'temperature', 'room': 'living_room', 'type': 'devices.types.thermostat', 'capabilities': [{"type": "devices.capabilities.range", "retrievable":True, "parameters": { "instance": "temperature", "unit": "unit.temperature.celsius", "range": {"min": 0, "max": 100, "precision": 1}}}], 'custom_data': {'devices.capabilities.range': {'state': {"instance": "temperature","value": 20}}}})                
            send_ok(s)
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
            devices_state(s)
        elif s.path == '/v1.0/user/devices/action':
            devices_set_state(s)
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
