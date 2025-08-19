from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import Point3, VBase3
from panda3d.bullet import BulletWorld, BulletPlaneShape, BulletRigidBodyNode, BulletSphereShape, BulletHeightfieldShape, BulletDebugNode,ZUp
#from panda3d.bullet import BulletWorld, BulletRigidBodyNode, BulletSphereShape, BulletHeightfieldShape
from panda3d.bullet import BulletCharacterControllerNode, BulletCapsuleShape
from panda3d.bullet import BulletTriangleMesh, BulletTriangleMeshShape, BulletBoxShape, BulletSphereShape

from direct.gui.DirectGui import *
from panda3d.core import *
import panda3d

panda3d.core.load_prc_file_data("", "textures-power-2 none")
class JumpingBallGame(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        #self.disable_mouse()
        # Set up orthographic camera
        lens = OrthographicLens()
        lens.setFilmSize(100, 75)  # Adjust to terrain size
        lens.setNearFar(-2000, 2000)
        #self.camera.node().setLens(lens)
        #base.cam.node().setLens(lens)
        
        debugNode = BulletDebugNode('Debug')
        #debugNP = render.attachNewNode(debugNode)
        debugNP = NodePath(debugNode)  # Attach directly to root, not render
        debugNP.reparentTo(base.camera)
        debugNP.show()
        #render.hide()
        
        # Set up the Bullet physics world
        self.world = BulletWorld()
        self.world.setGravity(Vec3(0, 0, 0))
        self.world.setDebugNode(debugNP.node())

        heightmap_imagename='heightfield.png'
        heightmap = PNMImage(Filename(heightmap_imagename))
        width, height = heightmap.getXSize(), heightmap.getYSize()
        # Set up the terrain
        self.terrain = GeoMipTerrain("terrain")
        self.terrain.setHeightfield(heightmap_imagename)  # Replace with your heightmap
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
        #shape = BulletHeightfieldShape(heightmap, 1.0, ZUp)
        #shape.setUseDiamondSubdivision(True)  # Improve collision accuracy
        terrain_node = BulletRigidBodyNode('Terrain')
        #terrain_node.addShape(shape)
        terrain_node.setMass(0)  # Static body
        terrain_physics_np = self.render.attachNewNode(terrain_node)
        Pos_HF=self.terrain.getRoot().getPos()
        Scalex=terrain_scale[0]*width
        Scaley=terrain_scale[1]*height
        Scalez=terrain_scale[2]
        terrain_physics_np.setPos(Pos_HF[0]+Scalex/2.0,Pos_HF[1]+Scaley/2.0,Pos_HF[2]+Scalez/2.0)  # Heightfield is centered at origin
        #terrain_physics_np.setSz(50)
        Sx=terrain_scale[0]#/width
        Sy=terrain_scale[1]#/height

        #print('Sx: ',Sx,'Sy: ',Sy)
        terrain_physics_np.setScale(Sx,Sy, 50)
        #print(terrain_physics_np.getScale())
        self.world.attachRigidBody(terrain_node)
        
        #print(self.terrain.getRoot().getPos())
        #print(terrain_physics_np.getPos())
        

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
        
        
        
        #Transport_Shuttle
        self.ob_1 = self.loader.loadModel("Transport_Shuttle/Transport_Shuttle.gltf")
        #shape=self.create_bullet_shape_2(self.ob_1,shape_type='box', complexity='high')
        shape=self.create_bullet_mesh_shape_from_model(self.ob_1)
        ob1_node = BulletRigidBodyNode('Transport_Shuttle')
        ob1_node.addShape(shape)
        ob1_np = self.render.attachNewNode(ob1_node)
        self.world.attachRigidBody(ob1_node)
        self.ob_1.reparentTo(ob1_np)
        ob1_np.setPos(0,0,10)
        
        #sci_fi_blocks_3builds
        self.ob_2 = self.loader.loadModel("sci_fi_blocks_3builds/sci_fi_blocks_3builds.gltf")
        self.ob_2.ls()
        #shape=self.create_bullet_shape_2(self.ob_2,shape_type='triangle', complexity='high')
        shape=self.create_bullet_mesh_shape_from_model(self.ob_2)
        ob2_node = BulletRigidBodyNode('sci_fi_blocks_3builds')
        ob2_node.addShape(shape)
        ob2_np = self.render.attachNewNode(ob2_node)
        self.world.attachRigidBody(ob2_node)
        self.ob_2.reparentTo(ob2_np)
        ob2_np.setPos(-20,0,0)

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
        #self.PlayerController.setFriction(0.9)
        self.ball_np = render.attachNewNode(self.PlayerController)
        self.ball_np.setPos(10, 10, 200)  # Initial position above terrain
        self.world.attach(self.PlayerController)


        # Load and set up the ball model
        self.ball = self.loader.loadModel("models/ball")
        self.ball.setScale(1)
        self.ball.reparentTo(self.ball_np)

        # Set up the camera
        #self.camera.setPos(0, -20, 5)
        #self.camera.lookAt(self.ball_np)
        self.camera.setPos(-1000, -1000, 100)
        self.camera.lookAt(self.ground)


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
            
    def create_bullet_shape_2(self, model, shape_type='triangle', complexity='high'):

        if not isinstance(model, NodePath):
            print(f"Warning: {model} is not a valid NodePath")
            return None

        geom_matches = model.find_all_matches("**/+GeomNode")
        if geom_matches.isEmpty():
            print(f"Warning: No GeomNode found in {model}")
            return None
        #geom_node = geom_np.node()

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
                for model_now in geom_matches:
                    geom_node = model_now.node()
                    if isinstance(geom_node, GeomNode):
                        for geom in geom_node.getGeoms():
                            mesh.addGeom(geom)
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

    def create_collision_mesh(self,model,meshname):
        # create a temporary copy to generate the collision meshes from
        
        self.model_copy = model.copy_to(base.render)
        self.model_copy.detach_node()
        # "bake" the transformations into the vertices
        self.model_copy.flatten_light()

        # create root node to attach collision nodes to
        collision_root = NodePath(meshname)#"collision_root"
        collision_root.reparent_to(model)
        # offset the collision meshes from the model so they're easier to see
        #collision_root.set_x(3)

        # Please note that the code below will not copy the hierarchy structure of the
        # loaded `model_root` and that the resulting collision meshes will all have
        # their origins at (0., 0., 0.), an orientation of (0., 0., 0.) and a scale of 1
        # (as a result of the call to `flatten_light`).
        # If a different relationship between loaded models and their corresponding
        # collision meshes is required, feel free to alter the code as needed, but keep
        # in mind that any (especially non-uniform) scale affecting a collision mesh
        # (whether set on the mesh itself or inherited from a node at a higher level)
        # can cause problems for the built-in collision system.

        #"""
        # create a collision mesh for each of the loaded models
        for model in self.model_copy.find_all_matches("**/+GeomNode"):

            model_node = model.node()
            collision_node = CollisionNode(model_node.name)
            collision_mesh = collision_root.attach_new_node(collision_node)
            # collision nodes are hidden by default
            #collision_mesh.show()

            for geom in model_node.modify_geoms():

                geom.decompose_in_place()
                vertex_data = geom.modify_vertex_data()
                vertex_data.format = GeomVertexFormat.get_v3()
                view = memoryview(vertex_data.arrays[0]).cast("B").cast("f")
                index_list = geom.primitives[0].get_vertex_list()
                index_count = len(index_list)

                for indices in (index_list[i:i+3] for i in range(0, index_count, 3)):
                    points = [Point3(*view[index*3:index*3+3]) for index in indices]
                    coll_poly = CollisionPolygon(*points)
                    collision_node.add_solid(coll_poly)


    def create_bullet_mesh_shape_from_model(self,model):
        # Create the triangle mesh
        mesh = BulletTriangleMesh()
        
        def add_geoms(np: NodePath, ts: TransformState = TransformState.make_identity()):
            """
            Recursively traverses the node path, adding geoms to the mesh with accumulated transforms.
            """
            node = np.node()
            if isinstance(node, GeomNode):
                for geom in node.get_geoms():
                    mesh.add_geom(geom, ts)
            
            # Recurse to children with composed transforms
            for child in np.get_children():
                #child_ts = ts.compose(child.get_transform())
                #print(child_ts)
                add_geoms(child, child.get_transform())
        
        # Start recursion from the model root
        add_geoms(model)
        
        # Create the shape from the mesh (set dynamic=True if for dynamic bodies, False for static)
        shape = BulletTriangleMeshShape(mesh, dynamic=False)
        
        return shape


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
            #self.PlayerController.setLinearVelocity(Vec3(0, 0, self.PlayerController.getLinearVelocity().z))
            
        dt = globalClock.getDt()
        self.world.doPhysics(dt)
        #print(self.world.getGravity())
        #print(self.camera.getPos())
        return Task.cont

# Run the game
game = JumpingBallGame()
game.run()

