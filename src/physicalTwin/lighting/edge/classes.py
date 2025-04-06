import sys, os, time
# Library to control GrovePi sensors/actuators 
# repo of GrovePi https://github.com/DexterInd/GrovePi/tree/master
from grovepi import *
# MQTT client for message publishing
import paho.mqtt.client as mqtt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

# Edge device class for the traffic light system.
# Initializes the sensor module and starts the traffic cycle.
class PTLightingEdge:
    def __init__(self, credentials, broker, port):
        self.credentials = credentials
        self.broker = broker
        self.port = port
        self.sensor = PTLightingSensor(self.credentials, self.broker, self.port)
        
    def startPTedge(self):
        self.sensor.run_traffic_cycle()
        
# Traffic light sensor class that controls LED lights via GrovePi and
# publishes their status using MQTT.
class PTLightingSensor:
    def __init__(self, credentials, broker, port):
        self.credentials = credentials
        self.broker = broker
        self.port = port
        
        self.client = mqtt.Client()

        # Authenticate with RabbitMQ MQTT
        self.client.username_pw_set(self.credentials["username"], self.credentials["password"])
        self.client.connect(self.broker, self.port)
        self.client.loop_start()
        
        # Define the pins for red, yellow, and green LEDs
        self.red_led = 2
        self.yellow_led = 3
        self.green_led = 4
        
        # Set the LED pins as outputs
        pinMode(self.red_led, "OUTPUT")
        pinMode(self.yellow_led, "OUTPUT")
        pinMode(self.green_led, "OUTPUT")
        
    def set_lights(self, red, yellow, green, duration):
        
        """
        Set the state of the traffic lights and publish the status via MQTT.

        Args:
            red (int): 1 to turn ON the red LED, 0 to turn it OFF.
            yellow (int): 1 to turn ON the yellow LED, 0 to turn it OFF.
            green (int): 1 to turn ON the green LED, 0 to turn it OFF.
            duration (int): Duration in seconds to maintain this state.
        """
        
        digitalWrite(self.red_led, red)
        digitalWrite(self.yellow_led, yellow)
        digitalWrite(self.green_led, green)
        
        # Create a dictionary with the current status and publish it to MQTT topics
        status = {'red': red, 'yellow': yellow, 'green': green}
        self.client.publish("traffic/light/status", str(status)) 
        self.client.publish("DT/lights/status", str(status))
    
        print(f"Lights: Red={red}, Yellow={yellow}, Green={green}")
        time.sleep(duration)

    def run_traffic_cycle(self):
        while True:
            try:
                self.set_lights(1, 0, 0, 10)  # Red ON for 10s
                self.set_lights(0, 0, 1, 10)  # Green ON for 10s
                
                # Green Blinking for 5s (1s ON, 1s OFF)
                # for _ in range(5):
                #     self.set_lights(0, 0, 1, 1)  
                #     self.set_lights(0, 0, 0, 1)

                self.set_lights(0, 1, 0, 5)  # Yellow ON for 5s
            except KeyboardInterrupt:
                self.cleanup()
                break

    def cleanup(self):
        digitalWrite(self.red_led, 0)
        digitalWrite(self.yellow_led, 0)
        digitalWrite(self.green_led, 0)
        print("Traffic light system stopped.")