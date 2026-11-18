"""Executed UI evidence for the original element classes, inverted-element links, mass sections and
Rayleigh damping: original .inp import through the window, drawing, element edges, the output-panel link
of an inverted-element report, and the original section/constraint/load/step forms with Calculix export.

The original model import (FeModel.ImportModelFromInpFile) keeps solid and shell/plane elements only;
mass, spring and gap elements are created by the original Calculix writer from point mass sections,
point springs and compression-only surface supports, so those classes are checked in the exported deck.
Beam elements come only from CAD edge visualization and beam results, which this probe does not cover."""
import json
import re
import time
import traceback
from pathlib import Path

from PyQt6 import QtCore, QtTest
from System import Array, Int32

DECKS = Path(__file__).resolve().parents[1] / 'Analysis/StaticDeck'
# Original element classes and the public decks that contain them.
FIXTURES = [
    ('pressure-solids', 'ThreeD', {'LinearTetraElement', 'ParabolicTetraElement', 'LinearWedgeElement', 'ParabolicWedgeElement',
                                   'LinearHexaElement', 'ParabolicHexaElement', 'LinearPyramidElement', 'ParabolicPyramidElement'}),
    ('plane-stress', 'PlaneStress', {'LinearTriangleElement', 'ParabolicTriangleElement', 'LinearQuadrilateralElement',
                                     'ParabolicQuadrilateralElement'}),
]
INVERTED = """*Node
1, 0, 0, 0
2, 1, 0, 0
3, 0, 1, 0
4, 0, 0, 1
5, 2, 0, 0
6, 3, 0, 0
7, 2, 1, 0
8, 2, 0, 1
*Element, Type=C3D4, Elset=Inverted
1, 1, 3, 2, 4
*Element, Type=C3D4, Elset=Regular
2, 5, 6, 7, 8
"""


def values(collection):
    """Python.NET returns some .NET dictionaries as Python dicts."""
    return list(collection.values()) if isinstance(collection, dict) else list(collection.Values)


