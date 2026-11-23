#ifndef FILE_OPTMEM
#define FILE_OPTMEM

#include <mutex>

/**************************************************************************/
/* File:   optmem.hh                                                      */
/* Author: Joachim Schoeberl                                              */
/* Date:   04. Apr. 97                                                    */
/**************************************************************************/

namespace netgen
{

/**
    Optimized Memory allocation classes
*/

class BlockAllocator
{
private:
  ///
  unsigned size, blocks;
  /// free list used when no per-thread slot is available
  void * freelist;
  /// all allocated chunks, freed in the destructor
  Array<char*> bablocks;
  /// protects bablocks and freelist
  std::mutex mutex;
  /// slot of this allocator in the per-thread free lists, -1 = shared list
  int slot;
public:
  ///
  BlockAllocator (unsigned asize, unsigned ablocks = 100);
  ///
  ~BlockAllocator ();

  /*
    Every thread keeps its own free list per allocator, so concurrent meshing
    threads do not serialize on one mutex for every tree node.  Memory freed by
    a thread goes to that thread's list; the chunks themselves are shared and
    released when the allocator is destroyed.
  */
  void * Alloc ();
  ///
  void Free (void * p);

private:
  void * AllocChunk ();
};

}

#endif
