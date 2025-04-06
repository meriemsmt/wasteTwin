extends Node3D  # Ensure this is attached to your Node3D
 
# red light
@export var redlight: Node3D
@export var on = false # by default the red light is off
@export var on_mat: StandardMaterial3D
@export var off_mat: StandardMaterial3D

# yellow light
@export var yellowlight: Node3D
@export var yellowon = false  
@export var yellow_on_mat: StandardMaterial3D
@export var yellow_off_mat: StandardMaterial3D

# green light
@export var greenlight: Node3D
@export var greenon = false  
@export var green_on_mat: StandardMaterial3D
@export var green_off_mat: StandardMaterial3D

# trash
#@export var trash: Node3D
@onready var bin = get_node("TrashBins/TrashBin/bin")
@onready var bin2 = get_node("TrashBins/TrashBin2/bin2")
var current_delta = 0.0 
var stop = false
var is_connec = false
var last_status_truck1 = -1
var last_status_truck2 = -1

const MOVE_SPEED := 20.0

@export var clear_sky: Sky
@export var cloudy_sky: Sky
#@onready var world_env: WorldEnvironment = get_node("WorldEnvironment")

@onready var audio_player: AudioStreamPlayer = get_node("AudioPlayer")
@export var city_sound: AudioStream
@export var rain_sound: AudioStream

func _ready():
	connect_to_broker()
	# Connect necessary signals
	if not %MQTT.is_connected("received_message", Callable(self, "_on_mqtt_message")):
		%MQTT.connect("received_message", Callable(self, "_on_mqtt_message"))
	if not %MQTT.is_connected("broker_connected", Callable(self, "_on_mqtt_broker_connected")):
		%MQTT.connect("broker_connected", Callable(self, "_on_mqtt_broker_connected"))

	if not %MQTT.is_connected("broker_connection_failed", Callable(self, "_on_mqtt_broker_connection_failed")):
		%MQTT.connect("broker_connection_failed", Callable(self, "_on_mqtt_broker_connection_failed"))
		
	

func connect_to_broker():
	
	%MQTT.client_id = "godot_client"  # Set a unique client ID

	# Set username and password
	%MQTT.set_user_pass("admin", "admin")

	# Connect to the RabbitMQ broker at 192.168.8.204, port 1883
	var broker_url = "tcp://192.168.8.204:1883"
	var success = %MQTT.connect_to_broker(broker_url)

	if not success:
		print("ERROR: Failed to connect to the broker.")

# Callback when successfully connected
func _on_mqtt_broker_connected():
	
	print("Successfull connection to the broker")
	is_connec = true
	# Subscribe to topics
	%MQTT.subscribe("DT/trucks/1/status")
	%MQTT.subscribe("DT/trucks/2/status")
	%MQTT.subscribe("DT/lights/status")
	%MQTT.subscribe("DT/bins/*")
	%MQTT.subscribe("DT/trucks/1/collect")
	%MQTT.subscribe("DT/trucks/2/collect")
	
	
	#%MQTT.subscribe("DT/bin/full")

# Callback when connection fails
func _on_mqtt_broker_connection_failed():
	print("ERROR: Connection failed.")
	
func _on_mqtt_received_message(topic: String, message: String):
	
	match topic:
		"DT/trucks/1/status":
			#print("Truck 1 Status: " + message)
			truck1_actions(message)
		"DT/trucks/2/status":
			#print("Truck 2 Status: " + message)
			truck2_actions(message)
		"DT/lights/status":
			lights1_actions(message)
		#"DT/bin/full":
			#print("Bin status: " + message)
		"DT/bins/1":
			bin1_actions(message)
		"DT/bins/2":
			bin2_actions(message)
		"DT/trucks/1/collect":
			truck1_collect(message)
		"DT/trucks/2/collect":
			truck2_collect(message)
		_:
			print("Unknown topic (" + topic + "): " + message)

