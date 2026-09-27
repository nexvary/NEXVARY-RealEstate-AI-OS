cmake_minimum_required(VERSION 3.21)

project(NEXVARYRealEstateNative VERSION 2.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_AUTOMOC ON)

find_package(Qt6 6.4 REQUIRED COMPONENTS Core Quick QuickControls2 Network Test)
qt_standard_project_setup(REQUIRES 6.4)

add_library(realestate_native_core STATIC
    src/AppState.cpp
    src/AppState.hpp
    src/ApiClient.cpp
    src/ApiClient.hpp
)
target_link_libraries(realestate_native_core
    PUBLIC
        Qt6::Core
        Qt6::Network
)
target_include_directories(realestate_native_core PUBLIC src)

if(MSVC)
    target_compile_options(realestate_native_core PRIVATE /W4 /permissive-)
else()
    target_compile_options(realestate_native_core PRIVATE -Wall -Wextra -Wpedantic)
endif()

qt_add_executable(nexvary_realestate_native
    src/main.cpp
)

qt_add_qml_module(nexvary_realestate_native
    URI Nexvary.RealEstate
    VERSION 1.0
    QML_FILES
        qml/Main.qml
        qml/LoginPage.qml
        qml/DashboardPage.qml
        qml/SidebarItem.qml
    RESOURCES
        qml/Theme.js
        assets/nexvary-mark.svg
)

target_link_libraries(nexvary_realestate_native
    PRIVATE
        realestate_native_core
        Qt6::Quick
        Qt6::QuickControls2
        Qt6::Network
)

enable_testing()
qt_add_executable(native_core_tests
    tests/test_appstate.cpp
)
target_link_libraries(native_core_tests
    PRIVATE
        realestate_native_core
        Qt6::Test
)
add_test(NAME native_core_tests COMMAND native_core_tests)

install(TARGETS nexvary_realestate_native
    BUNDLE DESTINATION .
    RUNTIME DESTINATION bin
)
