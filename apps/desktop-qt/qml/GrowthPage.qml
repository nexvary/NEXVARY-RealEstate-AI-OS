import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Theme.js" as Theme

Flickable {
    id: root
    contentWidth: width
    contentHeight: content.implicitHeight + 24
    clip: true
    property bool canManage: apiClient.userRole === "owner" || apiClient.userRole === "admin" || apiClient.userRole === "sales_manager"

    Dialog {
        id: addDialog
        property string mode: "campaign"
        modal: true
        width: Math.min(620, root.width - 40)
        anchors.centerIn: parent
        background: Rectangle { radius: 18; color: Theme.panel; border.width: 1; border.color: Qt.rgba(.72,.82,.89,.34) }

        function openFor(nextMode) {
            mode = nextMode
            field1.text = ""
            field2.text = ""
            field3.text = ""
            amount1.text = ""
            amount2.text = ""
            longText.text = ""
            open()
        }

        function titleText() {
            if (mode === "campaign") return appState.rtl ? "حملة جديدة" : "New Campaign"
            if (mode === "audience") return appState.rtl ? "شريحة جمهور" : "Audience Segment"
            if (mode === "media") return appState.rtl ? "وسائط عقارية" : "Property Media"
            if (mode === "playbook") return appState.rtl ? "دليل مبيعات" : "Sales Playbook"
            return appState.rtl ? "ملاحظة عميل" : "Customer Feedback"
        }

        contentItem: ColumnLayout {
            spacing: 9
            Text { text: addDialog.titleText(); color: Theme.platinum; font.pixelSize: 20; font.bold: true }
            TextField {
                id: field1; Layout.fillWidth: true
                placeholderText: addDialog.mode === "campaign" ? (appState.rtl ? "اسم الحملة" : "Campaign name")
                    : addDialog.mode === "audience" ? (appState.rtl ? "اسم الشريحة" : "Segment name")
                    : addDialog.mode === "media" ? (appState.rtl ? "عنوان الوسائط" : "Media title")
                    : addDialog.mode === "playbook" ? (appState.rtl ? "اسم الدليل" : "Playbook name")
                    : (appState.rtl ? "التصنيف" : "Category")
            }
            TextField {
                id: field2; Layout.fillWidth: true
                placeholderText: addDialog.mode === "campaign" ? (appState.rtl ? "القناة: facebook / google / ..." : "Channel: facebook / google / ...")
                    : addDialog.mode === "audience" ? (appState.rtl ? "المصدر مثل facebook" : "Lead source")
                    : addDialog.mode === "media" ? "https://..."
                    : addDialog.mode === "playbook" ? (appState.rtl ? "مرحلة التشغيل" : "Trigger stage")
                    : (appState.rtl ? "القناة" : "Channel")
            }
            TextField {
                id: field3; Layout.fillWidth: true
                placeholderText: addDialog.mode === "campaign" ? (appState.rtl ? "الهدف" : "Objective")
                    : addDialog.mode === "audience" ? (appState.rtl ? "المدينة" : "City")
                    : addDialog.mode === "media" ? (appState.rtl ? "نوع الوسائط" : "Media type")
                    : addDialog.mode === "playbook" ? (appState.rtl ? "الوصف" : "Description")
                    : ""
                visible: addDialog.mode !== "feedback"
            }
            RowLayout {
                Layout.fillWidth: true
                visible: addDialog.mode === "campaign" || addDialog.mode === "audience"
                TextField { id: amount1; Layout.fillWidth: true; placeholderText: addDialog.mode === "campaign" ? (appState.rtl ? "الميزانية" : "Budget") : (appState.rtl ? "أقل ميزانية" : "Min budget"); inputMethodHints: Qt.ImhFormattedNumbersOnly }
                TextField { id: amount2; Layout.fillWidth: true; placeholderText: addDialog.mode === "campaign" ? (appState.rtl ? "المصروف" : "Spend") : (appState.rtl ? "أقصى ميزانية" : "Max budget"); inputMethodHints: Qt.ImhFormattedNumbersOnly }
            }
            ComboBox {
                id: relationPicker
                visible: addDialog.mode === "media" || addDialog.mode === "feedback"
                Layout.fillWidth: true
                model: addDialog.mode === "media" ? apiClient.projects : apiClient.leads
                textRole: addDialog.mode === "media" ? "name" : "full_name"
                valueRole: "id"
            }
            ComboBox {
                id: auxPicker
                visible: addDialog.mode === "media" || addDialog.mode === "audience" || addDialog.mode === "feedback"
                Layout.fillWidth: true
                model: addDialog.mode === "media"
                    ? ["image","video","pdf","floorplan","virtual_tour"]
                    : addDialog.mode === "audience"
                        ? ["","new","contacted","qualified","viewing","negotiation","won","lost"]
                        : [1,2,3,4,5]
            }
            TextArea {
                id: longText
                Layout.fillWidth: true
                Layout.preferredHeight: 100
                placeholderText: addDialog.mode === "playbook"
                    ? (appState.rtl ? "كل خطوة في سطر مستقل" : "One step per line")
                    : addDialog.mode === "feedback"
                        ? (appState.rtl ? "تعليق العميل" : "Customer comment")
                        : (appState.rtl ? "وصف / ملاحظات" : "Description / notes")
                wrapMode: TextEdit.WordWrap
            }
            RowLayout {
                Layout.fillWidth: true; layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
                Button {
                    Layout.fillWidth: true; enabled: !apiClient.busy && field1.text.length >= 2
                    text: appState.rtl ? "حفظ" : "Save"
                    onClicked: {
                        if (addDialog.mode === "campaign")
                            apiClient.createGrowthCampaign(field1.text, field2.text, field3.text, Number(amount1.text||0), Number(amount2.text||0), "EGP", "", "", field1.text)
                        else if (addDialog.mode === "audience")
                            apiClient.createGrowthAudience(field1.text, longText.text, field2.text, auxPicker.currentText, 0, field3.text, Number(amount1.text||0), Number(amount2.text||0))
                        else if (addDialog.mode === "media")
                            apiClient.createGrowthMedia(relationPicker.currentValue||"", "", field1.text, auxPicker.currentText, field2.text, "company", true)
                        else if (addDialog.mode === "playbook")
                            apiClient.createGrowthPlaybook(field1.text, field3.text, field2.text, longText.text)
                        else
                            apiClient.createGrowthFeedback(relationPicker.currentValue||"", "", field2.text, field1.text, Number(auxPicker.currentText||0), longText.text)
                        addDialog.close()
                    }
                }
                Button { text: appState.rtl ? "إلغاء" : "Cancel"; onClicked: addDialog.close() }
            }
        }
    }

    Menu {
        id: addMenu
        MenuItem { text: appState.rtl ? "حملة" : "Campaign"; onTriggered: addDialog.openFor("campaign") }
        MenuItem { text: appState.rtl ? "جمهور" : "Audience"; onTriggered: addDialog.openFor("audience") }
        MenuItem { text: appState.rtl ? "وسائط" : "Media"; onTriggered: addDialog.openFor("media") }
        MenuItem { text: appState.rtl ? "Playbook" : "Playbook"; onTriggered: addDialog.openFor("playbook") }
        MenuItem { text: appState.rtl ? "Feedback" : "Feedback"; onTriggered: addDialog.openFor("feedback") }
    }

    ColumnLayout {
        id: content
        width: root.width
        spacing: 11

        RowLayout {
            Layout.fillWidth: true; layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
            ColumnLayout {
                Layout.fillWidth: true
                Text { text: appState.t("growth"); color: Theme.platinum; font.family: appState.rtl ? "Noto Kufi Arabic" : "Segoe UI"; font.pixelSize: 29; font.bold: true }
                Text { text: appState.rtl ? "الإسناد التسويقي والجمهور والوسائط وPlaybooks ورضا العملاء" : "Attribution, audiences, property media, playbooks and feedback"; color: Theme.muted; font.pixelSize: 12 }
            }
            Button { visible: root.canManage; text: appState.rtl ? "+ إضافة" : "+ Add"; onClicked: addMenu.open() }
            Button { text: appState.t("refresh"); onClicked: apiClient.refreshGrowth() }
        }

        GridLayout {
            Layout.fillWidth: true
            columns: 4
            columnSpacing: 8
            Repeater {
                model: [
                    {v:apiClient.growthCampaigns.length,l:appState.rtl?"الحملات":"Campaigns",c:Theme.electricBlue},
                    {v:apiClient.growthAudiences.length,l:appState.rtl?"شرائح الجمهور":"Audiences",c:Theme.violet},
                    {v:apiClient.growthMedia.filter(function(x){return x.is_verified}).length,l:appState.rtl?"وسائط موثقة":"Verified Media",c:Theme.emerald},
                    {v:apiClient.growthFeedbackSummary.average_rating===undefined||apiClient.growthFeedbackSummary.average_rating===null?"—":apiClient.growthFeedbackSummary.average_rating,l:appState.rtl?"رضا العملاء":"Avg Rating",c:Theme.gold}
                ]
                Rectangle {
                    required property var modelData
                    Layout.fillWidth: true; Layout.preferredHeight: 88; radius: 12
                    color: Theme.panel; border.width: 1; border.color: Qt.rgba(.67,.76,.83,.25)
                    RowLayout {
                        anchors.fill: parent; anchors.margins: 12; layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
                        Rectangle { width:30;height:30;radius:8;color:"#071522";border.width:1;border.color:modelData.c;Text{anchors.centerIn:parent;text:"◆";color:modelData.c} }
                        ColumnLayout { Layout.fillWidth:true; Text{text:String(modelData.v);color:Theme.platinum;font.pixelSize:20;font.bold:true} Text{text:modelData.l;color:Theme.muted;font.pixelSize:9} }
                    }
                }
            }
        }

        GridLayout {
            Layout.fillWidth: true
            columns: root.width > 1050 ? 2 : 1
            columnSpacing: 9; rowSpacing: 9

            Rectangle {
                Layout.fillWidth: true; Layout.preferredHeight: 310; radius: 14
                color: Theme.panel; border.width:1; border.color:Qt.rgba(.67,.76,.83,.25)
                ColumnLayout {
                    anchors.fill:parent;anchors.margins:12;spacing:6
                    Text{text:appState.rtl?"أداء الحملات والإسناد":"Campaign Attribution";color:Theme.platinum;font.pixelSize:16;font.bold:true}
                    ListView {
                        id:attrList;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;spacing:5;model:apiClient.growthAttribution
                        delegate:Rectangle {
                            required property var modelData
                            width:attrList.width;height:58;radius:8;color:index%2?"#071521":"#0A1B2A"
                            RowLayout {
                                anchors.fill:parent;anchors.margins:8;layoutDirection:appState.rtl?Qt.RightToLeft:Qt.LeftToRight
                                ColumnLayout { Layout.fillWidth:true; Text{Layout.fillWidth:true;text:modelData.campaign_name||"—";color:Theme.platinum;font.pixelSize:11;font.bold:true;elide:Text.ElideRight} Text{text:(modelData.channel||"")+" · "+String(modelData.leads_touched||0)+" leads";color:Theme.muted;font.pixelSize:8} }
                                Text{text:"ROAS "+(modelData.roas_last_touch===null||modelData.roas_last_touch===undefined?"—":String(modelData.roas_last_touch));color:Theme.emerald;font.pixelSize:9;font.bold:true}
                                Text{text:Number(modelData.spend||0).toLocaleString(Qt.locale("en_US"),"f",0)+" "+(modelData.currency||"");color:Theme.gold;font.pixelSize:9}
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth:true;Layout.preferredHeight:310;radius:14;color:Theme.panel;border.width:1;border.color:Qt.rgba(.67,.76,.83,.25)
                ColumnLayout {
                    anchors.fill:parent;anchors.margins:12;spacing:6
                    Text{text:appState.rtl?"Audience 360":"Audience 360";color:Theme.platinum;font.pixelSize:16;font.bold:true}
                    ListView {
                        id:audList;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;spacing:5;model:apiClient.growthAudiences
                        delegate:Rectangle {
                            required property var modelData
                            width:audList.width;height:58;radius:8;color:index%2?"#071521":"#0A1B2A"
                            RowLayout {
                                anchors.fill:parent;anchors.margins:8;layoutDirection:appState.rtl?Qt.RightToLeft:Qt.LeftToRight
                                Rectangle{width:31;height:31;radius:8;color:"#071522";border.width:1;border.color:Theme.violet;Text{anchors.centerIn:parent;text:"◎";color:Theme.violet}}
                                ColumnLayout{Layout.fillWidth:true;Text{Layout.fillWidth:true;text:modelData.name||"—";color:Theme.platinum;font.pixelSize:11;font.bold:true;elide:Text.ElideRight}Text{Layout.fillWidth:true;text:modelData.description||"";color:Theme.muted;font.pixelSize:8;elide:Text.ElideRight}}
                                Text{text:modelData.is_active?"ACTIVE":"OFF";color:modelData.is_active?Theme.emerald:Theme.muted;font.pixelSize:8;font.bold:true}
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth:true;Layout.preferredHeight:280;radius:14;color:Theme.panel;border.width:1;border.color:Qt.rgba(.67,.76,.83,.25)
                ColumnLayout {
                    anchors.fill:parent;anchors.margins:12;spacing:6
                    Text{text:appState.rtl?"Property Media Intelligence":"Property Media Intelligence";color:Theme.platinum;font.pixelSize:16;font.bold:true}
                    ListView {
                        id:mediaList;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;spacing:5;model:apiClient.growthMedia
                        delegate:Rectangle{
                            required property var modelData
                            width:mediaList.width;height:54;radius:8;color:index%2?"#071521":"#0A1B2A"
                            RowLayout{anchors.fill:parent;anchors.margins:8;layoutDirection:appState.rtl?Qt.RightToLeft:Qt.LeftToRight
                                Text{Layout.fillWidth:true;text:modelData.title||"—";color:Theme.platinum;font.pixelSize:10;font.bold:true;elide:Text.ElideRight}
                                Text{text:modelData.media_type||"";color:Theme.electricCyan;font.pixelSize:8}
                                Text{text:modelData.is_verified?"VERIFIED":"UNVERIFIED";color:modelData.is_verified?Theme.emerald:Theme.gold;font.pixelSize:8;font.bold:true}
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth:true;Layout.preferredHeight:280;radius:14;color:Theme.panel;border.width:1;border.color:Qt.rgba(.67,.76,.83,.25)
                ColumnLayout {
                    anchors.fill:parent;anchors.margins:12;spacing:6
                    Text{text:appState.rtl?"Sales Playbooks & Feedback":"Sales Playbooks & Feedback";color:Theme.platinum;font.pixelSize:16;font.bold:true}
                    ListView {
                        id:playList;Layout.fillWidth:true;Layout.preferredHeight:125;clip:true;spacing:4;model:apiClient.growthPlaybooks
                        delegate:Rectangle{
                            required property var modelData;width:playList.width;height:48;radius:8;color:index%2?"#071521":"#0A1B2A"
                            RowLayout{anchors.fill:parent;anchors.margins:8;layoutDirection:appState.rtl?Qt.RightToLeft:Qt.LeftToRight
                                Text{Layout.fillWidth:true;text:modelData.name||"—";color:Theme.platinum;font.pixelSize:10;font.bold:true;elide:Text.ElideRight}
                                Text{text:modelData.trigger_stage||"all";color:Theme.violet;font.pixelSize:8}
                            }
                        }
                    }
                    Rectangle{Layout.fillWidth:true;height:1;color:Theme.borderSoft}
                    ListView {
                        id:feedList;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;spacing:4;model:apiClient.growthFeedback
                        delegate:Rectangle{
                            required property var modelData;width:feedList.width;height:48;radius:8;color:index%2?"#071521":"#0A1B2A"
                            RowLayout{anchors.fill:parent;anchors.margins:8;layoutDirection:appState.rtl?Qt.RightToLeft:Qt.LeftToRight
                                Text{Layout.fillWidth:true;text:modelData.comment||"—";color:Theme.silver;font.pixelSize:9;elide:Text.ElideRight}
                                Text{text:modelData.rating?String(modelData.rating)+"/5":"—";color:Theme.gold;font.pixelSize:9;font.bold:true}
                            }
                        }
                    }
                }
            }
        }
    }
}
