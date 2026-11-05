"""Exercise real CAD picks/tree/dialogs and typed original-reader region unions."""
from PyQt6 import QtCore, QtWidgets


def prepare(app, window, output, check):
    r = window.regions
    original_scene, original_bytes = window.model_scene, window.mesh_bytes
    r.view.setCurrentIndex(r.view.findData('cad'))
    check('source CAD view retains edited model', window.scene is window.cad_document.scene and
          window.model_scene is original_scene and window.mesh_bytes == original_bytes)
    check('analysis controls available from linked CAD', window.configure_action.isEnabled() and window.run_action.isEnabled())

    def pick_part(part_id, mode):
        r.mode.setCurrentIndex(r.mode.findData(mode))
        for i, cell in enumerate(window.scene['elements']):
            if cell['sourcePartId'] != part_id:
                continue
            triangle = window.grid.GetCell(i)
            center = [sum(window.grid.GetPoint(triangle.GetPointId(j))[axis] for j in range(3)) / 3 for axis in range(3)]
            window.renderer.SetWorldPoint(*center, 1)
            window.renderer.WorldToDisplay()
            x, y, _ = window.renderer.GetDisplayPoint()
            if window.picker.Pick(x, y, 0, window.renderer) and window.picker.GetCellId() == i:
                result = window.pick(x, y)
                expected = (mode, part_id, cell['sourceFaceId'] if mode == 'face' else 0)
                check(f'real {mode} pick resolves part {part_id}', result['sourcePartId'] == part_id and r.refs == {expected})
                check(f'{mode} highlight matches CAD selection', r.actor.GetVisibility() and r.mapper.GetInput().GetNumberOfCells() > 0)
                return expected
        raise ValueError(f'No visible face could be picked in part {part_id}')

    picked = []
    ids = []
    for part in (1, 2):
        picked.append(pick_part(part, 'face'))
        ids.append(set(window.add_cad_region_set('node', f'PickedFace{part}')['ids']))
    check('equal local face IDs remain isolated by part', ids[0].isdisjoint(ids[1]))

    def tree_select(refs):
        window.model_tree.clearSelection()
        for ref in refs:
            r.items[ref].setSelected(True)
        check('multi-selection follows actual source tree items', r.refs == set(refs))

    tree_select(picked)
    union = window.add_cad_region_set('node', 'PickedFaces')['ids']
    check('original C# union includes both picked faces exactly once', set(union) == ids[0] | ids[1] and len(union) == len(set(union)))
    original = window.mesh_bytes
    try:
        window.add_cad_region_set('element', 'InvalidFaces')
    except ValueError:
        check('face-to-element conversion rejects without editing', window.mesh_bytes == original)
    else:
        raise ValueError('Face selection incorrectly accepted as whole solid')

    for part in (1, 2):
        pick_part(part, 'part')
    tree_select({('part', 1, 0), ('part', 2, 0)})
    errors = []
    def submit():
        dialog = app.activeModalWidget()
        try:
            check('CAD region action opens its real dialog', isinstance(dialog, QtWidgets.QDialog))
            name = dialog.findChild(QtWidgets.QLineEdit)
            kind = dialog.findChild(QtWidgets.QComboBox)
            kind.setCurrentIndex(kind.findData('element'))
            button = dialog.findChild(QtWidgets.QDialogButtonBox).button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
            name.setText('invalid name')
            button.click()
            check('invalid region name keeps dialog and mesh intact', dialog.isVisible() and window.mesh_bytes == original)
            name.setText('SelectedSolids')
            button.click()
        except Exception as error:
            errors.append(error)
            if dialog:
                dialog.reject()
    QtCore.QTimer.singleShot(100, submit)
    r.create.trigger()
    if errors:
        raise errors[0]
    check('selected parts create a section region', any(s['name'] == 'SelectedSolids' and s['count'] == len(window.model_scene['elements']) for s in window.model_scene['elementSets']))
    window.add_cad_region_set('node', 'SelectedNodes')
    tree_select({('face', 1, 5), ('face', 2, 5)})
    window.add_cad_region_set('node', 'SelectedBottoms')
    for part in (1, 2):
        tree_select({('face', part, 6)})
        window.add_cad_region_set('node', f'SelectedTop{part}')
    check('CAD regions retain source associations', len(window.cad_mesh.authored_regions) == 8)
    good_refs, before = set(r.refs), window.mesh_bytes
    r.select({('face', 1, 999999)})
    try:
        window.add_cad_region_set('node', 'UnmappedFace')
    except ValueError:
        check('unmapped CAD face rejects without changing model or provenance', window.mesh_bytes == before and len(window.cad_mesh.authored_regions) == 8)
    else:
        raise ValueError('Unmapped face was accepted')
    r.select(good_refs)
    window.raise_()
    app.processEvents()
    if window.transport == 'frame-bridge':
        capture = window.grab()
    else:
        origin = window.mapToGlobal(QtCore.QPoint(0, 0))
        capture = window.screen().grabWindow(0, origin.x(), origin.y(), window.width(), window.height())
    check('selected CAD overlay captured', capture.save(str(output / 'regions.png')))
    selected = set(r.refs)
    r.clear_action.trigger()
    cleared = not r.refs and not r.actor.GetVisibility() and not r.create.isEnabled()
    r.select(selected)
    r.view.setCurrentIndex(r.view.findData('mesh'))
    check('mesh view preserves CAD selection and set edits', window.scene is window.model_scene and r.refs == selected and
          window.editor_dirty and not r.actor.GetVisibility() and cleared)


def assign(definition):
    definition['sections'] = [{'name': 'SelectedSection', 'material': 'Elastic', 'elementSet': 'SelectedSolids'}]
    constraints = definition['step']['constraints']
    for c in constraints:
        c['nodeSet'] = {'ALL_NODES': 'SelectedNodes', 'PART_1_FACE_5': 'SelectedBottoms',
                        'PART_1_FACE_6': 'SelectedTop1', 'PART_2_FACE_6': 'SelectedTop2'}.get(c['nodeSet'], c['nodeSet'])
    definition['step']['constraints'] = [c for c in constraints if c['name'] != 'Bottom-2']
