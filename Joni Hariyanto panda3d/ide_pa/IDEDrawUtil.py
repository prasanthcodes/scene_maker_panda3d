from pandac.PandaModules import Geom, GeomNode, \
     GeomLinestrips, GeomTriangles, GeomTristrips, \
     GeomVertexFormat, GeomVertexArrayFormat, GeomVertexData, GeomVertexWriter,\
     InternalName, LineSegs, NodePath, Triangulator, Vec4

GEOM1array = GeomVertexArrayFormat()
GEOM1array.addColumn(InternalName.make('vertex'), 3, Geom.NTFloat32, Geom.CPoint)
GEOM1array.addColumn(InternalName.make('texcoord'), 2, Geom.NTFloat32, Geom.CTexcoord)
GEOM1format = GeomVertexFormat()
GEOM1format.addArray(GEOM1array)
GEOM1VtxFormat = GeomVertexFormat.registerFormat(GEOM1format)

def createPolygon(vertices,holes=None,color=(255,255,255,255)):
    if vertices[0]==vertices[-1]:
       vertices=list(vertices[:-1])
    tri=Triangulator()
    vdata = GeomVertexData('trig', GeomVertexFormat.getV3(), Geom.UHStatic)
    vwriter = GeomVertexWriter(vdata, 'vertex')
    for x,z in vertices:
        vi = tri.addVertex(x, z)
        vwriter.addData3f(x, 0, z)
        tri.addPolygonVertex(vi)
    if holes:
       for hole in holes:
           if hole:
              tri.beginHole()
              for x,z in hole:
                  vi = tri.addVertex(x, z)
                  vwriter.addData3f(x, 0, z)
                  tri.addHoleVertex(vi)
    tri.triangulate()
    prim = GeomTriangles(Geom.UHStatic)
    for i in range(tri.getNumTriangles()):
        prim.addVertices(tri.getTriangleV0(i),
                         tri.getTriangleV1(i),
                         tri.getTriangleV2(i))
        prim.closePrimitive()
    geom = Geom(vdata)
    geom.addPrimitive(prim)
    geomNode = GeomNode('bar')
    geomNode.addGeom(geom)
    np=NodePath(geomNode)
    np.setColor(Vec4(*color)/255.)
    return np

def createPolygonEdge(vertices,color=(1,1,1,1),thickness=1):
    if vertices[0]!=vertices[-1]:
       vertices=list(vertices)+[vertices[0]]
    LS=LineSegs()
    LS.setColor(*color)
    LS.setThickness(thickness)
    LS.moveTo(vertices[0][0],0,vertices[0][1])
    for xz in vertices[1:]:
        LS.drawTo(xz[0],0,xz[1])
    return NodePath(LS.create())

def createLine(length=1, color=(1,1,1,1), endColor=None, thickness=1, centered=1):
    LS=LineSegs()
    LS.setColor(*color)
    LS.setThickness(thickness)
    LS.moveTo(-length*.5*centered,0,0)
    LS.drawTo(length*(1-.5*centered),0,0)
    node=LS.create()
    if endColor:
       LS.setVertexColor(1,*endColor)
    return node

def createUVLine(length=1, thickness=1, centered=1):
    vdata = GeomVertexData('line', GEOM1VtxFormat, Geom.UHStatic)
    vertex = GeomVertexWriter(vdata, 'vertex')
    texcoord = GeomVertexWriter(vdata, 'texcoord')
    #_____________________________________
    vertex.addData3f(.5*length*centered,0,0)
    texcoord.addData2f(0, 0)
    #_____________________________________
    vertex.addData3f(length*(1-.5*centered),0,0)
    texcoord.addData2f(length, 0)
    #_____________________________________
    box = GeomLinestrips(Geom.UHStatic)
    box.addConsecutiveVertices(0,2)
    box.closePrimitive()

    geom = Geom(vdata)
    geom.addPrimitive(box)
    gn = GeomNode('line with UV')
    gn.addGeom(geom)
    return gn

def createUVRect(x=1,z=1,align=0,flipU=False,Uflood=None):
    vdata = GeomVertexData('leftrect', GEOM1VtxFormat, Geom.UHStatic)
    vertex = GeomVertexWriter(vdata, 'vertex')
    texcoord = GeomVertexWriter(vdata, 'texcoord')

    # vtx alignment : left=0, center=.5, right=1
    Xa=x*align
    # U alignment
    if Uflood is None:
       Ua0=-(x-1)*align
       Ua1=x-(x-1)*align
       if flipU:
          Ua0=-Ua0+1
          Ua1=-Ua1+1
    else:
       Ua0=Ua1=Uflood

    # UL
    vertex.addData3f(-Xa,0,z)
    texcoord.addData2f(Ua0, 1)
    # LL
    vertex.addData3f(-Xa,0,0)
    texcoord.addData2f(Ua0, 0)
    # UR
    vertex.addData3f(x-Xa,0,z)
    texcoord.addData2f(Ua1, 1)
    # LR
    vertex.addData3f(x-Xa,0,0)
    texcoord.addData2f(Ua1, 0)

    tris = GeomTristrips(Geom.UHStatic)
    tris.addConsecutiveVertices(0,3)
    tris.addVertex(3)
    tris.closePrimitive()

    geom = Geom(vdata)
    geom.addPrimitive(tris)
    gn = GeomNode('rect with UV')
    gn.addGeom(geom)
    return gn
