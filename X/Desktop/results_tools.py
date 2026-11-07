"""Result presentation: stored-field deformation, animation, original DAT histories.

No mesh/FRD/DAT parsing or engineering result calculation is implemented here.
Coordinates in the VTK display use x + scale*u; authoritative scene data stays
unchanged. Mode amplitudes retain the original solver's normalization.
"""
import csv
import math
import os
from pathlib import Path
import tempfile
from PyQt6 import QtCore,QtGui,QtWidgets
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from vtkmodules.vtkRenderingCore import vtkActor,vtkDataSetMapper


def result_command():
    import sys
    from jobs import ROOT,resources
    return ([str(resources()/'hosts/results/PrePoMaxX.InspectResults')] if getattr(sys,'frozen',False) else
        ['dotnet',str(ROOT/'X/Results/Inspect/bin/Release/net10.0/PrePoMaxX.InspectResults.dll')])


def read_histories(path):
    from viewport import run_reader
    return run_reader([*result_command(),'inspect-dat',str(path)])


def export_histories(path,histories):
    """Atomic new-file publication of original values and complete series identity."""
    path=Path(path);temporary=None
    try:
        with tempfile.NamedTemporaryFile('w',encoding='utf-8',newline='',dir=path.parent,prefix='.prepomaxx-history-',delete=False) as stream:
            temporary=Path(stream.name);writer=csv.writer(stream)
            writer.writerow(['step','set','field','component','node_or_element','integration_point','time','value','unit','local'])
            for h in histories:
                for time,value in zip(h['time'],h['values']):
                    writer.writerow([h['StepId'],h['SetName'],h['FieldName'],h['ComponentName'],h['Id'],h['IntegrationPoint'],time,value,h.get('Unit') or '',h.get('Local',False)])
            stream.flush();os.fsync(stream.fileno())
        os.link(temporary,path)
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)


class HistoryTable(QtCore.QAbstractTableModel):
    def __init__(self,history,parent=None):super().__init__(parent);self.history=history
    def rowCount(self,parent=QtCore.QModelIndex()):return 0 if parent.isValid() else len(self.history['time'])
    def columnCount(self,parent=QtCore.QModelIndex()):return 0 if parent.isValid() else 2
    def data(self,index,role=QtCore.Qt.ItemDataRole.DisplayRole):
        if index.isValid() and role==QtCore.Qt.ItemDataRole.DisplayRole:
            return format(self.history['time' if index.column()==0 else 'values'][index.row()],'.16g')
    def headerData(self,section,orientation,role=QtCore.Qt.ItemDataRole.DisplayRole):
        if role==QtCore.Qt.ItemDataRole.DisplayRole:return ['Time (as stored)','Value (as stored)'][section] if orientation==QtCore.Qt.Orientation.Horizontal else str(section+1)


class HistoryPlot(QtWidgets.QWidget):
    def __init__(self,parent=None):super().__init__(parent);self.history=None;self.setMinimumSize(420,260)
    def set_history(self,history):self.history=history;self.update()
    def paintEvent(self,event):
        painter=QtGui.QPainter(self);painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(),QtGui.QColor('#fbfcfe'));painter.setPen(QtGui.QColor('#182536'))
        if not self.history:return
        h=self.history;xs=h['time'];ys=h['values']
        if not xs:return
        area=QtCore.QRectF(90,35,max(1,self.width()-120),max(1,self.height()-100))
        xmin,xmax=min(xs),max(xs);ymin,ymax=min(ys),max(ys)
        dx=xmax-xmin or max(1,abs(xmin))*.1;dy=ymax-ymin or max(1,abs(ymin))*.1
        xmin-=dx*.03;xmax+=dx*.03;ymin-=dy*.05;ymax+=dy*.05
        dx=xmax-xmin;dy=ymax-ymin
        painter.drawText(12,22,f"{h['FieldName']} / {h['ComponentName']} · ID {h['Id']} · values as stored")
        for i in range(5):
            fraction=i/4;x=area.left()+fraction*area.width();y=area.bottom()-fraction*area.height()
            painter.setPen(QtGui.QColor('#d9dfe7'));painter.drawLine(QtCore.QPointF(x,area.top()),QtCore.QPointF(x,area.bottom()));painter.drawLine(QtCore.QPointF(area.left(),y),QtCore.QPointF(area.right(),y))
            painter.setPen(QtGui.QColor('#182536'));painter.drawText(QtCore.QRectF(x-45,area.bottom()+8,90,22),QtCore.Qt.AlignmentFlag.AlignCenter,format(xmin+fraction*dx,'.5g'))
            painter.drawText(QtCore.QRectF(2,y-12,80,24),QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignVCenter,format(ymin+fraction*dy,'.5g'))
        painter.drawText(QtCore.QRectF(area.left(),area.bottom()+36,area.width(),20),QtCore.Qt.AlignmentFlag.AlignCenter,'Time (as stored)')
        painter.save();painter.setClipRect(area)
        points=QtGui.QPolygonF([QtCore.QPointF(area.left()+(x-xmin)/dx*area.width(),area.bottom()-(y-ymin)/dy*area.height()) for x,y in zip(xs,ys)])
        painter.setPen(QtGui.QPen(QtGui.QColor('#1263ac'),2));painter.drawPolyline(points)
        if len(points)==1:painter.drawEllipse(points[0],3,3)
        painter.restore()


