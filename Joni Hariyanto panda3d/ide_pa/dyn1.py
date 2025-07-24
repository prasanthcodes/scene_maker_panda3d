from pandac.PandaModules import *
loadPrcFileData('','''
show-frame-rate-meter 0
# win-size 640 480
# win-size 1024 768
# fullscreen 1
''')

from direct.showbase.DirectObject import DirectObject
from direct.interval.IntervalGlobal import *
from direct.directutil.Mopath import Mopath
from direct.actor.Actor import Actor
from direct.gui.DirectGui import *
from direct.task import Task
import direct.directbase.DirectStart

# If you don't use model cache, and the models/textures loading time is longer than
# any scheduled stuff (e.g. jacks' color change doLater task or wait interval),
# and there are some clock ticks before run() (e.g. a render frame call
# for the green panda's RTT text), these stuff would be ran too early,
# since the frame time would be adjusted incorrectly.
globalClock.setMode(ClockObject.MSlave)

from smileyClass import Smiley
from jackClass import Jack
from pandaClass import Panda
from brokenClass import BrokenClass

import PauseResume as PR
import os, sys, random


# unstoppable stuff name prefix
unstoppable_namePrefix='unstoppable-'

# you'll always get this model upon update
m=loader.loadModel('jack')
m.reparentTo(render)
m.setScale(.5,.5,5)
m.setH(180)

def shakeMe(t):
    r=.75
    m.setPos(m,random.uniform(-1,1)*r,random.uniform(-1,1)*r,0)
#     print 'shakeMe'
    return Task.cont

BTprefix='other: '
myBTnode=ButtonThrower('my custom button thrower')
myBTnode.setPrefix(BTprefix)
myBTnodePath=base.buttonThrowers[0].getParent().attachNewNode(myBTnode)

# base.buttonThrowers[0].node().setModifierButtons(ModifierButtons(''))

DO=DirectObject()
DO.accept(BTprefix+'x',sys.exit)
taskMgr.add(shakeMe,'shakeMe')


useSoftwareMousePointer=1

if useSoftwareMousePointer:
   CBM=CullBinManager.getGlobalPtr()
   CBM.addBin('mouse cursor',CullBinEnums.BTUnsorted,100)
   pointerNode=loader.loadModel('misc/Spotlight')
   pointerNode.reparentTo(aspect2d)
   pointerNode.setHpr(90,-135,0)
   pointerNode.setScale(.012)
   pointerNode.wrtReparentTo(render2d)
   pointerNode.flattenStrong()
   pointerNode.setColor(0,0,0,1)
   pointerNode.setBin('mouse cursor',0)
   base.mouseWatcherNode.setGeometry(pointerNode.node())
   props=WindowProperties()
   props.setCursorHidden(1)
   base.win.requestProperties(props)


class World(DirectObject):
  def __init__(self):
#       camera.clearTransform() # force reset camera
      if camera.getPos()==Point3(0): # don't reset camera position on every update
         camera.setPos(10.00, -40.00, 15.00)
         camera.setHpr(18.43, -21.57, 0.00)
         mat=Mat4(camera.getMat())
         mat.invertInPlace()
         base.mouseInterfaceNode.setMat(mat)
      self.accept(BTprefix+'escape',sys.exit)
      self.accept('space',self.toggleSceneActive)
      self.accept('enter',self.printTaskMgr)
      self.accept('w',base.toggleWireframe)
      self.accept('c',camera.printTransform)
      # these 3 demonstrate IDE's error tracking of function call at messenger level,
      # i.e. due to arguments count/type mismatch
      self.accept('q',self.printTaskMgr,["force printTaskMgr to swallow me, and see what'd happen"])
      self.accept('r',m.removeNode,["force C/C++ function to swallow me, and see what'd happen"])
      self.accept('a',m.attachNewNode,[None])

      self.isPaused=0

      # just a proof that default cameras will always be preserved upon update,
      # normally, all saved-as-attribute nodes will be removed
      self.cam=camera

      self.title = OnscreenText(text = 'TITLE : it works :D !', parent = base.a2dBottomRight,
                   pos = (-.02, .1), fg=(1,1,1,1), shadow=(0,0,0,1),shadowOffset=(.1,.1),
                   align = TextNode.ARight, scale = .05, mayChange=1)

      OnscreenText(text = '[ SPACE ] : toggle pause/resume', parent = base.a2dTopLeft,
          pos = (.01, -.05), fg=(1,1,1,1), shadow=(0,0,0,1), shadowOffset=(.1,.1),
          align = TextNode.ALeft, scale = .05)
      # broken class cleanup demonstration
