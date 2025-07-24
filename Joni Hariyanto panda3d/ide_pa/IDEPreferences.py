import os, pickle, _thread, string, urllib.request, urllib.parse, urllib.error, zipfile, wx, wx.animate
from wx.lib.colourselect import ColourSelect, EVT_COLOURSELECT
from direct.showbase.PythonUtil import Functor
from wx.lib.intctrl import IntCtrl
from copy import copy, deepcopy
from IDE import IDE_CFG_DESC, IDE_CFG_TIP, DocumentSpec, Filename, HTTPClient 
from IDEwxExt import *
import IDE


class KeyMap:
  WHEEL_UP='wheelup'
  WHEEL_DN='wheeldown'
  EventKeys={
    ('Shift','shift'):[wx.WXK_SHIFT],
    (IDE.wxCtrl,IDE.Ctrl):[wx.WXK_CONTROL],
    ('Alt','alt'):[wx.WXK_ALT],
    ('WheelUp','wheel_up'):[WHEEL_UP],
    ('WheelDown','wheel_down'):[WHEEL_DN],
    ('LeftClick','mouse1'):[wx.MOUSE_BTN_LEFT],
    ('MiddleClick','mouse2'):[wx.MOUSE_BTN_MIDDLE],
    ('RightClick','mouse3'):[wx.MOUSE_BTN_RIGHT],
    ('Tab','tab'):[wx.WXK_TAB],
    ('Space','space'):[wx.WXK_SPACE],
    ('Backspace','backspace'):[wx.WXK_BACK],
    ('Delete','delete'):[wx.WXK_DELETE,wx.WXK_NUMPAD_DELETE],
    ('Insert','insert'):[wx.WXK_INSERT,wx.WXK_NUMPAD_INSERT],
    ('Home','home'):[wx.WXK_HOME,wx.WXK_NUMPAD_HOME],
    ('End','end'):[wx.WXK_END,wx.WXK_NUMPAD_END],
    ('PageUp','page_up'):[wx.WXK_PAGEUP,wx.WXK_NUMPAD_PAGEUP],
    ('PageDown','page_down'):[wx.WXK_PAGEDOWN,wx.WXK_NUMPAD_PAGEDOWN],
    ('Left','arrow_left'):[wx.WXK_LEFT,wx.WXK_NUMPAD_LEFT],
    ('Right','arrow_right'):[wx.WXK_RIGHT,wx.WXK_NUMPAD_RIGHT],
    ('Up','arrow_up'):[wx.WXK_UP,wx.WXK_NUMPAD_UP],
    ('Down','arrow_down'):[wx.WXK_DOWN,wx.WXK_NUMPAD_DOWN],
    ('Enter','enter'):[wx.WXK_RETURN,wx.WXK_NUMPAD_ENTER],
    ('.','.'):[wx.WXK_NUMPAD_DECIMAL,ord('.')],
    ('*','*'):[wx.WXK_NUMPAD_MULTIPLY],
    ('/','/'):[wx.WXK_NUMPAD_DIVIDE,ord('/')],
    ('-','-'):[wx.WXK_NUMPAD_SUBTRACT,ord('-')],
    ('+','+'):[wx.WXK_NUMPAD_ADD],
    # On Windows, equal sign (=) and leftquote (`) are shifted up.
    # Not sure what causes this, just translate them back.
    ('=','='):[ord('+'),ord('=')],
    ('`','`'):[ord('`'),ord('~')],
    ('PrintScreen','print_screen'):[wx.WXK_PRINT],
    ('ScrollLOCK','scroll_lock'):[wx.WXK_SCROLL],
    ('CapsLOCK','caps_lock'):[wx.WXK_CAPITAL],
    ('NumLOCK','num_lock'):[wx.WXK_NUMLOCK],
    ('Escape','escape'):[wx.WXK_ESCAPE],
    ('Pause','pause'):[wx.WXK_PAUSE],
  }
  KeyName={}
  for e,keys in list(EventKeys.items()):
      for k in keys:
          KeyName[k]=e
  chars=string.uppercase+string.digits+r",;'\[]"
  charsOrd=[ord(c) for c in chars]
  for c in chars:
      KeyName[ord(c)]=[c,c.lower()]
  for f in range(16):
      KeyName[wx.WXK_F1+f]=['F%s'%(f+1),'f%s'%(f+1)]
  for d in string.digits:
      KeyName[getattr(wx,'WXK_NUMPAD%s'%d)]=[d]*2

  P3D2key = dict([reversed(v) for v in list(KeyName.values())])
  keysSep=' '
  value=[]
  wxModKeys = [wx.WXK_SHIFT,wx.WXK_CONTROL,wx.WXK_ALT]
  altered = charsOrd + [ord(c) for c in './-=+`~'] +\
    list(range(wx.WXK_NUMPAD0,wx.WXK_NUMPAD9+1)) + [
    wx.WXK_NUMPAD_ADD,wx.WXK_NUMPAD_SUBTRACT,wx.WXK_NUMPAD_MULTIPLY,
    wx.WXK_NUMPAD_DIVIDE,wx.WXK_NUMPAD_DECIMAL, wx.WXK_SPACE,
    wx.WXK_NUMLOCK, wx.WXK_CAPITAL,
    ]

  def reset(self):
      self.value=[]

  def getMods(self,e):
      mods=[]
      if e.ShiftDown(): mods.append(wx.WXK_SHIFT)
      if IDE.MAC:
         if e.MetaDown(): mods.append(wx.WXK_CONTROL)
      else:
         if e.ControlDown(): mods.append(wx.WXK_CONTROL)
      if e.AltDown(): mods.append(wx.WXK_ALT)
      return mods

  def clearKey(self,e):
      if not self.value:
         e.EventObject.SetValue('None')
         updateKeyStatus()

  def setKey(self,e):
      if type(e)==wx.MouseEvent:
         kc=e.Button
         if kc: # mouse click !
            e.EventObject.SetFocus()
         else:
            wheelRot=e.GetWheelRotation()
            if wheelRot:
               up=wheelRot>0
               mods=self.getMods(e)
               self.value=mods+[self.WHEEL_UP if up else self.WHEEL_DN]
               e.EventObject.SetValue(self.keysSep.join([self.KeyName[k][0] for k in self.value]))
               updateKeyStatus()
            return
      else:
         kc=e.GetKeyCode()
#       e.Skip()
#       print kc
      newVal=[]
      mods=self.getMods(e)
      validKey=1
      if kc not in self.wxModKeys:
         if kc in self.KeyName:
            if (not mods or (len(mods)==1 and mods[0]==wx.WXK_SHIFT)) and kc in self.altered:
               mods=[wx.WXK_ALT]
         else:
            validKey=0
         if validKey:
            newVal.append(kc)
      TC=e.GetEventObject()
      if not newVal:
         if validKey:
            if self.WHEEL_UP in self.value or\
               self.WHEEL_DN in self.value or\
               wx.MOUSE_BTN_LEFT in self.value or\
               wx.MOUSE_BTN_MIDDLE in self.value or\
               wx.MOUSE_BTN_RIGHT in self.value:
               return
            TC.SetValue(self.keysSep.join([self.KeyName[k][0] for k in mods]))
         else:
            TC.SetValue('None')
         self.value=[]
      elif self.value!=mods+newVal:
         self.value=mods+newVal
         TC.SetValue(self.keysSep.join([self.KeyName[k][0] for k in self.value]))
      updateKeyStatus()

  def getP3Devent(self,e=None):
      P3Devent='-'.join([self.KeyName[k][1] for k in self.value])
#       print>>IDE.IDE_DEV, P3Devent
      return P3Devent

KM = KeyMap()
CAT_NAME = {
  IDE.AC_gen:'General',
  IDE.AC_doc:'Document',
  IDE.AC_edit:'Editing',
  IDE.AC_comp:'Completion',
  IDE.AC_mark:'Bookmark',
  IDE.AC_macro:'Macro',
  IDE.AC_search:'Search',
  IDE.AC_scene:'Scene',
}
CAT_ID = dict( [reversed(v) for v in list(CAT_NAME.items())] )
PREF_OPEN = False
RESET_CAM = 'resetCamTransform'
UPGRADE_NOW = 'Upgrade now'
AVAIL_UPGRADES = 'Available upgrades :'
DOWNLOADING_UPGRADES = 'Downloading :'
UPGRADES_SUCCESSFUL = 'Successfully installed :'
DOWNLOAD_ANIM = 'download animation'
DOWNLOAD_GAUGE_RANGE = 50
UPGRADE_OPT = {
  IDE.UPD_never:['never',0],
  IDE.UPD_daily:['daily',3600*24],
  IDE.UPD_weekly:['weekly',3600*24*7],
  IDE.UPD_monthly:['monthly',3600*24*30],
}
UPGRADE_SRV = {
  0:'panda3dprojects.com',
  1:'p3dp.com',
}

def drawSkins(tabpos,sliderpos,e):
    pdc = wx.PaintDC(e.EventObject)
    try:
        dc = wx.GCDC(pdc)
    except:
        dc = pdc

    loc=IDE.IDE_CFG[IDE.CFG_fileTabSkin]
    pos=tabpos
    size=32*.82
    labelWidth=50
    labelOffset=0
    totalWidth=(32+labelOffset)*2+labelWidth
    labelL=os.path.join(IDE.IDE_tabSkinsPath,loc,'IDEtab_labelL.png')
    labelR=os.path.join(IDE.IDE_tabSkinsPath,loc,'IDEtab_labelR.png')
    cornerL=os.path.join(IDE.IDE_tabSkinsPath,loc,'IDEtab_Lcorner.png')
    cornerR=os.path.join(IDE.IDE_tabSkinsPath,loc,'IDEtab_Rcorner.png')
    LLorig=wx.Image(labelL,wx.BITMAP_TYPE_PNG)
    LLstretch=LLorig.Mirror().GetSubImage((1,0,1,32))
    LC=wx.Image(cornerL,wx.BITMAP_TYPE_PNG)
    RL = wx.Image(labelR,wx.BITMAP_TYPE_PNG) if os.path.exists(labelR) else LLorig.Mirror()
    RC = wx.Image(cornerR,wx.BITMAP_TYPE_PNG) if os.path.exists(cornerR) else LC.Mirror()
    LLorig.Rescale(size,size)
    LLstretch.Rescale(labelWidth,size)
    LC.Rescale(size,size)
    RL.Rescale(size,size)
    RC.Rescale(size,size)
    dc.DrawBitmap(LLstretch.ConvertToBitmap(),pos.x+labelOffset+size,pos.y)
    dc.DrawBitmap(LLorig.ConvertToBitmap(),pos.x+labelOffset,pos.y)
    dc.DrawBitmap(RL.ConvertToBitmap(),pos.x+labelOffset+size+labelWidth,pos.y)
    dc.DrawBitmap(LC.ConvertToBitmap(),pos.x,pos.y)
    dc.DrawBitmap(RC.ConvertToBitmap(),pos.x+labelOffset*2+size+labelWidth,pos.y)

    loc=IDE.IDE_CFG[IDE.CFG_sliderSkin]
    pos=sliderpos
    xoffset=16
    midWidth=55
    totalWidth=(16+xoffset)*2+midWidth
    slider=os.path.join(IDE.IDE_sliderSkinsPath,loc,'IDE_slider.png')
    end=os.path.join(IDE.IDE_sliderSkinsPath,loc,'IDE_sliderEnd.png')
    Eorig=wx.Image(end,wx.BITMAP_TYPE_PNG)
    Sorig=wx.Image(slider,wx.BITMAP_TYPE_PNG)
    Smid=Sorig.Mirror().GetSubImage((0,0,1,16))
    Smid.Rescale(midWidth,16)
    dc.DrawBitmap(Sorig.ConvertToBitmap(),pos.x,pos.y)
    dc.DrawBitmap(Smid.ConvertToBitmap(),pos.x+16,pos.y)
    dc.DrawBitmap(Sorig.Mirror().Mirror(False).ConvertToBitmap(),pos.x+16+midWidth,pos.y)
    dc.DrawBitmap(Eorig.ConvertToBitmap(),pos.x,pos.y)
    dc.DrawBitmap(Eorig.Mirror().Mirror(False).ConvertToBitmap(),pos.x+xoffset+16+midWidth,pos.y)


