import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from mainClasses import SoSPTFleet
from classes import *

credentials = {"username": "admin", "password": "admin"}
broker = "localhost"
port = 1883

sospt = SoSPTFleet(credentials, broker, port, "SmartCitySoS")

sospt.runComponentFleet()
