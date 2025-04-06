import sys, os, time, math
import grovepi                      # GrovePi library for sensor interactions
import paho.mqtt.client as mqtt     # MQTT client library for messaging
import threading                    # For running tasks in parallel
import termios, tty, select         # For capturing keyboard input
import smbus                        # For I2C communications (LCD)
import RPi.GPIO as GPIO             # For Raspberry Pi GPIO control

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

# Triggering a disturbance
# Read a single keypress from standard input with a timeout.
# Returns the key as a string if pressed, otherwise None.
def get_key(timeout=0.1):
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        r, w, e = select.select([sys.stdin], [], [], timeout)
        if r:
            return sys.stdin.read(1)
        return None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

# Edge class for bin management.
# Initializes the bins sensor and starts sensor monitoring.
class PTBinsEdge:
    def __init__(self, credentials, broker, port):
        self.credentials = credentials
        self.broker = broker
        self.port = port
        self.sensor = PTBinsSensor(self.credentials, self.broker, self.port)
        
    def startPTedge(self):
        self.sensor.run_ultrasonic_dht()

# Sensor class to handle MQTT messages and control an LCD display.
# It subscribes to a disturbance topic and updates the LCD accordingly.
class PTBinsSensor:
    def __init__(self, credentials, broker, port):
        self.credentials = credentials
        self.broker = broker
        self.port = port
        
        # LCD
        self.lcd = LCD()
        initial_message = "Starting..."
        self.lcd.setText(initial_message)
        self.lcd.setRGB(0, 128, 64)
        self.last_lcd_message = initial_message
        
        self.client = mqtt.Client()

        # Authenticate with RabbitMQ MQTT
        self.client.username_pw_set(self.credentials["username"], self.credentials["password"])
        self.client.connect(self.broker, self.port)
        self.client.on_message = self.on_message
        
        # Queues from CS1 and CS3
        self.client.subscribe("DT/bins/disturbed/")
        self.client.loop_start()
        
    def on_message(self, client, userdata, message):
        try:
            topic = message.topic
            payload = message.payload.decode().strip()
            
            if topic == "DT/bins/disturbed/":
                # Only update if the payload has changed
                if payload != self.last_lcd_message:
                    self.lcd.setText(payload)
                    self.last_lcd_message = payload
                    print("LCD updated with message:", payload)
                    
                    # Change color based on the message content
                    if payload.lower() == "no disturbance":
                        # Green: (R, G, B)
                        self.lcd.setRGB(0, 255, 0)
                    elif payload.lower() == "bin 1 is disturbed":
                        # Red
                        self.lcd.setRGB(255, 0, 0)
                    elif payload.lower() == "bin 2 is disturbed":
                        # Orange (approximate)
                        self.lcd.setRGB(255, 165, 0)
                    else:
                        # Optionally set a default color if needed
                        self.lcd.setRGB(0, 128, 64)
        except Exception as e:
            print("Error parsing MQTT message:", e)
            
    def run_ultrasonic_dht(self):
        ptultra = PTUltrasonicDHT(self.client)
        ptultra.runUltrasonicDHT()
            
        