def openPreferences():
    global PREF_OPEN, KEYMAP_COPY, CFG_ORIG, HL_COLORS_ORIG, prefScreen, prefNotebook,\
           keymapTB, actionsList, keyText, keyStatusList, pythonSyntaxList,\
           lastWSfontPPU, lastWSfontSpacing
#     if IDE.WIN and not IDE.IDE_TDExtensionAvail:
#        print IDE.PandaSystem.getVersionString()
#        dll = ('http://ynjh.panda3dprojects.com/OIDE/TD for P3D %s.dll'%IDE.P3D_VERSION).replace(' ','%20')
#        print dll

#        import urllib2
#        try:
#            openfile = urllib2.urlopen(dll)
#            print 'FILE EXISTS'
#        except urllib2.URLError, ee:
#            print ee.code

#        http = HTTPClient()
#        channel = http.makeChannel(True)
#        channel.getDocument(DocumentSpec(dll))
#        print channel.isValid()
#        print channel.getStatusCode()

#        channel.beginGetDocument(DocumentSpec(dll))
#        def checkDllExistance(task):
#            if channel.run():
#               return task.cont
#            if channel.isValid():
#               print 'FILE EXISTS'
#            else:
#               print channel.getStatusCode()
#        taskMgr.add(checkDllExistance, IDE.IDE_tasksName+'download dll')
    if PREF_OPEN:
       prefScreen.Raise()
       return
    PREF_OPEN=True
    KEYMAP_COPY = deepcopy(IDE.IDE_KEYMAP)
    CFG_ORIG = deepcopy(IDE.IDE_CFG)
    HL_COLORS_ORIG = deepcopy(IDE.HL_COLORS)
    lastWSfontPPU=IDE.IDE_CFG[IDE.CFG_WSfontPPU]
    lastWSfontSpacing=IDE.IDE_CFG[IDE.CFG_WSfontSpacing]

    prefScreen = wx.Frame(None, -1, 'Preferences')
    prefPanel = wx.Panel(prefScreen)
    mainSizer = wx.BoxSizer(wx.VERTICAL)

    prefNotebook = wx.Notebook(prefPanel)#,size=(500,-1)
    generalPanel = wx.Panel(prefNotebook)
    editorPanel = wx.Panel(prefNotebook)
    keymapPanel = wx.Panel(prefNotebook)
    appearancePanel = wx.Panel(prefNotebook)
    colorsPanel = wx.Panel(prefNotebook)
    updatePanel = wx.Panel(prefNotebook)

    prefNotebook.AddPage(generalPanel,'General')
    prefNotebook.AddPage(editorPanel,'Editor')
    prefNotebook.AddPage(keymapPanel,'Key Map')
    prefNotebook.AddPage(appearancePanel,'Appearance')
    prefNotebook.AddPage(colorsPanel,'Colors')
    prefNotebook.AddPage(updatePanel,'Upgrades')

    allVert=wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL
    leftVert=wx.LEFT|wx.ALIGN_CENTER_VERTICAL
    leftTop=wx.LEFT|wx.TOP
    leftTopVert=wx.LEFT|wx.TOP|wx.ALIGN_CENTER_VERTICAL
    leftBottomTopVert=wx.LEFT|wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER_VERTICAL
    leftRightVert=wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL
    rightVert=wx.RIGHT|wx.ALIGN_CENTER_VERTICAL
    rightTopVert=wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL
    LRTop=wx.LEFT|wx.RIGHT|wx.TOP
    LRVert=wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL
    topVert=wx.TOP|wx.ALIGN_CENTER_VERTICAL
    vert=wx.ALIGN_CENTER_VERTICAL
    #_____________________________________________________________________________________
    generalSizer = wx.BoxSizer(wx.VERTICAL)
    generalPanel.SetSizer(generalSizer)
    generalGridSizer = wx.FlexGridSizer(2,2,0,0)

    resetCamCB = wx.CheckBox(generalPanel,-1, IDE_CFG_DESC[IDE.CFG_resetCamTransform],
      name=RESET_CAM)
    resetCamCB.Value=IDE.IDE_CFG[IDE.CFG_resetCamTransform]
    resetCamCB.Bind(wx.EVT_CHECKBOX,lambda e:IDE.IDE_CFG.__setitem__(IDE.CFG_resetCamTransform,e.EventObject.GetValue()))
    resetCamCB.SetToolTipString(IDE_CFG_TIP[IDE.CFG_resetCamTransform])
    respondSysExitCB = wx.CheckBox(generalPanel,-1,IDE_CFG_DESC[IDE.CFG_activatedBySysExit])
    respondSysExitCB.Value=IDE.IDE_CFG[IDE.CFG_activatedBySysExit]
    respondSysExitCB.Bind(wx.EVT_CHECKBOX,lambda e:IDE.IDE_CFG.__setitem__(IDE.CFG_activatedBySysExit,e.EventObject.GetValue()))
    respondSysExitCB.SetToolTipString(IDE_CFG_TIP[IDE.CFG_activatedBySysExit])
    excludeOldModsCB = wx.CheckBox(generalPanel,-1,IDE_CFG_DESC[IDE.CFG_excludeOldMods])
    excludeOldModsCB.Value=IDE.IDE_CFG[IDE.CFG_excludeOldMods]
    excludeOldModsCB.Bind(wx.EVT_CHECKBOX,lambda e:IDE.IDE_CFG.__setitem__(IDE.CFG_excludeOldMods,e.EventObject.GetValue()))
    excludeOldModsCB.SetToolTipString(IDE_CFG_TIP[IDE.CFG_excludeOldMods])
    autoCompleteCB = wx.CheckBox(generalPanel,-1,IDE_CFG_DESC[IDE.CFG_autoComplete])
    autoCompleteCB.Value=IDE.IDE_CFG[IDE.CFG_autoComplete]
    autoCompleteCB.Bind(wx.EVT_CHECKBOX,lambda e:IDE.IDE_CFG.__setitem__(IDE.CFG_autoComplete,e.EventObject.GetValue()))
    autoCompleteCB.SetToolTipString(IDE_CFG_TIP[IDE.CFG_autoComplete])
    autoLogCB = wx.CheckBox(generalPanel,-1,IDE_CFG_DESC[IDE.CFG_autoCreateLog])
    autoLogCB.Value=IDE.IDE_CFG[IDE.CFG_autoCreateLog]
    autoLogCB.Bind(wx.EVT_CHECKBOX,lambda e:IDE.IDE_CFG.__setitem__(IDE.CFG_autoCreateLog,e.EventObject.GetValue()))
    autoLogCB.SetToolTipString(IDE_CFG_TIP[IDE.CFG_autoCreateLog])

    def toggleAutoUpdateAvailability(e):
        IDE.IDE_CFG.__setitem__(IDE.CFG_autoReloadFiles,e.EventObject.GetValue())
        if autoReloadCB.IsChecked():
           autoUpdateCB.Enable()
        else:
           autoUpdateCB.Disable()

    autoReloadCB = wx.CheckBox(generalPanel,-1,IDE_CFG_DESC[IDE.CFG_autoReloadFiles])
    autoReloadCB.Value=IDE.IDE_CFG[IDE.CFG_autoReloadFiles]
    autoReloadCB.Bind(wx.EVT_CHECKBOX,toggleAutoUpdateAvailability)
    autoReloadCB.SetToolTipString(IDE_CFG_TIP[IDE.CFG_autoReloadFiles])
    autoUpdateCB = wx.CheckBox(generalPanel,-1,IDE_CFG_DESC[IDE.CFG_autoUpdateMainMod])
    autoUpdateCB.Value=IDE.IDE_CFG[IDE.CFG_autoUpdateMainMod]
    autoUpdateCB.Bind(wx.EVT_CHECKBOX,lambda e:IDE.IDE_CFG.__setitem__(IDE.CFG_autoUpdateMainMod,e.EventObject.GetValue()))
    autoUpdateCB.SetToolTipString(IDE_CFG_TIP[IDE.CFG_autoUpdateMainMod])
    if not autoReloadCB.IsChecked():
       autoUpdateCB.Disable()

    minLargeLogSize=20000
    minLargeLogSizeText = wx.StaticText(generalPanel,-1,IDE_CFG_DESC[IDE.CFG_minLargeLogSize])
    minLargeLogSizeIC = IntCtrl(generalPanel,-1,value=IDE.IDE_CFG[IDE.CFG_minLargeLogSize],min=minLargeLogSize,size=(70,-1))
    minLargeLogSizeIC.Bind(wx.lib.intctrl.EVT_INT,lambda e:IDE.IDE_CFG.__setitem__(IDE.CFG_minLargeLogSize,max(minLargeLogSize,e.EventObject.GetValue())))
    minLargeLogSizeIC.SetToolTipString(IDE_CFG_TIP[IDE.CFG_minLargeLogSize])
    minRecentFiles=30
    recentFilesLimitText = wx.StaticText(generalPanel,-1,IDE_CFG_DESC[IDE.CFG_recentFilesLimit])
    recentFilesLimitIC = IntCtrl(generalPanel,-1,value=IDE.IDE_CFG[IDE.CFG_recentFilesLimit],min=minRecentFiles,size=(70,-1))
    recentFilesLimitIC.Bind(wx.lib.intctrl.EVT_INT,lambda e:IDE.IDE_CFG.__setitem__(IDE.CFG_recentFilesLimit,max(minRecentFiles,e.EventObject.GetValue())))
    recentFilesLimitIC.SetToolTipString(IDE_CFG_TIP[IDE.CFG_recentFilesLimit])
    minCCdesc=1000

    generalGridSizer.Add(minLargeLogSizeText,0, allVert, 5)
    generalGridSizer.Add(minLargeLogSizeIC,0, allVert, 5)
    generalGridSizer.Add(recentFilesLimitText,0, allVert, 5)
    generalGridSizer.Add(recentFilesLimitIC,0, allVert,5)

    generalSizer.Add(resetCamCB,0, leftTopVert, 5)
    generalSizer.Add(respondSysExitCB,0, leftTopVert, 5)
    generalSizer.Add(excludeOldModsCB,0, leftTopVert, 5)
    generalSizer.Add(autoCompleteCB,0, leftTopVert, 5)
    generalSizer.Add(autoLogCB,0, leftTopVert, 5)
    generalSizer.Add(autoReloadCB,0, leftBottomTopVert, 5)
    generalSizer.Add(autoUpdateCB,0, leftVert, 25)
    generalSizer.Add(generalGridSizer,0, leftTopVert, 5)

    #_____________________________________________________________________________________
    editorSizer = wx.BoxSizer(wx.HORIZONTAL)
    editorPanel.SetSizer(editorSizer)
    editorIndentSpaceSizer = wx.StaticBoxSizer(wx.StaticBox(editorPanel,-1,' Indentation space '),wx.VERTICAL)
    editorVSizer1 = wx.BoxSizer(wx.VERTICAL)
    editorHSizer1 = wx.BoxSizer(wx.HORIZONTAL)
    editorScrollingSizer = wx.StaticBoxSizer(wx.StaticBox(editorPanel,-1,' Scrolling '),wx.VERTICAL)
    editorJumpSESizer = wx.StaticBoxSizer(wx.StaticBox(editorPanel,-1,' Jump '),wx.VERTICAL)
    editorGridSizer = wx.FlexGridSizer(2+len(list(IDE.IDE_CFG[IDE.CFG_smartIndent].keys())),3,0,0)
    editorGridSizer2 = wx.FlexGridSizer(0,2,0,0)
    editorVisLCSizer = wx.FlexGridSizer(0,3,0,0)

    fixedIndentSpacesText = wx.StaticText(editorPanel,-1,IDE_CFG_DESC[IDE.CFG_fixedIndentSpaces])
    fixedIndentSpacesSC = myIntSpinCtrl(editorPanel,-1,
      value=IDE.IDE_CFG[IDE.CFG_fixedIndentSpaces],min=1,max=50,limited=True,size=(30,-1),
      onValueChange=lambda val:IDE.IDE_CFG.__setitem__(IDE.CFG_fixedIndentSpaces,val))
    smartIndentText = wx.StaticText(editorPanel,-1,IDE_CFG_DESC[IDE.CFG_smartIndent])

    editorGridSizer.Add(fixedIndentSpacesText,0, leftVert, 5)
    editorGridSizer.Add(fixedIndentSpacesSC,0, leftVert, 5)
    editorGridSizer.Add((0,0))
    editorGridSizer.Add(smartIndentText,0, allVert, 5)
    editorGridSizer.Add((0,0))
    editorGridSizer.Add((0,0))

    for o,k in list(IDE.SMART_INDENT_order.items()):
        v=IDE.IDE_CFG[IDE.CFG_smartIndent][k]
        text = wx.StaticText(editorPanel,-1,k)
        SC = myIntSpinCtrl(editorPanel,-1,
          value=0 if v is None else v,min=0,max=50,limited=True,size=(30,-1),
          onValueChange=lambda c,val:IDE.IDE_CFG[IDE.CFG_smartIndent].__setitem__(c,val),
          extraArgs=k
          )
        SC.SetToolTipString(IDE_CFG_TIP[IDE.CFG_smartIndent]%k)
        editorGridSizer.Add(text,0, wx.ALIGN_RIGHT|allVert, 5)
        editorGridSizer.Add(SC,0, leftTopVert, 5)
        editorGridSizer.Add((10,0))

    editorIndentSpaceSizer.Add(editorGridSizer,0, rightVert, 5)

    minMinLinesDisBrMatch=0
    minLinesDisBrMatchText = wx.StaticText(editorPanel,-1,IDE_CFG_DESC[IDE.CFG_brMatchMaxLines])
    minLinesDisBrMatchIC = IntCtrl(editorPanel,-1,value=IDE.IDE_CFG[IDE.CFG_brMatchMaxLines],min=minMinLinesDisBrMatch,size=(70,-1))
    minLinesDisBrMatchIC.Bind(wx.lib.intctrl.EVT_INT,lambda e:IDE.IDE_CFG.__setitem__(IDE.CFG_brMatchMaxLines,max(minMinLinesDisBrMatch,e.EventObject.GetValue())))
    minLinesDisBrMatchIC.SetToolTipString(IDE_CFG_TIP[IDE.CFG_brMatchMaxLines])
    CCmaxSrcText = wx.StaticText(editorPanel,-1,IDE_CFG_DESC[IDE.CFG_CCmaxSrc])
    CCmaxSrcIC = IntCtrl(editorPanel,-1,value=IDE.IDE_CFG[IDE.CFG_CCmaxSrc],min=minCCdesc,size=(70,-1))
    CCmaxSrcIC.Bind(wx.lib.intctrl.EVT_INT,lambda e:IDE.IDE_CFG.__setitem__(IDE.CFG_CCmaxSrc,max(minCCdesc,e.EventObject.GetValue())))
    CCmaxSrcIC.SetToolTipString(IDE_CFG_TIP[IDE.CFG_CCmaxSrc])
    CTwrapWidthText = wx.StaticText(editorPanel,-1,IDE_CFG_DESC[IDE.CFG_CTwrapWidth])
    CTwrapWidthIC = IntCtrl(editorPanel,-1,value=IDE.IDE_CFG[IDE.CFG_CTwrapWidth],min=0,size=(70,-1))
    CTwrapWidthIC.Bind(wx.lib.intctrl.EVT_INT,lambda e:IDE.IDE_CFG.__setitem__(IDE.CFG_CTwrapWidth,max(0,e.EventObject.GetValue())))
    CTwrapWidthIC.SetToolTipString(IDE_CFG_TIP[IDE.CFG_CTwrapWidth])

    editorGridSizer2.Add(minLinesDisBrMatchText,0, leftTopVert, 5)
    editorGridSizer2.Add(minLinesDisBrMatchIC,0, leftTopVert,5)
    editorGridSizer2.Add(CCmaxSrcText,0, leftTopVert, 5)
    editorGridSizer2.Add(CCmaxSrcIC,0, leftTopVert,5)
    editorGridSizer2.Add(CTwrapWidthText,0, leftTopVert, 5)
    editorGridSizer2.Add(CTwrapWidthIC,0, leftTopVert,5)

    visLinesOfCaretText = wx.StaticText(editorPanel,-1,IDE_CFG_DESC[IDE.CFG_visLinesOfCaret])
    visLinesOfCaretSC = myIntSpinCtrl(editorPanel,-1,
      value=IDE.IDE_CFG[IDE.CFG_visLinesOfCaret],min=0,max=20,limited=True,size=(30,-1),
      onValueChange=lambda val:IDE.IDE_CFG.__setitem__(IDE.CFG_visLinesOfCaret,val))
    visLinesOfCaretSC.SetToolTipString(IDE_CFG_TIP[IDE.CFG_visLinesOfCaret])
    visColumnsOfCaretText = wx.StaticText(editorPanel,-1,IDE_CFG_DESC[IDE.CFG_visColumnsOfCaret])
    visColumnsOfCaretSC = myIntSpinCtrl(editorPanel,-1,
      value=IDE.IDE_CFG[IDE.CFG_visColumnsOfCaret],min=0,max=50,limited=True,size=(30,-1),
      onValueChange=lambda val:IDE.IDE_CFG.__setitem__(IDE.CFG_visColumnsOfCaret,val))
    visColumnsOfCaretSC.SetToolTipString(IDE_CFG_TIP[IDE.CFG_visColumnsOfCaret])
    linesPerScrollText = wx.StaticText(editorPanel,-1,IDE_CFG_DESC[IDE.CFG_linesPerScroll])
    linesPerScrollSC = myIntSpinCtrl(editorPanel,-1,
      value=IDE.IDE_CFG[IDE.CFG_linesPerScroll],min=0,max=10,limited=True,size=(30,-1),
      onValueChange=lambda val:IDE.IDE_CFG.__setitem__(IDE.CFG_linesPerScroll,val))
    linesPerScrollSC.SetToolTipString(IDE_CFG_TIP[IDE.CFG_linesPerScroll])
    realLineStartCB = wx.CheckBox(editorPanel,-1,IDE_CFG_DESC[IDE.CFG_realLineStart])
    realLineStartCB.Value=IDE.IDE_CFG[IDE.CFG_realLineStart]
    realLineStartCB.Bind(wx.EVT_CHECKBOX,lambda e:IDE.IDE_CFG.__setitem__(IDE.CFG_realLineStart,realLineStartCB.GetValue()))
    realLineStartCB.SetToolTipString(IDE_CFG_TIP[IDE.CFG_realLineStart])
    realLineEndCB = wx.CheckBox(editorPanel,-1,IDE_CFG_DESC[IDE.CFG_realLineEnd])
    realLineEndCB.Value=IDE.IDE_CFG[IDE.CFG_realLineEnd]
    realLineEndCB.Bind(wx.EVT_CHECKBOX,lambda e:IDE.IDE_CFG.__setitem__(IDE.CFG_realLineEnd,realLineEndCB.GetValue()))
    realLineEndCB.SetToolTipString(IDE_CFG_TIP[IDE.CFG_realLineEnd])

    editorVisLCSizer.Add(visLinesOfCaretText,0, vert, 5)
    editorVisLCSizer.Add(visLinesOfCaretSC,0, vert, 5)
    editorVisLCSizer.Add((15,0))
    editorVisLCSizer.Add(visColumnsOfCaretText,0, vert, 5)
    editorVisLCSizer.Add(visColumnsOfCaretSC,0, vert, 5)
    editorVisLCSizer.Add((15,0))
    editorVisLCSizer.Add(linesPerScrollText,0, vert, 5)
    editorVisLCSizer.Add(linesPerScrollSC,0, vert, 5)
    editorVisLCSizer.Add((15,0))

    editorScrollingSizer.Add(editorVisLCSizer)
    editorJumpSESizer.Add(realLineStartCB,0, vert, 5)
    editorJumpSESizer.Add(realLineEndCB,0, vert, 5)

    editorHSizer1.Add(editorScrollingSizer,0, leftRightVert|wx.EXPAND, 5)
    editorHSizer1.Add(editorJumpSESizer,0, leftVert|wx.EXPAND, 5)

    editorVSizer1.Add(editorHSizer1)
    editorVSizer1.Add((0,10))
    editorVSizer1.Add(editorGridSizer2)
    editorSizer.Add(editorIndentSpaceSizer,0, wx.ALL, 5)
    editorSizer.Add(editorVSizer1,0, wx.TOP, 5)

    #_____________________________________________________________________________________
    keymapSizer = wx.BoxSizer(wx.VERTICAL)
    keymapPanel.SetSizer(keymapSizer)
    keymapListKMSizer = wx.BoxSizer(wx.HORIZONTAL)
    keymapHSizer = wx.BoxSizer(wx.HORIZONTAL)
    keymapVSizer = wx.BoxSizer(wx.VERTICAL)
    keymapGridSizer = wx.FlexGridSizer(3,2,0,0)
    keymapHSizer1 = wx.BoxSizer(wx.HORIZONTAL)
    keymapHSizer2 = wx.BoxSizer(wx.HORIZONTAL)

    keymapTB = wx.Treebook(keymapPanel,-1)
    KMbookSizer = wx.BoxSizer(wx.VERTICAL)
    KMbookPanel = wx.Panel(keymapTB,-1)
    KMbookPanel.SetSizer(KMbookSizer)

    for ac in (IDE.AC_gen, IDE.AC_doc, IDE.AC_edit, IDE.AC_comp, IDE.AC_mark,
               IDE.AC_macro, IDE.AC_search, IDE.AC_scene
              ):
        keymapTB.AddPage(KMbookPanel,CAT_NAME[ac])
    keymapTB.Bind(wx.EVT_TREEBOOK_PAGE_CHANGED,lambda e:actionsCategorySelected(keymapGridSizer,oldKeysChoice,e))
