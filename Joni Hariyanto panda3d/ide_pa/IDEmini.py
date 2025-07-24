import os, sys, wx
import IDEFileSrv, asyncore, socket, subprocess

PLATFORM = sys.platform[:3]
LIN = PLATFORM=='lin'
WIN = PLATFORM=='win'
MAC = PLATFORM=='dar'
IDE_reallyExit = sys.exit
IDE_forcedExit = os._exit

def IDE_shutdown():
    # Python26's SystemExit in interactive session on Windows ends up at prompt,
    # so force exit instead
    if WIN and int(sys.version.split()[0].replace('.','')[:2])>25:
       IDE_forcedExit(0)
#        subprocess.Popen('taskkill /f /PID %s'%os.getpid())
    else:
       IDE_reallyExit()

def renderFrame(num=1):
    for i in range(num):
        base.graphicsEngine.renderFrame()

def APP_exit(args=None):
    ''' YNJH: replacement of sys.exit, so if sys.exit is called from user's app,
        it wouldn't shutdown Python
    '''
    m=IDE if IDE_activated else M
    print('APPLICATION EXIT', file=IDE_DEV)
    # brings user back to IDE instead of doing nothing
    if m.IDE_CFG[CFG_activatedBySysExit]:
       IDE_goBackToIDE()
sys.exit = os._exit = APP_exit
IDE_step = renderFrame

## wxPython setup ##############################################################
wxApp = wx.App(redirect=False)
wxappname='P3DIDE'
SIC = wx.SingleInstanceChecker('%s-%s'%(wxappname,wx.GetUserId()))
if SIC.IsAnotherRunning():
   s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   s.connect(('127.0.0.1', IDEFileSrv.PORT))
   s.send(sys.argv[1])
   s.close()
   IDE_shutdown()

FILE_SRV = IDEFileSrv.FileServer()

wx.Frame(None,-1,wxappname) # dummy frame to hold wx app name
wxApp.SetAssertMode(wx.PYAPP_ASSERT_SUPPRESS)
newWxEVTloop=wx.EventLoop()
wx.EventLoop.SetActive(newWxEVTloop)


sys.executable = sys.argv[4].strip().strip('"')
PythonVars = dir(__builtins__)
PythonVars.sort()
# print PythonVars
from copy import deepcopy
import builtins, time
_BV_=list(builtins.__dict__.values())

GLOBALS = globals()
M = sys.modules[__name__]
# caret types
CAR_DESC = {
  'vertical':  'vertical',
  'cage':      'cage',
  'underline': 'underline',
  'block':     'block',
}
for k in CAR_DESC:
    GLOBALS['CAR_'+k] = k

# upgrade check interval
UPD_never = 0
UPD_daily = 1
UPD_weekly = 2
UPD_monthly = 3

# actions categories
AC_gen = 0
AC_doc = 1
AC_edit = 2
AC_comp = 3
AC_mark = 4
AC_macro = 5
AC_search = 6
AC_scene = 7

# [indentspace,displayorder]
orderedSmartIndentDict={
  'class':[2,0],
  'def':[None,1],
  'if':[None,2],
  'else':[3,3],
  'elif':[3,4],
  'try':[4,5],
  'except':[4,6],
  'finally':[4,7],
  'for':[None,8],
  'while':[3,9],
  'with':[3,10],
}
SMART_INDENT_order=dict([reversed((k,v[1])) for k,v in list(orderedSmartIndentDict.items())])
SMART_INDENT={}
for c,v in list(orderedSmartIndentDict.items()):
    SMART_INDENT[c]=v[0]

colors={
  'WSback':                 [ (0,0,0), 'Workspace BG'],
  'markersBar':             [ (200,200,200), 'Markers bar'],
  'sliderBG':               [ (0,0,0), 'Slider bar BG'],
  'tabsNstatusBar':         [ (255,255,255), 'Tabs & status bars'],
  'statusText':             [ (0,0,0), 'Status text'],
  'block':                  [ (130,90,0), 'Selection BG'],
  'log':                    [ (200,200,200), 'Log'],
  'logOverScene':           [ (255,255,255), 'Log over scene'],
  'caret':                  [ (255,255,0), 'Caret'],
  'codesListBG':            [ (0,0,0), 'Codes list BG'],
  'codesListFG':            [ (255, 204, 51), 'Codes list text'],
  'codeDesc':               [ (255,228,181), 'Code description'],
  'tabLabelMainModActive':  [ (0,100,50), 'Main module tab (active)'],
  'tabLabelMainModInactive':[ (0,230,100), 'Main module tab (inactive)'],
  'tabLabelOtherModActive': [ (0,0,0), 'Other modules tab (active)'],
  'tabTextActive':          [ (255,255,255), 'Tab text (active)'],
  'tabTextInactive':        [ (0,0,0), 'Tab text (inactive)'],
  'callTipsBG':             [ (155,215,250), 'Call tips BG'],
  'callTipsText':           [ (0,0,0), 'Call tips text'],
  'callArgsBG':             [ (255,0,0), 'Call args hilight'],
  }
DEF_GEN_COLORS={}
GEN_COLORS={}
GEN_COLORS_DESC={}
for k,v in list(colors.items()):
    GLOBALS['GC_'+k]=k
    GEN_COLORS[k],GEN_COLORS_DESC[k]=v
    DEF_GEN_COLORS[k]=v[0]

