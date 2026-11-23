/**************************************************************************/
/* File:   optmem.cpp                                                     */
/* Author: Joachim Schoeberl                                              */
/* Date:   04. Apr. 97                                                    */
/**************************************************************************/

/*
   Abstract data type Array
*/

#include <mystdlib.h>
#include <myadt.hpp>
#include <atomic>

namespace netgen
{
  namespace
  {
    // free lists of the calling thread, one per allocator slot
    enum { MAX_BLOCK_ALLOCATORS = 32 };

    struct ThreadFreeLists
    {
      void * list[MAX_BLOCK_ALLOCATORS];
      ThreadFreeLists ()
      {
        for (int i = 0; i < MAX_BLOCK_ALLOCATORS; i++)
          list[i] = NULL;
      }
    };

    thread_local ThreadFreeLists thread_free_lists;
    std::atomic<int> next_allocator_slot(0);
  }


  BlockAllocator :: BlockAllocator (unsigned asize, unsigned ablocks)
    : bablocks (0)
  {
    if (asize < sizeof(void*))
      asize = sizeof(void*);
    size = asize;
    blocks = ablocks;
    freelist = NULL;

    slot = next_allocator_slot.fetch_add(1);
    if (slot >= MAX_BLOCK_ALLOCATORS)
      slot = -1;
  }

  BlockAllocator :: ~BlockAllocator ()
  {
    for (int i = 0; i < bablocks.Size(); i++)
      delete [] bablocks[i];
  }

  void * BlockAllocator :: AllocChunk ()
  {
    char * hcp = new char [size * blocks];
    for (unsigned i = 0; i < blocks-1; i++)
      *(void**)&(hcp[i * size]) = &(hcp[ (i+1) * size]);
    *(void**)&(hcp[(blocks-1)*size]) = NULL;

    std::lock_guard<std::mutex> guard(mutex);
    bablocks.Append (hcp);
    return hcp;
  }

  void * BlockAllocator :: Alloc ()
  {
    if (slot >= 0)
      {
        void * & list = thread_free_lists.list[slot];
        if (!list)
          list = AllocChunk();
        void * p = list;
        list = *(void**)list;
        return p;
      }

    std::lock_guard<std::mutex> guard(mutex);
    if (!freelist)
      {
        char * hcp = new char [size * blocks];
        for (unsigned i = 0; i < blocks-1; i++)
          *(void**)&(hcp[i * size]) = &(hcp[ (i+1) * size]);
        *(void**)&(hcp[(blocks-1)*size]) = NULL;
        bablocks.Append (hcp);
        freelist = hcp;
      }
    void * p = freelist;
    freelist = *(void**)freelist;
    return p;
  }

  void BlockAllocator :: Free (void * p)
  {
    if (slot >= 0)
      {
        void * & list = thread_free_lists.list[slot];
        *(void**)p = list;
        list = p;
        return;
      }

    std::lock_guard<std::mutex> guard(mutex);
    *(void**)p = freelist;
    freelist = p;
  }
}
