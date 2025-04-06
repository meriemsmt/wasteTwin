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
