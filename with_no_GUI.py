import panda3d
from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor
from direct.task.Task import Task
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from direct.showbase.DirectObject import DirectObject
from direct.gui.DirectGui import *
from direct.gui import DirectGuiGlobals as DGG
from direct.filter.FilterManager import FilterManager

import random
import sys
import os
import shutil
import math
from direct.filter.CommonFilters import CommonFilters

from panda3d.core import *
import panda3d.core as p3d

import simplepbr
import gltf

import json
import datetime
import time
from math import sin, cos, pi

import logging

# logging to text file and cmd output
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(formatter)

file_handler = logging.FileHandler('logs.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stdout_handler)

# To handle all uncaught exceptions
def error_handler(exc_type, exc_value, exc_traceback):
    logger.error("Unhandled error: ",exc_info=(exc_type, exc_value, exc_traceback))

# Install exception handler
sys.excepthook = error_handler

logger.info('program started')


panda3d.core.load_prc_file_data("", """
    textures-power-2 none
    gl-coordinate-system default
    filled-wireframe-apply-shader true
    #cursor-hidden true
    
    # As an optimization, set this to the maximum number of cameras
    # or lights that will be rendering the terrain at any given time.
    stm-max-views 16

    # Further optimize the performance by reducing this to the max
    # number of chunks that will be visible at any given time.
    stm-max-chunk-count 2048
    #textures-power-2 up
    view-frustum-cull false
""")

#panda3d.core.load_prc_file_data('', 'framebuffer-srgb true')
#panda3d.core.load_prc_file_data('', 'load-display pandadx9')#pandagl,p3tinydisplay,pandadx9,pandadx8
panda3d.core.load_prc_file_data('', 'show-frame-rate-meter true')
#panda3d.core.load_prc_file_data('', 'fullscreen true')
#loadPrcFileData('', 'coordinate-system y-up-left')
loadPrcFileData("", "basic-shaders-only #t")
#loadPrcFileData("", "notify-level-glgsg debug")
loadPrcFileData("", "framebuffer-multisample 0")
loadPrcFileData("", "multisamples 0")
#loadPrcFileData("", "win-size 1920 1080")
#loadPrcFileData("", "fullscreen t")
#loadPrcFileData("", "show-scene-graph-analyzer-meter 1")
loadPrcFileData("", "icon-filename icons/title_icon.ico")
loadPrcFileData("", "window-title Scene Maker")

#custom_font = FontPool.loadFont('Figtree-Regular.ttf') 
#custom_font.setLineHeight(1)
#TextNode.setDefaultFont(custom_font)

class SceneMakerMain(ShowBase):

    def __init__(self):
        ShowBase.__init__(self)
        self.props = WindowProperties()
        self.disable_mouse()
        
        #---adjustable parameters---
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.scene_data_filename=os.path.join(base_path,'scene_params1.json')
        self.scene_light_data_filename=os.path.join(base_path,'scene_light_params1.json')
        self.scene_global_params_filename=os.path.join(base_path,'scene_global_params1.json')

        self.load_lights_from_json=True #set this False if you dont want to load point light properties from json file

        # Camera param initializations
        self.cameraHeight = 1.5     # camera Height above ground
        self.cameraAngleH = 0     # Horizontal angle (yaw)
        self.cameraAngleP = 0   # Vertical angle (pitch)
        self.camLens.setNear(0.01)
        self.camLens.setFar(2500)
        self.camera.setPos(0,0,self.cameraHeight)
        self.mouse_rotate_flag=0
        
        #---if camera y,z axis rotated 90 deg, use below code----
        #self.cam_node=NodePath('cam_node')
        #self.cam_node.reparentTo(self.render)
        #self.cam_node.setHpr(0,-90,0)
        #self.camera.reparentTo(self.cam_node)
        
        #---load global params---
        self.temp_status=''
        self.global_params={}
        self.load_global_params()
        

        self.light_name_list=[]
        self.light_list=[]
        self.light_node_list=[]
        self.current_light_model_index=None
        self.plight_idx=0
        self.set_keymap()
        self.current_model_index=0
        self.anim_name_list=[]
        self.current_animation=None
        self.load_environment_models()
        taskMgr.add(self.camera_rotate, "camera_rotateTask")
        taskMgr.add(self.camera_move, "camera_move")
        #self.sun_rotate()
        
        self.crosshair = OnscreenImage(image='crosshair.png', pos=(0,0,0),scale=0.1)
        self.crosshair.setTransparency(TransparencyAttrib.MAlpha)
        self.crosshair.hide()
        
        #self.bottom_cam_label=DirectLabel(text='CamPos: ',pos=(-1,1,-0.9),scale=0.05,text_align=TextNode.ACenter,text_fg=(1,1,1,0.9),text_bg=(0,0,0,0.2),frameColor=(0, 0, 0, 0.1))
        base.accept('tab', base.bufferViewer.toggleEnable)

        self.param_2={}               
        self.current_property=1
        self.property_names=['position','scale','rotation','color']
        self.tonemap_option_items=['Linear','Reinhard Simple ','Reinhard Photographic','ACES']
        self.pos_increment=0.001
        self.scale_increment=0.01
        self.temp_count=1
        self.fog=""
        
        self.entry_temp=""
        self.identifier_temp=""
        
        #---apply global params---
        self.apply_global_params_1()
        self.setupLights()
        self.apply_global_params_2()
        #self.set_skybox()
        self.apply_global_params_3()
        self.apply_global_params_4()
        
        #---load pbr pipeline---

        if self.global_params['skybox_enable_envmap']==True:
            env_map = simplepbr.EnvPool.ptr().load('#_envmap.jpg')
        else:
            env_map=None
        
        self.pipeline = simplepbr.init(
        env_map=env_map,
        use_normal_maps=True,
        exposure=0,
        max_lights=16,
        enable_fog=True
        )
        
    
    def create_global_params(self):
        self.global_params={}
        # settings params
        self.global_params['mouse_sensitivity']=50
        self.global_params['move_speed']=0.1
        self.global_params['crosshair']=False
        self.global_params['gizmo']=True
        self.global_params['dark_theme']=True
        
        # daylight params
        self.global_params['ambientlight_intensity']=0.5
        self.global_params['ambientlight_R']=1
        self.global_params['ambientlight_G']=1
        self.global_params['ambientlight_B']=1
        self.global_params['directionallight_intensity']=10
        self.global_params['directionallight_R']=1
        self.global_params['directionallight_G']=1
        self.global_params['directionallight_B']=1
        self.global_params['directionallight_H']=0
        self.global_params['directionallight_P']=-45
        self.global_params['directionallight_RO']=0
        self.global_params['directionallight_X']=0
        self.global_params['directionallight_Y']=0
        self.global_params['directionallight_Z']=20
        self.global_params['DL_shadow']=True
        self.global_params['DL_AxisTripod']=True
        
        # skybox params
        self.global_params['skybox_enable']=False
        self.global_params['skybox_show']=True
        self.global_params['skybox_image']=""
        self.global_params['skybox_ambientlight_intensity']=1
        self.global_params['skybox_ambientlight_R']=1
        self.global_params['skybox_ambientlight_G']=1
        self.global_params['skybox_ambientlight_B']=1
        self.global_params['sky_background_color']=[0.6,0.6,0.6,1]
        self.global_params['skybox_enable_envmap']=True
        self.global_params['skybox_enable_tonemapping']=False
        self.global_params['skybox_tonemapping_method']=1
        self.global_params['skybox_exposure']=1
        self.global_params['skybox_gamma']=1
        
        # fog params
        self.global_params['fog_enable']=False
        self.global_params['fog_type']=0
        self.global_params['fog_R']=0.5
        self.global_params['fog_G']=0.5
        self.global_params['fog_B']=0.5
        self.global_params['fog_start']=15
        self.global_params['fog_end']=150
        self.global_params['fog_density']=0.001
        
    def apply_global_params_1(self): #settings params
        self.mouse_sensitivity=self.global_params['mouse_sensitivity']
        self.move_speed=self.global_params['move_speed']
        if self.global_params['crosshair']==True:
            self.crosshair.show()
        else:
            self.crosshair.hide()
                
    def apply_global_params_2(self): #daylight params
        self.daylight_commands(self.global_params['ambientlight_intensity'],'ambientlight_intensity')
        self.daylight_commands(self.global_params['ambientlight_R'],'ambientlight_R')
        self.daylight_commands(self.global_params['ambientlight_G'],'ambientlight_G')
        self.daylight_commands(self.global_params['ambientlight_B'],'ambientlight_B')
        self.daylight_commands(self.global_params['directionallight_intensity'],'DL_intensity')
        self.daylight_commands(self.global_params['directionallight_R'],'DL_R')
        self.daylight_commands(self.global_params['directionallight_G'],'DL_G')
        self.daylight_commands(self.global_params['directionallight_B'],'DL_B')
        self.daylight_commands(self.global_params['directionallight_H'],'DL_H')
        self.daylight_commands(self.global_params['directionallight_P'],'DL_P')
        self.daylight_commands(self.global_params['directionallight_RO'],'DL_RO')
        self.daylight_commands(self.global_params['directionallight_X'],'DL_X')
        self.daylight_commands(self.global_params['directionallight_Y'],'DL_Y')
        self.daylight_commands(self.global_params['directionallight_Z'],'DL_Z')
            
    def apply_global_params_3(self): #skybox params
        self.skybox_commands(self.global_params['skybox_enable'],'enable')
        self.skybox_commands(self.global_params['skybox_show'],'show')
        self.skybox_commands(self.global_params['skybox_ambientlight_intensity'],'intensity')
        self.skybox_commands(self.global_params['skybox_ambientlight_R'],'R')
        self.skybox_commands(self.global_params['skybox_ambientlight_G'],'G')
        self.skybox_commands(self.global_params['skybox_ambientlight_B'],'B')
        self.skybox_commands(self.global_params['sky_background_color'][0],'R0')
        self.skybox_commands(self.global_params['sky_background_color'][1],'G0')
        self.skybox_commands(self.global_params['sky_background_color'][2],'B0')
        self.skybox_commands(self.global_params['sky_background_color'][3],'A0')
        self.skybox_commands(self.global_params['skybox_enable_envmap'],'enable_ibl')
        
        self.skybox_commands(self.global_params['skybox_enable_tonemapping'],'enable_tonemapping')
        self.set_skybox_tonemapping_method(int(self.global_params['skybox_tonemapping_method'])-1)
        self.skybox_commands(self.global_params['skybox_exposure'],'exposure')
        self.skybox_commands(self.global_params['skybox_gamma'],'gamma')
                    
    def apply_global_params_4(self): #fog params
        self.fog_commands(self.global_params['fog_enable'],'enable')
        self.fog_commands(self.global_params['fog_R'],'R')
        self.fog_commands(self.global_params['fog_G'],'G')
        self.fog_commands(self.global_params['fog_B'],'B')
        self.fog_commands(self.global_params['fog_start'],'start')
        self.fog_commands(self.global_params['fog_end'],'end')
        self.fog_commands(self.global_params['fog_density'],'density')
        
    def save_global_params(self):
        try:
            with open(self.scene_global_params_filename, 'w', encoding='utf-8') as f:
                json.dump(self.global_params, f, ensure_ascii=False, indent=4)
            self.display_last_status('global params json saved')
            logger.info('global params json saved')
        except:
            self.display_last_status('error while saving global params json file.')
            logger.error('error while saving global params json file.')
    
    def load_global_params(self):
        try:
            if not(os.path.exists(self.scene_global_params_filename)):
                #self.create_global_params()
                #self.save_global_params()
                self.temp_status='global params json created (and saved)'
                logger.info('global params json created (and saved)')
            else:
                with open(self.scene_global_params_filename) as json_data:
                    self.global_params = json.load(json_data)
                self.temp_status='global params json loaded'
                logger.info('global params json loaded')
        except:
            self.temp_status='error while loading global params json file.'
            logger.error('error while loading global params json file.')
    
    def display_last_status(self,msg):
        now = datetime.datetime.now()
        self.dlabel_status2['text']=now.strftime('%d-%m-%y %H:%M:%S ')+msg

    def exit_program(self):
        logger.info('program exiting.')
        sys.exit()
        
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

    def set_skybox(self):
        # Create a skybox node
        self.skybox = self.render.attachNewNode("skybox")
        self.skybox.setScale(2000)  # Scale to surround scene

        # Create a sphere programmatically
        sphere = self.create_sphere(radius=1.0, segments=32)
        sphere.reparentTo(self.skybox)

        if os.path.exists(self.global_params['skybox_image']):
            # Load the equirectangular texture
            tex = self.loader.loadTexture(self.global_params['skybox_image'])
            
            self.skybox.setTexture(tex)
            # reverse normals
            #self.skybox.node().setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullCounterClockwise))
            # Flip texture horizontally
            self.skybox.setTexScale(TextureStage.getDefault(), -1, 1)  # Negative x-scale for horizontal flip
            self.skybox.setTexOffset(TextureStage.getDefault(), 1, 0)  # Adjust offset to align (U=1 to shift origin)

        # Configure skybox rendering
        self.skybox.setTwoSided(True)  # Render both sides to see inside
        self.skybox.setBin("background", 0)  # Render first
        self.skybox.setDepthWrite(False)  # Disable depth writing
        self.skybox.setDepthTest(False)  # Disable depth testing
        self.ambientLight_skybox = AmbientLight("ambientLight")
        self.ambientLight_skybox.setColor((self.global_params['skybox_ambientlight_R'],self.global_params['skybox_ambientlight_G'],self.global_params['skybox_ambientlight_B'], 1))
        self.skybox.setLightOff()  # Ignore lighting
        self.skybox.setLight(self.render.attachNewNode(self.ambientLight_skybox))
        #self.skybox.setShaderOff()
        #self.skybox.setShaderAuto()

        # Make the skybox follow the camera
        self.taskMgr.add(self.update_skybox, "update_skybox")

    def update_skybox(self, task):
        # Update skybox position to follow camera
        self.skybox.setPos(self.camera.getPos())
        return task.cont
                    
    def set_crosshair(self):
        self.crosshair = OnscreenImage(image='crosshair.png', pos=(0,0,0),scale=0.1)
        self.crosshair.setTransparency(TransparencyAttrib.MAlpha)

    def set_cubemap(self):

        # The options when loading the texture, in this case, does not make any sense, just for demonstration.
        lo = LoaderOptions(flags = LoaderOptions.TF_generate_mipmaps)

        # Let's create a texture named "world_cube_map" and configure it.
        texture_cube_map = Texture("world_cube_map")
        texture_cube_map.setup_cube_map()
        texture_cube_map.read(fullpath = 'right.png',  z = 0, n = 0, read_pages = False, read_mipmaps = False, options = lo)
        texture_cube_map.read(fullpath = 'left.png',   z = 1, n = 0, read_pages = False, read_mipmaps = False, options = lo)
        texture_cube_map.read(fullpath = 'bottom.png', z = 2, n = 0, read_pages = False, read_mipmaps = False, options = lo)
        texture_cube_map.read(fullpath = 'top.png',    z = 3, n = 0, read_pages = False, read_mipmaps = False, options = lo)
        texture_cube_map.read(fullpath = 'front.png',  z = 4, n = 0, read_pages = False, read_mipmaps = False, options = lo)
        texture_cube_map.read(fullpath = 'back.png',   z = 5, n = 0, read_pages = False, read_mipmaps = False, options = lo)

        # You can add texture to the pool if you need to.
        TexturePool.add_texture(texture_cube_map)

        skybox = loader.load_model('sphere.bam')
        skybox.reparentTo(self.render)
        skybox.set_texture(texture_cube_map)
        
        # Necessary manipulations with the transformation of texture coordinates.
        ts = TextureStage.get_default()
        skybox.set_tex_gen(ts, TexGenAttrib.M_world_cube_map)
        skybox.set_tex_hpr(ts, (0, 90, 180))
        skybox.set_tex_scale(ts, (1, -1))
        # We will remove rendering effects that will be unnecessary.
        skybox.set_light_off()
        skybox.set_material_off()
        skybox.setShaderOff()
        skybox.setScale(1000,1000,1000)
        #skybox.setHpr(0,90,0)                             
         # Create and configure an ambient light
        #ambient_light = AmbientLight("ambient_light")
        #ambient_light.set_color((.1, .1, .1, 1))  # RGBA: full white light, fully opaque
        ambient_light_node = self.render.attach_new_node(self.ambientLight)

        # Apply the light to the loaded model
        skybox.set_light(ambient_light_node)          
                
    def daylight_commands(self,textEntered,identifier):
        try:
            # textEntered value may be integer if it called from other than gui
            textEntered_num=float(textEntered)
            textEntered_str=str(textEntered)

            r=self.global_params['ambientlight_R']*self.global_params['ambientlight_intensity']
            g=self.global_params['ambientlight_G']*self.global_params['ambientlight_intensity']
            b=self.global_params['ambientlight_B']*self.global_params['ambientlight_intensity']
            self.ambientLight.setColor((r,g,b, 1))
            r=self.global_params['directionallight_R']*self.global_params['directionallight_intensity']
            g=self.global_params['directionallight_G']*self.global_params['directionallight_intensity']
            b=self.global_params['directionallight_B']*self.global_params['directionallight_intensity']
            h=self.global_params['directionallight_H']
            p=self.global_params['directionallight_P']
            ro=self.global_params['directionallight_RO']
            x=self.global_params['directionallight_X']
            y=self.global_params['directionallight_Y']
            z=self.global_params['directionallight_Z']
            self.directionalLight.setColor((r,g,b, 1))
            self.dlight1.setHpr(h,p,ro)
            self.dlight1.setPos(x,y,z)
        except Exception as e:
            logger.error('error in daylight gui entry:')
            logger.error(e)

    def set_skybox_tonemapping_method(self,InputValue):
        try:
            if self.global_params['skybox_enable_tonemapping']==True:
                self.skybox.setShaderInput('tonemapping_method', self.global_params['skybox_tonemapping_method'])
                self.skybox_commands(self.global_params['skybox_exposure'],'exposure')
                self.skybox_commands(self.global_params['skybox_gamma'],'gamma')
            else:
                print('skybox tonemapping is not enabled.')
        except:
            print('error when setting tonemapping_method')
        
    def skybox_commands(self,InputValue,identifier):
        try:
            if identifier=='enable':
                if InputValue==True:
                    self.set_skybox()
                else:
                    taskMgr.remove("update_skybox")
                    self.skybox.detachNode()
                    self.skybox.removeNode()
                    print('skybox removed.')
            elif identifier=='show':
                if self.global_params['skybox_enable']==True:
                    if InputValue==True:
                        self.skybox.show()
                        print('skybox showed.')
                    else:
                        self.skybox.hide()
                        print('skybox hided.')
                else:
                    print('skybox disabled. enable to show or hide.')
            elif identifier=='intensity':
                try:
                    InputValue=float(InputValue)
                    IN=self.global_params['skybox_ambientlight_intensity']
                    r=self.global_params['skybox_ambientlight_R']*IN
                    g=self.global_params['skybox_ambientlight_G']*IN
                    b=self.global_params['skybox_ambientlight_B']*IN
                    self.ambientLight_skybox.setColor((r,g,b, 1))
                except:
                    logger.error('error when setting skybox intensity')
            elif identifier=='R':
                try:
                    InputValue=float(InputValue)
                    IN=self.global_params['skybox_ambientlight_intensity']
                    r=self.global_params['skybox_ambientlight_R']*IN
                    g=self.global_params['skybox_ambientlight_G']*IN
                    b=self.global_params['skybox_ambientlight_B']*IN
                    self.ambientLight_skybox.setColor((r,g,b, 1))
                except:
                    logger.error('error when setting skybox color R')
            elif identifier=='G':
                try:
                    InputValue=float(InputValue)
                    IN=self.global_params['skybox_ambientlight_intensity']
                    r=self.global_params['skybox_ambientlight_R']*IN
                    g=self.global_params['skybox_ambientlight_G']*IN
                    b=self.global_params['skybox_ambientlight_B']*IN
                    self.ambientLight_skybox.setColor((r,g,b, 1))
                except:
                    logger.error('error when setting skybox color G')
            elif identifier=='B':
                try:
                    InputValue=float(InputValue)
                    IN=self.global_params['skybox_ambientlight_intensity']
                    r=self.global_params['skybox_ambientlight_R']*IN
                    g=self.global_params['skybox_ambientlight_G']*IN
                    b=self.global_params['skybox_ambientlight_B']*IN
                    self.ambientLight_skybox.setColor((r,g,b, 1))
                except:
                    logger.error('error when setting skybox color B')
            elif identifier=='R0':
                try:
                    InputValue=float(InputValue)
                    self.setBackgroundColor(self.global_params['sky_background_color'])
                except:
                    logger.error('error when setting background color R')
            elif identifier=='G0':
                try:
                    InputValue=float(InputValue)
                    self.setBackgroundColor(self.global_params['sky_background_color'])
                except:
                    logger.error('error when setting background color G')
            elif identifier=='B0':
                try:
                    InputValue=float(InputValue)
                    self.setBackgroundColor(self.global_params['sky_background_color'])
                except:
                    logger.error('error when setting background color B')
            elif identifier=='A0':
                try:
                    InputValue=float(InputValue)
                    self.setBackgroundColor(self.global_params['sky_background_color'])
                except:
                    logger.error('error when setting background color A')
            elif identifier=='save_envmap':
                base.saveCubeMap('#_envmap.jpg', size = 512)
                logger.info('envmap saved.')
            elif identifier=='enable_tonemapping':
                if self.global_params['skybox_enable']==True:
                    if InputValue==True:
                        shader = Shader.load(Shader.SL_GLSL, vertex = 'shaders/skybox_tonemapping.vert', fragment = 'shaders/skybox_tonemapping.frag')
                        # Apply shader to skybox
                        #self.skybox.setShaderOff()
                        #self.skybox.setShaderAuto()
                        self.skybox.setShader(shader)
                        self.skybox.setShaderInput('exposure', self.global_params['skybox_exposure'])
                        self.skybox.setShaderInput('gamma', self.global_params['skybox_gamma'])
                        self.skybox.setShaderInput('tonemapping_method', self.global_params['skybox_tonemapping_method'])
                        self.skybox.setShaderInput('param_a', self.global_params['skybox_exposure'])

                    else:
                        #self.skybox.setLightOff()
                        #self.skybox.setShaderAuto()
                        self.skybox.clearShader()
                else:
                    print('skybox is not enabled.')
            elif identifier=='exposure':
                try:
                    InputValue=float(InputValue)
                    if self.global_params['skybox_enable_tonemapping']==True:
                        self.skybox.setShaderInput('exposure', self.global_params['skybox_exposure'])
                    else:
                        print('skybox tonemapping is not enabled.')
                except:
                    logger.error('error when setting skybox_exposure')
            elif identifier=='gamma':
                try:
                    InputValue=float(InputValue)
                    if self.global_params['skybox_enable_tonemapping']==True:
                        self.skybox.setShaderInput('gamma', self.global_params['skybox_gamma'])
                    else:
                        print('skybox tonemapping is not enabled.')
                except:
                    logger.error('error when setting skybox_gamma')
                
        except Exception as e:
            logger.error('error in skybox gui entry:')
            logger.error(e)

    def heightmap_commands(self,InputValue,identifier):
        try:
            if identifier=='unique_name':
                if (InputValue.lower()=='render') or (InputValue.lower()=='none') or (InputValue.lower()==''):
                    logger.info('heightmap unique name should not be render or none or empty')
                else:
                    if InputValue not in self.models_names_all:
                        print('heightmap unique name is set.')
                    else:
                        print('heightmap unique name already exists.')
            elif identifier=='blocksize':
                try:
                    InputValue=int(InputValue)
                    if self.param_1['type']=='terrain':
                        self.terrain_all[self.current_model_index].setBlockSize(InputValue)
                    else:
                        print('current model not a terrain.')
                except:
                    print('error when setting the blocksize in heightmap.')
            elif identifier=='near':
                try:
                    InputValue=int(InputValue)
                    if self.param_1['type']=='terrain':
                        self.terrain_all[self.current_model_index].setNear(InputValue)
                    else:
                        print('current model not a terrain.')
                except:
                    print('error when setting the near in heightmap.')
            elif identifier=='far':
                try:
                    InputValue=int(InputValue)
                    if self.param_1['type']=='terrain':
                        self.terrain_all[self.current_model_index].setFar(InputValue)
                    else:
                        print('current model not a terrain.')
                except:
                    self.display_last_status('error when setting the far in heightmap.')
            elif identifier=='X':
                try:
                    InputValue=int(InputValue)
                    if self.param_1['type']=='terrain':
                        y_val=self.data_all[self.current_model_index]['heightmap_param'][6]
                        self.models_all[self.current_model_index].setTexScale(TextureStage.getDefault(), InputValue, y_val)
                    else:
                        print('current model not a terrain.')
                except:
                    self.display_last_status('error when setting the X in heightmap.')
            elif identifier=='Y':
                try:
                    InputValue=int(InputValue)
                    if self.param_1['type']=='terrain':
                        x_val=self.data_all[self.current_model_index]['heightmap_param'][5]
                        self.models_all[self.current_model_index].setTexScale(TextureStage.getDefault(), x_val, InputValue)
                    else:
                        print('current model not a terrain.')
                except:
                    self.display_last_status('error when setting the Y in heightmap.')
            elif identifier=='generate_terrain':
                if (InputValue.lower()=='render') or (InputValue.lower()=='none') or (InputValue.lower()==''):
                    self.display_last_status('heightmap unique name should not be render or none or empty.')
                else:
                    if InputValue not in self.models_names_all:
                        self.initialize_model_param(InputValue,'')
                        self.param_1['type']='terrain'
                        self.param_1["uniquename"]=InputValue
                        self.param_1["heightmap_param"][0]=self.dlabel_j4['text']
                        self.param_1["heightmap_param"][1]=int(self.dentry_j7.get())
                        self.param_1["heightmap_param"][2]=int(self.dentry_j9.get())
                        self.param_1["heightmap_param"][3]=int(self.dentry_j11.get())
                        self.param_1["heightmap_param"][4]=self.dlabel_j15['text']
                        self.param_1["heightmap_param"][5]=float(self.dentry_j19.get())
                        self.param_1["heightmap_param"][6]=float(self.dentry_j21.get())
                        self.terrain = GeoMipTerrain("myDynamicTerrain")
                        self.terrain.setHeightfield(self.param_1['heightmap_param'][0])#heightmap.png
                        # Set terrain properties
                        self.terrain.setBlockSize(self.param_1['heightmap_param'][1])
                        self.terrain.setNear(self.param_1['heightmap_param'][2])
                        self.terrain.setFar(self.param_1['heightmap_param'][3])
                        self.terrain.setFocalPoint(self.camera)
                        # Store the root NodePath
                        terrain_root = self.terrain.getRoot()
                        if self.param_1['heightmap_param'][4]!='':
                            # Apply a texture to the terrain
                            texture = loader.loadTexture(self.param_1['heightmap_param'][4])  # Replace with your texture
                            terrain_root.setTexture(TextureStage.getDefault(), texture)
                            terrain_root.setTexScale(TextureStage.getDefault(), self.param_1['heightmap_param'][5], self.param_1['heightmap_param'][6])  # Tile texture
                        #self.create_collision_mesh(terrain_root,"collision_root/environ1")
                        #terrain_root.setCollideMask(1)
                        self.ModelTemp=terrain_root
                        self.load_model_from_param(fileload_flag=True,indexload_flag=False)
                        # Generate it.
                        self.terrain.generate()
                        self.terrain_all[self.current_model_index]=self.terrain                                                    
                        logger.info('terrain generated.')
                    else:
                        print('heightmap unique name already exists. enter new unique name.')

        except Exception as e:
            logger.error('error in heightmap gui entry:')
            logger.error(e)

    def fog_commands(self,InputValue,identifier):
        try:
            if identifier=='enable':
                if self.global_params['fog_enable']==True:
                    self.fog = Fog("FogEffect")
                    self.fog.setColor(Vec4(self.global_params['fog_R'], self.global_params['fog_G'], self.global_params['fog_B'], 1))
                    if self.global_params['fog_type']==0:
                        self.fog.setLinearRange(self.global_params['fog_start'], self.global_params['fog_end'])
                    if self.global_params['fog_type']==1:
                        self.fog.setExpDensity(self.global_params['fog_density'])
                    self.render.setFog(self.fog)
                else:
                    self.render.clearFog()

            if identifier=='R':
                InputValue=float(InputValue)
                if self.global_params['fog_enable']==True:
                    self.fog.setColor(Vec4(self.global_params['fog_R'], self.global_params['fog_G'], self.global_params['fog_B'], 1))
            if identifier=='G':
                InputValue=float(InputValue)
                if self.global_params['fog_enable']==True:
                    self.fog.setColor(Vec4(self.global_params['fog_G'], self.global_params['fog_G'], self.global_params['fog_B'], 1))
            if identifier=='B':
                InputValue=float(InputValue)
                if self.global_params['fog_enable']==True:
                    self.fog.setColor(Vec4(self.global_params['fog_R'], self.global_params['fog_G'], self.global_params['fog_B'], 1))
            if identifier=='start':
                InputValue=float(InputValue)
                if self.global_params['fog_type']==0:
                    if self.global_params['fog_enable']==True:
                        self.fog.setLinearRange(self.global_params['fog_start'], self.global_params['fog_end'])
                        self.render.clearFog()
                        self.render.setFog(self.fog)
            if identifier=='end':
                InputValue=float(InputValue)
                if self.global_params['fog_type']==0:
                    if self.global_params['fog_enable']==True:
                        self.fog.setLinearRange(self.global_params['fog_start'], self.global_params['fog_end'])
                        self.render.clearFog()
                        self.render.setFog(self.fog)
            if identifier=='density':
                InputValue=float(InputValue)
                if self.global_params['fog_type']==1:
                    if self.global_params['fog_enable']==True:
                        self.fog.setExpDensity(self.global_params['fog_density'])
                        self.render.clearFog()
                        self.render.setFog(self.fog)

        except Exception as e:
            logger.error('error in fog gui entry:')
            logger.error(e)
            
    def SetEntryText_e(self,textEntered,identifier):
        #if 1:
        try:
            idx=self.current_light_model_index
            idx2=self.plight_idx
            if identifier=='Overall_Intensity':
                overall_intensity=float(textEntered)
                self.data_all_light[idx]['overall_intensity']=overall_intensity
                for i in range(len(self.light_list)):
                    intensity=self.data_all_light[idx]['plights'][i]['intensity']
                    r=self.data_all_light[idx]['plights'][i]['color'][1][0]*intensity*overall_intensity
                    g=self.data_all_light[idx]['plights'][i]['color'][1][1]*intensity*overall_intensity
                    b=self.data_all_light[idx]['plights'][i]['color'][1][2]*intensity*overall_intensity
                    self.light_list[i].setColor((r,g,b,1))
            elif identifier=='Intensity':
                intensity=float(textEntered)
                self.data_all_light[idx]['plights'][idx2]['intensity']=intensity
                overall_intensity=self.data_all_light[idx]['overall_intensity']
                r2=self.data_all_light[idx]['plights'][idx2]['color'][1][0]*intensity*overall_intensity
                g2=self.data_all_light[idx]['plights'][idx2]['color'][1][1]*intensity*overall_intensity
                b2=self.data_all_light[idx]['plights'][idx2]['color'][1][2]*intensity*overall_intensity
                self.light_list[idx2].setColor((r2,g2,b2,1))
            elif identifier=='R':
                r=float(textEntered)
                overall_intensity=self.data_all_light[idx]['overall_intensity']
                intensity=self.data_all_light[idx]['plights'][idx2]['intensity']
                self.data_all_light[idx]['plights'][idx2]['color'][1][0]=r
                r2=r*intensity*overall_intensity
                g2=self.data_all_light[idx]['plights'][idx2]['color'][1][1]*intensity*overall_intensity
                b2=self.data_all_light[idx]['plights'][idx2]['color'][1][2]*intensity*overall_intensity
                self.light_list[idx2].setColor((r2,g2,b2,1))
            elif identifier=='G':
                g=float(textEntered)
                overall_intensity=self.data_all_light[idx]['overall_intensity']
                intensity=self.data_all_light[idx]['plights'][idx2]['intensity']
                self.data_all_light[idx]['plights'][idx2]['color'][1][1]=g
                g2=g*intensity*overall_intensity
                r2=self.data_all_light[idx]['plights'][idx2]['color'][1][0]*intensity*overall_intensity
                b2=self.data_all_light[idx]['plights'][idx2]['color'][1][2]*intensity*overall_intensity
                self.light_list[idx2].setColor((r2,g2,b2,1))
            elif identifier=='B':
                b=float(textEntered)
                overall_intensity=self.data_all_light[idx]['overall_intensity']
                intensity=self.data_all_light[idx]['plights'][idx2]['intensity']
                self.data_all_light[idx]['plights'][idx2]['color'][1][2]=b
                b2=b*intensity*overall_intensity
                r2=self.data_all_light[idx]['plights'][idx2]['color'][1][0]*intensity*overall_intensity
                g2=self.data_all_light[idx]['plights'][idx2]['color'][1][1]*intensity*overall_intensity
                self.light_list[idx2].setColor((r2,g2,b2,1))
            elif identifier=='C':
                c=float(textEntered)
                self.data_all_light[idx]['plights'][idx2]['attenuation'][1][0]=c
                #c=self.data_all_light[idx]['plights'][idx2]['attenuation'][1][0]
                l=self.data_all_light[idx]['plights'][idx2]['attenuation'][1][1]
                q=self.data_all_light[idx]['plights'][idx2]['attenuation'][1][2]
                self.light_list[idx2].setAttenuation((c,l,q))
            elif identifier=='L':
                l=float(textEntered)
                self.data_all_light[idx]['plights'][idx2]['attenuation'][1][1]=l
                c=self.data_all_light[idx]['plights'][idx2]['attenuation'][1][0]
                #l=self.data_all_light[idx]['plights'][idx2]['attenuation'][1][1]
                q=self.data_all_light[idx]['plights'][idx2]['attenuation'][1][2]
                self.light_list[idx2].setAttenuation((c,l,q))
            elif identifier=='Q':
                q=float(textEntered)
                self.data_all_light[idx]['plights'][idx2]['attenuation'][1][2]=q
                c=self.data_all_light[idx]['plights'][idx2]['attenuation'][1][0]
                l=self.data_all_light[idx]['plights'][idx2]['attenuation'][1][1]
                #q=self.data_all_light[idx]['plights'][idx2]['attenuation'][1][2]
                self.light_list[idx2].setAttenuation((c,l,q))
            elif identifier=='Notes':
                val=str(textEntered)
                self.data_all_light[idx]['plights'][idx2]['notes']=val
        #else:
        except:
            logger.error('error in entry_e')
        
    def load_environment_models(self):
        json_file=self.scene_data_filename
        with open(json_file) as json_data:
            self.data_all = json.load(json_data)
        
        with open(self.scene_light_data_filename) as json_data:
            self.data_all_light = json.load(json_data)
            
        self.models_all=[]
        self.actors_all=[]
        self.terrain_all=[]
        self.models_names_all=[]
        self.models_names_enabled=[]
        self.ModelTemp=""
        self.models_with_lights=[]
        for dobj in self.data_all_light:
            self.models_with_lights.append(dobj["uniquename"])
        self.models_light_names=[]
        self.models_light_all=[]
        self.models_light_node_all=[]
        for i in range(len(self.data_all)):
            print(f"loading models: {i+1}/{len(self.data_all)}")
            data=self.data_all[i]
            self.models_names_all.append(data["uniquename"])
            if 'actor' not in data:
                data['actor']=[False, "",False,[]]#[load Actor?,animation name,loop on?,[animation file 1.egg,2.egg]]
            if 'parent' not in data:
                data['parent']=[True, "render"]#[load Actor?,animation name,loop on?,[animation file 1.egg,2.egg]]
            if 'type' not in data:
                data['type']="3d_model"
            if 'heightmap_param' not in data:
                data['heightmap_param']=['',0,0,0,'',0,0]
               
            if data["enable"]:
                if data['actor'][0]==True:
                    self.current_actor=Actor(data["filename"])
                    self.actors_all.append(self.current_actor)
                    self.ModelTemp=self.render.attachNewNode("actor_node")
                    self.current_actor.reparentTo(self.ModelTemp)
                    #self.ModelTemp=Actor(ModelTemp.find("**/__Actor_modelRoot"))
                    self.terrain_all.append('')
                elif data['type']=='terrain':
                    self.current_actor=''
                    self.actors_all.append(self.current_actor)
                    self.terrain = GeoMipTerrain("myDynamicTerrain")
                    self.terrain.setHeightfield(data['heightmap_param'][0])#heightmap.png
                    # Set terrain properties
                    self.terrain.setBlockSize(data['heightmap_param'][1])
                    self.terrain.setNear(data['heightmap_param'][2])
                    self.terrain.setFar(data['heightmap_param'][3])
                    self.terrain.setFocalPoint(self.camera)
                    # Store the root NodePath
                    terrain_root = self.terrain.getRoot()
                    if data['heightmap_param'][4]!='':
                        # Apply a texture to the terrain
                        texture = loader.loadTexture(data['heightmap_param'][4])  # Replace with your texture
                        terrain_root.setTexture(TextureStage.getDefault(), texture)
                        terrain_root.setTexScale(TextureStage.getDefault(), data['heightmap_param'][5], data['heightmap_param'][6])  # Tile texture
                    #self.create_collision_mesh(terrain_root,"collision_root/environ1")
                    #terrain_root.setCollideMask(1)
                    self.ModelTemp=terrain_root
                    # Generate it.
                    self.terrain.generate()
                    self.terrain_all.append(self.terrain)
                else:
                    self.current_actor=''
                    self.actors_all.append(self.current_actor)
                    self.ModelTemp=loader.loadModel(data["filename"])
                    self.terrain_all.append('')
                #--- uncomment the below code to load the point lights from model and use save button to save the params
                #(param_2,light_name_list,light_list,light_node_list)=self.get_point_light_properties_from_model(self.ModelTemp,data)
                #if len(param_2)>0:
                #    self.data_all_light.append(param_2.copy())
                if data["uniquename"] in self.models_with_lights:
                    idx=self.models_with_lights.index(data["uniquename"])
                    (self.param_2,self.light_name_list,self.light_list,self.light_node_list)=self.get_point_light_properties_from_model(self.ModelTemp,data)
                    if len(self.param_2)>0:
                        if self.load_lights_from_json==True:
                            self.current_light_model_index=idx
                        self.models_light_names.append(self.light_name_list)
                        self.models_light_all.append(self.light_list)
                        self.models_light_node_all.append(self.light_node_list)
                        for tmp in self.light_node_list:
                            self.render.setLight(tmp)
                        for j2 in range(len(self.light_name_list)):
                            idx2=j2
                            self.plight_idx=j2
                            self.SetEntryText_e(self.data_all_light[self.current_light_model_index]['plights'][idx2]['color'][1][0],'R')
                            self.SetEntryText_e(self.data_all_light[self.current_light_model_index]['plights'][idx2]['color'][1][1],'G')
                            self.SetEntryText_e(self.data_all_light[self.current_light_model_index]['plights'][idx2]['color'][1][2],'B')
                            self.SetEntryText_e(self.data_all_light[self.current_light_model_index]['plights'][idx2]['attenuation'][1][0],'C')
                            self.SetEntryText_e(self.data_all_light[self.current_light_model_index]['plights'][idx2]['attenuation'][1][0],'L')
                            self.SetEntryText_e(self.data_all_light[self.current_light_model_index]['plights'][idx2]['attenuation'][1][0],'Q')
                        
                self.models_names_enabled.append(data["uniquename"])
                d=data["pos"][1]
                if data["pos"][0]: self.ModelTemp.setPos(d[0],d[1],d[2])
                d=data["scale"][1]
                if data["scale"][0]: self.ModelTemp.setScale(d[0],d[1],d[2])
                d=data["hpr"][1]
                if data["hpr"][0]: self.ModelTemp.setHpr(d[0],d[1],d[2])
                d=data["color"][1]
                if data["color"][0]: self.ModelTemp.setColorScale(d[0],d[1],d[2],d[3]) 
                #self.ModelTemp.clearLight()
                
                #---set actor data---
                if data['actor'][0]==True:
                    try:
                        for k in range(len(data['actor'][3])):
                            animpath=data['actor'][3][k]
                            bname=os.path.basename(animpath)
                            aname=os.path.splitext(bname)[0]
                            #print(self.ModelTemp.getChild(0).ls())
                            #tmp=Actor(ModelTemp.find("**/__Actor_modelRoot"))
                            self.current_actor.loadAnims({aname: animpath})
                        
                        self.current_animation = self.current_actor.getAnimControl(data['actor'][1])
                        if data['actor'][2]==True:
                            self.current_animation.loop(0)
                    except Exception as err:
                        print(err)
                else:
                    pass
                
                self.models_all.append(self.ModelTemp)
                #self.models_all[-1].reparentTo(self.render)
                if data['show']==True:
                    self.models_all[-1].show()
                else:
                    self.models_all[-1].hide()
                #---for later use---
                self.param_1=data
            else:
                self.models_all.append("")
                
        #---parenting---
        self.create_model_parent_vars()
        for i in range(len(self.data_all)):
            if self.models_enabled_all[i]==True:
                if self.model_parent_enabled_all[i]==True:
                    self.attach_to_parent_2(self.models_all[i],self.model_parent_indices_all[i])

    def create_model_parent_vars(self):
        self.model_parent_names_all=[]
        self.model_parent_indices_all=[]
        self.model_parent_availability_all=[]#true means, the parent name is present in model names
        self.model_parent_enabled_all=[]
        self.models_enabled_all=[]
        for i in range(len(self.data_all)):
            self.models_enabled_all.append(self.data_all[i]['enable'])
            self.model_parent_enabled_all.append(self.data_all[i]['parent'][0])
            self.model_parent_names_all.append(self.data_all[i]['parent'][1])
            parent=self.data_all[i]['parent'][1]
            if parent=='render':
                self.model_parent_availability_all.append(True)
                self.model_parent_indices_all.append(0)
            elif parent=='none':
                self.model_parent_availability_all.append(True)
                self.model_parent_indices_all.append(-1)
            elif parent in self.models_names_all:
                idx=self.models_names_all.index(parent)
                self.model_parent_availability_all.append(True)
                self.model_parent_indices_all.append(idx+1)
            else:
                self.model_parent_availability_all.append(False)
                self.model_parent_indices_all.append(-1)
                        
    def set_keymap(self):
        self.keyMap = {"move_forward": 0, "move_backward": 0, "move_left": 0, "move_right": 0,"gravity_on":0,"take_screenshot":0}
        self.accept('escape', self.exit_program)
        self.accept("w", self.setKey, ["move_forward", True])
        self.accept("s", self.setKey, ["move_backward", True])
        self.accept("w-up", self.setKey, ["move_forward", False])
        self.accept("s-up", self.setKey, ["move_backward", False])
        self.accept("a", self.setKey, ["move_left", True])
        self.accept("d", self.setKey, ["move_right", True])
        self.accept("a-up", self.setKey, ["move_left", False])
        self.accept("d-up", self.setKey, ["move_right", False])
        self.accept("b", self.setKey, ["gravity_on", None])
        self.accept("x", self.setKey, ["take_screenshot", True]) 
        
    # Records the state of the keys
    def setKey(self, key, value):
        
        if key=="gravity_on":
            self.keyMap[key]=not(self.keyMap[key])
        elif key=='take_screenshot':
            self.take_screenshot()
            self.keyMap[key]=False
        else:
            self.keyMap[key] = value

    def initialize_model_param(self,uniquename,modelfilepath):
        self.param_1={}
        self.param_1['uniquename']=uniquename
        self.param_1['filename']=modelfilepath
        self.param_1['enable']=True
        self.param_1['show']=True
        tempos=self.get_an_point_front_of_camera(0,self.camera.getH(),self.camera.getP())
        self.param_1['pos']=[True,tempos]
        self.param_1['scale']=[False,[0,0,0]]
        self.param_1['color']=[False,[0,0,0,1]]
        self.param_1['hpr']=[False,[0,0,0]]
        self.param_1['details']=""
        self.param_1['notes']=""
        self.param_1['pickable']=[True, ""]
        self.param_1['enable_lights_from_model']=[False, ""]
        self.param_1['load_lights_from_json']=[True, ""]
        self.param_1['actor']=[False, "",False,[]]#[load Actor?,animation name,loop on?,[animation file 1.egg,2.egg]]
        self.param_1['parent']=[True,'render']
        self.param_1['type']='3d_model'#'terrain' for heightmaps
        self.param_1['heightmap_param']=['',0,0,0,'',0,0]#[heightmap_img_name,blocksize,near,far,texture_name,tex_scale_x,tex_scale_y]
            
    def setupLights(self):  # Sets up some default lighting
        self.ambientLight = AmbientLight("ambientLight")
        self.render.setLight(self.render.attachNewNode(self.ambientLight))
        self.directionalLight = DirectionalLight("directionalLight_1")
        self.directionalLight.setShadowCaster(True, 512,512)
        self.dlight1=self.render.attachNewNode(self.directionalLight)
        self.dlight1.setHpr(0, -45, 0)
        self.dlight1.setPos(0,0,20)
        
        self.suncube = loader.loadModel("cube_arrow.glb")
        self.suncube.reparentTo(self.dlight1)
        self.suncube.setScale(1.5,1.5,1.5)              

        self.dlight1.node().get_lens().set_film_size(50, 50)
        self.dlight1.node().get_lens().setNearFar(1, 50)
        self.dlight1.node().show_frustum()
        self.render.setLight(self.dlight1)
        
    def camera_rotate(self,task):
        # Check to make sure the mouse is readable
        if self.mouseWatcherNode.hasMouse():
            # get the mouse position as a LVector2. The values for each axis are from -1 to
            # 1. The top-left is (-1,-1), the bottom right is (1,1)
            mpos = self.mouseWatcherNode.getMouse()
            if self.mouse_rotate_flag==0:
                self.props.setCursorHidden(True)
                self.win.requestProperties(self.props)
                self.win.movePointer(0, int(self.win.getXSize() / 2), int(self.win.getYSize() / 2))
                self.mouse_rotate_flag=1
            mouse = self.win.getPointer(0)
            mx, my = mouse.getX(), mouse.getY()
            # Reset mouse to center to prevent edge stopping
            self.win.movePointer(0, int(self.win.getXSize() / 2), int(self.win.getYSize() / 2))

            # Calculate mouse delta
            dx = mx - int(self.win.getXSize() / 2)
            dy = my - int(self.win.getYSize() / 2)

            # Update camera angles based on mouse movement
            self.cameraAngleH -= dx * self.mouse_sensitivity * globalClock.getDt()
            self.cameraAngleP -= dy * self.mouse_sensitivity * globalClock.getDt()

            # Clamp pitch to avoid flipping
            self.cameraAngleP = max(-90, min(90, self.cameraAngleP))
            
            #self.camera.setPos(camX, camY, camZ)
            self.camera.setHpr(self.cameraAngleH, self.cameraAngleP, 0)
        return Task.cont  # Task continues infinitely

    def sun_rotate(self):
        self.dlight1_rot=self.dlight1.hprInterval(10.0, Point3(0, 360, 0))
        self.dlight1_rot.loop()
        self.suncube_rot=self.suncube.hprInterval(10.0, Point3(0, 360, 0))
        self.suncube_rot.loop()
        return 1
    
    def camera_move(self,task):
        pos_val=self.camera.getPos()
        heading=(math.pi*(self.camera.getH()))/180
        pitch=(math.pi*(self.camera.getP()))/180
        newval_1=pos_val[1]
        newval_2=pos_val[0]
        newval_3=pos_val[2]
        if self.keyMap['move_forward']==True:#forward is y direction
            newval_1=pos_val[1]+self.move_speed*math.cos(heading)*math.cos(pitch)
            newval_2=pos_val[0]-self.move_speed*math.sin(heading)*math.cos(pitch)
            newval_3=pos_val[2]+self.move_speed*math.sin(pitch)
        if self.keyMap['move_backward']==True:
            newval_1=pos_val[1]-self.move_speed*math.cos(heading)*math.cos(pitch)
            newval_2=pos_val[0]+self.move_speed*math.sin(heading)*math.cos(pitch)
            newval_3=pos_val[2]-self.move_speed*math.sin(pitch)
        if self.keyMap['move_left']==True==1:
            newval_1=pos_val[1]+self.move_speed*math.cos(heading+(math.pi/2))
            newval_2=pos_val[0]-self.move_speed*math.sin(heading+(math.pi/2))
        if self.keyMap['move_right']==True:#right is x direction
            newval_1=pos_val[1]-self.move_speed*math.cos(heading+(math.pi/2))
            newval_2=pos_val[0]+self.move_speed*math.sin(heading+(math.pi/2))
        if self.keyMap['gravity_on']==True:
            newval_3=1
        self.camera.setPos(newval_2,newval_1,newval_3)
        #self.bottom_cam_label.setText('CamPos: %0.2f,%0.2f,%0.2f'%(newval_2,newval_1,newval_3))
        #print([newval_2,newval_1,newval_3])
        return Task.cont

    def get_an_point_front_of_camera(self,distance,H,P):
        pos_val=self.camera.getPos()
        heading=(math.pi*(H))/180
        pitch=(math.pi*(P))/180
        newval_1=pos_val[1]+distance*math.cos(heading)*math.cos(pitch)
        newval_2=pos_val[0]-distance*math.sin(heading)*math.cos(pitch)
        newval_3=pos_val[2]+distance*math.sin(pitch)
        return [newval_2,newval_1,newval_3]

    def load_model_from_param(self,fileload_flag,indexload_flag):
        if self.param_1["uniquename"] not in self.models_names_all:
            self.models_names_all.append(self.param_1["uniquename"])
            self.actors_all.append('')
            self.terrain_all.append('')
            fileload_flag=True
            indexload_flag=False
            self.current_model_index=len(self.models_names_all)-1
        else:
            if indexload_flag==True:
                fileload_flag=False
                print('model file loading from index '+str(self.current_model_index))
                self.display_last_status('model file is loading... (index:'+str(self.current_model_index)+')')
            else:
                if fileload_flag==False:
                    indexload_flag==True
                    print('model file is loading from index '+str(self.current_model_index))
                    self.display_last_status('model file is loading... (index:'+str(self.current_model_index)+')')
                else:
                    print('model file loading from disk.')
                    self.display_last_status('model file is loading... (from drive)')
            
        if self.param_1['enable']==True:
            if fileload_flag==True:
                if self.param_1['type']=='3d_model':
                    self.ModelTemp=loader.loadModel(self.param_1["filename"])
                #---get and load light properties---
                (self.param_2,self.light_name_list,self.light_list,self.light_node_list)=self.get_point_light_properties_from_model(self.ModelTemp,self.param_1)
                if len(self.param_2)>0:
                    self.models_with_lights.append(self.param_1["uniquename"])
                    self.current_light_model_index=len(self.models_with_lights)-1
                    self.data_all_light.append(self.param_2.copy())
                    self.models_light_names.append(self.light_name_list)
                    self.models_light_all.append(self.light_list)
                    self.models_light_node_all.append(self.light_node_list)
                    for tmp in self.light_node_list:
                        self.render.setLight(tmp)
                    for j2 in range(len(self.light_name_list)):
                        idx2=j2
                        self.plight_idx=j2
                        self.SetEntryText_e(self.data_all_light[self.current_light_model_index]['plights'][idx2]['color'][1][0],'R')
                        self.SetEntryText_e(self.data_all_light[self.current_light_model_index]['plights'][idx2]['color'][1][1],'G')
                        self.SetEntryText_e(self.data_all_light[self.current_light_model_index]['plights'][idx2]['color'][1][2],'B')
                        self.SetEntryText_e(self.data_all_light[self.current_light_model_index]['plights'][idx2]['attenuation'][1][0],'C')
                        self.SetEntryText_e(self.data_all_light[self.current_light_model_index]['plights'][idx2]['attenuation'][1][0],'L')
                        self.SetEntryText_e(self.data_all_light[self.current_light_model_index]['plights'][idx2]['attenuation'][1][0],'Q')
                    
            if indexload_flag==True:
                self.ModelTemp=self.models_all[self.current_model_index]
                #self.ModelTemp.reparentTo(self.render)
                self.attach_to_parent_2(self.ModelTemp,self.model_parent_indices_all[self.current_model_index])
                #---load light properties---
                try:
                    idx=self.models_with_lights.index(self.models_names_all[self.current_model_index])
                except ValueError:
                    idx=None
                self.current_light_model_index=idx
                if idx is not None:
                    self.light_name_list=self.models_light_names[idx]
                    self.light_list=self.models_light_all[idx]
                    self.light_node_list=self.models_light_node_all[idx]
                else:
                    self.light_name_list=[]
                    self.light_list=[]
                    self.light_node_list=[]
                
            if ("pos" in self.param_1) and self.param_1["pos"][0]:
                d=self.param_1['pos'][1]
                self.ModelTemp.setPos(d[0],d[1],d[2])
            else:
                d=self.ModelTemp.getPos()
                self.param_1['pos']=[True,[d[0],d[1],d[2]]]
            if ("scale" in self.param_1) and self.param_1["scale"][0]:
                d=self.param_1['scale'][1]
                self.ModelTemp.setScale(d[0],d[1],d[2])
            else:
                d=self.ModelTemp.getScale()
                self.param_1['scale']=[True,[d[0],d[1],d[2]]]
            if ("hpr" in self.param_1) and self.param_1["hpr"][0]:
                d=self.param_1['hpr'][1]
                self.ModelTemp.setHpr(d[0],d[1],d[2])
            else:
                d=self.ModelTemp.getHpr()
                self.param_1['hpr']=[True,[d[0],d[1],d[2]]]
            if ("color" in self.param_1) and self.param_1["color"][0]:
                d=self.param_1['color'][1]
                self.ModelTemp.setColorScale(d[0],d[1],d[2],d[3])
            else:
                d=self.ModelTemp.getColorScale()
                self.param_1['color']=[True,[d[0],d[1],d[2],d[3]]]

            #self.ModelTemp.clearLight()
            if fileload_flag==True:
                self.data_all.append(self.param_1.copy())
                self.models_all.append(self.ModelTemp)
                #self.models_all[-1].reparentTo(self.render)
                self.create_model_parent_vars()
                self.attach_to_parent_2(self.ModelTemp,self.model_parent_indices_all[-1])
                
            if indexload_flag==True:
                self.data_all[self.current_model_index]['show']=True
                self.models_all[self.current_model_index].show()
            
            postemp=self.ModelTemp.getPos()
            self.preserve_scale_on_reparent(self.gizmo,self.ModelTemp)                                      
            #self.gizmo.reparentTo(self.ModelTemp)
            #self.gizmo.setPos(postemp)
            #self.gizmo.setScale(10,10,10)
            if self.param_1['show']==True:
                self.ModelTemp.show()
            else:
                self.ModelTemp.hide()
        else:
            if fileload_flag==True:
                self.ModelTemp=''
                self.data_all.append(self.param_1.copy())
                self.models_all.append(self.ModelTemp)
                self.create_model_parent_vars()
            if indexload_flag==True:
                if type(self.models_all[self.current_model_index])==type(NodePath()):
                    self.data_all[self.current_model_index]['show']=False
                    self.models_all[self.current_model_index].hide()

    def preserve_scale_on_reparent(self, node, new_parent):
        # Step 1: Get the world-space scale (relative to render)
        world_scale = node.getScale(self.render)
        # Step 2: Reparent the node
        node.reparentTo(new_parent)
        # Step 3: Calculate the required local scale to maintain world-space scale
        parent_scale = new_parent.getScale(self.render)
        local_scale = (
            world_scale[0] / parent_scale[0],
            world_scale[1] / parent_scale[1],
            world_scale[2] / parent_scale[2]
        )
        # Step 4: Set the local scale to preserve the world-space scale
        node.setScale(local_scale)

    def find_point_lights(self, root_node):
        """
        Traverses the scene graph from the given root node and returns a list of
        (PointLight, NodePath) tuples for all point lights found.
        """
        point_lights = []
        for nodepath in root_node.findAllMatches("**"):
            node = nodepath.node()
            if isinstance(node, PointLight):
                point_lights.append((node, nodepath))
                #print(nodepath.ls())
        return point_lights   

    def get_point_light_properties_from_model(self,model,data):
        # load point lights from model
        #model.ls()
        point_lights = self.find_point_lights(model)
        self.param_2={}
        light_name_list=[]
        light_list=[]
        light_node_list=[]
        if len(point_lights)>0:
            logger.info("Found Point Lights: "+str(data['filename']))
            #self.param_2={}
            self.param_2['enable']=True
            self.param_2['show']=True
            self.param_2['uniquename']=data['uniquename']
            self.param_2['filename']=data['filename']
            self.param_2['details']=data['details']
            self.param_2['notes']=""
            self.param_2['overall_intensity']=1
            self.param_2['plights']=[]
            temp_dict={}
            
            for i, (light, nodepath) in enumerate(point_lights):
                light_list.append(light)
                light_node_list.append(nodepath)
                temp_dict['name']=light.getName()
                light_name_list.append(temp_dict['name'])
                temp_dict['notes']=""
                temp_dict['intensity']=1
                temp1=nodepath.getPos(self.render)
                temp_dict['pos']=[False,[temp1[0],temp1[1],temp1[2]]]
                temp1=light.getColor()
                temp_dict['color']=[True,[temp1[0],temp1[1],temp1[2],temp1[3]]]
                temp1=light.getAttenuation()
                temp_dict['attenuation']=[True,[temp1[0],temp1[1],temp1[2]]]
                #print(f"{i + 1}. Name: {light.getName()}, Position: {nodepath.getPos(self.render)}")
                #print(nodepath.getHpr())
                self.param_2['plights'].append(temp_dict.copy())
        #print('light_name_list',light_name_list)
        return (self.param_2,light_name_list,light_list,light_node_list)
        
    def update_model_parent(self, textEntered,index):
        now = datetime.datetime.now()
        try:
            if textEntered=='render':
                self.models_all[index].reparentTo(self.render)
                self.Tentry_MIndices[index].enterText(str(0))
                self.data_all[index]['parent'][1]='render'
                self.model_parent_names_all[index]='render'
                self.model_parent_indices_all[index]=0
                self.display_last_status('model reparented.')
            elif textEntered=='none':
                self.models_all[index].detachNode()
                self.Tentry_MIndices[index].enterText(str(-1))
                self.data_all[index]['parent'][1]='none'
                self.model_parent_names_all[index]='none'
                self.model_parent_indices_all[index]=-1
                self.display_last_status('model detached.')
            elif textEntered in self.models_names_all:
                idx=self.models_names_all.index(textEntered)
                self.models_all[index].reparentTo(self.models_all[idx])
                self.Tentry_MIndices[index].enterText(str(idx+1))
                self.data_all[index]['parent'][1]=self.models_names_all[idx]
                self.model_parent_names_all[index]=self.models_names_all[idx]
                self.model_parent_indices_all[index]=idx+1
                self.display_last_status('model reparented.')
            else:
                print('model name not present.')
                self.display_last_status('model name not present.')
        except Exception as e:
            logger.error('model is not reparented. there is an error occurs:')
            logger.error(e)

    def update_model_parent_2(self,textEntered,index):
        now = datetime.datetime.now()
        try:
            idx=int(textEntered)
            self.Tentry_MIndices[index].enterText(str(idx))
        except:
            logger.error('entry in parenting gui is not a number')
            return

        try:
            if idx==-1:
                self.models_all[index].detachNode()
                self.Tentry_MNames[index].enterText('none')
                self.data_all[index]['parent'][1]='none'
                self.model_parent_names_all[index]='none'
                self.model_parent_indices_all[index]=-1
                self.display_last_status('model detached.')
            elif idx==0:
                self.models_all[index].reparentTo(self.render)
                self.Tentry_MNames[index].enterText('render')
                self.data_all[index]['parent'][1]='render'
                self.model_parent_names_all[index]='render'
                self.model_parent_indices_all[index]=0
                self.display_last_status('model reparented.')
            elif ((idx>0) & (idx<len(self.models_names_all)+1)):
                self.models_all[index].reparentTo(self.models_all[idx-1])
                self.Tentry_MNames[index].enterText(self.models_names_all[idx-1])
                self.data_all[index]['parent'][1]=self.models_names_all[idx-1]
                self.model_parent_names_all[index]=self.models_names_all[idx-1]
                self.model_parent_indices_all[index]=idx
                self.display_last_status('model reparented.')
            else:
                print('index is not in range.')
                self.display_last_status('index is not in range.')
        except:
            print('model is not reparented. there is an error occurs.')

    def attach_to_parent_2(self,model,idx):
        #now = datetime.datetime.now()
        if idx==0:
            model.reparentTo(self.render)
        elif idx==-1:
            model.detachNode()
        else:
            model.reparentTo(self.models_all[idx-1])
                
    def take_screenshot(self):
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        filename = Filename(f"screenshot_{timestamp}.jpg")
        base.win.saveScreenshot(filename)
        print("Screenshot saved")
        

Scene_1=SceneMakerMain()
Scene_1.run()