#     tc=keymapTB.GetTreeCtrl()
#     iid=tc.Selection
#     textColor=(0,)*3
#     for i in range(tc.Count):
#         tc.SetItemTextColour(iid,textColor)
#         iid=tc.GetNextSibling(iid)

    def warpPointer(e):
        # warping the pointer on Linux somehow deselects actionsList,
        # so the new key would be saved to the wrong action !
        #~ keyText.WarpPointer(keyText.Size.x-5,.5*keyText.Size.y)
        keyText.SetFocus()
        keyText.SelectAll()

    actionsList = SortableListCtrl(KMbookPanel,-1, size=(370,250), images=IDE.LCimageList,
                style=wx.LC_REPORT|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.BORDER_SUNKEN)
    actionsList.Bind(wx.EVT_LIST_ITEM_SELECTED,lambda e:actionSelected(keymapGridSizer,oldKeysChoice,e))
    actionsList.Bind(wx.EVT_LEFT_DCLICK,warpPointer)
    actionsList.InsertColumn(0, 'Action',wx.LIST_FORMAT_LEFT,260)
    actionsList.InsertColumn(1, 'Keys',wx.LIST_FORMAT_LEFT,140)
    actionsList.setStrConverter( (
      lambda s: s[s.find('\t')+1:],
      str
    ))
    actionsList.setSortDataBuilder( (
      lambda s: s[:s.find('\t')],
      str
    ))
    KMbookSizer.Add(actionsList,0,wx.EXPAND)


    keyText = wx.TextCtrl(keymapPanel,value='None',size=(170,-1))
    keyText.Bind(wx.EVT_KEY_DOWN,     KM.setKey)
    keyText.Bind(wx.EVT_KEY_UP,       KM.clearKey)
    keyText.Bind(wx.EVT_MOUSE_EVENTS, KM.setKey)
    keyText.SetEditable(0)

    oldKeysChoice = wx.Choice(keymapPanel,size=(170,-1))
    clearOldKeyButton = wx.Button(keymapPanel,-1,'Clear',style=wx.BU_EXACTFIT)
    restoreDefaultKeyButton = wx.Button(keymapPanel,-1,'Restore default',style=wx.BU_EXACTFIT)
    replaceKeyButton = wx.Button(keymapPanel,-1,'Replace keys',size=restoreDefaultKeyButton.Size)
    addKeyButton = wx.Button(keymapPanel,-1,'Add',size=clearOldKeyButton.Size)
    keyStatusList = wx.ListBox(keymapPanel,-1,size=(-1,50))
    actTextPadCB = wx.CheckBox(keymapPanel,-1,'pad')
    actTextPadCB.Value=True
    listKeymapButton = wx.Button(keymapPanel,-1,'List',style=wx.BU_EXACTFIT)
    loadKeymapButton = wx.Button(keymapPanel,-1,'Load')
    saveKeymapButton = wx.Button(keymapPanel,-1,'Save as')
    restoreAllDefaultKeysButton = wx.Button(keymapPanel,-1,'Restore')
    clearOldKeyButton.Bind(wx.EVT_BUTTON,lambda e:clearActionKey(oldKeysChoice))
    restoreDefaultKeyButton.Bind(wx.EVT_BUTTON,restoreActionDefaultKeys)
    addKeyButton.Bind(wx.EVT_BUTTON,addActionKey)
    replaceKeyButton.Bind(wx.EVT_BUTTON,lambda e:addActionKey(e,True))
    listKeymapButton.Bind(wx.EVT_BUTTON,lambda e:listKeymap(actTextPadCB))
    restoreAllDefaultKeysButton.Bind(wx.EVT_BUTTON,restoreAllDefaultKeys)
    loadKeymapButton.Bind(wx.EVT_BUTTON,loadKeymap)
    saveKeymapButton.Bind(wx.EVT_BUTTON,saveKeymap)

    keymapListKMSizer.Add(actTextPadCB,0, topVert, 5)
    keymapListKMSizer.Add(listKeymapButton,0,
    rightTopVert|wx.EXPAND, 5)

    keymapVSizer.Add(keymapListKMSizer,0, wx.ALIGN_RIGHT, 5)
    keymapVSizer.Add(loadKeymapButton,0, rightVert|wx.EXPAND, 5)
    keymapVSizer.Add(saveKeymapButton,0, rightVert|wx.EXPAND, 5)
    keymapVSizer.Add(restoreAllDefaultKeysButton,0, rightVert|wx.EXPAND, 5)

    keymapHSizer1.Add(oldKeysChoice,0, leftTopVert, 5)
    keymapHSizer1.Add(clearOldKeyButton,0, leftTopVert, 5)
    keymapHSizer1.Add(restoreDefaultKeyButton,0, leftTopVert, 5)
    keymapHSizer2.Add(keyText,0, leftTopVert, 5)
    keymapHSizer2.Add(replaceKeyButton,0, leftTopVert, 5)
    keymapHSizer2.Add(addKeyButton,0, leftTopVert, 5)

    keymapGridSizer.Add(wx.StaticText(keymapPanel,-1,'Current keys :'),0, leftTopVert|wx.ALIGN_RIGHT, 5)
    keymapGridSizer.Add(keymapHSizer1)
    keymapGridSizer.Add(wx.StaticText(keymapPanel,-1,'New key :'),0, leftTopVert|wx.ALIGN_RIGHT, 5)
    keymapGridSizer.Add(keymapHSizer2)
    keymapGridSizer.Add(wx.StaticText(keymapPanel,-1,'Used by :'),0, leftTopVert|wx.ALIGN_RIGHT, 5)
    keymapGridSizer.Add(keyStatusList,0, leftTopVert|wx.EXPAND, 5)
    for w in IDE.getWxSizerWidgets(keymapGridSizer):
        w.Disable()

    keymapHSizer.Add(keymapVSizer,0, wx.ALIGN_BOTTOM, 5)
