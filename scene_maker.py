import panda3d
from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight, PointLight
from panda3d.core import TextNode, NodePath, LightAttrib
from panda3d.core import LVector3
from direct.actor.Actor import Actor
from direct.task.Task import Task
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from direct.showbase.DirectObject import DirectObject
from direct.gui.DirectGui import *
from panda3d.core import Texture, TexturePool, LoaderOptions, TextureStage, TexGenAttrib, TransformState
from direct.filter.FilterManager import FilterManager

from panda3d.core import LRotation
from panda3d.core import Mat4
import random


import sys
import os
import shutil
import math
from direct.filter.CommonFilters import CommonFilters
from panda3d.core import ClockObject

from panda3d.core import *
from panda3d.core import SamplerState
import tkinter
from tkinter.filedialog import askopenfilename
from tkinter import messagebox
import tkinter as tk

import simplepbr
import gltf

import json
import datetime
import time


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
#loadPrcFileData("", "gl-version 3 2")
#loadPrcFileData("", "notify-level-glgsg debug")                                         
#loadPrcFileData("", "win-size 1920 1080")
#loadPrcFileData("", "fullscreen t")                                          
class SceneMakerMain(ShowBase):

    def __init__(self):
        ShowBase.__init__(self)

        self.disable_mouse()
        
        self.FilterManager_1 = FilterManager(base.win, base.cam)
        self.Filters=CommonFilters(base.win, base.cam)                                       
        self.pipeline = simplepbr.init(use_normal_maps=True,exposure=0.8,sdr_lut_factor=0,max_lights=16,enable_fog=True)
        #---adjustable parameters---
        self.mouse_sensitivity=50
        self.move_speed=0.1
        self.scene_data_filename='scene_params1.json'
        self.scene_data_backup_filename='scene_params1_tempbackup.json'
        self.scene_light_data_filename='scene_light_params1.json'
        self.scene_light_data_backup_filename='scene_light_params1_tempbackup.json'
        self.load_lights_from_json=True #set this False if you dont want to load point lights from json file

        # Camera param initializations
        self.cameraHeight = 1.5     # camera Height above ground
        self.cameraAngleH = 0     # Horizontal angle (yaw)
        self.cameraAngleP = 0   # Vertical angle (pitch)
        self.camLens.setNear(0.01)
        self.camLens.setFar(1500)
        self.camera.setPos(0,0,1)
        
        #---if camera y,z axis rotated 90 deg, use below code----
        #self.cam_node=NodePath('cam_node')
        #self.cam_node.reparentTo(self.render)
        #self.cam_node.setHpr(0,-90,0)
        #self.camera.reparentTo(self.cam_node)
                
        self.light_name_list=[]
        self.light_list=[]
        self.light_node_list=[]
        self.current_light_model_index=None
        self.plight_idx=0                          
        self.set_keymap()
        self.current_model_index=0
        self.load_environment_models()
        self.setupLights()
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

        self.param_1={}
        self.param_1['pos']=[True,[0,0,0]]
        self.param_1['uniquename']=''
        self.param_2={}               
        self.current_property=1
        self.property_names=['position','scale','color','rotation']
        #self.pos_acceleration=1
        self.pos_increment=0.001
        #self.scale_acceleration=1
        self.scale_increment=0.01
        self.temp_count=1
        self.create_top_level_main_gui()
        #self.hide_top_level_main_gui()
        #self.create_model_lights_gui()                              

        
        #self.set_cubemap()

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
        self.menu_1 = DirectOptionMenu(text="switch_property", scale=0.07, initialitem=0,highlightColor=(0.65, 0.65, 0.65, 1),command=self.menudef_1, textMayChange=1,items=self.property_names,pos=(-1.3, 1,0.95),frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9))
        
        self.menu_2 = DirectOptionMenu(text="switch_models", scale=0.07, initialitem=0,highlightColor=(0.65, 0.65, 0.65, 1),command=self.menudef_2, textMayChange=1,items=self.models_names_all,pos=(0.1, 1,0.95),frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9))
        
        self.MenuButton_1 = DirectButton(text = "Menu",scale=.06,command=self.menubuttonDef_1,pos=(-0.75, 1,0.95))
        self.dbutton_1 = DirectButton(text=("save"),scale=.06, pos=(0, 1,0.95),command=self.ButtonDef_1)
        self.dlabel_status=DirectLabel(text='Last Status: ',pos=(-1.3,1,0.85),scale=0.06,text_align=TextNode.ALeft,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dlabel_status2=DirectLabel(text='',pos=(-0.92,1,0.85),scale=0.06,text_align=TextNode.ALeft,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
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
        self.create_dropdown_main_menu()
        self.menu_dropdown_1.hide()
        
        #self.MenuButton_1['state'] = DGG.NORMAL
        #self.MenuButton_1.bind(DGG.WITHOUT, self.menu_hover_command, [False])
        #self.MenuButton_1.bind(DGG.WITHIN, self.menu_hover_command, [True])
        #---display camera pos at bottom---
        self.bottom_cam_label=DirectLabel(text='CamPos: ',pos=(-1,1,-0.9),scale=0.05,text_align=TextNode.ACenter,text_fg=(1, 1, 1, 0.8),text_bg=(0,0,0,0.2),frameColor=(0, 0, 0, 0.1))
    
    def show_top_level_main_gui(self):
        self.menu_1.show()
        self.menu_2.show()
        self.MenuButton_1.show()
        self.dbutton_1.show()
        self.dlabel_status.show()
        self.dlabel_status2.show()
        self.bottom_cam_label.show()        
        
    def hide_top_level_main_gui(self):
        self.menu_1.hide()
        self.menu_2.hide()
        self.MenuButton_1.hide()
        self.dbutton_1.hide()
        self.dlabel_status.hide()
        self.dlabel_status2.hide()                                                                                         
        self.bottom_cam_label.hide()
        panda3d.core.load_prc_file_data('', 'show-frame-rate-meter false')                                                                          
        
    def menu_hover_command(self,hover, frame):
        if hover:
            self.menu_dropdown_1.show()
        else:
            taskMgr.doMethodLater(2.0, self.menu_dropdown_1.hide, 'hidemainmenu', extraArgs=[])

    def create_dropdown_main_menu(self):
        self.menu_dropdown_1=DirectScrolledFrame(
            canvasSize=(0, 1, -0.9, 0),  # left, right, bottom, top
            frameSize=(0, 1, -0.9, 0),
            pos=(-1,0,0.9),
            #pos=(-0.35, 1,0.95)
            frameColor=(0.3, 0.3, 0.3, 0.3)
        )
        
        self.CheckButton_1 = DirectCheckButton(
            parent=self.menu_dropdown_1.getCanvas(),
            text = "properties " ,
            text_align=TextNode.ALeft,
            scale=.06,
            command=self.cbuttondef_1,
            pos=(0.1,1,-0.1),
            frameColor=(0, 0, 0, 0.4),
            text_fg=(1, 1, 1, 0.9),
            indicatorValue=1
            )
        self.CheckButton_2 = DirectCheckButton(
            parent=self.menu_dropdown_1.getCanvas(),
            text = "all properties" ,
            text_align=TextNode.ALeft,
            scale=.06,
            command=self.cbuttondef_2,
            pos=(0.1, 1,-0.2),
            frameColor=(0, 0, 0, 0.4),
            text_fg=(1, 1, 1, 0.9),
            indicatorValue=0
            )
        self.CheckButton_3 = DirectCheckButton(
            parent=self.menu_dropdown_1.getCanvas(),
            text = "General Settings" ,
            text_align=TextNode.ALeft,
            scale=.06,
            command=self.cbuttondef_b3,
            pos=(0.1, 1,-0.3),
            frameColor=(0, 0, 0, 0.4),
            text_fg=(1, 1, 1, 0.9),
            indicatorValue=0
            )
        self.CheckButton_4 = DirectCheckButton(
            parent=self.menu_dropdown_1.getCanvas(),
            text = "Light Settings" ,
            text_align=TextNode.ALeft,
            scale=.06,
            command=self.cbuttondef_b4,
            pos=(0.1, 1,-0.4),
            frameColor=(0, 0, 0, 0.4),
            text_fg=(1, 1, 1, 0.9),
            indicatorValue=0
            )
        self.CheckButton_5 = DirectCheckButton(
            parent=self.menu_dropdown_1.getCanvas(),
            text = "Model Light Settings" ,
            text_align=TextNode.ALeft,
            scale=.06,
            command=self.cbuttondef_b5,
            pos=(0.1, 1,-0.5),
            frameColor=(0, 0, 0, 0.4),
            text_fg=(1, 1, 1, 0.9),
            indicatorValue=0
            )
        

    def create_properties_gui(self):
        self.dlabel_1=DirectLabel(text='X: ',pos=(-1.3,1,0.75),scale=0.06,text_align=TextNode.ACenter,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dlabel_2=DirectLabel(text='Y: ',pos=(-1.3,1,0.65),scale=0.06,text_align=TextNode.ACenter,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dlabel_3=DirectLabel(text='Z: ',pos=(-1.3,1,0.55),scale=0.06,text_align=TextNode.ACenter,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        
        self.dslider_1 = DirectSlider(range=(-1000,1000), value=0, pageSize=1, command=self.GetSliderValue_1,pos=(-1.2, 1,0.83),frameSize=(0,0.9,-0.1,0),frameColor=(0,0,0,0.5),thumb_frameSize=(0,0.05,0.04,-0.04))
        self.dentry_1 = DirectEntry(text = "", scale=0.06,width=10,pos=(-0.2, 1,0.75), command=self.SetEntryText_1,initialText="0", numLines = 1, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dentry_1_value=0

        self.dslider_2 = DirectSlider(range=(-1000,1000), value=0, pageSize=1, command=self.GetSliderValue_2,pos=(-1.2, 1,0.73),frameSize=(0,0.9,-0.1,0),frameColor=(0,0,0,0.5),thumb_frameSize=(0,0.05,0.04,-0.04))
        self.dentry_2 = DirectEntry(text = "", scale=0.06,width=10,pos=(-0.2, 1,0.65), command=self.SetEntryText_2,initialText="0", numLines = 1, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dentry_2_value=0

        self.dslider_3 = DirectSlider(range=(-1000,1000), value=0, pageSize=1, command=self.GetSliderValue_3,pos=(-1.2, 1,0.63),frameSize=(0,0.9,-0.1,0),frameColor=(0,0,0,0.5),thumb_frameSize=(0,0.05,0.04,-0.04))
        self.dentry_3 = DirectEntry(text = "", scale=0.06,width=10,pos=(-0.2, 1,0.55), command=self.SetEntryText_3,initialText="0", numLines = 1, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
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
        self.CheckButton_b1 = DirectCheckButton(text = "enable model" ,scale=.06,command=self.cbuttondef_3,pos=(-1.3, 1,0.4),frameColor=(0, 0, 0, 0.4),text_fg=(1, 1, 1, 0.9),text_align=TextNode.ALeft)
        self.CheckButton_b2 = DirectCheckButton(text = "show model" ,scale=.06,command=self.cbuttondef_4,pos=(-1.3, 1,0.3),frameColor=(0, 0, 0, 0.4), text_fg=(1, 1, 1, 0.9),text_align=TextNode.ALeft)
        self.dlabel_b3=DirectLabel(text='uniquename: ',pos=(-1.3,1,0.2),scale=0.06,text_align=TextNode.ALeft,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dentry_b4 = DirectEntry(text = "", scale=0.06,width=20,pos=(-0.9, 1,0.2), command=self.SetEntryText_4,initialText="", numLines = 1, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_b5=DirectLabel(text='filename: ',pos=(-1.3,1,0.1),scale=0.06,text_align=TextNode.ALeft,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        
        self.dlabel_b6=DirectLabel(text='details: ',pos=(-1.3,1,0),scale=0.06,text_align=TextNode.ALeft,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dentry_b7 = DirectEntry(text = "", scale=0.06,width=30,pos=(-0.9, 1,0), command=self.SetEntryText_5,initialText="", numLines = 4, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_b8=DirectLabel(text='notes: ',pos=(-1.3,1,-0.3),scale=0.06,text_align=TextNode.ALeft,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dentry_b9 = DirectEntry(text = "", scale=0.06,width=30,pos=(-0.9, 1,-0.3), command=self.SetEntryText_6,initialText="", numLines = 4, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.CheckButton_b10 = DirectCheckButton(text = "pickable" ,scale=.06,command=self.cbuttondef_5,pos=(-1.3, 1,-0.6),frameColor=(0, 0, 0, 0.4),text_fg=(1, 1, 1, 0.9),text_align=TextNode.ALeft)
        self.dlabel_b9_2=DirectLabel(text='description: ',pos=(-1.3,1,-0.7),scale=0.06,text_align=TextNode.ALeft,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dentry_b11 = DirectEntry(text = "", scale=0.06,width=30,pos=(-0.9, 1,-0.7), command=self.SetEntryText_7,initialText="", numLines = 4, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),text_align=TextNode.ALeft,focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)

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

    def create_daylight_gui(self):
        self.ScrolledFrame_d1=DirectScrolledFrame(
            canvasSize=(-2, 2, -2, 2),  # left, right, bottom, top
            frameSize=(-2, 2, -2, 2),
            pos=(0.1,0,0),
            #pos=(-0.35, 1,0.95)
            frameColor=(0.3, 0.3, 0.3, 0)
        )
        canvas_1=self.ScrolledFrame_d1.getCanvas()
        #self.daylight_adjuster_gui=DirectFrame(pos=(-1.35, 1,1),frameSize=(0,0.8,-0.9,0),frameColor=(0, 0, 0, 0.1))
        
        self.dlabel_c1 = DirectLabel(parent=canvas_1,text='Ambient light: intensity',pos=(-0.8,1,0.75),scale=0.06,text_align=TextNode.ACenter,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dentry_c2 = DirectEntry(parent=canvas_1,text = "", scale=0.06,width=10,pos=(-0.3, 1,0.75), command=self.SetEntryText_c1,initialText="0.1", numLines = 1, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        
        self.dlabel_c3=DirectLabel(parent=canvas_1,text='R (0 to 1): ',pos=(-0.7,1,0.65),scale=0.06,text_align=TextNode.ACenter,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dlabel_c4=DirectLabel(parent=canvas_1,text='G (0 to 1): ',pos=(-0.7,1,0.55),scale=0.06,text_align=TextNode.ACenter,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dlabel_c5=DirectLabel(parent=canvas_1,text='B (0 to 1): ',pos=(-0.7,1,0.45),scale=0.06,text_align=TextNode.ACenter,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        
        self.dentry_c6 = DirectEntry(parent=canvas_1,text = "", scale=0.06,width=10,pos=(-0.35, 1,0.65), command=self.SetEntryText_c6,initialText="0.1", numLines = 1, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dentry_c7 = DirectEntry(parent=canvas_1,text = "", scale=0.06,width=10,pos=(-0.35, 1,0.55), command=self.SetEntryText_c7,initialText="0.1", numLines = 1, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dentry_c8 = DirectEntry(parent=canvas_1,text = "", scale=0.06,width=10,pos=(-0.35, 1,0.45), command=self.SetEntryText_c8,initialText="0.1", numLines = 1, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)

        self.dlabel_c9 = DirectLabel(parent=canvas_1,text='Directional light(sun): intensity',pos=(-0.8,1,0.35),scale=0.06,text_align=TextNode.ACenter,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dentry_c10 = DirectEntry(parent=canvas_1,text = "", scale=0.06,width=10,pos=(-0.3, 1,0.35), command=self.SetEntryText_c10,initialText="1", numLines = 1, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        
        self.dlabel_c11=DirectLabel(parent=canvas_1,text='R (0 to 1): ',pos=(-0.7,1,0.25),scale=0.06,text_align=TextNode.ACenter,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dlabel_c12=DirectLabel(parent=canvas_1,text='G (0 to 1): ',pos=(-0.7,1,0.15),scale=0.06,text_align=TextNode.ACenter,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dlabel_c13=DirectLabel(parent=canvas_1,text='B (0 to 1): ',pos=(-0.7,1,0.05),scale=0.06,text_align=TextNode.ACenter,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        
        self.dentry_c14 = DirectEntry(parent=canvas_1,text = "", scale=0.06,width=10,pos=(-0.35, 1,0.25), command=self.SetEntryText_c14,initialText="1", numLines = 1, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dentry_c15 = DirectEntry(parent=canvas_1,text = "", scale=0.06,width=10,pos=(-0.35, 1,0.15), command=self.SetEntryText_c15,initialText="1", numLines = 1, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dentry_c16 = DirectEntry(parent=canvas_1,text = "", scale=0.06,width=10,pos=(-0.35, 1,0.05), command=self.SetEntryText_c16,initialText="1", numLines = 1, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)

        self.dlabel_c17=DirectLabel(parent=canvas_1,text='H (0 to 360): ',pos=(-0.7,1,-0.05),scale=0.06,text_align=TextNode.ACenter,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dlabel_c18=DirectLabel(parent=canvas_1,text='P (0 to 360): ',pos=(-0.7,1,-0.15),scale=0.06,text_align=TextNode.ACenter,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dlabel_c19=DirectLabel(parent=canvas_1,text='R (0 to 360): ',pos=(-0.7,1,-0.25),scale=0.06,text_align=TextNode.ACenter,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        
        self.dentry_c20 = DirectEntry(parent=canvas_1,text = "", scale=0.06,width=10,pos=(-0.35, 1,-0.05), command=self.SetEntryText_c20,initialText="0", numLines = 1, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dentry_c21 = DirectEntry(parent=canvas_1,text = "", scale=0.06,width=10,pos=(-0.35, 1,-0.15), command=self.SetEntryText_c21,initialText="0", numLines = 1, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dentry_c22 = DirectEntry(parent=canvas_1,text = "", scale=0.06,width=10,pos=(-0.35, 1,-0.25), command=self.SetEntryText_c22,initialText="0", numLines = 1, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)

        self.dlabel_c23=DirectLabel(parent=canvas_1,text='X: ',pos=(-1.3,1,-0.35),scale=0.06,text_align=TextNode.ACenter,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dentry_c24 = DirectEntry(parent=canvas_1,text = "", scale=0.06,width=8,pos=(-1.25, 1,-0.35), command=self.SetEntryText_c24,initialText="0", numLines = 1, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_c25=DirectLabel(parent=canvas_1,text='Y: ',pos=(-0.6,1,-0.35),scale=0.06,text_align=TextNode.ACenter,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dentry_c26 = DirectEntry(parent=canvas_1,text = "", scale=0.06,width=8,pos=(-0.55, 1,-0.35), command=self.SetEntryText_c26,initialText="0", numLines = 1, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_c27=DirectLabel(parent=canvas_1,text='Z: ',pos=(0.1,1,-0.35),scale=0.06,text_align=TextNode.ACenter,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dentry_c28 = DirectEntry(parent=canvas_1,text = "", scale=0.06,width=8,pos=(0.55, 1,-0.35), command=self.SetEntryText_c28,initialText="0", numLines = 1, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)

    def create_general_settings_gui(self):
        self.ScrolledFrame_d2=DirectScrolledFrame(
            canvasSize=(-2, 2, -2, 2),  # left, right, bottom, top
            frameSize=(-2, 2, -2, 2),
            pos=(0.1,0,0),
            #pos=(-0.35, 1,0.95)
            frameColor=(0.3, 0.3, 0.3, 0)
        )
        canvas_2=self.ScrolledFrame_d2.getCanvas()
        #self.daylight_adjuster_gui=DirectFrame(pos=(-1.35, 1,1),frameSize=(0,0.8,-0.9,0),frameColor=(0, 0, 0, 0.1))
        
        self.dlabel_d1 = DirectLabel(parent=canvas_2,text='Mouse Sensitivity (0-100,default 50): ',pos=(-1.1,1,0.75),scale=0.06,text_align=TextNode.ALeft,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dentry_d2 = DirectEntry(parent=canvas_2,text = "", scale=0.06,width=10,pos=(0.3, 1,0.75), command=self.SetEntryText_d1,initialText="50", numLines = 1, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_d3 = DirectLabel(parent=canvas_2,text='Move Speed (0-1,default 0.1): ',pos=(-1.1,1,0.65),scale=0.06,text_align=TextNode.ALeft,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dentry_d4 = DirectEntry(parent=canvas_2,text = "", scale=0.06,width=10,pos=(0.3, 1,0.65), command=self.SetEntryText_d4,initialText="0.1", numLines = 1, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.CheckButton_gs1 = DirectCheckButton(
            parent=canvas_2,
            text = " crosshair" ,
            text_align=TextNode.ALeft,
            scale=0.06,
            command=self.cbuttondef_gs1,
            pos=(-1.05, 1,0.55),
            frameColor=(0, 0, 0, 0.4),
            text_fg=(1, 1, 1, 0.9),
            indicatorValue=0
            )
        self.CheckButton_gs2 = DirectCheckButton(
            parent=canvas_2,
            text = " Show Gizmo" ,
            text_align=TextNode.ALeft,
            scale=0.06,
            command=self.cbuttondef_gs2,
            pos=(-1.05, 1,0.45),
            frameColor=(0, 0, 0, 0.4),
            text_fg=(1, 1, 1, 0.9),
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
            frameColor=(0, 0, 0, 0.2),
            pos=(-1.3, 0, 0.1),  # Position in 3D space (x, y, z)
            numItemsVisible=14,
            itemFrame_pos=(0, 0,0.4),  # Positions frame at top
            itemsAlign=TextNode.ALeft
        )
        self.scrolled_list_e1.reparentTo(self.ScrolledFrame_e1)
        
        label_slist_top = DirectLabel(
        parent=self.scrolled_list_e1,  # Parent to the scrolled list
        text="cursor over list and scroll",
        frameColor=(0, 0, 0, 0.3),
        scale=0.06,
        pos=(0, 0, 0.53),  # Position at top of list frame
        #frameColor=(0.3, 0.3, 0.5, 1),
        text_fg=(0.3, 0.3, 0.7, 1),
        #frameSize=(-0.5, 0.5, -0.1, 0.1),
        text_align=TextNode.ALeft
        #relief=DGG.RAISED
        )

        # Bind mouse wheel events
        self.accept("wheel_up", self.scroll_up)
        self.accept("wheel_down", self.scroll_down)

        # Track scroll index manually
        self.current_scroll_index = 0
        
        self.dlabel_e1=DirectLabel(parent=self.ScrolledFrame_e1.getCanvas(),text='SelectedLight: ',pos=(0.57,0,-0.4),scale=0.06,text_align=TextNode.ALeft,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dlabel_e2=DirectLabel(parent=self.ScrolledFrame_e1.getCanvas(),text='',pos=(1,0,-0.4),scale=0.06,text_align=TextNode.ALeft,text_fg=(0.7, 0.7, 1, 1),text_bg=(0,0,0,0.5),frameColor=(0, 0, 0, 0.2))
        self.dlabel_e3=DirectLabel(parent=self.ScrolledFrame_e1.getCanvas(),text='Overall Intensity: ',pos=(0.5,0,-0.5),scale=0.06,text_align=TextNode.ALeft,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dentry_e4 = DirectEntry(parent=self.ScrolledFrame_e1.getCanvas(),text = "",pos=(1, 0,-0.5), scale=0.06,width=8, command=self.SetEntryText_e,extraArgs=['Overall_Intensity'],initialText="1", numLines = 1, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_e5=DirectLabel(parent=self.ScrolledFrame_e1.getCanvas(),text='Intensity: ',pos=(0.5,0,-0.7),scale=0.06,text_align=TextNode.ALeft,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dentry_e6 = DirectEntry(parent=self.ScrolledFrame_e1.getCanvas(),text = "",pos=(0.8, 0,-0.7), scale=0.06,width=8, command=self.SetEntryText_e,extraArgs=['Intensity'],initialText="1", numLines = 1, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)

        self.dlabel_e7=DirectLabel(parent=self.ScrolledFrame_e1.getCanvas(),text='Color: ',pos=(0.5,0,-0.8),scale=0.06,text_align=TextNode.ALeft,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dlabel_e8=DirectLabel(parent=self.ScrolledFrame_e1.getCanvas(),text='R:',pos=(0.75,0,-0.8),scale=0.06,text_align=TextNode.ALeft,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dentry_e9 = DirectEntry(parent=self.ScrolledFrame_e1.getCanvas(),text = "",pos=(0.85, 0,-0.8), scale=0.06,width=4, command=self.SetEntryText_e,extraArgs=['R'],initialText="1", numLines = 1, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_e10=DirectLabel(parent=self.ScrolledFrame_e1.getCanvas(),text='G:',pos=(1.15,0,-0.8),scale=0.06,text_align=TextNode.ALeft,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dentry_e11 = DirectEntry(parent=self.ScrolledFrame_e1.getCanvas(),text = "",pos=(1.25, 0,-0.8), scale=0.06,width=4, command=self.SetEntryText_e,extraArgs=['G'],initialText="1", numLines = 1, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_e12=DirectLabel(parent=self.ScrolledFrame_e1.getCanvas(),text='B:',pos=(1.55,0,-0.8),scale=0.06,text_align=TextNode.ALeft,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dentry_e13 = DirectEntry(parent=self.ScrolledFrame_e1.getCanvas(),text = "",pos=(1.65, 0,-0.8), scale=0.06,width=4, command=self.SetEntryText_e,extraArgs=['B'],initialText="1", numLines = 1, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        
        self.dlabel_e14=DirectLabel(parent=self.ScrolledFrame_e1.getCanvas(),text='Attenuation: ',pos=(0.5,0,-0.9),scale=0.06,text_align=TextNode.ALeft,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dlabel_e15=DirectLabel(parent=self.ScrolledFrame_e1.getCanvas(),text='C:',pos=(0.9,0,-0.9),scale=0.06,text_align=TextNode.ALeft,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dentry_e16 = DirectEntry(parent=self.ScrolledFrame_e1.getCanvas(),text = "",pos=(1, 0,-0.9), scale=0.06,width=4, command=self.SetEntryText_e,extraArgs=['C'],initialText="1", numLines = 1, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_e17=DirectLabel(parent=self.ScrolledFrame_e1.getCanvas(),text='L:',pos=(1.3,0,-0.9),scale=0.06,text_align=TextNode.ALeft,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dentry_e18 = DirectEntry(parent=self.ScrolledFrame_e1.getCanvas(),text = "",pos=(1.4, 0,-0.9), scale=0.06,width=4, command=self.SetEntryText_e,extraArgs=['L'],initialText="1", numLines = 1, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        self.dlabel_e19=DirectLabel(parent=self.ScrolledFrame_e1.getCanvas(),text='Q:',pos=(1.7,0,-0.9),scale=0.06,text_align=TextNode.ALeft,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dentry_e20 = DirectEntry(parent=self.ScrolledFrame_e1.getCanvas(),text = "",pos=(1.8, 0,-0.9), scale=0.06,width=4, command=self.SetEntryText_e,extraArgs=['Q'],initialText="1", numLines = 1, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)

        self.dlabel_e21=DirectLabel(parent=self.ScrolledFrame_e1.getCanvas(),text='Notes:',pos=(0.5,0,-1),scale=0.06,text_align=TextNode.ALeft,text_fg=(1, 1, 1, 0.9),text_bg=(0,0,0,0.3),frameColor=(0, 0, 0, 0.2))
        self.dentry_e22 = DirectEntry(parent=self.ScrolledFrame_e1.getCanvas(),text = "",pos=(0.7, 0,-1), scale=0.06,width=25, command=self.SetEntryText_e,extraArgs=['Notes'],initialText="", numLines = 1, focus=0,frameColor=(0,0,0,0.3),text_fg=(1, 1, 1, 0.9),focusInCommand=self.focusInDef,focusOutCommand=self.focusOutDef)
        
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
            self.models_all[self.current_model_index].reparentTo(self.render)
            self.load_model_from_param(fileload_flag=False,indexload_flag=True)
            self.load_model_values_to_gui()
            self.makeup_lights_gui()
        else:
            self.data_all[self.current_model_index]['enable']=False
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
            
    def cbuttondef_gs1(self,status):
        if status:
            self.crosshair.show()
        else:
            self.crosshair.hide()

    def cbuttondef_gs2(self,status):
        if status:
            self.gizmo.show()
        else:
            self.gizmo.hide()

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

    def SetEntryText_c1(self,textEntered):
        try:
            self.ambientLight_Intensity=float(textEntered)
            cur_color=self.ambientLight.getColor()
            self.ambientLight.setColor((self.ambientLight_Intensity,self.ambientLight_Intensity,self.ambientLight_Intensity, 1))
            self.dentry_c6.enterText(str(self.ambientLight_Intensity))
            self.dentry_c7.enterText(str(self.ambientLight_Intensity))
            self.dentry_c8.enterText(str(self.ambientLight_Intensity))
        except ValueError:
            print('value entered in entry c1 is not number')

    def SetEntryText_d1(self,textEntered):
        try:
            self.mouse_sensitivity=float(textEntered)
        except ValueError:
            print('value entered in entry d1 is not number')

    def SetEntryText_d4(self,textEntered):
        try:
            self.move_speed=float(textEntered)
        except ValueError:
            print('value entered in entry d4 is not number')
            
    def SetEntryText_c6(self,textEntered):
        try:
            self.dentry_c6.enterText(textEntered)
            cur_color=self.ambientLight.getColor()
            self.ambientLight.setColor((float(textEntered),cur_color[1],cur_color[2], 1))
        except ValueError:
            print('value entered in entry6 is not number')

    def SetEntryText_c7(self,textEntered):
        try:
            self.dentry_c7.enterText(textEntered)
            cur_color=self.ambientLight.getColor()
            self.ambientLight.setColor((cur_color[0],float(textEntered),cur_color[2], 1))
        except ValueError:
            print('value entered in entry7 is not number')

    def SetEntryText_c8(self,textEntered):
        try:
            self.dentry_c8.enterText(textEntered)
            cur_color=self.ambientLight.getColor()
            self.ambientLight.setColor((cur_color[0],cur_color[1],float(textEntered), 1))
        except ValueError:
            print('value entered in entry8 is not number')            

    def SetEntryText_c10(self,textEntered):
        try:
            self.directionalLight_intensity=float(textEntered)
            cur_color=self.directionalLight.getColor()
            self.directionalLight.setColor((self.directionalLight_intensity,self.directionalLight_intensity,self.directionalLight_intensity, 1))
            self.dentry_c14.enterText(str(self.directionalLight_intensity))
            self.dentry_c15.enterText(str(self.directionalLight_intensity))
            self.dentry_c16.enterText(str(self.directionalLight_intensity))
        except ValueError:
            print('value entered in entry c1 is not number')

    def SetEntryText_c14(self,textEntered):
        try:
            self.dentry_c14.enterText(textEntered)
            cur_color=self.directionalLight.getColor()
            self.directionalLight.setColor((float(textEntered),cur_color[1],cur_color[2], 1))
        except ValueError:
            print('value entered in entry is not number')

    def SetEntryText_c15(self,textEntered):
        try:
            self.dentry_c15.enterText(textEntered)
            cur_color=self.directionalLight.getColor()
            self.directionalLight.setColor((cur_color[0],float(textEntered),cur_color[2], 1))
        except ValueError:
            print('value entered in entry is not number')

    def SetEntryText_c16(self,textEntered):
        try:
            self.dentry_c16.enterText(textEntered)
            cur_color=self.directionalLight.getColor()
            self.directionalLight.setColor((cur_color[0],cur_color[1],float(textEntered), 1))
        except ValueError:
            print('value entered in entry is not number')            

    def SetEntryText_c20(self,textEntered):
        try:
            self.dentry_c20.enterText(textEntered)
            cur_color=self.dlight1.getHpr()
            self.dlight1.setHpr(float(textEntered),cur_color[1],cur_color[2])
        except ValueError:
            print('value entered in entry is not number')

    def SetEntryText_c21(self,textEntered):
        try:
            self.dentry_c21.enterText(textEntered)
            cur_color=self.dlight1.getHpr()
            self.dlight1.setHpr(cur_color[0],float(textEntered),cur_color[2])
        except ValueError:
            print('value entered in entry is not number')

    def SetEntryText_c22(self,textEntered):
        try:
            self.dentry_c22.enterText(textEntered)
            cur_color=self.dlight1.getHpr()
            self.dlight1.setHpr(cur_color[0],cur_color[1],float(textEntered))
        except ValueError:
            print('value entered in entry is not number')            

    def SetEntryText_c24(self,textEntered):
        try:
            self.dentry_c24.enterText(textEntered)
            cur_color=self.dlight1.getPos()
            self.dlight1.setPos(float(textEntered),cur_color[1],cur_color[2])
        except ValueError:
            print('value entered in entry is not number')

    def SetEntryText_c26(self,textEntered):
        try:
            self.dentry_c26.enterText(textEntered)
            cur_color=self.dlight1.getPos()
            self.dlight1.setPos(cur_color[0],float(textEntered),cur_color[2])
        except ValueError:
            print('value entered in entry is not number')

    def SetEntryText_c28(self,textEntered):
        try:
            self.dentry_c28.enterText(textEntered)
            cur_color=self.dlight1.getPos()
            self.dlight1.setPos(cur_color[0],cur_color[1],float(textEntered))
        except ValueError:
            print('value entered in entry is not number')            

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

    def SetEntryText_4(self,textEntered):
        try:
                                                                             
            self.dentry_3.enterText(textEntered)
            self.data_all[self.current_model_index]['uniquename']=textEntered
            self.models_names_all[self.current_model_index]=textEntered
            self.menu_2['items']=self.models_names_all
            #self.menu_2.set(self.current_model_index)
        except:
            print('error in entry4')

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
        if 1:
        #try:
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
        else:
        #except:
            print('error in entry_e')

    def focusInDef(self):
        self.ignoreAll()
        self.accept('escape', sys.exit)
        
    def focusInDef2(self):
        print('hh')

    def focusOutDef(self):
        self.set_keymap()

    def ButtonDef_1(self):
        shutil.copyfile(self.scene_data_filename, self.scene_data_backup_filename)
        try:
            with open(self.scene_data_filename, 'w', encoding='utf-8') as f:
                json.dump(self.data_all, f, ensure_ascii=False, indent=4)
            print('json saved')
            now = datetime.datetime.now()
            self.dlabel_status2['text']=now.strftime('%d-%m-%y %H:%M:%S ')+'json saved.'
        except:
            shutil.copyfile(self.scene_data_backup_filename, self.scene_data_filename)
            print('json save error')
            now = datetime.datetime.now()
            self.dlabel_status2['text']=now.strftime('%d-%m-%y %H:%M:%S ')+'error while saving json file.'
        # saving lights json
        shutil.copyfile(self.scene_light_data_filename, self.scene_light_data_backup_filename)
        try:
            with open(self.scene_light_data_filename, 'w', encoding='utf-8') as f:
                json.dump(self.data_all_light, f, ensure_ascii=False, indent=4)
            print('json saved(light data)')
            now = datetime.datetime.now()
            self.dlabel_status2['text']=now.strftime('%d-%m-%y %H:%M:%S ')+'json saved(light data).'
        except:
            shutil.copyfile(self.scene_light_data_backup_filename, self.scene_light_data_filename)
            print('json save error')
            now = datetime.datetime.now()
            self.dlabel_status2['text']=now.strftime('%d-%m-%y %H:%M:%S ')+'error while saving json file.'

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
        #self.menu_2['items']=self.models_names_all
        #self.menu_2.set(self.current_model_index)
        self.load_model_values_to_gui()
        self.makeup_lights_gui()

    def DialogDef_1(self,arg):
        if arg:
            try:
                del self.models_names_all[self.current_model_index]
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
                    del self.models_light_node_all[idx]
                self.current_model_index-=1
                if self.current_model_index<0: self.current_model_index=0
                self.menu_2['items']=self.models_names_all
                self.menu_2.set(self.current_model_index)
                self.dlabel_status2['text']=datetime.datetime.now().strftime('%d-%m-%y %H:%M:%S ')+'current model deleted.'
                self.dialog_1.cleanup()
                print('deleted.')
            except KeyError:
                print('error while deleting the model.')
                self.dlabel_status2['text']=datetime.datetime.now().strftime('%d-%m-%y %H:%M:%S ')+'error while deleting current model.'
                self.dialog_1.cleanup()
                pass
        else:
            print('model not deleted.')
            self.dlabel_status2['text']=datetime.datetime.now().strftime('%d-%m-%y %H:%M:%S ')+'current model not deleted. (option NO selected?)'
            self.dialog_1.cleanup()
        
    def load_environment_models(self):
        json_file=self.scene_data_filename
        with open(json_file) as json_data:
            self.data_all = json.load(json_data)
        
        with open(self.scene_light_data_filename) as json_data:
            self.data_all_light = json.load(json_data)
            
        self.models_all=[]
        self.models_names_all=[]
        self.models_names_enabled=[]
        self.ModelTemp=""
        #self.data_all_light=[]
        self.models_with_lights=[]
        for dobj in self.data_all_light:
            self.models_with_lights.append(dobj["uniquename"])
        self.models_light_names=[]
        self.models_light_all=[]
        self.models_light_node_all=[]
        for i in range(len(self.data_all)):
            data=self.data_all[i]
            self.models_names_all.append(data["uniquename"])
            if data["enable"]:
                self.ModelTemp=loader.loadModel(data["filename"])
                #--- uncomment the below code to load the point lights from model and use save button to save the params
                #(param_2,light_name_list,light_list,light_node_list)=self.get_point_light_properties_from_model(self.ModelTemp,data)
                #if len(param_2)>0:
                #    self.data_all_light.append(param_2.copy())
                if data["uniquename"] in self.models_with_lights:
                    idx=self.models_with_lights.index(data["uniquename"])
                    (self.param_2,self.light_name_list,self.light_list,self.light_node_list)=self.get_point_light_properties_from_model(self.ModelTemp,data)
                    if len(self.param_2)>0:
                        if self.load_lights_from_json==True:
                            #tempidx=self.current_light_model_index
                            self.current_light_model_index=idx
                            #print(idx)
                            #tempidx2=self.plight_idx
                            for j2 in range(len(self.light_name_list)):
                                idx2=j2
                                self.plight_idx=j2
                                self.SetEntryText_e(self.data_all_light[idx]['plights'][idx2]['color'][1][0],'R')
                                self.SetEntryText_e(self.data_all_light[idx]['plights'][idx2]['color'][1][1],'G')
                                self.SetEntryText_e(self.data_all_light[idx]['plights'][idx2]['color'][1][2],'B')
                                self.SetEntryText_e(self.data_all_light[idx]['plights'][idx2]['attenuation'][1][0],'C')
                                self.SetEntryText_e(self.data_all_light[idx]['plights'][idx2]['attenuation'][1][0],'L')
                                self.SetEntryText_e(self.data_all_light[idx]['plights'][idx2]['attenuation'][1][0],'Q')
                        #self.data_all_light.append(param_2.copy())
                        #self.models_with_lights.append(data["uniquename"])
                        self.models_light_names.append(self.light_name_list)
                        self.models_light_all.append(self.light_list)
                        self.models_light_node_all.append(self.light_node_list)
                        for tmp in self.light_node_list:
                            self.render.setLight(tmp)
                        
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
                
                self.models_all.append(self.ModelTemp)
                self.models_all[-1].reparentTo(self.render)
                if data['show']==True:
                    self.models_all[-1].show()
                else:
                    self.models_all[-1].hide()
            else:
                self.models_all.append("")
        

    def set_keymap(self):
        self.keyMap = {"move_forward": 0, "move_backward": 0, "move_left": 0, "move_right": 0,"gravity_on":0,"load_model":0,"set_camera_pos":0,"x_increase":0,"x_decrease":0,"y_increase":0,"y_decrease":0,"z_increase":0,"z_decrease":0,"right_click":0,"switch_model":0,"delete_model":0,"up_arrow":0,"down_arrow":0,"right_arrow":0,"left_arrow":0,"look_at":0,"show_gui":1}
        self.accept('escape', sys.exit)
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
            data=self.data_all[self.current_model_index]['scale'][1]
        if self.current_property==3:
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
        if self.current_property==4:
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
            #self.load_model_from_param(fileload_flag=False,indexload_flag=True)
            #self.load_model_values_to_gui()
            self.menu_2.set(self.current_model_index)#it will trigger the DirectOptionMenu function
        elif key=="load_model":
            print('open a model to load')
            self.keyMap['load_model']=False
            #print(self.camera.getPos())
            len_curdir=len(os.getcwd())+1
            root = tk.Tk()
            openedfilename=askopenfilename(title="open the model file",initialdir=".",filetypes=[("model files", ".gltf .glb .egg .bam"),("All files", "*.*")])
            root.destroy()
            if len(openedfilename)>0:
                modelfilepath=openedfilename[len_curdir:]
                if modelfilepath[0]=='/': modelfilepath=modelfilepath[1:]
                if modelfilepath[0]=='\\': modelfilepath=modelfilepath[1:]         
                tempname=modelfilepath
                tempname=tempname.replace('/','_')
                tempname=tempname.replace('\\','_')
                self.param_1={}
                self.param_1['uniquename']=tempname+' '+datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%S')
                self.param_1['filename']=modelfilepath
                self.param_1['enable']=True
                self.param_1['show']=True
                tempos=self.get_an_point_front_of_camera(0,self.camera.getH(),self.camera.getP())
                
                #tempp=self.cam_node.getPos()
                #print(tempp)
                #tempos=[0,0,0]
                self.param_1['pos']=[True,tempos]
                self.param_1['scale']=[False,[0,0,0]]
                self.param_1['color']=[False,[0,0,0,1]]
                self.param_1['hpr']=[False,[0,0,0]]
                self.param_1['details']=""
                self.param_1['notes']=""
                self.param_1['pickable']=[True, ""]
                self.param_1['enable_lights_from_model']=[False, ""]
                self.param_1['load_lights_from_json']=[True, ""]
                self.load_model_from_param(fileload_flag=True,indexload_flag=False)
                self.load_model_values_to_gui()
                self.menu_2['items']=self.models_names_all
                self.menu_2.set(self.current_model_index)
                print('model loaded')
                self.dlabel_status2['text']=datetime.datetime.now().strftime('%d-%m-%y %H:%M:%S ')+'model file loaded.'
            else:
                print('opened file name empty')
                self.dlabel_status2['text']=datetime.datetime.now().strftime('%d-%m-%y %H:%M:%S ')+'model file not loaded.'
        elif key=="delete_model":
            print('delete pressed.')
            self.dialog_1 = YesNoDialog(dialogName="YesNoCancelDialog", text="Delete the current model?",
                     command=self.DialogDef_1)
        else:
            self.keyMap[key] = value

    def load_model_values_to_gui(self):
        if self.current_property==1:
            data=self.data_all[self.current_model_index]['pos'][1]
        if self.current_property==2:
            data=self.data_all[self.current_model_index]['scale'][1]
        if self.current_property==3:
            data=self.data_all[self.current_model_index]['color'][1]
        if self.current_property==4:
            data=self.data_all[self.current_model_index]['hpr'][1]
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

        
    def setupLights(self):  # Sets up some default lighting
        self.ambientLight = AmbientLight("ambientLight")
        self.ambientLight_Intensity=0.3
        self.ambientLight.setColor((self.ambientLight_Intensity,self.ambientLight_Intensity,self.ambientLight_Intensity, 1))
        self.render.setLight(self.render.attachNewNode(self.ambientLight))
        self.directionalLight = DirectionalLight("directionalLight_1")
        self.directionalLight_intensity=5
        self.directionalLight.setColor((self.directionalLight_intensity,self.directionalLight_intensity,self.directionalLight_intensity, 1))
        #self.directionalLight.setSpecularColor((.1, .1, .1, .1))
        self.directionalLight.setShadowCaster(True, 512, 512)
        self.dlight1=self.render.attachNewNode(self.directionalLight)
        self.dlight1.setHpr(0, -45, 0)
        self.dlight1.setPos(0,0,20)
        #self.dlight1.look_at(0, 0, 0)
        
        self.suncube = loader.loadModel("cube_arrow.glb")
        self.suncube.reparentTo(self.dlight1)
        self.suncube.setScale(1.5,1.5,1.5)
        #self.suncube.setPos(10,10,20)
        #self.suncube.setHpr(0, -45, 0)
        #self.environ1.set_shader(self.shader)               

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
                mouse = self.win.getPointer(0)
                mx, my = mouse.getX(), mouse.getY()
                # Reset mouse to center to prevent edge stopping
                self.win.movePointer(0, int(800 / 2), int(600 / 2))
                #self.win.movePointer(0, int(self.win.getXSize() / 2), int(self.win.getYSize() / 2))

                # Calculate mouse delta
                dx = mx - 800 / 2
                dy = my - 600 / 2

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
            self.dlabel_status2['text']=datetime.datetime.now().strftime('%d-%m-%y %H:%M:%S ')+'camera position is set to center of current model.'
            
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
                if self.current_property==4:
                    cval=self.models_all[self.current_model_index].getH()+1
                    if cval>360: cval=0
                    self.models_all[self.current_model_index].setH(cval)
                    self.data_all[self.current_model_index]['hpr'][1][0]=cval
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
                if self.current_property==4:
                    cval=self.models_all[self.current_model_index].getH()-1
                    if cval<0: cval=360
                    self.models_all[self.current_model_index].setH(cval)
                    self.data_all[self.current_model_index]['hpr'][1][0]=cval
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
                if self.current_property==4:
                    cval=self.models_all[self.current_model_index].getP()+1
                    if cval>360: cval=0
                    self.models_all[self.current_model_index].setP(cval)
                    self.data_all[self.current_model_index]['hpr'][1][1]=cval
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
                if self.current_property==4:
                    cval=self.models_all[self.current_model_index].getP()-1
                    if cval<0: cval=360
                    self.models_all[self.current_model_index].setP(cval)
                    self.data_all[self.current_model_index]['hpr'][1][1]=cval
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
                if self.current_property==4:
                    cval=self.models_all[self.current_model_index].getR()+1
                    if cval>360: cval=0
                    self.models_all[self.current_model_index].setR(cval)
                    self.data_all[self.current_model_index]['hpr'][1][2]=cval
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
                if self.current_property==4:
                    cval=self.models_all[self.current_model_index].getR()-1
                    if cval<0: cval=360
                    self.models_all[self.current_model_index].setR(cval)
                    self.data_all[self.current_model_index]['hpr'][1][2]=cval
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
            fileload_flag=True
            indexload_flag=False
            self.current_model_index=len(self.models_names_all)-1
        else:
            if indexload_flag==True:
                fileload_flag=False
                print('model file loading from index going to happen.')
                self.dlabel_status2['text']=datetime.datetime.now().strftime('%d-%m-%y %H:%M:%S ')+'model file is loading... (using index)'
            else:
                if fileload_flag==False:
                    indexload_flag==True
                    print('model file loading from index going to happen.')
                    self.dlabel_status2['text']=datetime.datetime.now().strftime('%d-%m-%y %H:%M:%S ')+'model file is loading... (using index)'
                else:
                    print('model file loading from disk going to happen.')
                    self.dlabel_status2['text']=datetime.datetime.now().strftime('%d-%m-%y %H:%M:%S ')+'model file is loading... (from drive)'
            
        if self.param_1['enable']==True:
            if fileload_flag==True:
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
                self.models_all[-1].reparentTo(self.render)
            if indexload_flag==True:
                self.data_all[self.current_model_index]['show']=True
                self.models_all[self.current_model_index].show()
            
            postemp=self.ModelTemp.getPos()
            self.gizmo.reparentTo(self.ModelTemp)
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
            if indexload_flag==True:
                if type(self.models_all[self.current_model_index])==type(NodePath()):
                    self.data_all[self.current_model_index]['show']=False
                    self.models_all[self.current_model_index].hide()


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
                    cur_scale[1]=value
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
                if self.current_property==4:
                    cval=value
                    if cval>360: cval=0
                    self.models_all[self.current_model_index].setH(cval)
                    self.data_all[self.current_model_index]['hpr'][1][0]=cval
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
                if self.current_property==3:
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
                if self.current_property==4:
                    cval=value
                    if cval>360: cval=0
                    self.models_all[self.current_model_index].setP(cval)
                    self.data_all[self.current_model_index]['hpr'][1][1]=cval
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
                if self.current_property==3:
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
                if self.current_property==4:
                    cval=value
                    if cval>360: cval=0
                    self.models_all[self.current_model_index].setR(cval)
                    self.data_all[self.current_model_index]['hpr'][1][2]=cval
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
            print("Found Point Lights: ",data['filename'])
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
            frame = DirectFrame(frameSize=(0, 0.7, -0.05, 0.05),frameColor=(0, 0, 0, 0.2))

            # Add label
            label = DirectLabel(
                parent=frame,
                text=f"{i+1}. ",
                scale=0.05,
                text_fg=(1, 1, 1, 0.9),
                frameColor=(0, 0, 0, 0.3),
                pos=(0, 0, 0),
                text_align=TextNode.ALeft
            )

            # Add button
            button = DirectButton(
                parent=frame,
                text=self.light_name_list[i],
                text_fg=(1, 1, 1, 0.9),
                scale=0.05,
                pos=(0.1, 0, 0),
                command=self.on_item_click,
                frameColor=(0, 0, 0, 0.3),
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
        button["frameColor"] = (0, 0, 0, 0.3)
            
    def is_mouse_over_list(self):
        if not base.mouseWatcherNode.hasMouse():
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
        
    def LightItem_func(self):
        pass#print(i)

    def scroll_up(self):
        if self.is_mouse_over_list():
            if self.current_scroll_index > 0:
                self.current_scroll_index -= 1
                self.scrolled_list_e1.scrollTo(self.current_scroll_index)
                print("Scroll Up Triggered | Index:", self.current_scroll_index)
        else:
            print("Scroll Up Ignored - Mouse outside list")

    def scroll_down(self):
        if self.is_mouse_over_list():
            max_index = len(self.scrolled_list_e1['items']) - self.scrolled_list_e1['numItemsVisible']
            if self.current_scroll_index < max_index:
                self.current_scroll_index += 1
                self.scrolled_list_e1.scrollTo(self.current_scroll_index)
                print("Scroll Down Triggered | Index:", self.current_scroll_index)
        else:
            print("Scroll Down Ignored - Mouse outside list")


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

Scene_1=SceneMakerMain()
Scene_1.run()


