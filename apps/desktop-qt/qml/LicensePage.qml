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
                text: apiClient.licenseValid
                    ? appState.localize(appState.language, "تأكيد الترخيص أولًا", "Confirm the license first")
                    : appState.localize(appState.language, "تفعيل النسخة", "Activate this copy")
                color: Theme.platinum; font.pixelSize: 30; font.bold: true
                horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
            }
            Text {
                Layout.fillWidth: true
                text: apiClient.licenseValid
                    ? appState.localize(appState.language, "هذه أول مرة يُفتح فيها هذا الإصدار. راجع الترخيص الموقّع ثم تابع إلى إعداد مساحة العمل.", "This is the first launch of this release. Review the signed license, then continue to workspace setup.")
                    : appState.localize(appState.language, "أرسل كود الجهاز إلى المورّد، ثم اختر ملف الترخيص الموقّع. لا يحتوي البرنامج على اسم المورّد أو العميل قبل التفعيل.", "Send the machine code to your vendor, then select the signed license file. The application contains no vendor or customer identity before activation.")
                color: Theme.silver; font.pixelSize: 14; wrapMode: Text.WordWrap
                horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
            }

            Rectangle {
                visible: apiClient.licenseValid
                Layout.fillWidth: true
                Layout.preferredHeight: 132
                radius: 14
                color: Theme.panelAlt
                border.width: 2
                border.color: Theme.emerald

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 14
                    layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight

                    Rectangle {
                        Layout.preferredWidth: 48; Layout.preferredHeight: 48; radius: 14
                        color: Theme.shellDeep; border.width: 1; border.color: Theme.emerald
                        Text { anchors.centerIn: parent; text: "✓"; color: Theme.emerald; font.pixelSize: 23; font.bold: true }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Text {
                            Layout.fillWidth: true
                            text: apiClient.licenseInfo.company || appState.localize(appState.language, "ترخيص موقّع صالح", "Valid signed license")
                            color: Theme.emerald; font.pixelSize: 18; font.bold: true
                            horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                        }
                        Text {
                            Layout.fillWidth: true
                            text: (apiClient.licenseInfo.edition || "professional") + " · " + (apiClient.licenseInfo.expires_at || appState.localize(appState.language, "دائم", "perpetual"))
                            color: Theme.silver; font.pixelSize: 12
                            horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                        }
                    }
                    Button {
                        text: appState.localize(appState.language, "متابعة بهذا الترخيص", "Continue with this license")
                        onClicked: appState.acceptCurrentLicense()
                    }
                }
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
                        Text { Layout.fillWidth: true; text: apiClient.licenseValid ? appState.localize(appState.language, "استبدال الترخيص (اختياري)", "Replace license (optional)") : appState.localize(appState.language, "ملف الترخيص", "License file"); color: Theme.platinum; font.pixelSize: 17; font.bold: true }
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
