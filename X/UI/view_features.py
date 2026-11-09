"""Original viewport planes/pattern recipes adapted to VTK 9 Python bindings."""
import math
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkPlane
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkFiltersCore import vtkCutter
from vtkmodules.vtkFiltersExtraction import vtkExtractGeometry
from vtkmodules.vtkRenderingCore import vtkActor,vtkDataSetMapper
from System import Array,Double


def hatch(section,plane,spacing,index):
    # vtkControl/Tools/SectionViewHatch.cs and SectionViewCap.GetPlaneAxes.
    if section.GetNumberOfCells()==0 or spacing<=0:return None
    n=plane.GetNormal();length=math.sqrt(sum(v*v for v in n));n=[v/length for v in n];first=[1,0,0] if abs(n[0])<.9 else [0,1,0];projection=sum(a*b for a,b in zip(first,n));first=[a-projection*b for a,b in zip(first,n)];length=math.sqrt(sum(v*v for v in first));first=[v/length for v in first]
    second=[n[1]*first[2]-n[2]*first[1],n[2]*first[0]-n[0]*first[2],n[0]*first[1]-n[1]*first[0]];angle=math.radians(45 if index%2==0 else 135);spacing*=1+.5*((index//2)%3);normal=[-math.sin(angle)*a+math.cos(angle)*b for a,b in zip(first,second)];origin=plane.GetOrigin()
    distances=[sum((section.GetPoint(i)[a]-origin[a])*normal[a] for a in range(3)) for i in range(section.GetNumberOfPoints())]
    start=math.ceil(min(distances)/spacing);last=math.floor(max(distances)/spacing);count=last-start+1
    if count<=0 or count>2000:return None
    line=vtkPlane();line.SetOrigin(*origin);line.SetNormal(*normal);cutter=vtkCutter();cutter.SetCutFunction(line);cutter.SetInputData(section);cutter.GenerateCutScalarsOff();cutter.SetNumberOfContours(count)
    for i in range(count):cutter.SetValue(i,(start+i)*spacing)
    cutter.Update();return cutter.GetOutput()

class ViewFeatures:
    def __init__(self,presentation):self.p=presentation;self.copies=[];self.cuts=[];self.copy_sources=[];self.copy_values=[]
    def patterns(self,commands):
        # Apply each pattern to the complete preceding set, as the original nested copies do.
        sources=list(zip(self.p.scene.drawn,self.p.scene.actors));sources += [(None,edge) for edges in self.p.scene.edges_by_name.values() for edge in edges];sources+=[(None,prop) for prop in self.p.props if isinstance(prop,vtkActor)]
        matrices=[vtkTransform()]
        for command in commands:
            name=str(command.Name);args=command.Arguments;next_matrices=list(matrices)
            if name=='AddSymmetry':
                for parent in matrices:
                    t=vtkTransform();t.DeepCopy(parent);point=args[1];axis=int(args[0]);scale=[1,1,1];scale[axis]=-1;t.Translate(*point);t.Scale(*scale);t.Translate(*[-v for v in point]);next_matrices.append(t)
            elif name=='AddLinearPattern':
                for parent in matrices:
                    for i in range(1,int(args[1])):
                        t=vtkTransform();t.DeepCopy(parent);t.Translate(*[float(v)*i for v in args[0]]);next_matrices.append(t)
            elif name=='AddCircularPattern':
                for parent in matrices:
                    for i in range(1,int(args[3])):
                        t=vtkTransform();t.DeepCopy(parent);t.Translate(*args[0]);t.RotateWXYZ(float(args[2])*i,*args[1]);t.Translate(*[-v for v in args[0]]);next_matrices.append(t)
            matrices=next_matrices
        for original,actor in sources:
            for transform in matrices[1:]:
                copy=vtkActor();copy.ShallowCopy(actor);copy.SetUserTransform(transform);copy.PickableOff();self.p.add(copy);self.copies.append(copy)
                if original is not None:
                    data=original.Data;field=data.Geometry.Nodes.ResultField
                    if data.ColorContours and field is not None and field.IsValid():
                        # The original C# tensor/vector component transform owns scalar values.
                        from scene import grid,scalars
                        mapper=vtkDataSetMapper();mesh=grid(data.Geometry,original.SurfaceTopology);rotation=Array[Double]([transform.GetMatrix().GetElement(i,j) for i in range(3) for j in range(3)]);values=field.GetTransformedValues(rotation);scalars(mesh,values);self.copy_values.extend(float(v) for v in values if math.isfinite(v));mapper.SetInputData(mesh);mapper.SetLookupTable(self.p.table);mapper.SetScalarRange(self.p.table.GetTableRange());copy.SetMapper(mapper)
                self.copy_sources.append((original,actor,copy,transform))
        if self.copy_values:
            from contours import lookup
            state={str(c.Name):c.Arguments for c in commands}
            from vtkControl import vtkMaxColorSpectrum
            spectrum=state['SetScalarBarColorSpectrum'][0] if 'SetScalarBarColorSpectrum' in state else vtkMaxColorSpectrum()
            low=min(self.p.range[0],min(self.copy_values));high=max(self.p.range[1],max(self.copy_values))
            self.p.table.DeepCopy(lookup(spectrum,low,high))
            for mapper in self.p.scalar_mappers+[c.GetMapper() for c in self.copies if c.GetMapper().GetScalarVisibility()]:mapper.SetScalarRange(self.p.table.GetTableRange())
        self.section_commands=[c for c in commands if str(c.Name) in ['CreateSectionView','UpdateSectionView']]
        self.section()
        for maximum,name in [(False,'Min_Annotation'),(True,'Max_Annotation')]:
            if name in self.p.annotations:
                extreme=self.p.extreme(maximum)
                if extreme:self.p.update_annotation(name,*extreme)
    def extrema(self,frame=None):
        candidates=[]
        for original,actor,copy,transform in self.copy_sources:
            if original is None or not original.Data.ColorContours:continue
            data=original.Data;nodes=data.Geometry.NodesAnimation[frame] if frame is not None and data.Geometry.NodesAnimation is not None else data.Geometry.Nodes
            field=nodes.ResultField;rotation=Array[Double]([transform.GetMatrix().GetElement(i,j) for i in range(3) for j in range(3)])
            values=field.GetTransformedValues(rotation) if field is not None and field.IsValid() else nodes.Values
            if values is None:continue
            finite=[(float(v),i) for i,v in enumerate(values) if math.isfinite(v)]
            if not finite:continue
            ids=nodes.Ids if nodes.Ids is not None else data.Geometry.Nodes.Ids
            for value,index in [min(finite),max(finite)]:
                point=nodes.Coor[index] if nodes.Coor is not None else [nodes.FlatCoor[3*index+j] for j in range(3)]
                candidates.append((value,list(transform.TransformPoint(point)),int(ids[index]) if ids is not None else index))
        return candidates
    def section(self,frame=-1):
        if not self.section_commands:return
        from scene import grid
        scene=self.p.scene
        for actor in self.cuts:scene.renderer.RemoveActor(actor)
        self.cuts=[];args=self.section_commands[-1].Arguments;plane=vtkPlane();plane.SetOrigin(*args[0]);plane.SetNormal(*args[1])
        for index,(original,actor) in enumerate(zip(scene.drawn,scene.actors)):
            data=original.Data
            if not data.SectionViewPossible:continue
            actor.GetMapper().RemoveAllClippingPlanes();actor.GetMapper().AddClippingPlane(plane)
            for edge in scene.edges_by_name.get(str(data.Name),[]):edge.GetMapper().RemoveAllClippingPlanes();edge.GetMapper().AddClippingPlane(plane)
            volume=scene.volume_provider(str(data.Name),frame) if scene.volume_provider else None
            if volume is None:continue
            mesh=grid(volume)
            if args[4]:
                cut=vtkExtractGeometry();cut.SetImplicitFunction(plane);cut.ExtractInsideOff();cut.ExtractBoundaryCellsOff();cut.SetInputData(mesh);cut.Update();result=cut.GetOutput();actor.VisibilityOff()
                for edge in scene.edges_by_name.get(str(data.Name),[]):edge.VisibilityOff()
            else:
                cut=vtkCutter();cut.SetCutFunction(plane);cut.SetInputData(mesh);cut.GenerateCutScalarsOff();cut.Update();result=cut.GetOutput()
                if not data.HasVolumeCells and str(data.ActorRepresentation) in ['Solid','SolidAsShell']:
                    # Closed CAD/STL surfaces have a contour but no volume cells.
                    from vtkmodules.vtkFiltersGeneral import vtkContourTriangulator
                    from vtkmodules.vtkFiltersCore import vtkCleanPolyData
                    clean=vtkCleanPolyData();clean.SetInputData(result);clean.PointMergingOn();clean.ConvertLinesToPointsOff();clean.ConvertPolysToLinesOff();clean.ConvertStripsToPolysOff();clean.Update()
                    cap=vtkContourTriangulator();cap.SetInputData(clean.GetOutput());cap.Update();result=cap.GetOutput()
            mapper=vtkDataSetMapper();mapper.SetInputData(result);cap=vtkActor();cap.SetMapper(mapper);cap.GetProperty().DeepCopy(actor.GetProperty());cap.GetProperty().BackfaceCullingOff();cap.PickableOff()
            if data.ColorContours:mapper.SetLookupTable(self.p.table);mapper.SetScalarRange(self.p.table.GetTableRange())
            else:
                mapper.ScalarVisibilityOff()
                if not args[3].IsEmpty:color=args[3];cap.GetProperty().SetColor(color.R/255,color.G/255,color.B/255)
                elif args[2]:cap.GetProperty().SetColor(*[v+.3*(1-v) for v in actor.GetProperty().GetColor()])
            self.p.add(cap);self.cuts.append(cap)
            if args[5] and not args[4]:
                bounds=scene.renderer.ComputeVisiblePropBounds();spacing=math.sqrt(sum((bounds[i+1]-bounds[i])**2 for i in [0,2,4]))/100;lines=hatch(result,plane,spacing,index)
                if lines is not None:
                    mapper=vtkDataSetMapper();mapper.SetInputData(lines);mapper.ScalarVisibilityOff();line=vtkActor();line.SetMapper(mapper);line.GetProperty().SetColor(.1,.1,.1);line.PickableOff();self.p.add(line);self.cuts.append(line)
    def frame(self,index):
        # Actor geometry retains its mapper across frames; copies follow its points.
        for original,actor,copy,transform in self.copy_sources:
            if original is None:continue
            frames=original.Data.Geometry.NodesAnimation
            if frames is not None and copy.GetMapper() is not actor.GetMapper():
                from scene import coordinates,scalars
                mesh=copy.GetMapper().GetInput();nodes=frames[index];mesh.SetPoints(coordinates(nodes));field=nodes.ResultField
                if field is not None and field.IsValid():scalars(mesh,field.GetTransformedValues(Array[Double]([transform.GetMatrix().GetElement(i,j) for i in range(3) for j in range(3)])))
        self.section(index)
