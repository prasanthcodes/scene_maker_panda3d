from direct.showbase.ShowBase import ShowBase
from panda3d.core import GraphicsOutput, Texture, FrameBufferProperties, WindowProperties
from panda3d.core import *
from math import sin, cos, pi

import simplepbr

class MyGame(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        
        #env_map = simplepbr.EnvPool.ptr().load('cubemap_face_#.hdr')
        env_map = simplepbr.EnvPool.ptr().load('#_envmap.jpg')
        #env_map=None;
        self.pipeline = simplepbr.init(
        env_map=env_map,
        #applyToneMapping=False,
        use_normal_maps=True,
        exposure=0,
        #sdr_lut_factor=0,
        max_lights=16,
        enable_fog=True
        )
        
        self.scene = self.loader.loadModel("DamagedHelmet.glb")  # Simple model for testing
        self.scene.reparentTo(self.render)
        self.scene.setPos(0, 0, 0)
        
        # Create a skybox node
        self.skybox = self.render.attachNewNode("skybox")
        self.skybox.setScale(2000)  # Scale to surround scene

        # Create a sphere programmatically
        sphere = self.create_sphere(radius=1.0, segments=32)
        sphere.reparentTo(self.skybox)

        """
        if os.path.exists(self.global_params['skybox_image']):
            # Load the equirectangular texture
            tex = self.loader.loadTexture(self.global_params['skybox_image'])
            
            self.skybox.setTexture(tex)
            # reverse normals
            #self.skybox.node().setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullCounterClockwise))
            # Flip texture horizontally
            self.skybox.setTexScale(TextureStage.getDefault(), -1, 1)  # Negative x-scale for horizontal flip
            self.skybox.setTexOffset(TextureStage.getDefault(), 1, 0)  # Adjust offset to align (U=1 to shift origin)
        """

        # Configure skybox rendering
        self.skybox.setTwoSided(True)  # Render both sides to see inside
        self.skybox.setBin("background", 0)  # Render first
        self.skybox.setDepthWrite(False)  # Disable depth writing
        self.skybox.setDepthTest(False)  # Disable depth testing
        #self.ambientLight_skybox = AmbientLight("ambientLight")
        #self.ambientLight_skybox.setColor((self.global_params['skybox_ambientlight_R'],self.global_params['skybox_ambientlight_G'],self.global_params['skybox_ambientlight_B'], 1))
        self.skybox.setLightOff()  # Ignore lighting
        #self.skybox.setLight(self.render.attachNewNode(self.ambientLight_skybox))
        #self.skybox.setShaderOff()
        #self.skybox.setShaderAuto()
        
    def create_sphere(self, radius=1.0, segments=32):
        # Create vertex format
        vformat = GeomVertexFormat.getV3n3t2()
        vdata = GeomVertexData('sphere', vformat, Geom.UHStatic)
        
        # Vertex writers
        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        texcoord = GeomVertexWriter(vdata, 'texcoord')
        
        # Generate sphere vertices
        for i in range(segments + 1):
            phi = pi * i / segments
            sin_phi = sin(phi)
            cos_phi = cos(phi)
            
            for j in range(segments + 1):
                theta = 2 * pi * j / segments
                sin_theta = sin(theta)
                cos_theta = cos(theta)
                
                # Calculate vertex position
                x = radius * sin_phi * cos_theta
                y = radius * sin_phi * sin_theta
                z = radius * cos_phi
                
                # Add vertex data
                vertex.addData3(x, y, z)
                normal.addData3(x/radius, y/radius, z/radius)  # Normalized
                texcoord.addData2(j/segments, 1.0-i/segments)
        
        # Create triangles
        prim = GeomTriangles(Geom.UHStatic)
        for i in range(segments):
            for j in range(segments):
                v0 = i * (segments + 1) + j
                v1 = v0 + 1
                v2 = (i + 1) * (segments + 1) + j
                v3 = v2 + 1
                
                # First triangle
                prim.addVertices(v0, v1, v2)
                # Second triangle
                prim.addVertices(v1, v3, v2)
        
        # Create geometry
        geom = Geom(vdata)
        geom.addPrimitive(prim)
        
        # Create and return GeomNode
        node = GeomNode('sphere')
        node.addGeom(geom)
        return NodePath(node)


app = MyGame()
app.run()