"""Undocumented Module"""

__all__ = ['findClass', 'rebindClass', 'copyFuncs', 'replaceMessengerFunc', 'replaceTaskMgrFunc', 'replaceStateFunc', 'replaceCRFunc', 'replaceAIRFunc', 'replaceIvalFunc']

import time
import types
import os
import new
import sys


# YNJH : additional stuff needed to go dynamic
from pandac.PandaModules import Camera, NodePath, NodePathCollection, CollisionTraverser, LightNode
from direct.interval.IntervalGlobal import ivalMgr
from direct.showbase.ShowBase import ShowBase
from collections import deque
import imp, traceback
from IDE import atLeast16,taskFuncNameQuery,taskFunc,asList,IDE_path,IDE_ivalsName

debugDynamic=False

PythonSequence=(list, tuple, set, frozenset, deque)
FunctionOrMethod=(types.FunctionType,types.MethodType,\
   types.BuiltinFunctionType,types.BuiltinMethodType,types.UnboundMethodType)
InstanceOrObject=(types.InstanceType, object)
skippedTypes=(
   bool,
   memoryview,
   type,
   float,
   int,
   int,
   types.ModuleType,
   type(None),
   slice,
   bytes,
   type,
   ) + FunctionOrMethod
visitedInstances = []
preservedObjName = ('__builtins__','_messengerId')
destructors = {
          'Task':['remove'],
          'FSM':['cleanup'],
          'Actor':['stop','cleanup'],
          'AudioSound':['stop'],
          'CollisionTraverser':['clearColliders'],
          'CollisionHandlerPhysical':['clearColliders','clearRecorder'],
          'CommonFilters':['cleanup'],
          'DirectObject':['ignoreAll'],
          'DirectDialog':['cleanup'],
          'DirectFrame':['destroy'],
          'FilterManager':['cleanup'],
          'OnscreenText':['destroy'],
          'OnscreenImage':['destroy'],
          'MovieTexture':['releaseAll'],
          'MetaInterval':['pause'],
          'LerpFunctionInterval':['pause'],
          'LerpNodePathInterval':['pause'],
          'NodePath':['removeNode'],
          'ParticleEffect':['cleanup'],
          }

def truncStr(item,length):
    s=str(item)[:length]
    if len(s)==length:
       s+='...'
    return s

def findClass(className):
    """
    Look in sys.modules dictionary for a module that defines a class
    with this className.
    """
    for moduleName, module in list(sys.modules.items()):
        # Some modules are None for some reason
        if module is not None:
            #print>>IDE_DEV, "Searching in ", moduleName
            classObj = module.__dict__.get(className)
            # If this modules defines some object called classname and the
            # object is a class or type definition and that class's module
            # is the same as the module we are looking in, then we found
            # the matching class and a good module namespace to redefine
            # our class in.
            if (classObj and
                ((type(classObj) == type) or
                 (type(classObj) == type)) and
                (classObj.__module__ == moduleName)):
                return [classObj, module.__dict__]
#             if (classObj and
#                type(classObj) == types.ClassType and
#                classObj.__module__ == moduleName):
#                return [classObj, module.__dict__]
    return None, None

