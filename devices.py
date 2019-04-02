import pytuya
import subprocess, os

def set_switch(ip, id, key, state):
    d = pytuya.OutletDevice(id, ip, key)
    d.set_status(state)

def cleaner_command(ip, token, dir, command):
    my_env = os.environ.copy()
    my_env["MIROBO_IP"] = ip
    my_env["MIROBO_TOKEN"] = token
    my_env["LC_ALL"] = "C.UTF-8"
    my_env["LANG"] = "C.UTF-8"
    subprocess.Popen([dir, command], env=my_env)