#     keymapHSizer.Add((10,0))
    keymapHSizer.Add(keymapGridSizer,0, wx.ALIGN_RIGHT, 5)

    keymapSizer.Add(keymapTB,0, wx.TOP|wx.LEFT|wx.RIGHT|wx.EXPAND, 5)
    keymapSizer.Add(keymapHSizer,0, wx.BOTTOM|wx.ALIGN_CENTER, 5)

    lastCat=IDE.IDE_lastKeymapCategory
#     if lastCat==0:
#        keymapTB.SetSelection(1)
    keymapTB.SetSelection(lastCat)

    #_____________________________________________________________________________________
    appearanceSizer = wx.BoxSizer(wx.VERTICAL)
    appearancePanel.SetSizer(appearanceSizer)
    appearancePanel.Bind(wx.EVT_PAINT, lambda e:drawSkins(tabSkinLPos.GetPosition(),sliderSkinPos.GetPosition(),e))
    appearanceGridSizer1 = wx.FlexGridSizer(0,3,0,0)
    appearanceGridSizer2 = wx.FlexGridSizer(0,3,0,0)

    tabSkinText = wx.StaticText(appearancePanel,-1,IDE_CFG_DESC[IDE.CFG_fileTabSkin])
    tabSkinCh = wx.Choice(appearancePanel,-1,choices=IDE.IDE_getAvailTabSkins())
    tabSkinCh.SetStringSelection(IDE.IDE_CFG[IDE.CFG_fileTabSkin])
    tabSkinCh.Bind(wx.EVT_CHOICE,fileTabSkinSet)
    tabSkinLPos=wx.StaticText(appearancePanel,-1,' ',size=(1,32*.8))

    sliderSkinText = wx.StaticText(appearancePanel,-1,IDE_CFG_DESC[IDE.CFG_sliderSkin])
    sliderSkinCh = wx.Choice(appearancePanel,-1,choices=IDE.IDE_getAvailSliderSkins())
    sliderSkinCh.SetStringSelection(IDE.IDE_CFG[IDE.CFG_sliderSkin])
    sliderSkinCh.Bind(wx.EVT_CHOICE,sliderSkinSet)
    sliderSkinPos=wx.StaticText(appearancePanel,-1,' ',size=(1,16))

    def adjustWSfontSize(val):
        if IDE.IDE_CFG[IDE.CFG_WSfontPPU]!=val:
           IDE.IDE_CFG[IDE.CFG_WSfontPPU]=val
           IDE.IDE_setWSfontProps(val,IDE.IDE_CFG[IDE.CFG_WSfontSpacing])
    def adjustWSfontSpacing(val):
        if IDE.IDE_CFG[IDE.CFG_WSfontSpacing]!=val:
           IDE.IDE_CFG[IDE.CFG_WSfontSpacing]=val
           IDE.IDE_setWSfontProps(IDE.IDE_CFG[IDE.CFG_WSfontPPU],val)
    def adjustWSopacity(e):
        val=e.EventObject.Value
        IDE.IDE_adjustWSopacity(val-IDE.IDE_CFG[IDE.CFG_WSopacity])
        WSopacityLevelText.Label=str(val)
    def adjustCCopacity(e):
        val=e.EventObject.Value
        IDE.IDE_adjustCCopacity(val-IDE.IDE_CFG[IDE.CFG_CCopacity])
        CCopacityLevelText.Label=str(val)
    caretTypes=sorted(IDE.CAR_DESC.values())
    insCaretText = wx.StaticText(appearancePanel,-1,IDE_CFG_DESC[IDE.CFG_insCaret])
    insCaretCh = wx.Choice(appearancePanel,-1,choices=caretTypes)
    insCaretCh.SetStringSelection(IDE.CAR_DESC[IDE.IDE_CFG[IDE.CFG_insCaret]])
    insCaretCh.SetToolTipString(IDE_CFG_TIP[IDE.CFG_insCaret])
    insCaretCh.Bind(wx.EVT_CHOICE,lambda e:caretSet(True,e))
    ovrCaretText = wx.StaticText(appearancePanel,-1,IDE_CFG_DESC[IDE.CFG_ovrCaret])
    ovrCaretCh = wx.Choice(appearancePanel,-1,choices=caretTypes)
    ovrCaretCh.SetStringSelection(IDE.CAR_DESC[IDE.IDE_CFG[IDE.CFG_ovrCaret]])
    ovrCaretCh.SetToolTipString(IDE_CFG_TIP[IDE.CFG_ovrCaret])
    ovrCaretCh.Bind(wx.EVT_CHOICE,lambda e:caretSet(False,e))
    WSopacityText = wx.StaticText(appearancePanel,-1,IDE_CFG_DESC[IDE.CFG_WSopacity])
    WSopacityLevel = wx.Slider(appearancePanel,-1, IDE.IDE_CFG[IDE.CFG_WSopacity], 0,100, size=(0,-1))
    WSopacityLevel.Bind(wx.EVT_SLIDER,adjustWSopacity)
    WSopacityLevel.SetToolTipString(IDE_CFG_TIP[IDE.CFG_WSopacity])
    WSopacityLevelText = wx.StaticText(appearancePanel,-1,str(IDE.IDE_CFG[IDE.CFG_WSopacity]))
    CCopacityText = wx.StaticText(appearancePanel,-1,IDE_CFG_DESC[IDE.CFG_CCopacity])
    CCopacityLevel = wx.Slider(appearancePanel,-1, IDE.IDE_CFG[IDE.CFG_CCopacity], 0,100, size=(0,-1))
    CCopacityLevel.Bind(wx.EVT_SLIDER,adjustCCopacity)
    CCopacityLevel.SetToolTipString(IDE_CFG_TIP[IDE.CFG_CCopacity])
    CCopacityLevelText = wx.StaticText(appearancePanel,-1,str(IDE.IDE_CFG[IDE.CFG_CCopacity]))
    WSfontSizeText = wx.StaticText(appearancePanel,-1,IDE_CFG_DESC[IDE.CFG_WSfontPPU])
    WSfontSizeSC = myIntSpinCtrl(appearancePanel,-1,
      value=IDE.IDE_CFG[IDE.CFG_WSfontPPU],min=10,max=20,limited=True,size=(30,-1),
      onValueChange=adjustWSfontSize)
    WSfontSizeSC.SetToolTipString(IDE_CFG_TIP[IDE.CFG_WSfontPPU])
    WSfontSpacingText = wx.StaticText(appearancePanel,-1,IDE_CFG_DESC[IDE.CFG_WSfontSpacing])
    WSfontSpacingSC = myIntSpinCtrl(appearancePanel,-1,
      value=IDE.IDE_CFG[IDE.CFG_WSfontSpacing],min=5,max=15,limited=True,size=(30,-1),
      onValueChange=adjustWSfontSpacing)
    WSfontSpacingSC.SetToolTipString(IDE_CFG_TIP[IDE.CFG_WSfontSpacing])
    animSelColorCB = wx.CheckBox(appearancePanel,-1,IDE_CFG_DESC[IDE.CFG_animSelColor])
    animSelColorCB.Value=IDE.IDE_CFG[IDE.CFG_animSelColor]
    animSelColorCB.Bind(wx.EVT_CHECKBOX,lambda e:IDE.IDE_setBlockColorAnim(animSelColorCB.GetValue()))

    appearanceGridSizer1.Add(tabSkinText,0, allVert, 5)
    appearanceGridSizer1.Add(tabSkinCh,0, allVert, 5)
    appearanceGridSizer1.Add(tabSkinLPos,0, allVert, 5)
    appearanceGridSizer1.Add(sliderSkinText,0, allVert, 5)
    appearanceGridSizer1.Add(sliderSkinCh,0, allVert, 5)
    appearanceGridSizer1.Add(sliderSkinPos,0, allVert, 5)

    appearanceGridSizer2.Add(insCaretText,0, allVert, 5)
    appearanceGridSizer2.Add(insCaretCh,0, topVert, 5)
    appearanceGridSizer2.Add((0,0))
    appearanceGridSizer2.Add(ovrCaretText,0, allVert, 5)
    appearanceGridSizer2.Add(ovrCaretCh,0, topVert, 5)
    appearanceGridSizer2.Add((0,0))
    appearanceGridSizer2.AddMany([(0,10)]*3)
    appearanceGridSizer2.Add(WSfontSizeText,0, allVert, 5)
    appearanceGridSizer2.Add(WSfontSizeSC,0, wx.TOP|wx.ALIGN_CENTER_VERTICAL, 5)
    appearanceGridSizer2.Add((0,0))
    appearanceGridSizer2.Add(WSfontSpacingText,0, allVert, 5)
    appearanceGridSizer2.Add(WSfontSpacingSC,0, wx.TOP|wx.ALIGN_CENTER_VERTICAL, 5)
    appearanceGridSizer2.Add((0,0))
    appearanceGridSizer2.Add(WSopacityText,0, allVert, 5)
    appearanceGridSizer2.Add(WSopacityLevel,0, wx.TOP|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5)
    appearanceGridSizer2.Add(WSopacityLevelText,0, allVert, 5)
    appearanceGridSizer2.Add(CCopacityText,0, allVert, 5)
    appearanceGridSizer2.Add(CCopacityLevel,0, wx.TOP|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5)
    appearanceGridSizer2.Add(CCopacityLevelText,0, allVert, 5)

    appearanceSizer.Add(appearanceGridSizer1,0, wx.ALL, 5)
    appearanceSizer.Add(appearanceGridSizer2,0, wx.ALL, 5)
    appearanceSizer.Add((0,15))
    appearanceSizer.Add(animSelColorCB,0, wx.ALL, 5)

    #_____________________________________________________________________________________
    colorsSizer = wx.BoxSizer(wx.HORIZONTAL)
    colorsPanel.SetSizer(colorsSizer)
    colorsGColSizer = wx.StaticBoxSizer(wx.StaticBox(colorsPanel,-1,' General colors '),wx.VERTICAL)
    colorsHLitSizer = wx.StaticBoxSizer(wx.StaticBox(colorsPanel,-1,' Highlighter colors '),wx.VERTICAL)
    colorsGCHSizer = wx.BoxSizer(wx.HORIZONTAL)
    colorsVSizer1 = wx.BoxSizer(wx.VERTICAL)
    colorsVSizer2 = wx.BoxSizer(wx.VERTICAL)
    genColorsLoadSaveSizer = wx.BoxSizer(wx.HORIZONTAL)
    synColorsLoadSaveSizer = wx.BoxSizer(wx.HORIZONTAL)

    colors=IDE.IDE_CFG[IDE.CFG_colors]
    firstColumnColors=( 'WSback','markersBar','sliderBG','tabsNstatusBar','statusText',
      'log','logOverScene','tabLabelMainModActive','tabLabelMainModInactive',
      'tabLabelOtherModActive','tabTextActive','tabTextInactive','block')
    desc=[IDE.GEN_COLORS_DESC[getattr(IDE,'GC_'+c)] for c in firstColumnColors]
    descLen=[len(d) for d in desc]
    dummyButton = wx.Button(colorsPanel,-1,desc[descLen.index(max(descLen))]+'     ',style=wx.BU_EXACTFIT)
    size=dummyButton.Size
    dummyButton.Destroy()
    for c in firstColumnColors:
        cs = ColourSelect(colorsPanel,-1,IDE.GEN_COLORS_DESC[getattr(IDE,'GC_'+c)],colors[getattr(IDE,'COL_'+c)],size=size)
        cs.Bind(EVT_COLOURSELECT, Functor(colorSelected,getattr(IDE,'COL_'+c)))
        colorsVSizer1.Add(cs,0, leftVert|wx.EXPAND, 5)
    secondColumnColors=( 'caret','codesListBG','codesListFG','codeDesc',
      'callTipsBG','callTipsText','callArgsBG')
    desc=[IDE.GEN_COLORS_DESC[getattr(IDE,'GC_'+c)] for c in secondColumnColors]
    descLen=[len(d) for d in desc]
    dummyButton = wx.Button(colorsPanel,-1,desc[descLen.index(max(descLen))]+'     ',style=wx.BU_EXACTFIT)
    size=dummyButton.Size
    dummyButton.Destroy()
    for c in secondColumnColors:
        cs = ColourSelect(colorsPanel,-1,IDE.GEN_COLORS_DESC[getattr(IDE,'GC_'+c)],colors[getattr(IDE,'COL_'+c)],size=size)
        cs.Bind(EVT_COLOURSELECT, Functor(colorSelected,getattr(IDE,'COL_'+c)))
        colorsVSizer2.Add(cs,0, wx.EXPAND, 5)

    restoreGenColorsButton = wx.Button(colorsPanel,-1,'Restore',style=wx.BU_EXACTFIT)
    loadGenColorsButton = wx.Button(colorsPanel,-1,'Load',style=wx.BU_EXACTFIT)
    saveGenColorsButton = wx.Button(colorsPanel,-1,'Save as',style=wx.BU_EXACTFIT)
    restoreGenColorsButton.Bind(wx.EVT_BUTTON,restoreGenColors)
    loadGenColorsButton.Bind(wx.EVT_BUTTON,loadGenColors)
    saveGenColorsButton.Bind(wx.EVT_BUTTON,saveGenColors)

    genColorsLoadSaveSizer.Add(restoreGenColorsButton)
    genColorsLoadSaveSizer.Add(loadGenColorsButton)
    genColorsLoadSaveSizer.Add(saveGenColorsButton)

    colorsGCHSizer.Add(colorsVSizer1)
    colorsGCHSizer.Add(colorsVSizer2)
    colorsGColSizer.Add(colorsGCHSizer,0, rightVert|wx.BOTTOM|wx.ALIGN_CENTER, 5)
    colorsGColSizer.Add(genColorsLoadSaveSizer,0, LRVert|wx.BOTTOM|wx.ALIGN_CENTER, 5)

    lang='python'
    pythonSyntaxList = wx.SimpleHtmlListBox(colorsPanel,-1,size=(170,180),choices=getHilighterColorsAsHtml(lang))
    pythonSyntaxList.SetBackgroundColour(colors[IDE.COL_WSback])
    pythonSyntaxList.Bind(wx.EVT_LISTBOX,syntaxSelected)

    restoreSynColorsButton = wx.Button(colorsPanel,-1,'Restore',style=wx.BU_EXACTFIT)
    loadSynColorsButton = wx.Button(colorsPanel,-1,'Load',style=wx.BU_EXACTFIT)
    saveSynColorsButton = wx.Button(colorsPanel,-1,'Save as',style=wx.BU_EXACTFIT)
    restoreSynColorsButton.Bind(wx.EVT_BUTTON,restoreSynColors)
    loadSynColorsButton.Bind(wx.EVT_BUTTON,loadSynColors)
    saveSynColorsButton.Bind(wx.EVT_BUTTON,saveSynColors)

    synColorsLoadSaveSizer.Add(restoreSynColorsButton)
    synColorsLoadSaveSizer.Add(loadSynColorsButton)
    synColorsLoadSaveSizer.Add(saveSynColorsButton)

    colorsHLitSizer.Add(pythonSyntaxList)
    colorsHLitSizer.Add(synColorsLoadSaveSizer,0, LRVert|wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER, 5)

    colorsSizer.Add(colorsGColSizer,0, leftTop, 5)
    colorsSizer.Add(colorsHLitSizer,0, leftTop, 5)

    #_____________________________________________________________________________________
    updateSizer = wx.BoxSizer(wx.HORIZONTAL)
    autoUpdateSizer = wx.BoxSizer(wx.VERTICAL)
    manualUpdateSizer = wx.BoxSizer(wx.VERTICAL)
    DLlistSizer = wx.FlexGridSizer(cols=3)
    updatePanel.SetSizer(updateSizer)
    updatePanel.DLlistSizer=DLlistSizer

    regularUpdate = wx.RadioBox(updatePanel,-1,IDE_CFG_DESC[IDE.CFG_regularUpdateInterval],
      choices=[UPGRADE_OPT[i][0] for i in (IDE.UPD_never,IDE.UPD_daily,IDE.UPD_weekly,IDE.UPD_monthly)],style=wx.VERTICAL)
    regularUpdate.Selection=IDE.IDE_CFG[IDE.CFG_regularUpdateInterval]
    regularUpdate.Bind(wx.EVT_RADIOBOX,lambda e:IDE.IDE_CFG.__setitem__(IDE.CFG_regularUpdateInterval,e.EventObject.Selection))
    regularUpdate.SetToolTipString(IDE_CFG_TIP[IDE.CFG_regularUpdateInterval])

    serverRB = wx.RadioBox(updatePanel,-1,IDE_CFG_DESC[IDE.CFG_host],
      choices=[UPGRADE_SRV[i] for i in range(2)],style=wx.VERTICAL, name='server')
    serverRB.Selection=IDE.IDE_CFG[IDE.CFG_host]
    serverRB.Bind(wx.EVT_RADIOBOX,lambda e:IDE.IDE_CFG.__setitem__(IDE.CFG_host,e.EventObject.Selection))
    serverRB.SetToolTipString(IDE_CFG_TIP[IDE.CFG_host])

    autoUpdateSizer.Add(regularUpdate,0, leftTop, 5)
    autoUpdateSizer.Add(serverRB,0, leftTop, 5)


    checkUpdateButton = wx.Button(updatePanel,-1,'Check upgrades',name='check upgrade')
    checkUpdateButton.Bind(wx.EVT_BUTTON,lambda e:manualCheckUpdate(checkUpdateButton,mustBeUpdatedText,updateButton,updateDetailText,e))

    mustBeUpdatedText = wx.StaticText(updatePanel,-1,AVAIL_UPGRADES,name=AVAIL_UPGRADES)
    mustBeUpdatedText.Hide()
    mustBeUpdatedText.completeAnim = wx.animate.Animation(os.path.join(IDE.IDE_imagesPath,'DL_complete.gif'))
    mustBeUpdatedText.failAnim = wx.animate.Animation(os.path.join(IDE.IDE_imagesPath,'DL_fail.gif'))

    mustBeUpdatedText.DLanim = wx.animate.Animation(os.path.join(IDE.IDE_imagesPath,'DL_transfer.gif'))

    updateButton = wx.Button(updatePanel,-1,UPGRADE_NOW,name=UPGRADE_NOW)
    updateButton.Bind(wx.EVT_BUTTON,lambda e:doUpdate(serverRB,checkUpdateButton,mustBeUpdatedText,updateButton,updateDetailText,e))
    updateButton.Hide()
    updateDetailText = wx.StaticText(updatePanel,-1,'',name='upgrade details')
    updateDetailText.Hide()

    manualUpdateSizer.Add(checkUpdateButton,0, leftTop, 5)
    manualUpdateSizer.Add(mustBeUpdatedText,0, leftTop, 5)
    manualUpdateSizer.Add(DLlistSizer,0, leftTop, 5)
    manualUpdateSizer.Add(updateButton,0, leftTop, 5)
    manualUpdateSizer.Add(updateDetailText,0, leftTop, 5)

    updateSizer.Add(autoUpdateSizer,0, leftTop, 5)
