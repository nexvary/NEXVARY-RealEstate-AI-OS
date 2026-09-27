import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Theme.js" as Theme

Item {
    id: root

    ColumnLayout {
        anchors.fill: parent
        spacing: 11

        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 3
                Text {
                    text: appState.t("customerTimeline")
                    color: Theme.platinum
                    font.family: appState.rtl ? "Noto Kufi Arabic" : "Segoe UI"
                    font.pixelSize: 29
                    font.bold: true
                }
                Text {
                    text: appState.t("timelineSelectLead")
                    color: Theme.muted
                    font.pixelSize: 12
                }
            }

            ComboBox {
                id: leadPicker
                Layout.preferredWidth: 300
                model: apiClient.leads
                textRole: "full_name"
                valueRole: "id"
                onActivated: apiClient.loadTimeline(currentValue)
                Component.onCompleted: {
                    if (count > 0)
                        apiClient.loadTimeline(currentValue)
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: 15
            color: Theme.panel
            border.width: 1
            border.color: Qt.rgba(0.66, 0.76, 0.83, 0.30)

            ListView {
                id: timelineView
                anchors.fill: parent
                anchors.margins: 14
                clip: true
                spacing: 7
                model: apiClient.timeline

                delegate: Rectangle {
                    required property var modelData
                    width: timelineView.width
                    height: 72
                    radius: 10
                    color: index % 2 ? "#071521" : "#0A1B2A"
                    border.width: 1
                    border.color: Qt.rgba(0.45, 0.58, 0.68, 0.16)

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        spacing: 10
                        layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight

                        Rectangle {
                            width: 38; height: 38; radius: 10
                            color: "#06131F"
                            border.width: 1
                            border.color: modelData.channel === "finance" ? Theme.gold
                                : modelData.channel === "support" ? Theme.violet
                                : modelData.channel === "calendar" ? Theme.emerald
                                : Theme.electricBlue
                            Text {
                                anchors.centerIn: parent
                                text: modelData.channel === "finance" ? "$"
                                    : modelData.channel === "support" ? "!"
                                    : modelData.channel === "calendar" ? "◫"
                                    : "◆"
                                color: parent.border.color
                                font.pixelSize: 15
                                font.bold: true
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 3
                            Text {
                                Layout.fillWidth: true
                                text: modelData.title || modelData.kind || "—"
                                color: Theme.platinum
                                font.pixelSize: 12
                                font.bold: true
                                horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                                elide: Text.ElideRight
                            }
                            Text {
                                Layout.fillWidth: true
                                text: (modelData.kind || "") + (modelData.channel ? " · " + modelData.channel : "")
                                color: Theme.muted
                                font.pixelSize: 9
                                horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                                elide: Text.ElideRight
                            }
                        }

                        Text {
                            text: modelData.occurred_at ? new Date(modelData.occurred_at).toLocaleString(Qt.locale(appState.rtl ? "ar_EG" : "en_GB"), "dd MMM yyyy  HH:mm") : ""
                            color: Theme.silver
                            font.pixelSize: 9
                        }
                    }
                }

                footer: Item {
                    width: timelineView.width
                    height: apiClient.timeline.length === 0 ? 120 : 0
                    Text {
                        visible: apiClient.timeline.length === 0
                        anchors.centerIn: parent
                        text: "—"
                        color: Theme.muted
                        font.pixelSize: 18
                    }
                }
            }
        }
    }
}
