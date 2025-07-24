
from panda3d.core import *
from direct.interval.IntervalGlobal import *
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject
import direct.directbase.DirectStart

import PolyButton
import sys


class World(DirectObject):
  def __init__(self):
      # initiates polygonal button system
      PolyButton.setup( parent=render2d, startNow=True )

      # clears aspect2d's OmniBoundingVolume and its children's bounds test blockade,
      # so collision test performance against aspect2d is at its best.
      aspect2d.node().setFinal(0)
      aspect2d.node().clearBounds()

      base.setBackgroundColor(.3,.3,.3,1)
      TextNode.setDefaultFont(loader.loadFont('cmss12'))
      self.accept('escape',self.exit)

      # TITLE
      NodePath(OnscreenText('EXIT CONFIRMATION DIALOG :\n[ Y ] : YES\n[ C ], [ ESC ] : CANCEL\n[ N ] : NO\n',
          scale=.045, fg=(1,1,1,1), align=TextNode.ARight)
          ).setPos(render2d,.97,0,.8)

      OnscreenText('pretending that we edited something,\npress ESC to exit.\ntry holding down the test button while pressing ESC,\nand see what will happen',
          pos=(0,-.75), scale=.045, fg=(1,1,1,1))

      # 3D TEST BUTTONS
      self.createButtonOf3Dmodel('frowney','',pos=(-.45,0,.2))
      self.createButtonOf3Dmodel('smiley','',pos=(0,0,.3),hitKey='enter')
      self.createButtonOf3Dmodel('frowney','',pos=(.45,0,.2))

      self.clickedCount=[]
      # 2D TEST BUTTONS
      for t in range(-1,2):
          np=loader.loadModel('but.egg')
          np.reparentTo(aspect2d)
          np.setTransparency(1)
          np.setAlphaScale(.8)
          np.find('**/back').removeNode()
          txt='TEST BUTTONS\n'
          testText=OnscreenText(parent=np,text=txt, pos=(0,0), scale=.08, fg=(1,1,1,1),mayChange=1)
          idx=t+2
          if abs(t):
             i=len(self.clickedCount)
             self.clickedCount+=[0,0,0]
             buttons = (
                PolyButton.myButton(np, 'y', ('hover','pressed','disabled'),
                   command=( Functor(self.incCount,i),
                             Functor(self.updateTestText, testText,txt+'YES %i clicked\n' %idx,i) )),
                PolyButton.myButton(np, 'c', ('hover','pressed','disabled'),
                   command=( Functor(self.incCount,i+1),
                             Functor(self.updateTestText, testText,txt+'CANCEL %i clicked\n' %idx,i+1) )),
                PolyButton.myButton(np, 'n', ('hover','pressed','disabled'),
                   command=( Functor(self.incCount,i+2),
                             Functor(self.updateTestText, testText,txt+'NO %i clicked\n' %idx,i+2) )),
                )
          else:
             cBtn = PolyButton.myButton(np, 'c', ('hover','pressed','disabled'),
                command=Functor(testText.setText,txt+'CANCEL %i clicked' %idx),appearEnabled=0)
             yBtn = PolyButton.myButton(np, 'y', ('hover','pressed','disabled'),
                command=(cBtn.enable,Functor(testText.setText,txt+'CANCEL button %i ENABLED' %idx)))
             nBtn = PolyButton.myButton(np, 'n', ('hover','pressed','disabled'),
                command=(cBtn.disable,Functor(testText.setText,txt+'CANCEL button %i DISABLED' %idx)))
             buttons = (cBtn,yBtn,nBtn)

          PolyButton.myDialog(
             root = np,
             pos = (t*.8,0,-.3),
             scale = .55,
             keyboard = False,
             buttons = buttons )

  def createButtonOf3Dmodel(self,model,geom,pos=(0,0,0),hitKey=None):
      np=loader.loadModel(model)
      np.setDepthWrite(1); np.setDepthTest(1); np.setTwoSided(0)
      np.reparentTo(aspect2d)
      np.setScale(.2)
      np.setPos(*pos)
      g=np.find('**/'+geom)
      g.setSz(g,.3)
      # background
      bg=loader.loadModel('smiley')
      bg.reparentTo(g,-1)
      bg.setY(2)
      bg.setScale(1.12)
      bg.setTextureOff(1)
      bg.setColor(1,0,0,.8)
      bg.setAlphaScale(0)
      bg.setTransparency(1)
      bgBlink=Sequence(
         bg.colorScaleInterval(.2,Vec4(1)),
         bg.colorScaleInterval(.2,Vec4(1,1,1,0))
         )
      OnscreenText("I'm a button,\nclick me !", pos=(pos[0],pos[2]+.25), scale=.045, fg=(1,1,1,1))
      PolyButton.myButton(np, geom, hitKey=hitKey,
         command=self.rollMe, arg=g,
         # let the background blinks when the button is hilighted
         hoverFunc=bgBlink.loop, offFunc=bgBlink.finish,
         )

  def rollMe(self,np):
      np.hprInterval(.7,Vec3(0,0,np.getR()+360)).start()

  def incCount(self,idx):
      self.clickedCount[idx]+=1

  def updateTestText(self,OST,text,i):
      if self.clickedCount[i]>1:
         OST.setText(text+str(self.clickedCount[i])+' times')
      else:
         OST.setText(text+str(self.clickedCount[i])+' time')

