import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Theme.js" as Theme

Item {
    id: root

    Dialog {
        id: projectDialog
        modal: true
        width: Math.min(520, root.width - 40)
        anchors.centerIn: parent
        background: Rectangle { radius: 17; color: Theme.panel; border.width: 1; border.color: Qt.rgba(.7,.8,.88,.32) }
        contentItem: ColumnLayout {
            spacing: 9
            Text { text: appState.rtl ? "مشروع عقاري جديد" : "New Project"; color: Theme.platinum; font.pixelSize: 19; font.bold: true }
            TextField { id: projectName; Layout.fillWidth: true; placeholderText: appState.rtl ? "اسم المشروع" : "Project name" }
            TextField { id: projectCity; Layout.fillWidth: true; placeholderText: appState.rtl ? "المدينة" : "City" }
            TextField { id: projectDeveloper; Layout.fillWidth: true; placeholderText: appState.rtl ? "المطور" : "Developer" }
            TextArea { id: projectDescription; Layout.fillWidth: true; Layout.preferredHeight: 80; placeholderText: appState.rtl ? "الوصف" : "Description"; wrapMode: TextEdit.WordWrap }
            RowLayout {
                Layout.fillWidth: true
                Button {
                    Layout.fillWidth: true
                    text: appState.rtl ? "حفظ المشروع" : "Save Project"
                    onClicked: {
                        apiClient.createProject(projectName.text, projectCity.text, projectDeveloper.text, projectDescription.text)
                        projectDialog.close()
                    }
                }
                Button { text: appState.rtl ? "إلغاء" : "Cancel"; onClicked: projectDialog.close() }
            }
        }
    }

    Dialog {
        id: unitDialog
        modal: true
        width: Math.min(560, root.width - 40)
        anchors.centerIn: parent
        background: Rectangle { radius: 17; color: Theme.panel; border.width: 1; border.color: Qt.rgba(.7,.8,.88,.32) }
        contentItem: ColumnLayout {
            spacing: 9
            Text { text: appState.rtl ? "إضافة وحدة" : "Add Unit"; color: Theme.platinum; font.pixelSize: 19; font.bold: true }
            ComboBox { id: unitProject; Layout.fillWidth: true; model: apiClient.projects; textRole: "name"; valueRole: "id" }
            RowLayout {
                Layout.fillWidth: true
                TextField { id: unitCode; Layout.fillWidth: true; placeholderText: appState.rtl ? "كود الوحدة" : "Unit code" }
                TextField { id: unitType; Layout.fillWidth: true; placeholderText: appState.rtl ? "النوع" : "Type"; text: "apartment" }
            }
            RowLayout {
                Layout.fillWidth: true
                SpinBox { id: unitBedrooms; from: 0; to: 30; value: 2; editable: true; Layout.preferredWidth: 120 }
                TextField { id: unitArea; Layout.fillWidth: true; placeholderText: appState.rtl ? "المساحة م²" : "Area sqm"; inputMethodHints: Qt.ImhFormattedNumbersOnly }
            }
            RowLayout {
                Layout.fillWidth: true
                TextField { id: unitPrice; Layout.fillWidth: true; placeholderText: appState.rtl ? "السعر" : "Price"; inputMethodHints: Qt.ImhFormattedNumbersOnly }
                TextField { id: unitCurrency; Layout.preferredWidth: 100; text: "EGP"; placeholderText: "EGP" }
            }
            RowLayout {
                Layout.fillWidth: true
                Button {
                    Layout.fillWidth: true
                    enabled: unitProject.count > 0
                    text: appState.rtl ? "حفظ الوحدة" : "Save Unit"
                    onClicked: {
                        apiClient.createUnit(unitProject.currentValue || "", unitCode.text, unitType.text, unitBedrooms.value, Number(unitArea.text || 0), Number(unitPrice.text || 0), unitCurrency.text)
                        unitDialog.close()
                    }
                }
                Button { text: appState.rtl ? "إلغاء" : "Cancel"; onClicked: unitDialog.close() }
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
                Text { text: appState.t("inventory"); color: Theme.platinum; font.family: appState.rtl ? "Noto Kufi Arabic" : "Segoe UI"; font.pixelSize: 29; font.bold: true }
                Text { text: appState.rtl ? "المشروعات والوحدات والمخزون المتاح" : "Projects, units and live inventory"; color: Theme.muted; font.pixelSize: 12 }
            }
            Button { text: appState.rtl ? "+ مشروع" : "+ Project"; onClicked: projectDialog.open() }
            Button { text: appState.rtl ? "+ وحدة" : "+ Unit"; enabled: apiClient.projects.length > 0; onClicked: unitDialog.open() }
            Button { text: appState.t("refresh"); onClicked: apiClient.refreshAll() }
        }

        GridLayout {
            Layout.fillWidth: true
            columns: 3
            columnSpacing: 9
            Repeater {
                model: [
                    {value:apiClient.projects.length, label:appState.rtl ? "المشروعات" : "Projects", color:Theme.electricBlue},
                    {value:apiClient.units.length, label:appState.rtl ? "كل الوحدات" : "All units", color:Theme.violet},
                    {value:apiClient.overview.units_available || 0, label:appState.rtl ? "متاح الآن" : "Available now", color:Theme.emerald}
                ]
                Rectangle {
                    required property var modelData
                    Layout.fillWidth: true
                    Layout.preferredHeight: 92
                    radius: 13
                    color: Theme.panel
                    border.width: 1
                    border.color: Qt.rgba(.67,.76,.83,.25)
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 14
                        layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
                        Rectangle { width: 34; height: 34; radius: 9; color: "#071522"; border.width: 1; border.color: modelData.color; Text { anchors.centerIn: parent; text: "◆"; color: modelData.color } }
                        ColumnLayout {
                            Layout.fillWidth: true
                            Text { text: String(modelData.value); color: Theme.platinum; font.pixelSize: 22; font.bold: true }
                            Text { text: modelData.label; color: Theme.muted; font.pixelSize: 10 }
                        }
                    }
                }
            }
        }

        GridLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            columns: root.width > 900 ? 2 : 1
            columnSpacing: 10
            rowSpacing: 10

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: 15
                color: Theme.panel
                border.width: 1
                border.color: Qt.rgba(.67,.76,.83,.25)
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 13
                    Text { text: appState.rtl ? "المشروعات" : "Projects"; color: Theme.platinum; font.pixelSize: 17; font.bold: true }
                    ListView {
                        id: projectsList
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        spacing: 5
                        model: apiClient.projects
                        delegate: Rectangle {
                            required property var modelData
                            width: projectsList.width
                            height: 58
                            radius: 9
                            color: index % 2 ? "#071521" : "#0A1B2A"
                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 10
                                layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
                                Rectangle { width: 30; height: 30; radius: 8; color:"#071522"; border.width:1; border.color:Theme.electricBlue; Text { anchors.centerIn: parent; text:"▦"; color:Theme.electricBlue } }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    Text { Layout.fillWidth: true; text:modelData.name || "—"; color:Theme.platinum; font.pixelSize:12; font.bold:true; elide:Text.ElideRight }
                                    Text { Layout.fillWidth: true; text:(modelData.city || "—") + " · " + (modelData.developer || "—"); color:Theme.muted; font.pixelSize:9; elide:Text.ElideRight }
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
                border.color: Qt.rgba(.67,.76,.83,.25)
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 13
                    Text { text: appState.rtl ? "الوحدات" : "Units"; color: Theme.platinum; font.pixelSize: 17; font.bold: true }
                    ListView {
                        id: unitsList
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        spacing: 5
                        model: apiClient.units
                        delegate: Rectangle {
                            required property var modelData
                            width: unitsList.width
                            height: 62
                            radius: 9
                            color: index % 2 ? "#071521" : "#0A1B2A"
                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 10
                                layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
                                Rectangle {
                                    width: 32; height: 32; radius: 8; color:"#071522"; border.width:1
                                    border.color: modelData.status === "available" ? Theme.emerald : modelData.status === "sold" ? Theme.gold : Theme.violet
                                    Text { anchors.centerIn:parent; text:"■"; color:parent.border.color }
                                }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    Text { Layout.fillWidth:true; text:(modelData.code || "—") + " · " + (modelData.unit_type || ""); color:Theme.platinum; font.pixelSize:12; font.bold:true; elide:Text.ElideRight }
                                    Text { Layout.fillWidth:true; text:String(modelData.area_sqm || "—") + " m² · " + String(modelData.bedrooms === null || modelData.bedrooms === undefined ? "—" : modelData.bedrooms) + " BR"; color:Theme.muted; font.pixelSize:9 }
                                }
                                ColumnLayout {
                                    Text { text:Number(modelData.price || 0).toLocaleString(Qt.locale("en_US"),"f",0) + " " + (modelData.currency || ""); color:Theme.silver; font.pixelSize:10; font.bold:true }
                                    Text { text:modelData.status || "—"; color:modelData.status === "available" ? Theme.emerald : Theme.gold; font.pixelSize:9 }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
