"""Executed UI evidence for the 3.0.1 composite shell forms (M2), run as a step of forms_gui_probe.py on upstream's
composite_shells.inp: the original FrmMaterialOrientation creates a material orientation, and the original FrmSection
builds a composite shell section in its Layers tab. The layup diagram is the original pnlLayup_Paint/DrawLayup,
drawn by Qt from the GDI+ calls it records (X/Domain/WinFormsCompat/Painting.cs); a Qt click on a layer selects
its row through the original pnlLayup_MouseClick."""
from pathlib import Path

from PyQt6 import QtCore, QtGui, QtTest

from forms_gui_probe_child import ChildFormsProbe
from forms_gui_probe_grid import edit_cell, grid_widget

ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / 'APIs/Python/Test_Scripts/Models/composite_shells.inp'


def commands(control):
    return list(control.RenderPaint().Commands)


class CompositeFormsProbe(ChildFormsProbe):
    def model(self):
        from CaeModel import ModelSpaceEnum
        from CaeGlobals import UnitSystemType
        c = self.c
        c.New()
        c.SetNewModelPropertiesCommand(ModelSpaceEnum.ThreeD, UnitSystemType.MM_TON_S_C)
        self.window.refresh()
        self.window.import_path(str(MODEL), False)

    def ready(self):
        return self.window.operation_task is None

    def add_materials(self):
        from CaeModel import Material, Elastic
        from System import Array, Double
        for name, modulus in (('Ply', 140000.0), ('Core', 3000.0)):
            material = Material(name)
            row = Array[Double]([modulus, 0.3, 0.0])
            material.AddProperty(Elastic(Array[Array[Double]]([row])))
            self.c.AddMaterialCommand(material)
        self.check('composite model: upstream composite_shells.inp imported with two materials',
                   len(list(self.c.GetModelPartNames())) == 3 and len(list(self.c.GetMaterialNames())) == 2)

    def material_orientation(self):
        c = self.c
        self.entry('CreateMaterialOrientation')
        form = next(f for f in self.open_forms() if type(f).__name__ == 'FrmMaterialOrientation')
        self.check('FrmMaterialOrientation opened through FrmMain.CreateMaterialOrientation', str(form.Text) == 'Create Material Orientation')
        self.grid_set(form, 'Region type', 'Part name')
        self.snapshot('FrmMaterialOrientation', form)
        self.click(form, 'btnOK')
        names = [str(n) for n in c.GetMaterialOrientationNames()]
        self.report['forms']['FrmMaterialOrientation'] = {'created': names}
        self.check('FrmMaterialOrientation OK runs the original OnApply: orientation created', len(names) == 1)

    def section(self):
        c = self.c
        from System import Array, Int32
        self.entry('CreateSection')
        form = next(f for f in self.open_forms() if type(f).__name__ == 'FrmSection')
        lv = self.by_name(form, 'lvTypes')
        names = [str(i.Text) for i in lv.Items]
        self.check('FrmSection lists the 3.0.1 Composite Shell Section', 'Composite Shell Section' in names)
        self.renderer.guard(lambda: lv.SelectByUser(Array[Int32]([names.index('Composite Shell Section')])))
        self.renderer.flush()
        tabs = self.by_name(form, 'tcProperties')
        self.check('composite type adds the Layers page', [str(p.Text) for p in tabs.TabPages] == ['Properties', 'Layers'])
        self.renderer.guard(lambda: setattr(tabs, 'SelectedIndex', 1))
        self.renderer.flush()
        dgv = self.by_name(form, 'dgvData')
        layup = self.by_name(form, 'pnlLayup')
        window, panel = self.widget(form, layup)
        self.check('pnlLayup has a Paint handler and is drawn by Qt (PaintedControl)', bool(layup.HasPaintHandler) and type(panel).__name__ == 'PaintedControl')
        headers = [str(col.HeaderText).replace('\n', ' ') for col in dgv.Columns]
        thickness = next(i for i, h in enumerate(headers) if h.startswith('Thickness'))
        angle = next(i for i, h in enumerate(headers) if h.startswith('Angle'))
        one = commands(layup)
        texts = [str(cmd.Arguments[0]) for cmd in one if str(cmd.Name) == 'DrawText']
        self.check('one layer: DrawLayup fills one bar and names it "Layer 1" with axis 3',
                   sum(str(cmd.Name) == 'FillRectangle' for cmd in one) == 1 and texts.count('Layer 1') == 1 and '3' in texts)
        self.check('axis 3 is an arrow (AdjustableArrowCap) from the dash-dot reference surface',
                   any(str(cmd.Name) == 'DrawLine' and cmd.Arguments[0].CustomEndCap is not None for cmd in one)
                   and any(str(cmd.Name) == 'DrawLine' and str(cmd.Arguments[0].DashStyle) == 'DashDot' for cmd in one))
        # A second layer typed in the new row (Binding_AddingNew copies the last layer), turned to 90 degrees.
        table = grid_widget(window, dgv)
        edit_cell(self.app, table, 1, thickness, '2')
        self.renderer.flush()
        edit_cell(self.app, table, 1, angle, '90')
        self.renderer.flush()
        two = commands(layup)
        bars = [cmd.Arguments[1] for cmd in two if str(cmd.Name) == 'FillRectangle']
        cells = [[str(dgv.GetCellText(r, k)) for k in range(len(headers))] for r in range(int(dgv.RowCount))]
        self.report['forms']['FrmSection'] = {'headers': headers, 'rows': int(dgv.RowCount), 'cells': cells,
                                              'gridBounds': [dgv.Bounds.X, dgv.Bounds.Y, dgv.Bounds.Width, dgv.Bounds.Height],
                                              'bars': [[float(b.X), float(b.Y), float(b.Width), float(b.Height)] for b in bars]}
        self.check('layer rows: "Layer N" (dgvData_CellFormatting) and the material of the combo box column bound later',
                   cells[0][:2] == ['Layer 1', 'Ply'] and cells[1][:2] == ['Layer 2', 'Ply']
                   and [table.item(1, k).text() for k in range(2)] == ['Layer 2', 'Ply'])
        symmetric_box = self.by_name(form, 'cbSymmetric')
        self.check('the layers grid fills the page below the docked check box and above the layup (deferred layout)',
                   dgv.Bounds.Y == symmetric_box.Bounds.Bottom and dgv.Bounds.Bottom <= layup.Bounds.Y)
        self.check('two layers: two bars, layer 2 above layer 1 and twice as thick',
                   len(bars) == 2 and bars[1].Y < bars[0].Y and abs(float(bars[1].Height) - 2 * float(bars[0].Height)) <= 1.5)
        # What Qt shows: the replayed drawing has the hatching and the outlines (dark pixels inside the bars).
        panel.repaint()
        self.app.processEvents()
        image = panel.grab().toImage()
        top = bars[1]
        dark = sum(1 for x in range(int(top.X) + 2, int(top.X + top.Width) - 2, 2)
                   for y in range(int(top.Y) + 2, int(top.Y + top.Height) - 2, 2)
                   if QtGui.QColor(image.pixel(x, y)).lightness() < 128)
        self.report['forms']['FrmSection']['hatchPixels'] = dark
        self.check('Qt replays the layup: hatch lines inside the top bar', dark > 5 and panel.commands == len(two))
        # A click on layer 1 (the bottom bar) selects its row (pnlLayup_MouseClick), as it did for layer 2.
        bottom = bars[0]
        QtTest.QTest.mouseClick(panel, QtCore.Qt.MouseButton.LeftButton, QtCore.Qt.KeyboardModifier.NoModifier,
                                QtCore.QPoint(int(bottom.X + bottom.Width / 2), int(bottom.Y + bottom.Height / 2)))
        self.renderer.flush()
        self.check('Qt click on the bottom bar selects layer 1 (pnlLayup_MouseClick)', dgv.CurrentCell is not None and dgv.CurrentCell.RowIndex == 0)
        marker = [cmd for cmd in commands(layup) if str(cmd.Name) == 'FillPolygon']
        self.check('the selected layer is marked in the margin (DrawLayerMarker)', len(marker) == 1
                   and abs(float(marker[0].Arguments[1][0].Y) - float(bottom.Y + bottom.Height / 2)) <= 1)
        # Symmetric: the mirrored layers are drawn above (four solver layers).
        symmetric = self.by_name(form, 'cbSymmetric')
        self.renderer.guard(lambda: setattr(symmetric, 'Checked', True))
        self.renderer.flush()
        mirrored = [cmd for cmd in commands(layup) if str(cmd.Name) == 'FillRectangle']
        self.check('Symmetric draws the mirrored layers (four bars)', len(mirrored) == 4)
        self.snapshot('FrmSection-layup', form)
        self.grid_set(form, 'Region type', 'Part name')
        self.click(form, 'btnOK')
        sections = [c.GetSection(str(n)) for n in c.GetSectionNames()]
        composite = [s for s in sections if type(s).__name__ == 'CompositeShellSection']
        self.report['forms']['FrmSection']['created'] = [str(s.Name) for s in composite]
        self.check('FrmSection OK creates the symmetric composite section with two layers',
                   len(composite) == 1 and composite[0].Layers.Count == 2 and bool(composite[0].Symmetric)
                   and abs(float(composite[0].Layers[1].Angle.Value) - 90) < 1e-9)
