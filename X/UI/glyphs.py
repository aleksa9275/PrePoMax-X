"""VTK 9 presentation of original Controller glyph commands.

Source shapes/placement constants follow vtkControl/vtkControl.cs Add*Actor and
CreateSpringSource. These are renderer adapters; no model or field is computed here.
"""
import math
from vtkmodules.vtkCommonCore import vtkPoints,vtkDoubleArray,vtkFloatArray
from vtkmodules.vtkCommonDataModel import vtkPolyData,vtkCellArray
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkFiltersCore import vtkAppendPolyData,vtkTriangleFilter,vtkPolyDataNormals,vtkGlyph3D,vtkTubeFilter
from vtkmodules.vtkFiltersGeneral import vtkTransformPolyDataFilter,vtkTransformFilter
from vtkmodules.vtkFiltersModeling import vtkLinearExtrusionFilter,vtkRotationalExtrusionFilter
from vtkmodules.vtkFiltersSources import vtkArrowSource,vtkConeSource,vtkCubeSource,vtkCylinderSource,vtkLineSource,vtkSphereSource
from vtkmodules.vtkRenderingCore import vtkActor,vtkPolyDataMapper,vtkDistanceToCamera


def output(source):source.Update();return source.GetOutput()
def transformed(data,translate=None,rotate=None):
    transform=vtkTransform()
    if translate:transform.Translate(*translate)
    if rotate:
        for axis,angle in rotate:getattr(transform,'Rotate'+axis)(angle)
    filter=vtkTransformPolyDataFilter();filter.SetInputData(data);filter.SetTransform(transform);return output(filter)
def append(*data):
    result=vtkAppendPolyData()
    for item in data:result.AddInputData(item)
    return output(result)
def surface(points,faces):
    p=vtkPoints();cells=vtkCellArray()
    for point in points:p.InsertNextPoint(*point[:3])
    for face in faces:
        cells.InsertNextCell(len(face))
        for i in face:cells.InsertCellPoint(i)
    data=vtkPolyData();data.SetPoints(p);data.SetPolys(cells);return data
def sphere(radius,center=(0,0,0),phi=13,theta=13):
    source=vtkSphereSource();source.SetRadius(radius);source.SetCenter(*center);source.SetPhiResolution(phi);source.SetThetaResolution(theta);return output(source)
def cube(center,lengths):
    s=vtkCubeSource();s.SetCenter(*center);s.SetXLength(lengths[0]);s.SetYLength(lengths[1]);s.SetZLength(lengths[2]);return output(s)
def cylinder(x,length,radius):
    s=vtkCylinderSource();s.SetHeight(length);s.SetRadius(radius);s.SetResolution(16);s.CappingOn();return transformed(output(s),(x,0,0),[('Z',-90)])
def arrow(relative=1):
    s=vtkArrowSource();s.SetTipResolution(21);s.SetTipLength(.3/relative);s.SetTipRadius(.1/relative);s.SetShaftResolution(15);s.SetShaftRadius(.03/relative);return output(s)
def spring():
    # Original eight turns, ten radial samples, three-point smoothing.
    points=[];r=.1;lin=.2;delta=(1-2*lin)/80
    points += [[lin/3*i,0,0] for i in range(3)]
    points += [[lin,r/3*i,0] for i in range(3)]
    phi=0
    for i in range(81):points.append([lin+delta*i,r*math.cos(phi),r*math.sin(phi)]);phi+=math.pi/10
    points += [[1-lin,r-r/3*(i+1),0] for i in range(3)]
    points += [[1-lin+lin/3*(i+1),0,0] for i in range(3)]
    smooth=[points[0]]+[[sum(points[i+j][axis] for j in [-1,0,1])/3 for axis in range(3)] for i in range(1,len(points)-1)]+[points[-1]]
    p=vtkPoints();cells=vtkCellArray();cells.InsertNextCell(len(smooth))
    for i,point in enumerate(smooth):p.InsertNextPoint(*point);cells.InsertCellPoint(i)
    data=vtkPolyData();data.SetPoints(p);data.SetLines(cells);tube=vtkTubeFilter();tube.SetInputData(data);tube.SetRadius(.03);tube.SetNumberOfSides(10);tube.CappingOn();tube.UseDefaultNormalOff();return transformed(output(tube),(-1.05,0,0))