cfg={
  'autoCreateLog':         [False,'Display log at start',"Always display log when the IDE starts.\nThe log is always updated even if it's not displayed"],
  'autoComplete':          [True,'Enable &Auto-Complete at start','Always enable Auto-Complete when the IDE starts'],
  'autoReloadFiles':       [False,'Auto-reload &modified files','Auto-reload externally modified files'],
  'autoUpdateMainMod':     [True,'Auto-update scene','Auto-update scene\nif main module is externally modified'],
  'regularUpdateInterval': [UPD_weekly,' Regular upgrade interval : ','Check for upgrade regularly'],
  'lastUpdateCheckTime':   [time.time(),'',''],
  'host':                  [0,' Host : ','Download upgrades from here'],
  'resetCamTransform':     [False,'Reset &camera transform on scene update',"Clear main camera's transform each time the scene is updated.\nSometimes you want to keep it still."],
  'activatedBySysExit':    [True,'Activated by System&Exit','Jump back to IDE on SystemExit from the scene'],
  'excludeOldMods':        [True,'Exclude deprecated modules','Exclude deprecated modules from import completion'],
  'brMatchMaxLines':       [80000,'&Bracket matching max. lines :','Matching brackets highlight is disabled if the document size is beyond this lines limit'],
  'minLargeLogSize':       [1000000,'Min. size of LARGE &log :','You will be asked if you want the entire log beyond this limit'],
  'recentFilesLimit':      [150,'Available &recent files :','Max. length of recent files list'],
  'CCmaxSrc':              [5000,'Source &description max. size :',"Max. size of completion object's source code\nto display, if no documentation is available"],
  'CTwrapWidth':           [70,'Call tips &wrap width:','Call tips will be wrapped\nif beyond this amount of characters'],
  'realLineStart':         [False,'jump to real Line &Start','First jump goes to the first :\ncolumn | non-whitespace char'],
  'realLineEnd':           [False,'jump to real Line &End','First jump goes to the last :\ncolumn | non-whitespace char'],
  'animSelColor':          [True,'Animate &selection color intensity',''],
  'visLinesOfCaret':       [7,'Visible &Lines :','Visible lines around caret on scrolling'],
  'visColumnsOfCaret':     [15,'Visible &Columns :','Visible columns around caret on scrolling'],
  'fileTabSkin':           ['1','&Files tab skin :',''],
  'sliderSkin':            ['1','&Slider skin :',''],
  'insCaret':              [CAR_vertical,'&Insert-mode caret :','The shape of caret in INSERT mode'],
  'ovrCaret':              [CAR_cage,'&Overwrite-mode caret :','The shape of caret in OVERWRITE mode'],
  'WSfontPPU':             [11,'Workspace font size :','Workspace font size (pixels)'],
  'WSfontSpacing':         [6,'Workspace font spacing :','Workspace font spacing'],
  'WSopacity':             [75,'&Workspace BG opacity :','Opacity of workspace background'],
  'CCopacity':             [90,'&Codes list BG opacity :','Opacity of completion list (and its description) background'],
  'linesPerScroll':        [1,'Lines per sc&roll :','Amount of shifted lines on scrolling'],
  'fixedIndentSpaces':     [1,'Fixed-space indent :',''],
  'smartIndent':           [SMART_INDENT, 'Smart auto indent :',"Auto-indent space if the first word of previous line is : %s\n(0 means it's aligned to the 2nd word)"],
  'colors':                [GEN_COLORS, '',''],
  'SGBPos':                [None, '',''],
  'NPropsPos':             [None, '',''],
}
IDE_CFG={}
IDE_CFG_DESC={}
IDE_CFG_TIP={}
for k,v in list(cfg.items()):
    GLOBALS['CFG_'+k]=k
    IDE_CFG[k],IDE_CFG_DESC[k],IDE_CFG_TIP[k]=v

# [color, order, desc]
textColors={
  'python':{
    'builtin':    [ (150,150,255),0,'Builtin' ],
    'keyword':    [ (255,128,0),1,'Keyword' ],
    'identifier': [ (255,255,255),2,'Identifier' ],
    'string':     [ (255,0,0),3,'String' ],
    'int':        [ (255,255,0),4,'Integer' ],
    'float':      [ (0,255,50),5,'Float' ],
    'invalid':    [ (255,0,255),6,'Invalid' ],
    'punct':      [ (255,128,0),7,'Symbol' ],
    'comment':    [ (130,130,120),8,'Comment' ],
    'doc':        [ (155,255,200),9,'Documentation' ],
  },
}
HL_COLOR_DESC={}
HL_COLOR_ORDER={}
DEF_HL_COLORS={}
HL_COLORS={}
for l,v in list(textColors.items()):
    colors={}
    order={}
    desc={}
    for t,c in list(v.items()):
        colors[t],order[t],desc[t]=c
    order=dict([reversed(o) for o in list(order.items())])
    HL_COLORS[l]=colors
    DEF_HL_COLORS[l]=deepcopy(colors)
    HL_COLOR_ORDER[l]=order
    HL_COLOR_DESC[l]=desc

IDE_activated=False
# Renames IDE module key in sys.modules,
# so I can set user's main module as the real main module.
# The purposes of this are :
# 1. to direct whatever user does in python prompt to happen
#    in user's own main module namespace, not in the IDE module's.
# 2. to breach "if __name__=='__main__':" block, so everything in that block will happen,
#    except World class instantiation which must be blocked with the next trick.
__name__='IDE' # new module name
sys.modules[__name__]=sys.modules.pop('__main__')

# This is the flag to block World class from being instantiated in user's main module.
# I just can't use __builtins__, since in the way user's main module is imported,
# __builtins__ is a dictionary, not __builtin__ module, so let's just abuse
# one of the more universally available writeable objects :
#     exit, quit, help, copyright, credits, or license.
# help is chosen since it's 1 of the shortest names, and the probability of
# being overwritten by user is lower than exit or quit.
help.IDE=True

