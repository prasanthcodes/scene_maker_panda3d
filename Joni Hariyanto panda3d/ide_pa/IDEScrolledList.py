__all__=['ScrolledList']

from pandac.PandaModules import *
from direct.showbase.DirectObject import DirectObject
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectFrame,DirectButton,DirectLabel,DirectScrolledFrame,DGG
from direct.interval.IntervalGlobal import Sequence
from direct.task import Task
from direct.showbase.PythonUtil import clampScalar
from types import IntType,ListType,TupleType
import sys

atLeast16=PandaSystem.getMajorVersion()*10+PandaSystem.getMinorVersion()>=16
asList=lambda nc: list(nc) if atLeast16 else nc.asList()


class ScrolledList(DirectObject):
  """
     A class to display a list of selectable items.
     It is displayed using scrollable window (DirectScrolledFrame).
  """
  def __init__(self, parent=None, frameSize=(.8,1.2),
               frameColor=(0,0,0,.75),
               font=None, itemScale=.045, itemTextScale=1, itemTextZ=0,
               vertScrollPos=0,
               thumbWidth=.03,
               thumbMinHeight=.05,
               command=None,
               clickCommand=None,
               contextMenu=None, autoFocus=0, optimize=1,
               colorChange=1, colorChangeDuration=1.0, newItemColor=(0,1,0,1),
               rolloverColor=Vec4(1,.8,.2,.8),
               suppressMouseWheel=1, modifier='control',BTnode=None):
      if BTnode is None:
         self.BTnode=base.buttonThrowers[0].node()
      else:
         self.BTnode=BTnode
      self.focusButton=None
      self.command=command
      self.clickCommand=clickCommand
      self.contextMenu=contextMenu
      self.autoFocus=autoFocus
      self.optimize=optimize
      self.colorChange=colorChange
      self.colorChangeDuration=colorChangeDuration*.5
      self.newItemColor=Vec4(*newItemColor)
      self.rolloverColor=Vec4(*rolloverColor) if type(rolloverColor) in (list,tuple) else rolloverColor
      self.rightClickTextColors=(Vec4(0,1,0,1),Vec4(0,35,100,1))
      self.font=font
      if font:
         self.fontHeight=font.getLineHeight()
      else:
         self.fontHeight=TextNode.getDefaultFont().getLineHeight()
      self.fontHeight*=1.2 # let's enlarge font height a little
      self.xtraSideSpace=.2*self.fontHeight
      self.itemTextScale=itemTextScale
      self.itemTextZ=itemTextZ
      self.suppressMouseWheel=suppressMouseWheel
      self.modifier=modifier
      self.buttonsList=[]
      self.selectable=1
      self.numItems=0
      self.canvasLen=0
      self.canvasRatio=1
      self.__eventReceivers={}
      # DirectScrolledFrame to hold items
      self.itemScale=itemScale
      self.itemVertSpacing=self.fontHeight*self.itemScale
      self.frameWidth,self.frameHeight=frameSize
      # I set canvas' Z size smaller than the frame to avoid the auto-generated vertical slider bar
      self.Frame = DirectScrolledFrame(
                   parent=parent,pos=(-self.frameWidth*.5,0,.5*self.frameHeight), relief=DGG.GROOVE,
                   state=DGG.NORMAL, # to create a mouse watcher region
                   frameSize=(0, self.frameWidth, -self.frameHeight, 0), frameColor=frameColor,
                   canvasSize=(0, 0, -self.frameHeight*.5, 0), borderWidth=(0.008,0.008),
                   manageScrollBars=0, enableEdit=0, suppressMouse=0, sortOrder=1100 )
      # I don't want its default sliders
      self.Frame.findAllMatches('**/DirectScrollBar*').detach()
      # force the ScissorEffect for not spending some frame's space to the slider
      self.Frame['canvasSize']=(0,)*4
      self.Frame.bind(DGG.B1PRESS,self.__setFocusButton)
      self.thumbWidth=thumbWidth
      self.thumbHalfWidth=thumbWidth*.5
      self.thumbBorder=thumbWidth*.25
      self.thumbMinHeight=thumbMinHeight
      if frameColor[3]==0: # alpha == 0
         border=LineSegs('border')
         border.setThickness(3)
         border.setColor(*frameColor[:3])
