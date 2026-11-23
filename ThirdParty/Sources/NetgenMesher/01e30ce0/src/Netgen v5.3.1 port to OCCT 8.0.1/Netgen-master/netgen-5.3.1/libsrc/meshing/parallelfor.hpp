#ifndef FILE_PARALLELFOR
#define FILE_PARALLELFOR

/**************************************************************************/
/* File:   parallelfor.hpp                                                */
/* Purpose: worker dispatch shared by the parallel meshing paths          */
/**************************************************************************/

#include <atomic>
#include <exception>
#include <mutex>
#include <thread>
#include <vector>

namespace netgen
{
  /// Worker count for item_count independent items, from mp.parallel_meshing_threads
  /// (1 = serial, greater than 1 = explicit worker count).
  inline int ParallelMeshingThreads (const MeshingParameters & mp, int item_count)
  {
    int threads = mp.parallel_meshing_threads;
    if (threads < 1)
      threads = 1;
    if (threads > item_count)
      threads = item_count;
    return threads;
  }


  /*
    Runs function(item) for item = 0 .. item_count-1 on thread_count threads, the
    calling thread included.  Items are handed out dynamically, so a long item
    does not block the short ones behind it.  With thread_count 1 everything runs
    inline on the calling thread.  The first exception thrown by a worker is
    rethrown to the caller after all threads have finished.
  */
  template <typename FUNCTION>
  void ParallelForItems (int item_count, int thread_count, const FUNCTION & function)
  {
    if (item_count <= 0)
      return;

    if (thread_count <= 1)
      {
        for (int i = 0; i < item_count; i++)
          function(i);
        return;
      }

    std::atomic<int> next(0);
    std::atomic<bool> failed(false);
    std::exception_ptr first_exception;
    std::mutex exception_mutex;

    auto worker = [&] ()
    {
      while (!failed.load())
        {
          const int item = next.fetch_add(1);
          if (item >= item_count)
            return;

          try
            {
              function(item);
            }
          catch (...)
            {
              std::lock_guard<std::mutex> guard(exception_mutex);
              if (!first_exception)
                first_exception = std::current_exception();
              failed.store(true);
            }
        }
    };

    std::vector<std::thread> threads;
    for (int i = 1; i < thread_count; i++)
      threads.emplace_back(worker);
    worker();
    for (size_t i = 0; i < threads.size(); i++)
      threads[i].join();

    if (first_exception)
      std::rethrow_exception(first_exception);
  }
}

#endif
