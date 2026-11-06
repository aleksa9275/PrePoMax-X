"""Owned native CAD edit transactions; original commands own geometry behavior."""
from copy import deepcopy
import json
import math
import os
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory

from cad_document import CadDocument
from cad_import import NativeCadTool, CadImportCancelled, MAX_CAD_BYTES, MAX_CAD_PARTS, file_sha256, require_output, run_stage
from cad_scene import compose_cad_parts

MAX_EDIT_BYTES = 256 * 1024 * 1024
MAX_EDITS = 32


def vector(values, name):
    if not isinstance(values, (list, tuple)) or len(values) != 3:
        raise ValueError(name+' requires three finite model-unit values.')
    result = [float(v) for v in values]
    if any(not math.isfinite(v) or abs(v)>1e9 for v in result):
        raise ValueError(name+' requires finite values between -1e9 and 1e9.')
    return result


def selected_part(document, part_id):
    if not isinstance(document.tool, NativeCadTool):
        raise ValueError('CAD operations require the explicit native CAD profile.')
    if type(part_id) is not int or not 1 <= part_id <= len(document.parts):
        raise ValueError('Choose an existing CAD part.')
    document.verify()
    return document.parts[part_id-1][0]


def apply_edit(document, decoder, part_id, operation, values, *, cancel=None):
    source = selected_part(document, part_id)
    if len(document.edits) >= MAX_EDITS:
        raise ValueError('This native preview supports at most 32 CAD edits per document.')
    def numbers(values):return ' '.join(format(v,'.17g') for v in values)
    if operation=='translate':
        description=vector(values,'Translation')
        if not any(description):raise ValueError('Provide a nonzero translation.')
        parameters='Transform type: Translate\nDirection: '+numbers(description)+'\n'
        arguments=['BREP_TRANSFORM']
    elif operation=='split':
        if not isinstance(values,dict) or set(values)!={'origin','normal'}:
            raise ValueError('Provide a plane origin and normal.')
        origin,normal=vector(values['origin'],'Plane origin'),vector(values['normal'],'Plane normal')
        if not any(normal):raise ValueError('Plane normal must be nonzero.')
        scene=decoder(document.parts[part_id-1][1],cancel=cancel)
        extent=[value for axis in ('x','y','z') for value in
                (min(n[axis] for n in scene['nodes']),max(n[axis] for n in scene['nodes']))]
        description={'origin':origin,'normal':normal,'extent':extent}
        parameters='Tool type: Plane\nExtent: '+numbers(extent)+'\nPlane origin: '+numbers(origin)+'\nPlane normal: '+numbers(normal)+'\n'
        arguments=['BREP_SPLIT']
    elif operation=='repair':
        tolerance=float(values)
        if not math.isfinite(tolerance) or not 0<tolerance<=1:
            raise ValueError('Repair tolerance must be finite, positive and at most 1 model unit.')
        description={'option':1,'tolerance':tolerance}
        parameters='Repair option: 1\nTolerance: '+format(tolerance,'.17g')+'\n'
        arguments=['BREP_REPAIR']
    else:raise ValueError('Unsupported native CAD edit.')
    edited = CadDocument.__new__(CadDocument)
    edited.storage = TemporaryDirectory(prefix='prepomaxx-cad-edit-')
    edited.root = Path(edited.storage.name)
    edited.source, edited.tool = document.source, document.tool
    edited.edits, edited.edit_files = deepcopy(document.edits), []
    try:
        work = edited.root/'edit';work.mkdir()
        inputs = edited.root/'inputs';inputs.mkdir()
        number = len(document.edits)+1
        prefix = f'operation-{number:04d}'
        staged_source = work/(prefix+'-input.brep')
        shutil.copyfile(source, staged_source)
        definition = work/(prefix+'-parameters.txt')
        definition.write_text(parameters,encoding='utf-8')
        result = work/(prefix+'-output.brep')
        suffix=['1',format(tolerance,'.17g')] if operation=='repair' else [str(definition)]
        run_stage([*document.tool.command,*arguments,str(staged_source),str(result),*suffix],
                  work,'operation.log',cancel=cancel)
        if file_sha256(staged_source)!=document.identities[source] or definition.read_text(encoding='utf-8')!=parameters:
            raise ValueError('CAD command modified its staged input or parameters.')
        require_output(result,MAX_CAD_BYTES)
        converter=document.tool.separate_solids if operation=='split' else document.tool.convert_parts
        generated=converter(result,work/'decoded',cancel=cancel)
        if operation in ('translate','repair') and len(generated)!=1:
            raise ValueError('Translation/controlled repair must retain one selected CAD part.')
        extra=[]
        if operation=='split':
            origins_file=result.with_suffix('.brep.origins')
            require_output(origins_file,4096)
            if len(generated)<2 or origins_file.read_text().split()!=['1']*len(generated):
                raise ValueError('Plane split must yield multiple solids with checked original source-solid origins.')
            extra.append(origins_file)
        if len(document.parts)-1+len(generated)>MAX_CAD_PARTS:
            raise ValueError('Edited CAD exceeds the 32-part preview limit.')
        edited.parts=[]
        origins=[]
        for old_id,pair in enumerate(document.parts,1):
            for brep,vis in generated if old_id==part_id else [pair]:
                new_id=len(edited.parts)+1
                b,v=inputs/f'part-{new_id:04d}.brep',inputs/f'part-{new_id:04d}.vis'
                shutil.copyfile(brep,b);shutil.copyfile(vis,v)
                edited.parts.append((b,v));origins.append(old_id)
        edited.snapshot=inputs/('source'+document.snapshot.suffix)
        shutil.copyfile(document.snapshot,edited.snapshot)
        for path in document.edit_files+[staged_source,definition,result,work/'operation.log',*extra]:
            target=inputs/(path.name if path.name!='operation.log' else prefix+'-command.log')
            shutil.copyfile(path,target);edited.edit_files.append(target)
        edit={'operation':operation,'selectedPartId':part_id,'parameters':description,
              'inputBrepSha256':file_sha256(source),'outputBrepSha256':file_sha256(result),
              'partOrigins':origins,'toolReceiptSha256':document.tool_receipt}
        edited.edits.append(edit)
        edited.edits_snapshot=json.dumps(edited.edits,sort_keys=True,allow_nan=False)
        history=inputs/(prefix+'-receipt.json');history.write_text(json.dumps(edit,indent=2)+'\n')
        edited.edit_files.append(history)
        edited.scene=compose_cad_parts([(b.stem,decoder(v,cancel=cancel)) for b,v in edited.parts],force_parts=True)
        edited.scene['cad']['conversion']=document.tool.description
        paths=[edited.snapshot,*[p for pair in edited.parts for p in pair],*edited.edit_files]
        if len(set(p.name for p in paths))!=len(paths) or sum(p.stat().st_size for p in paths)>MAX_EDIT_BYTES:
            raise ValueError('Edited CAD document exceeds its bounded file inventory.')
        edited.identities={p:file_sha256(p) for p in paths}
        edited.tool_receipt=document.tool_receipt
        document.verify();edited.verify()
        if cancel is not None and cancel.is_set():
            raise CadImportCancelled('CAD operation cancelled.')
        return edited
    except BaseException:
        edited.close()
        raise


