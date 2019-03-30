# -*- coding: utf-8 -*-
import time
import BaseHTTPServer, SimpleHTTPServer
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
import subprocess
import subprocess, os
import urllib2
import alsaaudio, audioop
from pathlib import Path
import bluetooth
from google_images_download import google_images_download   #importing the library
from multiprocessing import Process
from lex_token import * 
from led import * 
from num2words import num2words
from yeelight import Bulb

HOST_NAME = '192.168.100.12' # !!!REMEMBER TO CHANGE THIS!!!
PORT_NUMBER = 8000 # Maybe set this to 9000.
MAC_BLUETOOTH = '00:21:13:00:4F:0D'
JALOUSIE_LINK = 'http://192.168.100.11/'
SENSORS_LINK = 'http://192.168.100.7/'
MIROBO_DIR = "/usr/local/bin/mirobo"
MIROBO_IP = u"192.168.100.10"
MIROBO_TOKEN = u"44655143634549325949375847366841"
SWITCH_BIN = "/home/pi/source/smartHome/switch/index.js"
MAX_LOUD = 100
BULB_IP = '192.168.100.6'

random.seed()

sock=bluetooth.BluetoothSocket(bluetooth.RFCOMM)
sock.connect((MAC_BLUETOOTH, 1))

def get_sensors():
  vals = urllib2.urlopen(SENSORS_LINK).read()
  vals = vals.split('/')
  res = []
  for val in vals:
    val = val.split('.')
    print val[0]
    res.append(num2words(val[0], lang='ru'))
  return res


my_env = os.environ.copy()
my_env["MIROBO_IP"] = MIROBO_IP
my_env["MIROBO_TOKEN"] = MIROBO_TOKEN
my_env["LC_ALL"] = "C.UTF-8"
my_env["LANG"] = "C.UTF-8"
equalize_thread = {}
capture_thread = {}
bulb = Bulb(BULB_IP)

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_HEAD(s):
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()
    def do_GET(s):
        """Respond to a GET request."""
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()
        s.wfile.write("<html><head><title>Title goes here.</title></head>")
        s.wfile.write("<body><p>This is a test.</p>")
        s.wfile.write("<p>You accessed path: %s</p>" % s.path)
        s.wfile.write("</body></html>")
    def do_POST(s):
      content_len = int(s.headers.getheader('content-length', 0))
      post_body = s.rfile.read(content_len)
      if post_body:
        data = json.loads(post_body)
        res = dict()
        res["version"] = data["version"]
        res["session"] = data["session"]
        res["response"] = {}
        res["response"]["text"] = "Я Мистер Мисикс! Посмотрите на меня!"
        res["response"]["tts"] = "<speaker effect=\"hamster\">Я Мистер Мисикс! Посмотрите на меня!"
        res["response"]["end_session"] = False
        if token_exist(data["request"]["nlu"]["tokens"], u"пылесос"):
          if is_on(data["request"]["nlu"]["tokens"]) or is_off(data["request"]["nlu"]["tokens"]):
            if is_on(data["request"]["nlu"]["tokens"]):
              subprocess.Popen([MIROBO_DIR, "start"], env=my_env)
            else:
              subprocess.Popen([MIROBO_DIR, "home"], env=my_env)
            res["response"] = pos_response()
          else:
            res["response"] = neg_response()

        if token_exist(data["request"]["nlu"]["tokens"], u"температура"):
            res["response"] = custom_responce("Текущая температура " + get_sensors()[0].encode('utf-8') + " градусов")

        if token_exist(data["request"]["nlu"]["tokens"], u"влажность"):
            res["response"] = custom_responce("Текущая влажность " + get_sensors()[1].encode('utf-8') + " процентов")

        if token_exist(data["request"]["nlu"]["tokens"], u"эквалайзер"):
          if is_on(data["request"]["nlu"]["tokens"]) or is_off(data["request"]["nlu"]["tokens"]):
            if is_on(data["request"]["nlu"]["tokens"]):
              global equalize_thread
              equalize_thread = Process(target=equalizer, args=(sock,))
              equalize_thread.start()
            else:
              equalize_thread.terminate()
            res["response"] = pos_response()
          else:
            res["response"] = neg_response()

        if token_exist(data["request"]["nlu"]["tokens"], u"экран"):
          if is_on(data["request"]["nlu"]["tokens"]) or is_off(data["request"]["nlu"]["tokens"]):
            if is_on(data["request"]["nlu"]["tokens"]):
              global capture_thread
              capture_thread = Process(target=capture, args=(sock,))
              capture_thread.start()
            else:
              capture_thread.terminate()
            res["response"] = pos_response()
          else:
            res["response"] = neg_response()

        if token_exist(data["request"]["nlu"]["tokens"], u"свет"):
          if is_on(data["request"]["nlu"]["tokens"]) or is_off(data["request"]["nlu"]["tokens"]):
            if is_on(data["request"]["nlu"]["tokens"]):
              subprocess.Popen(["node", SWITCH_BIN, "true"])
            else:
              subprocess.Popen(["node", SWITCH_BIN, "false"])
            res["response"] = pos_response()
          else:
            res["response"] = neg_response()

        if token_exist(data["request"]["nlu"]["tokens"], u"шторы") or token_exist(data["request"]["nlu"]["tokens"], u"окно"):
          if token_partly_exist(data["request"]["nlu"]["tokens"], u"откр") or token_partly_exist(data["request"]["nlu"]["tokens"], u"закр"):
            if token_partly_exist(data["request"]["nlu"]["tokens"], u"откр"):
              urllib2.urlopen(JALOUSIE_LINK + "open").read()
            else:
              urllib2.urlopen(JALOUSIE_LINK + "close").read()
            res["response"] = pos_response()
          else:
            res["response"] = neg_response()

        if token_exist(data["request"]["nlu"]["tokens"], u"цвет"):
          color = data["request"]["command"].replace(u" цвет","").encode('utf-8')
          led_color(color)
          res["response"] = pos_response()

        s.send_response(200)
        s.send_header("Content-type", "application/json; charset=utf-8")
        s.end_headers()
        s.wfile.write(json.dumps(res))

if __name__ == '__main__':
    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)
    httpd.socket = ssl.wrap_socket (httpd.socket, certfile='./server.pem', server_side=True)
    print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER)