"""Render transient original host commands with native VTK; retain engineering data."""
import math
from vtkmodules.vtkCommonCore import vtkPoints,vtkFloatArray
from vtkmodules.vtkRenderingCore import vtkTextActor,vtkActor,vtkPolyDataMapper
from vtkmodules.vtkRenderingAnnotation import vtkScalarBarActor,vtkCaptionActor2D
from contours import lookup
from glyphs import glyph_actor,plot_actor

class Presentation:
    def __init__(self,scene):
        self.scene=scene;self.props=[];self.commands=[];self.animated=[];self.scalar_mappers=[];self.frame=None;self.scalar_bar=None;self.status=None;self.annotations={}
    def clear(self):self.props=[];self.animated=[];self.scalar_mappers=[];self.scalar_bar=None;self.status=None
    def add(self,prop):self.scene.renderer.AddViewProp(prop);self.props.append(prop)
    def caption(self,text,position,color=(.08,.1,.13),size=14,leader=True):
        actor=vtkCaptionActor2D();actor.SetCaption(text);actor.SetAttachmentPoint(*position);actor.SetPosition(10,10);actor.BorderOff();actor.SetLeader(leader);actor.GetTextActor().SetTextScaleModeToNone();tp=actor.GetCaptionTextProperty();tp.SetFontSize(size);tp.SetColor(*color);tp.BoldOff();tp.ItalicOff();tp.ShadowOff();actor.PickableOff();actor.UseBoundsOff();self.add(actor);return actor
    def build(self,commands):
        self.commands=list(commands);state={str(c.Name):c.Arguments for c in self.commands}
        from vtkControl import vtkMaxColorSpectrum
        spectrum=state['SetScalarBarColorSpectrum'][0] if 'SetScalarBarColorSpectrum' in state else vtkMaxColorSpectrum()
        ranges=[]
        for original,actor in zip(self.scene.drawn,self.scene.actors):
            data=original.Data
            if data.Geometry.Nodes.Values is not None and data.ColorContours:
                self.scalar_mappers.append(actor.GetMapper())
                ranges.extend(float(v) for v in data.Geometry.Nodes.Values if math.isfinite(v))
            if data.Geometry.NodesAnimation is not None:self.animated.append((original,actor))
        self.plot_commands=[]
        for command in self.commands:
            name=str(command.Name);args=command.Arguments
            if name.startswith('AddOriented') or name=='AddSphereActor':self.add(glyph_actor(name,args,self.scene.renderer))
            elif name in ['AddVectorFieldActor','AddTensorFieldActor','AddAnimatedVectorFieldActor','AddAnimatedTensorFieldActor']:
                actor=plot_actor(name,args);self.add(actor);self.scalar_mappers.append(actor.GetMapper());self.plot_commands.append((name,args,actor));ranges.extend(float(v) for v in args[0].Geometry.Nodes.Values if math.isfinite(v))
            elif name=='AddCaptionActor':
                color=args[2];self.caption(str(args[1]),args[3],(color.R/255,color.G/255,color.B/255),int(14*args[5]),False)
            elif name=='AddLabelActor':
                color=args[3]
                for position,label in zip(args[1],args[2]):self.caption(str(label),position,(color.R/255,color.G/255,color.B/255),int(14*args[4]),False)
            elif name=='AddArrowWidget':
                if args[6]:
                    text=str(args[1]);position=args[3]
                    if str(args[0]) in ['Min_Annotation','Max_Annotation']:
                        extreme=self.extreme(str(args[0]).startswith('Max'))
                        if extreme is None:continue
                        text,position=extreme
                    self.annotations[str(args[0])]=self.caption(text,position)
            elif name=='AddMeasurementAnnotation' and args[6]:
                self.measurement(args)
            elif name=='AddCoordinateSystemSymbol':
                self.coordinate_system(args)
        if 'SetAnimationFrameData' in state:
            bounds=state['SetAnimationFrameData'][6]
            if bounds is not None and all(math.isfinite(v) for v in bounds):ranges.extend(bounds)
        self.range=(min(ranges),max(ranges)) if ranges else (0,1)
        self.table=lookup(spectrum,*self.range)
        for mapper in self.scalar_mappers:mapper.SetLookupTable(self.table);mapper.SetScalarRange(self.table.GetTableRange());mapper.ScalarVisibilityOn();mapper.SetColorModeToMapScalars();mapper.InterpolateScalarsBeforeMappingOn()
        if state.get('SetScalarBarVisibility',[False])[0] and self.scalar_mappers:
            self.scalar_bar=vtkScalarBarActor();self.scalar_bar.SetUnconstrainedFontSize(True);self.scalar_bar.SetLookupTable(self.table);fmt=str(state.get('SetScalarBarNumberFormat',['G4'])[0]);self.scalar_bar.SetLabelFormat('%.'+fmt[1:]+fmt[0].lower());text=state.get('SetScalarBarText',['','','','','']);self.scalar_bar.SetTitle('\n'.join(str(v) for v in list(text)[:4] if v));self.scalar_bar.SetNumberOfLabels(spectrum.NumberOfColors+1 if str(spectrum.Mode)=='Discrete' else 6);self.scalar_bar.SetPosition(.84,.15);self.scalar_bar.SetWidth(.14);self.scalar_bar.SetHeight(.7)
            for p in [self.scalar_bar.GetTitleTextProperty(),self.scalar_bar.GetLabelTextProperty()]:p.SetColor(.08,.1,.13);p.ItalicOff();p.ShadowOff();p.SetFontSize(13)
            self.scalar_bar.SetDrawBackground(bool(state.get('DrawLegendBackground',[False])[0]));self.scalar_bar.SetDrawFrame(bool(state.get('DrawLegendBorder',[False])[0]));self.scalar_bar.GetBackgroundProperty().SetColor(1,1,1);self.add(self.scalar_bar)
        if state.get('SetStatusBlockVisibility',[False])[0] and 'SetStatusBlock' in state:
            a=state['SetStatusBlock'];text=f'{a[0]}\n{a[6]}: {a[2]} {a[3]}\nStep {a[7]}, increment {a[8]}\nDeformation: {a[4]}, scale {a[5]}'
            self.status=vtkTextActor();self.status.SetInput(text);self.status.SetPosition(12,12);self.status.GetTextProperty().SetFontSize(14);self.status.GetTextProperty().SetColor(.08,.1,.13);self.status.GetTextProperty().SetBackgroundColor(1,1,1);self.status.GetTextProperty().SetBackgroundOpacity(1 if state.get('DrawStatusBlockBackground',[False])[0] else 0);self.status.GetTextProperty().SetFrame(bool(state.get('DrawStatusBlockBorder',[False])[0]));self.add(self.status)
        from view_features import ViewFeatures
        self.features=ViewFeatures(self);self.features.patterns(self.commands)
    def extreme(self,maximum,frame=None):
        candidates=[]
        for original in self.scene.drawn:
            data=original.Data
            if not data.ColorContours:continue
            nodes=data.Geometry.ExtremeNodesAnimation[frame] if frame is not None and data.Geometry.ExtremeNodesAnimation is not None else data.Geometry.ExtremeNodes
            if nodes is not None and nodes.Values is not None:
                i=1 if maximum else 0;candidates.append((float(nodes.Values[i]),list(nodes.Coor[i]),int(nodes.Ids[i])))
        if hasattr(self,'features'):candidates.extend(self.features.extrema(frame))
        if not candidates:return None
        value,position,node=(max if maximum else min)(candidates,key=lambda p:p[0])
        return ('Max' if maximum else 'Min')+f': {value:.6g} (node {node})',position
    def update_annotation(self,name,text,position):
        actor=self.annotations.get(str(name))
        if actor is None:return
        if text is not None:actor.SetCaption(str(text))
        if position is not None:actor.SetAttachmentPoint(*position)
    def measurement(self,args):
        from scene import grid
        from vtkmodules.vtkRenderingCore import vtkDataSetMapper
        for data in [args[1],args[2]]:
            if data is None or data.Geometry.Nodes.Coor is None:continue
            mapper=vtkDataSetMapper();mapper.SetInputData(grid(data.Geometry));mapper.ScalarVisibilityOff()
            actor=vtkActor();actor.SetMapper(mapper);actor.GetProperty().SetColor(data.Color.R/255,data.Color.G/255,data.Color.B/255);actor.GetProperty().SetPointSize(max(6,data.NodeSize));actor.GetProperty().SetLineWidth(max(2,data.LineWidth));actor.PickableOff();self.add(actor)
        if args[3] is not None and len(args[3]):
            from System import Array,Double
            from vtkControl import vtkMaxActorData
            data=vtkMaxActorData();data.Geometry.Nodes.Coor=args[3];data.Geometry.Nodes.Normals=args[4];data.Color=args[2].Color
            self.add(glyph_actor('AddOrientedArrowsActor',[data,args[5],False,1],self.scene.renderer))
    def coordinate_system(self,args):
        from vtkControl import vtkMaxActorData
        # Controller supplies the axis basis, rather than inferring it in Qt.
        from System import Array,Double
        for direction,label,color in zip(args[1],args[2],[(220,30,30),(30,170,30),(30,60,220)]):
            from System.Drawing import Color
            data=vtkMaxActorData();data.Geometry.Nodes.Coor=Array[Array[Double]]([Array[Double](args[0])]);data.Geometry.Nodes.Normals=Array[Array[Double]]([Array[Double](direction)]);data.Color=Color.FromArgb(*color)
            self.add(glyph_actor('AddOrientedArrowsActor',[data,args[3],False,1],self.scene.renderer));self.caption(str(label),args[0],tuple(v/255 for v in color))
    def set_frame(self,index):
        self.frame=index
        from scene import coordinates,scalars
        for original,actor in self.animated:
            data=original.Data;nodes=data.Geometry.NodesAnimation[index];mesh=actor.GetMapper().GetInput();mesh.SetPoints(coordinates(nodes));scalars(mesh,nodes.Values);mesh.Modified()
            for edge in self.scene.edges_by_name.get(str(data.Name),[]):
                source=data.ModelEdgesToDraw or data.ModelEdges
                if source is not None and source.NodesAnimation is not None:edge.GetMapper().GetInput().SetPoints(coordinates(source.NodesAnimation[index]));edge.GetMapper().GetInput().Modified()
        for name,args,actor in self.plot_commands:
            frames=args[0].Geometry.NodesAnimation
            if frames is not None:
                new=plot_actor(name,args,frames[index]);mapper=new.GetMapper();mapper.SetLookupTable(self.table);mapper.SetScalarRange(self.table.GetTableRange());actor.SetMapper(mapper)
        for maximum,name in [(False,'Min_Annotation'),(True,'Max_Annotation')]:
            if name in self.annotations:
                extreme=self.extreme(maximum,index)
                if extreme:self.update_annotation(name,*extreme)
        self.features.frame(index)
        state={str(c.Name):c.Arguments for c in self.commands}
        if self.status is not None and 'SetAnimationFrameData' in state:
            a=state['SetAnimationFrameData'];self.status.SetInput(f'Frame {index+1}/{len(a[0])}\nTime {a[0][index]}\nStep {a[1][index]}, increment {a[2][index]}\nScale {a[5][index]}')
