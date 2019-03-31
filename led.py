# -*- coding: utf-8 -*-
import time
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
from pathlib import Path
import bluetooth
from google_images_download import google_images_download   #importing the library
from multiprocessing import Process
import lex_token
import led
import operator

nice_colors = [
  [253.0, 69.0, 0.0],
  [220.0, 20.0, 60.0],
  [253.0, 253.0, 0.0],
  [0.0, 253.0, 0.0],
  [253.0, 0.0, 253.0]
]

basic_colors = {
  'красный': [253, 0, 0],
  'зеленый': [0, 253, 0],
  'синий': [0, 0, 253],
  'белый': [253, 253, 253],
  'черный': [254, 254, 254],
}

def set_bulb_color(color, bulb):
  if(color == [0, 0, 0]):
    bulb.turn_off()
  else:
    bulb.turn_on()
    if color in basic_colors:
      color = basic_colors[color]
    else:
      color = process(calc_color(load(color)))
    bulb.set_rgb(*[int(x) for x in color])

def load(name):
  response = google_images_download.googleimagesdownload()   #class instantiation
  print "NAME OF COLOR"
  arguments = {"keywords":name,"limit":1,"print_urls":True}   #creating list of arguments
  paths = response.download(arguments)   #passing the arguments to the function
  byte_val = name.encode('utf-8')
  return paths[byte_val][0]  #printing absolute paths of the downloaded images

def calc_color(path):
  f = open(path, 'rb')
  pic = f.read()
  f.close()
  type = path[path.rfind(".") + 1::]
  if (type == "jpeg") or (type == "jpg"):
    loader = gtk.gdk.PixbufLoader('jpeg')
  elif(type == 'png'):
    loader = gtk.gdk.PixbufLoader('png')
  else:
    print "Wrong type"
  loader.write(pic)
  loader.close()

  pb = loader.get_pixbuf()
  array = pb.get_pixels_array()
  avg_color_per_row = numpy.average(array, axis=0)
  avg_color = numpy.average(avg_color_per_row, axis=0)
  return avg_color

def led_color(color, sock):
  if color in basic_colors:
    color = basic_colors[color]
  else:
    color = process(calc_color(load(color)))
  send(color, sock)


def process(array):
  res = []
  array[0] = array[0] + 1
  array[1] = array[1] + 1
  array[2] = array[2] + 1
  denominator = array[0] * array[1] * array[2]
  sum = (array[0] + array[1] + array[2]) / (256.0 * 3.0)
  max = 0
  for color in range(0, 3):
    current_denominator = (denominator / array[color]) / (256.0 * 256.0)
    value = (array[color] / 256.0) / current_denominator
    array[color] = value
    if(max < array[color]):
      max = array[color]
    res.append(int(array[color]))
  res[0] = int(min(3.0 * math.pow((res[0] / max), 3.0), 1.0) * 253.0) * sum
  res[1] = int(min(3.0 * math.pow((res[1] / max), 3.0), 1.0) * 253.0) * sum
  res[2] = int(min(3.0 * math.pow((res[2] / max), 3.0), 1.0) * 253.0) * sum
  return res

def new_val(old_val):
  res = old_val
  while res == old_val:
    res = random.randint(0, len(nice_colors) - 1) 
  return res

def send(color, sock):
  rgbStr = []
  for i in range(0,3):
    rgbStr.append(chr(int(color[i])))
  rgbStr.append(chr(int(255)))
  res = ''.join(rgbStr)
  sock.send(res)


def equalizer(sock):
    STAGE_COUNT = 50
    _stage = 0
    _from = 0
    _to = 0
    _res = nice_colors[0]
    while True:
      time.sleep(0.05)
      if _stage == 0:
        _from = _to
        _to = new_val(_from)
        _offset = map(operator.sub, nice_colors[_to], nice_colors[_from])
        _res = nice_colors[_from]
        _offset = list(map(lambda x: x / (STAGE_COUNT + 1), _offset))
        _stage = STAGE_COUNT
      else:
        _res = map(operator.add, _res, _offset)
        _stage = _stage - 1
        send(_res, sock)

def capture(sock):
  last = [0,0,0]
  while True:
    w = gtk.gdk.get_default_root_window()
    sz = w.get_size()
    pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB,False,8,sz[0],sz[1])
    pb = pb.get_from_drawable(w,w.get_colormap(),0,0,0,0,sz[0],sz[1])
    array = pb.get_pixels_array()
    avg_color_per_row = numpy.average(array, axis=0)
    avg_color = numpy.average(avg_color_per_row, axis=0)
    color = process(avg_color)
    if(color != last):
      time.sleep(0.025)
      send(color, sock)
      last = color