#     updateSizer.Add(wx.StaticLine(updatePanel,-1,style=wx.VERTICAL),0, leftTop|wx.EXPAND, 5)
    updateSizer.Add(manualUpdateSizer,0, leftTop, 5)

    def updateUpdateButton(e):
        numUncheckedCB = 0
        for c in DLlistSizer.GetChildren():
            CB = c.GetWindow()
            if isinstance(CB,wx.CheckBox):
               numUncheckedCB += not CB.Value
        updateListLen = len(mustBeUpdatedText.mustBeUpdated)
        if updateListLen-numUncheckedCB:
           updateButton.Enable()
        else:
           updateButton.Disable()

    def buildDownloadItems(withCB=True):
        mustBeUpdatedText.Label=AVAIL_UPGRADES
        DLlistSizer.Clear(1)
        for i in mustBeUpdatedText.mustBeUpdated:
            ani = wx.animate.AnimationCtrl(updatePanel,-1,wx.animate.Animation(os.path.join(IDE.IDE_imagesPath,'DL_queue.gif')))
            ani.SetUseWindowBackgroundColour()
            ani.Play()
            if i=='code':
               codeTxt = i+' (v%s)'%mustBeUpdatedText.releaseVersion
               if withCB:
                  item = wx.CheckBox(updatePanel,-1, codeTxt)
                  item.Value = 1
                  item.Bind(wx.EVT_CHECKBOX, updateUpdateButton)
               else:
                  item = wx.StaticText(updatePanel,-1, codeTxt)
            elif i=='TextDrawer source' and withCB:
               item = wx.CheckBox(updatePanel,-1, i)
               item.Value = 1
               item.Bind(wx.EVT_CHECKBOX, updateUpdateButton)
            else:
               item = wx.StaticText(updatePanel,-1, i)
            gauge = wx.Gauge(updatePanel, -1, DOWNLOAD_GAUGE_RANGE, size=(70, 7))
            gauge.Hide()
            DLlistSizer.Add(ani,0, leftTopVert, 5)
            DLlistSizer.Add(item,0, leftTopVert, 5)
            DLlistSizer.Add(gauge,0, leftTopVert, 5)
        updateButton.Enable()
        manualUpdateSizer.Layout()
    mustBeUpdatedText.buildDownloadItems = buildDownloadItems

    #_____________________________________________________________________________________
    savePrefSizer = wx.BoxSizer(wx.HORIZONTAL)

    savePrefBtn = wx.Button(prefPanel, -1, 'Accept changes :')
    saveKMCB = wx.CheckBox(prefPanel,-1,'key map')
    saveKMCB.Value=True
    saveGCCB = wx.CheckBox(prefPanel,-1,'general colors')
    saveGCCB.Value=True
    saveHCCB = wx.CheckBox(prefPanel,-1,'hilighter colors')
    saveHCCB.Value=True
    saveOthersCB = wx.CheckBox(prefPanel,-1,'others')
    saveOthersCB.Value=True
    savePrefBtn.Bind(wx.EVT_BUTTON,lambda e:closePreferences(prefScreen,saveKMCB.Value,saveGCCB.Value,saveHCCB.Value,saveOthersCB.Value,True))

    savePrefSizer.Add(savePrefBtn,0, leftVert, 5)
    savePrefSizer.Add(saveKMCB,0, leftVert, 5)
    savePrefSizer.Add(saveGCCB,0, leftVert, 5)
    savePrefSizer.Add(saveHCCB,0, leftVert, 5)
    savePrefSizer.Add(saveOthersCB,0, leftVert, 5)

    mainSizer.Add(prefNotebook,0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND, 5)
    mainSizer.Add(savePrefSizer,0, wx.BOTTOM, 5)

    prefScreen.Bind(wx.EVT_CLOSE,closePreferences)
    prefPanel.SetSizer(mainSizer)
    mainSizer.Fit(prefScreen)
    mainSizer.SetSizeHints(prefScreen)
    # handles navigational wx events
    if IDE.WIN:
       for w in IDE.getWxSizerWidgets([mainSizer,generalSizer,editorSizer,
                                       # keymapSizer, <-- better not handled
                                       appearanceSizer,colorsSizer]):
           w.Bind(wx.EVT_KEY_DOWN,IDE.handleNavigationalWxEvents)

    prefScreen.Center()
    prefScreen.Show()
    prefNotebook.Selection=IDE.IDE_lastPreferencePage
    prefNotebook.SetFocus()
    KM.reset()
    if IDE.WIN: # the loop must be used in order to display tooltips
       IDE.startWxLoop()