from pandac.PandaModules import *
from direct.showbase.Loader import Loader
from direct.interval.IntervalGlobal import *
from direct.showbase.DirectObject import DirectObject
from direct.gui.DirectGuiBase import DirectGuiWidget
from direct.gui.DirectGui import *
from direct.task import Task
import panda3d

import pickle, math, string, re, imp, inspect, keyword, stat, traceback, types, urllib.request, urllib.parse, urllib.error, zlib
from http.client import HTTPConnection
from textwrap import TextWrapper
from collections import deque
from hashlib import md5
from glob import glob

# must be defined early so can be used by other modules
Ctrl = 'meta' if MAC else 'control'
wxCtrl = 'Meta' if MAC else 'Ctrl'
# prevents IDE tasks & ivals from getting paused, must be sync'ed with PauseResume module
IDE_ivalsName = 'IDE_IVALS_'
IDE_tasksName = 'IDE_TASKS_'
IDE_CC_tasksName = IDE_tasksName+'code_completion'
IDE_docLocRemovalTaskName = IDE_tasksName+'remove doc loc'
IDE_scheduledUpdateTaskName = IDE_tasksName+'scheduled upgrade'
dragCallTipTaskName = IDE_tasksName+'dragging call tip'
dragSGBTaskName = IDE_tasksName+'dragging SGB'
dragNPropsTaskName = IDE_tasksName+'dragging NProps'
closeWindowEventName = 'user want 2 close P3D window'

PY_VERSION = 'Python %s on %s'%(sys.version.replace('\n',''),sys.platform)
P3D_VERSION = PandaSystem.getVersionString()
# P3D pre-1.6 and 1.6+ switches
atLeast16 = PandaSystem.getMajorVersion()*10+PandaSystem.getMinorVersion()>=16
taskFunc = lambda t: t.getFunction() if atLeast16 else t.__call__
taskFuncNameQuery = lambda t: 'getFunction' if atLeast16 else '__call__'
# taskXArgs=lambda t: t.getArgs() if atLeast16 else t.extraArgs
# taskXArgsName=lambda t: 'getArgs' if atLeast16 else 'extraArgs'
# taskWakeT=lambda t: t.getDelay() if atLeast16 else t.wakeTime
asList = lambda nc: nc if atLeast16 else nc.asList()
add2List = lambda nc,np: nc.addPath(np) if atLeast16 else nc.append(np)

joinPaths = os.path.join
# IDE components paths
IDE_path = os.path.dirname(os.path.abspath(__file__))
IDE_fontsPath = joinPaths(IDE_path,'fonts')
IDE_imagesPath = joinPaths(IDE_path,'images')
IDE_soundsPath = joinPaths(IDE_path,'sounds')
IDE_macrosPath = joinPaths(IDE_path,'macros')
IDE_snippetsPath = joinPaths(IDE_path,'snippets')
IDE_tabSkinsPath = joinPaths(IDE_path,'tab skins')
IDE_sliderSkinsPath = joinPaths(IDE_path,'slider skins')
IDE_MODELPATHS = [IDE_path, IDE_soundsPath, IDE_fontsPath, IDE_imagesPath,
  IDE_tabSkinsPath, IDE_sliderSkinsPath]
IDE_settingsPath = joinPaths(IDE_path,'settings')
IDE_configPath = joinPaths(IDE_settingsPath,'settings')
IDE_keymapPath = joinPaths(IDE_settingsPath,'actionskeys')
IDE_hilighterPath = joinPaths(IDE_settingsPath,'hilighter')

def loadFromFile(path):
    f=open(path,'rU')
    obj=pickle.load(f)
    f.close()
    return obj

def dumpToFile(obj,path):
    f=open(path,'wb')
    pickle.dump(obj,f)
    f.close()

def overrideDict(orig,saved):
    for k,v in list(saved.items()):
        if k in orig:
           if type(v)==dict:
              overrideDict(orig[k],v)
           else:
              orig[k]=v


def IDE_redefineColors():
    m=IDE if IDE_activated else M
    for c,v in list(m.IDE_CFG[CFG_colors].items()):
        setattr(m,'COL_'+c,c)
        setattr(m,'IDE_COLOR_'+c,Vec4(*(v+(255,)))/255.)
    m.IDE_COLOR_callTipsBG.setW(.925)
#     IDE_COLOR_tabLabelMainModInactive.setW(.75)

def IDE_redefineHilighterColors():
    m=IDE if IDE_activated else M
    if IDE_TDExtensionAvail:
       IDE_TextDrawer.clearColors()
    m.IDE_TEXT_COLORS=[]
    for c,v in list(m.HL_COLORS['python'].items()):
        color=Vec4(*(v+(255,)))/255.
        setattr(m,'COL_python_'+c,c)
        setattr(m,'IDE_COLOR_'+c,color)
        setattr(m,'COLORIDX_'+c,len(m.IDE_TEXT_COLORS))
        m.IDE_TEXT_COLORS.append(color)
        if IDE_TDExtensionAvail:
           IDE_TextDrawer.storeColor(color)
    m.COLORIDX_notCode=(m.COLORIDX_string,m.COLORIDX_doc,m.COLORIDX_comment)

def IDE_saveCFGtoFile():
    m=IDE if IDE_activated else M
    dumpToFile(m.IDE_CFG,IDE_configPath)

def IDE_saveHilighterToFile():
    m=IDE if IDE_activated else M
    dumpToFile(m.HL_COLORS,IDE_hilighterPath)

# creates settings dir
if not os.path.exists(IDE_settingsPath):
   os.mkdir(IDE_settingsPath)

# loads saved configs
if os.path.exists(IDE_configPath):
   savedCFG=loadFromFile(IDE_configPath)
   # overrides the default configs
   overrideDict(IDE_CFG,savedCFG)
   del savedCFG
# saves after load, to save any new configs
IDE_saveCFGtoFile()

