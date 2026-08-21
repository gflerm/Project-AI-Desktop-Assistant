cmake_minimum_required(VERSION 3.16)

include($ENV{IDF_PATH}/tools/cmake/project.cmake)

# ESP-IDF configures the bootloader and other firmware pieces as nested CMake
# projects. Forward explicit tool locations/flags supplied by our sandbox build
# wrapper so those child configurations use the same working toolchain.
foreach(project_tool_setting IN ITEMS
        CMAKE_MAKE_PROGRAM
        CMAKE_PROGRAM_PATH
        CMAKE_C_COMPILER
        CMAKE_CXX_COMPILER
        CMAKE_ASM_COMPILER
        CMAKE_OBJDUMP
        CMAKE_C_FLAGS
        CMAKE_CXX_FLAGS
        CMAKE_ASM_FLAGS
        CMAKE_EXE_LINKER_FLAGS)
    if(DEFINED ${project_tool_setting} AND NOT "${${project_tool_setting}}" STREQUAL "")
        string(REPLACE "\\" "/" project_tool_value "${${project_tool_setting}}")
        idf_build_set_property(
            EXTRA_CMAKE_ARGS
            "-D${project_tool_setting}=${project_tool_value}"
            APPEND)
    endif()
endforeach()

project(project_james)