def getHilighterColorsAsHtml(lang):
    choices=[]
    for n in range(len(IDE.HL_COLOR_ORDER[lang])):
        elmType=IDE.HL_COLOR_ORDER[lang][n]
        col=IDE.HL_COLORS[lang][elmType]
        choices.append('<font size=2 color=rgb(%s,%s,%s)>%s</font>'%(col+(IDE.HL_COLOR_DESC[lang][elmType],)))
    return choices

def syntaxSelected(e):
    lang='python'
    sel=pythonSyntaxList.Selection
    # I don't want the selection highlight, to maintain item colors.
    # So just change the selected text a little to easily distinguish it.
    pythonSyntaxList.Selection=-1
    items=pythonSyntaxList.GetItems()
    bold=[items.index(i) for i in items if i[:3]=='<b>']
    if bold:
       items[bold[0]]=items[bold[0]][3:-4].replace(')>--[  ',')>').replace('  ]--</f','</f')
       pythonSyntaxList.SetString(bold[0],items[bold[0]])
    items[sel]='<b>%s</b>'%(items[sel].replace(')>',')>--[  ').replace('</f','  ]--</f'))
    pythonSyntaxList.SetString(sel,items[sel])
    elmType=IDE.HL_COLOR_ORDER[lang][sel]
    oldCol=col=IDE.HL_COLORS[lang][elmType]
    colorDlg=wx.ColourDialog(e.EventObject)
    colorDlg.GetColourData().SetChooseFull(True)
    colorDlg.GetColourData().SetColour(col)
    colorDlg.Position=(pythonSyntaxList.ScreenPosition.x-colorDlg.Size.x-30,
                       pythonSyntaxList.ScreenPosition.y+pythonSyntaxList.Size.y)
    res=colorDlg.ShowModal()
    col=colorDlg.GetColourData().GetColour()[:3]
    colorDlg.Destroy()
    if res==wx.ID_CANCEL: return
    e.EventObject.SetString(sel,items[sel].replace('%s,%s,%s'%oldCol,'%s,%s,%s'%col))
    IDE.HL_COLORS[lang][elmType]=col
    IDE.IDE_redefineHilighterColors()
    IDE.IDE_refreshWorkspace(all=True)

def updateSynColors():
    # on Linux, SimpleHtmlListBox's children can't be removed by Clear(),
    # so I have to change them 1 by 1
    i=0
    for s in getHilighterColorsAsHtml('python'):
        pythonSyntaxList.SetString(i,s)
        i+=1
    IDE.IDE_redefineHilighterColors()
    IDE.IDE_refreshWorkspace(all=True)

def restoreSynColors(e):
    if YesNoDialog('Restore ALL HIGHLIGHTER COLORS to default setting ?'):
       IDE.HL_COLORS=deepcopy(IDE.DEF_HL_COLORS)
       updateSynColors()

def loadSynColors(e):
    res=loadStuff('Load hilighter colors','*.hilight')
    if res:
       lang='python'
       res=res[lang]
       colors=IDE.HL_COLORS[lang]
       for k,v in list(res.items()):
           if k in colors:
              colors[k]=v
       updateSynColors()