class HistoryDialog(QtWidgets.QDialog):
    def __init__(self,parent,path,snapshot):
        super().__init__(parent);self.path=Path(path);self.snapshot=snapshot;self.setWindowTitle('Original result histories — '+self.path.name);self.resize(1050,650)
        layout=QtWidgets.QVBoxLayout(self);layout.addWidget(QtWidgets.QLabel('Original DAT data · select a series to inspect its graph and values. Quantities and units remain as stored.'))
        self.series=QtWidgets.QComboBox();self.series.setObjectName('historySeries')
        for h in snapshot['histories']:
            point='' if h['IntegrationPoint'] is None else f" · integration point {h['IntegrationPoint']}"
            self.series.addItem(f"Step {h['StepId']} · {h['SetName']} · {h['FieldName']} / {h['ComponentName']} · ID {h['Id']}{point}")
        self.series.setEditable(True);self.series.setInsertPolicy(QtWidgets.QComboBox.InsertPolicy.NoInsert);self.series.completer().setFilterMode(QtCore.Qt.MatchFlag.MatchContains)
        layout.addWidget(self.series);splitter=QtWidgets.QSplitter();self.plot=HistoryPlot();self.table=QtWidgets.QTableView();self.table.setObjectName('historyValues');self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        splitter.addWidget(self.plot);splitter.addWidget(self.table);splitter.setSizes([650,350]);layout.addWidget(splitter,1)
        buttons=QtWidgets.QHBoxLayout();selected=QtWidgets.QPushButton('Export selected CSV…');all_series=QtWidgets.QPushButton('Export all CSV…');close=QtWidgets.QPushButton('Close')
        buttons.addWidget(selected);buttons.addWidget(all_series);buttons.addStretch();buttons.addWidget(close);layout.addLayout(buttons)
        selected.clicked.connect(lambda:self.save(False));all_series.clicked.connect(lambda:self.save(True));close.clicked.connect(self.accept);self.series.currentIndexChanged.connect(self.select);self.select(0)
    def select(self,index):
        if 0<=index<len(self.snapshot['histories']):
            history=self.snapshot['histories'][index];self.plot.set_history(history);old=self.table.model();self.table.setModel(HistoryTable(history,self.table))
            if old is not None:old.deleteLater()
    def save(self,all_series):
        path,_=QtWidgets.QFileDialog.getSaveFileName(self,'Export original history values',str(self.path.with_suffix('.csv')),'CSV (*.csv)')
        if path:
            try:export_histories(path,self.snapshot['histories'] if all_series else [self.snapshot['histories'][self.series.currentIndex()]])
            except (OSError,ValueError) as error:QtWidgets.QMessageBox.critical(self,'Cannot export histories',str(error))


