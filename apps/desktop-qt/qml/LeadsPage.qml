import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Theme.js" as Theme

Item {
    id: root
    property var selectedLead: null

    Dialog {
        id: leadDialog
        modal: true
        width: Math.min(560, root.width - 40)
        anchors.centerIn: parent
        property bool editing: false

        function openNew() {
            editing = false
            root.selectedLead = null
            nameField.text = ""
            phoneField.text = ""
            emailField.text = ""
            sourceField.text = "manual"
            cityField.text = ""
            budgetField.text = ""
            bedroomsField.value = 0
            statusField.currentIndex = 0
            notesField.text = ""
            open()
        }

        function openEdit(item) {
            editing = true
            root.selectedLead = item
            nameField.text = item.full_name || ""
            phoneField.text = item.phone || ""
            emailField.text = item.email || ""
            sourceField.text = item.source || "manual"
            cityField.text = item.preferred_city || ""
            budgetField.text = item.budget === null || item.budget === undefined ? "" : String(item.budget)
            bedroomsField.value = item.bedrooms === null || item.bedrooms === undefined ? 0 : Number(item.bedrooms)
            var statuses = ["new", "qualified", "viewing", "negotiation", "won", "lost"]
            statusField.currentIndex = Math.max(0, statuses.indexOf(item.status || "new"))
            notesField.text = item.notes || ""
            open()
        }

        background: Rectangle {
            radius: 18
            color: Theme.panel
            border.width: 1
            border.color: Qt.rgba(0.72,0.82,0.9,.34)
        }

        contentItem: ColumnLayout {
            spacing: 10
            Text {
                Layout.fillWidth: true
                text: leadDialog.editing
                    ? (appState.localize(appState.language, "تعديل العميل المحتمل", "Edit Lead"))
                    : (appState.localize(appState.language, "عميل محتمل جديد", "New Lead"))
                color: Theme.platinum
                font.family: appState.localize(appState.language, "Noto Kufi Arabic", "Segoe UI")
                font.pixelSize: 20
                font.bold: true
                horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
            }
            TextField { id: nameField; visible: !leadDialog.editing; Layout.fillWidth: true; placeholderText: appState.localize(appState.language, "الاسم", "Full name") }
            TextField { id: phoneField; visible: !leadDialog.editing; Layout.fillWidth: true; placeholderText: appState.localize(appState.language, "الهاتف", "Phone") }
            TextField { id: emailField; visible: !leadDialog.editing; Layout.fillWidth: true; placeholderText: appState.localize(appState.language, "البريد الإلكتروني", "Email") }
            TextField { id: sourceField; visible: !leadDialog.editing; Layout.fillWidth: true; placeholderText: appState.localize(appState.language, "المصدر", "Source") }
            TextField { id: cityField; Layout.fillWidth: true; placeholderText: appState.localize(appState.language, "المدينة المفضلة", "Preferred city") }
            RowLayout {
                Layout.fillWidth: true
                TextField {
                    id: budgetField
                    Layout.fillWidth: true
                    placeholderText: appState.localize(appState.language, "الميزانية", "Budget")
                    inputMethodHints: Qt.ImhFormattedNumbersOnly
                }
                SpinBox {
                    id: bedroomsField
                    from: 0
                    to: 20
                    editable: true
                    Layout.preferredWidth: 120
                }
            }
            ComboBox {
                id: statusField
                visible: leadDialog.editing
                Layout.fillWidth: true
                model: ["new", "qualified", "viewing", "negotiation", "won", "lost"]
            }
            TextArea {
                id: notesField
                Layout.fillWidth: true
                Layout.preferredHeight: 90
                placeholderText: appState.localize(appState.language, "ملاحظات", "Notes")
                wrapMode: TextEdit.WordWrap
            }
            Text {
                visible: apiClient.lastError.length > 0
                Layout.fillWidth: true
                text: apiClient.lastError
                color: Theme.danger
                font.pixelSize: 11
                wrapMode: Text.WordWrap
            }
            RowLayout {
                Layout.fillWidth: true
                layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
                Button {
                    Layout.fillWidth: true
                    enabled: !apiClient.busy
                    text: apiClient.busy ? "…" : (appState.localize(appState.language, "حفظ", "Save"))
                    onClicked: {
                        if (leadDialog.editing && root.selectedLead) {
                            apiClient.updateLead(
                                root.selectedLead.id,
                                statusField.currentText,
                                cityField.text,
                                budgetField.text.length ? Number(budgetField.text) : -1,
                                bedroomsField.value,
                                notesField.text)
                        } else {
                            apiClient.createLead(
                                nameField.text,
                                phoneField.text,
                                emailField.text,
                                sourceField.text,
                                cityField.text,
                                Number(budgetField.text || 0),
                                bedroomsField.value,
                                notesField.text)
                        }
                        leadDialog.close()
                    }
                }
                Button { text: appState.localize(appState.language, "إلغاء", "Cancel"); onClicked: leadDialog.close() }
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
                    text: (appState.language, appState.t("leads"))
                    color: Theme.platinum
                    font.family: appState.localize(appState.language, "Noto Kufi Arabic", "Segoe UI")
                    font.pixelSize: 29
                    font.bold: true
                }
                Text {
                    text: appState.localize(appState.language, "إدارة العملاء المحتملين والتأهيل والمتابعة", "Lead management, qualification and follow-up")
                    color: Theme.muted
                    font.pixelSize: 12
                }
            }
            Rectangle {
                width: 130; height: 44; radius: 11
                color: Theme.panel
                border.width: 1
                border.color: Theme.borderSoft
                Column {
                    anchors.centerIn: parent
                    spacing: 1
                    Text { anchors.horizontalCenter: parent.horizontalCenter; text: String(apiClient.leads.length); color: Theme.electricCyan; font.pixelSize: 18; font.bold: true }
                    Text { anchors.horizontalCenter: parent.horizontalCenter; text: appState.localize(appState.language, "إجمالي العملاء", "Total leads"); color: Theme.muted; font.pixelSize: 11 }
                }
            }
            Button { text: appState.localize(appState.language, "+ عميل جديد", "+ New Lead"); onClicked: leadDialog.openNew() }
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
                spacing: 8

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 42
                    radius: 8
                    color: "#071522"
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
                        Text { Layout.preferredWidth: 210; text: appState.localize(appState.language, "العميل", "Lead"); color: Theme.silver; font.pixelSize: 11; font.bold: true }
                        Text { Layout.preferredWidth: 100; text: appState.localize(appState.language, "الحالة", "Status"); color: Theme.silver; font.pixelSize: 11; font.bold: true }
                        Text { Layout.preferredWidth: 70; text: appState.localize(appState.language, "التقييم", "Score"); color: Theme.silver; font.pixelSize: 11; font.bold: true }
                        Text { Layout.fillWidth: true; text: appState.localize(appState.language, "المصدر / المدينة", "Source / City"); color: Theme.silver; font.pixelSize: 11; font.bold: true }
                        Text { Layout.preferredWidth: 150; text: appState.localize(appState.language, "إجراءات", "Actions"); color: Theme.silver; font.pixelSize: 11; font.bold: true }
                    }
                }

                ListView {
                    id: leadList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 5
                    model: apiClient.leads

                    delegate: Rectangle {
                        required property var modelData
                        width: leadList.width
                        height: 60
                        radius: 9
                        color: index % 2 ? "#071521" : "#0A1B2A"
                        border.width: 1
                        border.color: Qt.rgba(.45,.58,.68,.14)

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 12
                            spacing: 8
                            layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight

                            ColumnLayout {
                                Layout.preferredWidth: 210
                                spacing: 1
                                Text { Layout.fillWidth: true; text: modelData.full_name || "—"; color: Theme.platinum; font.pixelSize: 12; font.bold: true; elide: Text.ElideRight }
                                Text { Layout.fillWidth: true; text: modelData.phone || ""; color: Theme.muted; font.pixelSize: 11; elide: Text.ElideRight }
                            }

                            Rectangle {
                                Layout.preferredWidth: 100
                                Layout.preferredHeight: 28
                                radius: 8
                                color: modelData.status === "won" ? Qt.rgba(.15,.55,.38,.18)
                                    : modelData.status === "lost" ? Qt.rgba(.65,.2,.25,.15)
                                    : Qt.rgba(.15,.45,.7,.14)
                                Text { anchors.centerIn: parent; text: modelData.status || "—"; color: modelData.status === "won" ? Theme.emerald : modelData.status === "lost" ? Theme.danger : Theme.electricBlue; font.pixelSize: 11; font.bold: true }
                            }

                            Text {
                                Layout.preferredWidth: 70
                                text: String(modelData.score === undefined ? 0 : modelData.score)
                                color: Number(modelData.score || 0) >= 70 ? Theme.emerald : Theme.gold
                                font.pixelSize: 15
                                font.bold: true
                            }

                            Text {
                                Layout.fillWidth: true
                                text: (modelData.source || "—") + " · " + (modelData.preferred_city || "—")
                                color: Theme.muted
                                font.pixelSize: 11
                                elide: Text.ElideRight
                            }

                            RowLayout {
                                Layout.preferredWidth: 150
                                spacing: 5
                                Button { text: appState.localize(appState.language, "تعديل", "Edit"); onClicked: leadDialog.openEdit(modelData) }
                                Button {
                                    text: appState.localize(appState.language, "السجل", "Timeline")
                                    onClicked: {
                                        apiClient.loadTimeline(modelData.id)
                                        appState.navigate("timeline")
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
