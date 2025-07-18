from direct.showbase.ShowBase import ShowBase
from panda3d.core import Shader, Texture, TextureStage, TransparencyAttrib, AmbientLight, DirectionalLight, Vec4, Vec3
import simplepbr
from gltflib import GLTF
from panda3d.core import *

class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        # Initialize simplepbr
        simplepbr.init(use_330=True, enable_shadows=True)
        self.setupLights()
        
        envmap=self.loader.loadCubeMap('#_envmap.jpg')
        # Load environment map from disk
        #envmap = self.loader.loadTexture("DaySkyHDRI059A_8K-TONEMAPPED.jpg")
        #envmap.setWrapU(Texture.WM_clamp)
        #envmap.setWrapV(Texture.WM_clamp)
        #envmap.setFormat(Texture.F_rgba16)  # Ensure HDR compatibility

        # Load models
        self.model1 = self.loader.loadModel("GlassHurricaneCandleHolder.glb")
        self.model2 = self.loader.loadModel("GlassHurricaneCandleHolder.glb")
        self.model1.reparentTo(self.render)
        self.model2.reparentTo(self.render)
        self.model1.setPos(0, 10, 0)
        self.model2.setPos(2, 10, 0)
        self.model1.setTransparency(TransparencyAttrib.MAlpha)
        self.model2.setTransparency(TransparencyAttrib.MAlpha)

        # Load custom shader
        shader = Shader.load(Shader.SL_GLSL, vertex="custom_glass.vert", fragment="custom_glass.frag")

        # Get material properties
        ior1, transmission1 = get_material_properties("GlassHurricaneCandleHolder.glb")
        ior2, transmission2 = get_material_properties("GlassHurricaneCandleHolder.glb")

        # Get textures
        textures1 = get_textures(self.model1)
        textures2 = get_textures(self.model2)

        # Apply shader and inputs to model1
        for node in self.model1.find_all_matches("**/+GeomNode"):
            node.setShader(shader)
            for ts_name, texture in textures1.items():
                if "baseColor" in ts_name:
                    node.setShaderInput("p3d_Texture0", texture)
                elif "metallicRoughness" in ts_name:
                    node.setShaderInput("p3d_Texture1", texture)
                elif "normal" in ts_name:
                    node.setShaderInput("p3d_Texture2", texture)
                elif "transmission" in ts_name:
                    node.setShaderInput("p3d_Texture3", texture)
            node.setShaderInput("ior", ior1)
            node.setShaderInput("transmissionFactor", transmission1)
            node.setShaderInput("environmentMap", envmap)
            node.setShaderInput("envmapIntensity", 0.1)

        # Apply shader and inputs to model2
        for node in self.model2.find_all_matches("**/+GeomNode"):
            node.setShader(shader)
            for ts_name, texture in textures2.items():
                if "baseColor" in ts_name:
                    node.setShaderInput("p3d_Texture0", texture)
                elif "metallicRoughness" in ts_name:
                    node.setShaderInput("p3d_Texture1", texture)
                elif "normal" in ts_name:
                    node.setShaderInput("p3d_Texture2", texture)
                elif "transmission" in ts_name:
                    node.setShaderInput("p3d_Texture3", texture)
            node.setShaderInput("ior", ior2)
            node.setShaderInput("transmissionFactor", transmission2)
            node.setShaderInput("environmentMap", envmap)
            node.setShaderInput("envmapIntensity", 0.1)

        # Add lighting
        dlight = DirectionalLight('dlight')
        dlight.setColor(Vec4(1, 1, 1, 1))
        dlight.setDirection(Vec3(-1, -1, -1))
        dlnp = self.render.attach_new_node(dlight)
        self.render.set_light(dlnp)

        alight = AmbientLight('alight')
        alight.setColor(Vec4(0.2, 0.2, 0.2, 1))
        alnp = self.render.attach_new_node(alight)
        self.render.set_light(alnp)
        
    def setupLights(self):  # Sets up some default lighting
        # set ambient light 0.4 for night, directional light 5 for day
        ambientLight = AmbientLight("ambientLight")
        ambientLight.setColor((.1,.1,.1, 1))
        self.render.setLight(self.render.attachNewNode(ambientLight))
        directionalLight = DirectionalLight("directionalLight_1")
        #directionalLight.setDirection(LVector3(-5,-5,-5))
        DL_intensity=2
        directionalLight.setColor((DL_intensity,DL_intensity,DL_intensity, 1))
        directionalLight.setSpecularColor((.1, .1, .1, .1))
        directionalLight.setShadowCaster(True, 512, 512)
        #self.render.setShaderAuto()
        #self.environ2.setShaderAuto()
        self.dlight1=self.render.attachNewNode(directionalLight)
        #self.dlight1.setHpr(45, -45, 0)
        self.dlight1.setPos(10,10,10)

        self.dlight1.node().get_lens().set_film_size(50, 50)
        self.dlight1.node().get_lens().setNearFar(1, 50)
        self.dlight1.node().show_frustum()
        self.render.setLight(self.dlight1)


def get_textures(model):
    textures = {}
    for node in model.find_all_matches("**/+GeomNode"):
        geom_state = node.getState()
        texture_attrib = geom_state.getAttrib(TextureAttrib)
        if texture_attrib:
            for ts in texture_attrib.getTextureStages():
                texture = texture_attrib.getTexture(ts)
                textures[ts.getName()] = texture
    return textures

def get_material_properties(gltf_file):
    ior = 1.5  # Default for glass
    transmission_factor = 1.0  # Default
    gltf = GLTF.load(gltf_file)
    for material in gltf.model.materials:
        if material.extensions:
            if "KHR_materials_ior" in material.extensions:
                ior = material.extensions["KHR_materials_ior"].get("ior", 1.5)
            if "KHR_materials_transmission" in material.extensions:
                transmission_factor = material.extensions["KHR_materials_transmission"].get("transmissionFactor", 1.0)
    return ior, transmission_factor
    
    
app = MyApp()
app.run()