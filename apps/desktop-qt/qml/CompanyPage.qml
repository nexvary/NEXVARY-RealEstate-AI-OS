import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Theme.js" as Theme

Flickable {
    id: root
    contentWidth: width
    contentHeight: body.implicitHeight + 28
    clip: true

    readonly property string companyName: apiClient.tenantSettings.brand_name || apiClient.tenantSettings.name || "Your Company"
    readonly property var socialLinks: [
        {label:"Facebook", url:apiClient.tenantSettings.facebook_url || "", color:"#5AA7FF"},
        {label:"LinkedIn", url:apiClient.tenantSettings.linkedin_url || "", color:"#79C8FF"},
        {label:"YouTube", url:apiClient.tenantSettings.youtube_url || "", color:"#FF6F7E"},
        {label:"X", url:apiClient.tenantSettings.x_url || "", color:Theme.silver},
        {label:"TikTok", url:apiClient.tenantSettings.tiktok_url || "", color:"#66F2E3"}
    ]

    ColumnLayout {
        id: body
        width: root.width
        spacing: 14

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 260
            radius: 20
            color: "#061321"
            border.width: 1
            border.color: Theme.metallicSilver
            clip: true

            Image {
                anchors.fill: parent
                source: apiClient.tenantSettings.cover_data_url || ""
                visible: String(source).length > 0
                fillMode: Image.PreserveAspectCrop
                opacity: .56
            }
            Rectangle {
                anchors.fill: parent
                gradient: Gradient {
                    GradientStop { position: 0; color: Qt.rgba(.01,.03,.06,.94) }
                    GradientStop { position: .58; color: Qt.rgba(.01,.06,.11,.72) }
                    GradientStop { position: 1; color: Qt.rgba(.02,.17,.27,.54) }
                }
            }

            RowLayout {
                anchors.fill: parent
                anchors.margins: 28
                spacing: 24
                layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight

                Rectangle {
                    Layout.preferredWidth: 136
                    Layout.preferredHeight: 136
                    radius: 30
                    color: Qt.rgba(.01,.04,.08,.92)
                    border.width: 2
                    border.color: Theme.electricBlue
                    Image {
                        anchors.fill: parent
                        anchors.margins: 10
                        source: apiClient.tenantSettings.logo_data_url || "qrc:/qt/qml/Business/RealEstate/assets/property-mark.svg"
                        fillMode: Image.PreserveAspectFit
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Text {
                        Layout.fillWidth: true
                        text: root.companyName
                        color: Theme.platinum
                        font.family: appState.localize(appState.language, "Noto Kufi Arabic", "Segoe UI")
                        font.pixelSize: 36
                        font.bold: true
                        horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                    }
                    Text {
                        Layout.fillWidth: true
                        text: appState.localize(appState.language, "حلول متكاملة لإدارة المبيعات والعقارات وخدمة العملاء", "Integrated real-estate, sales and customer operations")
                        color: Theme.electricCyan
                        font.pixelSize: 15
                        font.bold: true
                        horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                    }
                    Text {
                        Layout.fillWidth: true
                        text: appState.localize(appState.language, "نحو عمليات أسرع، قرارات أوضح، وتجربة عميل أكثر احترافية.", "Faster operations, clearer decisions and a more professional customer experience.")
                        color: Theme.silver
                        font.pixelSize: 12
                        wrapMode: Text.WordWrap
                        horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                    }
                }

                Rectangle {
                    Layout.preferredWidth: 150
                    Layout.preferredHeight: 78
                    radius: 14
                    color: Qt.rgba(.03,.14,.18,.9)
                    border.width: 1
                    border.color: Theme.emerald
                    Column {
                        anchors.centerIn: parent
                        spacing: 4
                        Text { anchors.horizontalCenter: parent.horizontalCenter; text: appState.localize(appState.language, "حالة المنصة", "PLATFORM STATUS"); color: Theme.muted; font.pixelSize: 11 }
                        Text { anchors.horizontalCenter: parent.horizontalCenter; text: appState.localize(appState.language, "نشطة", "ACTIVE"); color: Theme.emerald; font.pixelSize: 17; font.bold: true }
                    }
                }
            }
        }

        GridLayout {
            Layout.fillWidth: true
            columns: root.width > 950 ? 3 : 1
            columnSpacing: 12
            rowSpacing: 12

            Repeater {
                model: [
                    {icon:"◎", color:Theme.electricBlue, title:appState.localize(appState.language, "إدارة العملاء", "Customer Management"), desc:appState.localize(appState.language, "متابعة العملاء المحتملين والتواصل والفرص من مكان واحد.", "Track leads, communication and opportunities from one workspace.")},
                    {icon:"▦", color:Theme.emerald, title:appState.localize(appState.language, "إدارة العقارات", "Real Estate Operations"), desc:appState.localize(appState.language, "تنظيم المشروعات والوحدات والحجوزات والعقود والتحصيل.", "Organize projects, units, reservations, contracts and collections.")},
                    {icon:"✦", color:Theme.violet, title:appState.localize(appState.language, "النمو الذكي", "Intelligent Growth"), desc:appState.localize(appState.language, "أتمتة الأعمال وتحليل الأداء ودعم قرارات المبيعات.", "Automate workflows, analyze performance and support sales decisions.")}
                ]
                Rectangle {
                    required property var modelData
                    Layout.fillWidth: true
                    Layout.preferredHeight: 150
                    radius: 16
                    color: Theme.panel
                    border.width: 1
                    border.color: Theme.metallicSilverDark
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 13
                        layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
                        Rectangle {
                            width: 48; height: 48; radius: 13
                            color: "#071522"
                            border.width: 1
                            border.color: modelData.color
                            Text { anchors.centerIn: parent; text: modelData.icon; color: modelData.color; font.pixelSize: 22; font.bold: true }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 7
                            Text { Layout.fillWidth: true; text: modelData.title; color: Theme.platinum; font.pixelSize: 15; font.bold: true; horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft }
                            Text { Layout.fillWidth: true; text: modelData.desc; color: Theme.muted; font.pixelSize: 11; wrapMode: Text.WordWrap; horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft }
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 190
            radius: 16
            color: Theme.panel
            border.width: 1
            border.color: Theme.metallicSilverDark

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 17
                spacing: 11
                Text { Layout.fillWidth: true; text: appState.localize(appState.language, "التواصل مع الشركة", "Contact the company"); color: Theme.platinum; font.pixelSize: 18; font.bold: true; horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
                    Button { visible: !!apiClient.tenantSettings.contact_email; text: "✉  " + apiClient.tenantSettings.contact_email; onClicked: Qt.openUrlExternally("mailto:" + apiClient.tenantSettings.contact_email) }
                    Button { visible: !!apiClient.tenantSettings.website_url; text: "⌂  " + apiClient.tenantSettings.website_url; onClicked: Qt.openUrlExternally(apiClient.tenantSettings.website_url) }
                    Item { Layout.fillWidth: true }
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
                    Repeater {
                        model: root.socialLinks
                        Button {
                            required property var modelData
                            visible: modelData.url.length > 0
                            text: modelData.label
                            onClicked: Qt.openUrlExternally(modelData.url)
                            contentItem: Text { text: parent.text; color: modelData.color; font.pixelSize: 11; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                        }
                    }
                    Text { visible: root.socialLinks.every(function(item){ return item.url.length === 0 }); text: appState.localize(appState.language, "يمكن إضافة روابط التواصل من إعدادات الشركة.", "Social links can be added in Company Settings."); color: Theme.muted; font.pixelSize: 11 }
                    Item { Layout.fillWidth: true }
                }
            }
        }
    }
}