def saveSynColors(e):
    saveStuff(IDE.HL_COLORS,'Save hilighter colors','*.hilight')


def colorSelected(colType,e):
    col=e.GetValue()[:3]
    # the red channel must not be 0, so it's scalable and the error red blink can be visible
    if colType in (IDE.COL_tabTextActive,IDE.COL_tabTextInactive) and\
       col[0]==0:
         col=(1,)+col[1:]
    IDE.IDE_CFG[IDE.CFG_colors][colType]=col
    updateGenColors()

def updateGenColors():
    IDE.IDE_redefineColors()
    IDE.IDE_updateGeneralColors()
    pythonSyntaxList.SetBackgroundColour(IDE.IDE_CFG[IDE.CFG_colors][IDE.COL_WSback])
    pythonSyntaxList.Refresh()
    colTypes=dict([reversed(i) for i in list(IDE.GEN_COLORS_DESC.items())])
    colors=IDE.IDE_CFG[IDE.CFG_colors]
    for c in IDE.getWxSizerWidgets(pythonSyntaxList.GetParent().GetSizer()):
        if type(c)==ColourSelect:
           label=c.GetLabel()
           if label in colTypes:
              c.SetColour(colors[colTypes[label]])

def restoreGenColors(e):
    if YesNoDialog('Restore ALL GENERAL COLORS to default setting ?'):
       IDE.IDE_CFG[IDE.CFG_colors]=deepcopy(IDE.DEF_GEN_COLORS)
       updateGenColors()

def loadGenColors(e):
    res=loadStuff('Load general colors','*.colors')
    if res:
       colors=IDE.IDE_CFG[IDE.CFG_colors]
       for k,v in list(res.items()):
           if k in colors:
              colors[k]=v
       updateGenColors()

def saveGenColors(e):
    saveStuff(IDE.IDE_CFG[IDE.CFG_colors],'Save general colors','*.colors')


def actionsCategorySelected(sizer,oldKeysChoice,e):
    for w in IDE.getWxSizerWidgets(sizer):
        w.Disable()
    oldKeysChoice.Clear()
    keyText.SetValue('None')
    KM.reset()
    updateKeyStatus()
    updateKeyMapList()

def actionSelected(sizer,oldKeysChoice,e):
    for w in IDE.getWxSizerWidgets(sizer):
        w.Enable()
    sel=actionsList.GetItemData(actionsList.FocusedItem)
    act,keysStr=actionsList.itemDataMap[sel]
    sizer=oldKeysChoice.GetContainingSizer()
    if keysStr:
       oldKeysChoice.SetItems(keysStr.split(' | '))
       oldKeysChoice.SetSelection(0)
    else:
       oldKeysChoice.Clear()
       for w in IDE.getWxSizerWidgets(sizer):
           w.Disable()
    # enable/disable "Restore default" based on keys availability in the default keymap
#     getattr(sizer.GetChildren()[2].GetWindow(),'Enable' if IDE.IDE_DEF_KEYMAP[act] else 'Disable')()
    sizer.GetChildren()[2].GetWindow().Enable()
    keyText.SetValue('None')
    KM.reset()
    updateKeyStatus()

def addActionKey(e,clearCurrentKeys=False):
    sel=actionsList.GetItemData(actionsList.FocusedItem)
    act=actionsList.itemDataMap[sel][0]
    #~ print 'sel:',sel,act
    key=KM.getP3Devent()
    if key and key not in KEYMAP_COPY[act]:
       keyUsers=getKeyUsers(key,act)
       if keyUsers: # key is already used by other actions
          if not YesNoDialog('This key is already used by other action(s).\nDo you want to steal it ?'):
             keyText.SetFocus()
             return
       if keyUsers: # GO STEAL IT
          for a in keyUsers:
              KEYMAP_COPY[a].remove(key)
       if clearCurrentKeys:
          KEYMAP_COPY[act]=[]
       KEYMAP_COPY[act]+=[key]
       updateKeyMapList(sel)

def restoreActionDefaultKeys(e):
    sel=actionsList.GetItemData(actionsList.FocusedItem)
    act=actionsList.itemDataMap[sel][0]
    keys=IDE.IDE_DEF_KEYMAP[act]
    notRestored=False
    newKeys=list(keys)
    for key in keys:
        keyUsers=getKeyUsers(key,act)
        if act in keyUsers: # don't list itself
           keyUsers.remove(act)
        if keyUsers:
           newKeys.remove(key)
           notRestored=True
    if notRestored:
       wx.MessageDialog(None,
          message='Some of the default keys are already used by other action(s).\nThey are not restored.',
          caption='!!! WARNING !!!', style=wx.ICON_INFORMATION).ShowModal()
    KEYMAP_COPY[act]=newKeys
    updateKeyMapList(sel)

def clearActionKey(oldKeysChoice):
    keyIdx=oldKeysChoice.GetSelection()
    sel=actionsList.GetItemData(actionsList.FocusedItem)
    act=actionsList.itemDataMap[sel][0]
    del KEYMAP_COPY[act][keyIdx]
    updateKeyMapList(sel)

def getKeyUsers(P3Devent,act):
    modes=IDE.MODES_OF_ACT[act]
    acts=[]
    for m in modes:
        acts+=IDE.ACTS_IN_MODES[m]
    currAssignments=[]
    for a in set(acts):
        if P3Devent in KEYMAP_COPY[a]: # USED
           currAssignments.append(a)
    return currAssignments

def getActionsKeysInCategory(catID):
    actNkeys=[]
    for act,km in list(KEYMAP_COPY.items()):
        if IDE.CAT_OF_ACT[act]==catID:
           alternateKeys=[]
           for k in km:
               evts = k[:-1].split('-')+['-'] if k[-1]=='-' else k.split('-')
               if '' in evts:
                  evts.remove('')
               alternateKeys.append( ' '.join([KM.P3D2key[evt] for evt in evts]) )
           actNkeys.append( [act+'\t'+IDE.IDE_ACT_DESC[act], ' | '.join(alternateKeys)] )
    actNkeys.sort()
    return actNkeys

def updateKeyMapList(sel=None):
    catList=keymapTB.GetTreeCtrl()
    cat=catList.GetItemText(catList.Selection)
    catID=CAT_ID[cat]
    actNkeys=getActionsKeysInCategory(catID)
    actionsList.DeleteAllItems()
    actionsList.initSorter(actNkeys,init=not hasattr(actionsList,'_col'))
#     if actionsList._col>-1:
#        actionsList.SortListItems(actionsList._col,actionsList._colSortFlag[actionsList._col])
#        actionsList.OnSortOrderChanged()
    if sel is not None:
       actionsList.Focus(sel)
       actionsList.Select(sel,1)
       actionsList.EnsureVisible(sel)

def updateKeyStatus():
    if KM.value:
       P3Devent=KM.getP3Devent()
       # searches if the event is already used by other action at the same time frame,
       # ie. modes in which that action exists
       sel=actionsList.GetItemData(actionsList.FocusedItem)
       act=actionsList.itemDataMap[sel][0]
       keyUsers=getKeyUsers(P3Devent,act)
       if keyUsers:
          val=['^ itself ^' if act==a else '(%s) %s'%(CAT_NAME[IDE.CAT_OF_ACT[a]],IDE.IDE_ACT_DESC[a]) for a in keyUsers]
       else:
          val=["None"]
       keyStatusList.SetItems(val)
    else:
       keyStatusList.Clear()

def restoreAllDefaultKeys(e):
    global KEYMAP_COPY
    if YesNoDialog('Restore ALL KEYS to default setting ?'):
       KEYMAP_COPY=deepcopy(IDE.IDE_DEF_KEYMAP)
       lastCat=keymapTB.Selection
       keymapTB.SetSelection((lastCat+1)%keymapTB.GetPageCount())
       keymapTB.SetSelection(lastCat)

def listKeymap(actTextPadCB):
    pad=actTextPadCB.Value
    text=''
    for c,n in list(CAT_NAME.items()):
        actNkeys=getActionsKeysInCategory(c)
        text+='%s[ %s ]\n'%('\n'*2 if c>0 else '', n.upper())
        maxlen=0
        for ank in actNkeys:
            ank[0]=ank[0][ank[0].find('\t')+1:]
            actlen=len(ank[0])
            if actlen>maxlen:
               maxlen=actlen
        for act,keys in actNkeys:
            text+='%s  : %s\n'%(act.ljust(pad*maxlen),keys)
    IDE.IDE_newDoc()
    fn=IDE.IDE_doc.FileName
    IDE.IDE_doc.FileName=fn[:fn.find('.')+1].replace('New-','KeyMap-')+'txt'
    IDE.IDE_doc.hilight=IDE.IDE_HL_None
    IDE.IDE_paste(text)

def loadKeymap(e):
    global KEYMAP_COPY
    res=loadStuff('Load keymap','*.keys')
    if res:
       KEYMAP_COPY=res
       updateKeyMapList()

def saveKeymap(e):
    saveStuff(KEYMAP_COPY,'Save keymap','*.keys')



def fileTabSkinSet(e):
    availSkins=IDE.IDE_getAvailTabSkins()
    loc=e.EventObject.GetStringSelection()
    oldIdx=availSkins.index(IDE.IDE_CFG[IDE.CFG_fileTabSkin])
    newIdx=availSkins.index(loc)
    IDE.IDE_cycleTabSkin(newIdx-oldIdx)
    e.EventObject.GetParent().Refresh()

def sliderSkinSet(e):
    availSkins=IDE.IDE_getAvailSliderSkins()
    loc=e.EventObject.GetStringSelection()
    oldIdx=availSkins.index(IDE.IDE_CFG[IDE.CFG_sliderSkin])
    newIdx=availSkins.index(loc)
    IDE.IDE_cycleSliderSkin(newIdx-oldIdx)
    e.EventObject.GetParent().Refresh()

def caretSet(ins,e):
    ct=e.EventObject.GetStringSelection()
    IDE.IDE_CFG[IDE.CFG_insCaret if ins else IDE.CFG_ovrCaret]=[k for k,v in list(IDE.CAR_DESC.items()) if v==ct][0]
    IDE.IDE_updateCaretsTypes()


def manualCheckUpdate(checkUpdateButton,mustBeUpdatedText,updateButton,updateDetailText,e):
    if IDE.IDE_isUpgrading: return
    print('CHECKING UPGRADES...')
    frame=checkUpdateButton.GetParent()
    sizer=frame.GetSizer()
    updateButton.Hide()
    updateDetailText.Hide()
    checkUpdateButton.Disable()
    mustBeUpdatedText.Label='Checking upgrades...'
    mustBeUpdatedText.Show()
    frame.DLlistSizer.Clear(1)
    sizer.Layout()
    def updatesListReceived(mustBeUpdated,releaseVersion):
        focus = None
        if mustBeUpdated:
           mustBeUpdatedText.releaseVersion = releaseVersion
           mustBeUpdatedText.mustBeUpdated = mustBeUpdated
           mustBeUpdatedText.buildDownloadItems()
           updateButton.Show()
           focus = updateButton
        elif mustBeUpdated is not None:
           mustBeUpdatedText.Label='The IDE is up to date.'
        else:
           mustBeUpdatedText.Label='ERROR: failed to get upgrades list.'
           focus = checkUpdateButton
        checkUpdateButton.Enable()
        sizer.Layout()
        if focus:
           focus.SetFocus()
    IDE.IDE_getUpdatesList(updatesListReceived)

