add_executable(common_pwrforge_project_path)
target_sources(common_pwrforge_project_path PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/common_pwrforge_project_path.cpp)
target_include_directories(common_pwrforge_project_path PRIVATE ${CMAKE_CURRENT_SOURCE_DIR} ${CONAN_LIB_DIRS})

target_link_libraries(common_pwrforge_project_path ${CONAN_LIBS})

