from direct.showbase.ShowBase import ShowBase
from panda3d.core import ShaderTerrainMesh, Shader
from panda3d.core import SamplerState

from panda3d.bullet import BulletHeightfieldShape, BulletDebugNode, BulletWorld, ZUp, BulletTriangleMesh, BulletRigidBodyNode

from panda3d.core import Filename, PNMImage


class ShaderTerrainDemo(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        debugNode = BulletDebugNode('Debug')
        debugNP = render.attachNewNode(debugNode)
        debugNP.show()

        self.world = BulletWorld()
        self.world.setDebugNode(debugNP.node())

        shape = BulletHeightfieldShape(PNMImage(Filename('heightfield1.png')), 10, ZUp)

        node = BulletRigidBodyNode('Ground')
        node.addShape(shape)
        
        np = render.attachNewNode(node)
        self.world.attachRigidBody(node)

        self.camLens.set_fov(90)
        self.camLens.set_near_far(0.1, 50000)

        self.terrain_node = ShaderTerrainMesh()

        heightfield = self.loader.loadTexture("heightfield.png")
        heightfield.wrap_u = SamplerState.WM_clamp
        heightfield.wrap_v = SamplerState.WM_clamp
        self.terrain_node.heightfield = heightfield

        self.terrain_node.target_triangle_width = 10.0

        self.terrain_node.generate()

        self.terrain = self.render.attach_new_node(self.terrain_node)
        self.terrain.set_scale(128, 128, 10)
        self.terrain.set_pos(-64, -64, -5)

        terrain_shader = Shader.load(Shader.SL_GLSL, "terrain.vert.glsl", "terrain.frag.glsl")
        self.terrain.set_shader(terrain_shader)
        self.terrain.set_shader_input("camera", self.camera)

        self.accept("f3", self.toggleWireframe)

        grass_tex = self.loader.loadTexture("textures/grass.png")
        grass_tex.set_minfilter(SamplerState.FT_linear_mipmap_linear)
        grass_tex.set_anisotropic_degree(16)
        self.terrain.set_texture(grass_tex)

        taskMgr.add(self.update, 'update')
        
    def update(self, task):
       self.world.doPhysics(globalClock.getDt())
       return task.cont  

ShaderTerrainDemo().run()
