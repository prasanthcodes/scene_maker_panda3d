from panda3d.core import Vec3, PNMImage, NodePath, GeomNode, Camera, NodePath, BoundingSphere
from panda3d.bullet import BulletWorld, BulletCharacterControllerNode, BulletCapsuleShape, BulletPlaneShape, ZUp, BulletRigidBodyNode, BulletDebugNode
from panda3d.bullet import BulletTriangleMesh, BulletTriangleMeshShape, BulletBoxShape, BulletSphereShape

from direct.showbase.ShowBase import ShowBase
from direct.showbase.InputStateGlobal import inputState
import math

class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.world = BulletWorld()
        self.world.setGravity(Vec3(0, 0, -9.81))
        
        # Setup debug render and camera
        self.debug_render = NodePath('DebugRender')  # New root for debug scene
        self.debug_node = BulletDebugNode('Debug')
        self.debug_np = self.debug_render.attachNewNode(self.debug_node)
        self.world.setDebugNode(self.debug_node)
        self.debug_enabled = False
        self.debug_np.hide()
        
        # Create debug camera
        #self.debug_camera = self.makeCamera(self.win, displayRegion=self.win.getDisplayRegion(0))
        self.debug_camera = NodePath(Camera('DebugCamera'))
        self.debug_camera.node().setName('DebugCamera')
        self.debug_camera.reparentTo(self.debug_render)
        self.debug_camera.setPos(0, -10, 3)  # Match main camera's initial position
        self.debug_camera.node().setActive(False)  # Initially inactive
        self.win.getDisplayRegion(0).setCamera(self.debug_camera)  # Share default display region
        
        self.prev_velocity = Vec3(0, 0, 0)
        self.spawn_point = Vec3(0, 0, 5)
        self.visual_models = []
        self.setup_terrain()
        self.setup_character()
        self.setup_camera()
        self.setup_input()
        self.taskMgr.add(self.update, 'update')


    def create_bullet_shape(self, model, shape_type='triangle', complexity='high'):
        """
        Create a Bullet collision shape from a model with adjustable complexity.
        
        Args:
            model (NodePath): The model to create a collision shape for.
            shape_type (str): Type of shape ('triangle', 'box', or 'sphere').
            complexity (str): Complexity level ('high' or 'low'). For 'triangle', 'low' uses a box shape.
        
        Returns:
            BulletShape: The created collision shape, or None if failed.
        """
        if not isinstance(model, NodePath):
            print(f"Warning: {model} is not a valid NodePath")
            return None

        geom_np = model.find('**/+GeomNode')
        if geom_np.isEmpty():
            print(f"Warning: No GeomNode found in {model}")
            return None
        geom_node = geom_np.node()

        if shape_type == 'triangle':
            if complexity == 'low':
                bounds = model.getTightBounds()
                if not bounds:
                    print(f"Warning: Could not compute bounds for {model}")
                    return None
                min_point, max_point = bounds
                size = (max_point - min_point) / 2.0
                return BulletBoxShape(size)
            else:
                mesh = BulletTriangleMesh()
                if isinstance(geom_node, GeomNode):
                    for geom in geom_node.getGeoms():
                        mesh.addGeom(geom)
                    if mesh.getNumTriangles() == 0:
                        print(f"Warning: No triangles found in {model}")
                        return None
                    return BulletTriangleMeshShape(mesh, dynamic=False)
        
        elif shape_type == 'box':
            bounds = model.getTightBounds()
            if not bounds:
                print(f"Warning: Could not compute bounds for {model}")
                return None
            min_point, max_point = bounds
            size = (max_point - min_point) / 2.0
            return BulletBoxShape(size)
        
        elif shape_type == 'sphere':
            sphere = model.getBounds()
            if not sphere.isEmpty() and sphere.isOfType(BoundingSphere.getClassType()):
                radius = sphere.getRadius()
                return BulletSphereShape(radius)
            else:
                print(f"Warning: Could not compute bounding sphere for {model}")
                return None
        
        else:
            print(f"Error: Unsupported shape_type '{shape_type}'")
            return None

    def setup_terrain(self):
        terrain_model = self.loader.loadModel('models/box')
        shape = self.create_bullet_shape(terrain_model, shape_type='box', complexity='high')
        if not shape:
            shape = BulletPlaneShape(Vec3(10, 10, 1), 0)
            print('yo')
        terrain_node = BulletRigidBodyNode('Terrain')
        terrain_node.addShape(shape)
        terrain_np = self.render.attachNewNode(terrain_node)
        terrain_np.setPos(0, 0, 0)
        self.world.attachRigidBody(terrain_node)
        terrain_model.setScale(18, 18, 1)
        terrain_model.setPos(0, 0, 0)
        terrain_model.reparentTo(self.render)
        self.visual_models.append(terrain_model)

    def setup_character(self):
        shape = BulletCapsuleShape(0.5, 1.0, ZUp)
        self.controller = BulletCharacterControllerNode(shape, 0.4)
        self.char_np = self.render.attachNewNode(self.controller)
        self.char_np.setPos(self.spawn_point)
        self.world.attachCharacter(self.controller)
        self.controller.setJumpSpeed(5.0)
        self.controller.setMaxSlope(45.0)
        #self.controller.setFriction(0.0)
        model = self.loader.loadModel('models/ball')
        #char_shape = self.create_bullet_shape(model, shape_type='sphere', complexity='high')
        #if char_shape:
        #    self.controller.addShape(char_shape)
        model.setScale(0.5)
        model.reparentTo(self.char_np)
        self.visual_models.append(model)

    def setup_camera(self):
        self.disableMouse()
        self.camera.setPos(0, -10, 3)
        self.camera.lookAt(self.char_np)

    def setup_input(self):
        self.accept('w', self.set_key, ['forward', True])
        self.accept('w-up', self.set_key, ['forward', False])
        self.accept('s', self.set_key, ['backward', True])
        self.accept('s-up', self.set_key, ['backward', False])
        self.accept('a', self.set_key, ['left', True])
        self.accept('a-up', self.set_key, ['left', False])
        self.accept('d', self.set_key, ['right', True])
        self.accept('d-up', self.set_key, ['right', False])
        self.accept('space', self.jump)
        self.accept('v', self.toggle_debug)
        self.keys = {
            'forward': False,
            'backward': False,
            'left': False,
            'right': False
        }

    def set_key(self, key, value):
        self.keys[key] = value
        if key == 'forward' and not value:
            self.controller.setLinearMovement(Vec3(0, 0, 0), True)

    def jump(self):
        if self.controller.isOnGround():
            self.controller.doJump()

    def toggle_debug(self):
        """Toggle between normal view and debug view (collision shapes only)."""
        self.debug_enabled = not self.debug_enabled
        if self.debug_enabled:
            self.debug_np.show()
            self.render.hide()  # Hide main render (visual models)
            self.camNode.setActive(False)  # Disable main camera
            self.debug_camera.node().setActive(True)  # Enable debug camera
            print("Showing only Bullet collision shapes")
        else:
            self.debug_np.hide()
            self.render.show()  # Show main render
            self.camNode.setActive(True)  # Enable main camera
            self.debug_camera.node().setActive(False)  # Disable debug camera
            print("Showing visual models, hiding collision shapes")

    def update(self, task):
        dt = globalClock.getDt()
        velocity = Vec3(0, 0, 0)
        speed = 5.0

        if self.keys['forward']:
            velocity += Vec3(0, speed, 0)
        if self.keys['backward']:
            velocity += Vec3(0, -speed, 0)
        if self.keys['left']:
            velocity += Vec3(-speed, 0, 0)
        if self.keys['right']:
            velocity += Vec3(speed, 0, 0)

        if velocity.length() > 0:
            velocity = velocity.normalized() * speed
        else:
            velocity = Vec3(0, 0, 0)

        #smoothing_factor = 1.0 - math.exp(-dt * 10.0)
        #velocity = self.prev_velocity.lerp(velocity, smoothing_factor)
        self.prev_velocity = velocity
        self.controller.setLinearMovement(velocity, True)

        if self.char_np.getZ() < -10:
            self.char_np.setPos(self.spawn_point)
            #self.controller.setLinearVelocity(Vec3(0, 0, 0))
            self.controller.setAngularMovement(0)

        # Update both cameras to follow character
        target_pos = self.char_np.getPos() + Vec3(0, -10, 3)
        current_pos = self.camera.getPos()
        #self.camera.setPos(current_pos.lerp(target_pos, smoothing_factor))
        self.camera.lookAt(self.char_np)
        #self.debug_camera.setPos(current_pos.lerp(target_pos, smoothing_factor))
        self.debug_camera.lookAt(self.char_np)

        fixed_dt = 1.0 / 60.0
        self.world.doPhysics(fixed_dt, 1, fixed_dt)
        return task.cont

game = Game()
game.run()