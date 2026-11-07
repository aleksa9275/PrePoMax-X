pmx.model.properties.model_space = 'ThreeD'
pmx.model.properties.unit_system = 'MM_TON_S_C'
pmx.import_file('mesh.inp')
pmx.model.properties.model_space = 'ThreeD'
pmx.model.materials.add('Elastic',[pmx.create.elastic(1000,0)])
pmx.model.sections.add_membrane('Section','Elastic',pmx.create.region('ElementSetName','BODY'),thickness=1)
step=pmx.model.steps.add_static('Static',solver_type='Default',incrementation_type='Automatic',initial_time_increment=1,time_period=1,min_time_increment=1e-5,max_time_increment=1,output_frequency=1)
step.bcs.add_displacement_rotation('Base',pmx.create.region('NodeSetName','ROOT'),u2=0)
step.bcs.add_displacement_rotation('Side',pmx.create.region('NodeSetName','SIDE'),u1=0)
step.loads.add_concentrated_force('Pull',pmx.create.region('NodeSetName','TIP'),f2=.5)
step.bcs.add_displacement_rotation('Planar',pmx.create.region('NodeSetName','ALL'),u3=0)
step.history_outputs.add_nodal('Tip-history',pmx.create.region('NodeSetName','TIP'),['U','RF'])
pmx.save('original.pmx')
pmx.export_to_calculix('original.inp')