def rebindClass(builtinGlobals, filename, userModName=None):
    print('#################################################', file=IDE_DEV)
    print('####### REBIND STARTED ##########################', file=IDE_DEV)
    if userModName:
       # aggresively remove this module
       if userModName in sys.modules:
          del sys.modules[userModName]
       f = open(IDE.APP_mainFile,'rU')
       try:
          user_module = imp.load_source(userModName,IDE.APP_mainFile,f)
          print('####### FINISHED REBIND #########################', file=IDE_DEV)
          return None
       except Exception:
          user_module = types.ModuleType('')
          user_module.__file__ = IDE.APP_mainFile
          user_module.__builtins__ = __builtins__
          sys.modules[userModName] = user_module
          IDE.MAIN_MOD_ERROR = traceback.format_exc()
          IDE.MAIN_MOD_TRACEBACK = sys.exc_info()[2]
          print('''#########################################
                 \n EXCEPTION WHILE REBINDING MAIN MODULE :
                 \n#########################################''', file=IDE_DEV)
          traceback.print_exc()
          return traceback.format_exc()
       finally:
          f.close()
    try:
        file = open(filename, 'r')
        lines = file.readlines()
        for i in range(len(lines)):
            line = lines[i]
            if (line[0:6] == 'class '):
                # Chop off the "class " syntax and strip extra whitespace
                classHeader = line[6:].strip()
                # Look for a open paren if it does inherit
                parenLoc = classHeader.find('(')
                if parenLoc > 0:
                    className = classHeader[:parenLoc].strip()
                else:
                    # Look for a colon if it does not inherit
                    colonLoc = classHeader.find(':')
                    if colonLoc > 0:
                        className = classHeader[:colonLoc].strip()
                    else:
                        print('error: className not found', file=IDE_DEV)
                        continue

                print('### Rebinding Class : %s'%className, file=IDE_DEV)
                # YNJH_JO : to rebind the next classes, I indented the remaining of these lines
                # Try to find the original class with this class name
                res = findClass(className)

                if not res:
                   print('Warning: Finder could not find class', file=IDE_DEV)
                   # If not found, proceed to the next one instead.
                   continue

                # Store the original real class
                realClass, realNameSpace = res

                # Now execute that class def in this namespace
                exec(compile(open(filename, "rb").read(), filename, 'exec'), realNameSpace)

                # That execfile should have created a new class obj in that namespace
                tmpClass = realNameSpace[className]

                # Copy the functions that we just redefined into the real class
                copyFuncs(tmpClass, realClass)

                # Now make sure the original class is in that namespace,
                # not our temp one from the execfile. This will help us preserve
                # class variables and other state on the original class.
                realNameSpace[className] = realClass
        file.close()
        print('####### FINISHED REBIND #########################', file=IDE_DEV)
        return None
    except Exception:
        file.close()
        print('''#######################################
               \n EXCEPTION WHILE REBINDING THE CLASS :
               \n#######################################''', file=IDE_DEV)
        traceback.print_exc()
        return traceback.format_exc()

def cleanup():
    global visitedInstances,oldVisitedInstances,debugDynamic
    print('CLEANING UP.....', file=IDE_DEV)
    for c,cp in ([base.cam,camera],[base.cam2d,base.camera2d]):
        c.node().hideFrustum()
        c.removeChildren()
        c.clearTransform()
        cp.removeChildren()
        c.reparentTo(cp)
    try:
       ####################################################################
       clearVisitedInstances()
       if debugDynamic:
          print('//=====REMOVED INSTANCE ITEMS=====', file=IDE_DEV)
       # START THE HUNT IN USER'S LOCALIZED NAMESPACE
       myWorld=IDE.APP
       realClass, realNameSpace = findClass('World')
       if realClass is not None:
          oldVisitedInstances=list(visitedInstances)
          # crush the World instance
          crushInstance(realClass,myWorld.WorldInst)
       # cleans up main module's global namespace
       if myWorld.moduleName in sys.modules:
          mainMod=sys.modules[myWorld.moduleName]
          potentialGlobal=[v for v in list(mainMod.__dict__.values()) \
              if type(v) not in skippedTypes and v not in FrameworkComponents]
          for item in potentialGlobal:
              if item not in visitedInstances:
#                  visitedInstances.append(item)
#                  print 'potentialGlobal:',item.__class__.__name__
#                  if hasattr(item,'__dict__'):
#                     for i in item.__dict__:
#                         if i!='DtoolClassDict':
#                            removeItem(item.__dict__[i])
#                            if i!='_messengerId' and type(item.__dict__)!=types.DictProxyType:
#                               item.__dict__[i]=None
#                  if type(item) in FunctionOrMethod:
#                     name=item.__name__
#                     for t in taskMgr.getTasks()+taskMgr.getDoLaters():
#                         if t and hasattr(t,taskFuncNameQuery(t)) and taskFunc(t).__name__==name:
#                            t.remove()
#                            break
#                     removeItem(item)
#                  else:
#                  removeTasks(item)
                 removeItem(item)
