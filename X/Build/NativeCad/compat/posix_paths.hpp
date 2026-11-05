#pragma once
#include <cstring>
#include <filesystem>
#include <stdexcept>
#include <string>

// The original assembly exporter uses the MSVC array-overload path helpers.
// Preserve its stem/suffix naming while accepting native absolute paths.
constexpr std::size_t _MAX_PATH = 4096;
constexpr std::size_t _MAX_DRIVE = 4;
constexpr std::size_t _MAX_DIR = _MAX_PATH;
constexpr std::size_t _MAX_FNAME = _MAX_PATH;
constexpr std::size_t _MAX_EXT = _MAX_PATH;

template<std::size_t N>
void NativeCadCopyPath(char (&target)[N], const std::string& value)
{
    if (value.size() >= N)
        throw std::length_error("CAD output path exceeds the native path buffer");
    std::memcpy(target, value.c_str(), value.size() + 1);
}

template<std::size_t D, std::size_t P, std::size_t F, std::size_t E>
void _splitpath_s(const char* filename, char (&drive)[D], char (&directory)[P],
                  char (&stem)[F], char (&extension)[E])
{
    const std::filesystem::path path(filename);
    NativeCadCopyPath(drive, "");
    std::string parent = path.parent_path().string();
    if (!parent.empty() && parent.back() != '/') parent += '/';
    NativeCadCopyPath(directory, parent);
    NativeCadCopyPath(stem, path.stem().string());
    NativeCadCopyPath(extension, path.extension().string());
}

template<std::size_t N>
void _makepath_s(char (&target)[N], const char* drive, const char* directory,
                 const char* stem, const char* extension)
{
    NativeCadCopyPath(target, std::string(drive) + directory + stem + extension);
}
