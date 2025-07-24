################
VERSION='v0.5.4'
################

from pandac.PandaModules import PandaSystem
from direct.showbase.PythonUtil import Functor, intersection
from threading import Timer
from textwrap import TextWrapper
from glob import glob
import os, sys, imp, pickle, random, time, types, wx
from wx.py.editwindow import EditWindow

P3D_imports=[
'from pandac.PandaModules import *',
'from direct.actor.Actor import Actor',
'from direct.showbase.DirectObject import DirectObject',
'from direct.gui.DirectGui import *',
'from direct.gui.OnscreenText import OnscreenText',
'from direct.gui.OnscreenImage import OnscreenImage',
'from direct.interval.IntervalGlobal import *',
'from direct.task import Task',
'from direct.showbase import PythonUtil as PU',
]
Python_imports=[
'import imp, glob',
'import os, sys',
'import string, re',
'import cPickle',
'import random',
'import math',
'import time',
'import types',
'import traceback',
]

# wxlist=filter(lambda k: k.lower().find('wxevt_')>-1,vars(wx))
# wxlist.sort()
# print '\n'.join(wxlist)

joinPaths=os.path.join
LAST_FILES='lastFiles'
RECENT_FILES='recentFiles'
FILES_PROPS='filesProps'
LABEL_later='Maybe later...'
LABEL_close='not now'
LABEL_mainFile = '&main file :'
LABEL_CWD = 'working &directory :' 
LABEL_args = '&arguments :'
LABEL_enablePStats = 'enable performance &profiler (PStats)'
PLATFORM=sys.platform[:3]
TW=TextWrapper()
TW.width=74
NA='n/a'
FILESEP='*'*4
IDEfile='IDEmini.py'

def exit():
    if PLATFORM=='win' and int(sys.version.split()[0].replace('.','')[:2])>25:
       os._exit(0)
    else:
       sys.exit()

def loadFromFile(path):
    f=open(path,'rU')
    obj=pickle.load(f)
    f.close()
    return obj

def getParentDirs(f):
    pardirs=[]
    dir=os.path.dirname(f)
    while not os.path.ismount(dir):
        pardirs.append(dir)
        dir=os.path.dirname(dir)
    if dir!=os.sep:
       pardirs.append(dir)
    return pardirs

def getCWDnArgs(f):
    if f in IDE_filesProps:
       if len(IDE_filesProps[f])>7:
          cwd,args=IDE_filesProps[f][-2:]
          if cwd=='.':
             cwd=os.path.dirname(f)
          return cwd,args
    print(f)
    return os.path.dirname(f),[]

def args2Str(args):
    newArgs=[a if a.find(' ')==-1 else '"%s"'%a for a in args]
    return ' '.join(newArgs)

def quotedArgs(args):
    newArgs=[a if a.find(' ')==-1 else '"%s"'%a for a in args]
    return newArgs

def str2Args(s):
    args=[]
    i=0
    for a in s.split('"'):
        args+=[a] if i%2 else a.split()
        i+=1
    return args

def startIDE(files,mainNcurrFile,PStatsEnabled,cwd,args,lastSession=0):
    if 'welcomeScreen' in globals():
       welcomeScreen.Destroy()
       app.Dispatch()
    the_files='"[%s]"'%FILESEP.join(files)
    if not mainNcurrFile:
       mainNcurrFile=['??']
    if len(mainNcurrFile)<3:
       mainNcurrFile.append(cwd)
    else:
       mainNcurrFile[2]=cwd
    print('\nSTARTING IDE.....')
    # SPAWN A FRESH PYTHON SESSION, be sure to enable interactive mode
    params=[' -i ', IDEfile, the_files, ' %s'%lastSession, ' "[%s]"'%FILESEP.join(mainNcurrFile),
            ' "%s"'%sys.executable, ' %i'%PStatsEnabled ] + quotedArgs(str2Args(args))
    if PLATFORM=='dar':
       os.spawnlp(os.P_NOWAIT, sys.executable, *params)
       exit()
    else:
       os.execl(sys.executable.replace('pythonw','python'), *params)


CMDargs=sys.argv[1:]
APPargs=''
if '-a' in CMDargs:
   argsIdx=CMDargs.index('-a')
   APPargs=' '.join([ '"%s"'%a for a in CMDargs[argsIdx+1:] ])
   del CMDargs[argsIdx:]
# files fed via command line
files=[ os.path.abspath(p) for p in sum([glob(a) for a in CMDargs],[]) if os.path.isfile(p)]

# sets the working dir to the script's location, just to ease the pain
if sys.path[0]=='':
   sys.path[0]=os.getcwd()
# chdir() must be done after glob() above to get correct absolute paths
os.chdir(sys.path[0])

# files records
filesPropsName=joinPaths(sys.path[0],'%s.%s'%(FILES_PROPS,PLATFORM))
if os.path.exists(filesPropsName):
   IDE_filesProps=loadFromFile(filesPropsName)
else:
   IDE_filesProps={}

if len(files):
   mainFile=None
   for p in files:
       try:
           modType=imp.find_module(os.path.basename(os.path.splitext(p)[0]), [os.path.dirname(p)])[-1][-1]
           if modType==imp.PY_SOURCE:
              mainFile=p
              break
       except:
           pass
   # no python file at all, just pretend the first file is the main file
   if mainFile is None:
      mainFile=files[0]
   props_CWD, props_args=getCWDnArgs(mainFile)
   args=args2Str(props_args)
   startIDE(files, [mainFile]*2, False, props_CWD, APPargs if props_args!=APPargs!='' else args,
            lastSession=1)


CfgVarsLoaded=False
def loadCfgVars():
    global CfgVarsLoaded,ConfigVariable
    from pandac.PandaModules import loadPrcFileData,ConfigVariable
    OLD_CFG_VAR_winSize=ConfigVariable('win-size').getStringValue()
    OLD_CFG_VAR_undecorated=ConfigVariable('undecorated').getStringValue()
    # to populate all config variables value, the main window must be opened,
    # so override some variables to keep the window unnoticeable
    loadPrcFileData('','''
      win-size 1 1
      undecorated 1
    ''')
    import direct.directbase.DirectStart
    base.closeWindow(base.win)
    # restores the overriden old variables
    loadPrcFileData('','''
      win-size %s
      undecorated %s
    '''%(OLD_CFG_VAR_winSize,OLD_CFG_VAR_undecorated))
    CfgVarsLoaded=True


def destroy(win,ce):
    win.Close()
    welcomeScreen.Show()
    welcomeScreen.Raise()
    WELCOME_openLastEditedFilesBtn.SetFocus()

def getCheckListBoxSelectedStrings(CLB):
    sel=[]
    for i in range(CLB.Count):
        if CLB.IsChecked(i):
           sel.append(CLB.GetString(i))
    return sel


def closing(ce):
    ce.Skip()
    closeBtn.SetLabel('sure ?')

def closeNow(ce):
    ce.Skip()
    closeBtn.SetLabel(LABEL_later)

def enableWelcomeScreen(ce):
    ce.Skip()
    welcomeScreen.Show()
    welcomeScreen.Enable()
    welcomeScreenPanel.Enable()



