import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import "Theme.js" as Theme

Flickable {
    id: root
    contentWidth: width
    contentHeight: form.implicitHeight + 28
    clip: true

    property string logoData: ""
    property string coverData: ""

    function loadSettings() {
        var s = apiClient.tenantSettings
        brandField.text = s.brand_name || s.name || "NEXVARY"
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
        function onTenantSettingsChanged() { root.loadSettings() }
    }

    FileDialog {
        id: logoDialog
        title: appState.rtl ? "اختر شعار الشركة" : "Choose company logo"
        nameFilters: ["Images (*.png *.jpg *.jpeg *.webp)"]
        onAccepted: {
            var data = apiClient.imageFileToDataUrl(selectedFile, 1100000)
            if (data.length > 0) root.logoData = data
        }
    }

    FileDialog {
        id: coverDialog
        title: appState.rtl ? "اختر صورة غلاف الشركة" : "Choose company cover"
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
                    text: appState.t("settings")
                    color: Theme.platinum
                    font.family: appState.rtl ? "Noto Kufi Arabic" : "Segoe UI"
                    font.pixelSize: 29
                    font.bold: true
                }
                Text {
                    text: appState.rtl ? "هوية White-Label وروابط الشركة" : "White-label identity and company links"
                    color: Theme.muted
                    font.pixelSize: 12
                }
            }
            Button {
                text: appState.rtl ? "حفظ التغييرات" : "Save Changes"
                enabled: !apiClient.busy
                onClicked: apiClient.updateTenantSettings(
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

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 190
            radius: 15
            color: Theme.panel
            border.width: 1
            border.color: Qt.rgba(.68,.78,.85,.28)
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
                        source: root.logoData.length > 0 ? root.logoData : "qrc:/qt/qml/Nexvary/RealEstate/assets/nexvary-mark.svg"
                        fillMode: Image.PreserveAspectFit
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Text { text: brandField.text || "NEXVARY"; color: Theme.platinum; font.pixelSize: 25; font.bold: true }
                    Text { text: appState.rtl ? "معاينة الهوية داخل النظام" : "In-app brand preview"; color: Theme.electricCyan; font.pixelSize: 11 }
                    Text { text: appState.rtl ? "يمكن لكل شركة رفع شعار وغلاف مستقلين." : "Each white-label company can use its own logo and cover."; color: Theme.silver; font.pixelSize: 10 }
                }

                ColumnLayout {
                    Button { text: appState.rtl ? "اختيار الشعار" : "Choose Logo"; onClicked: logoDialog.open() }
                    Button { text: appState.rtl ? "اختيار الغلاف" : "Choose Cover"; onClicked: coverDialog.open() }
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
                Layout.preferredHeight: 270
                radius: 15
                color: Theme.panel
                border.width: 1
                border.color: Qt.rgba(.68,.78,.85,.25)

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 15
                    spacing: 9
                    Text { text: appState.rtl ? "هوية الشركة" : "Company Identity"; color: Theme.platinum; font.pixelSize: 16; font.bold: true }
                    TextField { id: brandField; Layout.fillWidth: true; placeholderText: appState.rtl ? "اسم العلامة التجارية" : "Brand name" }
                    TextField { id: colorField; Layout.fillWidth: true; placeholderText: "#128FE7" }
                    TextField { id: emailField; Layout.fillWidth: true; placeholderText: "info@example.com" }
                    TextField { id: websiteField; Layout.fillWidth: true; placeholderText: "https://example.com" }
                    RowLayout {
                        Layout.fillWidth: true
                        Button { text: appState.rtl ? "إزالة الشعار" : "Remove Logo"; onClicked: root.logoData = "" }
                        Button { text: appState.rtl ? "إزالة الغلاف" : "Remove Cover"; onClicked: root.coverData = "" }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 270
                radius: 15
                color: Theme.panel
                border.width: 1
                border.color: Qt.rgba(.68,.78,.85,.25)

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 15
                    spacing: 9
                    Text { text: appState.rtl ? "حسابات الشركة" : "Company Social Links"; color: Theme.platinum; font.pixelSize: 16; font.bold: true }
                    TextField { id: facebookField; Layout.fillWidth: true; placeholderText: "Facebook" }
                    TextField { id: linkedinField; Layout.fillWidth: true; placeholderText: "LinkedIn" }
                    TextField { id: youtubeField; Layout.fillWidth: true; placeholderText: "YouTube" }
                    TextField { id: xField; Layout.fillWidth: true; placeholderText: "X" }
                    TextField { id: tiktokField; Layout.fillWidth: true; placeholderText: "TikTok" }
                }
            }
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