def start(app, window, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    report = {'success': False, 'checks': [], 'elementClasses': {},
              'scope': 'local native Qt/VTK workflow on public decks; not four-target acceptance'}
    started = time.monotonic()
    state = {}
    c = window.controller

    def check(name, value):
        if not value:
            raise AssertionError(name)
        report['checks'].append(name)

    def ready():
        if window.operation_task is not None:
            return False
        if window.operation_error:
            raise AssertionError(window.operation_error)
        return True

    def new_model(space):
        from CaeModel import ModelSpaceEnum
        from CaeGlobals import UnitSystemType
        c.New()
        c.SetNewModelPropertiesCommand(getattr(ModelSpaceEnum, space), UnitSystemType.MM_TON_S_C)
        window.refresh()

    def import_fixture(index):
        def run():
            name, space, _ = FIXTURES[index]
            new_model(space)
            window.import_path(str(DECKS / (name + '.inp')), False)
            check('import of ' + name + ' runs through the window operation', window.operation_task is not None)
        return run

    def verify_fixture(index):
        def run():
            if not ready():
                return False
            name, _, expected = FIXTURES[index]
            mesh = c.Model.Mesh
            classes = sorted({type(e).__name__ for e in values(mesh.Elements)})
            report['elementClasses'][name] = classes
            check(name + ': original element classes imported', expected <= set(classes))
            from view_probe import ViewProbe
            view = ViewProbe(app, window)
            window.fit()
            drawn = set(view.actor_names())
            parts = [str(p.Name) for p in values(mesh.Parts)]
            check(name + ': every mesh part drawn', set(parts) <= drawn)
            window.set_edge_mode('Model edges')
            check(name + ': drawn cells', view.colored_pixels(output / (name + '-model.png')) > 100)
            model_edges = view.dark_pixels(output / (name + '-model.png'))
            window.element_edges.setChecked(True)
            app.processEvents()
            element_edges = view.dark_pixels(output / (name + '-elements.png'))
            # Element edges are thin lines inside the faces: the pixels they darken against the model-edge picture
            added = view.darkened_pixels(output / (name + '-model.png'), output / (name + '-elements.png'))
            report.setdefault('elementEdges', {})[name] = {'darkPixels': [model_edges, element_edges], 'addedLinePixels': added}
            check(name + ': element edges drawn', str(window.vtk.EdgesVisibility) == 'ElementEdges' and added > 0)
            window.element_edges.setChecked(False)
            app.processEvents()
            # The tree lists the parts with their part-type icons.
            part_items = [i for i in window.walk_tree() if i.data(0, QtCore.Qt.ItemDataRole.UserRole) is not None
                          and i.data(0, QtCore.Qt.ItemDataRole.UserRole).Family == 'Parts'
                          and not i.data(0, QtCore.Qt.ItemDataRole.UserRole).Group]
            check(name + ': parts in the FE Model tree', len(part_items) == len(parts) and all(not i.icon(0).isNull() for i in part_items))
            window.raise_()
            window.activateWindow()
            QtTest.QTest.qWait(100)
            window.screen().grabWindow(0, window.x(), window.y(), window.width(), window.height()).save(str(output / (name + '.png')))
        return run

    def import_inverted():
        new_model('ThreeD')
        path = output / 'inverted.inp'
        path.write_text(INVERTED)
        window.import_path(str(path), False)

    def inverted_link():
        if not ready():
            return False
        from CaeMesh import InvertedElements, MessageInvertedElements
        mesh = c.Model.Mesh
        inverted = {str(p.Name): len(InvertedElements.GetElementIds(mesh, p)) for p in values(mesh.Parts)}
        report['invertedElements'] = inverted
        check('original InvertedElements finds the inverted tetrahedron only', sorted(inverted.values()) == [0, 1])
        part = next(n for n, count in inverted.items() if count == 1)
        message = str(MessageInvertedElements.GetMessage(part, 1))
        window.write_output(message)
        app.processEvents()
        block = window.output.document().lastBlock()
        while block.isValid() and block.text() != message:
            block = block.previous()
        ranges = window.output_link_ranges(block.text())
        check('inverted-element report is an output link (FindOutputLinks)', len(ranges) == 1)
        cursor = window.output.textCursor()
        cursor.setPosition(block.position() + ranges[0][0] + 1)
        window.output.ensureCursorVisible()
        point = window.output.cursorRect(cursor).center()
        c.ClearAllSelection()
        from view_probe import ViewProbe
        view = ViewProbe(app, window)
        before = view.highlighted_pixels(output / 'inverted-before.png')
        QtTest.QTest.mouseClick(window.output.viewport(), QtCore.Qt.MouseButton.LeftButton, pos=point)
        app.processEvents()
        report['invertedHighlight'] = [before, view.highlighted_pixels(output / 'inverted-after.png')]
        check('clicking the link highlights the inverted elements (HighlightInvertedElementsNamedAt)',
              report['invertedHighlight'][1] > report['invertedHighlight'][0]
              and 'has no inverted' not in window.output.toPlainText())

    def mass_and_damping():
        new_model('ThreeD')
        window.import_path(str(DECKS / 'c3d10-force.inp'), False)

    def mass_and_damping_forms():
        if not ready():
            return False
        from CaeModel import PointMassSection, DampingTypeEnum
        from form_driver import FormDriver
        # Original FrmSection/FrmConstraint/FrmSurface/FrmStep/FrmLoad compiled whole (C9).
        forms = FormDriver(window)
        window.edit_definition('Sections')
        forms.select_type('Point Mass')
        forms.set_choice('RegionType', 'node set')
        forms.set('NodeSetName', 'TRACTION')
        name = forms.get('Name')
        before = len(forms.prompts)
        forms.set('Mass', '-1')
        report['negativeMassError'] = forms.prompts[before:]
        # MassSection.CheckPositive rejects the value in the property grid (WinForms: invalid property value).
        check('section form rejects a negative mass (MassSection.CheckPositive)',
              any('mass must be larger or equal to zero' in t.lower() or 'mass must be larger or equal to 0' in t.lower()
                  for t in forms.prompts[before:]) and forms.form is not None)
        forms.set('Mass', '0.5')
        forms.ok()
        section = c.GetSection(name)
        check('point mass section created through the section form', isinstance(section, PointMassSection)
              and section.Mass.Value == 0.5 and forms.form is None and window.active_editor is None)
        state['mass'] = name
        window.edit_definition('Constraints')
        forms.select_type('Point Spring')
        forms.set_choice('MasterRegionType', 'node set')
        forms.set('NodeSetName', 'BOTTOM')
        forms.set('K1', '100')
        forms.ok()
        check('point spring through the constraint form', forms.form is None and c.Model.Constraints.Count == 1)
        window.edit_definition('Surfaces')
        forms.set_choice('CreateSurfaceFrom', 'node')
        forms.set('NodeSetName', 'BOTTOM')
        surface = forms.get('Name')
        forms.ok()
        check('surface from a node set through the surface form', c.GetSurface(surface) is not None and forms.form is None)
        window.edit_definition('Constraints')
        forms.select_type('Surface Support')
        forms.set_choice('SupportType', 'compression')
        forms.set_choice('MasterRegionType', 'surface')
        forms.set('SurfaceName', surface)
        forms.ok()
        check('compression-only surface support through the constraint form', forms.form is None
              and c.Model.Constraints.Count == 2)
        window.edit_definition('Steps')
        forms.select_type('Static Step')
        static = forms.get('Name')
        forms.ok()
        window.edit_definition('Loads', static)
        forms.select_type('Gravity')
        forms.set_choice('RegionType', 'mass')
        forms.set('MassSectionName', name)
        forms.set('F3', '-9810')
        forms.ok()
        gravity = values(c.GetStep(static).Loads)[0]
        check('gravity load on the mass section through the load form', str(gravity.RegionType) == 'MassSection'
              and gravity.RegionName == name)
        window.edit_definition('Steps')
        forms.select_type('Dynamic Step')
        dynamic = forms.get('Name')
        forms.set_choice('DampingType', 'rayleigh')
        check('Rayleigh damping shows Alpha and Beta (ViewDynamicStep.UpdateVisibility)',
              forms.has('AlphaRayleigh') and forms.has('BetaRayleigh'))
        forms.set('AlphaRayleigh', '0.2')
        forms.set('BetaRayleigh', '0.001')
        forms.ok()
        damping = c.GetStep(dynamic).Damping
        check('dynamic step Damping set through the step form', damping.DampingType == DampingTypeEnum.Rayleigh
              and abs(damping.Alpha - 0.2) < 1e-12 and abs(damping.Beta - 0.001) < 1e-12)
        deck = output / 'mass-damping.inp'
        c.ExportToCalculixCommand(str(deck))
        text = deck.read_text()
        mass = re.search(r'^\*Mass, Elset=(\S+)', text, re.M | re.I)
        types = sorted(set(re.findall(r'^\*Element,\s*Type=(\w+)', text, re.M | re.I)))
        report['deck'] = {'mass': mass.group(0) if mass else None, 'elementTypes': types,
                          'damping': re.findall(r'^\*Damping.*$', text, re.M | re.I),
                          'gravity': re.findall(r'^.*GRAV.*$', text, re.M | re.I)}
        check('Calculix *Mass on the generated mass elements', mass is not None and re.search(
            r'^\*Element, Type=MASS, Elset=' + re.escape(mass.group(1)), text, re.M | re.I) is not None)
        check('LinearSpringElement and LinearGapElement written for the spring and the support',
              any(t.upper().startswith('SPRING') for t in types) and 'GAPUNI' in [t.upper() for t in types])
        gravity_sets = {line.split(',')[0].strip() for line in report['deck']['gravity'] if not line.startswith('**')}
        check('gravity written on the element set of the mass section (CalGravityLoad, ElementSetName)',
              len(gravity_sets) == 1 and next(iter(gravity_sets)).startswith(state['mass'] + '_') and
              re.search(r'^\*Elset, Elset=' + re.escape(next(iter(gravity_sets))) + r'\s*$', text, re.M | re.I) is not None)
        check('Calculix *Damping with the Rayleigh coefficients', len(report['deck']['damping']) == 1
              and 'Alpha=' in report['deck']['damping'][0] and 'Beta=' in report['deck']['damping'][0])
        report['success'] = True

    steps = []
    for i in range(len(FIXTURES)):
        steps += [import_fixture(i), verify_fixture(i)]
    steps += [import_inverted, inverted_link, mass_and_damping, mass_and_damping_forms]
    steps = iter(steps)
    current = [None]
    timer = QtCore.QTimer(window)

    def tick():
        try:
            if time.monotonic() - started > 180:
                raise TimeoutError('element GUI workflow timed out')
            if current[0] is None:
                current[0] = next(steps)
            if current[0]() is not False:
                current[0] = None
        except StopIteration:
            timer.stop()
            finish()
        except Exception as error:
            report.update(error=str(error), traceback=traceback.format_exc())
            timer.stop()
            finish()

    def finish():
        if window.active_editor is not None:
            window.active_editor.reject()
        window.form_host.CloseAllForms()
        (output / 'elements-gui.json').write_text(json.dumps(report, indent=2) + '\n')
        window.dirty = False
        window.close()
        app.exit(0 if report['success'] else 1)
    timer.timeout.connect(tick)
    timer.start(50)