def doUpdate(serverRB,checkUpdateButton,mustBeUpdatedText,updateButton,updateDetailText,e):
    IDE.IDE_isUpgrading = True
    IDE.IDE_removeUpdateEndsButton()
    mustBeUpdated = mustBeUpdatedText.mustBeUpdated
    frame = updateButton.GetParent()
    sizer = frame.GetSizer()
    uncheckedItem = []
    for updateKey in ('code','TextDrawer source'):
        if updateKey in mustBeUpdated:
           updateKeyIdx = mustBeUpdated.index(updateKey)
           updateKeyCB = frame.DLlistSizer.GetItem(updateKeyIdx*3+1).GetWindow()
           if not updateKeyCB.Value:
              uncheckedItem.append(updateKey)
    if uncheckedItem:
       for item in uncheckedItem:
           mustBeUpdated.remove(item)
    # rebuild download items, to remove the unchecked item and leave the check box
    mustBeUpdatedText.buildDownloadItems(withCB=False)
    mustBeUpdatedText.Label = DOWNLOADING_UPGRADES # must be after buildDownloadItems()
    updateButton.Hide()
    updateDetailText.Hide()
    serverRB.Disable()
    checkUpdateButton.Disable()
    sizer.Layout()
#     frame.Update()
    mustBeUpdatedText.idx = 0
    def getUpdate():
        while mustBeUpdatedText.idx<len(mustBeUpdated) and not mustBeUpdated[mustBeUpdatedText.idx]: # already installed
           mustBeUpdatedText.idx+=1
        package = IDE.IDE_PACKAGES[mustBeUpdated[mustBeUpdatedText.idx]]
        animCtrl = frame.DLlistSizer.GetItem(mustBeUpdatedText.idx*3).GetWindow()
        animCtrl.Animation = mustBeUpdatedText.DLanim
        animCtrl.Play()
        gauge = frame.DLlistSizer.GetItem(mustBeUpdatedText.idx*3+2).GetWindow()
        fullpath = os.path.join(IDE.IDE_path, package)

        http = HTTPClient()
        channel = http.makeChannel(True)
        channel.beginGetDocument(DocumentSpec('http://ynjh.%s/OIDE/%s'%(UPGRADE_SRV[IDE.IDE_CFG[IDE.CFG_host]],package)))
        fullpath = fullpath.replace('%20',' ')
        channel.downloadToFile(Filename.fromOsSpecific(fullpath))
        def downloadTask(task):
            if channel.isFileSizeKnown() and not task.filesize:
               task.filesize = float(channel.getFileSize())
               gauge.Show()
            if channel.run():
               if task.filesize:
                  gauge.Value = DOWNLOAD_GAUGE_RANGE*channel.getBytesDownloaded()/task.filesize
#                   print gauge.Value
#                   IDE.WxStep()
               return task.cont
            if channel.isDownloadComplete():
               gauge.Hide()
               if os.path.exists(fullpath):
                  z = zipfile.ZipFile(fullpath)
                  for f in z.namelist():
                      if not isinstance(f, zipfile.ZipInfo):
                         f = z.getinfo(f)
                      try:
                         z._extract_member(f,IDE.IDE_path,None)
                      except:
                         pass
                  z.close()
               # clears the downloaded packages, in case the next download fails,
               # the already installed ones won't be re-downloaded again
               mustBeUpdatedText.mustBeUpdated[mustBeUpdatedText.idx]=''
               animCtrl.Animation = mustBeUpdatedText.completeAnim
               mustBeUpdatedText.idx+=1
               if mustBeUpdatedText.idx==len(mustBeUpdated): # ALL UPDATES ARE INSTALLED
                  mustBeUpdatedText.Label=UPGRADES_SUCCESSFUL
                  updateDetailText.Label='\nPlease restart the IDE to enjoy the upgrades.'
                  updateDetailText.Show()
                  updateButton.Hide()
                  error = False
               else: # DOWNLOAD THE NEXT ITEM
                  getUpdate()
                  return
            else:
               print("Error downloading file.")
               updateButton.Show()
               updateDetailText.Show()
               updateDetailText.Label='ERROR: download failed'
               animCtrl.Animation = mustBeUpdatedText.failAnim
               error = True
            serverRB.Enable()
            checkUpdateButton.Enable()
            sizer.Layout()
            if error:
               updateButton.SetFocus()
            IDE.IDE_isUpgrading = False
            IDE.IDE_downloadUpdateEnds(error=error)
        task = taskMgr.add(downloadTask, IDE.IDE_tasksName+'download update item')
        task.filesize = 0
    getUpdate()


def loadStuff(title,wildcard):
    Fdlg = wx.FileDialog(None, title, wildcard=wildcard,
        defaultDir=IDE.IDE_settingsPath, style=wx.OPEN)
    if Fdlg.ShowModal() == wx.ID_OK:
       path=Fdlg.GetPath()
       try:
           return IDE.loadFromFile(path)
       except IOError as xxx_todo_changeme:
           (errno,errstr) = xxx_todo_changeme.args
           wx.MessageDialog(None,
              message='E R R O R :\n'+errstr+'\n\nUnable to load "%s"'%path,
              caption='!!! ERROR !!!', style=wx.ICON_INFORMATION).ShowModal()

def saveStuff(stuff,title,wildcard):
    Fdlg = wx.FileDialog(None, title, wildcard=wildcard,
           defaultDir=IDE.IDE_settingsPath, style=wx.SAVE|wx.FD_OVERWRITE_PROMPT)
    if Fdlg.ShowModal() == wx.ID_OK:
       path=Fdlg.GetPath()
       if not path.endswith(wildcard[1:]):
          path+=wildcard[1:]
       try:
           IDE.dumpToFile(stuff,path)
       except IOError as xxx_todo_changeme1:
           (errno,errstr) = xxx_todo_changeme1.args
           wx.MessageDialog(None,
              message='E R R O R :\n'+errstr+'\n\nUnable to save "%s"'%path,
              caption='!!! ERROR !!!', style=wx.ICON_INFORMATION).ShowModal()

def YesNoDialog(msg):
    Mdlg = wx.MessageDialog(None,msg, caption='Please confirm',
      style=wx.YES_NO|wx.NO_DEFAULT|wx.ICON_QUESTION|wx.CENTER)
    res=Mdlg.ShowModal()
    Mdlg.Destroy()
    return True if res==wx.ID_YES else False

def closePreferences(e,saveKM=False,saveGC=False,saveHC=False,saveOthers=False,save=False):
    global PREF_OPEN
    KMchanged=IDE.IDE_KEYMAP!=KEYMAP_COPY
    GCchanged=IDE.IDE_CFG[IDE.CFG_colors]!=CFG_ORIG[IDE.CFG_colors]
    HCchanged=IDE.HL_COLORS!=HL_COLORS_ORIG
    others=list(IDE.IDE_CFG.keys())
    others.remove(IDE.CFG_colors)
    othersChanged=bool([1 for c in others if IDE.IDE_CFG[c]!=CFG_ORIG[c]])
    discarded=''
    if KMchanged and (not save or (save and not saveKM)):
       discarded+='keymap'
    if GCchanged and (not save or (save and not saveGC)):
       discarded+=(', ' if len(discarded) else '')+'general colors'
    if HCchanged and (not save or (save and not saveHC)):
       discarded+=(', ' if len(discarded) else '')+'hilighter colors'
    if othersChanged and (not save or (save and not saveOthers)):
       discarded+=(', ' if len(discarded) else '')+'others'

    if discarded: # something was changed, warn user
       Mdlg = wx.MessageDialog(None,
         'Some settings (%s) have been changed.\n\nAre you sure to discard them ?'%discarded,
         caption='Please confirm',style=wx.YES_NO|wx.NO_DEFAULT|wx.ICON_QUESTION|wx.CENTER)
       if Mdlg.ShowModal() in (wx.ID_NO,wx.ID_CANCEL):
          return

    if IDE.IDE_isUpgrading:
       prefScreen.Lower()
    else:
       IDE.IDE_lastPreferencePage=prefNotebook.Selection
       IDE.IDE_lastKeymapCategory=keymapTB.Selection
       IDE.IDE_closeWxInterface(e,restoreMode=False)
       PREF_OPEN=False
       IDE.IDE_removeUpdateEndsButton()
    # saves settings
    if GCchanged and saveGC:
       # overwrite orig colors, so if other settings are NOT saved, GC will be
       CFG_ORIG[IDE.CFG_colors]=IDE.IDE_CFG[IDE.CFG_colors]
    else:
       IDE.IDE_CFG[IDE.CFG_colors]=CFG_ORIG[IDE.CFG_colors]
    # must be done after GeneralColors, because GC is in "other settings"
    if othersChanged and not saveOthers:
       # restores appearance changes
       availSkins=IDE.IDE_getAvailTabSkins()
       oldIdx=availSkins.index(CFG_ORIG[IDE.CFG_fileTabSkin])
       newIdx=availSkins.index(IDE.IDE_CFG[IDE.CFG_fileTabSkin])
       IDE.IDE_cycleTabSkin(oldIdx-newIdx)
       availSkins=IDE.IDE_getAvailSliderSkins()
       oldIdx=availSkins.index(CFG_ORIG[IDE.CFG_sliderSkin])
       newIdx=availSkins.index(IDE.IDE_CFG[IDE.CFG_sliderSkin])
       IDE.IDE_cycleSliderSkin(oldIdx-newIdx)
       IDE.IDE_CFG=CFG_ORIG
    if save:
       IDE.IDE_saveCFGtoFile()
    if HCchanged and save and saveHC:
       IDE.IDE_saveHilighterToFile()
    else:
       IDE.HL_COLORS=HL_COLORS_ORIG
    if KMchanged and save and saveKM:
       IDE.IDE_applyKeys(KEYMAP_COPY)
    # updates visual
    IDE.IDE_updateCaretsTypes()
    IDE.IDE_redefineColors()
    IDE.IDE_updateGeneralColors()
    IDE.IDE_redefineHilighterColors()
    updateLogTex = lastWSfontPPU!=IDE.IDE_CFG[IDE.CFG_WSfontPPU] or \
                   lastWSfontSpacing!=IDE.IDE_CFG[IDE.CFG_WSfontSpacing]
    IDE.IDE_setWSfontProps( IDE.IDE_CFG[IDE.CFG_WSfontPPU],
                            IDE.IDE_CFG[IDE.CFG_WSfontSpacing],
                            updateLogTex=updateLogTex)
#     IDE.IDE_refreshWorkspace(all=True)
    IDE.IDE_setBlockColorAnim(IDE.IDE_CFG[IDE.CFG_animSelColor])
    IDE.IDE_scheduleNextUpdate()
