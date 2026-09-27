import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Theme.js" as Theme

Flickable {
    id: root
    contentWidth: width
    contentHeight: body.implicitHeight + 24
    clip: true

    ColumnLayout {
        id: body
        width: root.width
        spacing: 12

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 280
            radius: 18
            color: "#061321"
            border.width: 1
            border.color: Qt.rgba(.72,.82,.89,.30)
            clip: true

            Image {
                anchors.fill: parent
                source: apiClient.tenantSettings.cover_data_url || ""
                visible: String(source).length > 0
                fillMode: Image.PreserveAspectCrop
                opacity: .68
            }

            Rectangle {
                anchors.fill: parent
                gradient: Gradient {
                    GradientStop { position: 0; color: Qt.rgba(.01,.04,.08,.82) }
                    GradientStop { position: .55; color: Qt.rgba(.01,.05,.09,.52) }
                    GradientStop { position: 1; color: Qt.rgba(.03,.13,.20,.36) }
                }
            }

            RowLayout {
                anchors.fill: parent
                anchors.margins: 28
                spacing: 22
                layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight

                Rectangle {
                    width: 135; height: 135; radius: 28
                    color: Qt.rgba(.01,.04,.08,.88)
                    border.width: 1
                    border.color: Theme.electricBlue
                    Image {
                        anchors.fill: parent
                        anchors.margins: 8
                        source: apiClient.tenantSettings.logo_data_url || "qrc:/qt/qml/Nexvary/RealEstate/assets/nexvary-mark.svg"
                        fillMode: Image.PreserveAspectFit
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 5
                    Text {
                        text: apiClient.tenantSettings.brand_name || apiClient.tenantSettings.name || "NEXVARY"
                        color: Theme.platinum
                        font.family: appState.rtl ? "Noto Kufi Arabic" : "Segoe UI"
                        font.pixelSize: 34
                        font.bold: true
                    }
                    Text {
                        text: appState.rtl
                            ? "منصة تشغيل عقاري ذكية · مبيعات · أتمتة · نمو"
                            : "Intelligent Real Estate Operations · Sales · Automation · Growth"
                        color: Theme.electricCyan
                        font.pixelSize: 13
                    }
                    Text {
                        text: "Qt 6 · C++20 · QML · NEXVARY RealEstate AI OS"
                        color: Theme.silver
                        font.pixelSize: 10
                    }
                }
            }
        }

        GridLayout {
            Layout.fillWidth: true
            columns: root.width > 820 ? 3 : 1
            columnSpacing: 10
            rowSpacing: 10

            Repeater {
                model: [
                    {label:appState.rtl ? "الخطة" : "Plan", value:apiClient.tenantSettings.plan || "—", color:Theme.electricBlue},
                    {label:appState.rtl ? "الحالة" : "Status", value:apiClient.tenantSettings.lifecycle || "—", color:Theme.emerald},
                    {label:appState.rtl ? "معرّف الشركة" : "Company ID", value:apiClient.tenantSettings.slug || "—", color:Theme.violet}
                ]

                Rectangle {
                    required property var modelData
                    Layout.fillWidth: true
                    Layout.preferredHeight: 92
                    radius: 13
                    color: Theme.panel
                    border.width: 1
                    border.color: Qt.rgba(.68,.78,.85,.25)
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 14
                        Text { text: modelData.label; color: modelData.color; font.pixelSize: 10; font.bold: true }
                        Text { Layout.fillWidth: true; text: String(modelData.value); color: Theme.platinum; font.pixelSize: 15; font.bold: true; elide: Text.ElideRight }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 200
            radius: 15
            color: Theme.panel
            border.width: 1
            border.color: Qt.rgba(.68,.78,.85,.25)

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 9
                Text { text: appState.rtl ? "التواصل والروابط" : "Contact & Links"; color: Theme.platinum; font.pixelSize: 17; font.bold: true }
                Text { text: apiClient.tenantSettings.contact_email || "—"; color: Theme.silver; font.pixelSize: 11 }
                Text { text: apiClient.tenantSettings.website_url || "—"; color: Theme.electricCyan; font.pixelSize: 11 }
                Text { text: [apiClient.tenantSettings.facebook_url, apiClient.tenantSettings.linkedin_url, apiClient.tenantSettings.youtube_url, apiClient.tenantSettings.x_url, apiClient.tenantSettings.tiktok_url].filter(function(v){return !!v}).join("   ·   ") || "—"; color: Theme.muted; font.pixelSize: 10; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                Item { Layout.fillHeight: true }
                Text { text: "Powered by NEXVARY RealEstate AI OS"; color: Theme.gold; font.pixelSize: 10; visible: apiClient.tenantSettings.powered_by_nexvary !== false }
            }
        }
    }
}