#          border.setColor(1,0,0)
         t=self.thumbBorder
         vtx=(
           (0,0,-t),
           (1-t,0,-t),
           (1-t,0,-1+t),
           (0,0,-1+t),
         )
         border.moveTo(*vtx[0])
         for i in range(3):
             border.drawTo(*vtx[i+1])
         border.drawTo(*vtx[0])
         # fills the corners
         for i in range(4):
             border.moveTo(*vtx[i])
         self.border=self.Frame.attachNewNode(border.create(),sort=-10)
         self.border.setScale(self.frameWidth,1,self.frameHeight)
      else:
         self.border=None
      # the real canvas is "self.Frame.getCanvas()",
      # but if the frame is hidden since the beginning,
      # no matter how I set the canvas Z pos, the transform would be resistant,
      # so just create a new node under the canvas to be my canvas
      self.canvas=self.Frame.getCanvas().attachNewNode('myCanvas')
      # slider background
      BGhalfWidth=self.thumbWidth*1.25*.5
      if vertScrollPos==0:
         x=-BGhalfWidth
      else:
         x=self.frameWidth+BGhalfWidth
      self.SliderBG = DirectFrame( parent=self.Frame, frameColor=(0,0,0,.7),
           frameSize=(-BGhalfWidth,BGhalfWidth,-self.frameHeight,0),
           pos=(x,0,0),enableEdit=0, suppressMouse=0)
      # slider thumb track
      self.sliderTrack = DirectFrame( parent=self.SliderBG, relief=DGG.FLAT, #state=DGG.NORMAL,
           frameSize=(-self.thumbHalfWidth,self.thumbHalfWidth,-self.frameHeight+self.thumbBorder,-self.thumbBorder),
           frameColor=(1,1,1,.2), enableEdit=0, suppressMouse=0)
      # page up
      self.pageUpRegion=DirectFrame( parent=self.SliderBG, relief=DGG.FLAT, state=DGG.NORMAL,
           frameColor=(1,.8,.2,.1), frameSize=(-self.thumbHalfWidth,self.thumbHalfWidth,0,0),
           enableEdit=0, suppressMouse=0)
      self.pageUpRegion.setAlphaScale(0)
      self.pageUpRegion.bind(DGG.B1PRESS,self.__startScrollPage,[-1])
      self.pageUpRegion.bind(DGG.WITHIN,self.__continueScrollUp)
      self.pageUpRegion.bind(DGG.WITHOUT,self.__suspendScrollUp)
      # page down
      self.pageDnRegion=DirectFrame( parent=self.SliderBG, relief=DGG.FLAT, state=DGG.NORMAL,
           frameColor=(1,.8,.2,.1), frameSize=(-self.thumbHalfWidth,self.thumbHalfWidth,0,0),
           enableEdit=0, suppressMouse=0)
      self.pageDnRegion.setAlphaScale(0)
      self.pageDnRegion.bind(DGG.B1PRESS,self.__startScrollPage,[1])
      self.pageDnRegion.bind(DGG.WITHIN,self.__continueScrollDn)
      self.pageDnRegion.bind(DGG.WITHOUT,self.__suspendScrollDn)
      self.pageUpDnSuspended=[0,0]
      # slider thumb
      self.vertSliderThumb=DirectButton(parent=self.SliderBG, relief=DGG.FLAT,
           frameColor=(1,1,1,.6), frameSize=(-self.thumbHalfWidth,self.thumbHalfWidth,0,0),
           rolloverSound=0,clickSound=0,enableEdit=0, suppressMouse=0)
      self.vertSliderThumb.bind(DGG.B1PRESS,self.__startdragSliderThumb)
      self.vertSliderThumb.bind(DGG.WITHIN,self.__enteringThumb)
      self.vertSliderThumb.bind(DGG.WITHOUT,self.__exitingThumb)
      self.oldPrefix=self.BTnode.getPrefix()
      self.sliderThumbDragPrefix='draggingSliderThumb_%s-'%id(self)
      # highlight
      CM=CardMaker('highlight')
      CM.setFrame(0,100,-1,0)
      self.hilight=self.canvas.attachNewNode(CM.generate())
      self.hilight.hide()
      # display
      self.display=NodePath('')
      self.accept(DGG.WITHIN+self.Frame.guiId,self.__enteringFrame)
      self.accept(DGG.WITHOUT+self.Frame.guiId,self.__exitingFrame)
      self.mouseOutInRegionCommand=(self.__exitingFrame,self.__enteringFrame)
      self.dragSliderThumbTaskName='dragSliderThumb_%s'%id(self)

  def __startdragSliderThumb(self,m=None):
      mpos=base.mouseWatcherNode.getMouse()
      parentZ=self.vertSliderThumb.getParent().getZ(render2d)
      sliderDragTask=taskMgr.add(self.__dragSliderThumb,self.dragSliderThumbTaskName)
      sliderDragTask.ZposNoffset=mpos[1]-self.vertSliderThumb.getZ(render2d)+parentZ
