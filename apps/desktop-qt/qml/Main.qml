import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Theme.js" as Theme

ApplicationWindow {
    id: root
    width: 1600
    height: 900
    minimumWidth: 1180
    minimumHeight: 720
    visible: true
    title: appState.t("appTitle")
    color: Theme.bg

    property real uiScale: Math.max(0.92, Math.min(1.22, width / 1600.0))
    property var navItems: [
        {page:"dashboard", key:"dashboard", symbol:"⌂"},
        {page:"leads", key:"leads", symbol:"◎"},
        {page:"inventory", key:"inventory", symbol:"▦"},
        {page:"appointments", key:"appointments", symbol:"◫"},
        {page:"finance", key:"finance", symbol:"$"},
        {page:"enterprise", key:"enterpriseCrm", symbol:"▣"},
        {page:"timeline", key:"customerTimeline", symbol:"↯"},
        {page:"inbox", key:"inbox", symbol:"✉"},
        {page:"knowledge", key:"knowledge", symbol:"▤"},
        {page:"tasks", key:"tasks", symbol:"✓"},
        {page:"team", key:"team", symbol:"♙"},
        {page:"settings", key:"settings", symbol:"⚙"},
        {page:"ai", key:"ai", symbol:"✦"},
        {page:"seo", key:"seo", symbol:"⌕"},
        {page:"growth", key:"growth", symbol:"◉"},
        {page:"automation", key:"automation", symbol:"↻"},
        {page:"about", key:"about", symbol:"ⓘ"},
        {page:"company", key:"company", symbol:"◆"}
    ]

    RowLayout {
        id: shellLayout
        anchors.fill: parent
        spacing: 0
        layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight

        Rectangle {
            id: sidebar
            objectName: "sidebar"
            Layout.preferredWidth: Math.round(292 * root.uiScale)
            Layout.minimumWidth: 265
            Layout.maximumWidth: 330
            Layout.fillHeight: true
            color: Theme.shell
            border.width: 1
            border.color: Theme.borderSoft

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 13
                spacing: 8
                layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight

                RowLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 84
                    spacing: 11
                    layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight

                    Rectangle {
                        Layout.preferredWidth: 67
                        Layout.preferredHeight: 67
                        radius: 18
                        color: "#050D16"
                        border.width: 1
                        border.color: Theme.electricBlue

                        Image {
                            anchors.fill: parent
                            anchors.margins: 5
                            source: "qrc:/Nexvary/RealEstate/assets/nexvary-mark.svg"
                            fillMode: Image.PreserveAspectFit
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        Text {
                            Layout.fillWidth: true
                            text: "NEXVARY"
                            color: Theme.platinum
                            font.pixelSize: 19
                            font.bold: true
                            font.letterSpacing: 2
                            horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                        }
                        Text {
                            Layout.fillWidth: true
                            text: "REALESTATE AI OS"
                            color: Theme.electricCyan
                            font.pixelSize: 9
                            font.bold: true
                            font.letterSpacing: 1.1
                            horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                        }
                        Text {
                            Layout.fillWidth: true
                            text: "QT 6 · C++20 · QML"
                            color: Theme.gold
                            font.pixelSize: 9
                            horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                        }
                    }
                }

                Rectangle { Layout.fillWidth: true; height: 1; color: Theme.borderSoft }

                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                    ScrollBar.vertical.policy: ScrollBar.AsNeeded

                    ColumnLayout {
                        width: parent.width
                        spacing: 5

                        Repeater {
                            model: root.navItems
                            delegate: SidebarItem {
                                required property var modelData
                                required property int index
                                label: appState.t(modelData.key)
                                symbol: modelData.symbol
                                pageId: modelData.page
                                itemIndex: index
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 62
                    radius: 11
                    color: Theme.shellDeep
                    border.width: 1
                    border.color: Theme.borderSoft

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight

                        Rectangle {
                            width: 8; height: 8; radius: 4
                            color: apiClient.healthStatus === "ok" ? Theme.emerald : Theme.gold
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 1
                            Text {
                                text: apiClient.loggedIn ? apiClient.userName : "API + RBAC"
                                color: Theme.platinum
                                font.pixelSize: 11
                            }
                            Text {
                                text: apiClient.loggedIn ? apiClient.userRole : apiClient.healthStatus
                                color: Theme.muted
                                font.pixelSize: 9
                            }
                        }

                        Button {
                            visible: apiClient.loggedIn
                            text: "×"
                            flat: true
                            onClicked: {
                                apiClient.logout()
                                appState.resetNavigation()
                            }
                        }
                    }
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 76
                color: "#06101B"
                border.width: 1
                border.color: Theme.borderSoft

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 18
                    anchors.rightMargin: 18
                    spacing: 10
                    layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight

                    Button {
                        visible: apiClient.loggedIn && appState.currentPage !== "dashboard"
                        text: (appState.rtl ? "→ " : "← ") + appState.t("back")
                        onClicked: appState.goBack()
                    }

                    Item { Layout.fillWidth: true }

                    Rectangle {
                        Layout.preferredWidth: 170
                        Layout.preferredHeight: 50
                        radius: 11
                        color: Theme.panel
                        border.width: 1
                        border.color: Theme.borderSoft

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 8
                            spacing: 8
                            layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight

                            Text {
                                text: "◷"
                                color: Theme.electricCyan
                                font.pixelSize: 19
                            }
                            ColumnLayout {
                                spacing: 0
                                Text {
                                    text: appState.currentTime
                                    color: Theme.platinum
                                    font.family: "Consolas"
                                    font.pixelSize: 15
                                    font.bold: true
                                    font.letterSpacing: 1
                                }
                                Text {
                                    text: appState.currentDate
                                    color: Theme.muted
                                    font.pixelSize: 9
                                }
                            }
                        }
                    }

                    Button {
                        text: appState.language === "ar" ? "EN" : "AR"
                        onClicked: appState.language = appState.language === "ar" ? "en" : "ar"
                    }
                }
            }

            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true

                Loader {
                    anchors.fill: parent
                    anchors.margins: 22
                    sourceComponent: !apiClient.loggedIn
                        ? loginComponent
                        : appState.currentPage === "dashboard"
                            ? dashboardComponent
                            : appState.currentPage === "leads"
                                ? leadsComponent
                                : appState.currentPage === "inventory"
                                    ? inventoryComponent
                                    : appState.currentPage === "appointments"
                                        ? appointmentsComponent
                                        : appState.currentPage === "finance"
                                        ? financeComponent
                                        : appState.currentPage === "enterprise"
                                            ? enterpriseComponent
                                            : appState.currentPage === "timeline"
                                                ? timelineComponent
                                                : appState.currentPage === "inbox"
                                                    ? omnichannelComponent
                                                    : appState.currentPage === "knowledge"
                                                        ? knowledgeComponent
                                                        : appState.currentPage === "tasks"
                                                            ? tasksComponent
                                                            : appState.currentPage === "team"
                                                                ? teamComponent
                                                                : appState.currentPage === "growth"
                                                                    ? growthComponent
                                                                    : appState.currentPage === "settings"
                                                                        ? settingsComponent
                                                                    : appState.currentPage === "company"
                                                                        ? companyComponent
                                                                        : migrationComponent
                }
            }
        }
    }

    Component {
        id: loginComponent
        LoginPage {}
    }

    Component {
        id: dashboardComponent
        DashboardPage {}
    }

    Component {
        id: leadsComponent
        LeadsPage {}
    }

    Component {
        id: inventoryComponent
        InventoryPage {}
    }

    Component {
        id: appointmentsComponent
        AppointmentsPage {}
    }

    Component {
        id: financeComponent
        FinancePage {}
    }

    Component {
        id: enterpriseComponent
        EnterpriseCrmPage {}
    }

    Component {
        id: timelineComponent
        CustomerTimelinePage {}
    }

    Component {
        id: omnichannelComponent
        OmnichannelPage {}
    }

    Component {
        id: knowledgeComponent
        KnowledgePage {}
    }

    Component {
        id: tasksComponent
        TasksPage {}
    }

    Component {
        id: teamComponent
        TeamPage {}
    }

    Component {
        id: growthComponent
        GrowthPage {}
    }

    Component {
        id: settingsComponent
        SettingsPage {}
    }

    Component {
        id: companyComponent
        CompanyPage {}
    }

    Component {
        id: migrationComponent
        Item {
            ColumnLayout {
                anchors.centerIn: parent
                width: Math.min(700, parent.width - 40)
                spacing: 14

                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    width: 72; height: 72; radius: 18
                    color: Theme.panelAlt
                    border.width: 1
                    border.color: Theme.violet
                    Text {
                        anchors.centerIn: parent
                        text: "Qt"
                        color: Theme.violet
                        font.pixelSize: 20
                        font.bold: true
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: appState.t("nativeMigration") + " · " + appState.t(appState.currentPage)
                    color: Theme.platinum
                    font.family: appState.rtl ? "Noto Kufi Arabic" : "Segoe UI"
                    font.pixelSize: 26
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                }

                Text {
                    Layout.fillWidth: true
                    text: appState.t("migrationNotice")
                    color: Theme.muted
                    font.pixelSize: 13
                    wrapMode: Text.WordWrap
                    horizontalAlignment: Text.AlignHCenter
                }

                Text {
                    Layout.fillWidth: true
                    text: "C++20  •  Qt 6  •  QML  •  CMake  •  Qt Network"
                    color: Theme.electricCyan
                    font.pixelSize: 12
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }
    }
}