func lights1_actions(message):
	var valid_message = message.replace("'", "\"")
	var json = JSON.new()
	var json_result = json.parse(valid_message)

	if json_result == OK:
		var message_dict = json.get_data()   
				
		if message_dict is Dictionary:
			if message_dict == {"red": 0, "yellow": 0, "green": 0}:
				print("off")
				redlight.get_node("redlight").visible = !on # on is the variable value
			else:
				for key in message_dict.keys():
					if message_dict[key] == 1:
						print(key)
						match key:
							"red":
								redlight.get_node("redlight").visible = on
								yellowlight.get_node("yellowlight").visible = !yellowon
								greenlight.get_node("greenlight").visible = !greenon
								stop = true
							"green":
								redlight.get_node("redlight").visible = !on 
								yellowlight.get_node("yellowlight").visible = !yellowon
								greenlight.get_node("greenlight").visible = greenon
								stop = false
							"yellow":
								redlight.get_node("redlight").visible = !on 
								yellowlight.get_node("yellowlight").visible = yellowon
								greenlight.get_node("greenlight").visible = !greenon
								stop = true
							_:
								print("Unknown key (" + key + ") " )
		else:
			print("Lights1 parsed data is not a dictionary:", message_dict)
	else:
		print("Error parsing JSON, error code:", json_result)
	
		
func bin1_actions(bin1):
	var valid_bin1 = bin1.replace("'", "\"")
	var json = JSON.new()
	var json_result = json.parse(valid_bin1)
	if json_result == OK:
		var bin1_dict = json.get_data()   
		
		# Accessing individual elements
		var distance = bin1_dict["distance"]
		var temperature = bin1_dict["temperature"]
		var humidity = bin1_dict["humidity"]
		
		var bin1_temp_label = %temp as Label3D
		var bin1_humidity_label = %humidity as Label3D
		var bin1_fill_label = %fill_level as Label3D
		var fill_percentage = 100-((distance*100)/11)
		
		var distance_to_truck1 = %bin.global_position.distance_to(%Truck.global_position)
		var distance_to_truck2 = %bin.global_position.distance_to(%Truck2.global_position)
		var send_to_trucks = []

		if int(distance) == -1 : 
			print("Bin 1 is disturbed")
			bin1_disturbed = true
		else:
			bin1_disturbed = false
			bin1_fill_label.text = "Bin 1 Fill Level: " + str(snapped(fill_percentage, 0.01)) + "%" # 11 iss the depth of the bin
			bin1_temp_label.text = "Bin 1 Temperature: " + str(snapped(temperature, 0.01)) + "°C"
			bin1_humidity_label.text = "Bin 1 Humidity: " + str(snapped(humidity, 0.01))
			
			if fill_percentage>=70:
				print("BIN ALMOST FILLED, INFORM TRUCK FLEET...")
				
				if distance_to_truck1 < distance_to_truck2:
					print("Truck is closer to Bin")
					send_to_trucks = [1,distance_to_truck1,1]
					%MQTT.publish("DT/bins/truck/", str(send_to_trucks))
				else:
					print("Truck2 is closer to Bin")
					send_to_trucks =[2,distance_to_truck2,1]
					%MQTT.publish("DT/bins/truck/", str(send_to_trucks))
					
				bin.find_child("trash10").visible = true
				bin.find_child("trash9").visible = true
				bin.find_child("trash8").visible = true
				bin.find_child("trash7").visible = true
				bin.find_child("trash6").visible = true
				bin.find_child("trash5").visible = true
				bin.find_child("trash4").visible = true
				bin.find_child("trash3").visible = true
				bin.find_child("trash2").visible = true
				bin.find_child("trash1").visible = true
			else:
				if fill_percentage>72 and not bin.find_child("trash9").visible:
					bin.find_child("trash9").visible = true
					bin.find_child("trash8").visible = true
					bin.find_child("trash7").visible = true
					bin.find_child("trash6").visible = true
					bin.find_child("trash5").visible = true
					bin.find_child("trash4").visible = true
					bin.find_child("trash3").visible = true
					bin.find_child("trash2").visible = true
					bin.find_child("trash1").visible = true
				elif fill_percentage>64 and not bin.find_child("trash8").visible:
					bin.find_child("trash8").visible = true
					bin.find_child("trash7").visible = true
					bin.find_child("trash6").visible = true
					bin.find_child("trash5").visible = true
					bin.find_child("trash4").visible = true
					bin.find_child("trash3").visible = true
					bin.find_child("trash2").visible = true
					bin.find_child("trash1").visible = true
				elif fill_percentage>56 and not bin.find_child("trash7").visible:
					bin.find_child("trash7").visible = true
					bin.find_child("trash6").visible = true
					bin.find_child("trash5").visible = true
					bin.find_child("trash4").visible = true
					bin.find_child("trash3").visible = true
					bin.find_child("trash2").visible = true
					bin.find_child("trash1").visible = true
				elif fill_percentage>48 and not bin.find_child("trash6").visible:
					bin.find_child("trash6").visible = true
					bin.find_child("trash5").visible = true
					bin.find_child("trash4").visible = true
					bin.find_child("trash3").visible = true
					bin.find_child("trash2").visible = true
					bin.find_child("trash1").visible = true
				elif fill_percentage>40 and not bin.find_child("trash5").visible:
					bin.find_child("trash5").visible = true
					bin.find_child("trash4").visible = true
					bin.find_child("trash3").visible = true
					bin.find_child("trash2").visible = true
					bin.find_child("trash1").visible = true
				elif fill_percentage>32 and not bin.find_child("trash4").visible:
					bin.find_child("trash4").visible = true
					bin.find_child("trash3").visible = true
					bin.find_child("trash2").visible = true
					bin.find_child("trash1").visible = true
				elif fill_percentage>24 and not bin.find_child("trash3").visible:
					bin.find_child("trash3").visible = true
					bin.find_child("trash2").visible = true
					bin.find_child("trash1").visible = true
				elif fill_percentage>16 and not bin.find_child("trash2").visible:
					bin.find_child("trash2").visible = true
					bin.find_child("trash1").visible = true
				elif fill_percentage>8 and not bin.find_child("trash1").visible:
					bin.find_child("trash1").visible = true
		
	else:
		print("Error parsing JSON, error code:", json_result)
	update_particles()
		 
