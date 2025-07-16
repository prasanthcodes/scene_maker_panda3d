from panda3d.core import Vec3, PNMImage, NodePath
from panda3d.bullet import BulletWorld, BulletCharacterControllerNode, BulletCapsuleShape, BulletHeightfieldShape, ZUp, BulletRigidBodyNode
from direct.showbase.ShowBase import ShowBase
from direct.showbase.InputStateGlobal import inputState

class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Setup physics world
        self.world = BulletWorld()
        self.world.setGravity(Vec3(0, 0, -9.81))

        # Setup terrain
        self.setup_terrain()

        # Setup character
        self.setup_character()

        # Setup camera
        self.setup_camera()

        # Setup input
        self.setup_input()

        # Start update task
        self.taskMgr.add(self.update, 'update')

    def setup_terrain(self):
        # Create a simple heightfield (flat for simplicity, or use a grayscale image)
        img = PNMImage(128, 128)
        img.fill(0.5)  # Flat terrain (height = 0.5 * max_height)
        shape = BulletHeightfieldShape(img, 10.0, ZUp)  # Max height 10 units
        shape.setUseDiamondSubdivision(True)  # Improve collision accuracy
        terrain_node = BulletRigidBodyNode('Terrain')
        terrain_node.addShape(shape)
        terrain_np = self.render.attachNewNode(terrain_node)
        terrain_np.setPos(0, 0, 0)
        self.world.attachRigidBody(terrain_node)

        # Optional: Add a visual terrain (e.g., a flat plane)
        plane = self.loader.loadModel('models/box')
        plane.setScale(18, 18, 1)
        plane.setPos(0, 0, 0)
        plane.reparentTo(self.render)

    def setup_character(self):
        # Create character controller with capsule shape
        shape = BulletCapsuleShape(0.5, 1.0, ZUp)  # Radius 0.5, height 1.0
        self.controller = BulletCharacterControllerNode(shape, 0.4)  # Step height 0.4
        self.char_np = self.render.attachNewNode(self.controller)
        self.char_np.setPos(0, 0, 5)  # Start above terrain
        self.world.attachCharacter(self.controller)

        # Set jump speed
        self.controller.setJumpSpeed(5.0)  # Adjust jump strength
        self.controller.setMaxSlope(45.0)  # Max slope to climb (degrees)

        # Optional: Add a visual model for the character
        model = self.loader.loadModel('models/ball')
        model.setScale(0.5)
        model.reparentTo(self.char_np)

    def setup_camera(self):
        # Third-person camera
        #self.disableMouse()  # Disable default camera control
        self.camera.setPos(0, -10, 3)  # Position behind character
        self.camera.lookAt(self.char_np)

    def setup_input(self):
        # Setup keyboard input using InputState
        self.accept('w', self.set_key, ['forward', True])
        self.accept('w-up', self.set_key, ['forward', False])
        self.accept('s', self.set_key, ['backward', True])
        self.accept('s-up', self.set_key, ['backward', False])
        self.accept('a', self.set_key, ['left', True])
        self.accept('a-up', self.set_key, ['left', False])
        self.accept('d', self.set_key, ['right', True])
        self.accept('d-up', self.set_key, ['right', False])
        self.accept('space', self.jump)

        # Input state dictionary
        self.keys = {
            'forward': False,
            'backward': False,
            'left': False,
            'right': False
        }

    def set_key(self, key, value):
        self.keys[key] = value

    def jump(self):
        if self.controller.isOnGround():
            self.controller.doJump()  # Trigger jump if on ground

    def update(self, task):
        dt = globalClock.getDt()

        # Calculate movement vector based on input
        velocity = Vec3(0, 0, 0)
        speed = 5.0  # Movement speed

        if self.keys['forward']:
            velocity += Vec3(0, speed, 0)
        if self.keys['backward']:
            velocity += Vec3(0, -speed, 0)
        if self.keys['left']:
            velocity += Vec3(-speed, 0, 0)
        if self.keys['right']:
            velocity += Vec3(speed, 0, 0)

        # Normalize velocity to prevent faster diagonal movement
        if velocity.length() > 0:
            velocity=velocity.normalized() * speed

        # Apply movement
        self.controller.setLinearMovement(velocity, True)  # True for local coordinates

        # Update camera to follow character
        cam_pos = self.char_np.getPos() + Vec3(0, -10, 3)
        self.camera.setPos(cam_pos)
        self.camera.lookAt(self.char_np)

        # Update physics
        self.world.doPhysics(dt)
        return task.cont

game = Game()
game.run()