#       sliderDragTask.mouseX=base.winList[0].getPointer(0).getX()
      self.oldPrefix=self.BTnode.getPrefix()
      self.BTnode.setPrefix(self.sliderThumbDragPrefix)
      self.acceptOnce(self.sliderThumbDragPrefix+'mouse1-up',self.__stopdragSliderThumb)

  def __dragSliderThumb(self,t):
      if not base.mouseWatcherNode.hasMouse():
         return
      mpos=base.mouseWatcherNode.getMouse()
#       newY=base.winList[0].getPointer(0).getY()
      self.__updateCanvasZpos((t.ZposNoffset-mpos[1])/(self.canvasRatio*self.Frame.getSz()))
#       base.winList[0].movePointer(0, t.mouseX, newY)
      return Task.cont

  def __stopdragSliderThumb(self,m=None):
      taskMgr.remove(self.dragSliderThumbTaskName)
      self.__stopScrollPage()
      self.BTnode.setPrefix(self.oldPrefix)

  def __startScrollPage(self,dir,m):
      self.oldPrefix=self.BTnode.getPrefix()
      self.BTnode.setPrefix(self.sliderThumbDragPrefix)
      self.acceptOnce(self.sliderThumbDragPrefix+'mouse1-up',self.__stopdragSliderThumb)
      t=taskMgr.add(self.__scrollPage,'scrollPage',extraArgs=[int((dir+1)*.5),dir*.01/self.canvasRatio])
      self.pageUpDnSuspended=[0,0]

  def __scrollPage(self,dir,scroll):
      if not self.pageUpDnSuspended[dir]:
         self.scrollCanvas(scroll)
      return Task.cont

  def __stopScrollPage(self,m=None):
      taskMgr.remove('scrollPage')

  def __suspendScrollUp(self,m=None):
      self.pageUpRegion.setAlphaScale(0)
      self.pageUpDnSuspended[0]=1
  def __continueScrollUp(self,m=None):
      if taskMgr.hasTaskNamed(self.dragSliderThumbTaskName):
         return
      self.pageUpRegion.setAlphaScale(1)
      self.pageUpDnSuspended[0]=0

  def __suspendScrollDn(self,m=None):
      self.pageDnRegion.setAlphaScale(0)
      self.pageUpDnSuspended[1]=1
  def __continueScrollDn(self,m=None):
      if taskMgr.hasTaskNamed(self.dragSliderThumbTaskName):
         return
      self.pageDnRegion.setAlphaScale(1)
      self.pageUpDnSuspended[1]=0

  def __suspendScrollPage(self,m=None):
      self.__suspendScrollUp()
      self.__suspendScrollDn()

  def __enteringThumb(self,m=None):
      self.vertSliderThumb['frameColor']=(1,1,1,1)
      self.__suspendScrollPage()

  def __exitingThumb(self,m=None):
      self.vertSliderThumb['frameColor']=(1,1,1,.6)

  def scrollCanvas(self,scroll):
      if self.vertSliderThumb.isHidden():
         return
      self.__updateCanvasZpos(self.canvas.getZ()+scroll)

  def __updateCanvasZpos(self,Zpos):
      newZ=clampScalar(Zpos, .0, self.canvasLen-self.frameHeight+.015)
      if newZ!=Zpos:
         newZ=round(newZ,2)
      self.canvas.setZ(newZ)
      thumbZ=-newZ*self.canvasRatio
      self.vertSliderThumb.setZ(thumbZ)
      self.pageUpRegion['frameSize']=(-self.thumbHalfWidth,self.thumbHalfWidth,thumbZ-self.thumbBorder,-self.thumbBorder)
      self.pageDnRegion['frameSize']=(-self.thumbHalfWidth,self.thumbHalfWidth,-self.frameHeight+self.thumbBorder,thumbZ+self.vertSliderThumb['frameSize'][2])
      if not self.optimize or self.display.isEmpty() or self.display.getNumChildren()==0:
         return
      # strips all offscreen lines, to speed up text rendering,
      # since Panda doesn't have to traverse all text lines just to decide
      # which lines should be rendered.
      # I know which ones must be rendered, so attach only those visible lines
      canvasZ=self.canvas.getZ()
      renderStartLine=int(canvasZ/self.itemVertSpacing)
      renderEndLine=int((canvasZ+self.frameHeight)/self.itemVertSpacing)
