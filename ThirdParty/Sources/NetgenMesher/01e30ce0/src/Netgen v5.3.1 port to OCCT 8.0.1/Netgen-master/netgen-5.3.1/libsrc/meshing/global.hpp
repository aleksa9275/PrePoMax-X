#ifndef FILE_GLOBAL
#define FILE_GLOBAL


/**************************************************************************/
/* File:   global.hh                                                      */
/* Author: Joachim Schoeberl                                              */
/* Date:   01. Okt. 95                                                    */
/**************************************************************************/

/*
  global functions and variables
*/

namespace netgen
{

  ///
  DLL_HEADER extern double GetTime ();
  extern void ResetTime ();

  ///
  extern thread_local int testmode;

  /// calling parameters
  // extern Flags parameters;

  // extern DLL_HEADER MeshingParameters mparam;

  extern thread_local Array<int> tets_in_qualclass;

  /*
    A face claimed by more than two volume elements of one subdomain.  The
    advancing front produces such a face occasionally and repairs it in a
    later step, so it is counted while meshing and judged afterwards on the
    finished mesh instead of being reported as an error on the spot.
  */
  DLL_HEADER void NoteNonManifoldFace ();
  DLL_HEADER int NonManifoldFaceNotices ();
  DLL_HEADER void ResetNonManifoldFaceNotices ();

  class multithreadt
  {
  public:
    int pause;
    int testmode;
    int redraw;
    int drawing;
    int terminate;
    int running;
    double percent;
    const char * task;
    bool demorunning;
    multithreadt();
  };

  extern volatile multithreadt multithread;

  DLL_HEADER extern string ngdir;
  extern DebugParameters debugparam;
  extern bool verbose;  

  extern int h_argc;
  extern char ** h_argv;
}

#endif
