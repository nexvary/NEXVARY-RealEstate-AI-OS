cmake_minimum_required(VERSION 3.21)

project(RealEstateBusinessOS VERSION 2.1.0 LANGUAGES CXX)

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
set_target_properties(nexvary_realestate_native PROPERTIES OUTPUT_NAME "real_estate_business_os")

set(NEXVARY_QML_FILES
    qml/Main.qml
    qml/LoginPage.qml
    qml/FirstRunSetupPage.qml
    qml/DashboardPage.qml
    qml/LeadsPage.qml
    qml/InventoryPage.qml
    qml/AppointmentsPage.qml
    qml/FinancePage.qml
    qml/EnterpriseCrmPage.qml
    qml/CustomerTimelinePage.qml
    qml/CrmQuickAddDialog.qml
    qml/SettingsPage.qml
    qml/CompanyPage.qml
    qml/KnowledgePage.qml
    qml/TasksPage.qml
    qml/TeamPage.qml
    qml/OmnichannelPage.qml
    qml/GrowthPage.qml
    qml/SeoPage.qml
    qml/AutomationStudioPage.qml
    qml/AiSalesPage.qml
    qml/AboutSystemPage.qml
    qml/LicensePage.qml
    qml/LegalPage.qml
    qml/SidebarItem.qml
    qml/NavIcon.qml
)

# Keep every QML type at the URI root. Without explicit aliases, an installed
# build can register the files below a nested "qml/" namespace and
# QQmlApplicationEngine::loadFromModule() cannot resolve the Main type.
foreach(qml_file IN LISTS NEXVARY_QML_FILES)
    get_filename_component(qml_alias "${qml_file}" NAME)
    set_source_files_properties("${qml_file}" PROPERTIES QT_RESOURCE_ALIAS "${qml_alias}")
endforeach()

set_source_files_properties(qml/Theme.js PROPERTIES QT_RESOURCE_ALIAS "Theme.js")
set_source_files_properties(qml/LegalText.js PROPERTIES QT_RESOURCE_ALIAS "LegalText.js")
set_source_files_properties(
    assets/property-mark.svg
    PROPERTIES QT_RESOURCE_ALIAS "assets/property-mark.svg"
)

qt_add_qml_module(nexvary_realestate_native
    URI Business.RealEstate
    VERSION 1.0
    RESOURCE_PREFIX "/qt/qml"
    QML_FILES
        ${NEXVARY_QML_FILES}
    RESOURCES
        qml/Theme.js
        qml/LegalText.js
        assets/property-mark.svg
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