def joint(symbol):
    if symbol=='Hinge':return append(cylinder(0,2.4,.12),cylinder(0,.9,.35),cylinder(-.49,.08,.5),cylinder(.49,.08,.5))
    if symbol=='Cylindrical':return append(cylinder(0,2.4,.12),cylinder(0,.9,.35))
    if symbol=='Slider':
        points=[];faces=[];ys=[-1,1,1,-1];zs=[-1,-1,1,1]
        for width in [.7,.34]:
            for end in [-1,1]:
                for y,z in zip(ys,zs):points.append([end*.9/2,y*width/2,z*width/2])
        for c in range(4):
            n=(c+1)%4;faces.extend([[c,n,4+n,4+c],[8+c,12+c,12+n,8+n],[4+c,4+n,12+n,12+c],[c,8+c,8+n,n]])
        return append(cube((0,0,0),(2.4,.24,.24)),surface(points,faces))
    if symbol=='Ball':
        points=[]
        for radius,indices in [(.65,range(13)),(.6,range(12,-1,-1))]:
            for i in indices:
                angle=math.radians(75+(178-75)*i/12);points.append([radius*math.sin(angle),0,radius*math.cos(angle)])
        extrusion=vtkRotationalExtrusionFilter();extrusion.SetInputData(surface(points,[list(range(26))]));extrusion.SetResolution(6);extrusion.SetAngle(50);extrusion.CappingOn();data=output(extrusion)
        return append(sphere(.45,phi=16,theta=16),*[transformed(data,rotate=[('Y',90),('Z',360*i/3-25)]) for i in range(3)])
    if symbol=='Weld':
        fillets=[]
        for side in [1,-1]:
            e=vtkLinearExtrusionFilter();e.SetInputData(surface([[0,side*.075,-.5],[0,side*.375,-.5],[.3,side*.075,-.5]],[[0,1,2]]));e.SetExtrusionTypeToVectorExtrusion();e.SetVector(0,0,1);e.SetScaleFactor(1);e.CappingOn();fillets.append(output(e))
        return append(cube((-.075,0,0),(.15,1.6,1)),cube((.5,0,0),(1,.15,1)),*fillets)
    raise ValueError('Unknown original joint symbol: '+symbol)

def symbol_source(name,args):
    if name=='AddSphereActor':return sphere(.2),1
    if name in ['AddOrientedDisplacementConstraintActor','AddOrientedConeActors']:
        s=vtkConeSource();s.SetCenter(-.5,0,0);s.SetResolution(31 if name=='AddOrientedDisplacementConstraintActor' else 11)
        if name=='AddOrientedConeActors':s.SetRadius(.35);s.CappingOn()
        return output(s),.3
    if name=='AddOrientedRotationalConstraintActor':
        s=vtkLineSource();s.SetPoint1(0,0,0);s.SetPoint2(-1.3,0,0);return append(cube((-1.55,0,0),(.4,.9,.9)),output(s)),.3
    if name=='AddOrientedJointActor':return joint(str(args[2])),.36
    if name=='AddOrientedArrowsActor':return transformed(arrow(float(args[3])),(-1.05 if args[2] else .05,0,0)),1
    if name=='AddOrientedDoubleArrowsActor':
        s=vtkConeSource();s.SetResolution(21);s.SetHeight(.3);s.SetRadius(.1);s.SetCenter(.65,0,0);return transformed(append(arrow(),output(s)),(.05,0,0)),1
    if name=='AddOrientedSpringActor':return spring(),1
    if name=='AddOrientedThermosActor':
        s=vtkCylinderSource();s.SetRadius(.1);s.SetHeight(.8);s.SetResolution(7);s.SetCenter(0,.7,0)
        return transformed(append(sphere(.2,(.2,0,0),11,11),transformed(output(s),rotate=[('Z',-90)])),(-1.05 if args[2] else .05,0,0)),.5
    if name=='AddOrientedFluxActor':return transformed(sphere(.2,(0 if args[2] else .2,0,0),9,11),(-1.05 if args[3] else .05,0,0)),.5
    raise ValueError('Unknown glyph command: '+name)