#_______________________________________________________________________________
class OpenLastEditedFiles(wx.Frame):
  def __init__(self,ce):
      welcomeScreen.Disable()
      welcomeScreenPanel.Disable()
      wx.Frame.__init__(self, None, -1, 'Open Last Edited Files', style=wx.RESIZE_BORDER|wx.FRAME_NO_TASKBAR)
      self.SetBackgroundColour(COLOR_optionsScreen)
      self.Bind(wx.EVT_CLOSE,enableWelcomeScreen)
      panel = wx.Panel(self)

      openLastEditedFilesSizer = wx.BoxSizer(wx.VERTICAL)

      openLastEditedFilesText = wx.StaticText(panel, -1, 'Open Last Edited Files')
      openLastEditedFilesText.SetFont(optionFont)

      openLastEditedFilesSizer.Add(openLastEditedFilesText, 0, wx.ALL|wx.ALIGN_CENTER, 5)

      self.lastFiles=[]
      self.mainNcurrFile=[]
      lastFiles='%s.%s'%(LAST_FILES,PLATFORM)
      if not os.path.exists(lastFiles):
         lastFiles=LAST_FILES
      elif os.path.exists(LAST_FILES):
         os.remove(LAST_FILES)
      if os.path.exists(lastFiles):
         f=open(lastFiles,'rU')
         lastFs=pickle.load(f)
         f.close()
         listdata=[i for i in lastFs if type(i)==list]
         if listdata:
            self.mainNcurrFile=listdata[0]
            if self.mainNcurrFile[1] is None:
               self.mainNcurrFile[1]=self.mainNcurrFile[0]
            lastFs.remove(self.mainNcurrFile)

         # if the CWD was saved at previous run, use it by default
         preferedCWD=None
         if os.path.isdir(lastFs[-1]):
            preferedCWD=lastFs.pop()
#          else: # otherwise, use main file's dir (OLD VERSION, READY FOR REMOVAL)
#             preferedCWD=os.path.dirname(lastFs[0])
         if len(self.mainNcurrFile)==2:
            if preferedCWD is None:
               preferedCWD=os.path.dirname(self.mainNcurrFile[0])
            self.mainNcurrFile.append(preferedCWD)
         elif len(self.mainNcurrFile)==3:
            preferedCWD=self.mainNcurrFile[2]

         self.lastFiles=lastFs
         lastFilesExist=len(self.lastFiles)
         if lastFiles==LAST_FILES: # from now on, use PLATFORM as extension
            os.rename(LAST_FILES,'%s.%s'%(LAST_FILES,PLATFORM))
      else:
         lastFilesExist=0

      self.lastFilesAll=list(self.lastFiles)
      self.lastFilesList = wx.CheckListBox(panel, size=(415,280), choices=self.lastFiles)
      self.lastFilesList.SetToolTipString('check the files you need')

      firstFileExist=-1
      for i in range(len(self.lastFiles)):
          self.lastFilesList.Check(i,1)
          if os.path.exists(self.lastFiles[i]) and firstFileExist<0:
             firstFileExist=i
      if not lastMainFileExists and self.mainNcurrFile:
          self.lastFilesList.Check(self.lastFiles.index(self.mainNcurrFile[0]),0)
      self.lastFilesList.Bind(wx.EVT_CHECKLISTBOX,self.lastFileChecked)

      mainFileText = wx.StaticText(panel, -1, LABEL_mainFile)
      self.lastFilesChoice = wx.Choice(panel, choices=self.lastFiles, size=(415,-1))
      mainFileIdx=self.lastFiles.index(self.mainNcurrFile[0]) if lastMainFileExists and self.mainNcurrFile else firstFileExist
         
      self.lastFilesChoice.Select(mainFileIdx)
      self.lastFilesChoice.Bind(wx.EVT_CHOICE,self.mainFileSelected)

      preferedCWD,preferedArgs=getCWDnArgs(self.lastFiles[mainFileIdx])

      CWDtext = wx.StaticText(panel, -1, LABEL_CWD)
      self.CWDchoice = wx.Choice(panel, size=(415,-1))
      parentDirs=getParentDirs(self.lastFiles[mainFileIdx])
      self.CWDchoice.SetItems(parentDirs)
      if preferedCWD in parentDirs:
         self.CWDchoice.SetStringSelection(preferedCWD)
      else:
         self.CWDchoice.SetSelection(0)

      ARGtext = wx.StaticText(panel, -1, LABEL_args)
      self.APPargs = wx.TextCtrl(panel, size=(415,-1), value=args2Str(preferedArgs))

      self.PStatsCheck = wx.CheckBox(panel, -1, LABEL_enablePStats)

      self.openLastEditedFilesBtn = wx.Button(panel, -1, 'Bring it ON !')
      self.openLastEditedFilesBtn.SetFont(optionFont)
      self.openLastEditedFilesBtn.Bind(wx.EVT_BUTTON,self.openLastFiles)

      closeBtn = wx.Button(panel, -1, LABEL_close, style=wx.BU_EXACTFIT)
      closeBtn.Bind(wx.EVT_BUTTON,Functor(destroy,self))

      openLastEditedFilesSizer.Add(self.lastFilesList, 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 5)
      openLastEditedFilesSizer.Add(mainFileText, 0, wx.LEFT|wx.TOP, 5)
      openLastEditedFilesSizer.Add(self.lastFilesChoice, 0, wx.ALL|wx.EXPAND, 5)
      openLastEditedFilesSizer.Add(CWDtext, 0, wx.LEFT, 5)
      openLastEditedFilesSizer.Add(self.CWDchoice, 0, wx.ALL|wx.EXPAND, 5)
      openLastEditedFilesSizer.Add(ARGtext, 0, wx.LEFT, 5)
      openLastEditedFilesSizer.Add(self.APPargs, 0, wx.ALL|wx.EXPAND, 5)
      openLastEditedFilesSizer.Add((5,10))
      openLastEditedFilesSizer.Add(self.PStatsCheck, 0, wx.ALL|wx.ALIGN_CENTER, 5)
      openLastEditedFilesSizer.Add(self.openLastEditedFilesBtn, 0, wx.ALIGN_CENTER, 5)
      openLastEditedFilesSizer.Add(closeBtn, 0, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER, 5)

      if lastFilesExist:
         self.openLastEditedFilesBtn.SetFocus()
      else:
         self.lastFilesList.Disable()
         mainFileText.Disable()
         self.lastFilesChoice.Disable()
         self.openLastEditedFilesBtn.Disable()

      welcomeScreen.Hide()
      panel.SetSizer(openLastEditedFilesSizer)
      openLastEditedFilesSizer.Fit(self)
      openLastEditedFilesSizer.SetSizeHints(self)
      self.Center()
      self.Show()
      self.Raise()

      if not lastMainFileExists and self.mainNcurrFile:
         wx.MessageDialog(self,
            message='Last edited main file does not exist :\n%s\n\nUsing the first available file instead.'%self.mainNcurrFile[0],
            caption='!!! WARNING !!!', style=wx.ICON_INFORMATION).ShowModal()

  def openLastFiles(self,ce):
      mainMod=self.lastFilesChoice.GetStringSelection()
      if self.mainNcurrFile:
         self.mainNcurrFile[0]=mainMod
      else:
         self.mainNcurrFile.append(mainMod)
      startIDE( self.lastFiles,self.mainNcurrFile,self.PStatsCheck.Value,
                self.CWDchoice.GetStringSelection(),self.APPargs.Value,lastSession=1)

  def mainFileSelected(self,ce):
      sel=self.lastFilesChoice.GetStringSelection()
      if not os.path.exists(sel):
         wx.MessageDialog(self,
            message='The selected file does not exist :\n%s\n\nUsing the first file instead.'%sel,
            caption='!!! WARNING !!!', style=wx.ICON_INFORMATION).ShowModal()
         self.lastFilesChoice.SetSelection(0)
      sel=self.lastFilesChoice.GetStringSelection()
      cwd,args=getCWDnArgs(sel)
      self.CWDchoice.SetItems(getParentDirs(sel))
      self.CWDchoice.SetStringSelection(cwd)
      self.APPargs.Value = args2Str(args)

  def lastFileChecked(self,ce):
      self.lastFiles=[self.lastFilesAll[i] for i in range(len(self.lastFilesAll)) if self.lastFilesList.IsChecked(i)]
      lastSelection=self.lastFilesChoice.GetStringSelection()
      self.lastFilesChoice.SetItems(self.lastFiles)
      if self.lastFiles:
         self.CWDchoice.Enable()
         self.APPargs.Enable()
         self.lastFilesChoice.Enable()
         if lastSelection not in self.lastFiles:
            self.lastFilesChoice.Select(0)
            self.lastFilesChoice.ProcessEvent(wx.CommandEvent(wx.wxEVT_COMMAND_CHOICE_SELECTED))
         else:
            self.lastFilesChoice.Select(self.lastFiles.index(lastSelection))
         self.openLastEditedFilesBtn.Enable()
      else:
         self.CWDchoice.Clear()
         self.CWDchoice.Disable()
         self.APPargs.Clear()
         self.APPargs.Disable()
         self.lastFilesChoice.Disable()
         self.openLastEditedFilesBtn.Disable()

