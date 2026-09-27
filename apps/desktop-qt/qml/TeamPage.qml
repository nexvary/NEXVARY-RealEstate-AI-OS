import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Theme.js" as Theme

Item {
    id: root
    property bool canManage: apiClient.userRole === "owner" || apiClient.userRole === "admin"

    Dialog {
        id: userDialog
        modal: true
        width: Math.min(520, root.width - 40)
        anchors.centerIn: parent
        background: Rectangle { radius: 18; color: Theme.panel; border.width: 1; border.color: Qt.rgba(.72,.82,.89,.34) }
        contentItem: ColumnLayout {
            spacing: 9
            Text { text: appState.rtl ? "إضافة عضو للفريق" : "Add Team Member"; color: Theme.platinum; font.pixelSize: 20; font.bold: true }
            TextField { id: nameField; Layout.fillWidth: true; placeholderText: appState.rtl ? "الاسم" : "Display name" }
            TextField { id: emailField; Layout.fillWidth: true; placeholderText: "Email" }
            TextField { id: passwordField; Layout.fillWidth: true; echoMode: TextInput.Password; placeholderText: appState.rtl ? "كلمة مرور مبدئية" : "Initial password" }
            ComboBox { id: roleField; Layout.fillWidth: true; model: ["admin","sales_manager","sales_agent","finance","viewer"] }
            RowLayout {
                Layout.fillWidth: true; layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
                Button {
                    Layout.fillWidth: true
                    enabled: root.canManage && nameField.text.length >= 2 && emailField.text.length >= 5 && passwordField.text.length >= 10
                    text: appState.rtl ? "إضافة المستخدم" : "Add User"
                    onClicked: {
                        apiClient.createUser(emailField.text, nameField.text, passwordField.text, roleField.currentText)
                        userDialog.close()
                    }
                }
                Button { text: appState.rtl ? "إلغاء" : "Cancel"; onClicked: userDialog.close() }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent; spacing: 11

        RowLayout {
            Layout.fillWidth: true; layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
            ColumnLayout {
                Layout.fillWidth: true
                Text { text: appState.t("team"); color: Theme.platinum; font.family: appState.rtl ? "Noto Kufi Arabic" : "Segoe UI"; font.pixelSize: 29; font.bold: true }
                Text { text: appState.rtl ? "الفريق والأدوار والصلاحيات المعتمدة على RBAC" : "Team, roles and RBAC permissions"; color: Theme.muted; font.pixelSize: 12 }
            }
            Button { visible: root.canManage; text: appState.rtl ? "+ مستخدم" : "+ User"; onClicked: userDialog.open() }
            Button { text: appState.t("refresh"); onClicked: apiClient.refreshWorkspace() }
        }

        Rectangle {
            Layout.fillWidth: true; Layout.fillHeight: true; radius: 15
            color: Theme.panel; border.width: 1; border.color: Qt.rgba(.67,.76,.83,.26)
            ColumnLayout {
                anchors.fill: parent; anchors.margins: 13; spacing: 8
                RowLayout {
                    Layout.fillWidth: true
                    Text { text: appState.rtl ? "أعضاء الشركة" : "Company Members"; color: Theme.platinum; font.pixelSize: 17; font.bold: true }
                    Item { Layout.fillWidth: true }
                    Text { text: String(apiClient.users.length); color: Theme.electricCyan; font.pixelSize: 12; font.bold: true }
                }
                ListView {
                    id: list
                    Layout.fillWidth: true; Layout.fillHeight: true; clip: true; spacing: 6
                    model: apiClient.users
                    delegate: Rectangle {
                        required property var modelData
                        width: list.width; height: 64; radius: 9
                        color: index % 2 ? "#071521" : "#0A1B2A"
                        RowLayout {
                            anchors.fill: parent; anchors.margins: 10; spacing: 9
                            layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
                            Rectangle {
                                width: 36; height: 36; radius: 18
                                color: "#071522"; border.width: 1
                                border.color: modelData.role === "owner" ? Theme.gold : modelData.role === "admin" ? Theme.violet : Theme.electricBlue
                                Text { anchors.centerIn: parent; text: String(modelData.display_name || "?").charAt(0).toUpperCase(); color: parent.border.color; font.pixelSize: 14; font.bold: true }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true; spacing: 2
                                Text { Layout.fillWidth: true; text: modelData.display_name || "—"; color: Theme.platinum; font.pixelSize: 12; font.bold: true; elide: Text.ElideRight }
                                Text { Layout.fillWidth: true; text: modelData.email || ""; color: Theme.muted; font.pixelSize: 9; elide: Text.ElideRight }
                            }
                            Rectangle {
                                width: 120; height: 28; radius: 8; color: Qt.rgba(.1,.35,.55,.14); border.width: 1; border.color: Qt.rgba(.35,.7,.95,.18)
                                Text { anchors.centerIn: parent; text: modelData.role || "—"; color: Theme.silver; font.pixelSize: 9; font.bold: true }
                            }
                        }
                    }
                }
            }
        }
    }
}
