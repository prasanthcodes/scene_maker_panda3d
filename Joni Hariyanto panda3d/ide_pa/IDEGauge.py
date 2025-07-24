from pandac.PandaModules import Plane, PlaneNode, Point3, Vec3, Vec4
from direct.interval.IntervalGlobal import *
from direct.gui.OnscreenText import OnscreenText
import IDEDrawUtil as DU

class LoadingGauge:
  def __init__(self,parent,scale,font,ivalName):
      self.parent=parent.attachNewNode('gauge parent')
      self.parent.setTransparency(1)
      self.parent.setBin('gaugeBin',0)
      self.font=font
      self.ivalName=ivalName
      self.barParent=self.parent.attachNewNode('progress')
      self.barBorder=self.barParent.attachNewNode('bars border')
      self.bar=self.barParent.attachNewNode('bars parent')
      self.barParent.setZ(-.05)
      barLen=.07
      barWidth=.012
      slant=.25
      vertices=[
        (0,-barWidth),
        (barLen*slant,0),
        (0,barWidth),
        (barLen*(1-slant),barWidth),
        (barLen,0),
        (barLen*(1-slant),-barWidth),
        (0,-barWidth),
      ]
      barColor=(255,200,100,255)
      self.realBar=DU.createPolygon(vertices,color=barColor)
      self.realBarBorder=DU.createPolygonEdge(vertices,(.5,.4,.3))
      barLen-=.0035
      for x in range(int(1.75/barLen)):
          xpos=x*barLen
          self.realBar.instanceUnderNode(self.bar,'').setX(xpos)
          self.realBarBorder.instanceUnderNode(self.barBorder,'').setX(xpos)
      bounds3=self.bar.getTightBounds()
      bounds=bounds3[1]-bounds3[0]
      self.length=bounds[0]
      # gauge border
      borderGap=.012
      halfLength=.5*self.length+borderGap
      halfHeight=.5*bounds[2]+borderGap
      borderVertices=[
        (borderGap-halfHeight*2,-halfHeight),
        (0,0),
        (borderGap-halfHeight*2,halfHeight),
        (self.length-borderGap,halfHeight),
        (self.length+halfHeight,0),
        (self.length-borderGap,-halfHeight),
        (borderGap-halfHeight*2,-halfHeight),
      ]
      barBGpoly=DU.createPolygon(borderVertices,color=(0,0,0,50))
      barBGpoly.reparentTo(self.barParent,sort=-100)
      DU.createPolygonEdge(borderVertices,(.8,.5,.2),2).reparentTo(self.barParent)
      # text
      OnscreenText('Loading :',parent=self.parent,
          font=self.font, fg=Vec4(*barColor)/255.,
          scale=.08, pos=(halfLength,halfHeight*7))
      self.nameText=OnscreenText(parent=self.parent,
          font=self.font, fg=(1,1,1,1),
          scale=.05, pos=(halfLength,halfHeight*4),
          mayChange=1)
      self.progressText=OnscreenText('0 %%',parent=self.parent,
          font=self.font, fg=(1,1,1,1),
          scale=.05, pos=(halfLength,0),
          mayChange=1)
      # background polygon
      padScale=1.1
      bounds3=self.parent.getTightBounds()
      minB,maxB=bounds3
      minB-=Vec3(.1,0,.07)
      maxB+=Vec3(.1,0,.07)
      corner=.03
      BGvertices=[
        (minB[0]+corner,minB[2]),
        (minB[0],minB[2]+corner),
        (minB[0],maxB[2]-corner),
        (minB[0]+corner,maxB[2]),
        (maxB[0]-corner,maxB[2]),
        (maxB[0],maxB[2]-corner),
        (maxB[0],minB[2]+corner),
        (maxB[0]-corner,minB[2]),
        (minB[0]+corner,minB[2]),
      ]
      BGpoly=DU.createPolygon(BGvertices,color=(20,50,80,230))
      BGpoly.reparentTo(self.parent,sort=-1000)
      DU.createPolygonEdge(BGvertices,(0,.5,.8),3).reparentTo(self.parent)
      # clip planes
      self.planes = self.bar.attachNewNode('clip planes')
      pn1 = PlaneNode('')
      pn1.setPlane( Plane(Vec3(-1,0,-1.5), Point3(0,0,0)) )
      self.plane1 = self.planes.attachNewNode(pn1)
      pn2 = PlaneNode('')
      pn2.setPlane( Plane(Vec3(-1,0,1.5), Point3(0,0,0)) )
      self.plane2 = self.planes.attachNewNode(pn2)
      self.bar.setClipPlane(self.plane1)
      self.bar.setClipPlane(self.plane2)
      self.parent.setScale(scale)
      self.parent.setX(-self.length*scale*.5)
      # methods
      hide=Sequence( self.parent.hprInterval(.1,Vec3(0,-90,0),Vec3(0,0,0),blendType='easeOut'),
                     Func(self.parent.hide),
                     Func(self.parent.setP,0),
                     name=self.ivalName
                     )
      self.hide=hide.start
      self.show=self.parent.show

  def get(self):
      return self.planes.getX()/float(self.length)

  def set(self,p):
      self.planes.setX(p*self.length)
      self.progressText['text']='%i %%'%(p*100)

  def reset(self):
      self.planes.setX(0)
      self.nameText['text']=''
      self.progressText['text']='0 %%'

  def setText(self,text):
      self.nameText['text']=text