class CadExport:
    def __init__(self):
        self.storage=TemporaryDirectory(prefix='prepomaxx-cad-export-')
        self.root=Path(self.storage.name)

    def publish(self,destination):
        destination=Path(destination)
        if destination.suffix.lower() not in ('.step','.stp'):
            raise ValueError('Choose a new .step or .stp destination.')
        if destination.exists() or destination.is_symlink():raise FileExistsError('Choose a new STEP filename.')
        if file_sha256(self.path)!=self.receipt['outputSha256']:
            raise ValueError('Validated STEP output changed before publication.')
        # Keep final publication on the destination filesystem, including when
        # the conversion workspace is on another volume/container mount.
        with TemporaryDirectory(prefix='.prepomaxx-step-',dir=destination.parent) as directory:
            staged=Path(directory)/'part.step'
            shutil.copyfile(self.path,staged)
            if file_sha256(staged)!=self.receipt['outputSha256']:
                raise ValueError('STEP bytes changed while staging publication.')
            os.link(staged,destination)
        return dict(self.receipt)

    def close(self):self.storage.cleanup()


def prepare_export(document,decoder,part_id,*,cancel=None):
    source=selected_part(document,part_id)
    export=CadExport()
    try:
        original=export.root/'input.brep';shutil.copyfile(source,original)
        export.path=export.root/'part.step'
        run_stage([*document.tool.command,'SAVE_BREP_AS_STEP',str(original),str(export.path)],
                  export.root,'export.log',cancel=cancel)
        require_output(export.path,MAX_CAD_BYTES)
        if file_sha256(original)!=document.identities[source]:raise ValueError('STEP export modified its staged input.')
        reopened=document.tool.convert_parts(export.path,export.root/'readback',cancel=cancel)
        scenes=[decoder(vis,cancel=cancel) for brep,vis in reopened]
        original_scene=decoder(document.parts[part_id-1][1],cancel=cancel)
        solids=sum(len(s['cad']['entities']['solid']) for s in scenes)
        if not solids or solids!=len(original_scene['cad']['entities']['solid']):
            raise ValueError('STEP readback changed the selected solid count.')
        document.verify()
        if cancel is not None and cancel.is_set():raise CadImportCancelled('STEP export cancelled.')
        export.receipt={'selectedPartId':part_id,'inputBrepSha256':file_sha256(source),
                        'outputSha256':file_sha256(export.path),'toolReceiptSha256':document.tool_receipt,
                        'geometryEditCount':len(document.edits),'reimportedSolids':solids,'nativeReadbackPassed':True}
        return export
    except BaseException:
        export.close();raise
