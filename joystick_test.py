from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from panda3d.core import Vec3, InputDevice
import sys

class JoystickDemo(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        
        # Load a model (using the panda model as an example)
        self.model = Actor("models/panda-model")
        self.model.setScale(0.01)  # Scale down the model
        self.model.reparentTo(self.render)
        
        # Set up camera
        self.disableMouse()
        self.camera.setPos(0, -20, 5)
        self.camera.lookAt(self.model)
        
        # Initialize joystick variables
        self.joystick = None
        self.setupJoystick()
        
        # Movement variables
        self.moveSpeed = 10.0
        self.rotateSpeed = 100.0
        
        # Start the update task
        self.taskMgr.add(self.update, "update")
        
    def setupJoystick(self):
        """Set up joystick input"""
        devices = self.devices.getDevices(InputDevice.DeviceClass.gamepad)
        if devices:
            self.joystick = devices[0]
            self.attachInputDevice(self.joystick)
            print(f"Connected joystick: {self.joystick.name}")
            # Print total number of buttons and axes for debugging
            print(f"Total buttons available: {len(self.joystick.buttons)}")
            print(f"Total axes available: {len(self.joystick.axes)}")
        else:
            print("No joystick found!")
            
    def update(self, task):
        """Update loop to handle joystick input"""
        if self.joystick:
            # Get joystick axes (typically left stick for movement)
            x_axis = self.joystick.findAxis(InputDevice.Axis.left_x)
            y_axis = self.joystick.findAxis(InputDevice.Axis.left_y)
            r_axis = self.joystick.findAxis(InputDevice.Axis.right_x)
            
            # Get axis values (-1 to 1)
            x = x_axis.value
            y = -y_axis.value  # Invert Y for intuitive forward/backward
            rotation = -r_axis.value  # Invert for intuitive rotation
            
            # Apply deadzone to prevent drift
            deadzone = 0.2
            x = 0 if abs(x) < deadzone else x
            y = 0 if abs(y) < deadzone else y
            rotation = 0 if abs(rotation) < deadzone else rotation
            
            # Calculate movement
            dt = globalClock.getDt()
            move_vec = Vec3(x, y, 0) * self.moveSpeed * dt
            self.model.setPos(self.model.getPos() + move_vec)
            
            # Apply rotation
            self.model.setH(self.model.getH() + rotation * self.rotateSpeed * dt)
            
            # Check for face button presses (Xbox 360: A=0, B=1, X=2, Y=3)
            if self.joystick.buttons[0].pressed:
                print("Button A pressed!")
            if self.joystick.buttons[1].pressed:
                print("Button B pressed!")
            if self.joystick.buttons[2].pressed:
                print("Button X pressed!")
            if self.joystick.buttons[3].pressed:
                print("Button Y pressed!")
            
            # Check for D-pad as buttons (try indices 4-7 as a starting point)
            try:
                if self.joystick.buttons[4].pressed:
                    print("D-pad Up pressed! (Button 4)")
                if self.joystick.buttons[5].pressed:
                    print("D-pad Down pressed! (Button 5)")
                if self.joystick.buttons[6].pressed:
                    print("D-pad Left pressed! (Button 6)")
                if self.joystick.buttons[7].pressed:
                    print("D-pad Right pressed! (Button 7)")
            except IndexError:
                print("Error: D-pad button indices out of range.")
            
            # Debug all button and axis states to find D-pad mappings
            for i, button in enumerate(self.joystick.buttons):
                if button.pressed:
                    print(f"Button {i} pressed!")
            for i, axis in enumerate(self.joystick.axes):
                if abs(axis.value) > deadzone:
                    print(f"Axis {i}: {axis.value}")
                
        return Task.cont

# Run the demo
app = JoystickDemo()
app.run()


"""
axis0:1                                                    axis1:1
  8                                                            9
                             5
  0           axis3:1        4         axis5:1                 14
2   3    axis2:-1  axis2:1   10    axis4:-1  axis4:1         13  12
  1           axis3:-1                 axis5:-1                11
  
"""