import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Theme.js" as Theme

Item {
    id: root

    Dialog {
        id: taskDialog
        modal: true
        width: Math.min(540, root.width - 40)
        anchors.centerIn: parent
        background: Rectangle { radius: 18; color: Theme.panel; border.width: 1; border.color: Qt.rgba(.72,.82,.89,.34) }
        contentItem: ColumnLayout {
            spacing: 9
            Text { text: appState.localize(appState.language, "مهمة متابعة جديدة", "New Follow-up Task"); color: Theme.platinum; font.pixelSize: 20; font.bold: true }
            TextField { id: titleField; Layout.fillWidth: true; placeholderText: appState.localize(appState.language, "عنوان المهمة", "Task title") }
            ComboBox { id: leadField; Layout.fillWidth: true; model: [{id:"",full_name:appState.localize(appState.language, "بدون عميل", "No lead")}].concat(apiClient.leads); textRole: "full_name"; valueRole: "id" }
            ComboBox { id: userField; Layout.fillWidth: true; model: [{id:"",display_name:appState.localize(appState.language, "غير مسند", "Unassigned")}].concat(apiClient.users); textRole: "display_name"; valueRole: "id" }
            TextField { id: dueField; Layout.fillWidth: true; text: new Date(Date.now()+24*3600*1000).toISOString(); placeholderText: "2026-09-28T12:00:00Z" }
            TextArea { id: notesField; Layout.fillWidth: true; Layout.preferredHeight: 90; placeholderText: appState.localize(appState.language, "الملاحظات", "Notes"); wrapMode: TextEdit.WordWrap }
            RowLayout {
                Layout.fillWidth: true; layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
                Button {
                    Layout.fillWidth: true; enabled: titleField.text.length >= 2 && !apiClient.busy
                    text: appState.localize(appState.language, "إنشاء المهمة", "Create Task")
                    onClicked: {
                        apiClient.createTask(leadField.currentValue || "", userField.currentValue || "", titleField.text, notesField.text, dueField.text)
                        taskDialog.close()
                    }
                }
                Button { text: appState.localize(appState.language, "إلغاء", "Cancel"); onClicked: taskDialog.close() }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent; spacing: 11

        RowLayout {
            Layout.fillWidth: true; layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
            ColumnLayout {
                Layout.fillWidth: true
                Text { text: (appState.language, appState.t("tasks")); color: Theme.platinum; font.family: appState.localize(appState.language, "Noto Kufi Arabic", "Segoe UI"); font.pixelSize: 29; font.bold: true }
                Text { text: appState.localize(appState.language, "متابعة المبيعات والتسليم والتحويل البشري", "Sales follow-up, delivery and human-handoff tasks"); color: Theme.muted; font.pixelSize: 12 }
            }
            Button { text: appState.localize(appState.language, "+ مهمة", "+ Task"); onClicked: taskDialog.open() }
            Button { text: (appState.language, appState.t("refresh")); onClicked: apiClient.refreshWorkspace() }
        }

        GridLayout {
            Layout.fillWidth: true
            columns: 3
            columnSpacing: 9
            Repeater {
                model: [
                    {v:apiClient.tasks.filter(function(x){return x.status==="open"}).length,l:appState.localize(appState.language, "مفتوحة", "Open"),c:Theme.electricBlue},
                    {v:apiClient.tasks.filter(function(x){return x.status==="done"}).length,l:appState.localize(appState.language, "مكتملة", "Done"),c:Theme.emerald},
                    {v:apiClient.tasks.length,l:appState.localize(appState.language, "الإجمالي", "Total"),c:Theme.violet}
                ]
                Rectangle {
                    required property var modelData
                    Layout.fillWidth: true; Layout.preferredHeight: 82; radius: 12
                    color: Theme.panel; border.width: 1; border.color: Qt.rgba(.67,.76,.83,.24)
                    RowLayout {
                        anchors.fill: parent; anchors.margins: 12; layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
                        Rectangle { width: 30; height: 30; radius: 8; color: "#071522"; border.width: 1; border.color: modelData.c; Text { anchors.centerIn: parent; text: "✓"; color: modelData.c; font.bold: true } }
                        ColumnLayout { Layout.fillWidth: true; Text { text: String(modelData.v); color: Theme.platinum; font.pixelSize: 21; font.bold: true } Text { text: modelData.l; color: Theme.muted; font.pixelSize: 11 } }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true; Layout.fillHeight: true; radius: 15
            color: Theme.panel; border.width: 1; border.color: Qt.rgba(.67,.76,.83,.26)
            ListView {
                id: list
                anchors.fill: parent; anchors.margins: 13; clip: true; spacing: 6
                model: apiClient.tasks
                delegate: Rectangle {
                    required property var modelData
                    width: list.width; height: 70; radius: 9
                    color: index % 2 ? "#071521" : "#0A1B2A"
                    RowLayout {
                        anchors.fill: parent; anchors.margins: 10; spacing: 9
                        layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
                        Rectangle {
                            width: 35; height: 35; radius: 9; color: "#071522"; border.width: 1
                            border.color: modelData.status === "done" ? Theme.emerald : Theme.electricBlue
                            Text { anchors.centerIn: parent; text: modelData.status === "done" ? "✓" : "◷"; color: parent.border.color; font.bold: true }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true; spacing: 2
                            Text { Layout.fillWidth: true; text: modelData.title || "—"; color: Theme.platinum; font.pixelSize: 12; font.bold: true; elide: Text.ElideRight }
                            Text { Layout.fillWidth: true; text: (modelData.notes || "") + (modelData.due_at ? " · " + new Date(modelData.due_at).toLocaleString(Qt.locale(appState.localize(appState.language, "ar_EG", "en_GB")),"dd MMM HH:mm") : ""); color: Theme.muted; font.pixelSize: 11; elide: Text.ElideRight }
                        }
                        Text { text: modelData.status || ""; color: modelData.status === "done" ? Theme.emerald : Theme.gold; font.pixelSize: 11; font.bold: true }
                        Button { visible: modelData.status === "open"; text: appState.localize(appState.language, "إكمال", "Complete"); onClicked: apiClient.completeTask(modelData.id) }
                    }
                }
            }
        }
    }
}
