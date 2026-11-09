"""Plot original XYPlotPanelState curves/settings; no engineering interpolation."""
import csv,math
from PyQt6 import QtCore,QtGui,QtWidgets
from PrePoMaxX.UI import PlotSession
from CaeResults import HistoryResultData
from application_widgets import SheetDialog

class XYCanvas(QtWidgets.QWidget):
    def __init__(self,parent=None):super().__init__(parent);self.state=None;self.setMinimumSize(260,200);self.setMouseTracking(True);self.drag=None
    def paintEvent(self,event):
        p=QtGui.QPainter(self);p.fillRect(self.rect(),QtGui.QColor('white'));p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        if self.state is None:return
        s=self.state.Settings;p.setFont(QtGui.QFont(s.GetFontFamilyName(),round(s.FontSize)));area=QtCore.QRectF(75,20,max(1,self.width()-105),max(1,self.height()-90));self.area=area
        curves=[c for c in self.state.Curves if c.Settings.Visible];points=[(float(x),float(y)) for c in curves for x,y in zip(c.XValues,c.YValues) if math.isfinite(x) and math.isfinite(y)]
        x0=min((x for x,y in points),default=0) if s.XAxisAutoScale else s.XAxisMin;x1=max((x for x,y in points),default=1) if s.XAxisAutoScale else s.XAxisMax
        y0=min((y for x,y in points),default=0) if s.YAxisAutoScale else s.YAxisMin;y1=max((y for x,y in points),default=1) if s.YAxisAutoScale else s.YAxisMax
        if x0==x1:x1=x0+1
        if y0==y1:y1=y0+1
        self.bounds=(x0,x1,y0,y1);p.setPen(QtGui.QColor('#333333'));p.drawRect(area)
        p.drawText(QtCore.QRectF(area.left(),area.bottom()+45,area.width(),30),QtCore.Qt.AlignmentFlag.AlignCenter,s.XAxisTitle)
        p.save();p.translate(18,area.center().y());p.rotate(-90);p.drawText(QtCore.QRectF(-area.height()/2,-15,area.height(),30),QtCore.Qt.AlignmentFlag.AlignCenter,s.YAxisTitle);p.restore()
        for i in range(6):
            x=area.left()+i*area.width()/5;y=area.bottom()-i*area.height()/5;p.drawText(QtCore.QRectF(x-40,area.bottom()+5,80,30),QtCore.Qt.AlignmentFlag.AlignHCenter,f'{x0+(x1-x0)*i/5:.4g}');p.drawText(QtCore.QRectF(20,y-10,50,25),QtCore.Qt.AlignmentFlag.AlignRight,f'{y0+(y1-y0)*i/5:.4g}')
        def pos(x,y):return QtCore.QPointF(area.left()+(x-x0)/(x1-x0)*area.width(),area.bottom()-(y-y0)/(y1-y0)*area.height())
        p.save();p.setClipRect(area)
        for c in curves:
            v=c.Settings;color=QtGui.QColor(v.Color.R,v.Color.G,v.Color.B);style={'Solid':QtCore.Qt.PenStyle.SolidLine,'Dash':QtCore.Qt.PenStyle.DashLine,'Dot':QtCore.Qt.PenStyle.DotLine,'DashDot':QtCore.Qt.PenStyle.DashDotLine,'DashDotDot':QtCore.Qt.PenStyle.DashDotDotLine}.get(str(v.LineStyle),QtCore.Qt.PenStyle.SolidLine);p.setPen(QtGui.QPen(color,v.LineWidth,style));path=QtGui.QPainterPath();started=False
            for x,y in zip(c.XValues,c.YValues):
                if not math.isfinite(x) or not math.isfinite(y):started=False;continue
                point=pos(x,y)
                if started:path.lineTo(point)
                else:path.moveTo(point);started=True
                if s.ShowPointSymbols:p.drawEllipse(point,2.5,2.5)
            p.drawPath(path)
        p.restore()
        if s.ShowLegend:
            position=str(s.LegendPosition);names=[c.Settings.Name.replace('\n',' ') for c in curves];width=max((p.fontMetrics().horizontalAdvance(n) for n in names),default=0)+25;height=len(names)*(p.fontMetrics().height()+3)+10
            left=area.left()+8 if 'Left' in position else area.center().x()-width/2 if 'Center' in position else area.right()-width-8;top=area.bottom()-height-8 if 'Bottom' in position else area.top()+8
            p.fillRect(QtCore.QRectF(left,top,width,height),QtGui.QColor(255,255,255,220))
            for i,(c,name) in enumerate(zip(curves,names)):p.setPen(QtGui.QColor(c.Settings.Color.R,c.Settings.Color.G,c.Settings.Color.B));p.drawText(QtCore.QPointF(left+8,top+8+(i+1)*(p.fontMetrics().height()+3)-3),name)
    def wheelEvent(self,event):
        if self.state is None or not hasattr(self,'bounds'):return
        factor=.8 if event.angleDelta().y()>0 else 1.25;x0,x1,y0,y1=self.bounds;s=self.state.Settings;s.XAxisAutoScale=False;s.YAxisAutoScale=False
        s.XAxisMin=(x0+x1)/2-(x1-x0)*factor/2;s.XAxisMax=(x0+x1)/2+(x1-x0)*factor/2;s.YAxisMin=(y0+y1)/2-(y1-y0)*factor/2;s.YAxisMax=(y0+y1)/2+(y1-y0)*factor/2;self.update()
    def mousePressEvent(self,event):
        if hasattr(self,'bounds'):self.drag=(event.position(),self.bounds)
    def mouseMoveEvent(self,event):
        if self.drag is None or self.state is None:return
        point,b=self.drag;d=event.position()-point;dx=d.x()/self.area.width()*(b[1]-b[0]);dy=d.y()/self.area.height()*(b[3]-b[2]);s=self.state.Settings;s.XAxisAutoScale=False;s.YAxisAutoScale=False;s.XAxisMin=b[0]-dx;s.XAxisMax=b[1]-dx;s.YAxisMin=b[2]+dy;s.YAxisMax=b[3]+dy;self.update()
    def mouseReleaseEvent(self,event):self.drag=None
    def mouseDoubleClickEvent(self,event):
        if self.state:self.state.Settings.XAxisAutoScale=True;self.state.Settings.YAxisAutoScale=True;self.update()

