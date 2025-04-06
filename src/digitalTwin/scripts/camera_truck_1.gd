#extends Camera3D  
#
#@export var target: Node3D  # Assign the truck in the editor
#@onready var initial_offset := global_transform.origin - target.global_transform.origin
#
#func _process(delta):
	#if target:
		## Keep the camera at its initial offset relative to the truck
		#global_transform.origin = target.global_transform.origin + initial_offset

#extends Camera3D
#
#@export var target: Node3D  # Assign the truck in the editor
#@export var offset: Vector3 = Vector3(0, 3, -10)  # Camera should stay behind the truck
#@export var smooth_speed: float = 5.0  # Camera smoothing
#
#@onready var initial_offset := global_transform.origin - target.global_transform.origin
#
#func _process(delta):
	#if target:
		#var target_position = target.global_transform.origin
		#
		## 🚛 Get the truck's forward direction (along the X-axis)
		#var forward_direction = target.global_transform.basis.x.normalized()
		#
		## 🎥 Position the camera BEHIND the truck, adjusting offset
		#var desired_position = target_position - (forward_direction * abs(offset.z)) + Vector3(0, offset.y, 0)
		#
		## 🔄 Smoothly move the camera to the new position
		#global_transform.origin = global_transform.origin.lerp(desired_position, delta * smooth_speed)
		#
		## 👀 Make sure the camera is looking at the truck
		#look_at(target_position, Vector3.UP)

#extends Camera3D  # Use Camera2D if working in 2D
#
#@export var target: Node3D  # Assign the truck in the editor
#@export var offset: Vector3 = Vector3(0, 30, -50)  
#@export var smooth_speed: float = 5.0  # Smooth follow speed
#
#func _process(delta):
	#if target:
		#var target_position = target.global_transform.origin
		#
		## Get the direction the truck is facing
		#var back_direction = -target.global_transform.basis.z.normalized()  
		#
		## Compute desired camera position (behind and above truck)
		#var desired_position = target_position + (back_direction * abs(offset.z)) + Vector3(0, offset.y, 0)
		#
		## Smoothly move the camera to the desired position
		#global_transform.origin = global_transform.origin.lerp(desired_position, delta * smooth_speed)
		#
		## Make the camera look at the truck
		#look_at(target_position, Vector3.UP)









#extends Camera3D
#
#@export var target: Node3D
#@export var offset: Vector3 = Vector3(0, 30, -20)
#@export var smooth_speed: float = 5.0
#
#func _process(delta):
	#if target:
		#var target_position = target.global_transform.origin
		#var back_direction = -target.global_transform.basis.z.normalized()
		#var desired_position = target_position + (back_direction * abs(offset.z)) + Vector3(0, offset.y, 0)
		#
		#global_transform.origin = global_transform.origin.lerp(desired_position, delta * smooth_speed)
		#look_at(target_position, Vector3.UP)
		
		
extends Camera3D

@export var target: Node3D
@export var offset: Vector3 = Vector3(0, 10, -20)  
@export var smooth_speed: float = 5.0

func _process(delta):
	if target:
		var target_position = target.global_transform.origin
		
		# The correct direction to move the camera behind the truck
		var back_direction = target.global_transform.basis.z.normalized()  # Use positive Z


		# Place the camera behind and above the truck
		var desired_position = target_position + (back_direction * abs(offset.z)) + Vector3(0, offset.y, 0)
		
		# Smooth follow
		global_transform.origin = global_transform.origin.lerp(desired_position, delta * smooth_speed)
		
		# Ensure the camera looks at the truck
		look_at(target_position, Vector3.UP)
