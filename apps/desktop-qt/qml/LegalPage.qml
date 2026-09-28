import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "LegalText.js" as LegalText

Item {
    ScrollView {
        anchors.fill: parent; clip: true
        ColumnLayout {
            width: Math.min(1050, parent.width); spacing: 14
            Text { Layout.fillWidth: true; text: appState.localize(appState.language, "اتفاقية المستخدم والترخيص", "User & license agreement"); color: Theme.platinum; font.pixelSize: 29; font.bold: true }
            Rectangle {
                Layout.fillWidth: true; implicitHeight: legalBody.implicitHeight + 40; radius: 15
                color: Theme.panel; border.width: 2; border.color: Theme.metallicSilver
                Text { id: legalBody; anchors.fill: parent; anchors.margins: 20; text: LegalText.full(appState.language); color: Theme.silver; font.pixelSize: 14; lineHeight: 1.35; wrapMode: Text.WordWrap }
            }
            Rectangle {
                Layout.fillWidth: true; implicitHeight: 92; radius: 13; color: Theme.panelAlt; border.width: 1; border.color: Theme.metallicSilverDark
                RowLayout { anchors.fill: parent; anchors.margins: 15
                    ColumnLayout { Layout.fillWidth: true
                        Text { text: appState.localize(appState.language, "الترخيص الحالي", "Current license"); color: Theme.electricCyan; font.pixelSize: 13; font.bold: true }
                        Text { text: (apiClient.licenseInfo.company || "—") + " · " + (apiClient.licenseInfo.edition || "—") + " · " + (apiClient.licenseInfo.expires_at || appState.localize(appState.language, "دائم", "Perpetual")); color: Theme.platinum; font.pixelSize: 14 }
                    }
                    Rectangle { width: 12; height: 12; radius: 6; color: Theme.emerald; border.width: 1; border.color: Theme.metallicSilverLight }
                }
            }
        }
    }
}