#       print renderStartLine,renderEndLine
      texts=self.display.getChildren()
      texts.removePath(self.hilight) # keeps the highlighter
      texts.stash() # strips them off
      for l in self.displayChildren[renderStartLine:min(renderEndLine+1,self.numItems)]:
          l.unstash()
          if l.getNumChildren()>1:
             selected=self.displayChildren.index(l)==self.focusButton
             if selected:
                oldCS=l.getColorScale()
             l.flattenStrong()
             if selected:
                l.setColorScale(oldCS)


  def __adjustCanvasLength(self,numItem):
      self.canvasLen=float(numItem)*self.itemVertSpacing
      canvasRatio=(self.frameHeight-.015)/(self.canvasLen+self.thumbBorder)
      scaledFrameHeight=self.frameHeight*canvasRatio
      thumbSizeDiff=max(scaledFrameHeight,self.thumbMinHeight)-scaledFrameHeight
      self.canvasRatio=canvasRatio-thumbSizeDiff/(self.canvasLen+self.thumbBorder)
      if self.canvasLen<=self.frameHeight-.015:
         canvasZ=.0
         self.vertSliderThumb.hide()
         self.pageUpRegion.hide()
         self.pageDnRegion.hide()
         self.canvasLen=self.frameHeight-.015
      else:
         canvasZ=self.canvas.getZ()
         self.vertSliderThumb.show()
         self.pageUpRegion.show()
         self.pageDnRegion.show()
      self.__updateCanvasZpos(canvasZ)
      self.vertSliderThumb['frameSize']=(-self.thumbHalfWidth,self.thumbHalfWidth,-max(scaledFrameHeight,self.thumbMinHeight),-self.thumbBorder)
      thumbZ=self.vertSliderThumb.getZ()
      self.pageUpRegion['frameSize']=(-self.thumbHalfWidth,self.thumbHalfWidth,thumbZ-self.thumbBorder,-self.thumbBorder)
      self.pageDnRegion['frameSize']=(-self.thumbHalfWidth,self.thumbHalfWidth,-self.frameHeight+self.thumbBorder,thumbZ+self.vertSliderThumb['frameSize'][2])

  def __acceptAndIgnoreWorldEvent(self,event,command,extraArgs=[]):
      receivers=messenger.whoAccepts(event)
      if receivers is None:
         self.__eventReceivers[event]={}
      else:
         newD={}
         for r in receivers:
             newr=messenger._getObject(r) if type(r)==tuple else r
             newD[newr]=receivers[r]
         self.__eventReceivers[event]=newD
      for r in list(self.__eventReceivers[event].keys()):
          r.ignore(event)
      self.accept(event,command,extraArgs)

  def __ignoreAndReAcceptWorldEvent(self,events):
      for event in events:
          self.ignore(event)
          if event in self.__eventReceivers:
             for r, method_xtraArgs_persist in list(self.__eventReceivers[event].items()):
                 messenger.accept(event,r,*method_xtraArgs_persist)
          self.__eventReceivers[event]={}

  def __enteringFrame(self,m=None):
      # sometimes the WITHOUT event for page down region doesn't fired,
      # so directly suspend the page scrolling here
      self.__suspendScrollPage()
      BTprefix=self.BTnode.getPrefix()
      if BTprefix==self.sliderThumbDragPrefix:
         return
      self.inOutBTprefix=BTprefix
      if self.suppressMouseWheel:
         self.__acceptAndIgnoreWorldEvent(self.inOutBTprefix+'wheel_up',
              command=self.scrollCanvas, extraArgs=[-.07])
         self.__acceptAndIgnoreWorldEvent(self.inOutBTprefix+'wheel_down',
              command=self.scrollCanvas, extraArgs=[.07])
      else:
         self.accept(self.inOutBTprefix+self.modifier+'-wheel_up',self.scrollCanvas, [-.07])
         self.accept(self.inOutBTprefix+self.modifier+'-wheel_down',self.scrollCanvas, [.07])