# THIS IS AN EXIT FUNCTION WITH 1 DIALOG
#   def exit(self):
#       self.exitConfirmation=loader.loadModel('but')
#       self.exitConfirmation.setTransparency(1)
#       self.exitConfirmation.setAlphaScale(.8)
#       self.BTlastPrefix=PolyButton.getBTprefix()
#       PolyButton.setBTprefix('dialogInFocus-')
#       self.exitDialog = PolyButton.myDialog(
#           root = self.exitConfirmation,
#           pos = (0,0,1.5),
#           scale = .8,
#           buttons = (
#              PolyButton.myButton(self.exitConfirmation, 'y', ('hover','pressed','disabled'),
#                 hitKey='y', command=self.exitSaveChangesYes, stayAlive=0),
#              # if you want to have a default in-focus button for your dialog,
#              # pack it in a sequence like this :
#              [PolyButton.myButton(self.exitConfirmation, 'c', ('hover','pressed','disabled'),
#                 hitKey=('c','escape'), command=self.exitSaveChangesCancel, stayAlive=0)],
#              PolyButton.myButton(self.exitConfirmation, 'n', ('hover','pressed','disabled'),
#                 hitKey='n', command=self.exitSaveChangesNo, stayAlive=0),
#                     )  # y, c, n are geom's name, will be searched under root node
#           )
#       # slide the dialog onto screen, and then enable it's buttons shortcut keys
#       Sequence(
#           Func(self.exitDialog.disableDialogButtons),
#           self.exitConfirmation.posInterval(.5,Point3(0,0,1),blendType='easeOut'),
#           Func(self.exitDialog.enableDialogButtons),
#           Func(self.exitDialog.setDialogKeysActive)
#       ).start()

  # THIS IS AN EXIT FUNCTION WITH 2 "DIALOG", but actually 1
  def exit(self):
      self.exitConfirmation=aspect2d.attachNewNode('exitConfirm')
      self.exitConfirmation.setTransparency(1)
      self.exitConfirmation.setAlphaScale(.8)
      dialog1=loader.loadModel('but')
      dialog1.reparentTo(self.exitConfirmation)
      dialog1.setX(-.75)
      dialog2=loader.loadModel('but')
      dialog2.reparentTo(self.exitConfirmation)
      dialog2.setX(.75)
      self.BTlastPrefix=PolyButton.getBTprefix()
      PolyButton.setBTprefix('dialogInFocus-')
      self.exitDialog = PolyButton.myDialog(
          root = self.exitConfirmation,
          pos = (0,0,1.5),
          scale = .8,
          buttons = (
             PolyButton.myButton(dialog1, 'y', ('hover','pressed','disabled'),
                hitKey='y', command=self.exitSaveChangesYes, stayAlive=0),
             # if you want to have a default in-focus button for your dialog,
             # pack it in a sequence like this :
             [PolyButton.myButton(dialog1, 'c', ('hover','pressed','disabled'),
                hitKey=('c','escape'), command=self.exitSaveChangesCancel, stayAlive=0)],
             PolyButton.myButton(dialog1, 'n', ('hover','pressed','disabled'),
                hitKey='n', command=self.exitSaveChangesNo, stayAlive=0),

             PolyButton.myButton(dialog2, 'y', ('hover','pressed','disabled'),
                command=self.exitSaveChangesYes, stayAlive=0),
             PolyButton.myButton(dialog2, 'c', ('hover','pressed','disabled'),
                command=self.exitSaveChangesCancel, stayAlive=0),
             PolyButton.myButton(dialog2, 'n', ('hover','pressed','disabled'),
                command=self.exitSaveChangesNo, stayAlive=0),
             )  # y, c, n are geom's name, will be searched under root node
          )
      # disable dialog's buttons, slide the dialog onto screen,
      # and then enable it's buttons
      Sequence(
          Func(self.exitDialog.disableDialogButtons),
          self.exitConfirmation.posInterval(.5,Point3(0,0,1),blendType='easeOut'),
          Func(self.exitDialog.enableDialogButtons),
          Func(self.exitDialog.setDialogKeysActive)
      ).start()

  def exitSaveChangesYes(self):
      print( '\n<YES YES YES>\n')
      self.exitSaveChangesCleanup()
      OnscreenText('changes saved\nexiting...',fg=(1,1,1,1),shadow=(0,0,0,1))
      taskMgr.doMethodLater(2,sys.exit,'exiting')
      self.ignoreAll()

  def exitSaveChangesCancel(self):
      print( '\n<CANCEL CANCEL CANCEL>\n')
      self.exitSaveChangesCleanup()

  def exitSaveChangesNo(self):
      print( '\n<NO NO NO>\n')
      self.exitSaveChangesCleanup()
      OnscreenText('changes NOT saved\nexiting...',fg=(1,1,1,1),shadow=(0,0,0,1))
      taskMgr.doMethodLater(2,sys.exit,'exiting')
      self.ignoreAll()

  def exitSaveChangesCleanup(self):
      Sequence(
          # disable dialog buttons' events and shortcut keys
          Func(self.exitDialog.disableDialogButtons),
          # slide it back off screen
          self.exitConfirmation.posInterval(.5,Point3(0,0,1.5)),
          # destroy it
          Func(self.exitDialog.cleanup),
          # restore the last button thrower prefix
          Func(PolyButton.setBTprefix,self.BTlastPrefix),
          # reset CollisionHandlerEvent
          Func(PolyButton.reset)
      ).start()


World()
run()