#       self.brokenInstance=BrokenClass()

      # create jacks
      self.jacks=Jack()

      ## create smileys
      self.smileys=Smiley()

      #### create pandas
      num=3
      self.pandas=[Panda() for p in range(num)]
      ##### let's complicate it a little, create circular references
      for p in range(num):
          for n in range(num):
              if p!=n:
                 self.pandas[p].other.append(self.pandas[n])

      # DirectEntry
      self.entrybox = DirectEntry(parent=base.a2dRightCenter,
           pos=Vec3(-.8,0,0), frameColor=(.50,.8,.9,.5),
           relief=DGG.GROOVE, initialText = 'just a text' ,scale=.05, width=15, numLines = 2,focus=0)

      # unstoppable task
      lilsmi=loader.loadModel('misc/lilsmiley')
      lilsmi.reparentTo(aspect2d)
      lilsmi.getChild(0).setScale(.2)
      lilsmi.getChild(0).setAlphaScale(.5)
      taskMgr.add( self.moveLilsmi, unstoppable_namePrefix+'moveLilsmi',
                   extraArgs=[lilsmi,lilsmi.getChild(0)] )
      OnscreenText('unstoppable\ntask',parent=lilsmi,scale=.05,pos=(0,-.15),fg=(1,1,1,1))

      # unstoppable interval
      lilsmi2=loader.loadModel('misc/lilsmiley').copyTo(aspect2d)
      lilsmi2.getChild(0).setScale(.2)
      OnscreenText('unstoppable\ninterval',parent=lilsmi2,scale=.05,pos=(0,-.15),fg=(1,1,1,1))
      Sequence( lilsmi2.posInterval(5,Point3(-.9,0,.9),Point3(.9,0,.9)),
                lilsmi2.posInterval(5,Point3(.9,0,.9),Point3(-.9,0,.9)),
                name=unstoppable_namePrefix+'smiIval').loop()

      # unstoppable actor
      textParent=NodePath('')
      text = OnscreenText(parent=textParent,text="You cannot\npause me\nHO HO HO")
      b3=text.getTightBounds()
      bHalf=(b3[0]+b3[1])*.5
      b=(b3[1]-b3[0])*.5
      ratio=b[0]/b[2]
      b.setZ(b[0]) if ratio>1 else b.setX(b[2])
      b*=1.05 # give a little gap from the border, to avoid artifact on texture's small mip level
      textBuffer = base.win.makeTextureBuffer('text buffer', 512,512)
      textBuffer.setClearColor(Vec4(1,1,1,1))
      textCam = base.makeCamera2d(textBuffer)
      textCam.reparentTo(textParent)
      textCam.setPos(bHalf) # put it exactly at text's center
      textCam.setScale(b[0],1,b[2]) # auto-zoom in to text
      self.textTexture = textBuffer.getTexture()
      self.textTexture.setMinfilter(Texture.FTLinearMipmapLinear)
      base.graphicsEngine.renderFrame()
      base.graphicsEngine.removeWindow(textBuffer)

      taskMgr.doMethodLater(3,self.spawnNewPanda,'spawnNewPanda')

      # Ralph
      ralphLoc='../samples/Roaming-Ralph/models/'
      self.Ralph = Actor(ralphLoc+'ralph',{'walk':ralphLoc+'ralph-walk','run':ralphLoc+'ralph-run'})
#       self.Ralph.enableBlend()
      # interpolate frames
#       self.Ralph.find('**/+Character').node().getBundle(0).setFrameBlendFlag(1)
#       self.Ralph.setControlEffect('walk', .5)
#       self.Ralph.setControlEffect('run', .5)
#       self.Ralph.loop('run')
      self.Ralph.loop('walk')
      self.Ralph.reparentTo(render)
      self.Ralph.setPos(-2,-15,0)
