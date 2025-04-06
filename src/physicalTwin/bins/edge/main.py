import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from mainClasses import SoSPTBins
from classes import *

credentials = {"username": "admin", "password": "admin"}
broker = "192.168.8.204"
port = 1883

sospt = SoSPTBins(credentials, broker, port, "SmartCitySoS")

sospt.runComponentBins()
