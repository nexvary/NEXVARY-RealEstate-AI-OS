import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Theme.js" as Theme

Flickable {
    id: root
    contentWidth: width
    contentHeight: content.implicitHeight + 30
    clip: true

    ColumnLayout {
        id: content
        width: root.width
        spacing: 14

        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 3
                Text {
                    text: appState.t("dashboard")
                    color: Theme.platinum
                    font.family: appState.rtl ? "Noto Kufi Arabic" : "Segoe UI"
                    font.pixelSize: 30
                    font.bold: true
                }
                Text {
                    text: appState.t("liveData") + " · FastAPI / C++ Qt Network"
                    color: Theme.muted
                    font.pixelSize: 12
                }
            }

            Button {
                text: appState.t("refresh")
                onClicked: apiClient.refreshAll()
            }
        }

        GridLayout {
            Layout.fillWidth: true
            columns: root.width > 1050 ? 5 : root.width > 720 ? 3 : 2
            columnSpacing: 10
            rowSpacing: 10

            Repeater {
                model: [
                    {key:"leads_total", label:appState.t("totalLeads"), accent:Theme.electricBlue},
                    {key:"leads_hot", label:appState.t("hotLeads"), accent:Theme.emerald},
                    {key:"units_available", label:appState.t("availableUnits"), accent:Theme.violet},
                    {key:"appointments_total", label:appState.t("viewings"), accent:Theme.gold},
                    {key:"active_reservations", label:appState.t("reservations"), accent:Theme.electricCyan}
                ]

                Rectangle {
                    required property var modelData
                    Layout.fillWidth: true
                    Layout.preferredHeight: 132
                    radius: 14
                    color: Theme.panel
                    border.width: 1
                    border.color: Theme.borderSoft

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 15
                        spacing: 7
                        Rectangle {
                            width: 34; height: 34; radius: 9
                            color: Qt.rgba(0.04, 0.10, 0.16, 0.94)
                            border.width: 1
                            border.color: modelData.accent
                            Text {
                                anchors.centerIn: parent
                                text: "◆"
                                color: modelData.accent
                                font.pixelSize: 14
                            }
                        }
                        Text {
                            text: apiClient.overview[modelData.key] === undefined ? "—" : apiClient.overview[modelData.key]
                            color: Theme.platinum
                            font.pixelSize: 27
                            font.bold: true
                        }
                        Text {
                            text: modelData.label
                            color: Theme.muted
                            font.pixelSize: 12
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                    }
                }
            }
        }

        GridLayout {
            Layout.fillWidth: true
            columns: root.width > 900 ? 2 : 1
            columnSpacing: 12
            rowSpacing: 12

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 390
                radius: 15
                color: Theme.panel
                border.width: 1
                border.color: Theme.borderSoft

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 9

                    Text {
                        text: appState.t("leads")
                        color: Theme.platinum
                        font.pixelSize: 17
                        font.bold: true
                    }

                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        spacing: 5
                        model: apiClient.leads.slice(0, 8)

                        delegate: Rectangle {
                            required property var modelData
                            width: ListView.view.width
                            height: 48
                            radius: 8
                            color: index % 2 ? "#081521" : "#0A1825"

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 10
                                anchors.rightMargin: 10
                                layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight

                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.full_name || "—"
                                    color: Theme.platinum
                                    font.pixelSize: 12
                                    horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                                }
                                Text {
                                    text: modelData.status || "—"
                                    color: Theme.emerald
                                    font.pixelSize: 10
                                }
                            }
                        }
                    }

                    Text {
                        visible: apiClient.leads.length === 0
                        text: "—"
                        color: Theme.muted
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 390
                radius: 15
                color: Theme.panel
                border.width: 1
                border.color: Theme.borderSoft

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 9

                    Text {
                        text: appState.t("inventory")
                        color: Theme.platinum
                        font.pixelSize: 17
                        font.bold: true
                    }

                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        spacing: 5
                        model: apiClient.units.slice(0, 8)

                        delegate: Rectangle {
                            required property var modelData
                            width: ListView.view.width
                            height: 48
                            radius: 8
                            color: index % 2 ? "#081521" : "#0A1825"

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 10
                                anchors.rightMargin: 10
                                layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight

                                Text {
                                    Layout.fillWidth: true
                                    text: (modelData.code || "—") + " · " + (modelData.unit_type || "")
                                    color: Theme.platinum
                                    font.pixelSize: 12
                                    horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                                }
                                Text {
                                    text: modelData.status || "—"
                                    color: modelData.status === "available" ? Theme.emerald : Theme.gold
                                    font.pixelSize: 10
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
