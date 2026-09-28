import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import "LegalText.js" as LegalText

Item {
    id: root
    property string licenseText: ""

    FileDialog {
        id: licenseDialog
        title: appState.localize(appState.language, "اختر ملف الترخيص", "Select license file")
        nameFilters: ["License files (*.license *.json)", "All files (*)"]
        onAccepted: {
            root.licenseText = apiClient.readTextFile(selectedFile, 1048576)
            licenseArea.text = root.licenseText
        }
    }

    ScrollView {
        anchors.fill: parent
        clip: true
        ColumnLayout {
            width: Math.min(900, root.width - 32)
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 16

            Text {
                Layout.fillWidth: true
                text: appState.localize(appState.language, "تفعيل النسخة", "Activate this copy")
                color: Theme.platinum; font.pixelSize: 30; font.bold: true
                horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
            }
            Text {
                Layout.fillWidth: true
                text: appState.localize(appState.language, "أرسل كود الجهاز إلى المورّد، ثم اختر ملف الترخيص الموقّع. لا يحتوي البرنامج على اسم المورّد أو العميل قبل التفعيل.", "Send the machine code to your vendor, then select the signed license file. The application contains no vendor or customer identity before activation.")
                color: Theme.silver; font.pixelSize: 14; wrapMode: Text.WordWrap
                horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
            }

            Rectangle {
                Layout.fillWidth: true; Layout.preferredHeight: 112; radius: 14
                color: Theme.panel; border.width: 2; border.color: Theme.metallicSilver
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 15
                    Text { text: appState.localize(appState.language, "كود هذا الجهاز", "THIS COMPUTER CODE"); color: Theme.electricCyan; font.pixelSize: 12; font.bold: true }
                    TextField {
                        Layout.fillWidth: true; readOnly: true; selectByMouse: true
                        text: apiClient.machineCode
                        font.family: "Consolas"; font.pixelSize: 19; font.bold: true
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true; Layout.preferredHeight: 300; radius: 14
                color: Theme.panel; border.width: 2; border.color: Theme.metallicSilverDark
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 15; spacing: 10
                    RowLayout {
                        Layout.fillWidth: true
                        Text { Layout.fillWidth: true; text: appState.localize(appState.language, "ملف الترخيص", "License file"); color: Theme.platinum; font.pixelSize: 17; font.bold: true }
                        Button { text: appState.localize(appState.language, "اختيار ملف", "Choose file"); onClicked: licenseDialog.open() }
                    }
                    TextArea {
                        id: licenseArea; Layout.fillWidth: true; Layout.fillHeight: true
                        placeholderText: appState.localize(appState.language, "أو الصق محتوى الترخيص هنا", "Or paste the license content here")
                        wrapMode: TextEdit.WrapAnywhere; font.family: "Consolas"; font.pixelSize: 12
                    }
                }
            }

            CheckBox {
                id: agreement
                Layout.fillWidth: true
                text: appState.localize(appState.language, "قرأت ووافقت على اتفاقية المستخدم والترخيص وسياسة حماية البرنامج.", "I have read and accept the user and license agreement and software-protection policy.")
                font.pixelSize: 13
            }
            Text {
                visible: apiClient.lastError.length > 0; Layout.fillWidth: true
                text: apiClient.lastError; color: Theme.danger; font.pixelSize: 13; wrapMode: Text.WordWrap
            }
            RowLayout {
                Layout.fillWidth: true
                Button { text: appState.localize(appState.language, "عرض الاتفاقية", "View agreement"); onClicked: legalDialog.open() }
                Item { Layout.fillWidth: true }
                Button {
                    text: apiClient.busy ? appState.localize(appState.language, "جاري التحقق...", "Verifying...") : appState.localize(appState.language, "تفعيل آمن", "Activate securely")
                    enabled: agreement.checked && licenseArea.text.trim().length > 0 && !apiClient.busy
                    onClicked: apiClient.activateLicense(licenseArea.text, agreement.checked)
                }
            }
        }
    }

    Dialog {
        id: legalDialog; anchors.centerIn: parent; width: Math.min(820, root.width - 50); height: Math.min(650, root.height - 50)
        title: appState.localize(appState.language, "اتفاقية المستخدم والترخيص", "User and license agreement"); modal: true; standardButtons: Dialog.Close
        ScrollView { anchors.fill: parent; Text { width: legalDialog.availableWidth; text: LegalText.full(appState.language); color: Theme.platinum; font.pixelSize: 13; wrapMode: Text.WordWrap } }
    }
}