#                  destroyItem(item)
          # preserve __builtins__ in user's main module, since IDErun lives there.
          bi=mainMod.__builtins__
          mainMod.__dict__.clear()
          mainMod.__builtins__=bi

       ##### THE FINAL CLEANUP, IN CASE OF UNSAVED OBJECTS______________________
       if type(base.cTrav)==CollisionTraverser:
          base.cTrav.clearColliders()
          base.cTrav=0
       # cleanup intervals
       ivals=[i for i in ivalMgr.getIntervalsMatching('*') if i.getName().find(IDE_ivalsName)<0]
       for i in ivals:
           i.pause()
       # cleanup events hooks for paused objects
       PR=sys.modules['PauseResume']
       for e in PR.PRmsg.getEvents():
           PRListeners=PR.PRmsg.whoAccepts(e)
           if PRListeners:
              for l in list(PRListeners.keys()):
                  PR.PRmsg.ignoreAll(l)
       # cleanup events hooks for objects handled by Panda's default messenger,
       # except the IDE and objects under direct (thus including showbase)
       directModulesDir=IDE.directModulesDir
       for e in messenger.getEvents():
           leftOverListeners=messenger.whoAccepts(e)
           if leftOverListeners:
              for l in list(leftOverListeners.keys()):
                  if hasattr(leftOverListeners[l][0],'__module__'):
                     if leftOverListeners[l][0].__module__ is not None and\
                        leftOverListeners[l][0].__module__ in sys.modules and\
                        hasattr(sys.modules[leftOverListeners[l][0].__module__],'__file__'):
                        modDir=os.path.dirname(sys.modules[leftOverListeners[l][0].__module__].__file__)
                     else:
                        modDir='only:exist?in<my dream>'
                  elif hasattr(leftOverListeners[l][0],'__self__') and\
                       hasattr(leftOverListeners[l][0].__self__,'__module__'):
                     if hasattr(sys.modules[leftOverListeners[l][0].__self__.__module__],'__file__'):
                        modDir=os.path.dirname(sys.modules[leftOverListeners[l][0].__self__.__module__].__file__)
                     else:
                        modDir='only:exist?in<my dream>'
                  else:
                     print('leftOverListeners[l][0]:',leftOverListeners[l][0])
                     error_here
                  modExists=os.path.exists(modDir)
                  if modExists:
                     if modDir==IDE_path: # don't remove IDE's events
#                         print>>IDE_DEV, modDir,l
                        pass
                     # don't remove direct/showbase/framework events hook
                     elif modDir.find(directModulesDir)==-1:
                        messenger.ignoreAll(messenger._getObject(l) if type(l)==tuple else l)
                  elif modDir:
                     messenger.ignoreAll(messenger._getObject(l) if type(l)==tuple else l)
       # cleanup non-default ShowBase events, ie. created by user using base.accept()
       for e in messenger.getAllAccepting(base):
           if e not in IDE.FrameworkEvents:
              base.ignore(e)
       # cleanup scenegraphs
       NC=NodePathCollection()
       # excludes all aspect2d's default children
       for a2dChild in [ k for k,v in list(vars(base).items())\
                         if k.find('a2d')==0 and \
                            k.find('a2dp')==-1 and \
                            type(v)==NodePath
                            ]:
           NC.addPath(getattr(base,a2dChild))
       NC.stash()
       for scene,excludedChildren in ((render,[]),(render2d,[aspect2d])):
           scene.getStashedChildren().unstash()
           for ec in excludedChildren:
               ec.stash()
           scene.removeChildren()
           for ec in excludedChildren:
               ec.unstash()
               ec.removeChildren()
       NC.unstash()
       for c in asList(NC):
           c.removeChildren()
       NC.clear()
       # clears the saved sounds and movies
       PR.notPausableSounds=[]
       PR.notPausableMovies=[]
       # THE FINAL CLEANUP END__________________________________________________
       ret=realClass
    except Exception:
       print('''#######################################
              \n EXCEPTION WHILE CLEANING UP:
              \n#######################################''', file=IDE_DEV)
       traceback.print_exc()
       ret=traceback.format_exc()

    clearVisitedInstances()
    # restores the cameras back to their default scene
    camera.reparentTo(render)
    if IDE.IDE_CFG[IDE.CFG_resetCamTransform]:
       camera.clearTransform()
    base.camera2d.reparentTo(render2d)
    base.camera2d.clearTransform()
    return ret