class ResultsTools:
    def __init__(self,window):
        self.window=window;self.phase=1.;self.tick_index=0;self.timer=QtCore.QTimer(window);self.timer.setInterval(100);self.timer.timeout.connect(self.tick)
        window.addToolBarBreak();self.toolbar=window.addToolBar('Result shape / histories');self.toolbar.setVisible(False)
        self.deformed=QtWidgets.QCheckBox('Deformed');self.deformed.setObjectName('deformedShape');self.toolbar.addWidget(self.deformed)
        self.scale=QtWidgets.QDoubleSpinBox();self.scale.setObjectName('deformationScale');self.scale.setRange(-1e12,1e12);self.scale.setDecimals(6);self.scale.setValue(1);self.scale.setPrefix('Scale ');self.toolbar.addWidget(self.scale)
        self.outline=QtWidgets.QCheckBox('Undeformed outline');self.toolbar.addWidget(self.outline)
        self.animation=QtWidgets.QComboBox();self.animation.addItems(['Increment sequence','Current shape cycle']);self.toolbar.addWidget(self.animation)
        self.play=self.toolbar.addAction('Play');self.play.setCheckable(True);self.play.toggled.connect(self.toggle)
        self.history_action=self.toolbar.addAction('Histories…');self.history_action.triggered.connect(self.open_histories)
        self.reference=vtkActor();self.reference_mapper=vtkDataSetMapper();self.reference.SetMapper(self.reference_mapper);self.reference_mapper.ScalarVisibilityOff();self.reference.GetProperty().SetRepresentationToWireframe();self.reference.GetProperty().SetColor(.6,.65,.7);self.reference.SetVisibility(False);self.reference.PickableOff();window.renderer.AddActor(self.reference)
        self.deformed.toggled.connect(self.apply);self.scale.valueChanged.connect(self.apply);self.outline.toggled.connect(self.apply)
        self.animation.currentIndexChanged.connect(lambda:self.toggle(False))
    def on_scene(self):
        self.toggle(False);self.toolbar.setVisible(bool(self.window.scene.get('fields')))
        self.reference_grid=vtkUnstructuredGrid();self.reference_grid.DeepCopy(self.window.grid);self.reference_mapper.SetInputData(self.reference_grid)
        self.apply()
    def selected_displacement(self):
        w=self.window;frame=w.frames.currentData()
        return next((f for f in (w.scene or {}).get('fields',[]) if f['name']=='DISP' and (f['stepId'],f['incrementId'],f['time'])==tuple(frame or ())),None)
    def apply(self,*args):
        w=self.window
        if w.scene is None or not hasattr(w,'grid'):return
        displacement=self.selected_displacement();available=displacement is not None
        self.deformed.setEnabled(available);self.scale.setEnabled(available);self.play.setEnabled(available or w.frames.count()>1)
        points=vtkPoints();points.SetDataTypeToDouble();scale=self.scale.value()*self.phase if self.deformed.isChecked() and available else 0
        order={identity:i for i,identity in enumerate(w.scene.get('nodeIdsInValueOrder',[]))}
        for node in w.scene['nodes']:
            coords=[node[a] for a in ('x','y','z')]
            if scale:
                i=order[node['id']];coords=[coords[d]+scale*displacement['components'][f'U{d+1}'][i] for d in range(3)]
            points.InsertNextPoint(*coords)
        w.grid.SetPoints(points);w.grid.Modified();self.reference.SetVisibility(bool(self.outline.isChecked() and scale))
        if (w.scene or {}).get('fields'):
            mode=(displacement or {}).get('stepType') in ('Frequency','Buckling')
            w.statusBar().showMessage(f"{len(w.scene['nodes'])} nodes · display scale {scale:g} · values as stored"+(' · eigenmode amplitude is arbitrary' if mode else ''))
        if w.isVisible():w.vtk.render()
    def toggle(self,playing):
        if playing:
            self.tick_index=0;self.timer.start();self.play.setText('Pause')
        else:
            self.timer.stop();self.phase=1.;self.play.setText('Play')
            with QtCore.QSignalBlocker(self.play):self.play.setChecked(False)
            self.apply()
    def tick(self):
        w=self.window
        if not w.isVisible():self.toggle(False);return
        if self.animation.currentIndex()==0:
            w.frames.setCurrentIndex((w.frames.currentIndex()+1)%max(1,w.frames.count()))
        else:
            self.tick_index+=1;self.phase=math.sin(2*math.pi*self.tick_index/32);self.apply()
    def open_histories(self):
        w=self.window;candidate=w.current_path.with_suffix('.dat') if w.current_path else None
        if candidate is None or not candidate.is_file():
            path,_=QtWidgets.QFileDialog.getOpenFileName(w,'Open original DAT histories','','CalculiX DAT (*.dat)')
            if not path:return
            candidate=Path(path)
        try:
            self.toggle(False);snapshot=read_histories(candidate)
            if not snapshot['histories']:raise ValueError('The original reader returned no supported history series.')
            dialog=HistoryDialog(w,candidate,snapshot);dialog.exec()
        except (OSError,ValueError) as error:QtWidgets.QMessageBox.critical(w,'Cannot open histories',str(error))