class PlotPanel(QtWidgets.QWidget):
    def __init__(self,owner):
        super().__init__(owner);self.owner=owner;self.session=PlotSession(owner.controller);layout=QtWidgets.QVBoxLayout(self);self.tabs=QtWidgets.QTabWidget();self.tabs.setTabsClosable(True);layout.addWidget(self.tabs);self.tabs.tabCloseRequested.connect(self.remove)
        row=QtWidgets.QHBoxLayout()
        for label,cb in [('New plot',self.add),('Add history…',self.history),('Add amplitude…',self.amplitude),('Plot settings…',self.settings),('Curve settings…',self.curve_settings),('Remove curve…',self.remove_curve),('Export data…',self.export),('Copy image',self.copy_image)]:
            button=QtWidgets.QPushButton(label);button.clicked.connect(lambda checked=False,f=cb:owner.guard(f));row.addWidget(button)
        layout.addLayout(row);self.add()
    def current(self):return self.tabs.currentIndex()
    def rebuild(self):
        selected=self.session.State.SelectedPlotIndex;self.tabs.clear()
        for i,state in enumerate(self.session.State.Plots):
            canvas=XYCanvas(self);canvas.state=state;self.tabs.addTab(canvas,'Plot '+str(i+1))
        self.tabs.setCurrentIndex(max(0,min(selected,self.tabs.count()-1)))
    def add(self):self.session.AddPlot();self.rebuild()
    def remove(self,index):self.session.RemovePlot(index);self.rebuild()
    def history(self):
        c=self.owner.controller
        if not c.ResultsInitialized:raise ValueError('Open results first.')
        sources=[]
        for h in c.GetHistoryResultSets():
            for field in h.Fields.Values:
                for component in field.Components.Values:sources.append((h.Name+' / '+field.Name+' / '+component.Name,HistoryResultData(h.Name,field.Name,component.Name)))
        if not sources:return
        choice,ok=QtWidgets.QInputDialog.getItem(self,'Add history','Source',[s[0] for s in sources],0,False)
        if ok:
            if self.current()<0:self.add()
            limited=self.session.AddHistory(self.current(),next(s[1] for s in sources if s[0]==choice));self.rebuild()
            if limited:raise ValueError('The maximum curve count was reached; additional curves were not added.')
    def amplitude(self):
        choice,ok=QtWidgets.QInputDialog.getItem(self,'Add amplitude','Amplitude',list(self.owner.controller.GetAmplitudeNames()),0,False)
        if ok:
            if self.current()<0:self.add()
            limited=self.session.AddAmplitude(self.current(),choice);self.rebuild()
            if limited:raise ValueError('The maximum curve count was reached.')
    def settings(self):
        if self.current()>=0:SheetDialog(self,'XY plot settings',self.session.Properties(self.current())).exec();self.rebuild()
    def choose_curve(self):
        if self.current()<0:return -1
        curves=self.session.State.Plots[self.current()].Curves
        name,ok=QtWidgets.QInputDialog.getItem(self,'Curve','Curve',[str(i+1)+': '+c.Settings.Name for i,c in enumerate(curves)],0,False)
        return int(name.split(':')[0])-1 if ok else -1
    def curve_settings(self):
        index=self.choose_curve()
        if index>=0:SheetDialog(self,'Curve settings',self.session.CurveProperties(self.current(),index)).exec();self.rebuild()
    def remove_curve(self):
        index=self.choose_curve()
        if index>=0:self.session.RemoveCurve(self.current(),index);self.rebuild()
    def export(self):
        if self.current()<0:return
        path,_=QtWidgets.QFileDialog.getSaveFileName(self,'Export plot data','','CSV (*.csv)')
        if path:
            curves=list(self.session.State.Plots[self.current()].Curves)
            with open(path,'w',newline='') as f:
                writer=csv.writer(f);writer.writerow([label for c in curves for label in [c.Settings.Name+' - X',c.Settings.Name+' - Y']])
                for row in range(max((len(c.XValues) for c in curves),default=0)):writer.writerow([value for c in curves for value in ([c.XValues[row],c.YValues[row]] if row<len(c.XValues) else ['',''])])
    def copy_image(self):
        if self.current()>=0:QtWidgets.QApplication.clipboard().setPixmap(self.tabs.currentWidget().grab())
