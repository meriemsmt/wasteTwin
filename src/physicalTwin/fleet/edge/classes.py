import sys, os, time, threading, ast
# Library to control Raspberry Pi GPIO pins
import RPi.GPIO as GPIO
# MQTT client for message communication
import paho.mqtt.client as mqtt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

# Edge class for fleet management.
# It initializes the sensor module and starts the truck fleet simulation.
class PTFleetEdge:
    def __init__(self, credentials, broker, port):
        self.credentials = credentials
        self.broker = broker
        self.port = port
        self.sensor = PTFleetSensor(self.credentials, self.broker, self.port)
        
    def startPTedge(self):
        self.sensor.startFleetTrucks()
    
# Sensor class that manages truck statuses based on MQTT messages.
# It listens to traffic light and bin sensor topics to update truck control signals.
class PTFleetSensor:
    def __init__(self, credentials, broker, port):
        self.credentials = credentials
        self.broker = broker
        self.port = port
        
        self.client = mqtt.Client()
        self.client.username_pw_set(self.credentials["username"], self.credentials["password"])
        self.client.connect(self.broker, self.port)
        self.client.on_message = self.on_message
        
        # Subscribe to topics for traffic light and bin sensors
        # Queues from CS1 and CS3
        self.client.subscribe("traffic/light/status")
        self.client.subscribe("bins/*")
        
        # Queues from DT 
        self.client.subscribe("DT/bins/truck/")
        self.client.loop_start()
        
        # Traffic status values: 0 = stopped, 2 = moving (default)
        self.traffic_status = 2   
        self.traffic_status2 = 2
        
        # Setup GPIO Buttons for Braking
        self.BUTTON_TRUCK1 = 15  # Physical Pin 15 27
        self.BUTTON_TRUCK2 = 13  # Physical Pin 13 22
        
        # Configure GPIO mode and setup button inputs with pull-up resistors
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.BUTTON_TRUCK1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.BUTTON_TRUCK2, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # Callback to process incoming MQTT messages.
    # Updates truck status based on traffic light changes and bin sensor readings.
    def on_message(self, client, userdata, message):
        try:
            topic = message.topic
            payload = message.payload.decode()

            if topic == "traffic/light/status":
                # Convert the payload string to a dictionary (eval used for simplicity)
                status = eval(payload) 
                
                # For Truck 1: if button pressed and red light active, stop truck
                if GPIO.input(self.BUTTON_TRUCK1) == GPIO.LOW and status['red'] == 1:
                    print("Truck 1 Stopped by red light")
                    self.traffic_status = 0
                # For yellow or green, ensure trucks are moving
                elif status.get('yellow', 0) == 1 or status.get('green', 0) == 1:
                    self.traffic_status = 2
                    self.traffic_status2 = 2
                
                # For Truck 2: if button pressed and red light active, stop truck
                if GPIO.input(self.BUTTON_TRUCK2) == GPIO.LOW and status['red'] == 1:
                    print("Truck 2 Stopped by red light")
                    self.traffic_status2 = 0
                    
            elif topic == "DT/bins/truck/":
                # Safely parse payload into a list using ast.literal_eval
                closestTruck = ast.literal_eval(payload)
                print(closestTruck)
                
                # Validate that the payload is a list with three items:
                # [truck_id, distance, bin_id]
                if isinstance(closestTruck, list) and len(closestTruck) == 3:
                    truck_id = int(closestTruck[0])
                    distance = float(closestTruck[1]) 
                    bin_id = int(closestTruck[2])
                    
                    # Process for bin 2
                    if bin_id == 2:
                        if truck_id == 1:
                            print('Truck is closer to bin2')
                            if int(distance) < 10 and GPIO.input(self.BUTTON_TRUCK1) == GPIO.LOW:
                                print("Truck 1 stopped by bin2")
                                self.traffic_status = 0
                                self.client.publish("DT/trucks/1/collect", str(2))
                                time.sleep(5)
                                                        
                                
                        elif truck_id == 2:
                            print('Truck2 is closer to bin2')
                            if int(distance) < 10 and GPIO.input(self.BUTTON_TRUCK1) == GPIO.LOW:
                                print("Truck 2 stopped by bin2")
                                self.traffic_status2 = 0
                                self.client.publish("DT/trucks/2/collect", str(2))
                                time.sleep(5)
                        else:
                            print('unknow truck id')
                    # Process for bin 1        
                    elif bin_id == 1:
                        if truck_id == 1:
                            print('Truck1 is closer to bin2')
                            if int(distance) < 10 and GPIO.input(self.BUTTON_TRUCK2) == GPIO.LOW:
                                print("Truck 1 stopped by bin1")
                                self.traffic_status = 0
                                self.client.publish("DT/trucks/1/collect", str(1))
                                time.sleep(5)  
                        elif truck_id == 2:
                            print('Truck2 is closer to bin1')
                            if int(distance) < 10 and GPIO.input(self.BUTTON_TRUCK2) == GPIO.LOW:
                                print("Truck2 stopped by bin1")
                                self.traffic_status2 = 0
                                self.client.publish("DT/trucks/2/collect", str(1))
                                time.sleep(5)
                    else:
                        print("unknown bin id")
               
                else:
                    print('Error: Unexpected payload format')
                
                
        except Exception as e:
            print("Error parsing MQTT message:", e)
    
    # Starts the operation of fleet trucks by initializing truck objects
    # and running their control loops in separate threads so that they operate in real-time and independently
    def startFleetTrucks(self):
        print('Starting fleet trucks...')
        pttruck1 = PTTruck1()
        pttruck2 = PTTruck2()
        
        # Setup trucks (initialize GPIO and PWM for servo control)
        pttruck1.setup_truck()
        pttruck2.setup_truck()
        
        # Define control loop for Truck 1
        def run_truck1():
            while True:
                if GPIO.input(self.BUTTON_TRUCK1) == GPIO.LOW:  # Button pressed → Stop truck
                    self.traffic_status = 0
                else:
                    self.traffic_status = 2
                self.client.publish("DT/trucks/1/status", str(self.traffic_status))
                pttruck1.runTruck(self.traffic_status, self.BUTTON_TRUCK1)    
                time.sleep(0.1)  # Small delay to prevent overload

        def run_truck2():
            while True:
                if GPIO.input(self.BUTTON_TRUCK2) == GPIO.LOW:  # Button pressed → Stop truck
                    self.traffic_status2 = 0
                else:
                    self.traffic_status2 = 2
                self.client.publish("DT/trucks/2/status", str(self.traffic_status2))
                pttruck2.runTruck(self.traffic_status2, self.BUTTON_TRUCK2)
                time.sleep(0.1)
                
                
        truck1_thread = threading.Thread(target=run_truck1)
        truck2_thread = threading.Thread(target=run_truck2)
        
        try:
            truck1_thread.start()
            truck2_thread.start()
            while True:
                time.sleep(1)
        
        except KeyboardInterrupt:
            pttruck1.stopTruck()
            pttruck2.stopTruck()
            GPIO.cleanup()

class PTTruck:
    def __init__(self, pin):
        self.pin = pin
        self.servo = None
    
    def setup_truck(self):
        GPIO.setup(self.pin, GPIO.OUT)
        self.servo = GPIO.PWM(self.pin, 50)
        self.servo.start(0)
        time.sleep(2)
        
    def runTruck(self, traffic_status, button_pin):
        if traffic_status == 0:
            self.servo.ChangeDutyCycle(0)  # Stop
            return

        elif traffic_status == 2:
            for duty in range(2, 13):  # Move normally (green)
                if GPIO.input(button_pin) == GPIO.LOW:  # Check button state
                    self.servo.ChangeDutyCycle(0)  # Stop immediately
                    return
            self.servo.ChangeDutyCycle(duty)
            time.sleep(0.1)  # Small delay
        
        self.servo.ChangeDutyCycle(7.5)

        time.sleep(1)


    def stopTruck(self):
        self.servo.ChangeDutyCycle(0)
        time.sleep(0.5)
        self.servo.stop()
        
class PTTruck1(PTTruck):
    def __init__(self):
        super().__init__(11)
        
class PTTruck2(PTTruck):
    def __init__(self):
        super().__init__(12)
