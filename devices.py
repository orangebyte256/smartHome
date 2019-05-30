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

def set_led(path, state, color):
    if state:
        set_led_color(path, color)
    else:
        send([0,0,0], path)

def set_bulb(bulb, state):
    if state:
        bulb.turn_on()
    else:
        bulb.turn_off()

def set_led_color(path, state):
    print state
    color = list(colorsys.hsv_to_rgb(state["h"] / 360.0, state["s"] / 100.0, state["v"] / 100.0))
    color = map(lambda x : int(x*255), color)
    print color
    send(color, path)

def set_bulb_color(bulb, state):
    print state
    bulb.set_hsv(state["h"], state["s"], state["v"])

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
