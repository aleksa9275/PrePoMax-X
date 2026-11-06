"""Native CAD operation controls and background document publication."""
from threading import Event
from PyQt6 import QtCore, QtWidgets
from cad_import import CadImportCancelled
from cad_edit import apply_edit,prepare_export


class CadEditJob(QtCore.QThread):
    def __init__(self, document, decoder, part_id, operation, values, parent=None):
        super().__init__(parent)
        self.document,self.decoder,self.part_id,self.operation,self.values=document,decoder,part_id,operation,values
        self.cancel_requested=Event();self.result=None;self.output=None

    def cancel(self):
        self.cancel_requested.set()

    def run(self):
        try:
            if self.operation=='export':
                self.output=prepare_export(self.document,self.decoder,self.part_id,cancel=self.cancel_requested)
                self.result={'success':True,'export':self.output}
            else:
                self.output=apply_edit(self.document,self.decoder,self.part_id,self.operation,self.values,cancel=self.cancel_requested)
                self.result={'success':True,'document':self.output}
        except CadImportCancelled:
            self.result={'success':False,'cancelled':True}
        except Exception as error:
            self.result={'success':False,'error':str(error)}


class CadOperations(QtCore.QObject):
    completed=QtCore.pyqtSignal(dict)

    def __init__(self, window, toolbar):
        super().__init__(window)
        self.window=window;self.job=None;self.result=None
        self.button=QtWidgets.QToolButton()
        self.button.setText('CAD tools…')
        self.button.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        self.menu=QtWidgets.QMenu(self.button);self.button.setMenu(self.menu)
        self.translate_action=self.menu.addAction('Translate part…',lambda:self.dialog('translate'))
        self.split_action=self.menu.addAction('Split part by plane…',lambda:self.dialog('split'))
        self.repair_action=self.menu.addAction('Repair part…',lambda:self.dialog('repair'))
        self.export_action=self.menu.addAction('Export part as STEP…',lambda:self.dialog('export'))
        self.toolbar_action=toolbar.insertWidget(window.mesh_action,self.button)
        self.refresh()

    def refresh(self):
        w=self.window
        self.translate_action.setEnabled(not w.busy and w.cad_document is not None and w.pmx_session is None)
        self.split_action.setEnabled(self.translate_action.isEnabled())
        self.repair_action.setEnabled(self.translate_action.isEnabled())
        self.export_action.setEnabled(not w.busy and w.cad_document is not None)
        self.button.setEnabled(self.translate_action.isEnabled() or self.export_action.isEnabled())

    def dialog(self,operation):
        w=self.window
        if w.busy or w.cad_document is None:return
        dialog=QtWidgets.QDialog(w);dialog.setWindowTitle({'translate':'Translate CAD part','split':'Split CAD part by plane','repair':'Repair CAD part','export':'Export selected CAD part as STEP'}[operation])
        form=QtWidgets.QFormLayout(dialog)
        part=QtWidgets.QComboBox()
        for entry in w.cad_document.scene['cad']['parts']:
            part.addItem(entry['name'],entry['id'])
        form.addRow('CAD part',part)
        fields=[]
        labels=['Translation '+axis+' (model units)' for axis in ('X','Y','Z')] if operation=='translate' else [group+' '+axis for group in ('Plane origin','Plane normal') for axis in ('X','Y','Z')]
        if operation=='repair':labels=['Repair tolerance (model units)']
        if operation=='export':labels=[]
        for index,label in enumerate(labels):
            field=QtWidgets.QLineEdit('0.000001' if operation=='repair' else '1' if operation=='split' and index==5 else '0')
            field.setObjectName('cadParameter'+str(index))
            form.addRow(label,field);fields.append(field)
        message=QtWidgets.QLabel();message.setWordWrap(True);message.setTextFormat(QtCore.Qt.TextFormat.PlainText)
        form.addRow(message)
        buttons=QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok|QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.rejected.connect(dialog.reject)
        def submit():
            try:
                from cad_edit import vector
                if operation=='export':
                    name,_=QtWidgets.QFileDialog.getSaveFileName(dialog,'Export selected CAD part',
                        str(w.cad_document.source.with_suffix('.step')),'STEP (*.step *.stp)',
                        options=QtWidgets.QFileDialog.Option.DontConfirmOverwrite)
                    if not name:return
                    from pathlib import Path
                    values=Path(name)
                    if not values.suffix:values=values.with_suffix('.step')
                    if values.exists() or values.is_symlink():raise FileExistsError('Choose a new STEP filename.')
                elif operation=='translate':
                    values=vector([f.text() for f in fields],'Translation')
                    if not any(values):raise ValueError('Provide a nonzero translation.')
                elif operation=='split':
                    values={'origin':vector([f.text() for f in fields[:3]],'Plane origin'),
                            'normal':vector([f.text() for f in fields[3:]],'Plane normal')}
                    if not any(values['normal']):raise ValueError('Plane normal must be nonzero.')
                else:
                    import math
                    values=float(fields[0].text())
                    if not math.isfinite(values) or not 0<values<=1:
                        raise ValueError('Repair tolerance must be positive and at most 1 model unit.')
                if self.start(part.currentData(),operation,values):dialog.accept()
            except (OSError,ValueError) as error:message.setText(str(error))
        buttons.accepted.connect(submit);form.addRow(buttons);dialog.exec()

    def start(self,part_id,operation,values):
        w=self.window
        if w.busy or w.cad_document is None or (w.pmx_session is not None and operation!='export'):
            raise ValueError('Open native CAD and finish active operations before editing geometry.')
        if operation!='export' and w.model_scene is not None and not w.confirm_discard():return False
        from viewport import decode
        self.result=None
        self.job=CadEditJob(w.cad_document,decode,part_id,operation,values,self)
        self.job.finished.connect(self.finished)
        w.job_state(w.job.state);self.job.start();return True

    def finished(self):
        w=self.window;job=self.job;self.job=None
        result=job.result or {'success':False,'error':'CAD operation returned no result.'}
        if job.cancel_requested.is_set():result={'success':False,'cancelled':True}
        if result['success']:
            try:
                if job.document is not w.cad_document:raise ValueError('CAD document changed before publication.')
                job.document.verify()
                if job.operation=='export':
                    result={'success':True,'receipt':result['export'].publish(job.values)}
                    job.output.close()
                else:
                    document=result['document']
                    document.verify()
                    w.set_cad_document(document.scene,document.source,document=document)
                    w.editor_dirty=True
            except Exception as error:result={'success':False,'error':str(error)}
        if not result['success'] and job.output is not None:job.output.close()
        self.result=result;w.job_state(w.job.state)
        w.job_label.setText(('STEP export complete' if job.operation=='export' else 'CAD edit complete') if result['success'] else 'CAD operation cancelled' if result.get('cancelled') else 'CAD operation failed')
        if result.get('error'):
            w.job_output.setPlainText(result['error'])
            if not w.closing_after_job and not getattr(w,'automated_workflow',False):
                QtWidgets.QMessageBox.critical(w,'Cannot edit CAD',result['error'])
        job.deleteLater();self.completed.emit(result)
        if w.closing_after_job:QtCore.QTimer.singleShot(0,w.close)
