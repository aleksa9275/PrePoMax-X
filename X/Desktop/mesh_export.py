"""New-file mesh-only INP publication after original-reader verification."""
import hashlib,os
from pathlib import Path
from tempfile import TemporaryDirectory


def publish_mesh(contents,scene,destination,decoder):
    destination=Path(destination)
    if destination.suffix.lower()!='.inp':raise ValueError('Choose a new mesh-only .inp filename.')
    if destination.exists() or destination.is_symlink():raise FileExistsError('Choose a new mesh filename.')
    digest=hashlib.sha256(contents).hexdigest()
    if not 0<len(contents)<=16*1024*1024 or digest!=scene['SourceSha256']:
        raise ValueError('Mesh bytes changed since original-reader validation.')
    with TemporaryDirectory(prefix='.prepomaxx-mesh-',dir=destination.parent) as directory:
        staged=Path(directory)/'mesh.inp';staged.write_bytes(contents)
        checked=decoder(staged)
        if (checked['SourceSha256']!=digest or checked['nodes']!=scene['nodes'] or checked['elements']!=scene['elements']):
            raise ValueError('Original INP readback changed mesh identities or connectivity.')
        if hashlib.sha256(staged.read_bytes()).hexdigest()!=digest:raise ValueError('Staged mesh bytes changed.')
        os.link(staged,destination)
    return {'sha256':digest,'originalReadbackPassed':True,'meshOnly':True,'scope':'Mesh-only INP exchange; analysis/project state is omitted.'}