# loads saved hilighter colors
if os.path.exists(IDE_hilighterPath):
   savedHL=loadFromFile(IDE_hilighterPath)
   # overrides the default colors
   overrideDict(HL_COLORS,savedHL)
   del savedHL
# saves after load, to save any new colors
IDE_saveHilighterToFile()


from IDEwxExt import SortableListCtrl
from IDEScrolledList import ScrolledList
from IDEGauge import LoadingGauge
from IDEMenu import PopupMenu
# I can't work around 1.6's new Messenger, which insists in adding an attribute (_messengerId)
# to every event receiver object. I need all object types able to receive events,
# including C++ objects, so 1.6's Messenger can't serve this purpose.
# So, myMessenger module imported here is 1.5.3's.
from myMessenger import Messenger
from IDELog import Log
import PauseResume as PR
import IDEDrawUtil as DU
import IDEAligner as Aligner
import myFinder

# redirects output
LSS = StringStream()
MS = MultiplexStream()
MS.addStandardOutput() # I still want it to be displayed at the console
MS.addOstream(LSS)
Notify.ptr().setOstreamPtr(MS,0)
LOG = Log(LSS)
IDE_DEV = Log(None,LOG,False)
myFinder.IDE_DEV = IDE_DEV
sys.stdout = LOG
sys.stderr = sys.stdout

print('IDE started on '+time.strftime('%A, %b %d %Y, %H:%M', time.gmtime(time.time()-time.timezone)))
print(PY_VERSION+'\n\n')

# loads C++ text drawer extension
IDE_TDExtensionAvail = False
IDE_TDExtensionErr = ''
buildNote = '\nNOTE: You can download the binary for Windows,\nor download the source and build it yourself.'
try:
   if WIN:
      TD = imp.load_dynamic('TD','TD/TD for P3D %s.dll'%P3D_VERSION)
      sys.modules[TD.__name__] = TD
   else:
      from TD import TD
   IDE_TextDrawer = TD.TextDrawer()
   TDcompatible = True
   if hasattr(TD,'getP3DVersion'):
      IDE_TDP3Dversion = TD.getP3DVersion()
      if IDE_TDP3Dversion != P3D_VERSION:
         TDcompatible = False
         IDE_TDExtensionErr = '\nINCOMPATIBLE TextDrawer : built with Panda3D v%s\n'%IDE_TDP3Dversion+buildNote
         print('!'*20 + IDE_TDExtensionErr + '\n' + '!'*20 + '\n')
   else:
      IDE_TDP3Dversion = 'UNKNOWN'
   if TDcompatible:
      IDE_TDExtensionAvail = True
      print('='*35 + ('\nC++ TextDrawer extension loaded,\nbuilt with Panda3D v%s.\n'%IDE_TDP3Dversion) + '='*35 + '\n')
except Exception as errstr:
   IDE_TDExtensionErr = '\n'+str(errstr)+'\n'+buildNote
   print(r'''\\\\\\\\\\\\
WARNING  : unable to use C++ TextDrawer extension
reason   : %s
////////////
'''%IDE_TDExtensionErr[1:])

IDE_cleanupMessenger = Messenger()

# defines characters
myPunctuation = string.punctuation.replace('_','')
myPunctuationNoDot = myPunctuation.replace('.','')
myPunctuationWhitespace = myPunctuation+' ' # I don't need TAB, LF, VT, FF, and CR
myPunctuationWhitespaceLF = myPunctuation+' '+'\n' # I don't need TAB, FF, VT, and CR
myPunctuationNoDotWhitespace = myPunctuationNoDot+' ' # I don't need TAB, LF, VT, FF, and CR
myLettersScore = string.letters+'_'
myLettersDigits = string.letters+'_'+string.digits
myPrintableChars = myPunctuationWhitespace+myLettersDigits