func bin2_actions(bin2message):
	var valid_bin2 = bin2message.replace("'", "\"")
	var json = JSON.new()
	var json_result = json.parse(valid_bin2)
	if json_result == OK:
		var bin2_dict = json.get_data()   
		
		# Accessing individual elements
		var distance = bin2_dict["distance"]
		var temperature = bin2_dict["temperature"]
		var humidity = bin2_dict["humidity"]
		
		var bin2_temp_label = %temp2 as Label3D
		var bin2_humidity_label = %humidity2 as Label3D
		var bin2_fill_label = %fill_level2 as Label3D
		var fill_percentage = 100-((distance*100)/11)
		
		var distance_to_truck1 = %bin2.global_position.distance_to(%Truck.global_position)
		var distance_to_truck2 = %bin2.global_position.distance_to(%Truck2.global_position)
		var send_to_trucks = []
		
		if int(distance) == -1 : 
			print("Bin 2 is disturbed")
			bin2_disturbed = true
		else:
			bin2_disturbed = false
			bin2_fill_label.text = "Bin 2 Fill Level: " + str(snapped(fill_percentage, 0.01)) + "%" # 11 iss the depth of the bin
			bin2_temp_label.text = "Bin 2 Temperature: " + str(snapped(temperature, 0.01)) + "°C"
			bin2_humidity_label.text = "Bin 2 Humidity: " + str(snapped(humidity, 0.01))
			
			if fill_percentage>=80:
				print("BIN2 ALMOST FILLED, INFORM TRUCK FLEET...")
				
				if distance_to_truck1 < distance_to_truck2:
					print("Truck is closer to Bin2")
					
					%log_truck1.text = "Notification received from Bin2. Truck1 closer"
					send_to_trucks = [1, distance_to_truck1,2]
					%MQTT.publish("DT/bins/truck/", str(send_to_trucks))
				else:
					print("Truck2 is closer to Bin2")
					
					%log_truck2.text = "Notification received from Bin2. Truck2 closer"
					
					send_to_trucks = [2, distance_to_truck2,2]
					%MQTT.publish("DT/bins/truck/", str(send_to_trucks))
					
				bin2.find_child("trash10").visible = true
				bin2.find_child("trash9").visible = true
				bin2.find_child("trash8").visible = true
				bin2.find_child("trash7").visible = true
				bin2.find_child("trash6").visible = true
				bin2.find_child("trash5").visible = true
				bin2.find_child("trash4").visible = true
				bin2.find_child("trash3").visible = true
				bin2.find_child("trash2").visible = true
				bin2.find_child("trash1").visible = true
			else:
					
				if fill_percentage>72 and not bin2.find_child("trash9").visible:
					bin2.find_child("trash9").visible = true
					bin2.find_child("trash8").visible = true
					bin2.find_child("trash7").visible = true
					bin2.find_child("trash6").visible = true
					bin2.find_child("trash5").visible = true
					bin2.find_child("trash4").visible = true
					bin2.find_child("trash3").visible = true
					bin2.find_child("trash2").visible = true
					bin2.find_child("trash1").visible = true
				elif fill_percentage>64 and not bin2.find_child("trash8").visible:
					bin2.find_child("trash8").visible = true
					bin2.find_child("trash7").visible = true
					bin2.find_child("trash6").visible = true
					bin2.find_child("trash5").visible = true
					bin2.find_child("trash4").visible = true
					bin2.find_child("trash3").visible = true
					bin2.find_child("trash2").visible = true
					bin2.find_child("trash1").visible = true
				elif fill_percentage>56 and not bin2.find_child("trash7").visible:
					bin2.find_child("trash7").visible = true
					bin2.find_child("trash6").visible = true
					bin2.find_child("trash5").visible = true
					bin2.find_child("trash4").visible = true
					bin2.find_child("trash3").visible = true
					bin2.find_child("trash2").visible = true
					bin2.find_child("trash1").visible = true
				elif fill_percentage>48 and not bin2.find_child("trash6").visible:
					bin2.find_child("trash6").visible = true
					bin2.find_child("trash5").visible = true
					bin2.find_child("trash4").visible = true
					bin2.find_child("trash3").visible = true
					bin2.find_child("trash2").visible = true
					bin2.find_child("trash1").visible = true
				elif fill_percentage>40 and not bin2.find_child("trash5").visible:
					bin2.find_child("trash5").visible = true
					bin2.find_child("trash4").visible = true
					bin2.find_child("trash3").visible = true
					bin2.find_child("trash2").visible = true
					bin2.find_child("trash1").visible = true
				elif fill_percentage>32 and not bin2.find_child("trash4").visible:
					bin2.find_child("trash4").visible = true
					bin2.find_child("trash3").visible = true
					bin2.find_child("trash2").visible = true
					bin2.find_child("trash1").visible = true
				elif fill_percentage>24 and not bin2.find_child("trash3").visible:
					bin2.find_child("trash3").visible = true
					bin2.find_child("trash2").visible = true
					bin2.find_child("trash1").visible = true
				elif fill_percentage>16 and not bin2.find_child("trash2").visible:
					bin2.find_child("trash2").visible = true
					bin2.find_child("trash1").visible = true
				elif fill_percentage>8 and not bin2.find_child("trash1").visible:
					bin2.find_child("trash1").visible = true
	else:
		print("Error parsing JSON, error code:", json_result)
	update_particles()

