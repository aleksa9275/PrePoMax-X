"""Qt controls over original C4 view objects and job monitor data."""
from PyQt6 import QtCore,QtWidgets
from System import Array,Double
from CaeResults import ResultHistoryOutputFromTable
from authoring_widgets import PropertyDialog,message

class ResultsDialog(PropertyDialog):
    def __init__(self,parent,family,name=None):
        self.matrix=None
        super().__init__(parent,family,name=name,rule=parent.results.Edit(family,name))
        self.setWindowModality(QtCore.Qt.WindowModality.NonModal)

    def rebuild(self):
        # Preserve pending cells when a property change rebuilds the original view.
        if self.matrix is not None:
            try:self.store_matrix()
            except (ValueError,AttributeError) as error:
                self.error.setText('Complete the numeric table cells before changing its layout.');return
        # A jagged numeric array is edited as a numeric table, not object descriptors.
        self.matrix=None
        super().rebuild()
        if isinstance(self.rule.Item,ResultHistoryOutputFromTable):
            item=self.rule.Item;self.matrix=QtWidgets.QTableWidget()
            self.matrix.setColumnCount(item.NumberOfYColumns+1)
            self.matrix.setHorizontalHeaderLabels(['X']+[item.GetYColumnName(i) for i in range(item.NumberOfYColumns)])
            self.matrix.setRowCount(len(item.DataPoints))
            for row,values in enumerate(item.DataPoints):
                for column,value in enumerate(values):self.matrix.setItem(row,column,QtWidgets.QTableWidgetItem(str(value)))
            body=self.scroll.widget();layout=body.layout();layout.insertWidget(1,self.matrix)
            bar=QtWidgets.QHBoxLayout()
            for text,callback in [('Add row',lambda:self.matrix.insertRow(self.matrix.rowCount())),('Remove row',lambda:self.matrix.removeRow(self.matrix.currentRow())),('Paste table',self.paste_matrix)]:
                button=QtWidgets.QPushButton(text);button.clicked.connect(callback);bar.addWidget(button)
            layout.insertLayout(2,bar)

    def paste_matrix(self):
        rows=[line.split('\t') for line in QtWidgets.QApplication.clipboard().text().splitlines() if line.strip()]
        if any(len(row)!=self.matrix.columnCount() for row in rows):raise ValueError('Paste one X column followed by every Y column, separated by tabs.')
        self.matrix.setRowCount(len(rows))
        for r,row in enumerate(rows):
            for c,text in enumerate(row):self.matrix.setItem(r,c,QtWidgets.QTableWidgetItem(text))

    def flush(self):
        super().flush()
        if self.matrix is not None:self.store_matrix()

    def store_matrix(self):
        width=self.rule.Item.NumberOfYColumns+1;values=[]
        for r in range(self.matrix.rowCount()):
            row=[float(self.matrix.item(r,c).text()) for c in range(min(width,self.matrix.columnCount()))]
            values.append(Array[Double](row+[0.0]*max(0,width-len(row))))
        self.rule.Item.DataPoints=Array[Array[Double]](values)

    def prepare_selection(self,prefix):
        self.rule.PrepareSelection()
        self.parent_window.pick_mode.setCurrentText({'Node':'Pick node','Element':'Pick element','Surface':'Pick surface','GeometryEdge':'Pick geometry edge'}[str(self.rule.SelectionKind)])
        self.parent_window.selected=[]
        self.error.setText('Pick the result region, then use the picked selection.')

    def apply(self):
        try:self.flush();self.parent_window.run_operation(self.rule.CommitInBackground(),self.accept,self)
        except Exception as error:self.error.setText(message(error))

class JobMonitor(QtWidgets.QDialog):
    def __init__(self,parent,name):
        super().__init__(parent);self.owner=parent;self.name=name
        self.setWindowTitle('Analysis monitor — '+name);self.resize(780,520)
        layout=QtWidgets.QVBoxLayout(self);self.status=QtWidgets.QLabel();layout.addWidget(self.status)
        tabs=QtWidgets.QTabWidget();layout.addWidget(tabs);self.texts={}
        for title in ['Output','Status','Convergence','DAT']:
            edit=QtWidgets.QPlainTextEdit();edit.setReadOnly(True);tabs.addTab(edit,title);self.texts[title]=edit
        from history_widgets import MonitorPlot
        self.plots={}
        for title in ['Progress','Convergence plot','Energy']:
            plot=MonitorPlot();self.plots[title]=plot;tabs.addTab(plot,title)
        bar=QtWidgets.QHBoxLayout();self.kill=QtWidgets.QPushButton('Kill');self.results=QtWidgets.QPushButton('Results')
        self.kill.clicked.connect(lambda:parent.guard(lambda:parent.results.Kill(name)))
        self.results.clicked.connect(lambda:parent.guard(lambda:parent.open_job(name)))
        close=QtWidgets.QPushButton('Close');close.clicked.connect(self.close)
        for button in [self.kill,self.results,close]:bar.addWidget(button)
        layout.addLayout(bar);self.timer=QtCore.QTimer(self);self.timer.timeout.connect(self.refresh);self.timer.start(200);self.refresh()

    def refresh(self):
        job=self.owner.controller.GetJob(self.name)
        self.status.setText(str(job.JobStatus)+f' — run step {job.CurrentRunStep}, increment {job.CurrentRunIncrement}')
        for title,text in [('Output',job.GetAllOutputData()),('Status',job.StatusFileData),('Convergence',job.ConvergenceFileData),('DAT',job.DatFileData)]:
            text=str(text or '');edit=self.texts[title]
            if edit.toPlainText()!=text:
                follow=edit.verticalScrollBar().value()==edit.verticalScrollBar().maximum();edit.setPlainText(text)
                if follow:edit.verticalScrollBar().setValue(edit.verticalScrollBar().maximum())
        for kind,plot in self.plots.items():plot.update_job(job,kind)
        self.kill.setEnabled(str(job.JobStatus)=='Running')
        self.results.setEnabled(self.owner.operation_task is None)

    def closeEvent(self,event):self.timer.stop();super().closeEvent(event)
