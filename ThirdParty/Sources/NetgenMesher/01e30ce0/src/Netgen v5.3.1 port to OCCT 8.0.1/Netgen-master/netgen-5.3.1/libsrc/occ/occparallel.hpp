#ifndef FILE_OCCPARALLEL
#define FILE_OCCPARALLEL

#include <OSD_ThreadPool.hxx>

#include <algorithm>
#include <atomic>
#include <exception>
#include <mutex>

namespace netgen
{
  /**
     Per-stage executor for OCC meshing.

     A private OCCT pool avoids changing the process-wide default pool and makes
     the worker budget explicit.  Workers must write only to task-local result
     slots; the caller remains responsible for deterministic serial commit.
  */
  class OCCParallelMeshingContext
  {
    OSD_ThreadPool pool;
    int thread_count;

  public:
    explicit OCCParallelMeshingContext(int requested_threads)
      : pool(std::max(1, requested_threads)),
        thread_count(pool.NbThreads())
    {
    }

    int ThreadCount() const
    {
      return thread_count;
    }

    bool IsParallel(int item_count) const
    {
      return thread_count > 1 && item_count > 1;
    }

    template <typename FUNCTION>
    void ParallelFor(int item_count, const FUNCTION & function)
    {
      if (item_count <= 0)
        return;

      if (!IsParallel(item_count))
      {
        for (int i = 0; i < item_count; i++)
          function(0, i);
        return;
      }

      std::atomic<bool> failed(false);
      std::exception_ptr first_exception;
      std::mutex exception_mutex;

      OSD_ThreadPool::Launcher launcher(pool, std::min(thread_count, item_count));
      launcher.Perform(0, item_count,
        [&] (int thread_index, int item_index)
        {
          if (failed.load())
            return;

          try
          {
            function(thread_index, item_index);
          }
          catch (...)
          {
            std::lock_guard<std::mutex> guard(exception_mutex);
            if (!first_exception)
              first_exception = std::current_exception();
            failed.store(true);
          }
        });

      if (first_exception)
        std::rethrow_exception(first_exception);
    }
  };
}

#endif
