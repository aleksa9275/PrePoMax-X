"""Bounded owned geometry checkpoints; no command replay or project format."""
MAX_CHECKPOINTS=32
MAX_CHECKPOINT_BYTES=256*1024*1024


class GeometryHistory:
    def __init__(self,*,maximum_count=MAX_CHECKPOINTS,maximum_bytes=MAX_CHECKPOINT_BYTES):
        self.undo=[];self.redo=[]
        self.maximum_count=maximum_count;self.maximum_bytes=maximum_bytes

    def validate_edit(self,current,candidate):
        current.verify();candidate.verify()
        if len(self.undo)>=self.maximum_count:
            raise ValueError('CAD geometry undo has reached its 32-checkpoint preview limit.')
        documents={id(d):d for d in [*self.undo,current,candidate]}
        total=sum(path.stat().st_size for d in documents.values() for path in d.identities)
        if total>self.maximum_bytes:
            raise ValueError('Retained CAD checkpoint inputs exceed the 256 MiB preview limit.')

    def edited(self,previous):
        for document in self.redo:document.close()
        self.redo.clear();self.undo.append(previous)

    def clear(self):
        documents={id(d):d for d in [*self.undo,*self.redo]}
        self.undo.clear();self.redo.clear()
        for document in documents.values():document.close()

    def target(self,direction):
        stack=self.undo if direction=='undo' else self.redo if direction=='redo' else None
        if not stack:raise ValueError('No CAD geometry '+direction+' is available.')
        stack[-1].verify()
        return stack[-1]

    def restored(self,direction,current):
        source,destination=(self.undo,self.redo) if direction=='undo' else (self.redo,self.undo)
        source.pop();destination.append(current)