STRINGTYPE = (bytes,str)
CLASSTYPE = (type,type)
# don't update recent files list if opening last session's files
UPDATE_RECENT_FILES = not int(sys.argv[2].strip())
IDE_QUOTES = "\'\""
IDE_SQUOTE1 = '\''
IDE_SQUOTE2 = '\"'
IDE_TQUOTE1 = '\''*3
IDE_TQUOTE2 = '\"'*3
IDE_QUOTE2IDX = {
  False:0,
  IDE_SQUOTE1:1,
  IDE_SQUOTE2:2,
  IDE_TQUOTE1:3,
  IDE_TQUOTE2:4,
}
IDE_IDX2QUOTE = invertDict(IDE_QUOTE2IDX)
IDE_CLIPBOARD = ''
PY_DIR = os.path.dirname(os.__file__)
PY_PATHS = list(sys.path)
DYN_LIB_EXT = ['.dll'] if WIN else ['.so'] if LIN else ['.so','.dylib']
DYN_LIB_EXT.append('.pyd')
LAST_FILES = 'lastFiles'
RECENT_FILES = 'recentFiles'
FILES_PROPS = 'filesProps'
MAXINT = 2**31-1
MAIN_MOD_ERROR = None
PLAYING_MACRO = False
MACROS = []
SNIPPETS = {
  'class':['''\
class :
  def __init__(self):
      pass
''',(6,)*2],
  'func':['''\
def ():
    pass
''',(4,)*2],
  'method':['''\
def (self,):
    pass
''',(4,)*2],
  'imActor':['from direct.actor.Actor import Actor\n',(37,)*2],
  'imCommonFilters':['from direct.filter.CommonFilters import CommonFilters\n',(54,)*2],
  'imDirectGui':['from direct.gui.DirectGui import *\n',(35,)*2],
  'imDirectObject':['from direct.showbase.DirectObject import DirectObject\n',(54,)*2],
  'imDirectStart':['import direct.directbase.DirectStart\n',(37,)*2],
  'imFSM':['from direct.fsm.FSM import FSM\n',(31,)*2],
  'imInterval':['from direct.interval.IntervalGlobal import *\n',(45,)*2],
  'imMopath':['from direct.directutil.Mopath import Mopath\n',(44,)*2],
  'imPandaAll':['from pandac.PandaModules import *\n',(34,)*2],
  'imPandaSome':['from pandac.PandaModules import \n',(32,)*2],
  'imPythonUtil':['from direct.showbase import PythonUtil as PU\n',(45,)*2],
  'imTask':['from direct.task import Task\n',(29,)*2],
  'main':["if __name__ == '__main__':\n",(27,)*2],
  'listComp':['[i for i in  if ]',(12,)*2],
  'generator':['(i for i in  if )',(12,)*2],
  'generatorTuple':['tuple(i for i in  if )',(17,)*2],
  'cPickleRead':['''f = open(,'rU')
v = cPickle.load(f)
f.close()
''',(9,)*2],
  'cPickleWrite':['''f = open(,'w')
cPickle.dump(,f)
f.close()
''',(9,)*2],
  'cPickleWriteBinary':['''f = open(,'wb')
cPickle.dump(,f)
f.close()
''',(9,)*2],
  'tryExcept':['try:\n    \nexcept:\n    pass\n',(9,)*2],
  'tryExceptErrStr':['try:\n    \nexcept Exception, errstr:\n    pass\n',(9,)*2],
  'tryExceptErrNoStr':['try:\n    \nexcept Exception, (errno,errstr):\n    pass\n',(9,)*2],
#   '':['',(,)*2],
}
HISTORY_ON = True
UNDO = UNDO_REPLACE = REDO = REPLACING = JUMP_TO_SAVED = MOVING_LINES = False
UPDATE_DISPLAY = True
EDIT_type = 'type'
EDIT_typeOvr = 'typeovr'
EDIT_del = 'del'
EDIT_delLine = 'delline'
EDIT_delLineTail = 'delLineTail'
EDIT_delLineHead = 'delLineHead'
EDIT_joinLines = 'joinLines'
EDIT_delSel = 'delsel'
EDIT_backsp = 'backsp'
EDIT_breakLine = 'break'
EDIT_changeCase = 'changecase'
EDIT_changeCaseSel = 'changecasesel'
EDIT_comment = 'comment'
EDIT_indentSel = 'indent'
EDIT_copyLine = 'copyline'
EDIT_moveLines = 'movelines'
EDIT_paste = 'paste'
IDE_REPEATCHARS_lastChars = ''
IDE_REPEATCHARS_lastCount = ''
IDE_REPEATCHARS_lastColumn = ''
IDE_SELECTMODE_char = 0
IDE_SELECTMODE_word = 1
IDE_SELECTMODE_line = 2
IDE_SELECTMODE = IDE_SELECTMODE_char
IDE_textTexturesUpdateDate = time.mktime( (2009,6,20)+(0,)*6 )
IDE_LOG_NAME = 'LOG.txt'
IDE_logOverSceneNodeName = 'log instance'
IDE_logOverSceneTexName = 'logTextOverScene-%s.png'%PLATFORM
IDE_logOverSceneTexPath = joinPaths(IDE_path,IDE_logOverSceneTexName)
IDE_CC_MODE_start = 0
IDE_CC_MODE_anywhere = 1
IDE_CC_MODE_desc = ['match start', 'match anywhere']
IDE_CC_MODE = IDE_CC_MODE_start
IDE_CC_IMPdictName = '__IMP_dict__'
IDE_CC_excludedPackages = ('directscripts','directbase','extensions_native','ffi',)
IDE_CC_deprecated = ('rgbimg','gopherlib','sre','xmllib',)
IDE_CC_isSnippet = IDE_CC_isImport=False
LIST_ITEMS = lambda obj:list(obj.keys()) if type(obj)==dict else dir(obj)
GET_ITEM = lambda obj,i:obj[i] if type(obj)==dict else getattr(obj,i) 
IDE_HL_None = 0
IDE_HL_Python = 1
IDE_isScenePaused = False
IDE_isUpgrading = False
IDE_isCtrlDown = False
IDE_exitStatus = 0
IDE_lastClickTime = 0
IDE_lastChosenColor = [0,0,0]
IDE_lastInjectedChar = None
IDE_lastModeB4ForcedRender = None
IDE_lastPreferencePage = IDE_lastKeymapCategory = 0
IDE_REptr_backSlsAtEnd = re.compile(r'\\$')
IDE_REptr_allBackSlsAtEnd = re.compile(r'\\+$')
IDE_REptr_backSlsQuote1 = re.compile(r'\\+\'')
IDE_REptr_backSlsQuote2 = re.compile(r'\\+\"')
IDE_REptr_backSls3Quote1 = re.compile(r'\\+\'\'\'')
IDE_REptr_backSls3Quote2 = re.compile(r'\\+\"\"\"')
IDE_REptr_lettersScore = re.compile(r'\w*')
IDE_REptr_possibleNum = re.compile(r'(\d*\.*)?\d*(\w+(-|\+)?\d*)?')
IDE_REptr_digits = re.compile(r'\d+\b')
IDE_REptr_punctFloat = re.compile(r'\.\d*(e(-|\+)?\d+)?')
IDE_REptr_float = re.compile(r'\d+\.?\d*(e(-|\+)?\d+)?')
# IDE_REptr_digitsWdots = re.compile(r'\d+[\w\d\.\d*e\-?\d+]*')
IDE_REptr_punctNoHashQuotes = re.compile(r'[^\w\s\'\"#]+')
IDE_REptr_quotesSequence1 = re.compile(r"\'+")
IDE_REptr_quotesSequence2 = re.compile(r'\"+')
IDE_REptr_space = re.compile(r'\s+')
IDE_REfont = [8, wx.TELETYPE, wx.NORMAL, wx.NORMAL]
IDE_FIND_list = []
IDE_FIND_re = IDE_FIND_caseSensitive = IDE_FIND_wholeWord = IDE_FIND_wildcards = False
IDE_REPLACE_list = []
IDE_REPLACE_dirList = []
IDE_REPLACE_prompt = True
IDE_REPLACE_slash = IDE_REPLACE_recurse = False
IDE_REPLACE_dirFilter = ['py pyw pyx']
IDE_REPLACE_numReplaced = None
IDE_bracketsPairs = {'(':')','[':']','{':'}'}
IDE_bracketsInvPairs = {')':'(',']':'[','}':'{'}
IDE_openBrackets = '([{'
IDE_closeBrackets = ')]}'
MODIF_alt = KeyboardButton.alt()
MODIF_shift = KeyboardButton.shift()
MODIF_control = KeyboardButton.control()
MODIF_meta = KeyboardButton.meta()
IDE_modifiers = (MODIF_alt,MODIF_shift,MODIF_control,MODIF_meta)
IDE_MSG_ready = 'Happy coding :D'
IDE_errShoutout = r'''
I guess   _           ____________________________________________
 I'm  _  [C]lueless  /                                            \
      O   |         |  That's why you make mistakes all the time  |
    _=^==^          \  __________________________________________/
    \_|             /,"
     .^.           /
     | |         `O__)
.____|/._________./_<.___
                         \_________________________________
                                                           \_______
                              E_R_R_O_R                            \
'''
NOT_YET = 'SORRY, NOT YET IMPLEMENTED'
# wxDir=os.path.dirname(sys.modules['wx'].__file__)
directModulesDir = os.path.abspath(os.path.join(os.path.dirname(sys.modules[Task.__name__].__file__),os.pardir))