class PTUltrasonicDHT(PTBinsSensor):
    def __init__(self, client):
        self.client = client
        self.threshold = 90 
        self.stop_flag = False
        # Flags to control if sensor data should be published for each bin.
        self.bin1_disturbed = False
        self.bin2_disturbed = False
        self.input_thread = threading.Thread(target=self.key_listener)
        self.input_thread.start()

    def key_listener(self):
        print("Keyboard listener active. Press '1' or '2' to send disturbances continuously until you press space.")
        while not self.stop_flag:
            key = get_key(timeout=0.1)
            if key == '1':
                print("Sending continuous disturbance for bin 1. Press space to stop.")
                self.bin1_disturbed = True
                while True:
                    # Check if space bar is pressed to stop disturbance for bin 1.
                    sp = get_key(timeout=0.1)
                    if sp == ' ':
                        print("Stopped disturbance for bin 1.")
                        self.bin1_disturbed = False
                        break
                    self.client.publish("DT/bins/1", "{'distance': -1, 'temperature': -1, 'humidity': -1}")
                    time.sleep(0.1)  # Adjust the rate as needed
            elif key == '2':
                print("Sending continuous disturbance for bin 2. Press space to stop.")
                self.bin2_disturbed = True
                while True:
                    sp = get_key(timeout=0.1)
                    if sp == ' ':
                        print("Stopped disturbance for bin 2.")
                        self.bin2_disturbed = False
                        break
                    self.client.publish("DT/bins/2", "{'distance': -1, 'temperature': -1, 'humidity': -1}")
                    time.sleep(0.1)
            # Small sleep to prevent busy waiting
            time.sleep(0.1)
            
    def runUltrasonicDHT(self):         
        ultrasonic_ranger = 3
        dht_sensor = 7
        ultrasonic_ranger2 = 4
        try:
            while not self.stop_flag:
                # Read distance value from ultrasonic ranger
                distance = grovepi.ultrasonicRead(ultrasonic_ranger)
                distance2 = grovepi.ultrasonicRead(ultrasonic_ranger2)
                
                percentage1= 100-((distance*100)/11)
                percentage2= 100-((distance2*100)/11)
                
                [temp, humidity] = grovepi.dht(dht_sensor, 0)
                
                bin1 = {'distance': distance, 'temperature': temp, 'humidity': humidity}
                bin2 = {'distance': distance2, 'temperature': temp, 'humidity': humidity}
                
                print("bin1: ", bin1)
                print("bin2: ",bin2)
                
                if not self.bin1_disturbed:
                    self.client.publish("DT/bins/1", str(bin1))
                if not self.bin2_disturbed:
                    self.client.publish("DT/bins/2", str(bin2))
                        
                if math.isnan(temp) == False and math.isnan(humidity) == False:
                    
                    print("temp = %.02f C humidity =%.02f%%"%(temp, humidity))
                
                    if not self.bin1_disturbed:
                        is_critical = (humidity >= 80 or temp >= 50)
                        
                        if percentage1 >= self.threshold:
                            priority = 1
                        elif is_critical:
                            priority = 2
                        else:
                            priority = 0
                            
                        print(priority)
                        if priority == 1 or priority == 2 :
                            self.client.publish("bins/1", str(priority))  # Notify fleet
                            # self.client.publish("DT/bin/full", str(priority))  # Notify DT
                    if not self.bin2_disturbed:    
                        if percentage2 >= self.threshold:
                            priority = 1
                            self.client.publish("bins/2", str(priority))  # Notify fleet
                        
                time.sleep(1)
                            
        except TypeError:
            print("Error")
        except IOError:
            print("Error")
        
class LCD:
    def __init__(self):
        # Initialize I2C bus based on platform and board revision
        if sys.platform == 'uwp':
            import winrt_smbus as wsmbus
            self.bus = wsmbus.SMBus(1)
        else:
            rev = GPIO.RPI_REVISION
            if rev == 2 or rev == 3:
                self.bus = smbus.SMBus(1)
            else:
                self.bus = smbus.SMBus(0)
        self.DISPLAY_RGB_ADDR = 0x62
        self.DISPLAY_TEXT_ADDR = 0x3e

    def setRGB(self, r, g, b):
        self.bus.write_byte_data(self.DISPLAY_RGB_ADDR, 0, 0)
        self.bus.write_byte_data(self.DISPLAY_RGB_ADDR, 1, 0)
        self.bus.write_byte_data(self.DISPLAY_RGB_ADDR, 0x08, 0xaa)
        self.bus.write_byte_data(self.DISPLAY_RGB_ADDR, 4, r)
        self.bus.write_byte_data(self.DISPLAY_RGB_ADDR, 3, g)
        self.bus.write_byte_data(self.DISPLAY_RGB_ADDR, 2, b)

    def textCommand(self, cmd):
        self.bus.write_byte_data(self.DISPLAY_TEXT_ADDR, 0x80, cmd)

    def setText(self, text):
        # Clear display and set initial commands for 2-line display
        self.textCommand(0x01)  # clear display
        time.sleep(0.05)
        self.textCommand(0x08 | 0x04)  # display on, no cursor
        self.textCommand(0x28)  # 2 lines
        time.sleep(0.05)
        count = 0
        row = 0
        for c in text:
            if c == '\n' or count == 16:
                count = 0
                row += 1
                if row == 2:
                    break
                self.textCommand(0xc0)
                if c == '\n':
                    continue
            count += 1
            self.bus.write_byte_data(self.DISPLAY_TEXT_ADDR, 0x40, ord(c))

    def setText_norefresh(self, text):
        # Update display without clearing the entire display
        self.textCommand(0x02)  # return home
        time.sleep(0.05)
        self.textCommand(0x08 | 0x04)  # display on, no cursor
        self.textCommand(0x28)  # 2 lines
        time.sleep(0.05)
        count = 0
        row = 0
        while len(text) < 32:  # Pad text to clear previous characters
            text += ' '
        for c in text:
            if c == '\n' or count == 16:
                count = 0
                row += 1
                if row == 2:
                    break
                self.textCommand(0xc0)
                if c == '\n':
                    continue
            count += 1
            self.bus.write_byte_data(self.DISPLAY_TEXT_ADDR, 0x40, ord(c))

    def create_char(self, location, pattern):
        """
        Writes a bit pattern to LCD CGRAM
        
        Arguments:
            location -- integer, one of 8 slots (0-7)
            pattern -- byte array containing the bit pattern
        """
        location &= 0x07  # Ensure location is within 0-7
        self.textCommand(0x40 | (location << 3))
        self.bus.write_i2c_block_data(self.DISPLAY_TEXT_ADDR, 0x40, pattern)