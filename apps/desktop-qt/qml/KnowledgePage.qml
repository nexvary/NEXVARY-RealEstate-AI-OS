import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Theme.js" as Theme

Item {
    id: root

    Dialog {
        id: addDialog
        modal: true
        width: Math.min(620, root.width - 40)
        anchors.centerIn: parent
        background: Rectangle { radius: 18; color: Theme.panel; border.width: 1; border.color: Qt.rgba(.72,.82,.89,.34) }
        contentItem: ColumnLayout {
            spacing: 9
            Text { text: appState.rtl ? "إضافة مستند معرفة" : "Add Knowledge Document"; color: Theme.platinum; font.pixelSize: 20; font.bold: true }
            TextField { id: titleField; Layout.fillWidth: true; placeholderText: appState.rtl ? "عنوان المستند" : "Document title" }
            RowLayout {
                Layout.fillWidth: true
                TextField { id: categoryField; Layout.fillWidth: true; text: "general"; placeholderText: appState.rtl ? "التصنيف" : "Category" }
                TextField { id: sourceField; Layout.fillWidth: true; placeholderText: appState.rtl ? "المصدر" : "Source" }
            }
            TextArea {
                id: contentField
                Layout.fillWidth: true
                Layout.preferredHeight: 220
                placeholderText: appState.rtl ? "محتوى موثوق يستخدمه مساعد المبيعات..." : "Verified content used by the sales copilot..."
                wrapMode: TextEdit.WordWrap
            }
            RowLayout {
                Layout.fillWidth: true
                layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
                Button {
                    Layout.fillWidth: true
                    enabled: !apiClient.busy && titleField.text.length >= 2 && contentField.text.length >= 20
                    text: appState.rtl ? "حفظ وفهرسة" : "Save & Index"
                    onClicked: {
                        apiClient.createKnowledgeDocument(titleField.text, categoryField.text, sourceField.text, contentField.text)
                        addDialog.close()
                    }
                }
                Button { text: appState.rtl ? "إلغاء" : "Cancel"; onClicked: addDialog.close() }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 11

        RowLayout {
            Layout.fillWidth: true
            layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
            ColumnLayout {
                Layout.fillWidth: true
                Text { text: (appState.language, appState.t("knowledge")); color: Theme.platinum; font.family: appState.rtl ? "Noto Kufi Arabic" : "Segoe UI"; font.pixelSize: 29; font.bold: true }
                Text { text: appState.rtl ? "مصادر موثوقة للبحث والردود المبنية على الأدلة" : "Verified sources for grounded search and sales replies"; color: Theme.muted; font.pixelSize: 12 }
            }
            Button { text: appState.rtl ? "+ مستند" : "+ Document"; onClicked: addDialog.open() }
            Button { text: (appState.language, appState.t("refresh")); onClicked: apiClient.refreshWorkspace() }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 72
            radius: 13
            color: Theme.panel
            border.width: 1
            border.color: Qt.rgba(.68,.78,.85,.26)
            RowLayout {
                anchors.fill: parent
                anchors.margins: 11
                layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
                TextField {
                    id: queryField
                    Layout.fillWidth: true
                    placeholderText: appState.rtl ? "ابحث داخل قاعدة المعرفة..." : "Search the knowledge base..."
                    onAccepted: if (text.length >= 2) apiClient.queryKnowledge(text)
                }
                Button {
                    text: appState.rtl ? "بحث موثوق" : "Grounded Search"
                    enabled: queryField.text.length >= 2 && !apiClient.busy
                    onClicked: apiClient.queryKnowledge(queryField.text)
                }
            }
        }

        GridLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            columns: root.width > 950 ? 2 : 1
            columnSpacing: 10
            rowSpacing: 10

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: 15
                color: Theme.panel
                border.width: 1
                border.color: Qt.rgba(.68,.78,.85,.25)
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 13; spacing: 7
                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: appState.rtl ? "المستندات" : "Documents"; color: Theme.platinum; font.pixelSize: 17; font.bold: true }
                        Item { Layout.fillWidth: true }
                        Text { text: String(apiClient.knowledgeDocuments.length); color: Theme.electricCyan; font.pixelSize: 11; font.bold: true }
                    }
                    ListView {
                        id: docs
                        Layout.fillWidth: true; Layout.fillHeight: true; clip: true; spacing: 5
                        model: apiClient.knowledgeDocuments
                        delegate: Rectangle {
                            required property var modelData
                            width: docs.width; height: 62; radius: 9
                            color: index % 2 ? "#071521" : "#0A1B2A"
                            RowLayout {
                                anchors.fill: parent; anchors.margins: 9
                                layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
                                Rectangle { width: 32; height: 32; radius: 8; color: "#071522"; border.width: 1; border.color: Theme.violet; Text { anchors.centerIn: parent; text: "▤"; color: Theme.violet } }
                                ColumnLayout {
                                    Layout.fillWidth: true; spacing: 2
                                    Text { Layout.fillWidth: true; text: modelData.title || "—"; color: Theme.platinum; font.pixelSize: 12; font.bold: true; elide: Text.ElideRight }
                                    Text { Layout.fillWidth: true; text: (modelData.category || "general") + " · " + String(modelData.chunk_count || 0) + " chunks"; color: Theme.muted; font.pixelSize: 9; elide: Text.ElideRight }
                                }
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: 15
                color: Theme.panel
                border.width: 1
                border.color: Qt.rgba(.68,.78,.85,.25)
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 13; spacing: 7
                    Text { text: appState.rtl ? "نتائج البحث الموثوق" : "Grounded Results"; color: Theme.platinum; font.pixelSize: 17; font.bold: true }
                    ListView {
                        id: hits
                        Layout.fillWidth: true; Layout.fillHeight: true; clip: true; spacing: 7
                        model: apiClient.knowledgeHits
                        delegate: Rectangle {
                            required property var modelData
                            width: hits.width
                            height: Math.max(94, hitText.implicitHeight + 52)
                            radius: 9
                            color: index % 2 ? "#071521" : "#0A1B2A"
                            ColumnLayout {
                                anchors.fill: parent; anchors.margins: 10; spacing: 4
                                RowLayout {
                                    Layout.fillWidth: true
                                    layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
                                    Text { Layout.fillWidth: true; text: modelData.document_title || "—"; color: Theme.electricCyan; font.pixelSize: 11; font.bold: true; elide: Text.ElideRight }
                                    Text { text: "SCORE " + String(modelData.score || 0); color: Theme.emerald; font.pixelSize: 9; font.bold: true }
                                }
                                Text {
                                    id: hitText
                                    Layout.fillWidth: true
                                    text: modelData.text || ""
                                    color: Theme.silver
                                    font.pixelSize: 10
                                    wrapMode: Text.WordWrap
                                    maximumLineCount: 5
                                    elide: Text.ElideRight
                                    horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
