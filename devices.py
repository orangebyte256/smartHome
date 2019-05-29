import pytuya
import subprocess, os
import time
import bluetooth
import urllib2
from led import send
from time import sleep
from num2words import num2words
import colorsys

def set_switch(ip, id, key, state):
    d = pytuya.OutletDevice(id, ip, key)
    while d.status()['dps']['1'] != state:
        sleep(0.5)
        d.set_status(state)

def set_jalousie(path, state):
    if state:
        urllib2.urlopen(path + "open").read()
    else:
        urllib2.urlopen(path + "close").read()

def set_led(path, state):
    if state:
        send([0,0,0], path)
    else:
        send([255,255,255], path)

def set_led_color(path, state):
    color = list(colorsys.hsv_to_rgb(state["h"], state["s"], state["v"]))
    color = map(lambda x : x*255, color)
    send(color, path)

def cleaner_command(ip, token, dir, command):
    my_env = os.environ.copy()
    my_env["MIROBO_IP"] = ip
    my_env["MIROBO_TOKEN"] = token
    my_env["LC_ALL"] = "C.UTF-8"
    my_env["LANG"] = "C.UTF-8"
    subprocess.Popen([dir, command], env=my_env)

def get_sensors(SENSORS_LINK):
  vals = urllib2.urlopen(SENSORS_LINK + "sensors").read()
  vals = vals.split('/')
  res = []
  for val in vals:
    val = val.split('.')
    res.append(num2words(val[0], lang='ru'))
  return res
