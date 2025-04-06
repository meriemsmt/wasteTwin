extends StaticBody3D

@export var main_camera: Camera3D
@export var subviewport_container_1: Control  # First SubViewportContainer
@export var subviewport_container_2: Control  # Second SubViewportContainer
@export var back_button: Button

func _ready():
	if subviewport_container_1:
		subviewport_container_1.visible = false
	if subviewport_container_2:
		subviewport_container_2.visible = false
	if back_button:
		back_button.visible = false
		back_button.pressed.connect(_on_back_button_pressed)  # Connect button signal
		
func _input_event(_camera, event, _position, _normal, _shape_idx):
	if event is InputEventMouseButton and event.pressed:
		print("Mesh clicked! Switching to subviewports...")

		if main_camera:
			main_camera.current = false

		if subviewport_container_1:
			subviewport_container_1.visible = true

		if subviewport_container_2:
			subviewport_container_2.visible = true

func _on_back_button_pressed():
	print("Back button clicked! Returning to main camera.")

	if main_camera:
		main_camera.current = true  # Reactivate main camera

	if subviewport_container_1:
		subviewport_container_1.visible = false
	if subviewport_container_2:
		subviewport_container_2.visible = false

	if back_button:
		back_button.visible = false  # Hide the button