imgSize = 64
imgMaxIdx = imgSize-1
img = PNMImage(1,imgSize)
img.addAlpha()
img.fill(1)
for z in range(imgSize):
    img.setAlpha(0,z,math.sin(deg2Rad(20+z*70./imgSize)))
IDE_gradingAlphaTexV0 = Texture()
IDE_gradingAlphaTexV0.load(img)
for z in range(imgSize):
    img.setAlpha(0,z,math.sin(deg2Rad(25+z*65./imgSize)))
IDE_gradingAlphaTexV0_1 = Texture()
IDE_gradingAlphaTexV0_1.load(img)
for z in range(imgSize):
    img.setAlpha(0,z,math.sin(deg2Rad(40+z*60./imgSize)))
IDE_gradingAlphaTexV0_2 = Texture()
IDE_gradingAlphaTexV0_2.load(img)
for z in range(imgSize):
    img.setAlpha(0,imgMaxIdx-z,math.sin(deg2Rad(20+70.*z/imgSize)))
IDE_gradingAlphaTexV1 = Texture()
IDE_gradingAlphaTexV1.load(img)
for z in range(imgSize):
    img.setAlpha(0,imgMaxIdx-z,math.sin(deg2Rad(25+65.*z/imgSize)))
IDE_gradingAlphaTexV1_1 = Texture()
IDE_gradingAlphaTexV1_1.load(img)
for z in range(imgSize):
    img.setAlpha(0,imgMaxIdx-z,math.sin(deg2Rad(30+60.*z/imgSize)))
IDE_gradingAlphaTexV1_2 = Texture()
IDE_gradingAlphaTexV1_2.load(img)

for tex in (IDE_gradingAlphaTexV0,IDE_gradingAlphaTexV0_1, 
            IDE_gradingAlphaTexV1,IDE_gradingAlphaTexV1_1,IDE_gradingAlphaTexV1_2):
    tex.setWrapV(Texture.WMClamp)


IDE_redefineColors()
IDE_redefineHilighterColors()

IDE_QUOTE_COLOR={
  False:COLORIDX_identifier,
  IDE_SQUOTE1:COLORIDX_string,
  IDE_SQUOTE2:COLORIDX_string,
  IDE_TQUOTE1:COLORIDX_doc,
  IDE_TQUOTE2:COLORIDX_doc,
}


def removePYC(path):
    '''
    Removes all .pyc files, since their module path is hardcoded inside.
    It's annoying for development on a multi-OSes machine.
    When an arror occurs, it's the other OS (where the .pyc was generated) path
    is reported in traceback. How nice........>_<
    '''
    PYCs=[]
    for root, dirs, files in os.walk(path):
        for f in files:
            if os.path.splitext(f)[1].upper()=='.PYC':
               fullpath=joinPaths(root,f)
               sameName=glob(os.path.splitext(fullpath)[0]+'.*')
               # remove .PYC only if there is the .PY
               PYexists=[n for n in sameName if os.path.splitext(n)[1].upper()=='.PY']
               if PYexists:
                  PYCs.append(fullpath)
    for f in PYCs:
        os.remove(f)

PStatsEnabled=int(sys.argv[5].strip())

FILESEP='*'*4
GET_ITEMS_FROM_ARG = lambda arg:arg.strip().strip('"')[1:-1].split(FILESEP)
LAST_mainNcurr = GET_ITEMS_FROM_ARG(sys.argv[3])
APP_files = GET_ITEMS_FROM_ARG(sys.argv[1])
APP_args = [a.strip('"') for a in sys.argv[6:]]
RunningAPP_CWD=APP_CWD=OldAPP_CWD=LAST_mainNcurr.pop()
if LAST_mainNcurr[0] in APP_files:
   RunningAPP_mainFile=APP_mainFile=LAST_mainNcurr[0]