#       self.Ralph.setTag('nopause','') # to exclude this actor from getting paused

      # Eve
      eveLoc='../samples/Looking-and-Gripping/models/'
      self.Eve = Actor(eveLoc+'eve', {'walk' : eveLoc+'eve_walk'})
      self.Eve.reparentTo(render)
      self.Eve.setPos(2,-15,0)
      self.Eve.actorInterval("walk", playRate = 2).loop()
#       self.Eve.setTag('nopause','') # to exclude this actor from getting paused

      # MOTION PATH INTERVAL
      np=render2d.attachNewNode('')
      child=np.attachNewNode('')
      LS=LineSegs()
      NC=NurbsCurve()
      NC.setOrder(2)
      num=100
      degInc=360./num
      for v in range(num):
          np.setR(-v*degInc)
          child.setX(.6+.3*random.random())
          x, z = child.getX(render2d),child.getZ(render2d)
          NC.appendCv(x,0,z)
          LS.drawTo(x,0,z)
          if v==0: ox,oz=x,z
      LS.drawTo(ox,0,oz)
      NC.recompute()
      render2d.attachNewNode(LS.create())

      s=loader.loadModel('misc/lilsmiley')
      s.reparentTo(render2d)
      s.setScale(.07)
      Sequence(
         s.colorScaleInterval(.75,Vec4(1,0,0,1)),
         s.colorScaleInterval(.5,Vec4(1)),
         # to make it not pausable
#          name=unstoppable_namePrefix+'colorscale-%s'%id(s)
      ).loop()

      mp=Mopath('mp1')
      mp.loadNodePath(NodePath(NC))
      mpi=MopathInterval( mp, s, duration=30,
         # to make it not pausable
#          name=unstoppable_namePrefix+'mopath-%s'%id(mp)
         )
      mpi.loop()

      # movie texture
#       movie='../samples/Media-Player/PandaSneezes.avi'
#       movTex=loader.loadTexture(movie)
#       movTexUV=movTex.getTexScale()
#       CM=CardMaker('')
#       CM.setFrameFullscreenQuad()
#       CM.setUvRange(movTex)
#       card=render.attachNewNode(CM.generate())
#       card.setTwoSided(1)
#       scale=8
#       card.setScale(movTexUV[0]*scale,1,movTexUV[1]*scale)
#       card.setPos(-15,5,2)
#       card.setTexture(movTex)
#       card.setTransparency(1)
#       card.setAlphaScale(.8)
#       playAudioToo=1  # play audio ?
#       pausable=1
#       if playAudioToo:
#          self.movAudio=loader.loadSfx(movie)
#          self.movAudio.setLoop(1)
#          self.movAudio.play()
#          self.movAudio.setPausable(pausable) # to make it pausable or not
#          movTex.synchronizeTo(self.movAudio)
#       else:
#          movTex.play()
#          movTex.setPausable(pausable) # to make it pausable or not

      # collisions
      self.loadFloor()
      self.loadColliders()

      # lights
      self.setupLights()

  def spawnNewPanda(self,t):
      p=Panda().pandaModel
      p.setY(-10)
      p.colorScaleInterval(3,Vec4(0,1,0,1),Vec4(1,1,1,1)).start()
      p.setTag('nopause','') # to exclude this actor from getting paused
      proj = LensNode('proj')
      proj.setLens(OrthographicLens())
      proj=p.attachNewNode(proj)
      proj.setScale(3.7)
      proj.setZ(4.7)
      p.projectTexture(TextureStage(''),self.textTexture,proj)
      taskMgr.doMethodLater(3,p.cleanup,'removeNewPanda',extraArgs=[])
      print('\n<id: %s>\n'%p.id(), p)
      p.ls()
      return Task.again

  def setupLights(self):
      ambientLight = AmbientLight( 'ambientLight' )
      ambientLight.setColor( Vec4(.3, 0.3, 0.3, 1) )
      self.ambientLight=render.attachNewNode( ambientLight )
      render.setLight(self.ambientLight)

      directionalLight = DirectionalLight( 'directionalLight1' )
      directionalLight.setDirection( Vec3( 0, 2, -1 ) )
      directionalLight.setColor( Vec4( .7, .7, .7, 1 ) )
      self.directionalLight=render.attachNewNode( directionalLight )
      render.setLight(self.directionalLight)

  def loadFloor(self):
      self.floorBit=BitMask32.bit(1)
      self.sphereBit=BitMask32.bit(2)
      self.offBit=BitMask32.allOff()
      self.floor=loader.loadModel('misc/rgbCube')
      self.floor.reparentTo(render)
      self.floor.setScale(18,18,.2)
      self.floor.setR(25)
      self.floor.flattenLight()
      box=loader.loadModel('box')
      box.reparentTo(self.floor)
      box.setScale(7,5,.5)
      box.setPos(-4,2,1.5)
      box.setR(-25)
      self.floor.flattenLight()
      self.floor.setPos(-5,-10,-7)
      self.floor.setCollideMask(self.floorBit)
      box.setCollideMask(self.floorBit|self.sphereBit)
      self.floor.setLightOff(1)
      self.floor.hprInterval(3,Vec3(360,0,0)).loop()

  def loadColliders(self):
      base.cTrav=CollisionTraverser()
      base.cTrav.setRespectPrevTransform(1)
