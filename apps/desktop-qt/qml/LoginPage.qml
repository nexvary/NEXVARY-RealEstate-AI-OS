import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    Rectangle {
        anchors.centerIn: parent
        width: Math.min(560, parent.width - 48)
        height: 590
        radius: 22
        color: Theme.panel
        border.width: 1
        border.color: Theme.borderSoft

        Rectangle {
            anchors.fill: parent
            anchors.margins: 1
            radius: 21
            color: "transparent"
            border.width: 1
            border.color: Qt.rgba(0.85, 0.92, 0.97, 0.07)
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 30
            spacing: 13

            Rectangle {
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: 76
                Layout.preferredHeight: 76
                radius: 20
                color: "#071522"
                border.width: 1
                border.color: Theme.electricBlue

                Image {
                    anchors.fill: parent
                    anchors.margins: 7
                    source: "qrc:/qt/qml/Business/RealEstate/assets/property-mark.svg"
                    fillMode: Image.PreserveAspectFit
                }
            }

            Text {
                Layout.fillWidth: true
                text: (appState.language, appState.t("secureWorkspace"))
                color: Theme.electricCyan
                font.pixelSize: 11
                font.bold: true
                font.letterSpacing: 1.8
                horizontalAlignment: Text.AlignHCenter
            }

            Text {
                Layout.fillWidth: true
                text: (appState.language, appState.t("loginTitle"))
                color: Theme.platinum
                font.family: appState.localize(appState.language, "Noto Kufi Arabic", "Segoe UI")
                font.pixelSize: 27
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
            }

            Text {
                Layout.fillWidth: true
                text: (appState.language, appState.t("loginText"))
                color: Theme.muted
                font.pixelSize: 13
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
            }

            Item { Layout.preferredHeight: 4 }

            TextField {
                id: tenant
                Layout.fillWidth: true
                Layout.preferredHeight: 48
                placeholderText: (appState.language, appState.t("companyId"))
                horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                onTextChanged: apiClient.clearError()
            }

            TextField {
                id: email
                Layout.fillWidth: true
                Layout.preferredHeight: 48
                placeholderText: (appState.language, appState.t("email"))
                inputMethodHints: Qt.ImhEmailCharactersOnly
                horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                onTextChanged: apiClient.clearError()
            }

            TextField {
                id: password
                Layout.fillWidth: true
                Layout.preferredHeight: 48
                placeholderText: (appState.language, appState.t("password"))
                echoMode: TextInput.Password
                horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                onAccepted: loginButton.clicked()
                onTextChanged: apiClient.clearError()
            }

            Rectangle {
                visible: apiClient.lastError.length > 0
                Layout.fillWidth: true
                Layout.preferredHeight: errorText.implicitHeight + 20
                radius: 9
                color: Qt.rgba(0.55, 0.10, 0.15, 0.15)
                border.width: 1
                border.color: Qt.rgba(1.0, 0.45, 0.50, 0.28)

                Text {
                    id: errorText
                    anchors.fill: parent
                    anchors.margins: 10
                    text: apiClient.lastError
                    color: Theme.danger
                    wrapMode: Text.WordWrap
                    font.pixelSize: 11
                    horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                }
            }

            Button {
                id: loginButton
                Layout.fillWidth: true
                Layout.preferredHeight: 50
                enabled: !apiClient.busy && tenant.text.trim().length > 0
                    && email.text.trim().length > 0 && password.text.length > 0
                text: apiClient.busy ? "…" : (appState.language, appState.t("signIn"))
                onClicked: apiClient.login(tenant.text, email.text, password.text)

                background: Rectangle {
                    radius: 11
                    color: loginButton.down ? "#2079B3" : Theme.electricBlue
                    border.width: 1
                    border.color: Theme.electricCyan
                }
                contentItem: Text {
                    text: loginButton.text
                    color: "#02101A"
                    font.bold: true
                    font.pixelSize: 14
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }

            Button {
                id: developmentButton
                visible: apiClient.developmentWorkspace
                Layout.fillWidth: true
                Layout.preferredHeight: 46
                enabled: !apiClient.busy
                text: appState.localize(appState.language, "فتح مساحة العمل السابقة", "Open previous workspace")
                onClicked: apiClient.resumeDevelopmentWorkspace()

                background: Rectangle {
                    radius: 11
                    color: developmentButton.down ? "#122C40" : "#0B1C2A"
                    border.width: 1
                    border.color: Theme.gold
                }
                contentItem: Text {
                    text: developmentButton.text
                    color: Theme.gold
                    font.bold: true
                    font.pixelSize: 13
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }

            Item { Layout.fillHeight: true }

            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: 8
                Rectangle {
                    width: 8; height: 8; radius: 4
                    color: apiClient.healthStatus === "ok" ? Theme.emerald : Theme.gold
                }
                Text {
                    text: "API · " + apiClient.healthStatus
                    color: Theme.muted
                    font.pixelSize: 11
                }
            }
        }
    }
}