func truck1_actions(message):
	var status = int(message)
	if status == 0:
		print("stop truck 1")
		
	else: 
		print("move truck 1")
		
	if status != last_status_truck1 and is_connec:
		last_status_truck1 = status
		
func truck2_actions(message):
	var status = int(message)
	if status == 0:
		print("stop truck 2")
	else: 
		print("move truck 2")
		
	if status != last_status_truck2 and is_connec:
		last_status_truck2 = status


#final version
#func _physics_process(delta: float) -> void:
	#current_delta = delta  # Update delta each frame
	#
	## Move the truck1 if status is not 0
	#if last_status_truck1 == 2:
		#%PathFollow3D.progress += MOVE_SPEED * current_delta
		#
	## Move the truck2 if status is not 0
	#if last_status_truck2 == 2:
		#%PathFollow3D2.progress += MOVE_SPEED * current_delta

func _physics_process(delta: float) -> void:
	current_delta = delta  # Update delta each frame
	
	# Get the positions of both trucks
	var truck1_pos = %PathFollow3D.global_transform.origin
	var truck2_pos = %PathFollow3D2.global_transform.origin

	# Calculate the distance between the two trucks
	var distance = truck1_pos.distance_to(truck2_pos)

	# Define a minimum safe distance to prevent overlap
	var safe_distance = 15.0  # Adjust based on truck size

	# Move Truck1
	if last_status_truck1 == 2:
		%PathFollow3D.progress += MOVE_SPEED * current_delta
	else: 
		%PathFollow3D.progress += 0
	
	# Move Truck2, but slow down or stop if too close to Truck1
	if last_status_truck2 == 2:
		if distance > safe_distance:
			%PathFollow3D2.progress += MOVE_SPEED * current_delta
		else:
			#%PathFollow3D2.progress += (MOVE_SPEED * 0.5) * current_delta  # Slow down to avoid collision
			%PathFollow3D2.progress += 0  # Stop completely until safe distance is restored
	else:
		%PathFollow3D2.progress += 0 
		