#       base.cTrav.showCollisions(render)
      self.arrows=[]
      for c in range(5):
          arrow=loader.loadModel('misc/Spotlight')
          arrow.reparentTo(render)
          arrow.setP(90)
          arrow.setScale(.3)
          arrow.setColor(.5+.5*random.random(),.5+.5*random.random(),.5+.5*random.random())
          arrow.flattenStrong()
          arrow.setPos(self.floor,random.uniform(-4,4),random.uniform(-4,4),10)
          rayNP = arrow.attachCollisionRay('', 0,0,2, 0,0,-1, self.floorBit,self.offBit)
          rayNP.show()
          sphereNP = arrow.attachCollisionSphere('', 0,0,1.5, .7, self.sphereBit,self.sphereBit)
#           sphereNP.show()
          CHgravity = CollisionHandlerGravity()
          CHgravity.addCollider(rayNP,arrow)
          CHpusher= CollisionHandlerPusher()
          CHpusher.addCollider(sphereNP,arrow)
          base.cTrav.addCollider(rayNP,CHgravity)
          base.cTrav.addCollider(sphereNP,CHpusher)
          self.arrows.append([arrow,CHgravity])
      taskMgr.add(self.moveArrows, 'move arrows')

  def moveArrows(self,task):
      dt=globalClock.getDt()
      if dt>.2: return Task.cont
      speed=10*dt
      for a,CHG in self.arrows:
          if CHG.isOnGround():
             a.setH(a,random.uniform(-20,20))
          lastPos=a.getPos(self.floor)
          a.setFluidY(a,speed)
          pos=a.getPos(self.floor)
          if not ( (-5 < pos[0] < 5) and (-5 < pos[1] < 5) ):
             a.setFluidPos(self.floor,lastPos)
             a.headsUp(self.floor) # looks at floor while stays upright
             a.setFluidY(a,speed)
      return Task.cont

  def moveLilsmi(self,np,geom):
      dt=globalClock.getDt()
      if dt>.2: return Task.cont
      geom.setR(geom,random.uniform(-10,10))
      speed=1.5*dt
      np.setZ(geom,speed)
      if np.getDistance(aspect2d)>.5:
         geom.setR(geom,180)
         np.setZ(geom,speed)
      return Task.cont

  def toggleSceneActive(self):
      self.isPaused=not self.isPaused
      if self.isPaused:
         PR.pause( allAnims=0,
                   allAudios=0,
                   allMovies=0,
                   collision=1,
                   excludedTaskNamePrefix=unstoppable_namePrefix,
                   excludedIvalNamePrefix=unstoppable_namePrefix
                   )
      else:
         PR.resume()

  def printTaskMgr(self):
      print(taskMgr)
      print(ivalMgr)


if __name__=='__main__':
   # World class instantiation must be blocked, so the IDE won't give you
   # another copy of everything.  Do you know how ?
   World()
   # restores clock mode to normal
   globalClock.setMode(ClockObject.MNormal)
   run()
