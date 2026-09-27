import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Theme.js" as Theme

Item {
    id: root

    Dialog {
        id: appointmentDialog
        modal: true
        width: Math.min(520, root.width - 40)
        anchors.centerIn: parent
        background: Rectangle { radius: 17; color: Theme.panel; border.width: 1; border.color: Qt.rgba(.7,.8,.88,.32) }

        contentItem: ColumnLayout {
            spacing: 9
            Text { text: appState.rtl ? "معاينة / موعد جديد" : "New Viewing / Appointment"; color: Theme.platinum; font.pixelSize: 19; font.bold: true }
            ComboBox { id: leadField; Layout.fillWidth: true; model: apiClient.leads; textRole: "full_name"; valueRole: "id" }
            ComboBox {
                id: projectField
                Layout.fillWidth: true
                model: [{id:"",name:appState.rtl ? "بدون مشروع محدد" : "No project"}].concat(apiClient.projects)
                textRole: "name"
                valueRole: "id"
            }
            TextField {
                id: startsAtField
                Layout.fillWidth: true
                text: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
                placeholderText: "2026-09-28T18:00:00Z"
            }
            TextArea {
                id: notesField
                Layout.fillWidth: true
                Layout.preferredHeight: 80
                placeholderText: appState.rtl ? "ملاحظات الموعد" : "Appointment notes"
                wrapMode: TextEdit.WordWrap
            }
            RowLayout {
                Layout.fillWidth: true
                Button {
                    Layout.fillWidth: true
                    enabled: leadField.count > 0 && !apiClient.busy
                    text: appState.rtl ? "حفظ الموعد" : "Save Appointment"
                    onClicked: {
                        apiClient.createAppointment(
                            leadField.currentValue || "",
                            projectField.currentValue || "",
                            startsAtField.text,
                            notesField.text)
                        appointmentDialog.close()
                    }
                }
                Button { text: appState.rtl ? "إلغاء" : "Cancel"; onClicked: appointmentDialog.close() }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 11

        RowLayout {
            Layout.fillWidth: true
            layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
            ColumnLayout {
                Layout.fillWidth: true
                Text {
                    text: (appState.language, appState.t("appointments"))
                    color: Theme.platinum
                    font.family: appState.rtl ? "Noto Kufi Arabic" : "Segoe UI"
                    font.pixelSize: 29
                    font.bold: true
                }
                Text {
                    text: appState.rtl ? "جدولة المعاينات ومتابعة المواعيد المرتبطة بالعملاء" : "Schedule viewings and track customer appointments"
                    color: Theme.muted
                    font.pixelSize: 12
                }
            }
            Button { text: appState.rtl ? "+ موعد" : "+ Appointment"; enabled: apiClient.leads.length > 0; onClicked: appointmentDialog.open() }
            Button { text: (appState.language, appState.t("refresh")); onClicked: apiClient.refreshAll() }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: 15
            color: Theme.panel
            border.width: 1
            border.color: Qt.rgba(.67,.76,.83,.28)

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 13
                spacing: 7

                RowLayout {
                    Layout.fillWidth: true
                    layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
                    Text { text: appState.rtl ? "المواعيد القادمة" : "Appointments"; color: Theme.platinum; font.pixelSize: 17; font.bold: true }
                    Item { Layout.fillWidth: true }
                    Text { text: String(apiClient.appointments.length); color: Theme.electricCyan; font.pixelSize: 12; font.bold: true }
                }

                ListView {
                    id: list
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 6
                    model: apiClient.appointments

                    delegate: Rectangle {
                        required property var modelData
                        width: list.width
                        height: 68
                        radius: 9
                        color: index % 2 ? "#071521" : "#0A1B2A"
                        border.width: 1
                        border.color: Qt.rgba(.45,.58,.68,.14)

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 10
                            layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight

                            Rectangle {
                                width: 36; height: 36; radius: 9
                                color: "#071522"
                                border.width: 1
                                border.color: Theme.emerald
                                Text { anchors.centerIn: parent; text: "◫"; color: Theme.emerald; font.pixelSize: 16 }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2
                                Text {
                                    Layout.fillWidth: true
                                    text: appState.rtl ? "معاينة مرتبطة بالعميل" : "Customer viewing"
                                    color: Theme.platinum
                                    font.pixelSize: 12
                                    font.bold: true
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: (modelData.lead_id || "").slice(0,8) + (modelData.project_id ? " · " + String(modelData.project_id).slice(0,8) : "")
                                    color: Theme.muted
                                    font.pixelSize: 9
                                }
                            }

                            ColumnLayout {
                                Text {
                                    text: modelData.starts_at ? new Date(modelData.starts_at).toLocaleString(Qt.locale(appState.rtl ? "ar_EG" : "en_GB"), "dd MMM yyyy  HH:mm") : "—"
                                    color: Theme.silver
                                    font.pixelSize: 10
                                }
                                Text { text: modelData.status || "—"; color: Theme.electricBlue; font.pixelSize: 9 }
                            }
                        }
                    }
                }
            }
        }
    }
}