def restart(realClass):
    global visitedInstances,oldVisitedInstances
    print(r'''
###############_
\\_             \_________________________________________||^^^^^^^^^^^^^^\\_
  _| RESTARTING: __ %s
//             _/
###############
'''%os.path.basename(IDE.APP_mainFile))
    try:
       #v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^
       myWorld=IDE.APP
       # World instance is already created
       if hasattr(sys.modules[myWorld.moduleName],'winst'):
          myWorld.WorldInst=sys.modules[myWorld.moduleName].winst
       # time to create an instance of the world class
       elif hasattr(sys.modules[myWorld.moduleName],'World'):
          try:
             myWorld.WorldInst=sys.modules[myWorld.moduleName].World()
          except: # INSTANTIATION FAILED, DESTROY THE PREMATURE INSTANCE
             visitedInstances=oldVisitedInstances
             myWorld.WorldInst=getBrokenInst(realClass)
             crushInstance(realClass,myWorld.WorldInst)
             clearVisitedInstances()
             raise
          if debugDynamic:
             print('\\\================================', file=IDE_DEV)
       #                print>>IDE_DEV, newInstanceQueue
       #                print>>IDE_DEV, visitedInstances
          # end
          ####################################################################
       else:
          myWorld.WorldInst=None
       return None
    except Exception:
       print('''#######################################
              \n EXCEPTION WHILE RESTARTING :
              \n#######################################''', file=IDE_DEV)
       traceback.print_exc()
       return traceback.format_exc()

def isItGoodToCrush(item):
    if type(item) in skippedTypes:
       return False
    good=type(item) in InstanceOrObject and item not in FrameworkComponents
    if not good:
       if hasattr(item,'__class__'):
          for b in item.__class__.__bases__:
              if b in InstanceOrObject:
                 return True
       return False
    return True

def crushInstance(realClass,item):
    global visitedInstances
    if isItGoodToCrush(item):
       realClassStr=str(realClass)
       if realClassStr.find('<')>-1:
          realClassStr=realClassStr.split("'")[1]
#        print>>IDE_DEV, '111:',realClassStr
#        print>>IDE_DEV, '222:',item.__class__.__module__+'.'+item.__class__.__name__
       itemClass=item.__class__
       if realClassStr==str(itemClass.__module__+'.'+itemClass.__name__):
          # CLASS INSTANCE FOUND, remove it away for good
          removeItem(item)
          #~ if item not in visitedInstances:
             #~ visitedInstances.append(item)
             #~ for i in item.__dict__:
                 #~ if i!='DtoolClassDict':
                    #~ removeItem(item.__dict__[i])
                    #~ if i not in preservedObjName:
                       #~ item.__dict__[i]=None
#~ #              removeTasks(item)
             #~ destroyItem(item)
          #~ elif debugDynamic:
             #~ print>>IDE_DEV, 'VISITED INSTANCE :',truncStr(item,50)
          return 1
       elif item not in FrameworkComponents:
          # not the CLASS INSTANCE we want
          if item not in visitedInstances:
             visitedInstances.append(item)
             if hasattr(item,'__dict__'):
                for v in list(item.__dict__.values()):
                    crushInstance(realClass,v)
          else:
             if debugDynamic:
                print('VISITED INSTANCE :',truncStr(item,50), file=IDE_DEV)
    elif type(item) in PythonSequence:
       #print>>IDE_DEV, item
       for i in range(item):
           crushInstance(realClass,i)
    elif type(item)==dict:
       for v in list(item.values()):
           crushInstance(realClass,v)
    return 0

def clearVisitedInstances():
    global oldVisitedInstances,visitedInstances
    oldVisitedInstances=[]
    visitedInstances=[]

def getBrokenInst(realClass,noModuleName=0):
    brokenInnerTB=sys.exc_info()[2].tb_next
    if not brokenInnerTB:
       return None
    brokenInstLocals=brokenInnerTB.tb_frame.f_locals
    currentBrokenInstLocals=list(brokenInstLocals.values())
    brokenInstLocalsCollections=[]
#     print>>IDE_DEV, 'BROKEN LOCALS :'
    # keep tracking 'til the REAL error found in the end of tracebacks chain
    brokenInnerTB=brokenInnerTB.tb_next
    while brokenInnerTB!=None:
        brokenInstLocals=brokenInnerTB.tb_frame.f_locals
        brokenInstLocalsCollections+=list(brokenInstLocals.values())
        brokenInnerTB=brokenInnerTB.tb_next
