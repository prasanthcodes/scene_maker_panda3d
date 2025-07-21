from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import Point3, VBase3
from panda3d.bullet import BulletWorld, BulletPlaneShape, BulletRigidBodyNode, BulletSphereShape, BulletHeightfieldShape, BulletDebugNode,ZUp
#from panda3d.bullet import BulletWorld, BulletRigidBodyNode, BulletSphereShape, BulletHeightfieldShape
from panda3d.bullet import BulletCharacterControllerNode, BulletCapsuleShape

from direct.gui.DirectGui import *
from panda3d.core import *
import panda3d

panda3d.core.load_prc_file_data("", "textures-power-2 none")
class JumpingBallGame(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        
        debugNode = BulletDebugNode('Debug')
        #debugNP = render.attachNewNode(debugNode)
        debugNP = NodePath(debugNode)  # Attach directly to root, not render
        debugNP.reparentTo(base.camera)
        #debugNP.show()
        #render.hide()
        
        # Set up the Bullet physics world
        self.world = BulletWorld()
        self.world.setGravity(Vec3(0, 0, 0))
        self.world.setDebugNode(debugNP.node())

        heightmap = PNMImage(Filename('heightfield.png'))
        width, height = heightmap.getXSize(), heightmap.getYSize()
        # Set up the terrain
        self.terrain = GeoMipTerrain("terrain")
        self.terrain.setHeightfield(heightmap)  # Replace with your heightmap
        self.terrain.setBlockSize(32)
        self.terrain.setNear(40)
        self.terrain.setFar(100)
        self.terrain.setFocalPoint(base.camera)
        self.terrain.getRoot().reparentTo(render)
        self.terrain.getRoot().setSz(50)  # Scale the terrain height
        self.terrain.generate()
        terrain_scale=self.terrain.getRoot().getScale()
        texture_1 = loader.loadTexture("grass.png")
        self.terrain.getRoot().setTexture(TextureStage.getDefault(), texture_1)

        # Set collision mask for the terrain
        #self.terrain.getRoot().setCollideMask(BitMask32.bit(1))
        #self.terrain.getRoot().setFromCollideMask(BitMask32.allOff())
        #self.terrain.getRoot().setIntoCollideMask(BitMask32.bit(1))

        #texture = loader.loadTexture("heightfield.png")  # Replace with your texture

        # Create physics for the terrain (BulletHeightfieldShape)
        shape = BulletHeightfieldShape(heightmap, 1.0, ZUp)
        shape.setUseDiamondSubdivision(True)  # Improve collision accuracy
        terrain_node = BulletRigidBodyNode('Terrain')
        terrain_node.addShape(shape)
        terrain_node.setMass(0)  # Static body
        terrain_physics_np = self.render.attachNewNode(terrain_node)
        terrain_physics_np.setPos(self.terrain.getRoot().getPos())  # Heightfield is centered at origin
        Sx=terrain_scale[0]/width
        Sy=terrain_scale[1]/height
        #terrain_physics_np.setScale(Sx,Sy, 1)
        self.world.attachRigidBody(terrain_node)
        

        # Create the ground
        shape = BulletPlaneShape(Vec3(0, 0, 1), 0)
        ground_node = BulletRigidBodyNode('Ground')
        ground_node.addShape(shape)
        ground_np = self.render.attachNewNode(ground_node)
        self.world.attachRigidBody(ground_node)
        
        # Load and set up the ground model
        self.ground = self.loader.loadModel("models/box")
        self.ground.setScale(100, 100, 0.1)
        self.ground.setPos(0, 0, -0.05)
        texture_2 = loader.loadTexture("grass.png")
        self.ground.setTexture(TextureStage.getDefault(), texture_2)
        self.ground.reparentTo(ground_np)

        """
        # Create the ball
        shape = BulletSphereShape(0.5)
        ball_node = BulletRigidBodyNode('Ball')
        ball_node.setMass(1.0)
        ball_node.setFriction(0.5)
        ball_node.addShape(shape)
        self.ball_np = self.render.attachNewNode(ball_node)
        self.ball_np.setPos(10, 10, 200)
        self.world.attachRigidBody(ball_node)
        """
        
        shape = BulletCapsuleShape(0.5, 1.0, ZUp)  # Radius 0.5, height 1.0
        self.PlayerController = BulletCharacterControllerNode(shape, 0.4)  # Step height 0.4
        # Set up character properties
        self.PlayerController.setMaxJumpHeight(7.0)
        self.PlayerController.setJumpSpeed(12.0)
        self.PlayerController.setMaxSlope(60.0)
        #self.PlayerController.setFallingFriction(0.9)
        self.ball_np = render.attachNewNode(self.PlayerController)
        self.ball_np.setPos(10, 10, 200)  # Initial position above terrain
        self.world.attach(self.PlayerController)


        # Load and set up the ball model
        self.ball = self.loader.loadModel("models/ball")
        self.ball.setScale(5.5)
        self.ball.reparentTo(self.ball_np)

        # Set up the camera
        self.camera.setPos(0, -20, 5)
        self.camera.lookAt(self.ball_np)


        # Input setup
        self.accept('w', self.setKey, ['forward', True])
        self.accept('w-up', self.setKey, ['forward', False])
        self.accept('s', self.setKey, ['backward', True])
        self.accept('s-up', self.setKey, ['backward', False])
        self.accept('a', self.setKey, ['left', True])
        self.accept('a-up', self.setKey, ['left', False])
        self.accept('d', self.setKey, ['right', True])
        self.accept('d-up', self.setKey, ['right', False])
        self.accept('space', self.jump)

        # Key map for movement
        self.keyMap = {
            'forward': False,
            'backward': False,
            'left': False,
            'right': False
        }
        
        # Movement settings
        self.speed = 15.0  # Movement speed in units per second


        # Add physics update task
        self.taskMgr.add(self.update, "update")

        # Add instructions
        self.instructions = OnscreenText(
            text="Press SPACE to jump",
            pos=(0, -0.95),
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
            scale=0.05
        )

    def setKey(self, key, value):
        self.keyMap[key] = value
        
    def jump(self):
        # Apply an upward impulse to make the ball jump
        #self.PlayerController.applyCentralImpulse(Vec3(0, 0, 5))
        #self.PlayerController.setLinearMovement(Vec3(0, 0, 35), True)
        #self.PlayerController.setMaxJumpHeight(1.0)
        #self.PlayerController.setJumpSpeed(50.0)
        if self.PlayerController.isOnGround():
            self.PlayerController.doJump()
        
    def move_forward(self):
        # Apply a forward impulse (along positive Y-axis)
        #self.PlayerController.applyCentralImpulse(Vec3(0, 3, 0))
        #self.PlayerController.setLinearMovement(Vec3(0, 33, 0), True)
        pass

    def move_backward(self):
        # Apply a backward impulse (along negative Y-axis)
        #self.PlayerController.applyCentralImpulse(Vec3(0, -3, 0))
        #self.PlayerController.setLinearMovement(Vec3(0, -33, 0), True)
        pass
        
    def update(self, task):
        # Calculate movement direction
        move_vec = Vec3(0, 0, 0)
        if self.keyMap['forward']:
            move_vec.y += 1
        if self.keyMap['backward']:
            move_vec.y -= 1
        if self.keyMap['left']:
            move_vec.x -= 1
        if self.keyMap['right']:
            move_vec.x += 1

        # Normalize and apply speed
        if move_vec.length() > 0:
            move_vec.normalize()
            move_vec *= self.speed
            self.PlayerController.setLinearMovement(move_vec, True)
        else:
            # Stop movement when no keys are pressed
            self.PlayerController.setLinearMovement(Vec3(0, 0, 0), True)
            
        dt = globalClock.getDt()
        self.world.doPhysics(dt)
        #print(self.world.getGravity())
        #print(self.camera.getPos())
        return Task.cont

# Run the game
game = JumpingBallGame()
game.run()