#       print 'enteringFrame'

  def __exitingFrame(self,m=None):
      if not hasattr(self,'inOutBTprefix'):
         return
      if self.suppressMouseWheel:
         self.__ignoreAndReAcceptWorldEvent( (
                                             self.inOutBTprefix+'wheel_up',
                                             self.inOutBTprefix+'wheel_down',
                                             ) )
      else:
         self.ignore(self.inOutBTprefix+self.modifier+'-wheel_up')
         self.ignore(self.inOutBTprefix+self.modifier+'-wheel_down')
#       print 'exitingFrame'

  def __setFocusButton(self,mwp):
      if not (self.selectable and len(self.buttonsList)):
         return
      mpos=mwp.getMouse()
      i=-int( self.canvas.getRelativePoint(render2d,Point3(mpos[0],0,mpos[1]))[2]/self.itemVertSpacing )
      i=clampScalar(0,self.numItems-1,i)
      if self.focusButton!=None:
         if self.focusButton==i: # double clicked
            if callable(self.command):
               # run user command and pass the selected item
               self.command(self.buttonsList[self.focusButton])
            return
      self.clearHighlight()
      self.focusButton=i
      self.highlightItem(self.focusButton,focus=0)
      if callable(self.clickCommand):
         self.clickCommand()

  def __rightPressed(self,button,m):
      self.__isRightIn=True
#       text0 : normal
#       text1 : pressed
#       text2 : rollover
#       text3 : disabled
      button._DirectGuiBase__componentInfo['text2'][0].setColorScale(self.rightClickTextColors[self.focusButton==button])
      button.bind(DGG.B3RELEASE,self.__rightReleased,[button])
      button.bind(DGG.WITHIN,self.__rightIn,[button])
      button.bind(DGG.WITHOUT,self.__rightOut,[button])

  def __rightIn(self,button,m):
      self.__isRightIn=True
      button._DirectGuiBase__componentInfo['text2'][0].setColorScale(self.rightClickTextColors[self.focusButton==button])
  def __rightOut(self,button,m):
      self.__isRightIn=False
      button._DirectGuiBase__componentInfo['text2'][0].setColorScale(Vec4(1,1,1,1))

  def __rightReleased(self,button,m):
      button.unbind(DGG.B3RELEASE)
      button.unbind(DGG.WITHIN)
      button.unbind(DGG.WITHOUT)
      button._DirectGuiBase__componentInfo['text2'][0].setColorScale(self.rolloverColor)
      if not self.__isRightIn:
         return
      if callable(self.contextMenu):
         # run user command and pass the selected item, it's index, and the button
         self.contextMenu(button['extraArgs'][1],self.buttonsList.index(button),button)

  def clear(self,retainDisplay=0):
      """
         clear the list
      """
      if not retainDisplay:
         self.display.removeNode()
      self.buttonsList=[]
      self.focusButton=None
      self.numItems=0
      self.hilight.hide()
      self.__adjustCanvasLength(self.numItems)

  def getSelectionIndex(self):
      return self.focusButton

  def getSelectedItem(self):
      if self.focusButton==None:
         return None
      return self.buttonsList[self.focusButton]
#       return self.focusButton.extraArgs[1]

  def setDisplay(self,display,scale=None,vertSpacing=1,baseline2top=0,selectable=1):
      if scale!=None:
         if display!=None:
            self.display.removeNode()
            self.display=display
            self.display.reparentTo(self.canvas,sort=10)
            self.display.setScale(scale)
            self.display.setZ(-scale[2]*baseline2top)
            self.display.setColor(self.rolloverColor)
            self.displayChildren=asList(self.display.getChildren())
            self.hilight.setScale(scale[0],1,scale[2]*vertSpacing)
            self.hilight.setColor(self.rolloverColor)
         self.itemVertSpacing=scale[2]*vertSpacing
      else:
         self.itemVertSpacing=vertSpacing
      self.hilight.hide()
      self.selectable=selectable

  def setRolloverColor(self,col):
      self.rolloverColor=col
      self.hilight.setColor(col)
      if not self.display.isEmpty():
         self.display.setColor(col)

  def getItems(self):
      return self.buttonsList

  def setItems(self,textArray):
      """
         add item to the list
         text : text which will be passed to user command(s)
      """
      self.buttonsList=textArray
