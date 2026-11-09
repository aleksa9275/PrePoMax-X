"""Marshal Qt work to its main thread while original .NET native jobs run."""
import queue
import threading
from PyQt6 import QtCore

class Dispatcher:
    def __init__(self):
        self.owner=threading.get_ident()
        self.pending=queue.Queue()
        self.timer=QtCore.QTimer()
        self.timer.timeout.connect(self.drain)
        self.timer.start(10)

    def call(self,callback):
        if threading.get_ident()==self.owner:return callback()
        done=threading.Event();result=[]
        self.pending.put((callback,done,result))
        done.wait()
        success,value=result[0]
        if not success:raise value
        return value

    def post(self,callback):
        if threading.get_ident()==self.owner:return callback()
        self.pending.put((callback,None,None))

    def drain(self):
        while True:
            try:callback,done,result=self.pending.get_nowait()
            except queue.Empty:return
            if done is None:callback();continue
            try:result.append((True,callback()))
            except Exception as error:result.append((False,error))
            finally:done.set()
