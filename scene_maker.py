import panda3d
from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor
from direct.task.Task import Task
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from direct.showbase.DirectObject import DirectObject
from direct.gui.DirectGui import *
from direct.filter.FilterManager import FilterManager

import random
import sys
import os
import shutil
import math
from direct.filter.CommonFilters import CommonFilters

from panda3d.core import *
import panda3d.core as p3d
import tkinter
from tkinter.filedialog import askopenfilename
from tkinter import messagebox
import tkinter as tk

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
#loadPrcFileData("", "win-size 1920 1080")
#loadPrcFileData("", "fullscreen t")
#loadPrcFileData("", "show-scene-graph-analyzer-meter 1")
loadPrcFileData("", "icon-filename icons/title_icon.ico")
loadPrcFileData("", "window-title Scene Maker")

class SceneMakerMain(ShowBase):

    def __init__(self):
        ShowBase.__init__(self)
        self.props = WindowProperties()
        self.disable_mouse()
        self.FilterManager_1 = FilterManager(base.win, base.cam)
        self.Filters=CommonFilters(base.win, base.cam)
        self.pstats = True
        
        #---adjustable parameters---
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.scene_data_filename=os.path.join(base_path,'scene_params1.json')
        self.scene_data_backup_filename=os.path.join(base_path,'scene_params1_tempbackup.json')
        self.scene_light_data_filename=os.path.join(base_path,'scene_light_params1.json')
        self.scene_light_data_backup_filename=os.path.join(base_path,'scene_light_params1_tempbackup.json')
        self.scene_global_params_filename=os.path.join(base_path,'scene_global_params1.json')

        self.load_lights_from_json=True #set this False if you dont want to load point lights from json file

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
        self.temp_ststus=''
        self.global_params={}
        self.load_global_params()
        
        #---theme colors---
        self.dark_theme = self.global_params['dark_theme']
        if self.dark_theme==True:
            self.FRAME_COLOR_1=(0, 0, 0, 0.4) #black transparent
            self.FRAME_COLOR_2=(0, 0, 0, 0.5) #black and slight less transparent
            self.TEXTFG_COLOR_1=(1,1,1,0.9) #white color
            self.TEXTFG_COLOR_2=(0.7,0.7,1,0.9) #pale blue color (to display info text)
            self.TEXTFG_COLOR_3=(1, 0.7, 0.7, 1) #pale red color (to display highlight text, i.e. filenames)
            self.TEXTFG_COLOR_4=(0.7, 1, 0.7, 0.9) #pale green color (to display help text)
            self.TEXTBG_COLOR_1=(0, 0, 0, 0.4) #black transparent for text background
        else:
            self.FRAME_COLOR_1=(1, 1, 1, 0.4) #white transparent
            self.FRAME_COLOR_2=(1, 1, 1, 0.5) #white and slight less transparent
            self.TEXTFG_COLOR_1=(0,0,0,0.9) #black color
            self.TEXTFG_COLOR_2=(0,0,0.6,0.9) #pale blue color (to display info text)
            self.TEXTFG_COLOR_3=(0.6, 0, 0, 1) #pale red color (to display highlight text, i.e. filenames)
            self.TEXTFG_COLOR_4=(0, 0.6, 0, 0.9) #pale green color (to display help text)
            self.TEXTBG_COLOR_1=(1, 1, 1, 0.4) #white transparent for text background

                
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
        taskMgr.add(self.general_tasks, "general_tasks")
        #self.sun_rotate()
        
        self.gizmo=self.create_gizmo(scale=10)
        
        self.crosshair = OnscreenImage(image='crosshair.png', pos=(0,0,0),scale=0.1)
        self.crosshair.setTransparency(TransparencyAttrib.MAlpha)
        self.crosshair.hide()
        
        self.textObject = OnscreenText(text='', pos=(-0.1, 0.95), scale=0.07,bg=(0,0,0,0.5),fg=(1,1,1,1))
        self.collide_mname=''
        self.collide_flag=False
        
        base.accept('tab', base.bufferViewer.toggleEnable)
        

        self.param_2={}               
        self.current_property=1
        self.property_names=['position','scale','rotation','color']
        self.tonemap_option_items=['Linear','Reinhard Simple ','Reinhard Photographic','ACES']
        self.pos_increment=0.001
        self.scale_increment=0.01
        self.temp_count=1
        self.fog=""
        self.create_top_level_main_gui()
        
        self.entry_temp=""
        self.identifier_temp=""
        self.floating_slider= DirectSlider(pos=(-1, 0, -0.1),scale=1,value=50,range=(0, 100),command=self.on_slider_change,frameSize=(0, 2, -0.05, 0.05),frameColor=(0.2, 0.2, 0.7, 1.0),thumb_frameSize=(-0.04, 0.04, -0.08, 0.08))
        self.floating_slider.hide()
        
        #---apply global params---
        self.apply_global_params_1()
        self.setupLights()
        self.apply_global_params_2()
        #self.set_skybox()
        self.apply_global_params_3()
        self.apply_global_params_4()
        self.display_last_status(self.temp_ststus)
        
        
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
        
        
    
    def create_shortcut_icons_top(self):
        self.ScrolledFrame_a0=DirectScrolledFrame(
            canvasSize=(-2, 2, -2, 2),  # left, right, bottom, top
            frameSize=(-2, 2, -2, 2),
            pos=(0,0,0),
            frameColor=(0, 0, 0, 0)
        )
        canvas_a1=self.ScrolledFrame_a0.getCanvas()
        
        self.checkbutton_a1 = DirectCheckButton(parent=canvas_a1,pos=(-0.72, 1,0.97),command=self.icons_command,extraArgs=['1'],scale=0.03,indicatorValue=0,image="icons/1.jpg",relief=None,indicator_image=None,indicator_text_scale=0,indicator_relief=None,text="",boxPlacement="left",boxImage=None)
        self.checkbutton_a2 = DirectCheckButton(parent=canvas_a1,pos=(-0.65, 1,0.97),command=self.icons_command,extraArgs=['2'],scale=0.03,indicatorValue=0,image="icons/2.jpg",relief=None,indicator_image=None,indicator_text_scale=0,indicator_relief=None,text="",boxPlacement="left",boxImage=None)
        self.checkbutton_a3 = DirectCheckButton(parent=canvas_a1,pos=(-0.58, 1,0.97),command=self.icons_command,extraArgs=['3'],scale=0.03,indicatorValue=0,image="icons/3.jpg",relief=None,indicator_image=None,indicator_text_scale=0,indicator_relief=None,text="",boxPlacement="left",boxImage=None)
        self.checkbutton_a4 = DirectCheckButton(parent=canvas_a1,pos=(-0.51, 1,0.97),command=self.icons_command,extraArgs=['4'],scale=0.03,indicatorValue=0,image="icons/4.jpg",relief=None,indicator_image=None,indicator_text_scale=0,indicator_relief=None,text="",boxPlacement="left",boxImage=None)
        self.checkbutton_a5 = DirectCheckButton(parent=canvas_a1,pos=(-0.44, 1,0.97),command=self.icons_command,extraArgs=['5'],scale=0.03,indicatorValue=0,image="icons/5.jpg",relief=None,indicator_image=None,indicator_text_scale=0,indicator_relief=None,text="",boxPlacement="left",boxImage=None)
        self.checkbutton_a6 = DirectCheckButton(parent=canvas_a1,pos=(-0.37, 1,0.97),command=self.icons_command,extraArgs=['6'],scale=0.03,indicatorValue=0,image="icons/6.jpg",relief=None,indicator_image=None,indicator_text_scale=0,indicator_relief=None,text="",boxPlacement="left",boxImage=None)
        self.checkbutton_a7 = DirectCheckButton(parent=canvas_a1,pos=(-0.30, 1,0.97),command=self.icons_command,extraArgs=['7'],scale=0.03,indicatorValue=0,image="icons/7.jpg",relief=None,indicator_image=None,indicator_text_scale=0,indicator_relief=None,text="",boxPlacement="left",boxImage=None)
        self.checkbutton_a8 = DirectCheckButton(parent=canvas_a1,pos=(-0.23, 1,0.97),command=self.icons_command,extraArgs=['8'],scale=0.03,indicatorValue=0,image="icons/8.jpg",relief=None,indicator_image=None,indicator_text_scale=0,indicator_relief=None,text="",boxPlacement="left",boxImage=None)
        self.checkbutton_a9 = DirectCheckButton(parent=canvas_a1,pos=(-0.16, 1,0.97),command=self.icons_command,extraArgs=['9'],scale=0.03,indicatorValue=0,image="icons/9.jpg",relief=None,indicator_image=None,indicator_text_scale=0,indicator_relief=None,text="",boxPlacement="left",boxImage=None)
        self.checkbutton_a10 = DirectCheckButton(parent=canvas_a1,pos=(-0.09, 1,0.97),command=self.icons_command,extraArgs=['10'],scale=0.03,indicatorValue=0,image="icons/10.jpg",relief=None,indicator_image=None,indicator_text_scale=0,indicator_relief=None,text="",boxPlacement="left",boxImage=None)

    def icons_command(self,InputValue,identifier):
        try:
            if identifier=="1":
                if InputValue:
                    self.show_properties_gui()
                    self.checkbutton_a1['image_color'] = (0.57, 0.88, 0.35, 1)
                else:
                    self.hide_properties_gui()
                    self.checkbutton_a1['image_color'] = (1, 1, 1, 1)
            if identifier=="2":
                if InputValue:
                    self.show_properties_gui_2()
                    self.checkbutton_a2['image_color'] = (0.57, 0.88, 0.35, 1)
                else:
                    self.hide_properties_gui_2()
                    self.checkbutton_a2['image_color'] = (1, 1, 1, 1)
            if identifier=="3":
                if InputValue:
                    self.ScrolledFrame_d2.show()
                    self.checkbutton_a3['image_color'] = (0.57, 0.88, 0.35, 1)
                else:
                    self.ScrolledFrame_d2.hide()
                    self.checkbutton_a3['image_color'] = (1, 1, 1, 1)
            if identifier=="4":
                if InputValue:
                    self.ScrolledFrame_d1.show()
                    self.checkbutton_a4['image_color'] = (0.57, 0.88, 0.35, 1)
                else:
                    self.ScrolledFrame_d1.hide()
                    self.checkbutton_a4['image_color'] = (1, 1, 1, 1)
            if identifier=="5":
                if InputValue:
                    self.ScrolledFrame_e1.show()
                    self.checkbutton_a5['image_color'] = (0.57, 0.88, 0.35, 1)
                else:
                    self.ScrolledFrame_e1.hide()
                    self.checkbutton_a5['image_color'] = (1, 1, 1, 1)
            if identifier=="6":
                if InputValue:
                    self.ScrolledFrame_f1.show()
                    self.checkbutton_a6['image_color'] = (0.57, 0.88, 0.35, 1)
                else:
                    self.ScrolledFrame_f1.hide()
                    self.checkbutton_a6['image_color'] = (1, 1, 1, 1)
            if identifier=="7":
                if InputValue:
                    self.ScrolledFrame_g1.show()
                    self.checkbutton_a7['image_color'] = (0.57, 0.88, 0.35, 1)
                else:
                    self.ScrolledFrame_g1.hide()
                    self.checkbutton_a7['image_color'] = (1, 1, 1, 1)
            if identifier=="8":
                if InputValue:
                    self.ScrolledFrame_h1.show()
                    self.checkbutton_a8['image_color'] = (0.57, 0.88, 0.35, 1)
                else:
                    self.ScrolledFrame_h1.hide()
                    self.checkbutton_a8['image_color'] = (1, 1, 1, 1)
            if identifier=="9":
                if InputValue:
                    self.ScrolledFrame_i1.show()
                    self.checkbutton_a9['image_color'] = (0.57, 0.88, 0.35, 1)
                else:
                    self.ScrolledFrame_i1.hide()
                    self.checkbutton_a9['image_color'] = (1, 1, 1, 1)
            if identifier=="10":
                if InputValue:
                    self.ScrolledFrame_j1.show()
                    self.checkbutton_a10['image_color'] = (0.57, 0.88, 0.35, 1)
                else:
                    self.ScrolledFrame_j1.hide()
                    self.checkbutton_a10['image_color'] = (1, 1, 1, 1)
        except Exception as e:
            logger.error('error in shortcut icon click:')
            logger.error(e)
            self.display_last_status('error in shortcut icon click.')
            
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
        self.global_params['fog_R']=0.5
        self.global_params['fog_G']=0.5
        self.global_params['fog_B']=0.5
        self.global_params['fog_start']=15
        self.global_params['fog_end']=150
        self.global_params['fog_density']=0.001
        
    def apply_global_params_1(self): #settings params
        self.mouse_sensitivity=self.global_params['mouse_sensitivity']
        self.dentry_d2.enterText(str(self.mouse_sensitivity))
        self.move_speed=self.global_params['move_speed']
        self.dentry_d4.enterText(str(self.move_speed))
        self.CheckButton_gs1['indicatorValue']=self.global_params['crosshair']
        self.CheckButton_gs2['indicatorValue']=self.global_params['gizmo']
        if self.global_params['crosshair']==True:
            self.crosshair.show()
        else:
            self.crosshair.hide()
        if self.global_params['gizmo']==True:
            self.gizmo.show()
        else:
            self.gizmo.hide()
        if self.global_params['dark_theme']==True:
            self.CheckButton_gs3['indicatorValue']=True
        else:
            self.CheckButton_gs3['indicatorValue']=False
            
    
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
        self.optionmenu_i18.set(int(self.global_params['skybox_tonemapping_method'])-1)
        self.skybox_commands(self.global_params['skybox_exposure'],'exposure')
        self.skybox_commands(self.global_params['skybox_gamma'],'gamma')
        
        self.dlabel_i4.setText(self.global_params['skybox_image'])
            
    def apply_global_params_4(self): #fog params
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
                self.create_global_params()
                self.save_global_params()
                self.temp_ststus='global params json created (and saved)'
                logger.info('global params json created (and saved)')
            else:
                with open(self.scene_global_params_filename) as json_data:
                    self.global_params = json.load(json_data)
                self.temp_ststus='global params json loaded'
                logger.info('global params json loaded')
        except:
            self.temp_ststus='error while loading global params json file.'
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
        
    def create_top_level_main_gui(self):
        self.menu_1 = DirectOptionMenu(text="switch_property", scale=0.07, initialitem=0,highlightColor=(0.65, 0.65, 0.65, 1),command=self.menudef_1, textMayChange=1,items=self.property_names,pos=(-1.3, 1,0.95),frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1)
        
        self.menu_2 = DirectButton(text=("switch_models                                                 ."),scale=.07,command=self.show_ScrolledFrame_menu_2,pos=(0.2, 1,0.95),frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,text_align=TextNode.ALeft)
        self.ScrolledFrame_menu_2=DirectScrolledFrame(
            frameSize=(-1, 1, -0.9, 0.8),  # left, right, bottom, top
            canvasSize=(-2, 2, -2, 2),
            pos=(0.1,0,0),
            frameColor=(0.3, 0.3, 0.3, 0.5)
        )
        self.add_models_to_menuoption()
        self.ScrolledFrame_menu_2.hide()
        
        self.MenuButton_1 = DirectButton(text = "Menu",scale=.06,command=self.menubuttonDef_1,pos=(-0.85, 1,0.95))
        self.dbutton_1 = DirectButton(text=("Save"),scale=.06, pos=(0.1, 1,0.95),command=self.ButtonDef_1)
        self.dlabel_status=DirectLabel(text='Last Status: ',pos=(-1.3,1,0.85),scale=0.06,text_align=TextNode.ALeft,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dlabel_status2=DirectLabel(text='',pos=(-0.92,1,0.85),scale=0.06,text_align=TextNode.ALeft,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.create_shortcut_icons_top()
        self.create_properties_gui()
        self.create_properties_gui_2()
        self.hide_properties_gui_2()
        self.hide_properties_gui()
        self.create_daylight_gui()
        self.ScrolledFrame_d1.hide()
        self.create_general_settings_gui()
        self.ScrolledFrame_d2.hide()
        self.create_model_lights_gui()
        self.ScrolledFrame_e1.hide()
        self.create_model_nodepaths_viewer_gui()
        self.ScrolledFrame_f1.hide()
        self.create_model_animation_viewer_gui()
        self.ScrolledFrame_g1.hide()
        self.create_model_parent_editor_gui()
        self.ScrolledFrame_h1.hide()
        self.create_skybox_settings_gui()
        self.ScrolledFrame_i1.hide()
        self.create_heightmap_loader_gui()
        self.ScrolledFrame_j1.hide()
        self.create_fog_settings_gui()
        self.ScrolledFrame_k1.hide()
        
        self.create_dropdown_main_menu()
        self.menu_dropdown_1.hide()
        
        #self.MenuButton_1['state'] = DGG.NORMAL
        #self.MenuButton_1.bind(DGG.WITHOUT, self.menu_hover_command, [False])
        #self.MenuButton_1.bind(DGG.WITHIN, self.menu_hover_command, [True])
        #---display camera pos at bottom---
        self.bottom_cam_label=DirectLabel(text='CamPos: ',pos=(-1,1,-0.9),scale=0.05,text_align=TextNode.ACenter,text_fg=self.TEXTFG_COLOR_1,text_bg=(0,0,0,0.2),frameColor=(0, 0, 0, 0.1))
    
    def show_ScrolledFrame_menu_2(self):
        if self.ScrolledFrame_menu_2.isHidden():
            self.ScrolledFrame_menu_2.show()
        else:
            self.ScrolledFrame_menu_2.hide()
    
    def show_top_level_main_gui(self):
        self.menu_1.show()
        self.menu_2.show()
        self.MenuButton_1.show()
        self.dbutton_1.show()
        self.dlabel_status.show()
        self.dlabel_status2.show()
        self.bottom_cam_label.show()  
        self.ScrolledFrame_a0.show()        
        
    def hide_top_level_main_gui(self):
        self.menu_1.hide()
        self.menu_2.hide()
        self.MenuButton_1.hide()
        self.dbutton_1.hide()
        self.dlabel_status.hide()
        self.dlabel_status2.hide()                                                                                         
        self.bottom_cam_label.hide()
        self.ScrolledFrame_a0.hide() 
        panda3d.core.load_prc_file_data('', 'show-frame-rate-meter false')                                                                          
        
    def menu_hover_command(self,hover, frame):
        if hover:
            self.menu_dropdown_1.show()
        else:
            taskMgr.doMethodLater(2.0, self.menu_dropdown_1.hide, 'hidemainmenu', extraArgs=[])

    def create_dropdown_main_menu(self):
        self.menu_dropdown_1=DirectScrolledFrame(
            canvasSize=(0, 1, -1.5, 0),  # left, right, bottom, top
            frameSize=(0, 1, -1.5, 0),
            pos=(-1,0,0.9),
            #pos=(-0.35, 1,0.95)
            frameColor=self.FRAME_COLOR_1
        )
        
        self.CheckButton_1 = DirectCheckButton(
            parent=self.menu_dropdown_1.getCanvas(),
            text = "properties " ,
            text_align=TextNode.ALeft,
            scale=.06,
            command=self.cbuttondef_1,
            pos=(0.1,1,-0.1),
            frameColor=self.FRAME_COLOR_1,
            text_fg=self.TEXTFG_COLOR_1,
            indicatorValue=0
            )
        self.CheckButton_2 = DirectCheckButton(
            parent=self.menu_dropdown_1.getCanvas(),
            text = "all properties" ,
            text_align=TextNode.ALeft,
            scale=.06,
            command=self.cbuttondef_2,
            pos=(0.1, 1,-0.2),
            frameColor=self.FRAME_COLOR_1,
            text_fg=self.TEXTFG_COLOR_1,
            indicatorValue=0
            )
        self.CheckButton_3 = DirectCheckButton(
            parent=self.menu_dropdown_1.getCanvas(),
            text = "General Settings" ,
            text_align=TextNode.ALeft,
            scale=.06,
            command=self.cbuttondef_b3,
            pos=(0.1, 1,-0.3),
            frameColor=self.FRAME_COLOR_1,
            text_fg=self.TEXTFG_COLOR_1,
            indicatorValue=0
            )
        self.CheckButton_4 = DirectCheckButton(
            parent=self.menu_dropdown_1.getCanvas(),
            text = "Light Settings" ,
            text_align=TextNode.ALeft,
            scale=.06,
            command=self.cbuttondef_b4,
            pos=(0.1, 1,-0.4),
            frameColor=self.FRAME_COLOR_1,
            text_fg=self.TEXTFG_COLOR_1,
            indicatorValue=0
            )
        self.CheckButton_5 = DirectCheckButton(
            parent=self.menu_dropdown_1.getCanvas(),
            text = "Model Light Settings" ,
            text_align=TextNode.ALeft,
            scale=.06,
            command=self.cbuttondef_b5,
            pos=(0.1, 1,-0.5),
            frameColor=self.FRAME_COLOR_1,
            text_fg=self.TEXTFG_COLOR_1,
            indicatorValue=0
            )
        self.CheckButton_6 = DirectCheckButton(
            parent=self.menu_dropdown_1.getCanvas(),
            text = "Model NodePaths Viewer" ,
            text_align=TextNode.ALeft,
            scale=.06,
            command=self.cbuttondef_b6,
            pos=(0.1, 1,-0.6),
            frameColor=self.FRAME_COLOR_1,
            text_fg=self.TEXTFG_COLOR_1,
            indicatorValue=0
            )
        self.CheckButton_7 = DirectCheckButton(
            parent=self.menu_dropdown_1.getCanvas(),
            text = "Model Animation Viewer" ,
            text_align=TextNode.ALeft,
            scale=.06,
            command=self.cbuttondef_b7,
            pos=(0.1, 1,-0.7),
            frameColor=self.FRAME_COLOR_1,
            text_fg=self.TEXTFG_COLOR_1,
            indicatorValue=0
            )
        self.CheckButton_8 = DirectCheckButton(
            parent=self.menu_dropdown_1.getCanvas(),
            text = "Model Parent Editor" ,
            text_align=TextNode.ALeft,
            scale=.06,
            command=self.cbuttondef_b8,
            pos=(0.1, 1,-0.8),
            frameColor=self.FRAME_COLOR_1,
            text_fg=self.TEXTFG_COLOR_1,
            indicatorValue=0
            )
        self.CheckButton_9 = DirectCheckButton(
            parent=self.menu_dropdown_1.getCanvas(),
            text = "Skybox Settings" ,
            text_align=TextNode.ALeft,
            scale=.06,
            command=self.cbuttondef_b9,
            pos=(0.1, 1,-0.9),
            frameColor=self.FRAME_COLOR_1,
            text_fg=self.TEXTFG_COLOR_1,
            indicatorValue=0
            )
        self.CheckButton_10 = DirectCheckButton(
            parent=self.menu_dropdown_1.getCanvas(),
            text = "HeightMap Loader" ,
            text_align=TextNode.ALeft,
            scale=.06,
            command=self.cbuttondef_b10,
            pos=(0.1, 1,-1.0),
            frameColor=self.FRAME_COLOR_1,
            text_fg=self.TEXTFG_COLOR_1,
            indicatorValue=0
            )
        self.CheckButton_11 = DirectCheckButton(
            parent=self.menu_dropdown_1.getCanvas(),
            text = "Fog Settings" ,
            text_align=TextNode.ALeft,
            scale=.06,
            command=self.cbuttondef_b11,
            pos=(0.1, 1,-1.1),
            frameColor=self.FRAME_COLOR_1,
            text_fg=self.TEXTFG_COLOR_1,
            indicatorValue=0
            )
                                
    def create_properties_gui(self):
        self.dlabel_1=DirectLabel(text='X: ',pos=(-1.3,1,0.75),scale=0.06,text_align=TextNode.ACenter,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dlabel_2=DirectLabel(text='Y: ',pos=(-1.3,1,0.65),scale=0.06,text_align=TextNode.ACenter,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dlabel_3=DirectLabel(text='Z: ',pos=(-1.3,1,0.55),scale=0.06,text_align=TextNode.ACenter,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        
        self.dslider_1 = DirectSlider(range=(-1000,1000), value=0, pageSize=1, command=self.GetSliderValue_1,pos=(-1.2, 1,0.83),frameSize=(0,0.9,-0.1,0),frameColor=self.FRAME_COLOR_2,thumb_frameSize=(0,0.05,0.04,-0.04))
        self.dentry_1 = DirectEntry(text = "", scale=0.06,width=10,pos=(-0.2, 1,0.75), command=self.SetEntryText_1,initialText="0", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dentry_1_value=0

        self.dslider_2 = DirectSlider(range=(-1000,1000), value=0, pageSize=1, command=self.GetSliderValue_2,pos=(-1.2, 1,0.73),frameSize=(0,0.9,-0.1,0),frameColor=self.FRAME_COLOR_2,thumb_frameSize=(0,0.05,0.04,-0.04))
        self.dentry_2 = DirectEntry(text = "", scale=0.06,width=10,pos=(-0.2, 1,0.65), command=self.SetEntryText_2,initialText="0", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dentry_2_value=0

        self.dslider_3 = DirectSlider(range=(-1000,1000), value=0, pageSize=1, command=self.GetSliderValue_3,pos=(-1.2, 1,0.63),frameSize=(0,0.9,-0.1,0),frameColor=self.FRAME_COLOR_2,thumb_frameSize=(0,0.05,0.04,-0.04))
        self.dentry_3 = DirectEntry(text = "", scale=0.06,width=10,pos=(-0.2, 1,0.55), command=self.SetEntryText_3,initialText="0", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dentry_3_value=0
        
    def show_properties_gui(self):
        self.dlabel_1.show()
        self.dlabel_2.show()
        self.dlabel_3.show()
        self.dslider_1.show()
        self.dentry_1.show()
        self.dslider_2.show()
        self.dentry_2.show()
        self.dslider_3.show()
        self.dentry_3.show()
        
    def hide_properties_gui(self):
        self.dlabel_1.hide()
        self.dlabel_2.hide()
        self.dlabel_3.hide()
        self.dslider_1.hide()
        self.dentry_1.hide()
        self.dslider_2.hide()
        self.dentry_2.hide()
        self.dslider_3.hide()
        self.dentry_3.hide()
        
    def create_properties_gui_2(self):
        self.CheckButton_b1 = DirectCheckButton(text = "enable model" ,scale=.06,command=self.cbuttondef_3,pos=(-1.3, 1,0.4),frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_align=TextNode.ALeft)
        self.CheckButton_b2 = DirectCheckButton(text = "show model" ,scale=.06,command=self.cbuttondef_4,pos=(-1.3, 1,0.3),frameColor=self.FRAME_COLOR_1, text_fg=self.TEXTFG_COLOR_1,text_align=TextNode.ALeft)
        self.dlabel_b3=DirectLabel(text='uniquename: ',pos=(-1.3,1,0.2),scale=0.06,text_align=TextNode.ALeft,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_b4 = DirectEntry(text = "", scale=0.06,width=20,pos=(-0.9, 1,0.2), command=self.SetEntryText_4,initialText="", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_b5=DirectLabel(text='filename: ',pos=(-1.3,1,0.1),scale=0.06,text_align=TextNode.ALeft,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        
        self.dlabel_b6=DirectLabel(text='details: ',pos=(-1.3,1,0),scale=0.06,text_align=TextNode.ALeft,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_b7 = DirectEntry(text = "", scale=0.06,width=30,pos=(-0.9, 1,0), command=self.SetEntryText_5,initialText="", numLines = 4, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_b8=DirectLabel(text='notes: ',pos=(-1.3,1,-0.3),scale=0.06,text_align=TextNode.ALeft,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_b9 = DirectEntry(text = "", scale=0.06,width=30,pos=(-0.9, 1,-0.3), command=self.SetEntryText_6,initialText="", numLines = 4, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.CheckButton_b10 = DirectCheckButton(text = "pickable" ,scale=.06,command=self.cbuttondef_5,pos=(-1.3, 1,-0.6),frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_align=TextNode.ALeft)
        self.dlabel_b9_2=DirectLabel(text='description: ',pos=(-1.3,1,-0.7),scale=0.06,text_align=TextNode.ALeft,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_b11 = DirectEntry(text = "", scale=0.06,width=30,pos=(-0.9, 1,-0.7), command=self.SetEntryText_7,initialText="", numLines = 4, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,text_align=TextNode.ALeft,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)

    def show_properties_gui_2(self):
        self.CheckButton_b1.show()
        self.CheckButton_b2.show()
        self.dlabel_b3.show()
        self.dentry_b4.show()
        self.dlabel_b5.show()
        self.dlabel_b6.show()
        self.dentry_b7.show()
        self.dlabel_b8.show()
        self.dentry_b9.show()
        self.dlabel_b9_2.show()
        self.CheckButton_b10.show()
        self.dentry_b11.show()
        
    def hide_properties_gui_2(self):
        self.CheckButton_b1.hide()
        self.CheckButton_b2.hide()
        self.dlabel_b3.hide()
        self.dentry_b4.hide()
        self.dlabel_b5.hide()
        self.dlabel_b6.hide()
        self.dentry_b7.hide()
        self.dlabel_b8.hide()
        self.dentry_b9.hide()
        self.dlabel_b9_2.hide()
        self.CheckButton_b10.hide()
        self.dentry_b11.hide()

    def daylight_commands(self,textEntered,identifier):
        try:
            # textEntered value may be integer if it called from other than gui
            textEntered_num=float(textEntered)
            textEntered_str=str(textEntered)
            if identifier=='ambientlight_intensity':
                self.dentry_c2.enterText(textEntered_str)
                self.global_params['ambientlight_intensity']=textEntered_num
                #self.dentry_c6.enterText(str(self.ambientLight_Intensity))
            elif identifier=='ambientlight_R':
                self.dentry_c6.enterText(textEntered_str)
                self.global_params['ambientlight_R']=textEntered_num
            elif identifier=='ambientlight_G':
                self.dentry_c7.enterText(textEntered_str)
                self.global_params['ambientlight_G']=textEntered_num
            elif identifier=='ambientlight_B':
                self.dentry_c8.enterText(textEntered_str)
                self.global_params['ambientlight_B']=textEntered_num
            elif identifier=='DL_intensity':
                self.dentry_c10.enterText(textEntered_str)
                self.global_params['directionallight_intensity']=textEntered_num
            elif identifier=='DL_R':
                self.dentry_c14.enterText(textEntered_str)
                self.global_params['directionallight_R']=textEntered_num
            elif identifier=='DL_G':
                self.dentry_c15.enterText(textEntered_str)
                self.global_params['directionallight_G']=textEntered_num
            elif identifier=='DL_B':
                self.dentry_c16.enterText(textEntered_str)
                self.global_params['directionallight_B']=textEntered_num
            elif identifier=='DL_H':
                self.dentry_c20.enterText(textEntered_str)
                self.global_params['directionallight_H']=textEntered_num
            elif identifier=='DL_P':
                self.dentry_c21.enterText(textEntered_str)
                self.global_params['directionallight_P']=textEntered_num
            elif identifier=='DL_RO':
                self.dentry_c22.enterText(textEntered_str)
                self.global_params['directionallight_RO']=textEntered_num
            elif identifier=='DL_X':
                self.dentry_c24.enterText(textEntered_str)
                self.global_params['directionallight_X']=textEntered_num
            elif identifier=='DL_Y':
                self.dentry_c26.enterText(textEntered_str)
                self.global_params['directionallight_Y']=textEntered_num
            elif identifier=='DL_Z':
                self.dentry_c28.enterText(textEntered_str)
                self.global_params['directionallight_Z']=textEntered_num

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
            self.display_last_status('error in daylight gui entry.')

    def create_daylight_gui(self):
        self.ScrolledFrame_d1=DirectScrolledFrame(
            canvasSize=(-2, 2, -2, 2),  # left, right, bottom, top
            frameSize=(-2, 2, -2, 2),
            pos=(0.1,0,0),
            #pos=(-0.35, 1,0.95)
            frameColor=(0.3, 0.3, 0.3, 0)
        )
        canvas_1=self.ScrolledFrame_d1.getCanvas()
        self.dlabel_c1 = DirectLabel(parent=canvas_1,text='Ambient light: intensity',pos=(-0.8,1,0.75),scale=0.06,text_align=TextNode.ACenter,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_c2 = DirectEntry(parent=canvas_1,text = "", scale=0.06,width=10,pos=(-0.3, 1,0.75), command=self.daylight_commands,extraArgs=['ambientlight_intensity'],initialText="0.1", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        
        self.dlabel_c3=DirectLabel(parent=canvas_1,text='R (0 to 1): ',pos=(-0.7,1,0.65),scale=0.06,text_align=TextNode.ACenter,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dlabel_c4=DirectLabel(parent=canvas_1,text='G (0 to 1): ',pos=(-0.7,1,0.55),scale=0.06,text_align=TextNode.ACenter,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dlabel_c5=DirectLabel(parent=canvas_1,text='B (0 to 1): ',pos=(-0.7,1,0.45),scale=0.06,text_align=TextNode.ACenter,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        
        self.dentry_c6 = DirectEntry(parent=canvas_1,text = "", scale=0.06,width=10,pos=(-0.35, 1,0.65), command=self.daylight_commands,extraArgs=['ambientlight_R'],initialText="0.1", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dentry_c7 = DirectEntry(parent=canvas_1,text = "", scale=0.06,width=10,pos=(-0.35, 1,0.55), command=self.daylight_commands,extraArgs=['ambientlight_G'],initialText="0.1", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dentry_c8 = DirectEntry(parent=canvas_1,text = "", scale=0.06,width=10,pos=(-0.35, 1,0.45), command=self.daylight_commands,extraArgs=['ambientlight_B'],initialText="0.1", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)

        self.dlabel_c9 = DirectLabel(parent=canvas_1,text='Directional light(sun): intensity',pos=(-0.8,1,0.35),scale=0.06,text_align=TextNode.ACenter,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_c10 = DirectEntry(parent=canvas_1,text = "", scale=0.06,width=10,pos=(-0.3, 1,0.35), command=self.daylight_commands,extraArgs=['DL_intensity'],initialText="1", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        
        self.dlabel_c11=DirectLabel(parent=canvas_1,text='R (0 to 1): ',pos=(-0.7,1,0.25),scale=0.06,text_align=TextNode.ACenter,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dlabel_c12=DirectLabel(parent=canvas_1,text='G (0 to 1): ',pos=(-0.7,1,0.15),scale=0.06,text_align=TextNode.ACenter,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dlabel_c13=DirectLabel(parent=canvas_1,text='B (0 to 1): ',pos=(-0.7,1,0.05),scale=0.06,text_align=TextNode.ACenter,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        
        self.dentry_c14 = DirectEntry(parent=canvas_1,text = "", scale=0.06,width=10,pos=(-0.35, 1,0.25), command=self.daylight_commands,extraArgs=['DL_R'],initialText="1", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dentry_c15 = DirectEntry(parent=canvas_1,text = "", scale=0.06,width=10,pos=(-0.35, 1,0.15), command=self.daylight_commands,extraArgs=['DL_G'],initialText="1", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dentry_c16 = DirectEntry(parent=canvas_1,text = "", scale=0.06,width=10,pos=(-0.35, 1,0.05), command=self.daylight_commands,extraArgs=['DL_B'],initialText="1", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)

        self.dlabel_c17=DirectLabel(parent=canvas_1,text='H (0 to 360): ',pos=(-0.7,1,-0.05),scale=0.06,text_align=TextNode.ACenter,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dlabel_c18=DirectLabel(parent=canvas_1,text='P (0 to 360): ',pos=(-0.7,1,-0.15),scale=0.06,text_align=TextNode.ACenter,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dlabel_c19=DirectLabel(parent=canvas_1,text='R (0 to 360): ',pos=(-0.7,1,-0.25),scale=0.06,text_align=TextNode.ACenter,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        
        self.dentry_c20 = DirectEntry(parent=canvas_1,text = "", scale=0.06,width=10,pos=(-0.35, 1,-0.05), command=self.daylight_commands,extraArgs=['DL_H'],initialText="0", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dentry_c21 = DirectEntry(parent=canvas_1,text = "", scale=0.06,width=10,pos=(-0.35, 1,-0.15), command=self.daylight_commands,extraArgs=['DL_P'],initialText="0", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dentry_c22 = DirectEntry(parent=canvas_1,text = "", scale=0.06,width=10,pos=(-0.35, 1,-0.25), command=self.daylight_commands,extraArgs=['DL_RO'],initialText="0", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)

        self.dlabel_c23=DirectLabel(parent=canvas_1,text='X: ',pos=(-1.3,1,-0.35),scale=0.06,text_align=TextNode.ACenter,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_c24 = DirectEntry(parent=canvas_1,text = "", scale=0.06,width=8,pos=(-1.25, 1,-0.35), command=self.daylight_commands,extraArgs=['DL_X'],initialText="0", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_c25=DirectLabel(parent=canvas_1,text='Y: ',pos=(-0.6,1,-0.35),scale=0.06,text_align=TextNode.ACenter,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_c26 = DirectEntry(parent=canvas_1,text = "", scale=0.06,width=8,pos=(-0.55, 1,-0.35), command=self.daylight_commands,extraArgs=['DL_Y'],initialText="0", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_c27=DirectLabel(parent=canvas_1,text='Z: ',pos=(0.1,1,-0.35),scale=0.06,text_align=TextNode.ACenter,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_c28 = DirectEntry(parent=canvas_1,text = "", scale=0.06,width=8,pos=(0.55, 1,-0.35), command=self.daylight_commands,extraArgs=['DL_Z'],initialText="0", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)

    def create_general_settings_gui(self):
        self.ScrolledFrame_d2=DirectScrolledFrame(
            canvasSize=(-2, 2, -2, 2),  # left, right, bottom, top
            frameSize=(-2, 2, -2, 2),
            pos=(0.1,0,0),
            #pos=(-0.35, 1,0.95)
            frameColor=(0.3, 0.3, 0.3, 0)
        )
        canvas_2=self.ScrolledFrame_d2.getCanvas()
        
        self.dlabel_d1 = DirectLabel(parent=canvas_2,text='Mouse Sensitivity (0-100,default 50): ',pos=(-1.1,1,0.75),scale=0.06,text_align=TextNode.ALeft,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_d2 = DirectEntry(parent=canvas_2,text = "", scale=0.06,width=10,pos=(0.3, 1,0.75), command=self.SetEntryText_d1,initialText="50", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_d3 = DirectLabel(parent=canvas_2,text='Move Speed (0-1,default 0.1): ',pos=(-1.1,1,0.65),scale=0.06,text_align=TextNode.ALeft,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_d4 = DirectEntry(parent=canvas_2,text = "", scale=0.06,width=10,pos=(0.3, 1,0.65), command=self.SetEntryText_d4,initialText="0.1", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.CheckButton_gs1 = DirectCheckButton(
            parent=canvas_2,
            text = " crosshair" ,
            text_align=TextNode.ALeft,
            scale=0.06,
            command=self.cbuttondef_gs1,
            pos=(-1.05, 1,0.55),
            frameColor=self.FRAME_COLOR_1,
            text_fg=self.TEXTFG_COLOR_1,
            indicatorValue=0
            )
        self.CheckButton_gs2 = DirectCheckButton(
            parent=canvas_2,
            text = " Show Gizmo" ,
            text_align=TextNode.ALeft,
            scale=0.06,
            command=self.cbuttondef_gs2,
            pos=(-1.05, 1,0.45),
            frameColor=self.FRAME_COLOR_1,
            text_fg=self.TEXTFG_COLOR_1,
            indicatorValue=1
            )
        self.CheckButton_gs3 = DirectCheckButton(
            parent=canvas_2,
            text = " Dark Theme" ,
            text_align=TextNode.ALeft,
            scale=0.06,
            command=self.cbuttondef_gs3,
            pos=(-1.05, 1,0.35),
            frameColor=self.FRAME_COLOR_1,
            text_fg=self.TEXTFG_COLOR_1,
            indicatorValue=1
            )            

    def create_model_lights_gui(self):
        self.ScrolledFrame_e1=DirectScrolledFrame(
            #canvasSize=(-2, 2, -2, 2),  # left, right, bottom, top
            frameSize=(-2, 2, -2, 2),
            pos=(0.1,0,0),
            #pos=(-0.35, 1,0.95)
            frameColor=(0.3, 0.3, 0.3, 0)
        )

        # Create a scrolled list without itemHeight
        self.scrolled_list_e1 = DirectScrolledList(
            decButton_pos=(0.35, 0, 0.6),
            decButton_text="Up",
            decButton_text_scale=0.05,
            decButton_borderWidth=(0.005, 0.005),
            incButton_pos=(0.35, 0, -0.98),
            incButton_text="Down",
            incButton_text_scale=0.05,
            incButton_borderWidth=(0.005, 0.005),
            frameSize=(0, 0.7, -0.95, 0.6),  # Left, Right, Bottom, Top
            frameColor=self.FRAME_COLOR_1,
            pos=(-1.3, 0, 0.1),  # Position in 3D space (x, y, z)
            numItemsVisible=14,
            itemFrame_pos=(0, 0,0.4),  # Positions frame at top
            itemsAlign=TextNode.ALeft
        )
        self.scrolled_list_e1.reparentTo(self.ScrolledFrame_e1)
        
        label_slist_top = DirectLabel(
        parent=self.scrolled_list_e1,  # Parent to the scrolled list
        text="cursor over list and scroll",
        frameColor=self.FRAME_COLOR_1,
        scale=0.06,
        pos=(0, 0, 0.53),  # Position at top of list frame
        text_fg=(0.3, 0.3, 0.7, 1),
        text_align=TextNode.ALeft
        )

        # Bind mouse wheel events
        self.accept("wheel_up", self.scroll_up)
        self.accept("wheel_down", self.scroll_down)

        # Track scroll index manually
        self.current_scroll_index = 0
        
        self.dlabel_e1=DirectLabel(parent=self.ScrolledFrame_e1.getCanvas(),text='SelectedLight: ',pos=(0.57,0,-0.4),scale=0.06,text_align=TextNode.ALeft,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dlabel_e2=DirectLabel(parent=self.ScrolledFrame_e1.getCanvas(),text='',pos=(1,0,-0.4),scale=0.06,text_align=TextNode.ALeft,text_fg=self.TEXTFG_COLOR_2,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dlabel_e3=DirectLabel(parent=self.ScrolledFrame_e1.getCanvas(),text='Overall Intensity: ',pos=(0.5,0,-0.5),scale=0.06,text_align=TextNode.ALeft,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_e4 = DirectEntry(parent=self.ScrolledFrame_e1.getCanvas(),text = "",pos=(1, 0,-0.5), scale=0.06,width=8, command=self.SetEntryText_e,extraArgs=['Overall_Intensity'],initialText="1", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_e5=DirectLabel(parent=self.ScrolledFrame_e1.getCanvas(),text='Intensity: ',pos=(0.5,0,-0.7),scale=0.06,text_align=TextNode.ALeft,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_e6 = DirectEntry(parent=self.ScrolledFrame_e1.getCanvas(),text = "",pos=(0.8, 0,-0.7), scale=0.06,width=8, command=self.SetEntryText_e,extraArgs=['Intensity'],initialText="1", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)

        self.dlabel_e7=DirectLabel(parent=self.ScrolledFrame_e1.getCanvas(),text='Color: ',pos=(0.5,0,-0.8),scale=0.06,text_align=TextNode.ALeft,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dlabel_e8=DirectLabel(parent=self.ScrolledFrame_e1.getCanvas(),text='R:',pos=(0.75,0,-0.8),scale=0.06,text_align=TextNode.ALeft,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_e9 = DirectEntry(parent=self.ScrolledFrame_e1.getCanvas(),text = "",pos=(0.85, 0,-0.8), scale=0.06,width=4, command=self.SetEntryText_e,extraArgs=['R'],initialText="1", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_e10=DirectLabel(parent=self.ScrolledFrame_e1.getCanvas(),text='G:',pos=(1.15,0,-0.8),scale=0.06,text_align=TextNode.ALeft,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_e11 = DirectEntry(parent=self.ScrolledFrame_e1.getCanvas(),text = "",pos=(1.25, 0,-0.8), scale=0.06,width=4, command=self.SetEntryText_e,extraArgs=['G'],initialText="1", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_e12=DirectLabel(parent=self.ScrolledFrame_e1.getCanvas(),text='B:',pos=(1.55,0,-0.8),scale=0.06,text_align=TextNode.ALeft,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_e13 = DirectEntry(parent=self.ScrolledFrame_e1.getCanvas(),text = "",pos=(1.65, 0,-0.8), scale=0.06,width=4, command=self.SetEntryText_e,extraArgs=['B'],initialText="1", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        
        self.dlabel_e14=DirectLabel(parent=self.ScrolledFrame_e1.getCanvas(),text='Attenuation: ',pos=(0.5,0,-0.9),scale=0.06,text_align=TextNode.ALeft,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dlabel_e15=DirectLabel(parent=self.ScrolledFrame_e1.getCanvas(),text='C:',pos=(0.9,0,-0.9),scale=0.06,text_align=TextNode.ALeft,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_e16 = DirectEntry(parent=self.ScrolledFrame_e1.getCanvas(),text = "",pos=(1, 0,-0.9), scale=0.06,width=4, command=self.SetEntryText_e,extraArgs=['C'],initialText="1", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_e17=DirectLabel(parent=self.ScrolledFrame_e1.getCanvas(),text='L:',pos=(1.3,0,-0.9),scale=0.06,text_align=TextNode.ALeft,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_e18 = DirectEntry(parent=self.ScrolledFrame_e1.getCanvas(),text = "",pos=(1.4, 0,-0.9), scale=0.06,width=4, command=self.SetEntryText_e,extraArgs=['L'],initialText="1", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_e19=DirectLabel(parent=self.ScrolledFrame_e1.getCanvas(),text='Q:',pos=(1.7,0,-0.9),scale=0.06,text_align=TextNode.ALeft,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_e20 = DirectEntry(parent=self.ScrolledFrame_e1.getCanvas(),text = "",pos=(1.8, 0,-0.9), scale=0.06,width=4, command=self.SetEntryText_e,extraArgs=['Q'],initialText="1", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)

        self.dlabel_e21=DirectLabel(parent=self.ScrolledFrame_e1.getCanvas(),text='Notes:',pos=(0.5,0,-1),scale=0.06,text_align=TextNode.ALeft,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_e22 = DirectEntry(parent=self.ScrolledFrame_e1.getCanvas(),text = "",pos=(0.7, 0,-1), scale=0.06,width=25, command=self.SetEntryText_e,extraArgs=['Notes'],initialText="", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        
    def create_model_nodepaths_viewer_gui(self):
        self.ScrolledFrame_f1=DirectScrolledFrame(
            frameSize=(-1, 1, -0.9, 0.8),  # left, right, bottom, top
            canvasSize=(-2, 2, -2, 2),
            pos=(0.1,0,0),
            frameColor=self.FRAME_COLOR_1
        )
        
    def create_model_animation_viewer_gui(self):
        self.ScrolledFrame_g1=DirectScrolledFrame(
            frameSize=(-2, 2, -2, 2),  # left, right, bottom, top
            canvasSize=(-2, 2, -2, 2),
            pos=(0.1,0,0),
            frameColor=(0.3, 0.3, 0.3, 0)
        )
        canvas_3=self.ScrolledFrame_g1.getCanvas()
        
        self.ScrolledFrame_g2=DirectScrolledFrame(
            parent=canvas_3,
            frameSize=(-1.4, -0.3, -0.9, 0.6),  # left, right, bottom, top
            canvasSize=(-2, 2, -2, 2),
            pos=(0.1,0,0),
            frameColor=self.FRAME_COLOR_1
        )
        
        self.checkbutton_g3=DirectCheckButton(
            parent=canvas_3,
            text = " Actor (Enable Actor)" ,
            text_align=TextNode.ALeft,
            scale=0.06,
            command=self.cbuttondef_g3,
            pos=(-1.05, 1,0.7),
            frameColor=self.FRAME_COLOR_1,
            text_fg=self.TEXTFG_COLOR_1,
            indicatorValue=0
            )

        self.dlabel_g4 = DirectLabel(parent=canvas_3,text='Current Animation: ',pos=(-0.1,1,0.6),scale=0.06,text_align=TextNode.ALeft,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dlabel_g5 = DirectLabel(parent=canvas_3,text='',pos=(0,1,0.5),scale=0.06,text_align=TextNode.ALeft,text_fg=self.TEXTFG_COLOR_2,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dbutton_g6 = DirectButton(parent=canvas_3,text='Play',pos=(-0.1,1,0.3),scale=0.07,text_align=TextNode.ALeft,command=self.ButtonDef_g6)
        self.dbutton_g7 = DirectButton(parent=canvas_3,text='Pause',pos=(-0.1,1,0.2),scale=0.07,text_align=TextNode.ALeft,command=self.ButtonDef_g7)
        self.dbutton_g8 = DirectButton(parent=canvas_3,text='Stop',pos=(-0.1,1,0.1),scale=0.07,text_align=TextNode.ALeft,command=self.ButtonDef_g8)
        self.checkbutton_g9=DirectCheckButton(parent=canvas_3,text = " Loop" ,text_align=TextNode.ALeft,scale=0.06,command=self.cbuttondef_g9,pos=(-0.05, 1,0),frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,indicatorValue=0)
        self.dbutton_g10 = DirectButton(parent=canvas_3,text='Load Egg Animation File',pos=(-0.1,1,-0.2),scale=0.07,text_align=TextNode.ALeft,command=self.ButtonDef_g10)
        self.dlabel_g11 = DirectLabel(parent=canvas_3,text='Animation Index to Remove(* for all): ',pos=(-0.1,1,-0.3),scale=0.06,text_align=TextNode.ALeft,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_g12 = DirectEntry(parent=canvas_3,text = "", scale=0.06,width=3,pos=(0.95, 1,-0.3), command=self.SetEntryText_g12,initialText="", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dentry_g12.enterText('*')
        self.dbutton_g13 = DirectButton(parent=canvas_3,text='Remove Animation',pos=(-0.1,1,-0.4),scale=0.07,text_align=TextNode.ALeft,command=self.ButtonDef_g13)
        
    def create_model_parent_editor_gui(self):
        self.ScrolledFrame_h1=DirectScrolledFrame(
            frameSize=(-2, 2, -2, 2),  # left, right, bottom, top
            canvasSize=(-2, 2, -2, 2),
            pos=(0.1,0,0),
            frameColor=(0.3, 0.3, 0.3, 0)
        )
        canvas_4=self.ScrolledFrame_h1.getCanvas()
        
        self.ScrolledFrame_h2=DirectScrolledFrame(
            parent=canvas_4,
            frameSize=(-1.5, 1.15, -0.9, 0.55),  # left, right, bottom, top
            canvasSize=(-2, 2, -2, 2),
            pos=(0.1,0,0),
            frameColor=(0.3, 0.3, 0.3, 0)
        )
        
        # description label at top
        self.dlabel_h0=DirectLabel(
            parent=canvas_4,
            text="Tip: Type 'render' or 0 to reparent to render. 'none' or -1 to detach the model.",
            text_scale=0.06,
            text_align=TextNode.ALeft,
            pos=(-1.4, 0, 0.7),
            text_fg=self.TEXTFG_COLOR_4,frameColor=self.FRAME_COLOR_2
        )
        # Title labels
        self.dlabel_h1=DirectLabel(
            parent=canvas_4,
            text="Index",
            text_scale=0.06,
            text_align=TextNode.ALeft,
            pos=(-1.4, 0, 0.6),
            text_fg=self.TEXTFG_COLOR_2,frameColor=self.FRAME_COLOR_2
        )
        self.dlabel_h2=DirectLabel(
            parent=canvas_4,
            text="Model Name",
            text_scale=0.06,
            text_align=TextNode.ALeft,
            pos=(-1.15, 0, 0.6),
            text_fg=self.TEXTFG_COLOR_2,frameColor=self.FRAME_COLOR_2
        )
        self.dlabel_h3=DirectLabel(
            parent=canvas_4,
            text="Parent Name",
            text_scale=0.06,
            text_align=TextNode.ALeft,
            pos=(-0.25, 0, 0.6),
            text_fg=self.TEXTFG_COLOR_2,frameColor=self.FRAME_COLOR_2
        )
        self.dlabel_h4=DirectLabel(
            parent=canvas_4,
            text="Parent Index",
            text_scale=0.06,
            text_align=TextNode.ALeft,
            pos=(0.86, 0, 0.6),
            text_fg=self.TEXTFG_COLOR_2,frameColor=self.FRAME_COLOR_2
        )
        self.add_items_to_model_parent_editor()
        
    def create_skybox_settings_gui(self):
        self.ScrolledFrame_i1=DirectScrolledFrame(
            frameSize=(-2, 2, -2, 2),  # left, right, bottom, top
            canvasSize=(-2, 2, -2, 2),
            pos=(0.1,0,0),
            frameColor=(0.3, 0.3, 0.3, 0)
        )
        canvas_5=self.ScrolledFrame_i1.getCanvas()
        
        self.dlabel_i0=DirectLabel(parent=canvas_5,text="SKYBOX SETTINGS",text_scale=0.06,text_align=TextNode.ALeft,pos=(-1.2, 0, 0.7),text_fg=self.TEXTFG_COLOR_2,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.CheckButton_i1 = DirectCheckButton(parent=canvas_5,text = "Enable Skybox" ,scale=.06,command=self.skybox_commands,extraArgs=['enable'],pos=(-1.15, 1,0.6),frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_align=TextNode.ALeft)
        self.CheckButton_i2 = DirectCheckButton(parent=canvas_5,text = "Show Skybox" ,scale=.06,command=self.skybox_commands,extraArgs=['show'],pos=(-1.15, 1,0.5),frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_align=TextNode.ALeft)
        self.dlabel_i3=DirectLabel(parent=canvas_5,text="Current Image: ",text_scale=0.06,text_align=TextNode.ALeft,pos=(-1.1, 0, 0.4),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dlabel_i4=DirectLabel(parent=canvas_5,text="",text_scale=0.05,text_align=TextNode.ALeft,pos=(-0.6, 0, 0.4),text_fg=self.TEXTFG_COLOR_3,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_2)
        self.dbutton_i5 = DirectButton(parent=canvas_5,text='Select Image',pos=(-1.1,1,0.3),scale=0.07,text_align=TextNode.ALeft,command=self.skybox_commands,extraArgs=['','select_image'])
        self.dlabel_i5_2=DirectLabel(parent=canvas_5,text=" *should be Equirectangular image",text_scale=0.06,text_align=TextNode.ALeft,pos=(-0.5, 0, 0.3),text_fg=self.TEXTFG_COLOR_4,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dlabel_i5_3=DirectLabel(parent=canvas_5,text="Skybox AmbientLight Intensity:",text_scale=0.06,text_align=TextNode.ALeft,pos=(-1.1, 0, 0.2),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_i5_4 = DirectEntry(parent=canvas_5,text = "", scale=0.06,width=5,pos=(-0.2, 1,0.2), command=self.skybox_commands,extraArgs=['intensity'],initialText="", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)

        self.dlabel_i6=DirectLabel(parent=canvas_5,text="Skybox AmbientLight Color:",text_scale=0.06,text_align=TextNode.ALeft,pos=(-1.1, 0, 0.1),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dlabel_i7=DirectLabel(parent=canvas_5,text="R:",text_scale=0.06,text_align=TextNode.ALeft,pos=(-0.3, 0, 0.1),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_i8 = DirectEntry(parent=canvas_5,text = "", scale=0.06,width=5,pos=(-0.2, 1,0.1), command=self.skybox_commands,extraArgs=['R'],initialText="", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_i9=DirectLabel(parent=canvas_5,text="G:",text_scale=0.06,text_align=TextNode.ALeft,pos=(0.2, 0, 0.1),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_i10 = DirectEntry(parent=canvas_5,text = "", scale=0.06,width=5,pos=(0.3, 1,0.1), command=self.skybox_commands,extraArgs=['G'],initialText="", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_i11=DirectLabel(parent=canvas_5,text="B:",text_scale=0.06,text_align=TextNode.ALeft,pos=(0.7, 0, 0.1),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_i12 = DirectEntry(parent=canvas_5,text = "", scale=0.06,width=5,pos=(0.8, 1,0.1), command=self.skybox_commands,extraArgs=['B'],initialText="", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        
        self.dlabel_i6_2=DirectLabel(parent=canvas_5,text="Sky Background Color:",text_scale=0.06,text_align=TextNode.ALeft,pos=(-1.1, 0, 0),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dlabel_i7_2=DirectLabel(parent=canvas_5,text="R:",text_scale=0.06,text_align=TextNode.ALeft,pos=(-0.4, 0, 0),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_i8_2 = DirectEntry(parent=canvas_5,text = "", scale=0.06,width=4,pos=(-0.3, 1,0), command=self.skybox_commands,extraArgs=['R0'],initialText="", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_i9_2=DirectLabel(parent=canvas_5,text="G:",text_scale=0.06,text_align=TextNode.ALeft,pos=(0, 0, 0),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_i10_2 = DirectEntry(parent=canvas_5,text = "", scale=0.06,width=4,pos=(0.1, 1,0), command=self.skybox_commands,extraArgs=['G0'],initialText="", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_i11_2=DirectLabel(parent=canvas_5,text="B:",text_scale=0.06,text_align=TextNode.ALeft,pos=(0.4, 0, 0),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_i12_2 = DirectEntry(parent=canvas_5,text = "", scale=0.06,width=4,pos=(0.5, 1,0), command=self.skybox_commands,extraArgs=['B0'],initialText="", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_i13_2=DirectLabel(parent=canvas_5,text="A:",text_scale=0.06,text_align=TextNode.ALeft,pos=(0.8, 0, 0),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_i14_2 = DirectEntry(parent=canvas_5,text = "", scale=0.06,width=4,pos=(0.9, 1,0), command=self.skybox_commands,extraArgs=['A0'],initialText="", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        
        self.CheckButton_i16 = DirectCheckButton(parent=canvas_5,text = "Enable ToneMapping" ,scale=.06,command=self.skybox_commands,extraArgs=['enable_tonemapping'],pos=(-1.15, 1,-0.1),frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_align=TextNode.ALeft)
        self.dlabel_i16_s = DirectLabel(parent=canvas_5,text = "*tonemapping for HDR images" ,scale=.06,pos=(-0.4, 1,-0.1),frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_4,text_bg=self.TEXTBG_COLOR_1,text_align=TextNode.ALeft)
        self.dlabel_i17 = DirectLabel(parent=canvas_5,text = "ToneMapping Method:" ,scale=.06,pos=(-1.1, 1,-0.2),frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,text_align=TextNode.ALeft)
        self.optionmenu_i18 = DirectOptionMenu(parent=canvas_5,text="switch_tonemap_method", scale=0.07, initialitem=0,highlightColor=(0.65, 0.65, 0.65, 1),command=self.set_skybox_tonemapping_method, textMayChange=1,items=self.tonemap_option_items,pos=(-0.4, 1,-0.2),frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,text_align=TextNode.ALeft)

        self.dlabel_i19=DirectLabel(parent=canvas_5,text="Exposure:",text_scale=0.06,text_align=TextNode.ALeft,pos=(-1.1, 0, -0.3),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_i20 = DirectEntry(parent=canvas_5,text = "", scale=0.06,width=5,pos=(-0.8, 1,-0.3), command=self.skybox_commands,extraArgs=['exposure'],initialText="", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,focusOutCommand=self.focusOutDef_arg)
        self.dentry_i20['focusInCommand'] = self.focusInDef_arg
        self.dentry_i20['focusInExtraArgs'] = [self.dentry_i20, "exposure",(0,50.0),0.01]
        self.dlabel_i21=DirectLabel(parent=canvas_5,text="Gamma:",text_scale=0.06,text_align=TextNode.ALeft,pos=(-0.4, 0, -0.3),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_i22 = DirectEntry(parent=canvas_5,text = "", scale=0.06,width=5,pos=(-0.1, 1,-0.3), command=self.skybox_commands,extraArgs=['gamma'],initialText="", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,focusOutCommand=self.focusOutDef_arg)
        self.dentry_i22['focusInCommand'] = self.focusInDef_arg
        self.dentry_i22['focusInExtraArgs'] = [self.dentry_i22, "gamma",(0,50.0),0.01]
        
        self.dlabel_i13=DirectLabel(parent=canvas_5,text="ENVIRONMENT MAP + IBL SETTINGS (simplepbr specific)",text_scale=0.06,text_align=TextNode.ALeft,pos=(-1.2, 0, -0.5),text_fg=self.TEXTFG_COLOR_2,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dbutton_i14 = DirectButton(parent=canvas_5,text='Save Environment Map',pos=(-1.2,1,-0.6),scale=0.07,text_align=TextNode.ALeft,command=self.skybox_commands,extraArgs=['','save_envmap'])
        self.dlabel_i14_2=DirectLabel(parent=canvas_5,text=" *it saves the background(skybox) as 6 cubemap images",text_scale=0.06,text_align=TextNode.ALeft,pos=(-0.4, 0, -0.6),text_fg=self.TEXTFG_COLOR_4,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.CheckButton_i15 = DirectCheckButton(parent=canvas_5,text = "enable envmap+IBL" ,scale=.06,command=self.skybox_commands,extraArgs=['enable_ibl'],pos=(-1.15, 1,-0.7),frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_align=TextNode.ALeft)
        self.dlabel_i15_2=DirectLabel(parent=canvas_5,text=" *it sets the saved cubemap as envmap+IBL in simplepbr",text_scale=0.06,text_align=TextNode.ALeft,pos=(-0.5, 0, -0.7),text_fg=self.TEXTFG_COLOR_4,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dlabel_i15_3=DirectLabel(parent=canvas_5,text=" (save the program and restart to see this takes effect)",text_scale=0.06,text_align=TextNode.ALeft,pos=(-0.45, 0, -0.8),text_fg=self.TEXTFG_COLOR_4,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)

    def set_skybox_tonemapping_method(self,InputValue):
        try:
            if self.global_params['skybox_enable_tonemapping']==True:
                InputValue=int(self.tonemap_option_items.index(InputValue))
                self.global_params['skybox_tonemapping_method']=InputValue+1
                self.skybox.setShaderInput('tonemapping_method', self.global_params['skybox_tonemapping_method'])
                self.skybox_commands(self.global_params['skybox_exposure'],'exposure')
                self.skybox_commands(self.global_params['skybox_gamma'],'gamma')
            else:
                self.display_last_status('skybox tonemapping is not enabled.')
        except:
            self.display_last_status('error when setting tonemapping_method')
        
    def skybox_commands(self,InputValue,identifier):
        try:
            if identifier=='enable':
                self.global_params['skybox_enable']=InputValue
                self.CheckButton_i1['indicatorValue']=InputValue
                if InputValue==True:
                    self.set_skybox()
                    self.display_last_status('skybox enabled.')
                else:
                    taskMgr.remove("update_skybox")
                    self.skybox.detachNode()
                    self.skybox.removeNode()
                    self.display_last_status('skybox removed.')
            elif identifier=='show':
                self.CheckButton_i2['indicatorValue']=InputValue
                if self.global_params['skybox_enable']==True:
                    if InputValue==True:
                        self.skybox.show()
                        self.display_last_status('skybox showed.')
                    else:
                        self.skybox.hide()
                        self.display_last_status('skybox hided.')
                else:
                    self.display_last_status('skybox disabled. enable to show or hide.')
            elif identifier=='select_image':
                root = tk.Tk()
                openedfilename=askopenfilename(title="open an image file",filetypes=[("image files", ".jpg .jpeg .png .hdr .exr"),("All files", "*.*")])
                root.destroy()
                if len(openedfilename)>0:
                    Loadedfilepath=os.path.relpath(openedfilename, os.getcwd())
                    uqname=os.path.basename(Loadedfilepath)
                    Loadedfilepath=Loadedfilepath.replace("\\","/")
                    try:
                        tex = self.loader.loadTexture(Loadedfilepath)
                        self.skybox.setTexture(tex)
                        self.skybox.setTexScale(TextureStage.getDefault(), -1, 1)
                        self.skybox.setTexOffset(TextureStage.getDefault(), 1, 0)
                        self.global_params['skybox_image']=Loadedfilepath
                        self.dlabel_i4.setText(Loadedfilepath)
                        self.display_last_status('skybox texture is set.')
                    except Exception as e:
                        logger.error('skybox texture file not supported:')
                        logger.error(e)
                        self.display_last_status('skybox texture file not supported:')
                else:
                    self.display_last_status('no file selected.')
            elif identifier=='intensity':
                try:
                    InputValue=float(InputValue)
                    self.global_params['skybox_ambientlight_intensity']=InputValue
                    IN=self.global_params['skybox_ambientlight_intensity']
                    r=self.global_params['skybox_ambientlight_R']*IN
                    g=self.global_params['skybox_ambientlight_G']*IN
                    b=self.global_params['skybox_ambientlight_B']*IN
                    self.ambientLight_skybox.setColor((r,g,b, 1))
                    self.dentry_i5_4.enterText(str(InputValue))
                except:
                    self.display_last_status('error when setting skybox intensity')
                    logger.error('error when setting skybox intensity')
            elif identifier=='R':
                try:
                    InputValue=float(InputValue)
                    self.global_params['skybox_ambientlight_R']=InputValue
                    IN=self.global_params['skybox_ambientlight_intensity']
                    r=self.global_params['skybox_ambientlight_R']*IN
                    g=self.global_params['skybox_ambientlight_G']*IN
                    b=self.global_params['skybox_ambientlight_B']*IN
                    self.ambientLight_skybox.setColor((r,g,b, 1))
                    self.dentry_i8.enterText(str(InputValue))
                except:
                    self.display_last_status('error when setting skybox color')
                    logger.error('error when setting skybox color R')
            elif identifier=='G':
                try:
                    InputValue=float(InputValue)
                    self.global_params['skybox_ambientlight_G']=InputValue
                    IN=self.global_params['skybox_ambientlight_intensity']
                    r=self.global_params['skybox_ambientlight_R']*IN
                    g=self.global_params['skybox_ambientlight_G']*IN
                    b=self.global_params['skybox_ambientlight_B']*IN
                    self.ambientLight_skybox.setColor((r,g,b, 1))
                    self.dentry_i10.enterText(str(InputValue))
                except:
                    self.display_last_status('error when setting skybox color')
                    logger.error('error when setting skybox color G')
            elif identifier=='B':
                try:
                    InputValue=float(InputValue)
                    self.global_params['skybox_ambientlight_B']=InputValue
                    IN=self.global_params['skybox_ambientlight_intensity']
                    r=self.global_params['skybox_ambientlight_R']*IN
                    g=self.global_params['skybox_ambientlight_G']*IN
                    b=self.global_params['skybox_ambientlight_B']*IN
                    self.ambientLight_skybox.setColor((r,g,b, 1))
                    self.dentry_i12.enterText(str(InputValue))
                except:
                    self.display_last_status('error when setting skybox color')
                    logger.error('error when setting skybox color B')
            elif identifier=='R0':
                try:
                    InputValue=float(InputValue)
                    self.global_params['sky_background_color'][0]=InputValue
                    self.setBackgroundColor(self.global_params['sky_background_color'])
                    self.dentry_i8_2.enterText(str(InputValue))
                except:
                    self.display_last_status('error when setting background color')
                    logger.error('error when setting background color R')
            elif identifier=='G0':
                try:
                    InputValue=float(InputValue)
                    self.global_params['sky_background_color'][1]=InputValue
                    self.setBackgroundColor(self.global_params['sky_background_color'])
                    self.dentry_i10_2.enterText(str(InputValue))
                except:
                    self.display_last_status('error when setting background color')
                    logger.error('error when setting background color G')
            elif identifier=='B0':
                try:
                    InputValue=float(InputValue)
                    self.global_params['sky_background_color'][2]=InputValue
                    self.setBackgroundColor(self.global_params['sky_background_color'])
                    self.dentry_i12_2.enterText(str(InputValue))
                except:
                    self.display_last_status('error when setting background color')
                    logger.error('error when setting background color B')
            elif identifier=='A0':
                try:
                    InputValue=float(InputValue)
                    self.global_params['sky_background_color'][3]=InputValue
                    self.setBackgroundColor(self.global_params['sky_background_color'])
                    self.dentry_i14_2.enterText(str(InputValue))
                except:
                    self.display_last_status('error when setting background color')
                    logger.error('error when setting background color A')
            elif identifier=='save_envmap':
                base.saveCubeMap('#_envmap.jpg', size = 512)
                logger.info('envmap saved.')
                self.display_last_status('envmap saved.')
            elif identifier=='enable_ibl':
                self.CheckButton_i15['indicatorValue']=InputValue
                if InputValue==True:
                    self.global_params['skybox_enable_envmap']=True
                    self.display_last_status('envmap ibl enabled.')
                else:
                    self.global_params['skybox_enable_envmap']=False
                    self.display_last_status('envmap ibl disabled.')
            elif identifier=='enable_tonemapping':
                if self.global_params['skybox_enable']==True:
                    self.global_params['skybox_enable_tonemapping']=InputValue
                    self.CheckButton_i16['indicatorValue']=InputValue
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
                        
                        self.display_last_status('skybox tonemapping enabled.')
                    else:
                        #self.skybox.setLightOff()
                        #self.skybox.setShaderAuto()
                        self.skybox.clearShader()
                        self.display_last_status('skybox tonemapping off.')
                else:
                    self.display_last_status('skybox is not enabled.')
            elif identifier=='exposure':
                try:
                    InputValue=float(InputValue)
                    self.global_params['skybox_exposure']=InputValue
                    self.dentry_i20.enterText(str(InputValue))
                    if self.global_params['skybox_enable_tonemapping']==True:
                        #if self.global_params['skybox_tonemapping_method']==1:
                        #    self.skybox.setShaderInput('exposure', self.global_params['skybox_exposure'])
                        self.skybox.setShaderInput('exposure', self.global_params['skybox_exposure'])
                    else:
                        self.display_last_status('skybox tonemapping is not enabled.')
                except:
                    self.display_last_status('error when setting skybox_exposure')
                    logger.error('error when setting skybox_exposure')
            elif identifier=='gamma':
                try:
                    InputValue=float(InputValue)
                    self.global_params['skybox_gamma']=InputValue
                    self.dentry_i22.enterText(str(InputValue))
                    if self.global_params['skybox_enable_tonemapping']==True:
                        self.skybox.setShaderInput('gamma', self.global_params['skybox_gamma'])
                    else:
                        self.display_last_status('skybox tonemapping is not enabled.')
                except:
                    self.display_last_status('error when setting skybox_gamma')
                    logger.error('error when setting skybox_gamma')
                
        except Exception as e:
            logger.error('error in skybox gui entry:')
            logger.error(e)
            self.display_last_status('error in skybox gui entry.')

    def create_heightmap_loader_gui(self):
        self.ScrolledFrame_j1=DirectScrolledFrame(
            frameSize=(-2, 2, -2, 2),  # left, right, bottom, top
            canvasSize=(-2, 2, -2, 2),
            pos=(0.1,0,0),
            frameColor=(0.3, 0.3, 0.3, 0)
        )
        canvas_5=self.ScrolledFrame_j1.getCanvas()
        
        self.dlabel_j0=DirectLabel(parent=canvas_5,text="GeoMipTerrain HeightMap Loader",text_scale=0.06,text_align=TextNode.ALeft,pos=(-1.4, 0, 0.7),text_fg=self.TEXTFG_COLOR_2,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dlabel_j1=DirectLabel(parent=canvas_5,text="Unique Name: ",text_scale=0.06,text_align=TextNode.ALeft,pos=(-1.4, 0, 0.6),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_j2 = DirectEntry(parent=canvas_5,text = "", scale=0.06,width=20,pos=(-0.9, 0,0.6), command=self.heightmap_commands,extraArgs=['unique_name'],initialText="Terrain_1", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_2,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_j3=DirectLabel(parent=canvas_5,text="Current Heightmap Image: ",text_scale=0.06,text_align=TextNode.ALeft,pos=(-1.4, 0, 0.5),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dlabel_j4=DirectLabel(parent=canvas_5,text="",text_scale=0.06,text_align=TextNode.ALeft,pos=(-0.6, 0, 0.5),text_fg=self.TEXTFG_COLOR_3,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dbutton_j5 = DirectButton(parent=canvas_5,text='Select HeightMap Image',pos=(-1.4,0,0.4),scale=0.07,text_align=TextNode.ALeft,command=self.heightmap_commands,extraArgs=['','select_heightmap'])
        self.dlabel_j6=DirectLabel(parent=canvas_5,text="BlockSize: ",text_scale=0.06,text_align=TextNode.ALeft,pos=(-1.4, 0, 0.3),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_j7 = DirectEntry(parent=canvas_5,text = "", scale=0.06,width=5,pos=(-1, 1,0.3), command=self.heightmap_commands,extraArgs=['blocksize'],initialText="32", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_j8=DirectLabel(parent=canvas_5,text="Near: ",text_scale=0.06,text_align=TextNode.ALeft,pos=(-1.4, 0, 0.2),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_j9 = DirectEntry(parent=canvas_5,text = "", scale=0.06,width=5,pos=(-1, 1,0.2), command=self.heightmap_commands,extraArgs=['near'],initialText="40", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_j10=DirectLabel(parent=canvas_5,text="Far: ",text_scale=0.06,text_align=TextNode.ALeft,pos=(-1.4, 0, 0.1),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_j11 = DirectEntry(parent=canvas_5,text = "", scale=0.06,width=5,pos=(-1, 1,0.1), command=self.heightmap_commands,extraArgs=['far'],initialText="100", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_j12=DirectLabel(parent=canvas_5,text="FocalPoint: ",text_scale=0.06,text_align=TextNode.ALeft,pos=(-1.4, 0, 0),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dlabel_j13=DirectLabel(parent=canvas_5,text=" self.Camera",text_scale=0.06,text_align=TextNode.ALeft,pos=(-1, 0, 0),text_fg=self.TEXTFG_COLOR_2,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dlabel_j14=DirectLabel(parent=canvas_5,text="Current Texture: ",text_scale=0.06,text_align=TextNode.ALeft,pos=(-1.4, 0, -0.2),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dlabel_j15=DirectLabel(parent=canvas_5,text="",text_scale=0.06,text_align=TextNode.ALeft,pos=(-0.8, 0, -0.2),text_fg=self.TEXTFG_COLOR_3,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dbutton_j16 = DirectButton(parent=canvas_5,text='Load Texture',pos=(-1.4,0,-0.3),scale=0.07,text_align=TextNode.ALeft,command=self.heightmap_commands,extraArgs=['','select_texture'])
        self.dlabel_j17=DirectLabel(parent=canvas_5,text="Texture Scale: ",text_scale=0.06,text_align=TextNode.ALeft,pos=(-1.4, 0, -0.4),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dlabel_j18=DirectLabel(parent=canvas_5,text="X: ",text_scale=0.06,text_align=TextNode.ALeft,pos=(-0.9, 0, -0.4),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_j19 = DirectEntry(parent=canvas_5,text = "", scale=0.06,width=5,pos=(-0.8, 0,-0.4), command=self.heightmap_commands,extraArgs=['X'],initialText="10", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_j20=DirectLabel(parent=canvas_5,text="Y: ",text_scale=0.06,text_align=TextNode.ALeft,pos=(-0.4, 0, -0.4),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_j21 = DirectEntry(parent=canvas_5,text = "", scale=0.06,width=5,pos=(-0.3, 0,-0.4), command=self.heightmap_commands,extraArgs=['Y'],initialText="10", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dbutton_j22 = DirectButton(parent=canvas_5,text='Generate Terrain',pos=(-1.4,0,-0.6),scale=0.07,text_align=TextNode.ALeft,command=self.heightmap_commands,extraArgs=['','generate_terrain'])

    def heightmap_commands(self,InputValue,identifier):
        try:
            if identifier=='unique_name':
                if (InputValue.lower()=='render') or (InputValue.lower()=='none') or (InputValue.lower()==''):
                    logger.info('heightmap unique name should not be render or none or empty')
                    self.display_last_status('heightmap unique name should not be render or none or empty.')
                else:
                    if InputValue not in self.models_names_all:
                        self.display_last_status('heightmap unique name is set.')
                    else:
                        self.display_last_status('heightmap unique name already exists.')
                        self.dentry_j2.enterText("")
            elif identifier=='select_heightmap':
                root = tk.Tk()
                openedfilename=askopenfilename(title="open an image file",filetypes=[("image files", ".jpg .jpeg .png .bmp .gif"),("All files", "*.*")])
                root.destroy()
                if len(openedfilename)>0:
                    Loadedfilepath=os.path.relpath(openedfilename, os.getcwd())
                    uqname=os.path.basename(Loadedfilepath)
                    Loadedfilepath=Loadedfilepath.replace("\\","/")
                    self.dlabel_j4.setText(Loadedfilepath)
                    if self.param_1['type']=='terrain':
                        self.dlabel_j4.setText(Loadedfilepath)
                        self.data_all[self.current_model_index]['heightmap_param'][0]=Loadedfilepath
                        self.display_last_status('heightmap is set.')
                    else:
                        self.display_last_status('current model is not a terrain. heightmap not applied.')
                else:
                    self.display_last_status('no file selected.')
            elif identifier=='blocksize':
                try:
                    InputValue=int(InputValue)
                    if self.param_1['type']=='terrain':
                        self.data_all[self.current_model_index]['heightmap_param'][1]=InputValue
                        self.terrain_all[self.current_model_index].setBlockSize(InputValue)
                        self.dentry_j7.enterText(str(InputValue))
                    else:
                        self.display_last_status('current model not a terrain.')
                except:
                    self.display_last_status('error when setting the entered number.')
                    self.dentry_j7.enterText("32")
            elif identifier=='near':
                try:
                    InputValue=int(InputValue)
                    if self.param_1['type']=='terrain':
                        self.data_all[self.current_model_index]['heightmap_param'][2]=InputValue
                        self.terrain_all[self.current_model_index].setNear(InputValue)
                        self.dentry_j9.enterText(str(InputValue))
                    else:
                        self.display_last_status('current model not a terrain.')
                except:
                    self.display_last_status('error when setting the entered number.')
                    self.dentry_j9.enterText("40")
            elif identifier=='far':
                try:
                    InputValue=int(InputValue)
                    if self.param_1['type']=='terrain':
                        self.data_all[self.current_model_index]['heightmap_param'][3]=InputValue
                        self.terrain_all[self.current_model_index].setFar(InputValue)
                        self.dentry_j11.enterText(str(InputValue))
                    else:
                        self.display_last_status('current model not a terrain.')
                except:
                    self.display_last_status('error when setting the entered number.')
                    self.dentry_j11.enterText("100")
            elif identifier=='select_texture':
                root = tk.Tk()
                openedfilename=askopenfilename(title="open an image file",filetypes=[("image files", ".jpg .jpeg .png .bmp .gif"),("All files", "*.*")])
                root.destroy()
                if len(openedfilename)>0:
                    Loadedfilepath=os.path.relpath(openedfilename, os.getcwd())
                    uqname=os.path.basename(Loadedfilepath)
                    Loadedfilepath=Loadedfilepath.replace("\\","/")
                    self.dlabel_j15.setText(Loadedfilepath)
                    if self.param_1['type']=='terrain':
                        try:
                            tex = self.loader.loadTexture(Loadedfilepath)
                            self.models_all[self.current_model_index].setTexture(TextureStage.getDefault(),tex)
                            self.dlabel_j15.setText(Loadedfilepath)
                            self.data_all[self.current_model_index]['heightmap_param'][4]=Loadedfilepath
                            self.display_last_status('terrain texture is set.')
                        except Exception as e:
                            logger.error('terrain texture file not set')
                            logger.error(e)
                            self.display_last_status('error when setting terrain texture.')
                    else:
                        self.display_last_status('current model is not a terrain. texture not applied.')
                else:
                    self.display_last_status('no file selected.')
            elif identifier=='X':
                try:
                    InputValue=int(InputValue)
                    if self.param_1['type']=='terrain':
                        self.data_all[self.current_model_index]['heightmap_param'][5]=InputValue
                        y_val=self.data_all[self.current_model_index]['heightmap_param'][6]
                        self.models_all[self.current_model_index].setTexScale(TextureStage.getDefault(), InputValue, y_val)
                        self.dentry_j19.enterText(str(InputValue))
                    else:
                        self.display_last_status('current model not a terrain.')
                except:
                    self.display_last_status('error when setting the entered number.')
                    self.dentry_j19.enterText("10")
            elif identifier=='Y':
                try:
                    InputValue=int(InputValue)
                    if self.param_1['type']=='terrain':
                        self.data_all[self.current_model_index]['heightmap_param'][6]=InputValue
                        x_val=self.data_all[self.current_model_index]['heightmap_param'][5]
                        self.models_all[self.current_model_index].setTexScale(TextureStage.getDefault(), x_val, InputValue)
                        self.dentry_j21.enterText(str(InputValue))
                    else:
                        self.display_last_status('current model not a terrain.')
                except:
                    self.display_last_status('error when setting the entered number.')
                    self.dentry_j21.enterText("10")
            elif identifier=='generate_terrain':
                InputValue=self.dentry_j2.get()
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
                        self.add_models_to_menuoption()
                        self.menudef_2_new(self.current_model_index)                                                       
                        logger.info('terrain generated.')
                        self.display_last_status('terrain generated and added to models.')
                    else:
                        self.display_last_status('heightmap unique name already exists. enter new unique name.')
                        self.dentry_j2.enterText("")

        except Exception as e:
            logger.error('error in heightmap gui entry:')
            logger.error(e)
            self.display_last_status('error in heightmap gui entry.')

    def add_heightmap_params_to_gui(self):
        self.dentry_j2.enterText(self.param_1["uniquename"])
        self.dlabel_j4.setText(self.param_1["heightmap_param"][0])
        self.heightmap_commands(self.param_1["heightmap_param"][1],'blocksize')
        self.heightmap_commands(self.param_1["heightmap_param"][2],'Near')
        self.heightmap_commands(self.param_1["heightmap_param"][3],'Far')
        self.dlabel_j15.setText(self.param_1["heightmap_param"][4])
        self.heightmap_commands(self.param_1["heightmap_param"][5],'X')
        self.heightmap_commands(self.param_1["heightmap_param"][6],'Y')
    
    def create_fog_settings_gui(self):
        self.ScrolledFrame_k1=DirectScrolledFrame(
            frameSize=(-2, 2, -2, 2),  # left, right, bottom, top
            canvasSize=(-2, 2, -2, 2),
            pos=(0.1,0,0),
            frameColor=(0.3, 0.3, 0.3, 0)
        )
        canvas_6=self.ScrolledFrame_k1.getCanvas()
        
        self.dlabel_k0=DirectLabel(parent=canvas_6,text="FOG SETTINGS",text_scale=0.06,text_align=TextNode.ALeft,pos=(-1.4, 0, 0.7),text_fg=self.TEXTFG_COLOR_2,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.CheckButton_k1 = DirectCheckButton(parent=canvas_6,text = "Enable Fog" ,scale=.06,command=self.fog_commands,extraArgs=['enable'],pos=(-1.3, 1,0.6),frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_align=TextNode.ALeft)
        self.dlabel_k2=DirectLabel(parent=canvas_6,text="Color:",text_scale=0.06,text_align=TextNode.ALeft,pos=(-1.3, 0, 0.5),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dlabel_k3=DirectLabel(parent=canvas_6,text="R:",text_scale=0.06,text_align=TextNode.ALeft,pos=(-1.1, 0, 0.5),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_k4 = DirectEntry(parent=canvas_6,text = "", scale=0.06,width=5,pos=(-1, 1,0.5), command=self.fog_commands,extraArgs=['R'],initialText="", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_k5=DirectLabel(parent=canvas_6,text="G:",text_scale=0.06,text_align=TextNode.ALeft,pos=(-0.6, 0, 0.5),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_k6 = DirectEntry(parent=canvas_6,text = "", scale=0.06,width=5,pos=(-0.5, 1,0.5), command=self.fog_commands,extraArgs=['G'],initialText="", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_k7=DirectLabel(parent=canvas_6,text="B:",text_scale=0.06,text_align=TextNode.ALeft,pos=(-0.1, 0, 0.5),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_k8 = DirectEntry(parent=canvas_6,text = "", scale=0.06,width=5,pos=(0, 1,0.5), command=self.fog_commands,extraArgs=['B'],initialText="", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.fog_radio_val=[1]
        self.RadioButtons_k9 = [
            DirectRadioButton(parent=canvas_6,text='Linear Fog', variable=self.fog_radio_val, value=[0],scale=0.07, pos=(-1.3, 0, 0.4), command=self.fog_commands,extraArgs=['','radio_1'],text_align=TextNode.ALeft,frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1),
            DirectRadioButton(parent=canvas_6,text='Exponential Fog', variable=self.fog_radio_val, value=[1],scale=0.07, pos=(-1.3, 0, 0.1), command=self.fog_commands,extraArgs=['','radio_2'],text_align=TextNode.ALeft,frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1)
        ]

        for button in self.RadioButtons_k9:
            button.setOthers(self.RadioButtons_k9)
        
        self.dlabel_k10=DirectLabel(parent=canvas_6,text="Linear Range:",text_scale=0.06,text_align=TextNode.ALeft,pos=(-1.3, 0, 0.3),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dlabel_k11=DirectLabel(parent=canvas_6,text="Start: ",text_scale=0.06,text_align=TextNode.ALeft,pos=(-0.9, 0, 0.3),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_k12 = DirectEntry(parent=canvas_6,text = "", scale=0.06,width=5,pos=(-0.7, 1,0.3), command=self.fog_commands,extraArgs=['start'],initialText="15", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_k13=DirectLabel(parent=canvas_6,text="End: ",text_scale=0.06,text_align=TextNode.ALeft,pos=(-0.3, 0, 0.3),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_k14 = DirectEntry(parent=canvas_6,text = "", scale=0.06,width=5,pos=(-0.1, 1,0.3), command=self.fog_commands,extraArgs=['end'],initialText="150", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_k15=DirectLabel(parent=canvas_6,text="Exponential Density: ",text_scale=0.06,text_align=TextNode.ALeft,pos=(-1.3, 0, 0),text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_1)
        self.dentry_k16 = DirectEntry(parent=canvas_6,text = "", scale=0.06,width=7,pos=(-0.7, 1,0), command=self.fog_commands,extraArgs=['density'],initialText="0.005", numLines = 1, focus=0,frameColor=self.FRAME_COLOR_1,text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)

    def fog_commands(self,InputValue,identifier):
        try:
            if identifier=='enable':
                self.CheckButton_k1['indicatorValue']=InputValue
                self.global_params['fog_enable']=InputValue
                if self.global_params['fog_enable']==True:
                    self.fog = Fog("FogEffect")
                    self.fog.setColor(Vec4(self.global_params['fog_R'], self.global_params['fog_G'], self.global_params['fog_B'], 1))
                    if self.fog_radio_val[0]==0:
                        self.fog.setLinearRange(self.global_params['fog_start'], self.global_params['fog_end'])
                    if self.fog_radio_val[0]==1:
                        self.fog.setExpDensity(self.global_params['fog_density'])
                    self.render.setFog(self.fog)
                else:
                    self.render.clearFog()

            if identifier=='R':
                self.dentry_k4.enterText(str(InputValue))
                InputValue=float(InputValue)
                self.global_params['fog_R']=InputValue
                if self.global_params['fog_enable']==True:
                    self.fog.setColor(Vec4(self.global_params['fog_R'], self.global_params['fog_G'], self.global_params['fog_B'], 1))
            if identifier=='G':
                self.dentry_k6.enterText(str(InputValue))
                InputValue=float(InputValue)
                self.global_params['fog_G']=InputValue
                if self.global_params['fog_enable']==True:
                    self.fog.setColor(Vec4(self.global_params['fog_G'], self.global_params['fog_G'], self.global_params['fog_B'], 1))
            if identifier=='B':
                self.dentry_k8.enterText(str(InputValue))
                InputValue=float(InputValue)
                self.global_params['fog_B']=InputValue
                if self.global_params['fog_enable']==True:
                    self.fog.setColor(Vec4(self.global_params['fog_R'], self.global_params['fog_G'], self.global_params['fog_B'], 1))
            if identifier=='start':
                self.dentry_k12.enterText(str(InputValue))
                InputValue=float(InputValue)
                self.global_params['fog_start']=InputValue
                if self.fog_radio_val[0]==0:
                    if self.global_params['fog_enable']==True:
                        self.fog.setLinearRange(self.global_params['fog_start'], self.global_params['fog_end'])
                        self.render.clearFog()
                        self.render.setFog(self.fog)
            if identifier=='end':
                self.dentry_k14.enterText(str(InputValue))
                InputValue=float(InputValue)
                self.global_params['fog_end']=InputValue
                if self.fog_radio_val[0]==0:
                    if self.global_params['fog_enable']==True:
                        self.fog.setLinearRange(self.global_params['fog_start'], self.global_params['fog_end'])
                        self.render.clearFog()
                        self.render.setFog(self.fog)
            if identifier=='density':
                self.dentry_k16.enterText(str(InputValue))
                InputValue=float(InputValue)
                self.global_params['fog_density']=InputValue
                if self.fog_radio_val[0]==1:
                    if self.global_params['fog_enable']==True:
                        self.fog.setExpDensity(self.global_params['fog_density'])
                        self.render.clearFog()
                        self.render.setFog(self.fog)

        except Exception as e:
            logger.error('error in fog gui entry:')
            logger.error(e)
            self.display_last_status('error in fog gui entry.')
            
    def cbuttondef_tst(self,status):
        if status:
            print('clickd')
        else:
            print('not clickd')
        
    def cbuttondef_1(self,status):
        if status:
            self.show_properties_gui()
        else:
            self.hide_properties_gui()

    def cbuttondef_2(self,status):
        if status:
            self.show_properties_gui_2()
        else:
            self.hide_properties_gui_2()

    def cbuttondef_3(self,status):
        if status:
            self.data_all[self.current_model_index]['enable']=True
            self.models_all[self.current_model_index]=loader.loadModel(self.data_all[self.current_model_index]["filename"])
            self.load_model_from_param(fileload_flag=False,indexload_flag=True)
            self.set_model_values_to_gui()
            self.makeup_lights_gui()
            self.add_model_nodepaths_to_gui_f1()
            self.add_model_animations_to_gui_g1()
            if self.model_parent_enabled_all[self.current_model_index]==True:
                self.attach_to_parent_2(self.models_all[self.current_model_index],self.model_parent_indices_all[self.current_model_index])
            
        else:
            self.data_all[self.current_model_index]['enable']=False
            self.models_all[self.current_model_index].detachNode()
            self.models_all[self.current_model_index].removeNode()
            self.models_all[self.current_model_index]=''
            
    def cbuttondef_4(self,status):
        if status:
            self.data_all[self.current_model_index]['show']=True
            self.models_all[self.current_model_index].show()
        else:
            self.data_all[self.current_model_index]['show']=False
            self.models_all[self.current_model_index].hide()

    def cbuttondef_5(self,status):
        if status:
            self.data_all[self.current_model_index]['pickable']=True
        else:
            self.data_all[self.current_model_index]['pickable']=False

    def cbuttondef_b3(self,status):
        if status:
            self.ScrolledFrame_d2.show()
        else:
            self.ScrolledFrame_d2.hide()

    def cbuttondef_b4(self,status):
        if status:
            self.ScrolledFrame_d1.show()
        else:
            self.ScrolledFrame_d1.hide()

    def cbuttondef_b5(self,status):
        if status:
            self.ScrolledFrame_e1.show()
        else:
            self.ScrolledFrame_e1.hide()

    def cbuttondef_b6(self,status):
        if status:
            self.ScrolledFrame_f1.show()
        else:
            self.ScrolledFrame_f1.hide()
            
    def cbuttondef_b7(self,status):
        if status:
            self.ScrolledFrame_g1.show()
        else:
            self.ScrolledFrame_g1.hide()

    def cbuttondef_b8(self,status):
        if status:
            self.ScrolledFrame_h1.show()
        else:
            self.ScrolledFrame_h1.hide()

    def cbuttondef_b9(self,status):
        if status:
            self.ScrolledFrame_i1.show()
        else:
            self.ScrolledFrame_i1.hide()

    def cbuttondef_b10(self,status):
        if status:
            self.ScrolledFrame_j1.show()
        else:
            self.ScrolledFrame_j1.hide()

    def cbuttondef_b11(self,status):
        if status:
            self.ScrolledFrame_k1.show()
        else:
            self.ScrolledFrame_k1.hide()

    def cbuttondef_gs1(self,status):
        if status:
            self.crosshair.show()
            self.global_params['crosshair']=True
        else:
            self.crosshair.hide()
            self.global_params['crosshair']=False

    def cbuttondef_gs2(self,status):
        if status:
            self.gizmo.show()
            self.global_params['gizmo']=True
        else:
            self.gizmo.hide()
            self.global_params['gizmo']=False

    def cbuttondef_gs3(self,status):
        if status:
            self.global_params['dark_theme']=True
            self.display_last_status('Dark Theme is on (save and restart to take effect)')
        else:
            self.global_params['dark_theme']=False
            self.display_last_status('Dark Theme is off (save and restart to take effect)')

    def cbuttondef_g3(self,status):
        if status:
            self.data_all[self.current_model_index]['actor'][0]=True
            self.param_1['actor'][0]=True
            #---cleanup existing actors---
            if isinstance(self.ModelTemp, Actor):
                self.ModelTemp.cleanup()
            self.ModelTemp.removeNode()
            if isinstance(self.models_all[self.current_model_index], Actor):
                self.models_all[self.current_model_index].cleanup()
            self.models_all[self.current_model_index].removeNode()
            #---load actor---
            self.current_actor=Actor(self.param_1["filename"])
            self.actors_all[self.current_model_index]=self.current_actor
            self.ModelTemp=self.render.attachNewNode("actor_node")
            self.current_actor.reparentTo(self.ModelTemp)
            self.models_all[self.current_model_index]=self.ModelTemp
            self.load_model_from_param(fileload_flag=0,indexload_flag=1)
            self.add_model_animations_to_gui_g1()
        else:
            self.data_all[self.current_model_index]['actor'][0]=False
            self.param_1['actor'][0]=False
            #---cleanup existing actors---
            if isinstance(self.ModelTemp, Actor):
                self.ModelTemp.stop()#.pose("idle", 0)
            self.gizmo.detachNode()
            model = self.ModelTemp.copyTo(self.render)
            if isinstance(self.ModelTemp, Actor):
                self.ModelTemp.cleanup()
            self.ModelTemp.removeNode()
            self.ModelTemp=''
            if isinstance(self.models_all[self.current_model_index], Actor):
                self.models_all[self.current_model_index].cleanup()
            self.models_all[self.current_model_index].removeNode()
            self.models_all[self.current_model_index]=model
            self.load_model_from_param(fileload_flag=0,indexload_flag=1)
            self.add_model_animations_to_gui_g1()
            
    def cbuttondef_g9(self,status):
        if self.current_animation is not None:
            if status:
                self.current_animation.loop(0)
                self.data_all[self.current_model_index]['actor'][2]=True
            else:
                self.current_animation.stop()
                self.data_all[self.current_model_index]['actor'][2]=False

    def GetSliderValue_1(self):
            self.dentry_1.enterText(str(self.dslider_1['value']))
            if self.dslider_1['value']!=self.dentry_1_value:
                self.update_model_property(self.dslider_1['value'],1)
            
    def SetEntryText_1(self,textEntered):
        try:
            self.dentry_1_value=float(textEntered)
            self.dentry_1.enterText(textEntered)
            self.dslider_1['value']=self.dentry_1_value
            self.update_model_property(self.dslider_1['value'],1)
        except ValueError:
            print('value entered in entry1 is not number')

    def SetEntryText_d1(self,textEntered):
        try:
            self.mouse_sensitivity=float(textEntered)
            self.global_params['mouse_sensitivity']=float(textEntered)
        except ValueError:
            print('value entered in entry d1 is not number')

    def SetEntryText_d4(self,textEntered):
        try:
            self.move_speed=float(textEntered)
            self.global_params['move_speed']=float(textEntered)
        except ValueError:
            print('value entered in entry d4 is not number')
            

    def GetSliderValue_2(self):
            self.dentry_2.enterText(str(self.dslider_2['value']))
            if self.dslider_2['value']!=self.dentry_2_value:
                self.update_model_property(self.dslider_2['value'],2)
            
    def SetEntryText_2(self,textEntered):
        try:
            self.dentry_2_value=float(textEntered)
            self.dentry_2.enterText(textEntered)
            self.dslider_2['value']=self.dentry_2_value
            self.update_model_property(self.dslider_2['value'],2)
        except ValueError:
            print('value entered in entry2 is not number')

    def GetSliderValue_3(self):
            self.dentry_3.enterText(str(self.dslider_3['value']))
            if self.dslider_3['value']!=self.dentry_3_value:
                self.update_model_property(self.dslider_3['value'],3)
            
    def SetEntryText_3(self,textEntered):
        try:
            self.dentry_3_value=float(textEntered)
            self.dentry_3.enterText(textEntered)
            self.dslider_3['value']=self.dentry_3_value
            self.update_model_property(self.dslider_3['value'],3)
        except ValueError:
            print('value entered in entry3 is not number')

    def SetEntryText_4(self, textEntered):
        try:
            if (textEntered.lower()=='render') or (textEntered.lower()=='none') or (textEntered.lower()==''):
                logger.info('unique name should not be render or none or empty.')
                self.display_last_status('unique name should not be render or none or empty.')
            else:
                if textEntered not in self.models_names_all:
                    curname=self.data_all[self.current_model_index]['uniquename']
                    self.dentry_3.enterText(textEntered)
                    self.data_all[self.current_model_index]['uniquename']=textEntered
                    self.models_names_all[self.current_model_index]=textEntered
                    #self.menu_2['items']=self.models_names_all
                    self.add_models_to_menuoption()
                    self.param_1['uniquename']=textEntered
                    if self.param_1['uniquename']==curname: 
                        self.param_1['uniquename']=textEntered
                    if curname in self.models_names_enabled:
                        idx=self.models_names_enabled.index(curname)
                        self.models_names_enabled[idx]=textEntered
                    if curname in self.models_with_lights:
                        idx=self.models_with_lights.index(curname)
                        self.models_with_lights[idx]=textEntered
                        self.data_all_light[idx]['uniquename']=textEntered
                    for i in range(len(self.model_parent_names_all)):
                        if self.model_parent_names_all[i]==curname:
                            self.model_parent_names_all[i]=textEntered
                            self.data_all[i]['parent'][1]=textEntered
                    
                    self.display_last_status('uniquename updated.')
                    logger.info('uniquename of model index '+str(self.current_model_index)+' is '+curname+' updated with '+textEntered)
                else:
                    logger.info('entered uniquename already exist.')
                    self.display_last_status('entered uniquename already exist.')
        except:
            logger.error('error in entry4')
            self.display_last_status('error in entry4')

    def SetEntryText_5(self,textEntered):
        try:
            self.data_all[self.current_model_index]['details']=textEntered
        except:
            print('error in entry5')
            
    def SetEntryText_6(self,textEntered):
        try:
            self.data_all[self.current_model_index]['notes']=textEntered
        except:
            print('error in entry6')
            
    def SetEntryText_7(self,textEntered):
        try:
            self.data_all[self.current_model_index]['pickable'][1]=textEntered
        except:
            print('error in entry7')

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
            self.display_last_status('error in entry_e.')

    def SetEntryText_g12(self,textEntered):
        try:
            #self.data_all[self.current_model_index]['pickable'][1]=textEntered
            print('')
        except:
            print('error in entry g12')

    def focusInDef(self):
        self.set_keymap()
        self.ignoreAll()
        self.accept('escape', self.exit_program)
        
    def focusInDef_arg(self,entry,identifier,entry_range,scrollSize):
        self.set_keymap()
        self.ignoreAll()
        self.accept('escape', self.exit_program)
        self.entry_temp=entry
        self.identifier_temp=identifier
        value = entry.get()
        try:
            value=float(value)
            self.floating_slider['value']=value
        except:
            self.display_last_status('error occurred when converting the value')
            logger.error('error occurred when converting the value to float in focusInDef_arg')
            return
        pos=entry.getPos()
        pos2=self.floating_slider.getPos()
        pos2[2]=pos[2]-0.1
        self.floating_slider.setPos(pos2)
        self.floating_slider['range']=entry_range
        self.floating_slider['scrollSize']=scrollSize
        self.floating_slider.show()

    def focusOutDef(self):
        self.set_keymap()

    def focusOutDef_arg(self):
        self.set_keymap()
        self.floating_slider.hide()
    
    def on_slider_change(self):
        current_value = self.floating_slider['value']
        if self.identifier_temp=="exposure":
            current_value=float("{:.2f}".format(current_value))
            self.skybox_commands(current_value,"exposure")
        if self.identifier_temp=="gamma":
            current_value=float("{:.2f}".format(current_value))
            self.skybox_commands(current_value,"gamma")
            
    def ButtonDef_g6(self):
        if self.current_animation is not None:
            self.current_animation.play()
        else:
            print('current_animation is none')

    def ButtonDef_g7(self):
        if self.current_animation is not None:
            if self.current_animation.isPlaying():
                self.current_animation.stop()
        else:
            print('current_animation is none')
        
    def ButtonDef_g8(self):
        if self.current_animation is not None:
            if self.current_animation.isPlaying():
                self.current_animation.stop()
                self.current_animation.pose(0)
        else:
            print('current_animation is none')
            
    def ButtonDef_g10(self):
        try:
            if self.param_1['actor'][0]==True:
                openedfilenames=askopenfilename(title="open a model animation file",filetypes=[("animation files", " .egg .bam .pz"),("All files", "*.*")],multiple=True)
                for i in range(len(openedfilenames)):
                    bname=os.path.basename(openedfilenames[i])
                    relpath=os.path.relpath(openedfilenames[i], os.getcwd())
                    aname=os.path.splitext(bname)[0]
                    self.current_actor=self.actors_all[self.current_model_index]
                    self.current_actor.loadAnims({aname: relpath})
                    self.data_all[self.current_model_index]['actor'][3].append(relpath)
                self.add_model_animations_to_gui_g1()
                
            else:
                print('not an Actor')
                self.display_last_status('not an Actor.')
        except Exception as e:
            logger.error('anim loading error:')
            logger.error(e)
            self.display_last_status('animation loading error.')
            
    def ButtonDef_g13(self):
        try:
            if self.param_1['actor'][0]==True:
                animIndex=self.dentry_g12.get()
                if animIndex=='*':
                    self.current_actor=self.actors_all[self.current_model_index]
                    self.current_actor.unloadAnims()
                    self.actors_all[self.current_model_index].unloadAnims()
                    self.data_all[self.current_model_index]['actor'][3]=[]
                else:
                    animIndex=int(animIndex)-1
                    self.current_actor.stop(self.anim_name_list[animIndex]) # this is important
                    self.current_actor.unloadAnims(anims = [self.anim_name_list[animIndex]])
                    for i in range(len(self.data_all[self.current_model_index]['actor'][3])-1,-1,-1):
                        aname=self.data_all[self.current_model_index]['actor'][3][i]
                        if aname==self.anim_name_list[animIndex]:
                            del self.data_all[self.current_model_index]['actor'][3][i]
                    # Release the animation control
                    #anim_control=self.current_actor.getAnimControl(self.anim_name_list[animIndex])
                    #self.current_actor.releaseAnim(anim_control)
                    self.add_model_animations_to_gui_g1()
                self.display_last_status('animation unloaded.')
            else:
                print('not an Actor')
                self.display_last_status('not an Actor.')
        except Exception as e:
            logger.error('anim removing error:')
            logger.error(e)
            self.display_last_status('animation removing error.')

    def ButtonDef_1(self):
        shutil.copyfile(self.scene_data_filename, self.scene_data_backup_filename)
        try:
            with open(self.scene_data_filename, 'w', encoding='utf-8') as f:
                json.dump(self.data_all, f, ensure_ascii=False, indent=4)
            self.display_last_status('json saved')
            logger.info('scene json saved')
        except:
            shutil.copyfile(self.scene_data_backup_filename, self.scene_data_filename)
            self.display_last_status('error while saving scene json file.')
            logger.error('error while saving scene json file.')
        # saving lights json
        shutil.copyfile(self.scene_light_data_filename, self.scene_light_data_backup_filename)
        try:
            with open(self.scene_light_data_filename, 'w', encoding='utf-8') as f:
                json.dump(self.data_all_light, f, ensure_ascii=False, indent=4)
            self.display_last_status('json saved(light data)')
            logger.info('json saved(light data)')
        except:
            shutil.copyfile(self.scene_light_data_backup_filename, self.scene_light_data_filename)
            self.display_last_status('json(light data) save error')
            logger.error('json(light data) save error')
        
        self.save_global_params()

    def menubuttonDef_1(self):
        if self.menu_dropdown_1.isHidden():
            self.menu_dropdown_1.show()
        else:
            self.menu_dropdown_1.hide()
    
    def menudef_1(self,val):
        self.current_property=self.property_names.index(val)+1
        self.change_property()
        
    def menudef_2(self,val):
        self.current_model_index=self.models_names_all.index(val)
        data=self.data_all[self.current_model_index]
        self.param_1=data
        self.load_model_from_param(fileload_flag=False,indexload_flag=True)
        self.set_model_values_to_gui()
        self.makeup_lights_gui()
        self.add_model_nodepaths_to_gui_f1()
        self.add_model_animations_to_gui_g1()
        self.add_items_to_model_parent_editor()

    def menudef_2_new(self,item_index):
        self.current_model_index=item_index
        data=self.data_all[self.current_model_index]
        self.param_1=data
        self.load_model_from_param(fileload_flag=False,indexload_flag=True)
        self.set_model_values_to_gui()
        self.makeup_lights_gui()
        self.add_model_nodepaths_to_gui_f1()
        self.add_model_animations_to_gui_g1()
        self.add_items_to_model_parent_editor()
        self.menu_2["text"]=self.models_names_all[item_index]
        self.ScrolledFrame_menu_2.hide()

    def DialogDef_1(self,arg):
        if arg:
            try:
                del self.models_names_all[self.current_model_index]
                if isinstance(self.models_all[self.current_model_index], Actor):
                    self.models_all[self.current_model_index].cleanup()
                if type(self.models_all[self.current_model_index])==type(NodePath()):
                    self.models_all[self.current_model_index].removeNode()
                del self.models_all[self.current_model_index]
                del self.data_all[self.current_model_index]
                #---delete lights data---
                idx=self.current_light_model_index
                if idx is not None:
                    del self.models_with_lights[idx]
                    del self.models_light_all[idx]
                    del self.models_light_names[idx]
                    for node in self.models_light_node_all[idx]:
                        self.render.clearLight(node)
                        # Remove all child nodes
                        for node2 in node.getChildren():
                            node2.removeNode()
                        node.removeNode()
                    del self.models_light_node_all[idx]
                    del self.data_all_light[idx]
                #---update model parent vars---
                self.create_model_parent_vars()
                
                self.current_model_index-=1
                if self.current_model_index<0: self.current_model_index=0
                self.add_models_to_menuoption()
                self.menudef_2_new(self.current_model_index)
                self.display_last_status('current model deleted.')
                self.dialog_1.cleanup()
                print('deleted.')
            except Exception as e:
                logger.error('error while deleting the model:')
                logger.error(e)
                self.display_last_status('error while deleting current model.')
                self.dialog_1.cleanup()
                pass
        else:
            print('model not deleted.')
            self.display_last_status('current model not deleted. (option NO selected?)')
            self.dialog_1.cleanup()
        
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
        self.keyMap = {"move_forward": 0, "move_backward": 0, "move_left": 0, "move_right": 0,"gravity_on":0,"load_model":0,"set_camera_pos":0,"x_increase":0,"x_decrease":0,"y_increase":0,"y_decrease":0,"z_increase":0,"z_decrease":0,"right_click":0,"switch_model":0,"delete_model":0,"up_arrow":0,"down_arrow":0,"right_arrow":0,"left_arrow":0,"look_at":0,"show_gui":1}
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
        self.accept("o", self.setKey, ["load_model", True])
        self.accept("c", self.setKey, ["set_camera_pos", True])
        self.accept("r", self.setKey, ["x_increase", True])
        self.accept("f", self.setKey, ["x_decrease", True])
        self.accept("r-up", self.setKey, ["x_increase", False])
        self.accept("f-up", self.setKey, ["x_decrease", False])
        self.accept("t", self.setKey, ["y_increase", True])
        self.accept("g", self.setKey, ["y_decrease", True])
        self.accept("t-up", self.setKey, ["y_increase", False])
        self.accept("g-up", self.setKey, ["y_decrease", False])
        self.accept("y", self.setKey, ["z_increase", True])
        self.accept("h", self.setKey, ["z_decrease", True])
        self.accept("y-up", self.setKey, ["z_increase", False])
        self.accept("h-up", self.setKey, ["z_decrease", False])
        self.accept("q", self.setKey, ["change_property", True])
        self.accept("mouse3", self.setKey, ["right_click", True])
        self.accept("mouse3-up", self.setKey, ["right_click", False])
        self.accept("z", self.setKey, ["switch_model", True])
        self.accept("delete", self.setKey, ["delete_model", False])
        self.accept("v", self.setKey, ["look_at", True])
        self.accept("m", self.setKey, ["show_gui", True])                                                                
        
        self.accept("arrow_up", self.setKey, ["up_arrow", True])
        self.accept("arrow_up-up", self.setKey, ["up_arrow", False])
        self.accept("arrow_down", self.setKey, ["down_arrow", True])
        self.accept("arrow_down-up", self.setKey, ["down_arrow", False])
        self.accept("arrow_right", self.setKey, ["right_arrow", True])
        self.accept("arrow_right-up", self.setKey, ["right_arrow", False])
        self.accept("arrow_left", self.setKey, ["left_arrow", True])
        self.accept("arrow_left-up", self.setKey, ["left_arrow", False])
        
    def change_property(self):
        if self.current_property==1:
            self.dlabel_1.setText('X: ')
            self.dlabel_2.setText('Y: ')
            self.dlabel_3.setText('Z: ')
            self.dslider_1['range']=(-1000,1000)
            self.dslider_1['pageSize']=1
            self.dslider_2['range']=(-1000,1000)
            self.dslider_2['pageSize']=1
            self.dslider_3['range']=(-1000,1000)
            self.dslider_3['pageSize']=1
            data=self.data_all[self.current_model_index]['pos'][1]
        if self.current_property==2:
            self.dlabel_1.setText('X: ')
            self.dlabel_2.setText('Y: ')
            self.dlabel_3.setText('Z: ')
            data=self.data_all[self.current_model_index]['scale'][1]
        if self.current_property==3:
            self.dlabel_1.setText('H: ')
            self.dlabel_2.setText('P: ')
            self.dlabel_3.setText('R: ')
            self.dslider_1['range']=(0,360)
            self.dslider_1['pageSize']=1
            self.dslider_2['range']=(0,360)
            self.dslider_2['pageSize']=1
            self.dslider_3['range']=(0,360)
            self.dslider_3['pageSize']=1
            data=self.data_all[self.current_model_index]['hpr'][1]
        if self.current_property==4:
            self.dlabel_1.setText('R: ')
            self.dlabel_2.setText('G: ')
            self.dlabel_3.setText('B: ')
            self.dslider_1['range']=(0,1)
            self.dslider_1['pageSize']=1.0/256
            self.dslider_2['range']=(0,1)
            self.dslider_2['pageSize']=1.0/256
            self.dslider_3['range']=(0,1)
            self.dslider_3['pageSize']=1.0/256
            data=self.data_all[self.current_model_index]['color'][1]
        self.dslider_1['value']=data[0]
        self.dentry_1.enterText(str(data[0]))
        self.dslider_2['value']=data[1]
        self.dentry_2.enterText(str(data[1]))
        self.dslider_3['value']=data[2]
        self.dentry_3.enterText(str(data[2]))
        
    # Records the state of the keys
    def setKey(self, key, value):
        
        if key=="gravity_on":
            self.keyMap[key]=not(self.keyMap[key])
        elif key=="show_gui":
            self.keyMap[key]=not(self.keyMap[key])
            if self.keyMap[key]==True:
                self.show_top_level_main_gui()
            else:
                self.hide_top_level_main_gui()
        
        elif key=="change_property":
            self.current_property+=1
            if self.current_property>len(self.property_names):
                self.current_property=1
            self.change_property()
            self.menu_1.set(self.current_property-1)
        elif key=="switch_model":
            self.current_model_index+=1
            if self.current_model_index>=len(self.models_names_all):
                self.current_model_index=0
            data=self.data_all[self.current_model_index]
            self.param_1=data
            self.menudef_2_new(self.current_model_index)
        elif key=="load_model":
            print('opening askfilename dialog to load a model')
            self.keyMap['load_model']=False
            len_curdir=len(os.getcwd())+1
            root = tk.Tk()
            openedfilenames=askopenfilename(title="open the model files",filetypes=[("model files", ".gltf .glb .egg .bam .pz"),("All files", "*.*")],multiple=True)#initialdir="."
            root.destroy()
            if len(openedfilenames)>0:
                for idx in range(len(openedfilenames)):
                    modelfilepath=os.path.relpath(openedfilenames[idx], os.getcwd())
                    modelfilepath=modelfilepath.replace("\\","/")
                    uqname=os.path.basename(modelfilepath)
                    tempname=uqname
                    for i in range(int(1e3)):
                        if tempname not in self.models_names_all:
                            continue
                        else:
                            tempname=uqname+'.%03d'%(i)
                    self.initialize_model_param(tempname,modelfilepath)
                    self.load_model_from_param(fileload_flag=True,indexload_flag=False)
                    self.add_models_to_menuoption()
                    self.menudef_2_new(self.current_model_index)                                                                                                                       
                    logger.info('model '+modelfilepath+' loaded')
                self.display_last_status('model files are loaded.')
            else:
                print('opened file name empty')
                self.display_last_status('model file not loaded.')
        elif key=="delete_model":
            print('delete pressed.')
            self.dialog_1 = YesNoDialog(dialogName="YesNoCancelDialog", text="Delete the current model?",
                     command=self.DialogDef_1)
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
    
    def set_model_values_to_gui(self):
        if self.current_property==1:
            data=self.data_all[self.current_model_index]['pos'][1]
        if self.current_property==2:
            data=self.data_all[self.current_model_index]['scale'][1]
        if self.current_property==3:
            data=self.data_all[self.current_model_index]['hpr'][1]
        if self.current_property==4:
            data=self.data_all[self.current_model_index]['color'][1]
        self.dslider_1['value']=data[0]
        self.dentry_1.enterText(str(data[0]))
        self.dslider_2['value']=data[1]
        self.dentry_2.enterText(str(data[1]))
        self.dslider_3['value']=data[2]
        self.dentry_3.enterText(str(data[2]))
        self.CheckButton_b1['indicatorValue']=self.data_all[self.current_model_index]['enable']
        self.CheckButton_b2['indicatorValue']=self.data_all[self.current_model_index]['show']
        self.dentry_b4.enterText(self.data_all[self.current_model_index]['uniquename'])
        self.dlabel_b5['text']='filename: '+self.data_all[self.current_model_index]['filename']
        self.dentry_b7.enterText(self.data_all[self.current_model_index]['details'])
        self.dentry_b9.enterText(self.data_all[self.current_model_index]['notes'])
        self.CheckButton_b10['indicatorValue']=self.data_all[self.current_model_index]['pickable'][0]
        self.dentry_b11.enterText(self.data_all[self.current_model_index]['pickable'][1])
        
        #---set actor data---
        self.checkbutton_g3['indicatorValue']=self.data_all[self.current_model_index]['actor'][0]
        self.dlabel_g5.setText(self.data_all[self.current_model_index]['actor'][1])
        self.checkbutton_g9['indicatorValue']=self.data_all[self.current_model_index]['actor'][2]
        self.add_model_animations_to_gui_g1()
        if self.param_1['type']=='terrain':
            self.add_heightmap_params_to_gui()
        
        
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
            if self.keyMap['right_click']==True:
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
                """
                rotate1 = Mat4()
                rotate1.setRotateMat(self.mouse_sensitivity*yval2, Vec3(1, 0, 0))
                rotate2 = Mat4()
                rotate2.setRotateMat(self.mouse_sensitivity*xval2, Vec3(0, 1, 0))
                self.cam_matrix = self.cam_matrix * rotate1 * rotate2
                self.camera.setMat(self.cam_matrix)
                """
            else:
                self.mouse_rotate_flag=0
                self.props.setCursorHidden(False)
                self.win.requestProperties(self.props)
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
            #print([newval_2,newval_1,newval_3])
            #print(self.cam_node.getPos())
            #print(self.render.getRelativePoint(self.camera, Vec3(0, 0, 0)))
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
        self.bottom_cam_label.setText('CamPos: %0.2f,%0.2f,%0.2f'%(newval_2,newval_1,newval_3))
        #print([newval_2,newval_1,newval_3])
        return Task.cont

    def general_tasks(self,task):
        if self.keyMap['set_camera_pos']==True:
            #rel_pos=self.cam_node.getRelativePoint(self.render,Vec3(self.param_1['pos'][1][0],self.param_1['pos'][1][1],self.param_1['pos'][1][2]))
            #self.camera.setPos((rel_pos[0],rel_pos[1],rel_pos[2]))                                                                                                                                                                                                       
            self.camera.setPos((self.param_1['pos'][1][0],self.param_1['pos'][1][1],self.param_1['pos'][1][2]))
            self.keyMap['set_camera_pos']=False
            self.display_last_status('camera position is set to center of current model.')
            
        if self.keyMap['look_at']==True:
            self.camera.lookAt(self.models_all[self.current_model_index])
            self.keyMap['look_at']=False                   
        if self.keyMap['x_increase']==True:
            if type(self.models_all[self.current_model_index])==type(NodePath()):
                if self.current_property==1:
                    value=self.models_all[self.current_model_index].getX()+self.temp_count*self.pos_increment
                    self.models_all[self.current_model_index].setX(value)
                    self.temp_count=self.temp_count+1
                    self.data_all[self.current_model_index]['pos'][1][0]=value
                    self.dentry_1_value=value
                    self.dentry_1.enterText(str(self.dentry_1_value))
                    self.dslider_1['value']=self.dentry_1_value
                if self.current_property==2:
                    cur_scale=self.models_all[self.current_model_index].getScale()
                    cur_scale[0]=cur_scale[0]+self.temp_count*self.scale_increment
                    cur_scale[1]=cur_scale[1]+self.temp_count*self.scale_increment
                    cur_scale[2]=cur_scale[2]+self.temp_count*self.scale_increment
                    self.models_all[self.current_model_index].setScale(cur_scale)
                    self.data_all[self.current_model_index]['scale'][1]=[cur_scale[0],cur_scale[1],cur_scale[2]]
                    self.dentry_1_value=cur_scale[0]
                    self.dentry_1.enterText(str(self.dentry_1_value))
                    self.dslider_1['value']=self.dentry_1_value
                    self.dentry_2_value=cur_scale[1]
                    self.dentry_2.enterText(str(self.dentry_2_value))
                    self.dslider_2['value']=self.dentry_2_value
                    self.dentry_3_value=cur_scale[2]
                    self.dentry_3.enterText(str(self.dentry_3_value))
                    self.dslider_3['value']=self.dentry_3_value
                if self.current_property==3:
                    cval=self.models_all[self.current_model_index].getH()+1
                    if cval>360: cval=0
                    self.models_all[self.current_model_index].setH(cval)
                    self.data_all[self.current_model_index]['hpr'][1][0]=cval
                    self.dentry_1_value=cval
                    self.dentry_1.enterText(str(self.dentry_1_value))
                    self.dslider_1['value']=self.dentry_1_value
                if self.current_property==4:
                    cur_color=self.models_all[self.current_model_index].getColorScale()
                    cval=cur_color.getX()
                    cval=cval+(1.0/256)
                    if cval>1:
                        self.models_all[self.current_model_index].setColorScale(1,cur_color[1],cur_color[2],cur_color[3])
                    else:
                        self.models_all[self.current_model_index].setColorScale(cval,cur_color[1],cur_color[2],cur_color[3])
                    self.data_all[self.current_model_index]['color'][1][0]=cval
                    self.dentry_1_value=cval
                    self.dentry_1.enterText(str(self.dentry_1_value))
                    self.dslider_1['value']=self.dentry_1_value
        elif self.keyMap['x_decrease']==True:
            if type(self.models_all[self.current_model_index])==type(NodePath()):
                if self.current_property==1:
                    value=self.models_all[self.current_model_index].getX()-self.temp_count*self.pos_increment
                    self.models_all[self.current_model_index].setX(value)
                    self.temp_count=self.temp_count+1
                    self.data_all[self.current_model_index]['pos'][1][0]=value
                    self.dentry_1_value=value
                    self.dentry_1.enterText(str(self.dentry_1_value))
                    self.dslider_1['value']=self.dentry_1_value
                if self.current_property==2:
                    cur_scale=self.models_all[self.current_model_index].getScale()
                    if sum(cur_scale)>0:
                        cur_scale[0]=cur_scale[0]-self.temp_count*self.scale_increment
                        cur_scale[1]=cur_scale[1]-self.temp_count*self.scale_increment
                        cur_scale[2]=cur_scale[2]-self.temp_count*self.scale_increment
                        self.models_all[self.current_model_index].setScale(cur_scale)
                        self.data_all[self.current_model_index]['scale'][1]=[cur_scale[0],cur_scale[1],cur_scale[2]]
                        self.dentry_1_value=cur_scale[0]
                        self.dentry_1.enterText(str(self.dentry_1_value))
                        self.dslider_1['value']=self.dentry_1_value
                        self.dentry_2_value=cur_scale[1]
                        self.dentry_2.enterText(str(self.dentry_2_value))
                        self.dslider_2['value']=self.dentry_2_value
                        self.dentry_3_value=cur_scale[2]
                        self.dentry_3.enterText(str(self.dentry_3_value))
                        self.dslider_3['value']=self.dentry_3_value
                if self.current_property==3:
                    cval=self.models_all[self.current_model_index].getH()-1
                    if cval<0: cval=360
                    self.models_all[self.current_model_index].setH(cval)
                    self.data_all[self.current_model_index]['hpr'][1][0]=cval
                    self.dentry_1_value=cval
                    self.dentry_1.enterText(str(self.dentry_1_value))
                    self.dslider_1['value']=self.dentry_1_value
                if self.current_property==4:
                    cur_color=self.models_all[self.current_model_index].getColorScale()
                    cval=cur_color.getX()
                    cval=cval-(1.0/256)
                    if cval<0:
                        self.models_all[self.current_model_index].setColorScale(0,cur_color[1],cur_color[2],cur_color[3])
                    else:
                        self.models_all[self.current_model_index].setColorScale(cval,cur_color[1],cur_color[2],cur_color[3])
                    self.data_all[self.current_model_index]['color'][1][0]=cval
                    self.dentry_1_value=cval
                    self.dentry_1.enterText(str(self.dentry_1_value))
                    self.dslider_1['value']=self.dentry_1_value
        elif self.keyMap['y_increase']==True:
            if type(self.models_all[self.current_model_index])==type(NodePath()):
                if self.current_property==1:
                    value=self.models_all[self.current_model_index].getY()+self.temp_count*self.pos_increment
                    self.models_all[self.current_model_index].setY(value)
                    self.temp_count=self.temp_count+1
                    self.data_all[self.current_model_index]['pos'][1][1]=value
                    self.dentry_2_value=value
                    self.dentry_2.enterText(str(self.dentry_2_value))
                    self.dslider_2['value']=self.dentry_2_value
                if self.current_property==3:
                    cval=self.models_all[self.current_model_index].getP()+1
                    if cval>360: cval=0
                    self.models_all[self.current_model_index].setP(cval)
                    self.data_all[self.current_model_index]['hpr'][1][1]=cval
                    self.dentry_2_value=cval
                    self.dentry_2.enterText(str(self.dentry_2_value))
                    self.dslider_2['value']=self.dentry_2_value
                if self.current_property==4:
                    cur_color=self.models_all[self.current_model_index].getColorScale()
                    cval=cur_color.getY()
                    cval=cval+(1.0/256)
                    if cval>1:
                        self.models_all[self.current_model_index].setColorScale(cur_color[0],1,cur_color[2],cur_color[3])
                    else:
                        self.models_all[self.current_model_index].setColorScale(cur_color[0],cval,cur_color[2],cur_color[3])
                    self.data_all[self.current_model_index]['color'][1][1]=cval
                    self.dentry_2_value=cval
                    self.dentry_2.enterText(str(self.dentry_2_value))
                    self.dslider_2['value']=self.dentry_2_value
        elif self.keyMap['y_decrease']==True:
            if type(self.models_all[self.current_model_index])==type(NodePath()):
                if self.current_property==1:
                    value=self.models_all[self.current_model_index].getY()-self.temp_count*self.pos_increment
                    self.models_all[self.current_model_index].setY(value)
                    self.temp_count=self.temp_count+1
                    self.data_all[self.current_model_index]['pos'][1][1]=value
                    self.dentry_2_value=value
                    self.dentry_2.enterText(str(self.dentry_2_value))
                    self.dslider_2['value']=self.dentry_2_value
                if self.current_property==3:
                    cval=self.models_all[self.current_model_index].getP()-1
                    if cval<0: cval=360
                    self.models_all[self.current_model_index].setP(cval)
                    self.data_all[self.current_model_index]['hpr'][1][1]=cval
                    self.dentry_2_value=cval
                    self.dentry_2.enterText(str(self.dentry_2_value))
                    self.dslider_2['value']=self.dentry_2_value
                if self.current_property==4:
                    cur_color=self.models_all[self.current_model_index].getColorScale()
                    cval=cur_color.getY()
                    cval=cval-(1.0/256)
                    if cval<0:
                        self.models_all[self.current_model_index].setColorScale(cur_color[0],0,cur_color[2],cur_color[3])
                    else:
                        self.models_all[self.current_model_index].setColorScale(cur_color[0],cval,cur_color[2],cur_color[3])
                    self.data_all[self.current_model_index]['color'][1][1]=cval
                    self.dentry_2_value=cval
                    self.dentry_2.enterText(str(self.dentry_2_value))
                    self.dslider_2['value']=self.dentry_2_value
        elif self.keyMap['z_increase']==True:
            if type(self.models_all[self.current_model_index])==type(NodePath()):
                if self.current_property==1:
                    value=self.models_all[self.current_model_index].getZ()+self.temp_count*self.pos_increment
                    self.models_all[self.current_model_index].setZ(value)
                    self.temp_count=self.temp_count+1
                    self.data_all[self.current_model_index]['pos'][1][2]=value
                    self.dentry_3_value=value
                    self.dentry_3.enterText(str(self.dentry_3_value))
                    self.dslider_3['value']=self.dentry_3_value
                if self.current_property==3:
                    cval=self.models_all[self.current_model_index].getR()+1
                    if cval>360: cval=0
                    self.models_all[self.current_model_index].setR(cval)
                    self.data_all[self.current_model_index]['hpr'][1][2]=cval
                    self.dentry_3_value=cval
                    self.dentry_3.enterText(str(self.dentry_3_value))
                    self.dslider_3['value']=self.dentry_3_value
                if self.current_property==4:
                    cur_color=self.models_all[self.current_model_index].getColorScale()
                    cval=cur_color.getZ()
                    cval=cval+(1.0/256)
                    if cval>1:
                        self.models_all[self.current_model_index].setColorScale(cur_color[0],cur_color[1],1,cur_color[3])
                    else:
                        self.models_all[self.current_model_index].setColorScale(cur_color[0],cur_color[1],cval,cur_color[3])
                    self.data_all[self.current_model_index]['color'][1][2]=cval
                    self.dentry_3_value=cval
                    self.dentry_3.enterText(str(self.dentry_3_value))
                    self.dslider_3['value']=self.dentry_3_value
        elif self.keyMap['z_decrease']==True:
            if type(self.models_all[self.current_model_index])==type(NodePath()):
                if self.current_property==1:
                    value=self.models_all[self.current_model_index].getZ()-self.temp_count*self.pos_increment
                    self.models_all[self.current_model_index].setZ(value)
                    self.temp_count=self.temp_count+1
                    self.data_all[self.current_model_index]['pos'][1][2]=value
                    self.dentry_3_value=value
                    self.dentry_3.enterText(str(self.dentry_3_value))
                    self.dslider_3['value']=self.dentry_3_value
                if self.current_property==3:
                    cval=self.models_all[self.current_model_index].getR()-1
                    if cval<0: cval=360
                    self.models_all[self.current_model_index].setR(cval)
                    self.data_all[self.current_model_index]['hpr'][1][2]=cval
                    self.dentry_3_value=cval
                    self.dentry_3.enterText(str(self.dentry_3_value))
                    self.dslider_3['value']=self.dentry_3_value
                if self.current_property==4:
                    cur_color=self.models_all[self.current_model_index].getColorScale()
                    cval=cur_color.getZ()
                    cval=cval-(1.0/256)
                    if cval<0:
                        self.models_all[self.current_model_index].setColorScale(cur_color[0],cur_color[1],0,cur_color[3])
                    else:
                        self.models_all[self.current_model_index].setColorScale(cur_color[0],cur_color[1],cval,cur_color[3])
                    self.data_all[self.current_model_index]['color'][1][2]=cval
                    self.dentry_3_value=cval
                    self.dentry_3.enterText(str(self.dentry_3_value))
                    self.dslider_3['value']=self.dentry_3_value
        else:
            self.temp_count=1
            
        return Task.cont
    
    def get_an_point_front_of_camera(self,distance,H,P):
        pos_val=self.camera.getPos()
        #pos_val=self.render.getRelativePoint(self.camera, Vec3(0,0,0))
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

    def update_model_property(self,value,option):
        # option 1 is x slider, 2 is y slider and 3 is z slider
        if option==1:
            if type(self.models_all[self.current_model_index])==type(NodePath()):
                if self.current_property==1:
                    self.models_all[self.current_model_index].setX(value)
                    self.data_all[self.current_model_index]['pos'][1][0]=value
                    self.dentry_1_value=value
                    self.dentry_1.enterText(str(self.dentry_1_value))
                    self.dslider_1['value']=self.dentry_1_value
                if self.current_property==2:
                    cur_scale=self.models_all[self.current_model_index].getScale()
                    cur_scale[0]=value
                    #cur_scale[1]=value
                    #cur_scale[2]=value
                    self.models_all[self.current_model_index].setScale(cur_scale)
                    self.data_all[self.current_model_index]['scale'][1]=[cur_scale[0],cur_scale[1],cur_scale[2]]
                    self.dentry_1_value=cur_scale[0]
                    self.dentry_1.enterText(str(self.dentry_1_value))
                    self.dslider_1['value']=self.dentry_1_value
                    self.dentry_2_value=cur_scale[1]
                    self.dentry_2.enterText(str(self.dentry_2_value))
                    self.dslider_2['value']=self.dentry_2_value
                    self.dentry_3_value=cur_scale[2]
                    self.dentry_3.enterText(str(self.dentry_3_value))
                    self.dslider_3['value']=self.dentry_3_value
                if self.current_property==3:
                    cval=value
                    if cval>360: cval=0
                    self.models_all[self.current_model_index].setH(cval)
                    self.data_all[self.current_model_index]['hpr'][1][0]=cval
                    self.dentry_1_value=cval
                    self.dentry_1.enterText(str(self.dentry_1_value))
                    self.dslider_1['value']=self.dentry_1_value
                if self.current_property==4:
                    cur_color=self.models_all[self.current_model_index].getColorScale()
                    cval=value
                    if cval>1:
                        self.models_all[self.current_model_index].setColorScale(1,cur_color[1],cur_color[2],cur_color[3])
                    else:
                        self.models_all[self.current_model_index].setColorScale(cval,cur_color[1],cur_color[2],cur_color[3])
                    self.data_all[self.current_model_index]['color'][1][0]=cval
                    self.dentry_1_value=cval
                    self.dentry_1.enterText(str(self.dentry_1_value))
                    self.dslider_1['value']=self.dentry_1_value
        elif option==2:
            if type(self.models_all[self.current_model_index])==type(NodePath()):
                if self.current_property==1:
                    self.models_all[self.current_model_index].setY(value)
                    self.data_all[self.current_model_index]['pos'][1][1]=value
                    self.dentry_2_value=value
                    self.dentry_2.enterText(str(self.dentry_2_value))
                    self.dslider_2['value']=self.dentry_2_value
                if self.current_property==2:
                    cur_scale=self.models_all[self.current_model_index].getScale()
                    #cur_scale[0]=value
                    cur_scale[1]=value
                    #cur_scale[2]=value
                    self.models_all[self.current_model_index].setScale(cur_scale)
                    self.data_all[self.current_model_index]['scale'][1]=[cur_scale[0],cur_scale[1],cur_scale[2]]
                    self.dentry_1_value=cur_scale[0]
                    self.dentry_1.enterText(str(self.dentry_1_value))
                    self.dslider_1['value']=self.dentry_1_value
                    self.dentry_2_value=cur_scale[1]
                    self.dentry_2.enterText(str(self.dentry_2_value))
                    self.dslider_2['value']=self.dentry_2_value
                    self.dentry_3_value=cur_scale[2]
                    self.dentry_3.enterText(str(self.dentry_3_value))
                    self.dslider_3['value']=self.dentry_3_value
                if self.current_property==3:
                    cval=value
                    if cval>360: cval=0
                    self.models_all[self.current_model_index].setP(cval)
                    self.data_all[self.current_model_index]['hpr'][1][1]=cval
                    self.dentry_2_value=cval
                    self.dentry_2.enterText(str(self.dentry_2_value))
                    self.dslider_2['value']=self.dentry_2_value
                if self.current_property==4:
                    cur_color=self.models_all[self.current_model_index].getColorScale()
                    cval=value
                    if cval>1:
                        self.models_all[self.current_model_index].setColorScale(cur_color[0],1,cur_color[2],cur_color[3])
                    else:
                        self.models_all[self.current_model_index].setColorScale(cur_color[0],cval,cur_color[2],cur_color[3])
                    self.data_all[self.current_model_index]['color'][1][1]=cval
                    self.dentry_2_value=cval
                    self.dentry_2.enterText(str(self.dentry_2_value))
                    self.dslider_2['value']=self.dentry_2_value
        elif option==3:
            if type(self.models_all[self.current_model_index])==type(NodePath()):
                if self.current_property==1:
                    self.models_all[self.current_model_index].setZ(value)
                    self.data_all[self.current_model_index]['pos'][1][2]=value
                    self.dentry_3_value=value
                    self.dentry_3.enterText(str(self.dentry_3_value))
                    self.dslider_3['value']=self.dentry_3_value
                if self.current_property==2:
                    cur_scale=self.models_all[self.current_model_index].getScale()
                    #cur_scale[0]=value
                    #cur_scale[1]=value
                    cur_scale[2]=value
                    self.models_all[self.current_model_index].setScale(cur_scale)
                    self.data_all[self.current_model_index]['scale'][1]=[cur_scale[0],cur_scale[1],cur_scale[2]]
                    self.dentry_1_value=cur_scale[0]
                    self.dentry_1.enterText(str(self.dentry_1_value))
                    self.dslider_1['value']=self.dentry_1_value
                    self.dentry_2_value=cur_scale[1]
                    self.dentry_2.enterText(str(self.dentry_2_value))
                    self.dslider_2['value']=self.dentry_2_value
                    self.dentry_3_value=cur_scale[2]
                    self.dentry_3.enterText(str(self.dentry_3_value))
                    self.dslider_3['value']=self.dentry_3_value
                if self.current_property==3:
                    cval=value
                    if cval>360: cval=0
                    self.models_all[self.current_model_index].setR(cval)
                    self.data_all[self.current_model_index]['hpr'][1][2]=cval
                    self.dentry_3_value=cval
                    self.dentry_3.enterText(str(self.dentry_3_value))
                    self.dslider_3['value']=self.dentry_3_value
                if self.current_property==4:
                    cur_color=self.models_all[self.current_model_index].getColorScale()
                    cval=value
                    if cval>1:
                        self.models_all[self.current_model_index].setColorScale(cur_color[0],cur_color[1],1,cur_color[3])
                    else:
                        self.models_all[self.current_model_index].setColorScale(cur_color[0],cur_color[1],cval,cur_color[3])
                    self.data_all[self.current_model_index]['color'][1][2]=cval
                    self.dentry_3_value=cval
                    self.dentry_3.enterText(str(self.dentry_3_value))
                    self.dslider_3['value']=self.dentry_3_value

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
    
    def makeup_lights_gui(self):
        self.scrolled_list_e1.removeAllItems()
        self.scrolled_list_e1.refresh()
        # Add clickable items to the list
        for i in range(len(self.light_name_list)):
            # Create a frame to hold label and button
            frame = DirectFrame(frameSize=(0, 0.7, -0.05, 0.05),frameColor=self.FRAME_COLOR_1)

            # Add label
            label = DirectLabel(
                parent=frame,
                text=f"{i+1}. ",
                scale=0.05,
                text_fg=self.TEXTFG_COLOR_1,
                frameColor=self.FRAME_COLOR_1,
                pos=(0, 0, 0),
                text_align=TextNode.ALeft
            )

            # Add button
            button = DirectButton(
                parent=frame,
                text=self.light_name_list[i],
                text_fg=self.TEXTFG_COLOR_1,
                scale=0.05,
                pos=(0.1, 0, 0),
                command=self.on_item_click,
                frameColor=self.FRAME_COLOR_1,
                text_align=TextNode.ALeft,
                extraArgs=[i]  # Pass item number to callback
            )
            # Define hover events
            button.bind(DGG.WITHIN, self.on_hover_1, [button])
            button.bind(DGG.WITHOUT, self.on_exit_1, [button])
            self.scrolled_list_e1.addItem(frame)
        
    def on_hover_1(self, button,frame):
        button["frameColor"] = (0, 0, 1, 0.5)

    def on_exit_1(self, button,frame):
        button["frameColor"] = self.FRAME_COLOR_1
    
    def is_mouse_over_list(self):
        if not base.mouseWatcherNode.hasMouse():
            return False
            
        if self.scrolled_list_e1.isHidden():
            return False

        mouse_x = base.mouseWatcherNode.getMouseX()
        mouse_y = base.mouseWatcherNode.getMouseY()

        list_pos = self.scrolled_list_e1.getPos()
        frame_size = self.scrolled_list_e1['frameSize']

        left = list_pos[0] + frame_size[0]
        right = list_pos[0] + frame_size[1]
        bottom = list_pos[2] + frame_size[2]
        top = list_pos[2] + frame_size[3]
        left=-0.904;right=-0.37;bottom=-0.84;top=0.7 #values manually findout from gui
        return (left <= mouse_x <= right) and (bottom <= mouse_y <= top)
    
    def scroll_up(self):
        if self.is_mouse_over_list():
            if self.current_scroll_index > 0:
                self.current_scroll_index -= 1
                self.scrolled_list_e1.scrollTo(self.current_scroll_index)
                print("Scroll Up Triggered | Index:", self.current_scroll_index)
        else:
            pass
            #print("Scroll Up Ignored - Mouse outside list")

    def scroll_down(self):
        if self.is_mouse_over_list():
            max_index = len(self.scrolled_list_e1['items']) - self.scrolled_list_e1['numItemsVisible']
            if self.current_scroll_index < max_index:
                self.current_scroll_index += 1
                self.scrolled_list_e1.scrollTo(self.current_scroll_index)
                print("Scroll Down Triggered | Index:", self.current_scroll_index)
        else:
            pass
            #print("Scroll Down Ignored - Mouse outside list")

    def on_item_click(self, item_index):
        self.plight_idx=item_index
        self.dlabel_e2.setText(self.light_name_list[item_index])
        
        idx=self.current_light_model_index
        if idx is not None:
            self.dentry_e4.enterText(str(self.data_all_light[idx]['overall_intensity']))
            self.dentry_e6.enterText(str(self.data_all_light[idx]['plights'][item_index]['intensity']))
            self.dentry_e9.enterText(str(self.data_all_light[idx]['plights'][item_index]['color'][1][0]))
            self.dentry_e11.enterText(str(self.data_all_light[idx]['plights'][item_index]['color'][1][1]))
            self.dentry_e13.enterText(str(self.data_all_light[idx]['plights'][item_index]['color'][1][2]))
            self.dentry_e16.enterText(str(self.data_all_light[idx]['plights'][item_index]['attenuation'][1][0]))
            self.dentry_e18.enterText(str(self.data_all_light[idx]['plights'][item_index]['attenuation'][1][1]))
            self.dentry_e20.enterText(str(self.data_all_light[idx]['plights'][item_index]['attenuation'][1][2]))
            self.dentry_e22.enterText(str(self.data_all_light[idx]['plights'][item_index]['notes']))
        else:
            pass

    def add_model_nodepaths_to_gui_f1(self):
        # Get the canvas NodePath
        canvas = self.ScrolledFrame_f1.getCanvas()

        # Remove all child nodes
        for child in canvas.getChildren():
            child.removeNode()
        
        nodepathlist=[]
        for npath in self.ModelTemp.find_all_matches("**/*"):
            nodepathlist.append(str(npath)+' , '+str(npath.node().getClassType()))#node().getName()

        # Add clickable items to the list
        for i in range(len(nodepathlist)):

            # Add label
            label = DirectLabel(
                parent=canvas,
                text=f"{i+1}. ",
                scale=0.05,
                text_fg=self.TEXTFG_COLOR_1,
                frameColor=self.FRAME_COLOR_1,
                pos=(0, 0, -0.1*i),
                text_align=TextNode.ALeft
            )

            # Add button
            button = DirectButton(
                parent=canvas,
                text=nodepathlist[i],
                text_fg=self.TEXTFG_COLOR_1,
                scale=0.05,
                pos=(0.1, 0, -0.1*i),
                command=self.on_item_click_f1,
                frameColor=self.FRAME_COLOR_1,
                text_align=TextNode.ALeft,
                extraArgs=[i]  # Pass item number to callback
            )
            # Define hover events
            button.bind(DGG.WITHIN, self.on_hover_1, [button])
            button.bind(DGG.WITHOUT, self.on_exit_1, [button])
            
            canvas_left=-0.1
            canvas_right=6
            canvas_bottom=-(len(nodepathlist)*0.1)
            canvas_top=0.1
            self.ScrolledFrame_f1["canvasSize"] = (canvas_left, canvas_right, canvas_bottom, canvas_top)

            # Force scrollbars to recompute
            self.ScrolledFrame_f1.guiItem.remanage()

    def add_models_to_menuoption(self):
        # Get the canvas NodePath
        canvas = self.ScrolledFrame_menu_2.getCanvas()

        # Remove all child nodes
        for child in canvas.getChildren():
            child.removeNode()
        
        modellist=[]
        for name in self.models_names_all:
            modellist.append(name)

        # Add clickable items to the list
        for i in range(len(modellist)):

            # Add label
            label = DirectLabel(
                parent=canvas,
                text=f"{i+1}. ",
                scale=0.07,
                text_fg=self.TEXTFG_COLOR_1,
                frameColor=self.FRAME_COLOR_1,
                pos=(0, 0, -0.1*i),
                text_align=TextNode.ALeft
            )

            # Add button
            button = DirectButton(
                parent=canvas,
                text=modellist[i],
                text_fg=self.TEXTFG_COLOR_1,
                scale=0.07,
                pos=(0.1, 0, -0.1*i),
                command=self.menudef_2_new,
                frameColor=self.FRAME_COLOR_1,
                text_align=TextNode.ALeft,
                extraArgs=[i]  # Pass item number to callback
            )
            # Define hover events
            button.bind(DGG.WITHIN, self.on_hover_1, [button])
            button.bind(DGG.WITHOUT, self.on_exit_1, [button])
            
            canvas_left=-0.1
            canvas_right=6
            #canvas_bottom=-(len(modellist)*button.getHeight()/10)
            canvas_bottom=-(len(modellist)*0.1)
            canvas_top=0.1
            self.ScrolledFrame_menu_2["canvasSize"] = (canvas_left, canvas_right, canvas_bottom, canvas_top)

            # Force scrollbars to recompute
            self.ScrolledFrame_menu_2.guiItem.remanage()

    def on_item_click_f1(self, item_index):
        pass

    def add_model_animations_to_gui_g1(self):
        # Get the canvas NodePath
        canvas = self.ScrolledFrame_g2.getCanvas()

        # Remove all child nodes
        for child in canvas.getChildren():
            child.removeNode()
        
        self.anim_name_list=[]
        self.current_actor=self.actors_all[self.current_model_index]
        self.current_animation=None
        if self.param_1['actor'][1]:
            self.dlabel_g5.setText(self.param_1['actor'][1])
        if isinstance(self.current_actor, Actor):
            self.anim_name_list=self.current_actor.getAnimNames()#self.ModelTemp
        
        # Add clickable items to the list
        for i in range(len(self.anim_name_list)):

            # Add label
            label = DirectLabel(
                parent=canvas,
                text=f"{i+1}. ",
                scale=0.05,
                text_fg=self.TEXTFG_COLOR_1,
                frameColor=self.FRAME_COLOR_1,
                pos=(0, 0, -0.1*i),
                text_align=TextNode.ALeft
            )

            # Add button
            button = DirectButton(
                parent=canvas,
                text=self.anim_name_list[i],
                text_fg=self.TEXTFG_COLOR_1,
                scale=0.05,
                pos=(0.1, 0, -0.1*i),
                command=self.on_item_click_g1,
                frameColor=self.FRAME_COLOR_1,
                text_align=TextNode.ALeft,
                extraArgs=[i]  # Pass item number to callback
            )
            # Define hover events
            button.bind(DGG.WITHIN, self.on_hover_1, [button])
            button.bind(DGG.WITHOUT, self.on_exit_1, [button])
            
            canvas_left=-0.1
            canvas_right=2
            canvas_bottom=-(len(self.anim_name_list)*button.getHeight()/10)
            canvas_top=0.1
            self.ScrolledFrame_g2["canvasSize"] = (canvas_left, canvas_right, canvas_bottom, canvas_top)

            # Force scrollbars to recompute
            self.ScrolledFrame_g2.guiItem.remanage()

    def on_item_click_g1(self, item_index):
        self.current_animation = self.current_actor.getAnimControl(self.anim_name_list[item_index])
        self.data_all[self.current_model_index]['actor'][1]=self.anim_name_list[item_index]
        self.dlabel_g5.setText(self.anim_name_list[item_index])

    def create_gizmo(self, position=Vec3(0, 0, 0), scale=1.0):
        # Create a LineSegs object for drawing the gizmo axes
        lines = LineSegs()
        lines.setThickness(3.0)  # Slightly thicker lines for visibility

        # X-axis (Bright Red)
        lines.setColor(VBase4(1, 0, 0, 1))  # Bright red
        lines.moveTo(0, 0, 0)  # Start at origin
        lines.drawTo(1 * scale, 0, 0)  # Draw to X=1

        # Y-axis (Bright Green)
        lines.setColor(VBase4(0, 1, 0, 1))  # Bright green
        lines.moveTo(0, 0, 0)  # Start at origin
        lines.drawTo(0, 1 * scale, 0)  # Draw to Y=1

        # Z-axis (Bright Blue)
        lines.setColor(VBase4(0, 0, 1, 1))  # Bright blue
        lines.moveTo(0, 0, 0)  # Start at origin
        lines.drawTo(0, 0, 1 * scale)  # Draw to Z=1

        # Create a GeomNode to hold the line geometry
        geom_node = lines.create()  # Generate the geometry
        gizmo_np = NodePath(geom_node)  # Create a NodePath for the gizmo
        gizmo_np.reparentTo(self.render)  # Attach to the scene graph
        gizmo_np.setPos(position)  # Set the gizmo's position

        # Simulate emission
        gizmo_np.setLightOff()  # Disable lighting to ensure consistent brightness
        #gizmo_np.setDepthTest(False)  # Render in front of other objects
        gizmo_np.setBin("fixed", 0)  # Ensure gizmo is drawn last
        gizmo_np.setTwoSided(True)  # Visible from all angles

        return gizmo_np            

    def add_items_to_model_parent_editor(self):
        canvas_5=self.ScrolledFrame_h2.getCanvas()
        
        # Remove all child nodes
        for child in canvas_5.getChildren():
            child.removeNode()
        
        # Populate table with models
        self.Tentry_MNames = []
        self.Tentry_MIndices = []
        for i in range(len(self.models_names_all)):
            # Serial number
            DirectLabel(
                parent=canvas_5,
                text=str(i + 1),
                text_scale=0.05,
                text_align=TextNode.ALeft,
                pos=(-1.48, 0, 0.5 - i * 0.1),
                text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_2
            )
            # Model name
            DirectLabel(
                parent=canvas_5,
                text=self.models_names_all[i],
                text_scale=0.05,
                text_align=TextNode.ALeft,
                pos=(-1.23, 0, 0.5 - i * 0.1),
                text_fg=self.TEXTFG_COLOR_1,text_bg=self.TEXTBG_COLOR_1,frameColor=self.FRAME_COLOR_2
            )
            # Text entry
            entry = DirectEntry(
                parent=canvas_5,
                scale=0.06,
                pos=(-0.33, 0, 0.5 - i * 0.1),
                initialText=self.model_parent_names_all[i],
                numLines=1,
                width=20,
                frameColor=self.FRAME_COLOR_2,
                text_fg=self.TEXTFG_COLOR_1,
                command=self.update_model_parent,
                extraArgs=[i],
                focusInCommand=self.focusInDef,
                focusOutCommand=self.focusOutDef
            )
            # Text entry 2
            entry2 = DirectEntry(
                parent=canvas_5,
                scale=0.06,
                pos=(0.97, 0, 0.5 - i * 0.1),
                initialText=str(self.model_parent_indices_all[i]),
                numLines=1,
                width=2,
                frameColor=self.FRAME_COLOR_2,
                text_fg=self.TEXTFG_COLOR_1,
                command=self.update_model_parent_2,
                extraArgs=[i],
                focusInCommand=self.focusInDef,
                focusOutCommand=self.focusOutDef
            )
            self.Tentry_MNames.append(entry)
            self.Tentry_MIndices.append(entry2)
            
            canvas_left=-1.5
            canvas_right=6
            canvas_bottom=-(len(self.models_names_all)*entry.getHeight()/10)
            canvas_top=0.6
            self.ScrolledFrame_h2["canvasSize"] = (canvas_left, canvas_right, canvas_bottom, canvas_top)

            # Force scrollbars to recompute
            self.ScrolledFrame_h2.guiItem.remanage()
        
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
                
Scene_1=SceneMakerMain()
Scene_1.run()