func truck1_collect(message):
	var bin_to_collect = message
	
	if int(bin_to_collect) == 2:
		%log_truck1.text = "Truck1 emptying Bin2"
		
		for i in range(10,0,-1):
			var trash = bin2.find_child("trash" + str(i))
			if trash and trash.visible:
				print("OK! " + str(i))
				trash.visible = false 
				await get_tree().create_timer(0.5).timeout
	elif int(bin_to_collect) == 1:
		print("Truck 1 collects BIN 1")
		%log_truck1.text = "Truck1 collects Bin1"
		
		
		for i in range(10,0,-1):
			var trash = bin.find_child("trash" + str(i))
			if trash and trash.visible:
				print("OK! " + str(i))
				trash.visible = false 
				await get_tree().create_timer(0.5).timeout
				
	
	else: 
		print("unexpected value received in the collection queue")
	%log_truck1.text = "Collection done"
	await get_tree().create_timer(1).timeout
	%log_truck1.text = ""
func truck2_collect(message):
	var bin_to_collect = message
	
	if int(bin_to_collect) == 2:
		print("Truck 2 collects BIN 2")
		%log_truck2.text = "Truck2 emptying Bin2"

		
		for i in range(10,0,-1):
			var trash = bin2.find_child("trash" + str(i))
			if trash and trash.visible:
				print("OK! " + str(i))
				trash.visible = false 
				await get_tree().create_timer(0.5).timeout
	elif int(bin_to_collect) == 1:
		print("Truck 2 collects BIN 1")
		%log_truck2.text = "Truck2 emptying Bin1"

		
		for i in range(10,0,-1):
			var trash = bin.find_child("trash" + str(i))
			if trash and trash.visible:
				print("OK! " + str(i))
				trash.visible = false 
				await get_tree().create_timer(0.5).timeout
	else: 
		print("unexpected value received in the collection queue")	
	%log_truck2.text = "Collection done"
	await get_tree().create_timer(1).timeout
	%log_truck2.text = ""
	
	
	
	
	
	
	
	
	
	
	
	
	
	

# Works without PT
#func _physics_process(delta: float) -> void:
	#current_delta = delta  # Update delta each frame
	#
	## Get their global positions
	#var pos_a = %Truck2.global_transform.origin
	#var pos_b = %lights.global_transform.origin
#
	## Calculate the distance
	#var distance = pos_a.distance_to(pos_b)
	#
	#var new_status = 2  # Default moving
	#if int(distance) < 24 and stop:
		#new_status = 0  # Stop
	#
	#if new_status != last_status_truck1 and is_connec:
		#%MQTT.publish("DT/traffic/truck1", str(new_status))
		#last_status_truck1 = new_status
	#
	#if new_status == 2:
		#%PathFollow3D2.progress += MOVE_SPEED * current_delta


 #Work with both trucks independently from the PT
#func _physics_process(delta: float) -> void:
	#current_delta = delta  # Update delta each frame
	 #
	#%PathFollow3D.progress += MOVE_SPEED * current_delta
	#%PathFollow3D2.progress += MOVE_SPEED * current_delta
#
	#

# Declare these variables at the script level (or in a singleton if needed)
var bin1_disturbed = false
var bin2_disturbed = false

# Function to update the particle visibility based on both bins
func update_particles():
	var disturbed = bin1_disturbed or bin2_disturbed
	%GPUParticles3D.visible = disturbed
	%water.visible = disturbed
	%water2.visible = disturbed 
	update_sky(disturbed)
	update_audio(disturbed)
	
	if bin1_disturbed == true:
		%MQTT.publish("DT/bins/disturbed/", "Bin 1 is disturbed")
	elif bin2_disturbed == true:
		%MQTT.publish("DT/bins/disturbed/", "Bin 2 is disturbed")
	else:
		%MQTT.publish("DT/bins/disturbed/", "No disturbance")
		
func update_sky(is_disturbed: bool) -> void:
	# Adjust the node path as needed
	var world_env = get_node("WorldEnvironment")
	if world_env and world_env.environment:
		if is_disturbed:
			world_env.environment.sky = cloudy_sky
			print("Switched to cloudy sky")
		else:
			world_env.environment.sky = clear_sky
			print("Switched to clear sky")
	else:
		print("WorldEnvironment or its environment resource not found!")
		
func update_audio(is_raining: bool) -> void:
	if audio_player:
		if is_raining:
			if audio_player.stream != rain_sound:
				audio_player.stream = rain_sound
				audio_player.play()
				print("Switched to rain sound")
		else:
			if audio_player.stream != city_sound:
				audio_player.stream = city_sound
				audio_player.play()
				print("Switched to city sound")
	else:
		print("Audio player node not found!")
