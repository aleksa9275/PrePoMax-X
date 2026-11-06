# Run after opening the checked task0069 original CAD PMX in original 3.0.0.
# Supply duplicate existing regions so native reassignment has audited choices.
data = pmx.model.nodes.get_data()
for name,axis,bound in [('X0_Copy',0,0),('X1_Copy',0,10),('Y0_Copy',1,0),('Z0_Copy',2,0)]:
    ids = [int(label) for label,xyz in zip(data.ids,data.coordinates) if abs(float(xyz[axis])-bound)<1e-8]
    if not ids:
        raise Exception('Empty fixture region: '+name)
    pmx.model.node_sets.add(name,pmx.create.selection_by_ids('femodel','nodes','nodes',ids))
part = pmx.model.parts.first()
pmx.model.element_sets.add('SOLID_Copy',pmx.create.selection_by_ids('femodel','elements','parts',[part.id]))
pmx.save('region-reference.pmx')
pmx.export_to_calculix('region-reference.inp')