#_______________________________________________________________________________
class OpenFiles(wx.Frame):
  def __init__(self,ce):
      # checks recent files list
      recentFilesListName='%s.%s'%(RECENT_FILES,PLATFORM)
      if os.path.exists(recentFilesListName):
         f=open(recentFilesListName,'rU')
         recentFiles=pickle.load(f)
         f.close()
      else:
         recentFiles=[]

      welcomeScreen.Disable()
      welcomeScreenPanel.Disable()
      wx.Frame.__init__(self, None, -1, 'Open Files', style=wx.RESIZE_BORDER|wx.FRAME_NO_TASKBAR)
      self.SetBackgroundColour(COLOR_optionsScreen)
      self.Bind(wx.EVT_CLOSE,enableWelcomeScreen)
      panel = wx.Panel(self)

      self.addedFiles = []
      self.newFiles = []
      self.mainNcurrFile=[]
      self.recentFiles = []

      openFilesSizer = wx.BoxSizer(wx.VERTICAL)

      openFilesText = wx.StaticText(panel, -1, 'Open Files')
      openFilesText.SetFont(optionFont)

      recentFilesText = wx.StaticText(panel, -1, 'Recent files (%s) :'%len(recentFiles))

      self.recentFilesList = wx.CheckListBox(panel, size=(450,140), choices=recentFiles)
      self.recentFilesList.Bind(wx.EVT_CHECKLISTBOX,self.recentFileChecked)

      browseFilesBtn = wx.Button(panel, -1, 'Add New Files')
      browseFilesBtn.Bind(wx.EVT_BUTTON,self.browseFiles)

      self.newFilesList = wx.CheckListBox(panel, size=(450,140))
      self.newFilesList.Bind(wx.EVT_CHECKLISTBOX,self.newFileChecked)

      mainFileText = wx.StaticText(panel, -1, LABEL_mainFile)

      self.filesChoice = wx.Choice(panel, size=(450,-1))
      self.filesChoice.Disable()
      self.filesChoice.Bind(wx.EVT_CHOICE,self.mainFileSet)

      CWDtext = wx.StaticText(panel, -1, LABEL_CWD)
      self.CWDchoice = wx.Choice(panel, size=(450,-1))
      self.CWDchoice.Disable()

      ARGtext = wx.StaticText(panel, -1, LABEL_args)
      self.APPargs = wx.TextCtrl(panel, size=(415,-1))
      self.APPargs.Disable()

      self.PStatsCheck = wx.CheckBox(panel, -1, LABEL_enablePStats)

      self.openFilesBtn = wx.Button(panel, wx.ID_OPEN)
      self.openFilesBtn.SetFont(optionFont)
      self.openFilesBtn.Bind(wx.EVT_BUTTON,self.openFiles)
      self.openFilesBtn.Disable()

      closeBtn = wx.Button(panel, -1, LABEL_close, style=wx.BU_EXACTFIT)
      closeBtn.Bind(wx.EVT_BUTTON,Functor(destroy,self))

      openFilesSizer.Add(openFilesText, 0, wx.ALL|wx.ALIGN_CENTER, 5)
      openFilesSizer.Add(recentFilesText, 0, wx.LEFT|wx.ALIGN_LEFT, 5)
      openFilesSizer.Add(self.recentFilesList, 0, wx.ALL|wx.ALIGN_CENTER|wx.EXPAND, 5)
      openFilesSizer.Add(browseFilesBtn, 0, wx.ALIGN_CENTER, 5)
      openFilesSizer.Add(self.newFilesList, 0, wx.ALL|wx.ALIGN_CENTER|wx.EXPAND, 5)
      openFilesSizer.Add(mainFileText, 0, wx.LEFT, 5)
      openFilesSizer.Add(self.filesChoice, 0, wx.ALL|wx.EXPAND, 5)
      openFilesSizer.Add(CWDtext, 0, wx.LEFT, 5)
      openFilesSizer.Add(self.CWDchoice, 0, wx.ALL|wx.EXPAND, 5)
      openFilesSizer.Add(ARGtext, 0, wx.LEFT, 5)
      openFilesSizer.Add(self.APPargs, 0, wx.ALL|wx.EXPAND, 5)
      openFilesSizer.Add((5,10))
      openFilesSizer.Add(self.PStatsCheck, 0, wx.BOTTOM|wx.ALIGN_CENTER, 5)
      openFilesSizer.Add(self.openFilesBtn, 0, wx.ALIGN_CENTER, 5)
      openFilesSizer.Add(closeBtn, 0, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER, 5)

      welcomeScreen.Hide()
      panel.SetSizer(openFilesSizer)
      openFilesSizer.Fit(self)
      openFilesSizer.SetSizeHints(self)
      self.Center()
      self.Show()
      self.Raise()
