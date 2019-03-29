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
from pathlib import Path
import bluetooth
from google_images_download import google_images_download   #importing the library
from multiprocessing import Process
import lex_token
import led

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
    res = random.randint(0, 4) 
  return res

def send(color, sock):
  rgbStr = []
  for i in range(0,3):
    rgbStr.append(chr(int(color[i])))
  rgbStr.append(chr(int(255)))
  res = ''.join(rgbStr)
  sock.send(res)