else:
   RunningAPP_mainFile=APP_mainFile=APP_files[0]

print('############### YOUR FILES ###############', file=IDE_DEV)
print('\n'.join(APP_files), file=IDE_DEV)
print('##########################################', file=IDE_DEV)
print('CWD :',APP_CWD, file=IDE_DEV)
print('##########################################', file=IDE_DEV)
print('args :',APP_args, file=IDE_DEV)
print('##########################################\n', file=IDE_DEV)

IDE_lastBrowsePath=os.path.dirname(APP_mainFile)
removePYC(IDE_lastBrowsePath)

sys.path.insert(0,APP_CWD)
sys.path.append(IDE_lastBrowsePath)
os.chdir(APP_CWD)
# sets arguments for main module
sys.argv=[APP_mainFile]+APP_args

MODE_starting='IDE_starting'
MODE_SUFFIX=':-> '

IDE_WP_cursor=WindowProperties()
IDE_WP_mouseMode=WindowProperties()

# I want to remove all RTT upon update, so I need an easy way to tell
# all cameras to remove theirselves and their outputs
def killCam(self):
    camNP=NodePath(self)
    if not self in (base.cam.node(),base.cam2d.node(),base.cam2dp.node()) and \
         self.getName()!='closeup vpcam' and self.getNumDisplayRegions():
       Goutput=self.getDisplayRegion(0).getWindow()
       Goutput.clearRenderTextures()
       if Goutput==base.win:
          DRs=[Goutput.getDisplayRegion(i) for i in range(Goutput.getNumDisplayRegions()) \
             if not Goutput.getDisplayRegion(i).getCamera().isEmpty() and \
             Goutput.getDisplayRegion(i).getCamera().node()==self]
          for dr in DRs:
              Goutput.removeDisplayRegion(dr)
          return
       Goutput.removeAllDisplayRegions()
       Goutput.getGsg().getEngine().removeWindow(Goutput)
       camNP.removeNode()


ORIG_FUNCS={}
def replaceOrigFunc(cls,n):
    newName=n.__name__
    f=getattr(cls,newName)
    name='%s.%s'%(cls.__name__, newName)
    # transfers all possible attributes
    for a in dir(f):
        try:
           setattr(n,a,getattr(f,a))
        except:
           pass
    n.__module__=cls.__module__
    ORIG_FUNCS[name]=f
    Dtool_funcToMethod(n,cls)
    del GLOBALS[newName]

def setLens(self,*args):
    IDE_cleanupMessenger.accept('killAllCameras',self,killCam,[self])
    ORIG_FUNCS['Camera.setLens'](*((self,)+args))
replaceOrigFunc(Camera, setLens)

def copyLens(self,*args):
    IDE_cleanupMessenger.accept('killAllCameras',self,killCam,[self])
    ORIG_FUNCS['Camera.copyLens'](*((self,)+args))
replaceOrigFunc(Camera, copyLens)

# overrides app's pointer movement, so it will be blocked if the IDE is active
def movePointer(self,*args):
    if IDE_activated:
       if IDE_root.isHidden():
          return ORIG_FUNCS['GraphicsWindow.movePointer'](*((self,)+args))
       else:
          if IDE.APP_pointerNrestPos is None:
             IDE.APP_pointerNrestPos=args
          return False
replaceOrigFunc(GraphicsWindow, movePointer)


def orderedDifference(s1,s2):
    d=[]
    for i in s1:
        if i not in s2 and i not in d:
           d.append(i)
    for i in s2:
        if i not in s1 and i not in d:
           d.append(i)
    return d
def difference(s1,s2):
    return list((set(s1).symmetric_difference(s2)))
def intersection(s1,s2):
    return list((set(s1).intersection(s2)))

def IDE_setLoaderPaths():
    for p in IDE_MODELPATHS:
        getModelPath().appendPath(p)

def IDE_showCursor():
    IDE_WP_cursor.setCursorHidden(0)
    base.win.requestProperties(IDE_WP_cursor)

def IDE_hideCursor():
    IDE_WP_cursor.setCursorHidden(1)
    base.win.requestProperties(IDE_WP_cursor)

def IDE_setMouseAbsolute():
    IDE_WP_mouseMode.setMouseMode(WindowProperties.MAbsolute)
    base.win.requestProperties(IDE_WP_mouseMode)

def IDE_setMouseRelative():
    IDE_WP_mouseMode.setMouseMode(WindowProperties.MRelative)
    base.win.requestProperties(IDE_WP_mouseMode)

def TASK_run(tm):
    print('\nINFO: run() is not here, use IDErun() instead.\n')
Task.TaskManager._origRun=Task.TaskManager.run
Task.TaskManager.run=TASK_run

def IDE_safeRun():
    try:
        taskMgr._origRun()
    except SystemExit:
        if IDE.IDE_exitStatus==1:
           IDE_shutdown()
        else:
           print("user's APP just tried to force exit", file=IDE_DEV)
           IDE_alertUserNcontinue()
    except:
        print(IDE_errShoutout)
        traceback.print_exc()
        if 'IDE_alertUserNcontinue' not in GLOBALS:
           IDE_doActivate()
        IDE_alertUserNcontinue()