#       self.Update()
#       self.browseFiles(0)

  def browseFiles(self,ce):
      Fdlg = wx.FileDialog(self, "Open files",
          wildcard='*.py;*.pyw',
          style=wx.OPEN|wx.MULTIPLE)
      if Fdlg.ShowModal() == wx.ID_OK:
         new=Fdlg.GetPaths()
         onList=intersection(self.addedFiles,new)
         for p in onList:
             new.remove(p)
         if new:
            oldLen=len(self.addedFiles)
            self.addedFiles+=new
            self.newFiles+=new
            self.newFilesList.AppendItems(new)
            for i in range(oldLen,len(self.addedFiles)):
                self.newFilesList.Check(i,1)
            self.updateMainFileList(self.recentFiles+self.newFiles)
      else:
         print('Nothing was selected.')
      Fdlg.Destroy()

  def openFiles(self,ce):
      mainFile=self.filesChoice.GetStringSelection()
      files=self.recentFiles+self.newFiles
      files.remove(mainFile)
      files.insert(0,mainFile)
      startIDE(files,self.mainNcurrFile,self.PStatsCheck.Value,
               self.CWDchoice.GetStringSelection(),self.APPargs.Value)

  def recentFileChecked(self,ce):
      self.recentFiles=[]
      for i in range(self.recentFilesList.Count):
          if self.recentFilesList.IsChecked(i):
             self.recentFiles.append(self.recentFilesList.GetString(i))
      self.updateMainFileList(self.recentFiles+self.newFiles)

  def newFileChecked(self,ce):
      self.newFiles=[]
      for i in range(self.newFilesList.Count):
          if self.newFilesList.IsChecked(i):
             self.newFiles.append(self.newFilesList.GetString(i))
      self.updateMainFileList(self.recentFiles+self.newFiles)

  def updateMainFileList(self,checkedFiles):
      self.filesChoice.SetItems(checkedFiles)
      if len(checkedFiles):
         self.filesChoice.Select(0)
         self.filesChoice.Enable()
         preferedCWD,preferedArgs=getCWDnArgs(checkedFiles[0])
         self.CWDchoice.SetItems(getParentDirs(checkedFiles[0]))
         self.CWDchoice.SetStringSelection(preferedCWD)
         self.CWDchoice.Enable()
         self.APPargs.Enable()
         self.APPargs.Value=args2Str(preferedArgs)
         self.openFilesBtn.Enable()
      else:
         self.filesChoice.Disable()
         self.CWDchoice.Clear()
         self.CWDchoice.Disable()
         self.APPargs.Clear()
         self.APPargs.Disable()
         self.openFilesBtn.Disable()

  def mainFileSet(self,ce):
      f=self.filesChoice.GetStringSelection()
      preferedCWD,preferedArgs=getCWDnArgs(f)
      self.CWDchoice.SetItems(getParentDirs(f))
      self.CWDchoice.SetStringSelection(preferedCWD)
      self.APPargs.Value=args2Str(preferedArgs)


#_______________________________________________________________________________
class ConfigVar:
  def __init__(self,name):
      self.name=name
      self.var=ConfigVariable(name)
      self.oldVal=self.var.getStringValue()
      self.newVal=self.oldVal
      self.checked=False
      desc=self.var.getDescription()
      self.desc=desc.lower() if len(desc)>8 else ''

