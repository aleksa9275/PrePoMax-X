# Run after opening the portable edited CAD PMX in original PrePoMax 3.0.0.
import json
part = pmx.model.geometry.parts.first()
pmx.export_to_calculix('original-readback.inp')
pmx.save('original-resave.pmx')
with open('Z:/tmp/prepomaxx-task0069-reference/readback/readback.json','w') as stream:
    json.dump({'cadParts':len(pmx.model.geometry.parts),'partName':str(part.name),
               'partId':int(part.id),'volume':float(part.volume),
               'faces':int(part.get_face_data().count),'nodes':int(pmx.model.nodes.count),
               'elements':int(pmx.model.elements.count)},stream)
