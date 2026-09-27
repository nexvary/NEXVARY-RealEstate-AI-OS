import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Theme.js" as Theme

Flickable {
    id: root
    contentWidth: width
    contentHeight: content.implicitHeight + 24
    clip: true

    function value(key) {
        var v = apiClient.enterpriseSummary[key]
        return v === undefined || v === null ? "0" : String(v)
    }

    function money(key) {
        var n = Number(apiClient.enterpriseSummary[key] || 0)
        return n.toLocaleString(Qt.locale(appState.rtl ? "ar_EG" : "en_US"), "f", 0) + " EGP"
    }

    ColumnLayout {
        id: content
        width: root.width
        spacing: 12

        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 3
                Text {
                    text: appState.t("enterpriseCrm")
                    color: Theme.platinum
                    font.family: appState.rtl ? "Noto Kufi Arabic" : "Segoe UI"
                    font.pixelSize: 29
                    font.bold: true
                }
                Text {
                    text: appState.rtl
                        ? "العروض والفواتير والتحصيل والدعم والتذكيرات في مركز واحد"
                        : "Proposals, billing, collections, support and reminders in one workspace"
                    color: Theme.muted
                    font.pixelSize: 12
                }
            }

            Button {
                text: appState.t("customerTimeline")
                enabled: apiClient.leads.length > 0
                onClicked: {
                    if (apiClient.leads.length > 0)
                        apiClient.loadTimeline(apiClient.leads[0].id)
                    appState.navigate("timeline")
                }
            }

            Button {
                text: appState.t("refresh")
                onClicked: apiClient.refreshEnterprise()
            }
        }

        GridLayout {
            Layout.fillWidth: true
            columns: root.width > 1080 ? 5 : root.width > 760 ? 3 : 2
            columnSpacing: 9
            rowSpacing: 9

            Repeater {
                model: [
                    {key:"proposals_accepted", label:appState.t("acceptedProposals"), color:Theme.emerald, icon:"✓"},
                    {key:"invoices_open", label:appState.t("openInvoices"), color:Theme.electricBlue, icon:"▤"},
                    {key:"receivables", label:appState.t("receivables"), color:Theme.gold, icon:"$"},
                    {key:"tickets_open", label:appState.t("openTickets"), color:Theme.violet, icon:"!"},
                    {key:"reminders_pending", label:appState.t("pendingReminders"), color:Theme.electricCyan, icon:"◷"}
                ]

                Rectangle {
                    required property var modelData
                    Layout.fillWidth: true
                    Layout.preferredHeight: 120
                    radius: 14
                    color: Theme.panel
                    border.width: 1
                    border.color: Qt.rgba(0.64, 0.73, 0.80, 0.28)

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 13
                        spacing: 5
                        RowLayout {
                            Layout.fillWidth: true
                            Rectangle {
                                width: 32; height: 32; radius: 8
                                color: "#071522"
                                border.width: 1
                                border.color: modelData.color
                                Text {
                                    anchors.centerIn: parent
                                    text: modelData.icon
                                    color: modelData.color
                                    font.pixelSize: 15
                                    font.bold: true
                                }
                            }
                            Item { Layout.fillWidth: true }
                            Text {
                                text: "LIVE"
                                color: modelData.color
                                font.pixelSize: 9
                                font.bold: true
                            }
                        }
                        Text {
                            text: modelData.key === "receivables" ? root.money(modelData.key) : root.value(modelData.key)
                            color: Theme.platinum
                            font.pixelSize: modelData.key === "receivables" ? 20 : 27
                            font.bold: true
                        }
                        Text {
                            Layout.fillWidth: true
                            text: modelData.label
                            color: Theme.muted
                            font.pixelSize: 11
                            elide: Text.ElideRight
                        }
                    }
                }
            }
        }

        GridLayout {
            Layout.fillWidth: true
            columns: root.width > 920 ? 2 : 1
            columnSpacing: 10
            rowSpacing: 10

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 300
                radius: 15
                color: Theme.panel
                border.width: 1
                border.color: Qt.rgba(0.65, 0.75, 0.82, 0.24)

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 7
                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: appState.t("proposals"); color: Theme.platinum; font.pixelSize: 17; font.bold: true }
                        Item { Layout.fillWidth: true }
                        Text { text: String(apiClient.proposals.length); color: Theme.emerald; font.pixelSize: 11 }
                    }
                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        spacing: 5
                        model: apiClient.proposals.slice(0, 8)
                        delegate: Rectangle {
                            required property var modelData
                            width: ListView.view.width
                            height: 47
                            radius: 8
                            color: index % 2 ? "#071521" : "#0B1C2B"
                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 10
                                anchors.rightMargin: 10
                                layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 1
                                    Text { text: modelData.title || modelData.proposal_number || "—"; color: Theme.platinum; font.pixelSize: 11; elide: Text.ElideRight; Layout.fillWidth: true }
                                    Text { text: modelData.proposal_number || ""; color: Theme.muted; font.pixelSize: 9 }
                                }
                                Text { text: modelData.status || "—"; color: modelData.status === "accepted" ? Theme.emerald : Theme.gold; font.pixelSize: 10 }
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 300
                radius: 15
                color: Theme.panel
                border.width: 1
                border.color: Qt.rgba(0.65, 0.75, 0.82, 0.24)

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 7
                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: appState.t("invoices"); color: Theme.platinum; font.pixelSize: 17; font.bold: true }
                        Item { Layout.fillWidth: true }
                        Text { text: String(apiClient.invoices.length); color: Theme.electricBlue; font.pixelSize: 11 }
                    }
                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        spacing: 5
                        model: apiClient.invoices.slice(0, 8)
                        delegate: Rectangle {
                            required property var modelData
                            width: ListView.view.width
                            height: 47
                            radius: 8
                            color: index % 2 ? "#071521" : "#0B1C2B"
                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 10
                                anchors.rightMargin: 10
                                layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 1
                                    Text { text: modelData.title || modelData.invoice_number || "—"; color: Theme.platinum; font.pixelSize: 11; elide: Text.ElideRight; Layout.fillWidth: true }
                                    Text { text: modelData.invoice_number || ""; color: Theme.muted; font.pixelSize: 9 }
                                }
                                Text { text: modelData.status || "—"; color: modelData.status === "paid" ? Theme.emerald : Theme.gold; font.pixelSize: 10 }
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 260
                radius: 15
                color: Theme.panel
                border.width: 1
                border.color: Qt.rgba(0.65, 0.75, 0.82, 0.24)

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 7
                    Text { text: appState.t("tickets"); color: Theme.platinum; font.pixelSize: 17; font.bold: true }
                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        spacing: 5
                        model: apiClient.tickets.slice(0, 7)
                        delegate: Rectangle {
                            required property var modelData
                            width: ListView.view.width
                            height: 45
                            radius: 8
                            color: index % 2 ? "#071521" : "#0B1C2B"
                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 10
                                anchors.rightMargin: 10
                                layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
                                Text { Layout.fillWidth: true; text: modelData.subject || "—"; color: Theme.platinum; font.pixelSize: 11; elide: Text.ElideRight }
                                Text { text: modelData.priority || ""; color: modelData.priority === "urgent" ? Theme.danger : Theme.violet; font.pixelSize: 9 }
                                Text { text: modelData.status || ""; color: Theme.muted; font.pixelSize: 9 }
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 260
                radius: 15
                color: Theme.panel
                border.width: 1
                border.color: Qt.rgba(0.65, 0.75, 0.82, 0.24)

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 7
                    Text { text: appState.t("reminders"); color: Theme.platinum; font.pixelSize: 17; font.bold: true }
                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        spacing: 5
                        model: apiClient.reminders.slice(0, 7)
                        delegate: Rectangle {
                            required property var modelData
                            width: ListView.view.width
                            height: 45
                            radius: 8
                            color: index % 2 ? "#071521" : "#0B1C2B"
                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 10
                                anchors.rightMargin: 10
                                layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
                                Text { Layout.fillWidth: true; text: modelData.title || "—"; color: Theme.platinum; font.pixelSize: 11; elide: Text.ElideRight }
                                Text { text: modelData.status || ""; color: Theme.electricCyan; font.pixelSize: 9 }
                            }
                        }
                    }
                }
            }
        }
    }
}
