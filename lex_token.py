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

def token_exist(elements, value):
  for elem in elements:
    if value == elem:
      return True
  return False

def token_partly_exist(elements, value):
  for elem in elements:
    if value in elem:
      return True
  return False

def is_on(elements):
  return token_partly_exist(elements, u'вклю')


def is_off(elements):
  return token_partly_exist(elements, u'выклю')

def pos_response():
  res = dict()
  res["text"] = "О, да! Это я могу!"
  res["tts"] = "<speaker effect=\"hamster\">О, да! -- Это я могу!"
  res["end_session"] = True
  return res

def neg_response():
  res = dict()
  res["text"] = "О, нет! Это я не могу!"
  res["tts"] = "<speaker effect=\"hamster\">О, нет! -- Это я не могу!"
  res["end_session"] = True
  return res

def custom_responce(text):
  res = dict()
  res["text"] = text
  res["tts"] = "<speaker effect=\"hamster\">" + text
  res["end_session"] = True
  return res
