from direct.actor.Actor import Actor
from random import random,gauss

class Panda:
  def __init__(self):
      self.pandaModel=Actor('panda',{'walk':'panda-walk'})
      self.pandaModel.reparentTo(render)
      scale=.2+random()*.5
      self.pandaModel.setScale(scale)
      self.pandaModel.setPos(gauss(0,4),1+gauss(0,3),0)
      self.pandaModel.setColorScale(.4+random()*.3,.7+random()*.3,.7+random()*.3,1)
      self.pandaModel.setPlayRate(1./scale,'walk')
      self.pandaModel.setP(1/(.8*scale*scale))
      self.pandaModel.loop('walk')
      self.other=[]