###############################################################################
###############################################################################
# ISOLATES USER'S APPLICATION (MAIN MODULE),
# so I only need to hunt in this class instance's namespace, should be fast
class APP_MODULE:
   def __init__(self):
       m = IDE if IDE_activated else M
       niceName = '__main__'
       self.moduleName = niceName
       ### LOADS THE MAIN MODULE
       f = open(m.APP_mainFile,'rU')
       try:
          user_module = imp.load_source(niceName,m.APP_mainFile,f)
       except:
          user_module = types.ModuleType('')
          user_module.__file__ = m.APP_mainFile#''
          user_module.__builtins__ = __builtins__
          sys.modules[niceName] = user_module
          m.MAIN_MOD_ERROR = traceback.format_exc()
          m.MAIN_MOD_TRACEBACK = sys.exc_info()[2]
          if not hasattr(__builtin__,'base'):
             import direct.directbase.DirectStart
       finally:
          f.close()
       # SAVE WORLD INSTANCE IF IT'S ALREADY CREATED
       if hasattr(user_module,'winst'):
          self.WorldInst = user_module.winst
       # CREATE AND SAVE THE INSTANCE SO I CAN FIND IT LATER
       elif hasattr(user_module,'World'):
          self.WorldInst=user_module.World()#  <----- the World class
       else:
          self.WorldInst = None
       self.modDir = os.path.dirname(user_module.__file__)
       m.RunningAPP_modDir=self.modDir

# I need to know what ShowBase puts in __builtin__,
# to protect them from being destroyed
from direct.showbase.ShowBase import ShowBase
def ShowBase__newInit(self):
    global FrameworkComponents, FrameworkEvents, ShowBaseAttrs
    visitedAttrs=[]
    def ShowBase__copyAttr(self):
        for k in ShowBaseAttrs:
            if not hasattr(self,k):
               setattr(self,k,getattr(base,k))
    def getObj(seq):
        objs=[]
        if seq not in visitedAttrs:
           visitedAttrs.append(seq)
           for i in seq:
               if i:
#                   print type(i).__name__
                  if type(i) in myFinder.PythonSequence:
                     objs+=getObj(seq)
                  elif type(i)==dict:
                     objs+=getObj(list(seq.values()))
                  elif type(i) not in myFinder.skippedTypes:
                     objs.append(i)
        return objs
    ShowBase.__origInit__(self)
    ShowBase.__init__ = ShowBase__copyAttr
    ShowBase.run = lambda s:None
    newBV = list(builtins.__dict__.values())
    builtinObjs = getObj([v for v in list((set(newBV).difference(_BV_)))]) + [ivalMgr]
    ShowBaseObjs = getObj(list(base.__dict__.values()))
    FrameworkComponents = builtinObjs+ShowBaseObjs
    myFinder.FrameworkComponents = FrameworkComponents
    myFinder.FrameworkComponentsAvail = True
    FrameworkEvents = messenger.getAllAccepting(base)
    ShowBaseAttrs = list(base.__dict__.keys())
#     print '\n'.join([str(type(c.node()) if type(c)==NodePath else type(c)) for c in FrameworkComponents])
#     print 'FrameworkEvents:\n',FrameworkEvents
ShowBase.__origInit__ = ShowBase.__init__
ShowBase.__init__ = ShowBase__newInit

def tempWxLoop(task):
    while newWxEVTloop.Pending():
        newWxEVTloop.Dispatch()
    # very important for UI updates
    wxApp.ProcessIdle()
    return Task.cont

def offerCreateWindow():
    global createWindowFrame
    createWindowFrame = wx.Frame(None,-1,'IDE: no host window')
    createWindowPanel = wx.Panel(createWindowFrame)
    createWindowFrame.Bind(wx.EVT_CLOSE,lambda e:0) # not closeable
    cwSizer = wx.BoxSizer(wx.VERTICAL)
    yesB = wx.Button(createWindowPanel,-1,'Create default window',size=(240,40))
    yesB.Bind(wx.EVT_BUTTON,createDefaultWindow)
    cwSizer.Add(yesB,-1,wx.ALL|wx.CENTER,5)
 
    createWindowPanel.SetSizer(cwSizer)
    cwSizer.Fit(createWindowFrame)
    cwSizer.SetSizeHints(createWindowFrame)
    createWindowFrame.SetMaxSize(createWindowFrame.GetSize())
    createWindowFrame.Center()
    createWindowFrame.Show()

    taskMgr.add(tempWxLoop, IDE_tasksName+'tempWxLoop')

def closeOfferCreateWindow():
    try:
       createWindowFrame.Destroy()
       while newWxEVTloop.Pending():
           newWxEVTloop.Dispatch()
       wxApp.ProcessIdle()
    except:
       pass

def createDefaultWindow(e):
    closeOfferCreateWindow()
    base.openDefaultWindow()

def pollConn():
    asyncore.loop(0,False,count=1)
    return Task.cont

def IDE_activate(win):
    if win==base.win:
       taskMgr.doMethodLater(.01,IDE_doActivate,IDE_tasksName+'activate',extraArgs=[])

def IDE_doActivate():
    global __name__,IDE_activated
    if IDE_activated: return
    # removes the create window dialog
    taskMgr.remove(IDE_tasksName+'tempWxLoop')
    closeOfferCreateWindow()

    __name__='IDEmini'
    sys.modules[__name__] = sys.modules.pop('IDE')
    # runs the main bulk of IDE code
    exec(('import IDE\nfrom IDE import *'), GLOBALS)
    IDE_activated = True
    # redefines old refs to the real IDE core module
    myFinder.IDE = IDE
    IDEFileSrv.IDE = IDE
    taskMgr.add(pollConn,IDE_tasksName+'fileSrv poll',extraArgs=[])

IDE_setLoaderPaths()
getModelPath().appendPath(APP_CWD)
DirectObject().acceptOnce('window-event',IDE_activate)
VirtualFileSystem.getGlobalPtr().chdir(Filename.fromOsSpecific(APP_CWD))

# RUNS USER'S MAIN MODULE
APP = APP_MODULE()

if not 'FrameworkComponents' in GLOBALS: # ShowBase not yet started
   import direct.directbase.DirectStart
if not base.win: # no usable window yet, offer user to create one
   offerCreateWindow()

IDE_safeRun()
