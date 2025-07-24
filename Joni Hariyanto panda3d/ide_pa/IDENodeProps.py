__all__=['NodeProps']
from pandac.PandaModules import CollisionNode,LineSegs,ModelRoot,NodePath,TextNode,TextProperties,SceneGraphAnalyzer,Vec4
from direct.gui.DirectGui import *
import math, os
import IDE

class NodeProps(SceneGraphAnalyzer):
  def __init__(self, textColor=Vec4(1)):
      SceneGraphAnalyzer.__init__(self)
      self.getNumCollNodes=lambda np:len(self.collNodes)
      self.getNumCollSolids=lambda np:sum([n.node().getNumSolids() for n in self.collNodes])
      self.getTFans=lambda:'%s (%s)'%(self.getNumTrifans(),self.getNumTrianglesInFans())
      self.getTStrips=lambda:'%s (%s)'%(self.getNumTristrips(),self.getNumTrianglesInStrips())
      self.getTexMem=lambda:int(math.ceil(self.getTextureBytes()/1024.))
      self.getNumTex=lambda np:len(np.findAllTextures())
      self.getVtxDataMem=lambda:int(math.ceil(self.getVertexDataSize()/1024.))

      self.selectedNodePath=None
      self.propsFont=IDE.IDE_FONT_medrano#monospaceBold
      self.typeFont=IDE.IDE_FONT_transmetals
      fg = textColor
      self.frame = DirectFrame(parent=IDE.IDE_root, frameColor=(0,0,0,.8), 
        state=DGG.NORMAL, scale=IDE.IDE_statusBarHeight*8.8,
        enableEdit=0)
      self.TYPE=OnscreenText(parent=self.frame, text='PROPERTIES', font=self.typeFont, fg=fg, scale=.09)
      self.TYPEnp=NodePath(self.TYPE)
      self.GENERAL=self.frame.attachNewNode('general props')
      self.GENERALlines=self.GENERAL.attachNewNode('lines')
      self.GENERALlines.setTransparency(1)
      self.GENERALfields='''\
Nodes:getNumNodes
Geoms:getNumGeoms
Geom Nodes:getNumGeomNodes
LOD Nodes:getNumLodNodes
Instances:getNumInstances

Coll. Nodes:getNumCollNodes>
Coll. Solids:getNumCollSolids>

Vertices:getNumVertices
Normals:getNumNormals
Colors:getNumColors

Triangles:getNumTris
TFans (tris):getTFans
TStrips (tris):getTStrips
Loose tris:getNumIndividualTris
Points:getNumPoints
Lines:getNumLines

Textures:getNumTex>
Tex Coords:getNumTexcoords
Tex memory:getTexMem|K

VtxFormats:getNumGeomVertexFormats
VtxDatas:getNumGeomVertexDatas
VDatas mem:getVtxDataMem|K'''
      split=self.GENERALfields.split('\n')
      numSep=0
      separators=[]
      for i in range(len(split)):
          if not split[i]:
             separators.append(i-numSep)
             numSep+=1
      for i in range(numSep):
          split.remove('')
      self.GENERALnumFields=len(split)
      self.GENERALvalQueryFuncs=[[f[f.find(':')+1:],'',False] for f in split]
      for f in self.GENERALvalQueryFuncs:
          suffixPos=f[0].find('|')
          if suffixPos>-1:
             f[1]=f[0][suffixPos+1:]
             f[0]=f[0][:suffixPos]
          npPos=f[0].find('>')
          if npPos>-1:
             f[2]=True
             f[0]=f[0][:npPos]
          f[0]=getattr(self,f[0])
      self.GENERALfields='\n'.join([f[:f.find(':')] for f in split])

      LS=LineSegs('')
      LS.setColor(.65,.65,.65,1)
      LS.moveTo(0,0,0)
      LS.drawTo(.5,0,0)
      LS.drawTo(1,0,0)
      line=NodePath(LS.create())
      LS.setVertexColor(1,.5,.5,.5,0)
      LS=LineSegs('')
      LS.moveTo(0,0,0)
      LS.drawTo(1,0,0)
      flatLine=NodePath(LS.create())
      flatLine.copyTo(self.GENERALlines)
      flatLine.copyTo(self.GENERALlines).setZ(-self.GENERALnumFields)
      for z in range(1,self.GENERALnumFields):
          (flatLine if z in separators else line).copyTo(self.GENERALlines).setZ(-z)
          
      self.valueAfter=True
      self.GENERALprop=OnscreenText(parent=self.GENERAL, text=self.GENERALfields, 
         font=self.propsFont, fg=fg, align=TextNode.ALeft)
      self.GENERALval=OnscreenText(parent=self.GENERAL, text='-\n'*self.GENERALnumFields,
         font=self.propsFont, fg=fg, align=TextNode.ARight)
      self.fieldHeight=self.propsFont.getLineHeight()*self.GENERALprop['scale'][1]
      self.baseline2top=self.fieldHeight*.75
      self.GENERALprop.setX(0 if self.valueAfter else self.fieldHeight)
      self.GENERALlines.flattenStrong()
      self.GENERALlines.setColorScale(textColor)
      self.GENERALlines.setZ(self.baseline2top)
      self.GENERALlines.setSz(self.fieldHeight)
      self.TYPEnp.setZ(self.fieldHeight*1.2)
      
      self.tooltipScale=.9/self.frame['scale']
      self.gotoModelLocDB=DirectButton(parent=self.TYPE,image='IDE_dir.png', relief=None,
         scale=.05, command=IDE.IDE_gotoDir, clickSound=0, rolloverSound=0, pressEffect=0)
      self.gotoModelLocDB.setTransparency(1)
      self.gotoModelLocDB.stateNodePath[2].setR(10)
      locText=IDE.createTooltip('Open model directory',align=TextProperties.ALeft, alpha=0)
      locText.reparentTo(self.gotoModelLocDB.stateNodePath[0])
      locText.setScale(self.tooltipScale)
      locText.setZ(locText,1.3)
      locText.copyTo(self.gotoModelLocDB.stateNodePath[1])
      locText.wrtReparentTo(self.gotoModelLocDB.stateNodePath[2])
      self.gotoModelLocDB.stateNodePath[2].setColor(0,1,0,1)
      self.gotoModelLocDB.stash()
      
      self.invertValsDB = DirectButton(parent=self.frame,image='IDE_reverse.png', relief=None,
         scale=.055,# pos=(self.fieldHeight*.4,0,self.GENERALlines.getTightBounds()[0][2]-self.fieldHeight*.75),
         command=self.invertValuesPosition, clickSound=0, rolloverSound=0, pressEffect=0)
      self.invertValsDB.setTransparency(1)
      invertValsTT=IDE.createTooltip('Flip',align=TextProperties.ALeft, alpha=1)
      invertValsTT.reparentTo(self.invertValsDB.stateNodePath[2])
      invertValsTT.setScale(locText,self.gotoModelLocDB['scale']/self.invertValsDB['scale'])
      invertValsTT.setPos(invertValsTT,1.5,0,-1.5)
      invertValsTT.copyTo(self.invertValsDB.stateNodePath[1])
      self.invertValsDB.stateNodePath[2].setColor(0,1,0,1)

      self.putFieldsNvals()

  def setBlank(self):
      self.clear()
      self.GENERALval['text']='-\n'*self.GENERALnumFields
      self.TYPE['text']='PROPERTIES'
      self.putFieldsNvals()
      self.gotoModelLocDB.stash()
      self.selectedNodePath=None

  def invertValuesPosition(self):
      self.valueAfter=not self.valueAfter
      self.putFieldsNvals()

  def putFieldsNvals(self):
      minB,maxB=self.GENERALprop.getTightBounds()
      pDim=maxB-minB
      minB,maxB=self.GENERALval.getTightBounds()
      vDim=maxB-minB
      dim=pDim+vDim
      self.GENERALval.setX((dim[0]+.55*self.fieldHeight) if self.valueAfter else vDim[0])
      self.GENERALprop.setX(0 if self.valueAfter else vDim[0]+.55*self.fieldHeight)
      self.GENERALlines.setSx((self.GENERALval if self.valueAfter else self.GENERALprop).getTightBounds()[1][0])
      self.TYPEnp.setX(self.GENERALlines,.5)
      minB,maxB=self.GENERALlines.getTightBounds()
      buttonFrame=self.invertValsDB.node().getFrame()
      pad=self.fieldHeight*.2
      bottomPad=(buttonFrame[3]-buttonFrame[2])*self.invertValsDB['scale']
      l,r,b=minB[0]-pad,maxB[0]+pad,minB[2]-pad-bottomPad
      t=self.TYPEnp.getTightBounds()[1][2]+pad
      self.frame['frameSize']=(l,r,b,t)
      self.invertValsDB.alignTo(self.frame, DGG.LL)

  def getNodePath(self):
      return self.selectedNodePath

  def setNodePath(self,np):
      self.selectedNodePath=np
      node=np.node()
      nodeType=type(node)
      self.clear()
      self.addNode(node)
#       self.write(ostream)
      self.collNodes=IDE.asList(np.findAllMatches('**/+CollisionNode'))
      if nodeType==CollisionNode:
         IDE.add2List(self.collNodes,np)
      # populates the values
      self.GENERALval['text']=('%s\n'*self.GENERALnumFields)%tuple(str(f[0](np) if f[2] else f[0]())+f[1] for f in self.GENERALvalQueryFuncs)
      self.TYPE['text']=str(node.getClassType())
      self.putFieldsNvals()

      self.gotoModelLocDB.stash()
      if nodeType==ModelRoot:
         modelLoc=os.path.dirname(node.getFullpath().toOsSpecific())
         if os.path.exists(modelLoc):
            x=self.TYPE.getTightBounds()[0][0]-.75*self.fieldHeight
            z=self.TYPE.getBounds().getCenter()[2]
            self.gotoModelLocDB.unstash()
            self.gotoModelLocDB.setPos(self.TYPE.getParent(),x,0,z)
            self.gotoModelLocDB['extraArgs']=[modelLoc]

  def setTextColor(self,color):
      self.GENERALprop['fg'] = self.GENERALval['fg'] = self.TYPE['fg'] = color
      self.GENERALlines.setColorScale(color)