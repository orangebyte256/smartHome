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
import operator
import urllib2
import alsaaudio, audioop
from pathlib import Path
import bluetooth
from google_images_download import google_images_download   #importing the library
from multiprocessing import Process
from lex_token import * 
from led import * 
from num2words import num2words

HOST_NAME = '192.168.100.5' # !!!REMEMBER TO CHANGE THIS!!!
PORT_NUMBER = 8000 # Maybe set this to 9000.
MAC_BLUETOOTH = '00:21:13:00:4F:0D'
JALOUSIE_LINK = 'http://192.168.100.11/'
SENSORS_LINK = 'http://192.168.100.7/'
MIROBO_DIR = "/usr/local/bin/mirobo"
SWITCH_BIN = "/home/pi/source/smartHome/switch/index.js"
MAX_LOUD = 100

random.seed()

colors = {
  'красный': [253, 0, 0],
  'зеленый': [0, 253, 0],
  'синий': [0, 0, 253],
  'белый': [253, 253, 253],
  'черный': [254, 254, 254],
}

sock=bluetooth.BluetoothSocket(bluetooth.RFCOMM)
sock.connect((MAC_BLUETOOTH, 1))


colors2 = [
  [253.0, 69.0, 0.0],
  [220.0, 20.0, 60.0],
  [253.0, 253.0, 0.0],
  [0.0, 253.0, 0.0],
  [253.0, 0.0, 253.0]
]

card = 'default:CARD=ALSA'
inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE,alsaaudio.PCM_NONBLOCK, cardindex=1)

# Set attributes: Mono, 8000 Hz, 16 bit little endian samples
inp.setchannels(1)
inp.setrate(8000)
inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)

# The period size controls the internal number of frames per period.
# The significance of this parameter is documented in the ALSA api.
# For our purposes, it is suficcient to know that reads from the device
# will return this many frames. Each frame being 2 bytes long.
# This means that the reads below will return either 320 bytes of data
# or 0 bytes of data. The latter is possible because we are in nonblocking
# mode.
inp.setperiodsize(160)

def equalizer():
    STAGE_COUNT = 100
    _stage = 0
    _from = 0
    _to = 0
    _res = colors2[0]
    while True:
      i = 50
      avar_val = 0
      avar_count = 0
      while i:
        i = i - 1
        time.sleep(0.001)
        l,data = inp.read()
        if l: 
          avar_val = avar_val + audioop.max(data, 2)
          avar_count = avar_count + 1
      avar = avar_val / avar_count
      print avar
      if _stage == 0:
        _from = _to
        _to = new_val(_from)
        _offset = map(operator.sub, colors2[_to], colors2[_from])
        _res = colors2[_from]
        _offset = list(map(lambda x: x / (STAGE_COUNT + 1), _offset))
        _stage = STAGE_COUNT
      else:
        _res = map(operator.add, _res, _offset)
        _stage = _stage - 1
        avar = avar / MAX_LOUD
        if avar > 1.0:
          avar = 1.0
        send(list(map(lambda x: x * avar, _res)), sock)

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
my_env["MIROBO_IP"] = u"192.168.100.10"
my_env["MIROBO_TOKEN"] = u"44655143634549325949375847366841"
my_env["LC_ALL"] = "C.UTF-8"
my_env["LANG"] = "C.UTF-8"
equalize_thread = {}

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
        # If someone went to "http://something.somewhere.net/foo/bar/",
        # then s.path equals "/foo/bar/".
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
              equalize_thread = Process(target=equalizer)
              equalize_thread.start()
            else:
              equalize_thread.terminate()
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
          print color
          print colors
          if color in colors:
            color = colors[color]
            print "Yes"
          else:
            print "No"
            color = process(calc_color(load(color)))
          print color
          send(color, sock)
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