def glyph_actor(name,args,renderer):
    data=args[0];nodes=data.Geometry.Nodes
    if name in ['AddOrientedArrowsActor','AddOrientedDoubleArrowsActor']:
        # Same original zero-vector filtering, on a renderer-local copy.
        geometry=data.Geometry.DeepCopy();geometry.RemoveZeroLengthNormals();nodes=geometry.Nodes
    points=vtkPoints();normals=vtkDoubleArray();normals.SetNumberOfComponents(3)
    for i,p in enumerate(nodes.Coor):
        points.InsertNextPoint(*p)
        normals.InsertNextTuple3(*(nodes.Normals[i] if nodes.Normals is not None else [1,0,0]))
    poly=vtkPolyData();poly.SetPoints(points);poly.GetPointData().SetNormals(normals)
    distance=vtkDistanceToCamera();distance.SetInputData(poly);distance.SetScreenSize(float(args[1])*(float(args[3]) if name=='AddOrientedArrowsActor' else 1));distance.SetRenderer(renderer)
    source,scale=symbol_source(name,args);tri=vtkTriangleFilter();tri.SetInputData(source)
    glyph=vtkGlyph3D();glyph.SetSourceConnection(tri.GetOutputPort());glyph.SetInputConnection(distance.GetOutputPort());glyph.SetVectorModeToUseNormal();glyph.ScalingOn();glyph.SetScaleModeToScaleByScalar();glyph.SetInputArrayToProcess(0,0,0,0,'DistanceToCamera');glyph.SetScaleFactor(scale);glyph.OrientOn()
    mapper=vtkPolyDataMapper();mapper.SetInputConnection(glyph.GetOutputPort());mapper.ScalarVisibilityOff()
    actor=vtkActor();actor.SetMapper(mapper);actor.GetProperty().SetColor(data.Color.R/255,data.Color.G/255,data.Color.B/255);actor.GetProperty().SetAmbient(.6);actor.GetProperty().SetDiffuse(.6);actor.PickableOff();actor.UseBoundsOff()
    return actor


def plot_actor(name,args,nodes=None):
    """Original line-arrow presentation, including tensor tension/compression signs."""
    data,maximum,length,size=args;nodes=nodes or data.Geometry.Nodes;tensor='Tensor' in name
    points=vtkPoints();lines=vtkCellArray();vertices=vtkCellArray();values=vtkFloatArray();values.SetName('Scalars')
    def point(p,value):index=points.InsertNextPoint(*p);values.InsertNextValue(value);return index
    def line(a,b):lines.InsertNextCell(2);lines.InsertCellPoint(a);lines.InsertCellPoint(b)
    def add_arrow(start,base,value,head,width):
        u=[b-a for a,b in zip(start,base)];norm=math.sqrt(sum(v*v for v in u));u=[v/norm for v in u]
        r=[0,0,1] if abs(u[2])<.9 else [0,1,0];p=[u[1]*r[2]-u[2]*r[1],u[2]*r[0]-u[0]*r[2],u[0]*r[1]-u[1]*r[0]];norm=math.sqrt(sum(v*v for v in p));p=[v/norm for v in p]
        ids=[point(start,value),point(base,value),point([base[i]+head*u[i] for i in range(3)],value),point([base[i]+width*p[i] for i in range(3)],value),point([base[i]-width*p[i] for i in range(3)],value)]
        for a,b in [(0,1),(2,3),(3,4),(4,2)]:line(ids[a],ids[b])
    for p,direction,value in zip(nodes.Coor,nodes.Normals,nodes.Values):
        value=float(value)
        if not math.isfinite(value):continue
        index=point(p,value);vertices.InsertNextCell(1);vertices.InsertCellPoint(index)
        if maximum<=0 or length<=0 or size<=0 or direction is None:continue
        norm=math.sqrt(sum(v*v for v in direction))
        if not math.isfinite(norm) or norm<=0:continue
        if tensor:
            if abs(value)<=maximum*1e-10:continue
            u=[v/norm for v in direction];half=.5*length*abs(value)/maximum;head=.125*size;width=.03*size
            for sign in [-1,1]:
                if value>0:add_arrow(list(p),[p[i]+sign*half*u[i] for i in range(3)],value,head,width)
                else:add_arrow([p[i]+sign*(head+half)*u[i] for i in range(3)],[p[i]+sign*head*u[i] for i in range(3)],value,head,width)
        else:
            if norm<=maximum*1e-10:continue
            add_arrow(list(p),[p[i]+length*direction[i]/maximum for i in range(3)],value,.25*size,.06*size)
    poly=vtkPolyData();poly.SetPoints(points);poly.SetLines(lines);poly.SetVerts(vertices);poly.GetPointData().SetScalars(values)
    mapper=vtkPolyDataMapper();mapper.SetInputData(poly);actor=vtkActor();actor.SetMapper(mapper);actor.GetProperty().SetColor(1,1,1);actor.GetProperty().LightingOff();actor.GetProperty().SetLineWidth(data.LineWidth);actor.GetProperty().SetPointSize(data.NodeSize);actor.PickableOff();return actor
