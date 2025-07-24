from pandac.PandaModules import Point3
from direct.interval.IntervalGlobal import Sequence


class BrokenClass:
  def __init__(s):
      s.t=loader.loadModel('teapot')
      s.t.reparentTo(render)
      tCenter=s.t.find('**/body').getBounds().getCenter()+Point3(0,0,.5)
      duration=.3
      for c in s.t.findAllMatches('**/+GeomNode').asList():
          vec=c.getBounds().getCenter()-tCenter
          vec.normalize()
          vec*=3
          pos=c.getPos()
          Sequence(
                   c.posInterval(duration,pos+vec,blendType='easeOut'),
                   c.posInterval(duration,pos,blendType='easeIn')
                   ).loop()
      s.messItUp()

  def messItUp(you):
      you.are=Screwed()
