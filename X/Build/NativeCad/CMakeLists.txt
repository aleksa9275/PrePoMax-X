cmake_minimum_required(VERSION 3.20)
project(PrePoMaxXNativeCad LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
find_package(Threads REQUIRED)
find_package(ZLIB REQUIRED)
find_package(OpenCASCADE 8.0.1 EXACT CONFIG REQUIRED COMPONENTS
  FoundationClasses ModelingData ModelingAlgorithms Visualization ApplicationFramework DataExchange)
include("${CMAKE_CURRENT_BINARY_DIR}/sources.cmake")
add_library(nglib SHARED ${NETGEN_SOURCES})
target_compile_definitions(nglib PRIVATE OCCGEOMETRY HAVE_CONFIG_H OCCT_NO_DEPRECATED)
target_include_directories(nglib PRIVATE "${NETGEN_ROOT}" "${NETGEN_ROOT}/libsrc/include"
  "${NETGEN_ROOT}/nglib" "${OpenCASCADE_INCLUDE_DIR}" "${CMAKE_CURRENT_SOURCE_DIR}/compat")
target_link_directories(nglib PRIVATE "${OpenCASCADE_LIBRARY_DIR}")
target_link_libraries(nglib PRIVATE Threads::Threads ZLIB::ZLIB
  TKernel TKMath TKG2d TKG3d TKGeomBase TKGeomAlgo TKBRep TKTopAlgo TKBO TKBool
  TKPrim TKOffset TKFillet TKShHealing TKMesh TKXSBase TKDEIGES TKDESTEP TKDESTL
  TKXCAF TKLCAF)
add_executable(NetGenMesher "${MESHER_ROOT}/NetGenLibTest.cpp")
target_compile_definitions(NetGenMesher PRIVATE OCCT_NO_DEPRECATED OCCGEOMETRY)
target_include_directories(NetGenMesher PRIVATE "${NETGEN_ROOT}/nglib" "${OpenCASCADE_INCLUDE_DIR}"
  "${CMAKE_CURRENT_SOURCE_DIR}/compat")
target_link_directories(NetGenMesher PRIVATE "${OpenCASCADE_LIBRARY_DIR}")
target_link_libraries(NetGenMesher PRIVATE nglib TKernel TKMath TKG2d TKG3d
  TKGeomBase TKBRep TKTopAlgo TKBO TKBool TKGeomAlgo)
set_target_properties(nglib PROPERTIES INSTALL_RPATH "@loader_path")
set_target_properties(NetGenMesher PROPERTIES INSTALL_RPATH "@loader_path/../lib")
if(UNIX AND NOT APPLE)
  set_target_properties(nglib PROPERTIES INSTALL_RPATH "$ORIGIN")
  set_target_properties(NetGenMesher PROPERTIES INSTALL_RPATH "$ORIGIN/../lib")
endif()
install(TARGETS nglib NetGenMesher RUNTIME DESTINATION bin LIBRARY DESTINATION lib)