class CreateNewFile(wx.Frame):
  def __init__(self,ce):
      self.mainNcurrFile=[]
      if not CfgVarsLoaded:
         loadCfgVars()
      welcomeScreen.Disable()
      welcomeScreenPanel.Disable()
      wx.Frame.__init__(self, None, -1, 'Create New File', style=wx.RESIZE_BORDER|wx.FRAME_NO_TASKBAR)
      self.SetBackgroundColour(COLOR_optionsScreen)
      self.Bind(wx.EVT_CLOSE,enableWelcomeScreen)
      panel = wx.Panel(self)

      startFreshSizer = wx.BoxSizer(wx.VERTICAL)

      startFreshText = wx.StaticText(panel, -1, 'Create New File')
      startFreshText.SetFont(optionFont)

      pickDirBtn = wx.Button(panel, -1, 'where ?', style=wx.BU_EXACTFIT)
      pickDirBtn.Bind(wx.EVT_BUTTON,self.pickDir)
      pickDirBtn.SetFocus()

      self.dirText = wx.TextCtrl(panel,size=(325,-1))
      self.dirText.Disable()

      CWDtext = wx.StaticText(panel, -1, LABEL_CWD)
      self.CWDchoice = wx.Choice(panel, size=(390,-1))
      self.CWDchoice.Disable()

      ARGtext = wx.StaticText(panel, -1, LABEL_args)
      self.APPargs = wx.TextCtrl(panel, size=(390,-1))
      self.APPargs.Disable()

      self.filenameText = wx.TextCtrl(panel,size=(240,-1))

      self.onlyPYcheckBtn = wx.CheckBox(panel,-1,'.py* only')
      self.onlyPYcheckBtn.SetValue(1)

      pickFileBtn = wx.Button(panel, -1, 'pick name', style=wx.BU_EXACTFIT)
      pickFileBtn.Bind(wx.EVT_BUTTON,self.pickFile)

      PYfilterNpickSizer = wx.BoxSizer(wx.VERTICAL)
      PYfilterNpickSizer.Add(self.onlyPYcheckBtn, 0, wx.LEFT|wx.ALIGN_CENTER,5)
      PYfilterNpickSizer.Add(pickFileBtn, 0, wx.LEFT|wx.TOP,5)

      filenameNpickerSizer = wx.BoxSizer()
      filenameNpickerSizer.Add(self.filenameText,0,wx.ALIGN_CENTER_HORIZONTAL)
      filenameNpickerSizer.Add(PYfilterNpickSizer, 0, wx.LEFT|wx.ALIGN_CENTER,5)

      locNfilenameSizer = wx.FlexGridSizer(cols=2, hgap=5)
      locNfilenameSizer.Add(pickDirBtn)
      locNfilenameSizer.Add(self.dirText,0,wx.RIGHT,5)
      locNfilenameSizer.Add(wx.StaticText(panel, -1, 'name :'),
           0, wx.ALIGN_RIGHT|wx.TOP, 5)
      locNfilenameSizer.Add(filenameNpickerSizer)

      self.PStatsCheck = wx.CheckBox(panel, -1, LABEL_enablePStats)

      self.startBtn = wx.Button(panel, -1, 'Create')
      self.startBtn.SetFont(optionFont)
      self.startBtn.Bind(wx.EVT_BUTTON,self.startFresh)
      self.startBtn.Disable()

      startFreshSizer.Add(startFreshText, 0, wx.ALL|wx.ALIGN_CENTER, 5)
      startFreshSizer.Add(locNfilenameSizer, 0, wx.ALIGN_CENTER, 5)
      startFreshSizer.Add(CWDtext,0,wx.LEFT,5)
      startFreshSizer.Add(self.CWDchoice,0,wx.ALL|wx.ALIGN_CENTER|wx.EXPAND,5)
      startFreshSizer.Add(ARGtext, 0, wx.LEFT, 5)
      startFreshSizer.Add(self.APPargs, 0, wx.ALL|wx.EXPAND, 5)
      startFreshSizer.Add((5,5))

      #_______________________________________________________________________________
      self.configNimportsNotebook = wx.Notebook(panel,  size=(390,380))
      self.configNimportsNotebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED,self.processNotebookPageChange)
      panel1 = wx.Panel(self.configNimportsNotebook)
      panel2 = wx.Panel(self.configNimportsNotebook)
      self.previewPanel = wx.Panel(self.configNimportsNotebook)

      #_______________________________________________________________________________
      importsNotebook = wx.Notebook(panel2, size=(360,250))
      generalSizer = wx.BoxSizer(wx.VERTICAL)
      importSizer = wx.StaticBoxSizer(wx.StaticBox(panel2,-1,' Imports '),wx.VERTICAL)

      self.P3DimportsList = wx.CheckListBox(importsNotebook, choices=P3D_imports)
      for i in range(len(P3D_imports)):
          self.P3DimportsList.Check(i,1)

      self.Python_importsList = wx.CheckListBox(importsNotebook, choices=Python_imports)
      for i in range(len(Python_imports)):
          self.Python_importsList.Check(i,1)

      importsNotebook.AddPage(self.P3DimportsList, 'Panda3D')
      importsNotebook.AddPage(self.Python_importsList, 'Python')

      self.fileType = wx.RadioBox(panel2,-1,'File type',
               choices=['with console (.py)','without console (.pyw)'])

      importSizer.Add(importsNotebook, 0, wx.ALIGN_CENTER, 5)

      generalSizer.Add(importSizer, 0, wx.ALL|wx.ALIGN_CENTER, 5)
      generalSizer.Add(self.fileType, 0, wx.ALIGN_CENTER, 5)
      panel2.SetSizer(generalSizer)

      #_______________________________________________________________________________
      self.CfgVarTypes=['undefined','list','string','filename','boolean','integer','double','enumerate','search path','64-bit integer']

      self.CfgVarsName=[ cvMgr.getVariableName(i) for i in range(cvMgr.getNumVariables()) ]
      self.CfgVarsName.sort()

      self.CfgVars=[ ConfigVar(n) for n in self.CfgVarsName ]
      self.filteredCfgVars=self.CfgVars
      self.CfgVarsDict={}
      for i in range(len(self.CfgVarsName)):
          self.CfgVarsDict[self.CfgVarsName[i]]=self.CfgVars[i]

      configTuningSizer = wx.BoxSizer(wx.VERTICAL)
      searchSizer = wx.BoxSizer(wx.HORIZONTAL)

      searchPic = wx.StaticBitmap(panel1)
      searchPic.SetBitmap(wx.Bitmap('images/IDE_search.png'))

      self.cfgVarSearch = wx.TextCtrl(panel1,size=(170,-1))
      self.cfgVarSearch.Bind(wx.EVT_TEXT,self.filterCfgVars)

      self.searchDesc = wx.CheckBox(panel1,-1,'search description too')
      self.searchDesc.SetValue(1)
      self.searchDesc.Bind(wx.EVT_CHECKBOX,self.toggleSearchDesc)

      searchSizer.Add(searchPic,0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
      searchSizer.Add(self.cfgVarSearch, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL,10)
      searchSizer.Add(self.searchDesc, 0, wx.ALIGN_CENTER_VERTICAL, 10)

      self.cfgVarsList = wx.CheckListBox(panel1, size=(350,110), choices=self.CfgVarsName)
      self.cfgVarsList.SetToolTipString('check the variables you need to change,\nselect to view the description')
      self.cfgVarsList.Bind(wx.EVT_CHECKLISTBOX,self.cfgVarChecked)
      self.cfgVarsList.Bind(wx.EVT_LISTBOX,self.cfgVarSelected)

      self.cfgVarDesc = wx.TextCtrl(panel1,value=NA,size=(0,85),style=wx.MULTIPLE)
      self.cfgVarDesc.SetEditable(0)

      prevCfgVarBtn = wx.Button(panel1, -1, 'Previous')
      prevCfgVarBtn.Bind(wx.EVT_BUTTON,self.prevTunedCfgVar)

      nextCfgVarBtn = wx.Button(panel1, -1, 'Next')
      nextCfgVarBtn.Bind(wx.EVT_BUTTON,self.nextTunedCfgVar)

      prefPic = wx.Bitmap('images/IDE_checked.png')
      checkedVarsBtn = wx.BitmapButton(panel1, -1, prefPic,size=(30,-1))
      checkedVarsBtn.SetToolTipString('toggle view all / checked variables')
      checkedVarsBtn.Bind(wx.EVT_BUTTON,self.toggleCheckedOrAllVars)

      tunedVarNavgtSizer = wx.BoxSizer(wx.HORIZONTAL)
      tunedVarNavgtSizer.Add(prevCfgVarBtn, 0, wx.ALIGN_CENTER_VERTICAL)
      tunedVarNavgtSizer.Add(checkedVarsBtn, 0, wx.ALIGN_CENTER_VERTICAL)
      tunedVarNavgtSizer.Add(nextCfgVarBtn, 0, wx.ALIGN_CENTER_VERTICAL)

      self.cfgValueTypeText = wx.StaticText(panel1, -1, NA)

      self.cfgOldValue = wx.TextCtrl(panel1,size=(240,-1))
      self.cfgOldValue.Disable()

      cfgOldValueSizer = wx.BoxSizer(wx.HORIZONTAL)
      cfgOldValueSizer.Add(wx.StaticText(panel1, -1, 'old'), 0, wx.ALIGN_CENTER_VERTICAL, 5)
      cfgOldValueSizer.Add(self.cfgOldValue, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)

      self.cfgNewValue = wx.TextCtrl(panel1,size=(240,-1))
      self.cfgNewValue.Bind(wx.EVT_TEXT,self.cfgNewValueChanged)
      self.cfgNewValue.Disable()

      cfgNewValueSizer = wx.BoxSizer(wx.HORIZONTAL)
      cfgNewValueSizer.Add(wx.StaticText(panel1, -1, 'new'), 0, wx.ALIGN_CENTER_VERTICAL, 5)
      cfgNewValueSizer.Add(self.cfgNewValue, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.BOTTOM, 5)

      self.cfgVarResetBtn = wx.Button(panel1, -1, 'Reset\nvalue', style=wx.BU_EXACTFIT)
      self.cfgVarResetBtn.Bind(wx.EVT_BUTTON,self.configVarReset)
      self.cfgVarResetBtn.Disable()

      cfgAllValuesSizer = wx.BoxSizer(wx.VERTICAL)
      cfgAllValuesSizer.Add(cfgOldValueSizer,0, wx.ALIGN_RIGHT|wx.LEFT, 5)
      cfgAllValuesSizer.Add(cfgNewValueSizer,0, wx.ALIGN_RIGHT|wx.LEFT, 5)

      cfgValueAdjustmentSizer = wx.FlexGridSizer(cols=3)
      cfgValueAdjustmentSizer.Add(wx.StaticText(panel1, -1, 'Type :'), 0, wx.LEFT|wx.ALIGN_LEFT, 5)
      cfgValueAdjustmentSizer.Add(self.cfgValueTypeText, 0, wx.LEFT|wx.ALIGN_LEFT, 5)
      cfgValueAdjustmentSizer.Add((5,5))
      cfgValueAdjustmentSizer.Add(wx.StaticText(panel1, -1, 'Value :'), 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
      cfgValueAdjustmentSizer.Add(cfgAllValuesSizer,0, wx.TOP|wx.ALIGN_CENTER, 5)
      cfgValueAdjustmentSizer.Add(self.cfgVarResetBtn,0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)

      configTuningSizer.Add(searchSizer, 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
      configTuningSizer.Add(self.cfgVarsList, 0, wx.EXPAND|wx.ALIGN_TOP|wx.ALL, 5)
#       configTuningSizer.Add(wx.StaticText(panel1, -1, 'Description :'), 0, wx.LEFT|wx.ALIGN_LEFT, 5)
      configTuningSizer.Add(self.cfgVarDesc, 0, wx.LEFT|wx.RIGHT|wx.EXPAND|wx.ALIGN_CENTER, 5)
      configTuningSizer.Add(tunedVarNavgtSizer, 0, wx.TOP|wx.ALIGN_CENTER, 5)
#       configTuningSizer.Add(wx.StaticLine(panel1), 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 5)
      configTuningSizer.Add(cfgValueAdjustmentSizer, 0, wx.ALL|wx.ALIGN_CENTER, 5)
      panel1.SetSizer(configTuningSizer)

      #_______________________________________________________________________________
      previewSizer = wx.BoxSizer(wx.VERTICAL)
      self.previewText = EditWindow(self.previewPanel,-1,size=(365,300))
      self.previewText.SetToolTipString('this preview is read-only')

      cfgOptionsSizer = wx.BoxSizer(wx.HORIZONTAL)

      self.embedDesc = wx.CheckBox(self.previewPanel,-1,'embed config description')
      self.embedDesc.SetValue(1)
      self.embedDesc.Bind(wx.EVT_CHECKBOX,self.updatePreview)

      self.separateVars = wx.CheckBox(self.previewPanel,-1,'insert blank line separator')
      self.separateVars.SetValue(1)
      self.separateVars.Bind(wx.EVT_CHECKBOX,self.updatePreview)

      cfgOptionsSizer.Add(self.embedDesc)
      cfgOptionsSizer.Add((15,-1))
      cfgOptionsSizer.Add(self.separateVars)

      previewSizer.Add(cfgOptionsSizer, 0, wx.ALL|wx.ALIGN_CENTER, 5)
      previewSizer.Add(wx.StaticLine(self.previewPanel), 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)
      previewSizer.Add(self.previewText, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER, 5)
      self.previewPanel.SetSizer(previewSizer)

      #_______________________________________________________________________________
      self.configNimportsNotebook.AddPage(panel2,'General')
      self.configNimportsNotebook.AddPage(panel1,'Config Variables tuning')
      self.configNimportsNotebook.AddPage(self.previewPanel,'preview')

      closeBtn = wx.Button(panel, -1, LABEL_close, style=wx.BU_EXACTFIT)
      closeBtn.Bind(wx.EVT_BUTTON,Functor(destroy,self))

      startFreshSizer.Add(self.configNimportsNotebook,0,wx.ALIGN_CENTER, 5)
      startFreshSizer.Add(self.PStatsCheck, 0, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER, 5)
      startFreshSizer.Add(self.startBtn, 0, wx.ALIGN_CENTER, 5)
      startFreshSizer.Add(closeBtn, 0, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER, 5)

      welcomeScreen.Hide()
      panel.SetSizer(startFreshSizer)
      startFreshSizer.Fit(self)
      startFreshSizer.SetSizeHints(self)
      self.Center()
      self.Show()
      self.Raise()

  def pickDir(self,e):
      defaultPath=self.dirText.GetValue()
      if not os.path.exists(defaultPath):
         defaultPath=''
         self.dirText.SetValue('')
      Ddlg = wx.DirDialog(self, defaultPath=defaultPath, style=wx.OPEN)
      if Ddlg.ShowModal() == wx.ID_OK:
         path = Ddlg.GetPath()
         self.dirText.SetValue(path)
         self.CWDchoice.SetItems(getParentDirs(joinPaths(path,'x')))
         self.CWDchoice.Select(0)
         self.CWDchoice.Enable()
         self.APPargs.Enable()
         self.startBtn.Enable()
      else:
         print('Nothing was selected.')

  def pickFile(self,e):
      defaultDir=self.dirText.GetValue()
      wildcard='*.py;*.pyw;*.pyc;*.pyo;*.pyd;*.pyx' if self.onlyPYcheckBtn.GetValue() else '*.*'
      Fdlg = wx.FileDialog(self, 'Pick a file',
          defaultDir=defaultDir, wildcard=wildcard,
          style=wx.OPEN)
      if Fdlg.ShowModal() == wx.ID_OK:
         name = os.path.basename(Fdlg.GetPath())
         self.filenameText.SetValue(name)
      else:
         print('Nothing was selected.')

  def cfgVarSelected(self,e):
      idx=self.cfgVarsList.GetSelection()
      if idx<0:
         return # nothing selected
      varName=self.cfgVarsList.GetStringSelection()
      v=self.CfgVarsDict[varName]
      self.cfgValueTypeText.SetLabel(self.CfgVarTypes[v.var.getValueType()])
      self.cfgOldValue.SetValue(v.oldVal)
      self.cfgNewValue.SetValue(v.newVal)
      desc=v.var.getDescription()
      if len(desc)<8: # just to avoid displaying "DConfig"
         desc=NA
      self.cfgVarDesc.SetValue(desc)
      self.cfgNewValue.Enable(v.checked)

  def cfgVarChecked(self,e):
      idx=self.cfgVarsList.GetSelection()
      for i in range(len(self.filteredCfgVars)):
          if self.cfgVarsList.IsChecked(i)!=self.filteredCfgVars[i].checked:
             self.filteredCfgVars[i].checked=self.cfgVarsList.IsChecked(i)
             break
      if idx>-1:
         varName=self.cfgVarsList.GetStringSelection()
         v=self.CfgVarsDict[varName]
         v.checked=self.cfgVarsList.IsChecked(idx)
         self.cfgNewValue.Enable(v.checked)

  def cfgNewValueChanged(self,e):
      idx=self.cfgVarsList.GetSelection()
      if idx<0:
         self.cfgVarResetBtn.Disable()
         return
      varName=self.cfgVarsList.GetStringSelection()
      v=self.CfgVarsDict[varName]
      val=self.cfgNewValue.GetValue()
      v.newVal=val
      if val==v.oldVal:
         self.cfgVarResetBtn.Disable()
      elif self.cfgVarsList.IsChecked(idx):
         self.cfgVarResetBtn.Enable()

  def configVarReset(self,e):
      varName=self.cfgVarsList.GetStringSelection()
      v=self.CfgVarsDict[varName]
      v.newVal=v.oldVal
      self.cfgNewValue.SetValue(v.newVal)

  def prevTunedCfgVar(self,e):
      if not [1 for v in self.filteredCfgVars if v.checked]:
         return # nothing checked
      idx=self.cfgVarsList.GetSelection()
      if idx<0:
         idx=self.cfgVarsList.Count
         checked=0
      else:
         checked=self.cfgVarsList.IsChecked(idx)
      for i in range(idx-1,-1,-1):
          if self.cfgVarsList.IsChecked(i):
             self.cfgVarsList.SetSelection(i)
             self.cfgVarSelected(0)
             return
      if not checked:
         idx=self.cfgVarsList.Count
         for i in range(idx-1,-1,-1):
             if self.cfgVarsList.IsChecked(i):
                self.cfgVarsList.SetSelection(i)
                self.cfgVarSelected(0)
                return
      self.cfgVarsList.DeselectAll()
      self.cfgVarsList.SetSelection(idx)

  def nextTunedCfgVar(self,e):
      if not [1 for v in self.filteredCfgVars if v.checked]:
         return # nothing checked
      idx=max(0,self.cfgVarsList.GetSelection())
      checked=self.cfgVarsList.IsChecked(idx)
      for i in range(idx+1,self.cfgVarsList.Count):
          if self.cfgVarsList.IsChecked(i):
             self.cfgVarsList.SetSelection(i)
             self.cfgVarSelected(0)
             return
      if not checked:
         idx=0
         for i in range(idx+1,self.cfgVarsList.Count):
             if self.cfgVarsList.IsChecked(i):
                self.cfgVarsList.SetSelection(i)
                self.cfgVarSelected(0)
                return
      self.cfgVarsList.DeselectAll()
      self.cfgVarsList.SetSelection(idx)

  def filterCfgVars(self,e):
      text=self.cfgVarSearch.GetValue().lower().replace(',',' ').replace('.',' ').\
           replace(';',' ').replace(':',' ').split()
      if text:
         if self.searchDesc.GetValue(): # search in description too
            self.filteredCfgVars=[]
            for v in self.CfgVars:
                for word in text:
                    if v.name.lower().find(word)>-1 or v.desc.find(word)>-1:
                       self.filteredCfgVars.append(v)
                       break
         else:
            self.filteredCfgVars=[]
            for v in self.CfgVars:
                for word in text:
                    if v.name.lower().find(word)>-1:
                       self.filteredCfgVars.append(v)
                       break
      else:
         self.filteredCfgVars=self.CfgVars

      self.cfgVarsList.SetItems([v.name for v in self.filteredCfgVars])
      for v in self.filteredCfgVars:
          if v.checked:
             self.cfgVarsList.Check(self.filteredCfgVars.index(v),True)
      self.cfgVarDesc.SetValue(NA)
      self.cfgValueTypeText.SetLabel(NA)
      self.cfgOldValue.Clear()
      self.cfgNewValue.Clear()
      self.cfgNewValue.Disable()

  def toggleCheckedOrAllVars(self,e):
      if len(self.filteredCfgVars)==len(self.CfgVars):
         self.filteredCfgVars=[v for v in self.CfgVars if v.checked]
         self.cfgVarsList.SetItems([v.name for v in self.filteredCfgVars])
         for i in range(len(self.filteredCfgVars)):
             self.cfgVarsList.Check(i)
      else:
         self.filteredCfgVars=self.CfgVars
         self.cfgVarsList.SetItems(self.CfgVarsName)
         for v in self.filteredCfgVars:
             if v.checked:
                self.cfgVarsList.Check(self.filteredCfgVars.index(v),True)
      self.cfgVarDesc.SetValue(NA)
      self.cfgValueTypeText.SetLabel(NA)
      self.cfgOldValue.Clear()
      self.cfgNewValue.Clear()
      self.cfgNewValue.Disable()

  def toggleSearchDesc(self,e):
      if self.cfgVarSearch.GetValue():
         self.filterCfgVars(0)

  def updatePreview(self,e=None):
      # only update if the current page is the preview panel
      if self.configNimportsNotebook.GetCurrentPage()==self.previewPanel:
         self.previewText.SetReadOnly(0)
         self.previewText.SetText(self.getFinalScript(0))
         self.previewText.SetReadOnly(1)
         self.previewText.Refresh() # I want highlighting now !
         self.previewText.SetFocus()
         print('PREVIEW UPDATED')

  def processNotebookPageChange(self,e):
      e.Skip()
      if self.configNimportsNotebook.GetSelection()<0: return
      # somehow, on Windows, app.Dispatch() and app.ProcessIdle()
      # aren't enough to force update the notebook,
      # so just use a timer to let wx update it in its mainloop
      Timer(.02, self.updatePreview).start()

  def startFresh(self,ce):
      if not os.path.exists(self.dirText.GetValue()):
         wx.MessageDialog(self,
              message='Invalid location to save the file.', caption='ERROR',
              style=wx.ICON_ERROR).ShowModal()
         return
      filename=self.filenameText.GetValue()
      if not len(filename.strip()):
         wx.MessageDialog(self,
              message='You have not set the filename yet.', caption='ERROR',
              style=wx.ICON_ERROR).ShowModal()
         self.filenameText.SetFocus()
         return
      else:
         illegalChars=(r'"\*?/:<>|')
         for c in illegalChars:
             if filename.find(c)>-1:
                wx.MessageDialog(self,
                     message='Filename should not contain any of these characters :\n%s'%''.join([ic+' ' for ic in illegalChars]), caption='ERROR',
                     style=wx.ICON_ERROR).ShowModal()
                self.filenameText.SetFocus()
                return

      # check if there are some config vars that still use default value
      isFiltered=len(self.filteredCfgVars)!=len(self.CfgVars)
      for v in self.CfgVars:
          if v.checked:
             if v.oldVal==v.newVal:
                if isFiltered:
                   self.cfgVarSearch.SetValue('')
                   isFiltered=0
                self.configNimportsNotebook.SetSelection(1)
                self.cfgVarsList.SetSelection(self.CfgVars.index(v))
                self.cfgVarSelected(0)
                self.cfgNewValue.SetFocus()
                wx.MessageDialog(self,
                     message='Variable "%s" is still using the default value.\nPlease make up your mind.'%v.name,
                     caption='Please pay attention',
                     style=wx.ICON_INFORMATION).ShowModal()
                return
             # TODO : validates the new value




      filename=self.filenameText.GetValue()
      basenameExt=os.path.splitext(filename)
      ext=basenameExt[-1][1:].lower()
      if ext in ('py','pyw','pyc','pyo','pyd','pyx'):
         finalnameWOext=basenameExt[0]
      else:
         finalnameWOext=filename

      path=joinPaths(self.dirText.GetValue(),'%s.%s'%(finalnameWOext,('py','pyw')[self.fileType.GetSelection()]))
      # check if it is already exist
      if os.path.exists(path):
         Mdlg = wx.MessageDialog(self,'This file already exists.\nOverwrite it ?',
              caption='Please confirm',style=wx.YES_NO|wx.NO_DEFAULT|wx.ICON_QUESTION|wx.CENTER)
         if Mdlg.ShowModal()==wx.ID_NO:
            self.filenameText.SetFocus()
            return

      f=open(path,'w')
      f.write(self.getFinalScript(0))
      f.close()

      startIDE([path],self.mainNcurrFile,self.PStatsCheck.Value,
               self.CWDchoice.GetStringSelection(),self.APPargs.Value)

  def getFinalScript(self,ce):
      lineSep=self.separateVars.GetValue()
      if self.embedDesc.GetValue():
         tunedCfgVars=[]
         for v in self.CfgVars:
             if v.checked:
                desc='\n    # '+TW.fill(v.var.getDescription()).replace('\n','\n    # ') if v.desc else ''
                tunedCfgVars.append('  %s %s%s%s'%(v.name,v.newVal,desc,'\n'*lineSep))
      else:
         tunedCfgVars=['  %s %s%s'%(v.name,v.newVal,'\n'*lineSep) for v in self.CfgVars if v.checked]
      CfgVarsTuning="from pandac.PandaModules import loadPrcFileData\n# config variables tuning\nloadPrcFileData('','''\n%s\n''')" %'\n'.join(tunedCfgVars)
      PPythonFramework='import direct.directbase.DirectStart'
      if tunedCfgVars:
         PPythonFramework=CfgVarsTuning+'\n'+PPythonFramework
      P3DimpLines='\n'.join(getCheckListBoxSelectedStrings(self.P3DimportsList))
      PythonImpLines='\n'.join(getCheckListBoxSelectedStrings(self.Python_importsList))
      if PythonImpLines:
         PythonImpLines='\n# Python imports ______________________________________\n'+PythonImpLines
      contents='''

class World:
  def __init__(self):
      pass # :D GOOD LUCK !


if __name__=='__main__':
   winst = World()
   run()
'''
      fullContents=[ '# Panda3D imports _____________________________________',
                     PPythonFramework,
                     P3DimpLines,
                     PythonImpLines,
                     contents ]
      return '\n'.join(fullContents)


################################################################################
app = wx.App(redirect=0)

COLOR_welcomeScreen=(160,160,255)
COLOR_optionsScreen=(190,200,255)
optionFont = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
smallFont = wx.Font(7, wx.SWISS, wx.NORMAL, wx.NORMAL)
startButtonsFont = wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD)

welcomeScreen = wx.Frame(None, -1, title='Welcome to my P3D IDE', style=wx.RESIZE_BORDER|wx.FRAME_NO_TASKBAR)
welcomeScreen.SetBackgroundColour(COLOR_welcomeScreen)
welcomeScreen.Bind(wx.EVT_CLOSE,lambda e:exit())
welcomeScreenPanel = wx.Panel(welcomeScreen)

topSizer = wx.BoxSizer(wx.VERTICAL)
WELCOME_buttonsSizer = wx.StaticBoxSizer(wx.StaticBox(welcomeScreenPanel),wx.VERTICAL)

PandaPic = wx.StaticBitmap(welcomeScreenPanel)
logos=glob(joinPaths('images/logo/*.png'))
if logos:
   PandaPic.SetBitmap(wx.Bitmap(random.choice(logos)))

P3DversionText = wx.StaticText(welcomeScreenPanel,-1,'v'+PandaSystem.getVersionString())
P3DversionText.SetFont(smallFont)
welcomeText = wx.StaticText(welcomeScreenPanel, -1, 'Welcome  to  my  PANDA3D  IDE')
welcomeText.SetFont(optionFont)

lastFilesListExists=False
lastMainFileExists=False
lastFiles='%s.%s'%(LAST_FILES,PLATFORM)
if not os.path.exists(lastFiles):
   lastFiles=LAST_FILES

lastFs=mainNcurrFile=[]
lastFilesListExists=os.path.exists(lastFiles)
if lastFilesListExists:
   f=open(lastFiles,'rU')
   lastFs=pickle.load(f)
   f.close()
   listdata=[i for i in lastFs if type(i)==list]
   mainNcurrFile=listdata[0] if len(listdata) else []
   if mainNcurrFile:
      lastFs.remove(mainNcurrFile)
   lastMainFileExists=len(lastFs) and len(mainNcurrFile) and os.path.exists(mainNcurrFile[0])

WELCOME_openLastEditedFilesBtn = wx.Button(welcomeScreenPanel, -1, 'Open Last Edited Files', size=(0,55))
WELCOME_openLastEditedFilesBtn.SetFont(startButtonsFont)
WELCOME_openFilesBtn = wx.Button(welcomeScreenPanel, -1, 'Open Files',size=(0,55))
WELCOME_openFilesBtn.SetFont(startButtonsFont)
WELCOME_openFilesBtn.Bind(wx.EVT_BUTTON,OpenFiles)
WELCOME_createNewFileBtn = wx.Button(welcomeScreenPanel, -1, 'Create New File',size=(0,55))
WELCOME_createNewFileBtn.SetFont(startButtonsFont)
WELCOME_createNewFileBtn.Bind(wx.EVT_BUTTON,CreateNewFile)

if len(lastFs):
   WELCOME_openLastEditedFilesBtn.Bind(wx.EVT_BUTTON,OpenLastEditedFiles)
   WELCOME_openLastEditedFilesBtn.SetFocus()
else:
   WELCOME_openLastEditedFilesBtn.Disable()
   WELCOME_openFilesBtn.SetFocus()

WELCOME_buttonsSizer.Add((220,0))
WELCOME_buttonsSizer.Add(WELCOME_openLastEditedFilesBtn,0,wx.EXPAND)
WELCOME_buttonsSizer.Add(WELCOME_openFilesBtn,0,wx.EXPAND)
WELCOME_buttonsSizer.Add(WELCOME_createNewFileBtn,0,wx.EXPAND)

closeBtn = wx.Button(welcomeScreenPanel, -1, LABEL_later)
closeBtn.Bind(wx.EVT_BUTTON,lambda e:exit())
closeBtn.Bind(wx.EVT_LEFT_DOWN,closing)
closeBtn.Bind(wx.EVT_LEFT_UP,closeNow)
#_______________________________________________________________________________
topSizer.Add(PandaPic,0, wx.ALL|wx.ALIGN_CENTER, 5)
topSizer.Add(P3DversionText,0, wx.TOP|wx.RIGHT|wx.ALIGN_RIGHT, 5)
topSizer.Add((5,10))
topSizer.Add(wx.StaticText(welcomeScreenPanel,-1,'Hello, %s !'%wx.GetUserName()), 0, wx.ALIGN_CENTER, 5)
topSizer.Add(welcomeText, 0, wx.ALL|wx.ALIGN_CENTER, 5)
topSizer.Add((5,20))
topSizer.Add(wx.StaticText(welcomeScreenPanel, -1, 'What do you want to do ?'),
         0, wx.ALL|wx.ALIGN_CENTER, 5)
topSizer.Add(WELCOME_buttonsSizer, 0, wx.ALIGN_CENTER, 5)
topSizer.Add(closeBtn, 0, wx.ALL|wx.ALIGN_CENTER, 5)
versionText=wx.StaticText(welcomeScreenPanel, -1, VERSION)
# the latest modification time of IDE modules
IDEtime = max( [time.gmtime(os.path.getmtime(f)) for f in ('IDE.py', 'IDEmini.py', 'IDE_STARTER.py')] )
dateText = wx.StaticText(welcomeScreenPanel, -1, time.strftime('%b %d, %Y',IDEtime))

welcomeScreenPanel.SetSizer(topSizer)
topSizer.Fit(welcomeScreen)
topSizer.SetSizeHints(welcomeScreen)
welcomeScreen.SetMaxSize(welcomeScreen.GetSize())
welcomeScreen.Center()
welcomeScreen.Show()

# I don't want to spend additional space under the Close button just for this.
# The placement must be done after Show() on Linux, or panel size would be wrong.
panelSize = welcomeScreenPanel.Size
versionText.MoveXY(panelSize.x-versionText.Size.x-2,panelSize.y-versionText.Size.y*2-2)
dateText.MoveXY(panelSize.x-dateText.Size.x-2,panelSize.y-dateText.Size.y-2)

if not lastMainFileExists and mainNcurrFile:
   wx.MessageDialog(None,
      message='WARNING :\n\nLast edited main file does not exist :\n'+mainNcurrFile[0],
      caption='!!! WARNING !!!', style=wx.ICON_INFORMATION).ShowModal()

app.MainLoop()
