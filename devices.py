import pytuya
import subprocess, os
import time
import bluetooth
import urllib2
from num2words import num2words

def set_switch(ip, id, key, state):
    d = pytuya.OutletDevice(id, ip, key)
    while d.status()['dps']['1'] != state:
        d.set_status(state)

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
