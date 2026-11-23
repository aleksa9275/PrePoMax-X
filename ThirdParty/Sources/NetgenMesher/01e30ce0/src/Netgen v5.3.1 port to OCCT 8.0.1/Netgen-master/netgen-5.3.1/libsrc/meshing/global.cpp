#include <mystdlib.h>
#include "meshing.hpp"
#include <atomic>


namespace netgen
{
  // stringstream emptystr;
  // ostream * testout = &emptystr;
  // testout -> clear(ios::failbit);

  // ostream * testout = &cout;
  static ostream & NullTestOut ()
  {
    static ostream nullstream(0);
    return nullstream;
  }

  thread_local ostream * testout = &NullTestOut();

  // NetgenOutStream * testout = new NetgenOutStream;

  ostream * mycout = &cout;
  ostream * myerr = &cerr;


  //  Flags parameters;


  int silentflag = 0;
  thread_local int testmode = 0;

  volatile multithreadt multithread;

  string ngdir = ".";

  thread_local Array<int> tets_in_qualclass;

  static std::atomic<int> nonmanifold_face_notices(0);

  void NoteNonManifoldFace ()
  {
    ++nonmanifold_face_notices;
  }

  int NonManifoldFaceNotices ()
  {
    return nonmanifold_face_notices.load();
  }

  void ResetNonManifoldFaceNotices ()
  {
    nonmanifold_face_notices.store(0);
  }

  int h_argc = 0;
  char ** h_argv = NULL;

  multithreadt :: multithreadt()
  {
    pause =0;
    testmode = 0;
    redraw = 0;
    drawing = 0;
    terminate = 0;
    running = 0;
    percent = 0;
    task = "";
  }

  DebugParameters debugparam;
  bool verbose = 0;

  static std::atomic<int> timestamp(0);
  int GetTimeStamp() 
  { 
    return timestamp.load();
  }

  int NextTimeStamp()
  {
    return ++timestamp;
  }
}
