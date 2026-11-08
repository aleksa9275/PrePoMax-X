// PrePoMax-X C ABI over the QuadMesher Gmsh integration (qmorph_gmsh.h), so the
// portable GmshCommon assembly can call it through P/Invoke exactly as the
// original C++/CLI GmshCommon/QMorph.h does. Build into libpmx_qmorph together
// with the QuadMesher sources and the platform's Gmsh library.
//
// Status (2026-11-08): QuadMesher is present in the repository only as Windows
// static libraries; its source must be recovered before this can be built for
// macOS/Linux (dependency gap recorded in the Phase A report).
#include "qmorph/qmorph_gmsh.h"

#include <cstdlib>
#include <cstring>
#include <exception>
#include <string>
#include <vector>

extern "C" {

struct pmx_qmorph_face_report
{
    int tag;
    int qmorph;
    char *reason;
    int background;
    int triangles;
    int quads;
    double p95Condition;
    double maxCondition;
    double minAngle;
    double maxAngle;
    double seconds;
    int periodic;
    int singular;
};

static char *dup_string(const std::string &s)
{
    char *p = static_cast<char *>(std::malloc(s.size() + 1));
    std::memcpy(p, s.c_str(), s.size() + 1);
    return p;
}

static std::vector<int> to_vector(const int *values, size_t n)
{
    return values ? std::vector<int>(values, values + n) : std::vector<int>();
}

#if defined(_WIN32)
#define PMX_API __declspec(dllexport)
#else
#define PMX_API __attribute__((visibility("default")))
#endif

PMX_API void pmx_qmorph_free(void *p) { std::free(p); }

PMX_API int pmx_qmorph_make_face_node_counts_even(const int *tags, size_t n, int *result, char **error)
{
    try { *result = qmg::makeFaceNodeCountsEven(to_vector(tags, n)); return 0; }
    catch (const std::exception &e) { *error = dup_string(e.what()); return 1; }
}

PMX_API int pmx_qmorph_set_background_algorithms(const int *tags, size_t n, char **error)
{
    try { qmg::setBackgroundAlgorithms(to_vector(tags, n)); return 0; }
    catch (const std::exception &e) { *error = dup_string(e.what()); return 1; }
}

PMX_API int pmx_qmorph_quad_mesh_surfaces(const int *tags, size_t n, int cleanup, const int *alternatives,
                                          size_t alternatives_n, pmx_qmorph_face_report **reports,
                                          size_t *reports_n, char **error)
{
    try
    {
        qm::Options options;
        options.cleanup = cleanup != 0;
        std::vector<qmg::FaceReport> r =
            qmg::quadMeshSurfaces(to_vector(tags, n), options, to_vector(alternatives, alternatives_n));
        auto *out = static_cast<pmx_qmorph_face_report *>(std::malloc(sizeof(pmx_qmorph_face_report) * (r.empty() ? 1 : r.size())));
        for (size_t i = 0; i < r.size(); i++)
        {
            out[i] = {r[i].tag, r[i].qmorph ? 1 : 0, dup_string(r[i].reason), r[i].background, r[i].triangles,
                      r[i].quads, r[i].p95, r[i].maxCondition, r[i].minAngle, r[i].maxAngle, r[i].seconds,
                      r[i].periodic ? 1 : 0, r[i].singular ? 1 : 0};
        }
        *reports = out;
        *reports_n = r.size();
        return 0;
    }
    catch (const std::exception &e) { *error = dup_string(e.what()); return 1; }
}

}
