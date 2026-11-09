"""Tables and plots present original result history and monitor parser data."""
import math
from PyQt6 import QtCore,QtGui,QtWidgets
from System import Array,String
from CaeResults import HistoryResultData
from CaeJob import CalculixMonitorDataParser

class CurvePlot(QtWidgets.QWidget):
    def __init__(self,parent=None):super().__init__(parent);self.curves=[];self.setMinimumHeight(210)
    def set_curves(self,curves):self.curves=curves;self.update()
    def paintEvent(self,event):
        painter=QtGui.QPainter(self);painter.fillRect(self.rect(),QtGui.QColor('white'));painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        area=QtCore.QRectF(65,15,max(1,self.width()-90),max(1,self.height()-60));painter.setPen(QtGui.QColor('#333333'));painter.drawRect(area)
        curves=[(name,[(float(x),float(y)) for x,y in zip(xs,ys) if math.isfinite(x) and math.isfinite(y)]) for name,xs,ys in self.curves]
        points=[p for _,values in curves for p in values]
        if not points:return
        x0=min(x for x,y in points);x1=max(x for x,y in points);y0=min(y for x,y in points);y1=max(y for x,y in points)
        def pos(x,y):return QtCore.QPointF(area.left()+(x-x0)/(x1-x0 or 1)*area.width(),area.bottom()-(y-y0)/(y1-y0 or 1)*area.height())
        painter.drawText(5,30,f'{y1:.5g}');painter.drawText(5,int(area.bottom()),f'{y0:.5g}');painter.drawText(int(area.left()),self.height()-5,f'{x0:.5g}');painter.drawText(int(area.right())-50,self.height()-5,f'{x1:.5g}')
        for index,(name,values) in enumerate(curves):
            painter.setPen(QtGui.QPen(QtGui.QColor.fromHsv(index*67%360,200,180),1.5));path=QtGui.QPainterPath()
            for i,(x,y) in enumerate(values):
                if i:path.lineTo(pos(x,y))
                else:path.moveTo(pos(x,y))
            painter.drawPath(path);painter.drawText(int(area.left())+8,32+index*16,name)

def show_history(owner,name):
    c=owner.controller;history=c.CurrentResult.GetHistory().Sets[name]
    dialog=QtWidgets.QDialog(owner);dialog.setWindowTitle('History — '+name);dialog.resize(850,560);layout=QtWidgets.QVBoxLayout(dialog)
    source=QtWidgets.QComboBox();sources=[]
    for field in history.Fields.Values:
        for component in field.Components.Values:sources.append(HistoryResultData(name,field.Name,component.Name));source.addItem(field.Name+' / '+component.Name)
    layout.addWidget(source);split=QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical);table=QtWidgets.QTableWidget();plot=CurvePlot();split.addWidget(table);split.addWidget(plot);layout.addWidget(split)
    def changed(index):
        data=owner.results.History(sources[index]);columns,rows=data.Columns,data.Rows
        table.setColumnCount(len(columns));table.setRowCount(len(rows));table.setHorizontalHeaderLabels(list(columns))
        for r,row in enumerate(rows):
            for col,value in enumerate(row):
                item=QtWidgets.QTableWidgetItem(str(value or '') if value is None else str(value));item.setFlags(item.flags()&~QtCore.Qt.ItemFlag.ItemIsEditable);table.setItem(r,col,item)
        curves=[]
        for col in range(1,len(columns)):
            points=[]
            for row in rows:
                try:points.append((float(row[0]),float(row[col])))
                except (ValueError,TypeError):continue
            curves.append((str(columns[col]),[p[0] for p in points],[p[1] for p in points]))
        plot.set_curves(curves)
    source.currentIndexChanged.connect(changed)
    if sources:changed(0)
    button=QtWidgets.QPushButton('Export history…')
    def export():
        path,_=QtWidgets.QFileDialog.getSaveFileName(dialog,'Export history','','CSV (*.csv)')
        if path:
            from PrePoMax import ExportHistoryResultSetFileProperties
            properties=ExportHistoryResultSetFileProperties();properties.FileName=path;properties.HistoryOutputNames=Array[String]([name]);c.ExportResultHistoryOutputCommand(properties)
    button.clicked.connect(lambda:owner.guard(export));layout.addWidget(button);dialog.show();return dialog

class MonitorPlot(CurvePlot):
    def update_job(self,job,kind):
        if kind=='Progress':
            d=CalculixMonitorDataParser.ParseStatus(job.StatusFileData);curves=[('Increment time',d.TotalTimes,d.IncrementTimes),('Iterations',d.TotalTimes,d.IterationCounts)]
        elif kind=='Convergence plot':
            d=CalculixMonitorDataParser.ParseConvergence(job.ConvergenceFileData);curves=[('Residual force',d.RecordNumbers,d.ResidualForces),('Displacement correction',d.RecordNumbers,d.DisplacementCorrections),('Residual flux',d.RecordNumbers,d.ResidualFluxes),('Temperature correction',d.RecordNumbers,d.TemperatureCorrections)]
        else:
            d=job.GetEnergyData();curves=[('External work',d.TotalTimes,d.ExternalWorks),('Internal energy',d.TotalTimes,d.InternalEnergies),('Kinetic energy',d.TotalTimes,d.KineticEnergies),('Contact energy',d.TotalTimes,d.ContactEnergies)]
        self.set_curves(curves)