#         print>>IDE_DEV, brokenInstLocals
#     print>>IDE_DEV, 'brokenInstLocalsCollection :',brokenInstLocalsCollection
    for i in currentBrokenInstLocals:
        instClass=i.__class__
        if noModuleName:
           found=realClass==instClass.__name__
        else:
           found=str(realClass)==str(instClass.__module__+'.'+instClass.__name__)
        if found:
           print('XXXXX-------------------XXXXX', file=IDE_DEV)
           print('--> BROKEN INSTANCE FOUND !!!', file=IDE_DEV)
           print('XXXXX-------------------XXXXX', file=IDE_DEV)
           # just save those broken instances in this broken instance's __dict__,
           # so they can be crushed altogether later
           i.IDE_BROKEN_INST_COLLECTIONS=brokenInstLocalsCollections
           return i

def removeTasks(item):
    if item in FrameworkComponents: return
    for i in dir(item):
        if type(getattr(item,i)) in FunctionOrMethod:
           for t in taskMgr.getTasks()+taskMgr.getDoLaters():
               if t and hasattr(t,taskFuncNameQuery(t)) and taskFunc(t).__name__==i:
                  print(t.name)
                  t.remove()
                  break

def removeItem(item):
    if item in FrameworkComponents or item in visitedInstances: return
    visitedInstances.append(item)
    isShowBaseInst = isinstance(item,ShowBase) and item!=base
    # CLEARS ShowBase ATTRIBUTES
    if isShowBaseInst:
       itemDict = item.__dict__
       for a in IDE.ShowBaseAttrs:
           if hasattr(item,a):
              del itemDict[a]
    if type(item) in PythonSequence:
       for i in item:
           removeItem(i)
    elif type(item)==dict and item!=__builtins__:
       for k,v in list(item.items()):
           if k!='DtoolClassDict':
              removeItem(v)
    elif isItGoodToCrush(item):
       if hasattr(item,'__dict__'):
#           if type(item.__dict__)==types.DictProxyType:
#              print id(item),item.__name__#,item.__dict__.keys()
          for k,v in list(item.__dict__.items()):
              if k!='DtoolClassDict':
                 removeItem(v)
       destroyItem(item)
    else:
       destroyItem(item)

def destroyItem(item):
    if item in FrameworkComponents: return
    if debugDynamic:
#        print>>IDE_DEV, '||= '+truncStr(item,70)
       print('||    <ClassName>: '+(type(item) if not hasattr(item,'__class__') else item.__class__).__name__, file=IDE_DEV)
    destroyed=0
    if hasattr(item,'__class__') and hasattr(item.__class__,'__bases__'):
       baseClasses=item.__class__.__bases__
    else:
       baseClasses=None
    if baseClasses:
       if debugDynamic:
          print('||      bases:', end=' ', file=IDE_DEV)
       for b in baseClasses:
           if debugDynamic:
              print(b.__name__+',', end=' ', file=IDE_DEV)
           baseClsName=b.__name__
           if baseClsName in destructors:
              # Actors should be destroyed using cleanup(), or the underlying events hook
              # extension by PauseResume module won't be removed
              if not (baseClsName=='NodePath' and item.__class__.__name__=='Actor'):
                 if destroySpecialClass(baseClsName,item):
                    for d in destructors[baseClsName]:
                        try:
                           getattr(item,d)()
                        except:
                           pass
                 destroyed+=1
       if debugDynamic:
          print()
          if destroyed:
             print('||      (DESTROYED from %i base class(es))'%destroyed, file=IDE_DEV)
    if hasattr(item,'__class__'):
       itemCname=item.__class__.__name__
       if itemCname in destructors:
          if destroySpecialClass(itemCname,item):
             for d in destructors[itemCname]:
                 try:
                    getattr(item,d)()
                 except:
                    pass
          if debugDynamic:
             print('||    (DESTROYED)', file=IDE_DEV)

