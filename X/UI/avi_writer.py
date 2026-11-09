"""Uncompressed 24-bit AVI for platforms without VTK's Windows-only AVI writer.
RIFF layout: https://learn.microsoft.com/windows/win32/directshow/avi-riff-file-reference
Frames are native viewport pixels, never recomputed engineering data.
"""
import os,struct,tempfile
from fractions import Fraction
from pathlib import Path

def chunk(tag,data):return tag+struct.pack('<I',len(data))+data+(b'\0' if len(data)&1 else b'')
def group(tag,data):return chunk(b'LIST',tag+data)

class AviWriter:
    def __init__(self,path,width,height,rate,count):
        self.path=Path(path);self.width=int(width);self.height=int(height);self.rate=Fraction(str(rate)).limit_denominator(100000);self.count=int(count);self.entries=[]
        if min(self.width,self.height,self.count,self.rate)<=0 or max(self.width,self.height)>32767:raise ValueError('Invalid AVI dimensions, frame count or rate.')
        self.stride=(self.width*3+3)&~3;self.size=self.stride*self.height
        if 1024+self.count*(self.size+24)>=2**31:raise ValueError('This uncompressed AVI exceeds 2 GiB. Export a PNG sequence or Ogg video.')
        fd,self.temporary=tempfile.mkstemp(prefix='.'+self.path.name+'-',suffix='.tmp',dir=self.path.parent);self.file=os.fdopen(fd,'w+b')
        avih=struct.pack('<14I',round(1000000/float(self.rate)),round(self.size*float(self.rate)),0,0x10,self.count,0,1,self.size,self.width,self.height,0,0,0,0)
        strh=struct.pack('<4s4sIHHIIIIIIIIhhhh',b'vids',b'DIB ',0,0,0,0,self.rate.denominator,self.rate.numerator,0,self.count,self.size,0xffffffff,0,0,0,self.width,self.height)
        bitmap=struct.pack('<IiiHHIIiiII',40,self.width,self.height,1,24,0,self.size,0,0,0,0)
        header=group(b'hdrl',chunk(b'avih',avih)+group(b'strl',chunk(b'strh',strh)+chunk(b'strf',bitmap)))
        self.file.write(b'RIFF\0\0\0\0AVI '+header+b'LIST\0\0\0\0movi');self.movi=self.file.tell()-4
    def write(self,image):
        if len(self.entries)>=self.count:raise ValueError('More AVI frames than declared.')
        if tuple(image.GetDimensions()[:2])!=(self.width,self.height):raise ValueError('The viewport size changed during AVI export.')
        from vtkmodules.util.numpy_support import vtk_to_numpy
        import numpy as np
        pixels=vtk_to_numpy(image.GetPointData().GetScalars()).reshape(self.height,self.width,-1)
        data=np.zeros((self.height,self.stride),dtype=np.uint8);data[:,:self.width*3]=pixels[:,:,:3][:,:,::-1].reshape(self.height,self.width*3)
        self.entries.append((self.file.tell()-self.movi,self.size));self.file.write(chunk(b'00db',data.tobytes()))
    def finish(self):
        if len(self.entries)!=self.count:raise ValueError('AVI frame count is incomplete.')
        end=self.file.tell();self.file.seek(self.movi-4);self.file.write(struct.pack('<I',end-self.movi));self.file.seek(end)
        self.file.write(chunk(b'idx1',b''.join(struct.pack('<4sIII',b'00db',0x10,offset,size) for offset,size in self.entries)));end=self.file.tell();self.file.seek(4);self.file.write(struct.pack('<I',end-8));self.file.close();os.replace(self.temporary,self.path)
    def abort(self):
        if not self.file.closed:self.file.close()
        Path(self.temporary).unlink(missing_ok=True)
