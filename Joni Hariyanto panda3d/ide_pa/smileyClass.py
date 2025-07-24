from pandac.PandaModules import Vec3
from direct.interval.IntervalGlobal import *
from math import pi, sin

class Smiley:
  def __init__(self):
      scale=.8
      num=int(10/scale)
      self.smileys=[]
      self.moves = [0 for i in range(num)]
      self.roll = [0 for i in range(num)]
      for s in range(num):
          smi=loader.loadModel('smiley')
          smi.reparentTo(render)
          smi.setScale(scale)
          smi.setPos((-(num-1)*.5+s)*scale*2,-6,scale*1.25)
          self.smileys.append(smi)
          self.moves[s] = LerpFunc(
                       self.oscilateSmiley,
                       duration = 2,
                       fromData = 0,
                       toData = 2*pi,
                       extraArgs=[self.smileys[s], pi*(s%2)]
                       )
          self.moves[s].loop()
          self.roll[s]=self.smileys[s].hprInterval(3.,Vec3(720,0,360))
          self.roll[s].loop()

  def oscilateSmiley(self, rad, np, offset):
      np.setZ(sin(rad + offset) *.9)
