# Run inside the pinned original PrePoMax 3.0.0; input is sweep_two_apart.brep.
import json
parts = list(pmx.model.geometry.parts)
pmx.model.geometry.parts.remove([str(p.name) for p in parts[1:]])
part = pmx.model.geometry.parts.first()
selection = pmx.create.selection_by_ids('geometry', 'geometry', 'parts', [part.id])
pmx.model.mesh.setup_items.add_meshing_parameters('Linear', selection, max_size=5,
    min_size=0, second_order=False)
pmx.model.mesh.setup_items.add_tetrahedral_gmsh('Tetrahedra', selection)
report = pmx.model.mesh.generate(part.name)
if any(str(reason) for reason in report.values()):
    raise Exception('Meshing failed: ' + str(report))
data = pmx.model.nodes.get_data()
ids = [int(i) for i in data.ids]
coordinates = [[float(v) for v in row] for row in data.coordinates]
for name, axis, bound in [('X0',0,0),('Y0',1,0),('Z0',2,0),('X1',0,10)]:
    labels = [label for label,xyz in zip(ids,coordinates) if abs(xyz[axis]-bound)<1e-8]
    if not labels:
        raise Exception('Empty region: ' + name)
    pmx.model.node_sets.add(name, pmx.create.selection_by_ids('femodel','nodes','nodes',labels))
mesh_part = pmx.model.parts.first()
pmx.model.element_sets.add('SOLID', pmx.create.selection_by_ids('femodel','elements','parts',[mesh_part.id]))
pmx.model.materials.add('Elastic',[pmx.create.elastic(210000,0.3),pmx.create.density(7.85e-9)])
pmx.model.sections.add_solid('Section','Elastic',pmx.create.region('ElementSetName','SOLID'))
step = pmx.model.steps.add_static('Static', solver_type='Default',
    incrementation_type='Automatic', initial_time_increment=1, time_period=1,
    min_time_increment=1e-5, max_time_increment=1, output_frequency=1)
for name,values in [('X0',{'u1':0}),('Y0',{'u2':0}),('Z0',{'u3':0})]:
    step.bcs.add_displacement_rotation(name,pmx.create.region('NodeSetName',name),**values)
step.loads.add_concentrated_force('Force',pmx.create.region('NodeSetName','X1'),f1=100)
pmx.save('cad-reference.pmx')
pmx.export_to_calculix('cad-reference.inp')
with open('Z:/tmp/prepomaxx-task0069-reference/work/capture.json','w') as stream:
    json.dump({'geometryPart':str(part.name),'meshPart':str(mesh_part.name),
               'geometryId':int(part.id),'meshPartId':int(mesh_part.id),
               'nodes':len(ids),'elements':int(pmx.model.elements.count)},stream)
