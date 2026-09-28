import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

Flickable {
    id: root
    contentWidth: width
    contentHeight: form.implicitHeight + 28
    clip: true

    property string logoData: ""
    property string coverData: ""
    property bool saveRequested: false
    property bool savedSuccessfully: false

    function validWebLink(value) {
        var text = String(value || "").trim()
        return text.length === 0 || /^https:\/\/[A-Za-z0-9.-]+(?::[0-9]+)?(?:[\/?#].*)?$/.test(text)
    }
    readonly property bool linksValid: validWebLink(websiteField.text)
        && validWebLink(facebookField.text) && validWebLink(linkedinField.text)
        && validWebLink(youtubeField.text) && validWebLink(xField.text)
        && validWebLink(tiktokField.text)

    function loadSettings() {
        var s = apiClient.tenantSettings
        brandField.text = s.brand_name || s.name || "Your Company"
        colorField.text = s.primary_color || "#128FE7"
        emailField.text = s.contact_email || ""
        websiteField.text = s.website_url || ""
        facebookField.text = s.facebook_url || ""
        linkedinField.text = s.linkedin_url || ""
        youtubeField.text = s.youtube_url || ""
        xField.text = s.x_url || ""
        tiktokField.text = s.tiktok_url || ""
        logoData = s.logo_data_url || ""
        coverData = s.cover_data_url || ""
    }

    Component.onCompleted: loadSettings()
    Connections {
        target: apiClient
        function onTenantSettingsChanged() {
            root.loadSettings()
            if (root.saveRequested) {
                root.savedSuccessfully = true
                root.saveRequested = false
                savedTimer.restart()
            }
        }
        function onLastErrorChanged() {
            if (apiClient.lastError.length > 0)
                root.saveRequested = false
        }
    }

    Timer { id: savedTimer; interval: 3500; onTriggered: root.savedSuccessfully = false }

    FileDialog {
        id: logoDialog
        title: appState.localize(appState.language, "اختر شعار الشركة", "Choose company logo")
        nameFilters: ["Images (*.png *.jpg *.jpeg *.webp)"]
        onAccepted: {
            var data = apiClient.imageFileToDataUrl(selectedFile, 1100000)
            if (data.length > 0) root.logoData = data
        }
    }

    FileDialog {
        id: coverDialog
        title: appState.localize(appState.language, "اختر صورة غلاف الشركة", "Choose company cover")
        nameFilters: ["Images (*.png *.jpg *.jpeg *.webp)"]
        onAccepted: {
            var data = apiClient.imageFileToDataUrl(selectedFile, 3000000)
            if (data.length > 0) root.coverData = data
        }
    }

    ColumnLayout {
        id: form
        width: root.width
        spacing: 12

        RowLayout {
            Layout.fillWidth: true
            layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
            ColumnLayout {
                Layout.fillWidth: true
                Text {
                    text: (appState.language, appState.t("settings"))
                    color: Theme.platinum
                    font.family: appState.localize(appState.language, "Noto Kufi Arabic", "Segoe UI")
                    font.pixelSize: 29
                    font.bold: true
                }
                Text {
                    text: appState.localize(appState.language, "هوية White-Label وروابط الشركة", "White-label identity and company links")
                    color: Theme.muted
                    font.pixelSize: 12
                }
            }
            Button {
                text: appState.localize(appState.language, "حفظ التغييرات", "Save Changes")
                enabled: !apiClient.busy && root.linksValid
                onClicked: {
                    root.savedSuccessfully = false
                    root.saveRequested = true
                    apiClient.updateTenantSettings(
                        brandField.text,
                        colorField.text,
                        root.logoData,
                        root.coverData,
                        emailField.text,
                        websiteField.text,
                        facebookField.text,
                        linkedinField.text,
                        youtubeField.text,
                        xField.text,
                        tiktokField.text)
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 112
            radius: 15
            color: Theme.panel
            border.width: 2
            border.color: Theme.metallicSilver

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 13
                spacing: 8
                Text {
                    text: appState.localize(appState.language, "اختر مظهر النظام — يتم حفظه تلقائيًا", "Choose the application theme — saved automatically")
                    color: Theme.platinum
                    font.pixelSize: 15
                    font.bold: true
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Repeater {
                        model: [
                            {code:"neon", name:"Neon Fusion", accent:"#39FF88"},
                            {code:"blue", name:"Electric Blue", accent:"#2DBDFF"},
                            {code:"green", name:"Neon Green", accent:"#2DFF73"},
                            {code:"amber", name:"Amber", accent:"#FFB000"},
                            {code:"silver", name:"Silver", accent:"#E3EBEF"},
                            {code:"violet", name:"Violet", accent:"#B37CFF"}
                        ]
                        delegate: Rectangle {
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.preferredHeight: 48
                            radius: 10
                            color: appState.theme === modelData.code ? Theme.panelAlt : Theme.shellDeep
                            border.width: appState.theme === modelData.code ? 2 : 1
                            border.color: appState.theme === modelData.code ? modelData.accent : Theme.metallicSilverDark
                            Row {
                                anchors.centerIn: parent
                                spacing: 7
                                Rectangle { width: 13; height: 13; radius: 7; color: modelData.accent; border.width: 1; border.color: Theme.metallicSilverLight }
                                Text { text: modelData.name; color: Theme.platinum; font.pixelSize: 10; font.bold: appState.theme === modelData.code }
                            }
                            MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: appState.theme = modelData.code }
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 190
            radius: 15
            color: Theme.panel
            border.width: 1
            border.color: Theme.metallicSilverDark
            clip: true

            Image {
                anchors.fill: parent
                source: root.coverData
                visible: root.coverData.length > 0
                fillMode: Image.PreserveAspectCrop
                opacity: .62
            }
            Rectangle {
                anchors.fill: parent
                color: root.coverData.length > 0 ? Qt.rgba(.01,.04,.08,.55) : "transparent"
                gradient: Gradient {
                    GradientStop { position: 0; color: Qt.rgba(.02,.06,.11,.20) }
                    GradientStop { position: 1; color: Qt.rgba(.01,.03,.06,.80) }
                }
            }
            RowLayout {
                anchors.fill: parent
                anchors.margins: 18
                spacing: 16
                layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight

                Rectangle {
                    width: 105; height: 105; radius: 22
                    color: "#050D16"
                    border.width: 1
                    border.color: Theme.electricBlue
                    Image {
                        anchors.fill: parent
                        anchors.margins: 7
                        source: root.logoData.length > 0 ? root.logoData : "qrc:/qt/qml/Business/RealEstate/assets/property-mark.svg"
                        fillMode: Image.PreserveAspectFit
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Text { text: brandField.text || "Your Company"; color: Theme.platinum; font.pixelSize: 25; font.bold: true }
                    Text { text: appState.localize(appState.language, "معاينة الهوية داخل النظام", "In-app brand preview"); color: Theme.electricCyan; font.pixelSize: 11 }
                    Text { text: appState.localize(appState.language, "يمكن لكل شركة رفع شعار وغلاف مستقلين.", "Each white-label company can use its own logo and cover."); color: Theme.silver; font.pixelSize: 11 }
                }

                ColumnLayout {
                    Button { text: appState.localize(appState.language, "اختيار الشعار", "Choose Logo"); onClicked: logoDialog.open() }
                    Button { text: appState.localize(appState.language, "اختيار الغلاف", "Choose Cover"); onClicked: coverDialog.open() }
                }
            }
        }

        GridLayout {
            Layout.fillWidth: true
            columns: root.width > 900 ? 2 : 1
            columnSpacing: 11
            rowSpacing: 11

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 405
                radius: 15
                color: Theme.panel
                border.width: 1
                border.color: Theme.metallicSilverDark

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 15
                    spacing: 9
                    Text { text: appState.localize(appState.language, "هوية الشركة", "Company Identity"); color: Theme.platinum; font.pixelSize: 16; font.bold: true }
                    Text { text: appState.localize(appState.language, "اسم الشركة", "Company name"); color: Theme.muted; font.pixelSize: 11 }
                    TextField { id: brandField; Layout.fillWidth: true; placeholderText: appState.localize(appState.language, "اسم العلامة التجارية", "Brand name"); selectByMouse: true }
                    Text { text: appState.localize(appState.language, "اللون الرئيسي", "Primary color"); color: Theme.muted; font.pixelSize: 11 }
                    TextField { id: colorField; Layout.fillWidth: true; placeholderText: "#128FE7"; selectByMouse: true }
                    Text { text: appState.localize(appState.language, "البريد الإلكتروني", "Contact email"); color: Theme.muted; font.pixelSize: 11 }
                    TextField { id: emailField; Layout.fillWidth: true; placeholderText: "info@example.com"; selectByMouse: true }
                    Text { text: appState.localize(appState.language, "الموقع الإلكتروني", "Website"); color: Theme.muted; font.pixelSize: 11 }
                    TextField { id: websiteField; Layout.fillWidth: true; placeholderText: "https://example.com"; selectByMouse: true }
                    RowLayout {
                        Layout.fillWidth: true
                        Button { text: appState.localize(appState.language, "إزالة الشعار", "Remove Logo"); onClicked: root.logoData = "" }
                        Button { text: appState.localize(appState.language, "إزالة الغلاف", "Remove Cover"); onClicked: root.coverData = "" }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 405
                radius: 15
                color: Theme.panel
                border.width: 1
                border.color: Theme.metallicSilverDark

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 15
                    spacing: 9
                    Text { text: appState.localize(appState.language, "روابط السوشيال ميديا — قابلة للتحرير", "Editable social media links"); color: Theme.platinum; font.pixelSize: 16; font.bold: true }
                    Text { text: "Facebook"; color: Theme.muted; font.pixelSize: 11 }
                    TextField { id: facebookField; Layout.fillWidth: true; placeholderText: "https://facebook.com/..."; selectByMouse: true; inputMethodHints: Qt.ImhUrlCharactersOnly }
                    Text { text: "LinkedIn"; color: Theme.muted; font.pixelSize: 11 }
                    TextField { id: linkedinField; Layout.fillWidth: true; placeholderText: "https://linkedin.com/..."; selectByMouse: true; inputMethodHints: Qt.ImhUrlCharactersOnly }
                    Text { text: "YouTube"; color: Theme.muted; font.pixelSize: 11 }
                    TextField { id: youtubeField; Layout.fillWidth: true; placeholderText: "https://youtube.com/..."; selectByMouse: true; inputMethodHints: Qt.ImhUrlCharactersOnly }
                    Text { text: "X / Twitter"; color: Theme.muted; font.pixelSize: 11 }
                    TextField { id: xField; Layout.fillWidth: true; placeholderText: "https://x.com/..."; selectByMouse: true; inputMethodHints: Qt.ImhUrlCharactersOnly }
                    Text { text: "TikTok"; color: Theme.muted; font.pixelSize: 11 }
                    TextField { id: tiktokField; Layout.fillWidth: true; placeholderText: "https://tiktok.com/@..."; selectByMouse: true; inputMethodHints: Qt.ImhUrlCharactersOnly }
                }
            }
        }

        Text {
            visible: !root.linksValid
            Layout.fillWidth: true
            text: appState.localize(appState.language, "استخدم روابط صحيحة تبدأ بـ https:// أو اترك الخانة فارغة.", "Use valid links beginning with https://, or leave the field empty.")
            color: Theme.danger
            font.pixelSize: 12
        }

        Text {
            visible: root.savedSuccessfully
            Layout.fillWidth: true
            text: appState.localize(appState.language, "تم حفظ بيانات الشركة وروابط السوشيال ميديا.", "Company details and social links were saved.")
            color: Theme.emerald
            font.pixelSize: 11
            font.bold: true
        }

        Text {
            visible: apiClient.lastError.length > 0
            Layout.fillWidth: true
            text: apiClient.lastError
            color: Theme.danger
            font.pixelSize: 11
            wrapMode: Text.WordWrap
        }
    }
}
