import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    Component.onCompleted: {
        if (apiClient.licenseInfo.company)
            companyName.text = apiClient.licenseInfo.company
        if (apiClient.licenseInfo.company)
            brandName.text = apiClient.licenseInfo.company
    }

    Flickable {
        anchors.fill: parent
        contentWidth: width
        contentHeight: card.height + 50
        clip: true

        Rectangle {
            id: card
            anchors.horizontalCenter: parent.horizontalCenter
            y: 24
            width: Math.min(780, parent.width - 48)
            height: 690
            radius: 22
            color: Theme.panel
            border.width: 1
            border.color: Qt.rgba(.68,.79,.87,.32)

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 28
                spacing: 11

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 14
                    layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight

                    Rectangle {
                        Layout.preferredWidth: 76
                        Layout.preferredHeight: 76
                        radius: 19
                        color: "#050D16"
                        border.width: 1
                        border.color: Theme.electricBlue

                        Image {
                            anchors.fill: parent
                            anchors.margins: 7
                            source: "qrc:/qt/qml/Business/RealEstate/assets/property-mark.svg"
                            fillMode: Image.PreserveAspectFit
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 3

                        Text {
                            Layout.fillWidth: true
                            text: "FIRST OWNER SETUP"
                            color: Theme.electricCyan
                            font.pixelSize: 11
                            font.bold: true
                            font.letterSpacing: 1.5
                            horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                        }

                        Text {
                            Layout.fillWidth: true
                            text: appState.localize(appState.language, "إعداد الشركة لأول مرة", "Set up your company")
                            color: Theme.platinum
                            font.family: appState.localize(appState.language, "Noto Kufi Arabic", "Segoe UI")
                            font.pixelSize: 27
                            font.bold: true
                            horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                        }

                        Text {
                            Layout.fillWidth: true
                            text: appState.localize(appState.language, "أنشئ مساحة الشركة وحساب المالك الأول. هذه الخطوة تظهر مرة واحدة فقط.", "Create the company workspace and first owner account. This appears only once.")
                            color: Theme.muted
                            font.pixelSize: 12
                            wrapMode: Text.WordWrap
                            horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 1
                    color: Theme.borderSoft
                }

                GridLayout {
                    Layout.fillWidth: true
                    columns: card.width > 660 ? 2 : 1
                    columnSpacing: 10
                    rowSpacing: 10

                    TextField {
                        id: companyName
                        Layout.fillWidth: true
                        Layout.preferredHeight: 48
                        placeholderText: appState.localize(appState.language, "اسم الشركة *", "Company name *")
                        horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                    }

                    TextField {
                        id: companySlug
                        Layout.fillWidth: true
                        Layout.preferredHeight: 48
                        placeholderText: appState.localize(appState.language, "معرّف الشركة بالإنجليزية *", "Company identifier *")
                        validator: RegularExpressionValidator { regularExpression: /[a-z0-9][a-z0-9-]{1,98}[a-z0-9]/ }
                        horizontalAlignment: Text.AlignLeft
                        inputMethodHints: Qt.ImhLowercaseOnly | Qt.ImhNoPredictiveText
                    }

                    TextField {
                        id: brandName
                        Layout.fillWidth: true
                        Layout.preferredHeight: 48
                        placeholderText: appState.localize(appState.language, "الاسم التجاري", "Brand name")
                        horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                    }

                    TextField {
                        id: ownerName
                        Layout.fillWidth: true
                        Layout.preferredHeight: 48
                        placeholderText: appState.localize(appState.language, "اسم المالك *", "Owner name *")
                        horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                    }

                    TextField {
                        id: ownerEmail
                        Layout.fillWidth: true
                        Layout.preferredHeight: 48
                        placeholderText: appState.localize(appState.language, "بريد المالك *", "Owner email *")
                        inputMethodHints: Qt.ImhEmailCharactersOnly
                        horizontalAlignment: Text.AlignLeft
                    }

                    TextField {
                        id: ownerPassword
                        Layout.fillWidth: true
                        Layout.preferredHeight: 48
                        placeholderText: appState.localize(appState.language, "كلمة مرور المالك — 10 أحرف على الأقل *", "Owner password — minimum 10 characters *")
                        echoMode: TextInput.Password
                        horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                    }

                    TextField {
                        id: confirmPassword
                        Layout.fillWidth: true
                        Layout.preferredHeight: 48
                        placeholderText: appState.localize(appState.language, "تأكيد كلمة المرور *", "Confirm password *")
                        echoMode: TextInput.Password
                        horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 86
                    radius: 12
                    color: "#071522"
                    border.width: 1
                    border.color: Theme.borderSoft

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 13
                        spacing: 10
                        layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight

                        Rectangle {
                            width: 36; height: 36; radius: 9
                            color: "#06131F"
                            border.width: 1
                            border.color: Theme.emerald
                            Text { anchors.centerIn: parent; text: "✓"; color: Theme.emerald; font.pixelSize: 16; font.bold: true }
                        }

                        Text {
                            Layout.fillWidth: true
                            text: appState.localize(appState.language, "سيتم إنشاء قاعدة البيانات المحلية الآمنة، الشركة، حساب المالك، والصلاحيات الأساسية تلقائيًا.", "The local workspace, company, owner account and base permissions will be initialized automatically.")
                            color: Theme.silver
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                            horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                        }
                    }
                }

                Text {
                    visible: ownerPassword.text.length > 0 && ownerPassword.text !== confirmPassword.text
                    Layout.fillWidth: true
                    text: appState.localize(appState.language, "كلمتا المرور غير متطابقتين.", "Passwords do not match.")
                    color: Theme.gold
                    font.pixelSize: 11
                    horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                }

                Text {
                    visible: apiClient.lastError.length > 0
                    Layout.fillWidth: true
                    text: apiClient.lastError
                    color: Theme.danger
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                    horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                }

                Button {
                    id: createButton
                    Layout.fillWidth: true
                    Layout.preferredHeight: 52
                    enabled: !apiClient.busy
                        && companyName.text.length >= 2
                        && companySlug.acceptableInput
                        && ownerName.text.length >= 2
                        && ownerEmail.text.length >= 5
                        && ownerPassword.text.length >= 10
                        && ownerPassword.text === confirmPassword.text
                    text: apiClient.busy
                        ? "…"
                        : (appState.localize(appState.language, "إنشاء الشركة والدخول", "Create company and enter"))
                    onClicked: apiClient.bootstrapFirstOwner(
                        companyName.text,
                        companySlug.text,
                        brandName.text,
                        ownerName.text,
                        ownerEmail.text,
                        ownerPassword.text)

                    background: Rectangle {
                        radius: 11
                        color: createButton.enabled ? Theme.electricBlue : "#173247"
                        border.width: 1
                        border.color: createButton.enabled ? Theme.electricCyan : Theme.borderSoft
                    }
                    contentItem: Text {
                        text: createButton.text
                        color: createButton.enabled ? "#02101A" : Theme.muted
                        font.pixelSize: 14
                        font.bold: true
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
                        text: "LOCAL API · " + apiClient.healthStatus
                        color: Theme.muted
                        font.pixelSize: 11
                    }
                }
            }
        }
    }
}