#       button.setPos(.02,0,Zpos)
      self.numItems=len(self.buttonsList)
      self.__adjustCanvasLength(self.numItems)

  def clearHighlight(self):
      self.hilight.hide()
      self.displayChildren[self.focusButton].clearColorScale()

  def highlightItem(self,idx,focus=1):
      lastidx=self.focusButton
      if len(self.buttonsList):
         if self.focusButton!=None:
            self.displayChildren[self.focusButton].clearColorScale()
         idx=clampScalar(0,self.numItems-1,idx)
         self.focusButton=idx
         self.hilight.setPos(0,0,-idx*self.itemVertSpacing)
         self.hilight.show()
         self.displayChildren[idx].setColorScale(0,0,0,1)
         if focus:
            self.focusViewOnItem(idx)
      return lastidx!=self.focusButton

  def highlightFirstItem(self,focus=1):
      self.highlightItem(0,focus)

  def highlightLastItem(self,focus=1):
      self.highlightItem(self.numItems-1,focus)

  def highlightNextItem(self,inc=1):
      if not len(self.buttonsList):
         return
      lastidx=self.focusButton
      if self.focusButton==None:
         self.focusButton=0
         self.highlightItem(0)
      else:
         self.displayChildren[self.focusButton].clearColorScale()
         self.focusButton=min(self.focusButton+inc,self.numItems-1)
         self.highlightItem(self.focusButton)
      return lastidx!=self.focusButton

  def highlightPrevItem(self,inc=1):
      if not len(self.buttonsList):
         return
      lastidx=self.focusButton
      if self.focusButton==None:
         self.focusButton=self.numItems-1
         self.highlightItem(self.numItems-1)
      else:
         self.displayChildren[self.focusButton].clearColorScale()
         self.focusButton=max(0,self.focusButton-inc)
         self.highlightItem(self.focusButton)
      return lastidx!=self.focusButton

  def setFrameSize(self,l,r,b,t):
      self.frameWidth,self.frameHeight=r-l,t-b
      self.Frame['frameSize']=(l,r,b,t)
      self.SliderBG['frameSize']=self.SliderBG['frameSize'][:2]+(b,0)
      self.sliderTrack['frameSize']=self.sliderTrack['frameSize'][:2]+(b+self.thumbBorder,-self.thumbBorder)
      if self.border:
         self.border.setScale(r,1,-b)
      self.__adjustCanvasLength(self.numItems)

  def focusViewOnItem(self,idx):
      """
         Scroll the window so the newly added item will be displayed
         in the middle of the window, if possible.
      """
      Zpos=(idx+.7)*self.itemVertSpacing-self.frameHeight*.5
      self.__updateCanvasZpos(Zpos)

  def setAutoFocus(self,b):
      """
         set auto-view-focus state of newly added item
      """
      self.autoFocus=b

  def index(self,button):
      """
         get the index of button
      """
      if not button in self.buttonsList:
         return None
      return self.buttonsList.index(button)

  def getNumItems(self):
      """
         get the current number of items on the list
      """
      return self.numItems

  def disableItem(self,i):
      if not 0<=i<self.numItems:
         print('DISABLING : invalid index (%s)' %i)
         return
      self.buttonsList[i]['state']=DGG.DISABLED
      self.buttonsList[i].setColorScale(.3,.3,.3,1)

  def enableItem(self,i):
      if not 0<=i<self.numItems:
         print('ENABLING : invalid index (%s)' %i)
         return
      self.buttonsList[i]['state']=DGG.NORMAL
      self.buttonsList[i].setColorScale(1,1,1,1)

  def removeItem(self,index):
      if not 0<=index<self.numItems:
         print('REMOVAL : invalid index (%s)' %index)
         return
      if self.numItems==0: return
      if self.focusButton==self.buttonsList[index]:
         self.focusButton=None
      self.buttonsList[index].removeNode()
      del self.buttonsList[index]
      self.numItems-=1
      for i in range(index,self.numItems):
          self.buttonsList[i].setZ(self.buttonsList[i],self.fontHeight)
      self.__adjustCanvasLength(self.numItems)

  def destroy(self):
      self.clear()
      self.__exitingFrame()
      self.ignoreAll()
      self.Frame.removeNode()

  def hide(self):
      self.Frame.hide()
      self.__exitingFrame()

  def show(self):
      self.Frame.show()

  def toggleVisibility(self):
      if self.Frame.isHidden():
         self.show()
      else:
         self.hide()

  def isHidden(self):
      return self.Frame.isHidden()
