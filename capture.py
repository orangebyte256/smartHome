from led import * 
from devices import * 
import gtk.gdk
import math
import numpy
import time
from defines import *

bluetooth_sock = connect(MAC_BLUETOOTH)
last = [0,0,0]
w = gtk.gdk.get_default_root_window()
sz = w.get_size()
pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB,False,8,sz[0],sz[1])
while True:
    pb = pb.get_from_drawable(w,w.get_colormap(),0,0,0,0,sz[0],sz[1])
    array = pb.get_pixels_array()
    avg_color_per_row = numpy.average(array, axis=0)
    avg_color = numpy.average(avg_color_per_row, axis=0)
    color = process(avg_color)
    if(color != last):
        time.sleep(0.025)
        send(color, bluetooth_sock)
        last = color
