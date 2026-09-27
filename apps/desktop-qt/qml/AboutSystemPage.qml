import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Theme.js" as Theme

Flickable {
    id: root
    contentWidth: width
    contentHeight: body.implicitHeight + 26
    clip: true

    ColumnLayout {
        id: body
        width: root.width
        spacing: 12

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 230
            radius: 18
            color: "#061321"
            border.width: 1
            border.color: Qt.rgba(.72,.82,.89,.30)
            clip: true

            Rectangle {
                anchors.fill: parent
                gradient: Gradient {
                    GradientStop { position: 0; color: "#030810" }
                    GradientStop { position: .55; color: "#071A2B" }
                    GradientStop { position: 1; color: "#0A2942" }
                }
            }

            RowLayout {
                anchors.fill: parent
                anchors.margins: 24
                spacing: 20
                layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight

                Rectangle {
                    width: 118; height: 118; radius: 25
                    color: "#030A12"
                    border.width: 1
                    border.color: Theme.electricBlue
                    Image {
                        anchors.fill: parent
                        anchors.margins: 8
                        source: "qrc:/qt/qml/Nexvary/RealEstate/assets/nexvary-mark.svg"
                        fillMode: Image.PreserveAspectFit
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 5
                    Text {
                        text: "NEXVARY RealEstate AI OS"
                        color: Theme.platinum
                        font.family: appState.rtl ? "Noto Kufi Arabic" : "Segoe UI"
                        font.pixelSize: 31
                        font.bold: true
                    }
                    Text {
                        text: appState.rtl
                            ? "نظام تشغيل عقاري مؤسسي يجمع CRM وERP والذكاء الاصطناعي والأتمتة"
                            : "Enterprise real-estate operating system combining CRM, ERP, AI and automation"
                        color: Theme.electricCyan
                        font.pixelSize: 13
                    }
                    Text {
                        text: "Qt 6 · C++20 · QML · FastAPI · White-Label"
                        color: Theme.silver
                        font.pixelSize: 10
                    }
                    Text {
                        text: appState.rtl
                            ? "بنية Native مستقرة مع فصل واضح بين الواجهة والخدمات والبيانات."
                            : "A stable native architecture with clear separation between UI, services and data."
                        color: Theme.muted
                        font.pixelSize: 10
                    }
                }

                Rectangle {
                    width: 150
                    height: 74
                    radius: 13
                    color: Theme.panel
                    border.width: 1
                    border.color: Theme.borderSoft
                    Column {
                        anchors.centerIn: parent
                        spacing: 2
                        Text { anchors.horizontalCenter: parent.horizontalCenter; text: "NATIVE"; color: Theme.emerald; font.pixelSize: 11; font.bold: true }
                        Text { anchors.horizontalCenter: parent.horizontalCenter; text: "QT 6 / C++20"; color: Theme.platinum; font.pixelSize: 13; font.bold: true }
                        Text { anchors.horizontalCenter: parent.horizontalCenter; text: "MIGRATION TRACK"; color: Theme.muted; font.pixelSize: 8 }
                    }
                }
            }
        }

        GridLayout {
            Layout.fillWidth: true
            columns: root.width > 1150 ? 4 : root.width > 760 ? 2 : 1
            columnSpacing: 10
            rowSpacing: 10

            Repeater {
                model: [
                    {icon:"◎", title:appState.rtl?"CRM والمبيعات":"CRM & Sales", desc:appState.rtl?"العملاء، Pipeline، العروض، الفواتير، المدفوعات والسجل الموحد.":"Leads, pipeline, proposals, invoices, payments and unified timeline.", color:Theme.electricBlue},
                    {icon:"▦", title:appState.rtl?"المخزون والعقود":"Inventory & Finance", desc:appState.rtl?"المشروعات، الوحدات، الحجوزات، العقود، الأقساط والعمولات.":"Projects, units, reservations, contracts, installments and commissions.", color:Theme.emerald},
                    {icon:"✦", title:appState.rtl?"AI موثوق":"Grounded AI", desc:appState.rtl?"Copilot مرتبط بالمخزون وقاعدة المعرفة والوسائط الموثوقة.":"Copilot grounded in live inventory, knowledge and verified media.", color:Theme.violet},
                    {icon:"✉", title:appState.rtl?"Omnichannel":"Omnichannel", desc:appState.rtl?"WhatsApp والمحادثات وحالة المبيعات والتحويل البشري.":"WhatsApp, inbox, sales state and human handoff.", color:Theme.gold},
                    {icon:"◉", title:appState.rtl?"Growth Intelligence":"Growth Intelligence", desc:appState.rtl?"الحملات والإسناد والجمهور والوسائط والـPlaybooks والتغذية الراجعة.":"Campaigns, attribution, audiences, media, playbooks and feedback.", color:Theme.electricCyan},
                    {icon:"⌕", title:"SEO Autopilot", desc:appState.rtl?"التدقيق والزحف والفرص وخطط التغيير المحكومة.":"Audits, crawl, opportunities and guarded change plans.", color:"#F19AAF"},
                    {icon:"↻", title:"Automation Studio", desc:appState.rtl?"Workflows مرئية مع تشغيل وموافقات ومراجعة.":"Visual workflows with runs, approvals and review.", color:Theme.electricBlue},
                    {icon:"◆", title:appState.rtl?"White-Label":"White-Label", desc:appState.rtl?"اسم وشعار وغلاف وروابط وهوية مستقلة لكل شركة.":"Independent brand, logo, cover, links and identity per tenant.", color:Theme.gold}
                ]

                Rectangle {
                    required property var modelData
                    Layout.fillWidth: true
                    Layout.preferredHeight: 155
                    radius: 15
                    color: Theme.panel
                    border.width: 1
                    border.color: Qt.rgba(.68,.78,.85,.25)

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 6
                        Rectangle {
                            width: 38; height: 38; radius: 10
                            color: "#071522"
                            border.width: 1
                            border.color: modelData.color
                            Text { anchors.centerIn: parent; text: modelData.icon; color: modelData.color; font.pixelSize: 17; font.bold: true }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: modelData.title
                            color: Theme.platinum
                            font.pixelSize: 13
                            font.bold: true
                            horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                        }
                        Text {
                            Layout.fillWidth: true
                            text: modelData.desc
                            color: Theme.muted
                            font.pixelSize: 10
                            lineHeight: 1.35
                            wrapMode: Text.WordWrap
                            horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                        }
                    }
                }
            }
        }

        GridLayout {
            Layout.fillWidth: true
            columns: root.width > 860 ? 3 : 1
            columnSpacing: 10
            rowSpacing: 10

            Repeater {
                model: [
                    {label:appState.rtl?"اتجاه العربية":"Arabic layout", value:"RTL", color:Theme.emerald},
                    {label:appState.rtl?"واجهة سطح المكتب":"Desktop UI", value:"Qt 6 / QML", color:Theme.electricBlue},
                    {label:appState.rtl?"النواة":"Core", value:"C++20", color:Theme.violet}
                ]
                Rectangle {
                    required property var modelData
                    Layout.fillWidth: true
                    Layout.preferredHeight: 86
                    radius: 13
                    color: Theme.panel
                    border.width: 1
                    border.color: Qt.rgba(.68,.78,.85,.24)
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 13
                        layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
                        ColumnLayout {
                            Layout.fillWidth: true
                            Text { text: modelData.label; color: Theme.muted; font.pixelSize: 9 }
                            Text { text: modelData.value; color: modelData.color; font.pixelSize: 16; font.bold: true }
                        }
                    }
                }
            }
        }
    }
}