def destroySpecialClass(classname,item):
    if classname=='NodePath':
       if not item.isEmpty():
          nodeBases=item.node().__class__.__bases__
          # removes lights effects
          if LightNode in nodeBases:
             parent=item.getParent()
             if not parent.isEmpty():
                parent.setLightOff(item)
          # preserves the default cameras
          camExist=False
          for c in (camera, base.cam, base.camera2d, base.cam2d):
              camExist|=item==c
          return not camExist  # returns 1 to destroy the item, 0 to preserve it
    return 1



# YNJH : I don't need the rest of the original Finder.py
#_______________________________________________________________________________
def copyFuncs(fromClass, toClass):
    replaceFuncList = []
    newFuncList = []

    # Copy the functions from fromClass into toClass dictionary
    for funcName, newFunc in list(fromClass.__dict__.items()):
        # Filter out for functions
        if (type(newFunc) == types.FunctionType):
            # See if we already have a function with this name
            oldFunc = toClass.__dict__.get(funcName)
            if oldFunc:
                replaceFuncList.append((oldFunc, funcName, newFunc))
            else:
                newFuncList.append((funcName, newFunc))

    # Look in the messenger, taskMgr, and other globals that store func
    # pointers to see if this old function pointer is stored there, and
    # update it to the new function pointer.
    replaceMessengerFunc(replaceFuncList)
    replaceTaskMgrFunc(replaceFuncList)
    replaceStateFunc(replaceFuncList)
    replaceCRFunc(replaceFuncList)
    replaceAIRFunc(replaceFuncList)
    replaceIvalFunc(replaceFuncList)

    # Now that we've the globals funcs, actually swap the pointers in
    # the new class to the new functions
    for oldFunc, funcName, newFunc in replaceFuncList:
#         print>>IDE_DEV, "REPLACING: ", oldFunc, funcName, newFunc
        setattr(toClass, funcName, newFunc)
    # Add the brand new functions too
    for funcName, newFunc in newFuncList:
#         print>>IDE_DEV, "ADDING: ", oldFunc, funcName, newFunc
        setattr(toClass, funcName, newFunc)

def replaceMessengerFunc(replaceFuncList):
    try:
        messenger
    except:
        return
    for oldFunc, funcName, newFunc in replaceFuncList:
        res = messenger.replaceMethod(oldFunc, newFunc)
#         if res:
#             print>>IDE_DEV, ('replaced %s messenger function(s): %s' % (res, funcName))

def replaceTaskMgrFunc(replaceFuncList):
    try:
        taskMgr
    except:
        return
    for oldFunc, funcName, newFunc in replaceFuncList:
        if taskMgr.replaceMethod(oldFunc, newFunc):
           continue
           print(('replaced taskMgr function: %s' % funcName), file=IDE_DEV)

def replaceStateFunc(replaceFuncList):
    if not sys.modules.get('direct.fsm.State'):
        return
    from direct.fsm.State import State
    for oldFunc, funcName, newFunc in replaceFuncList:
        res = State.replaceMethod(oldFunc, newFunc)
#         if res:
#             print>>IDE_DEV, ('replaced %s FSM transition function(s): %s' % (res, funcName))

def replaceCRFunc(replaceFuncList):
    try:
        base.cr
    except:
        return
    for oldFunc, funcName, newFunc in replaceFuncList:
        if base.cr.replaceMethod(oldFunc, newFunc):
           continue
           print(('replaced DistributedObject function: %s' % funcName), file=IDE_DEV)

def replaceAIRFunc(replaceFuncList):
    try:
        simbase.air
    except:
        return
    for oldFunc, funcName, newFunc in replaceFuncList:
        if simbase.air.replaceMethod(oldFunc, newFunc):
           continue
           print(('replaced DistributedObject function: %s' % funcName), file=IDE_DEV)

def replaceIvalFunc(replaceFuncList):
    # Make sure we have imported IntervalManager and thus created
    # a global ivalMgr.
    if not sys.modules.get('direct.interval.IntervalManager'):
        return
    from direct.interval.FunctionInterval import FunctionInterval
    for oldFunc, funcName, newFunc in replaceFuncList:
        res = FunctionInterval.replaceMethod(oldFunc, newFunc)
#         if res:
#             print>>IDE_DEV, ('replaced %s interval function(s): %s' % (res, funcName))
