#!/usr/bin/env python3
"""Decode an exported movie with the existing pinned Qt multimedia backend."""
import argparse,json
from pathlib import Path
from PyQt6 import QtCore,QtMultimedia
p=argparse.ArgumentParser();p.add_argument('video',type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
app=QtCore.QCoreApplication([]);player=QtMultimedia.QMediaPlayer();sink=QtMultimedia.QVideoSink();player.setVideoSink(sink);frames=[];errors=[]
def frame(value):
 if value.isValid():frames.append({'width':value.width(),'height':value.height(),'startTime':value.startTime(),'endTime':value.endTime(),'imageValid':not value.toImage().isNull()})
sink.videoFrameChanged.connect(frame)
player.errorOccurred.connect(lambda error,text:(errors.append(str(text)),app.quit()))
player.mediaStatusChanged.connect(lambda status:app.quit() if status==QtMultimedia.QMediaPlayer.MediaStatus.EndOfMedia else None)
player.setSource(QtCore.QUrl.fromLocalFile(str(a.video.resolve())));player.play();QtCore.QTimer.singleShot(20000,app.quit);app.exec();report={'success':bool(frames) and not errors and all(f['imageValid'] for f in frames),'frames':frames,'errors':errors,'durationMs':player.duration()};player.stop();a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'success':report['success'],'frames':len(frames),'errors':errors}));raise SystemExit(0 if report['success'] else 1)
