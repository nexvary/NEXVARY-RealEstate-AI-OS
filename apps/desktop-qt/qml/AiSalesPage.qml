import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Flickable {
    id: root
    contentWidth: width
    contentHeight: body.implicitHeight + 28
    clip: true

    function money(v, currency) {
        var n = Number(v || 0)
        return n.toLocaleString(Qt.locale(appState.localize(appState.language, "ar_EG", "en_US")), "f", 0) + " " + (currency || "EGP")
    }

    ColumnLayout {
        id: body
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
                    text: (appState.language, appState.t("ai"))
                    color: Theme.platinum
                    font.family: appState.localize(appState.language, "Noto Kufi Arabic", "Segoe UI")
                    font.pixelSize: 29
                    font.bold: true
                }
                Text {
                    text: appState.localize(appState.language, "إجابات مبنية على المخزون الحقيقي وقاعدة المعرفة والوسائط الموثوقة", "Grounded answers from live inventory, knowledge and verified media")
                    color: Theme.muted
                    font.pixelSize: 12
                }
            }

            Rectangle {
                width: 158
                height: 46
                radius: 11
                color: Theme.panel
                border.width: 1
                border.color: Theme.borderSoft
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 9
                    Rectangle {
                        width: 9; height: 9; radius: 5
                        color: apiClient.healthStatus === "ok" ? Theme.emerald : Theme.gold
                    }
                    Text {
                        text: appState.localize(appState.language, "GROUNDING فعّال", "GROUNDING ACTIVE")
                        color: Theme.silver
                        font.pixelSize: 11
                        font.bold: true
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            radius: 15
            color: Theme.panel
            border.width: 1
            border.color: Qt.rgba(.69,.79,.86,.28)
            Layout.preferredHeight: 215

            GridLayout {
                anchors.fill: parent
                anchors.margins: 14
                columns: root.width > 1050 ? 4 : 2
                columnSpacing: 9
                rowSpacing: 9

                TextArea {
                    id: questionField
                    Layout.columnSpan: root.width > 1050 ? 4 : 2
                    Layout.fillWidth: true
                    Layout.preferredHeight: 82
                    placeholderText: appState.localize(appState.language, "مثال: أريد شقة 3 غرف في القاهرة بحد أقصى 4 مليون جنيه", "Example: Find a 3-bedroom apartment in Cairo under EGP 4M")
                    wrapMode: TextEdit.WordWrap
                }

                TextField {
                    id: cityField
                    Layout.fillWidth: true
                    placeholderText: appState.localize(appState.language, "المدينة", "City")
                }
                TextField {
                    id: minPriceField
                    Layout.fillWidth: true
                    placeholderText: appState.localize(appState.language, "أقل سعر", "Min price")
                    inputMethodHints: Qt.ImhFormattedNumbersOnly
                }
                TextField {
                    id: maxPriceField
                    Layout.fillWidth: true
                    placeholderText: appState.localize(appState.language, "أعلى سعر", "Max price")
                    inputMethodHints: Qt.ImhFormattedNumbersOnly
                }
                RowLayout {
                    Layout.fillWidth: true
                    SpinBox {
                        id: bedroomsField
                        from: -1
                        to: 20
                        value: -1
                        editable: true
                        Layout.preferredWidth: 110
                    }
                    TextField {
                        id: typeField
                        Layout.fillWidth: true
                        placeholderText: appState.localize(appState.language, "نوع الوحدة", "Unit type")
                    }
                    Button {
                        enabled: !apiClient.busy && questionField.text.trim().length >= 2
                        text: apiClient.busy ? "…" : (appState.localize(appState.language, "تحليل", "Analyze"))
                        onClicked: apiClient.runAiSalesAssist(
                            questionField.text,
                            cityField.text,
                            Number(minPriceField.text || 0),
                            Number(maxPriceField.text || 0),
                            bedroomsField.value,
                            typeField.text)
                    }
                }
            }
        }

        Rectangle {
            visible: apiClient.aiSalesResult.answer !== undefined
            Layout.fillWidth: true
            Layout.preferredHeight: Math.max(120, answerText.implicitHeight + 58)
            radius: 15
            color: "#081B29"
            border.width: 1
            border.color: Qt.rgba(.20,.76,1,.32)

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 15
                spacing: 7
                RowLayout {
                    Layout.fillWidth: true
                    layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
                    Rectangle {
                        width: 34; height: 34; radius: 9
                        color: "#06131F"
                        border.width: 1
                        border.color: Theme.electricCyan
                        Text { anchors.centerIn: parent; text: "✦"; color: Theme.electricCyan; font.pixelSize: 17 }
                    }
                    Text {
                        Layout.fillWidth: true
                        text: appState.localize(appState.language, "الإجابة المبنية على البيانات", "Grounded response")
                        color: Theme.platinum
                        font.pixelSize: 15
                        font.bold: true
                    }
                    Text {
                        text: apiClient.aiSalesResult.mode || ""
                        color: Theme.emerald
                        font.pixelSize: 11
                    }
                }
                Text {
                    id: answerText
                    Layout.fillWidth: true
                    text: apiClient.aiSalesResult.answer || ""
                    color: Theme.silver
                    font.pixelSize: 12
                    lineHeight: 1.45
                    wrapMode: Text.WordWrap
                    horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                }
            }
        }

        GridLayout {
            Layout.fillWidth: true
            columns: root.width > 980 ? 2 : 1
            columnSpacing: 10
            rowSpacing: 10

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 330
                radius: 15
                color: Theme.panel
                border.width: 1
                border.color: Qt.rgba(.68,.78,.85,.25)

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 13
                    spacing: 7
                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: appState.localize(appState.language, "الوحدات المطابقة", "Matching Units"); color: Theme.platinum; font.pixelSize: 17; font.bold: true }
                        Item { Layout.fillWidth: true }
                        Text { text: String((apiClient.aiSalesResult.units || []).length); color: Theme.emerald; font.pixelSize: 11; font.bold: true }
                    }
                    ListView {
                        id: unitsList
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        spacing: 5
                        model: apiClient.aiSalesResult.units || []
                        delegate: Rectangle {
                            required property var modelData
                            width: unitsList.width
                            height: 58
                            radius: 9
                            color: index % 2 ? "#071521" : "#0A1B2A"
                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 9
                                layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
                                Rectangle {
                                    width: 31; height: 31; radius: 8
                                    color: "#06131F"; border.width: 1; border.color: Theme.emerald
                                    Text { anchors.centerIn: parent; text: "▦"; color: Theme.emerald }
                                }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 2
                                    Text { text: (modelData.code || "—") + " · " + (modelData.unit_type || ""); color: Theme.platinum; font.pixelSize: 11; font.bold: true }
                                    Text { text: String(modelData.bedrooms === null ? "—" : modelData.bedrooms) + " BR · " + String(modelData.area_sqm || 0) + " m²"; color: Theme.muted; font.pixelSize: 11 }
                                }
                                Text { text: root.money(modelData.price, modelData.currency); color: Theme.gold; font.pixelSize: 11; font.bold: true }
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 330
                radius: 15
                color: Theme.panel
                border.width: 1
                border.color: Qt.rgba(.68,.78,.85,.25)

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 13
                    spacing: 7
                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: appState.localize(appState.language, "الأدلة والمراجع", "Evidence & Sources"); color: Theme.platinum; font.pixelSize: 17; font.bold: true }
                        Item { Layout.fillWidth: true }
                        Text { text: String((apiClient.aiSalesResult.evidence || []).length); color: Theme.violet; font.pixelSize: 11; font.bold: true }
                    }
                    ListView {
                        id: evidenceList
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        spacing: 6
                        model: apiClient.aiSalesResult.evidence || []
                        delegate: Rectangle {
                            required property var modelData
                            width: evidenceList.width
                            height: Math.max(72, evText.implicitHeight + 42)
                            radius: 9
                            color: index % 2 ? "#071521" : "#0A1B2A"
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 9
                                spacing: 3
                                RowLayout {
                                    Layout.fillWidth: true
                                    Text { Layout.fillWidth: true; text: modelData.document_title || "—"; color: Theme.electricCyan; font.pixelSize: 11; font.bold: true; elide: Text.ElideRight }
                                    Text { text: "SCORE " + String(modelData.score || 0); color: Theme.emerald; font.pixelSize: 8; font.bold: true }
                                }
                                Text {
                                    id: evText
                                    Layout.fillWidth: true
                                    text: modelData.text || ""
                                    color: Theme.silver
                                    font.pixelSize: 11
                                    wrapMode: Text.WordWrap
                                    maximumLineCount: 4
                                    elide: Text.ElideRight
                                    horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                                }
                            }
                        }
                    }
                }
            }
        }

        Rectangle {
            visible: (apiClient.aiSalesResult.media || []).length > 0
            Layout.fillWidth: true
            Layout.preferredHeight: 116
            radius: 14
            color: Theme.panel
            border.width: 1
            border.color: Qt.rgba(.68,.78,.85,.25)

            RowLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 8
                layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight

                Text {
                    text: appState.localize(appState.language, "وسائط موثوقة", "Verified Media")
                    color: Theme.platinum
                    font.pixelSize: 13
                    font.bold: true
                }
                Repeater {
                    model: (apiClient.aiSalesResult.media || []).slice(0, 5)
                    Rectangle {
                        required property var modelData
                        Layout.fillWidth: true
                        Layout.preferredHeight: 78
                        radius: 9
                        color: "#071522"
                        border.width: 1
                        border.color: modelData.verified ? Theme.emerald : Theme.borderSoft
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 8
                            Text { Layout.fillWidth: true; text: modelData.title || "—"; color: Theme.silver; font.pixelSize: 11; elide: Text.ElideRight }
                            Text { text: modelData.media_type || ""; color: modelData.verified ? Theme.emerald : Theme.gold; font.pixelSize: 8 }
                        }
                    }
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
