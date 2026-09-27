import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Theme.js" as Theme

Item {
    id: root
    property var selectedConversation: null
    property bool manager: apiClient.userRole === "owner" || apiClient.userRole === "admin" || apiClient.userRole === "sales_manager"

    Dialog {
        id: conversationDialog
        modal: true; width: Math.min(520, root.width - 40); anchors.centerIn: parent
        background: Rectangle { radius:18; color:Theme.panel; border.width:1; border.color:Qt.rgba(.72,.82,.89,.34) }
        contentItem: ColumnLayout {
            spacing: 9
            Text { text: appState.rtl ? "محادثة جديدة" : "New Conversation"; color:Theme.platinum; font.pixelSize:19; font.bold:true }
            ComboBox { id: convLead; Layout.fillWidth:true; model:[{id:"",full_name:appState.rtl?"بدون Lead":"No lead"}].concat(apiClient.leads); textRole:"full_name"; valueRole:"id" }
            ComboBox { id: convChannel; Layout.fillWidth:true; model:["manual","whatsapp","website","instagram","messenger","telegram","phone"] }
            TextField { id: convContact; Layout.fillWidth:true; placeholderText: appState.rtl ? "الهاتف / الحساب الخارجي" : "Phone / external contact" }
            TextField { id: convName; Layout.fillWidth:true; placeholderText: appState.rtl ? "اسم العرض" : "Display name" }
            RowLayout {
                Layout.fillWidth:true
                Button { Layout.fillWidth:true; enabled:convContact.text.length>=2; text:appState.rtl?"إنشاء":"Create"; onClicked:{apiClient.createConversation(convLead.currentValue||"",convChannel.currentText,convContact.text,convName.text);conversationDialog.close()} }
                Button { text:appState.rtl?"إلغاء":"Cancel";onClicked:conversationDialog.close() }
            }
        }
    }

    Dialog {
        id: whatsappDialog
        modal: true; width: Math.min(560, root.width - 40); anchors.centerIn: parent
        background: Rectangle { radius:18; color:Theme.panel; border.width:1; border.color:Qt.rgba(.72,.82,.89,.34) }
        contentItem: ColumnLayout {
            spacing:8
            Text { text:"WhatsApp Business Cloud API";color:Theme.platinum;font.pixelSize:19;font.bold:true }
            TextField{id:waName;Layout.fillWidth:true;placeholderText:appState.rtl?"اسم القناة":"Channel name"}
            TextField{id:waPhoneId;Layout.fillWidth:true;placeholderText:"Phone Number ID"}
            TextField{id:waWaba;Layout.fillWidth:true;placeholderText:"WABA ID"}
            TextField{id:waBusinessPhone;Layout.fillWidth:true;placeholderText:appState.rtl?"رقم الأعمال":"Business phone"}
            TextField{id:waVersion;Layout.fillWidth:true;text:"v23.0";placeholderText:"Graph API version"}
            TextField{id:waToken;Layout.fillWidth:true;echoMode:TextInput.Password;placeholderText:"Access Token"}
            TextField{id:waSecret;Layout.fillWidth:true;echoMode:TextInput.Password;placeholderText:"App Secret"}
            CheckBox{id:waDefault;text:appState.rtl?"القناة الافتراضية":"Default channel";checked:true}
            RowLayout {
                Layout.fillWidth:true
                Button {
                    Layout.fillWidth:true
                    text:appState.rtl?"حفظ القناة":"Save Channel"
                    enabled:waName.text.length>=2&&waPhoneId.text.length>=2
                    onClicked:{
                        apiClient.createWhatsAppChannel(waName.text,waPhoneId.text,waWaba.text,waBusinessPhone.text,waVersion.text,waToken.text,waSecret.text,waDefault.checked,true)
                        whatsappDialog.close()
                    }
                }
                Button{text:appState.rtl?"إلغاء":"Cancel";onClicked:whatsappDialog.close()}
            }
        }
    }

    Dialog {
        id: aiDialog
        modal:true; width:Math.min(620,root.width-40);anchors.centerIn:parent
        background:Rectangle{radius:18;color:Theme.panel;border.width:1;border.color:Qt.rgba(.72,.82,.89,.34)}
        contentItem:ColumnLayout{
            spacing:8
            Text{text:appState.rtl?"رد مبيعات موثوق بالبيانات":"Grounded Sales Reply";color:Theme.platinum;font.pixelSize:19;font.bold:true}
            TextArea{id:aiQuestion;Layout.fillWidth:true;Layout.preferredHeight:90;placeholderText:appState.rtl?"اكتب سؤال العميل...":"Customer question...";wrapMode:TextEdit.WordWrap}
            RowLayout{
                Layout.fillWidth:true
                TextField{id:aiCity;Layout.fillWidth:true;placeholderText:appState.rtl?"المدينة":"City"}
                TextField{id:aiPrice;Layout.fillWidth:true;placeholderText:appState.rtl?"أقصى سعر":"Max price";inputMethodHints:Qt.ImhFormattedNumbersOnly}
            }
            RowLayout{
                Layout.fillWidth:true
                SpinBox{id:aiBedrooms;from:-1;to:30;value:-1;editable:true;Layout.preferredWidth:120}
                TextField{id:aiType;Layout.fillWidth:true;placeholderText:appState.rtl?"نوع الوحدة":"Unit type"}
            }
            Button{
                Layout.fillWidth:true
                text:appState.rtl?"إنشاء رد موثوق":"Prepare Grounded Reply"
                enabled:root.selectedConversation&&aiQuestion.text.length>=2&&!apiClient.busy
                onClicked:{
                    var channelId=apiClient.whatsappChannels.length?apiClient.whatsappChannels[0].id:""
                    apiClient.prepareGroundedReply(root.selectedConversation.id,aiQuestion.text,aiCity.text,Number(aiPrice.text||0),aiBedrooms.value,aiType.text,channelId)
                    aiDialog.close()
                }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent; spacing: 9

        RowLayout {
            Layout.fillWidth:true; layoutDirection:appState.rtl?Qt.RightToLeft:Qt.LeftToRight
            ColumnLayout {
                Layout.fillWidth:true
                Text{text:appState.t("inbox");color:Theme.platinum;font.family:appState.rtl?"Noto Kufi Arabic":"Segoe UI";font.pixelSize:29;font.bold:true}
                Text{text:appState.rtl?"صندوق موحد · WhatsApp · AI Sales · موافقات · تحويل بشري":"Unified inbox · WhatsApp · AI Sales · approvals · human handoff";color:Theme.muted;font.pixelSize:12}
            }
            Button{text:appState.rtl?"+ محادثة":"+ Conversation";onClicked:conversationDialog.open()}
            Button{visible:apiClient.userRole==="owner"||apiClient.userRole==="admin";text:"WhatsApp +";onClicked:whatsappDialog.open()}
            Button{text:appState.t("refresh");onClicked:apiClient.refreshWorkspace()}
        }

        GridLayout {
            Layout.fillWidth:true;Layout.fillHeight:true
            columns:root.width>1180?3:1
            columnSpacing:9;rowSpacing:9

            Rectangle {
                Layout.fillWidth:true;Layout.fillHeight:true;Layout.minimumWidth:270
                radius:14;color:Theme.panel;border.width:1;border.color:Qt.rgba(.67,.76,.83,.25)
                ColumnLayout {
                    anchors.fill:parent;anchors.margins:10;spacing:6
                    RowLayout{Layout.fillWidth:true;Text{text:appState.rtl?"المحادثات":"Conversations";color:Theme.platinum;font.pixelSize:15;font.bold:true}Item{Layout.fillWidth:true}Text{text:String(apiClient.conversations.length);color:Theme.electricCyan;font.pixelSize:10}}
                    ListView {
                        id:convList;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;spacing:5;model:apiClient.conversations
                        delegate:Rectangle {
                            required property var modelData
                            width:convList.width;height:62;radius:8
                            color:root.selectedConversation&&root.selectedConversation.id===modelData.id?"#10304A":index%2?"#071521":"#0A1B2A"
                            border.width:root.selectedConversation&&root.selectedConversation.id===modelData.id?1:0
                            border.color:Theme.electricBlue
                            RowLayout {
                                anchors.fill:parent;anchors.margins:8;layoutDirection:appState.rtl?Qt.RightToLeft:Qt.LeftToRight
                                Rectangle{width:31;height:31;radius:8;color:"#071522";border.width:1;border.color:modelData.channel==="whatsapp"?Theme.emerald:Theme.electricBlue;Text{anchors.centerIn:parent;text:modelData.channel==="whatsapp"?"W":"✉";color:parent.border.color;font.bold:true}}
                                ColumnLayout{Layout.fillWidth:true;spacing:1
                                    Text{Layout.fillWidth:true;text:modelData.display_name||modelData.external_contact||"—";color:Theme.platinum;font.pixelSize:11;font.bold:true;elide:Text.ElideRight}
                                    Text{Layout.fillWidth:true;text:(modelData.channel||"")+" · "+(modelData.status||"");color:Theme.muted;font.pixelSize:9;elide:Text.ElideRight}
                                }
                            }
                            MouseArea{anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:{root.selectedConversation=modelData;apiClient.loadMessages(modelData.id)}}
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth:true;Layout.fillHeight:true;Layout.minimumWidth:440
                radius:14;color:Theme.panel;border.width:1;border.color:Qt.rgba(.67,.76,.83,.25)
                ColumnLayout {
                    anchors.fill:parent;anchors.margins:10;spacing:6
                    RowLayout {
                        Layout.fillWidth:true;layoutDirection:appState.rtl?Qt.RightToLeft:Qt.LeftToRight
                        Text{Layout.fillWidth:true;text:root.selectedConversation?(root.selectedConversation.display_name||root.selectedConversation.external_contact): (appState.rtl?"اختر محادثة":"Select a conversation");color:Theme.platinum;font.pixelSize:15;font.bold:true;elide:Text.ElideRight}
                        Button{visible:!!root.selectedConversation;text:"AI ✦";onClicked:aiDialog.open()}
                        Button{visible:!!root.selectedConversation;text:appState.rtl?"تحويل":"Handoff";onClicked:if(root.selectedConversation)apiClient.requestHandoff(root.selectedConversation.id,appState.rtl?"يحتاج تدخل موظف":"Staff intervention requested","")}
                    }
                    ListView {
                        id:msgList;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;spacing:6;model:apiClient.messages
                        delegate:Rectangle {
                            required property var modelData
                            width:Math.min(msgList.width*.88,Math.max(220,msgText.implicitWidth+30))
                            height:Math.max(48,msgText.implicitHeight+26)
                            x:modelData.direction==="outbound"?(appState.rtl?0:msgList.width-width):(appState.rtl?msgList.width-width:0)
                            radius:10
                            color:modelData.direction==="outbound"?"#0D3047":"#101B2A"
                            border.width:1;border.color:modelData.direction==="outbound"?Qt.rgba(.2,.65,.9,.24):Qt.rgba(.6,.7,.8,.18)
                            ColumnLayout{
                                anchors.fill:parent;anchors.margins:9;spacing:2
                                Text{id:msgText;Layout.fillWidth:true;text:modelData.body||"";color:Theme.platinum;font.pixelSize:11;wrapMode:Text.WordWrap;horizontalAlignment:appState.rtl?Text.AlignRight:Text.AlignLeft}
                                Text{text:(modelData.sender||"")+" · "+(modelData.direction||"");color:Theme.muted;font.pixelSize:8}
                            }
                        }
                    }
                    RowLayout {
                        Layout.fillWidth:true
                        TextField{id:messageField;Layout.fillWidth:true;placeholderText:appState.rtl?"اكتب رسالة داخلية/يدوية...":"Write message...";onAccepted:sendBtn.clicked()}
                        Button{id:sendBtn;text:appState.rtl?"إرسال":"Send";enabled:!!root.selectedConversation&&messageField.text.length>0;onClicked:{apiClient.sendMessage(root.selectedConversation.id,"outbound",apiClient.userName,messageField.text);messageField.clear()}}
                    }
                }
            }

            Rectangle {
                Layout.fillWidth:true;Layout.fillHeight:true;Layout.minimumWidth:300
                radius:14;color:Theme.panel;border.width:1;border.color:Qt.rgba(.67,.76,.83,.25)
                ScrollView {
                    anchors.fill:parent;anchors.margins:10;clip:true
                    ColumnLayout {
                        width:parent.width;spacing:8
                        Text{text:appState.rtl?"حالة المبيعات":"Sales State";color:Theme.platinum;font.pixelSize:15;font.bold:true}
                        ComboBox{id:replyPref;Layout.fillWidth:true;model:["unset","text","voice"];currentIndex:Math.max(0,model.indexOf(apiClient.salesState.reply_preference||"unset"))}
                        ComboBox{id:stage;Layout.fillWidth:true;model:["new","asked_price","interested","explained","qualified","viewing_requested","high_intent","reservation_requested","won","lost"];currentIndex:Math.max(0,model.indexOf(apiClient.salesState.journey_stage||"new"))}
                        SpinBox{id:leadScore;Layout.fillWidth:true;from:0;to:100;value:Number(apiClient.salesState.lead_score||0)}
                        CheckBox{id:autoReply;text:appState.rtl?"رد تلقائي موثوق":"Grounded auto-reply";checked:!!apiClient.salesState.auto_reply_enabled}
                        Button{
                            Layout.fillWidth:true;text:appState.rtl?"حفظ حالة المبيعات":"Save Sales State";enabled:!!root.selectedConversation
                            onClicked:apiClient.updateSalesState(root.selectedConversation.id,replyPref.currentText,stage.currentText,leadScore.value,"",autoReply.checked)
                        }
                        Rectangle{Layout.fillWidth:true;height:1;color:Theme.borderSoft}
                        Text{text:"WhatsApp";color:Theme.emerald;font.pixelSize:14;font.bold:true}
                        Repeater{
                            model:apiClient.whatsappChannels
                            Rectangle{
                                required property var modelData
                                Layout.fillWidth:true;Layout.preferredHeight:58;radius:8;color:"#071521";border.width:1;border.color:modelData.status==="ready"?Qt.rgba(.25,.75,.52,.3):Theme.borderSoft
                                ColumnLayout{anchors.fill:parent;anchors.margins:8;spacing:1
                                    Text{Layout.fillWidth:true;text:modelData.display_name||"WhatsApp";color:Theme.platinum;font.pixelSize:10;font.bold:true;elide:Text.ElideRight}
                                    Text{Layout.fillWidth:true;text:(modelData.business_phone||"—")+" · "+(modelData.status||"draft");color:modelData.status==="ready"?Theme.emerald:Theme.gold;font.pixelSize:8;elide:Text.ElideRight}
                                }
                            }
                        }
                        Rectangle{Layout.fillWidth:true;height:1;color:Theme.borderSoft}
                        Text{text:appState.rtl?"مخرجات AI والموافقات":"AI Outbox & Approvals";color:Theme.platinum;font.pixelSize:14;font.bold:true}
                        Text{visible:apiClient.groundedReply.answer!==undefined;Layout.fillWidth:true;text:apiClient.groundedReply.answer||"";color:Theme.silver;font.pixelSize:9;wrapMode:Text.WordWrap}
                        Repeater{
                            model:apiClient.outbox.slice(0,12)
                            Rectangle{
                                required property var modelData
                                Layout.fillWidth:true;Layout.preferredHeight:modelData.status==="pending_approval"?92:66;radius:8;color:"#071521";border.width:1;border.color:modelData.status==="pending_approval"?Theme.gold:Theme.borderSoft
                                ColumnLayout{anchors.fill:parent;anchors.margins:7;spacing:3
                                    Text{Layout.fillWidth:true;text:(modelData.body||modelData.kind||"").slice(0,90);color:Theme.silver;font.pixelSize:8;elide:Text.ElideRight}
                                    RowLayout{
                                        Layout.fillWidth:true
                                        Text{text:modelData.status||"";color:modelData.status==="sent"?Theme.emerald:modelData.status==="pending_approval"?Theme.gold:Theme.muted;font.pixelSize:8;font.bold:true}
                                        Item{Layout.fillWidth:true}
                                        Button{visible:root.manager&&modelData.status==="pending_approval";text:"✓";onClicked:apiClient.approveOutbox(modelData.id)}
                                        Button{visible:root.manager&&modelData.status==="pending_approval";text:"×";onClicked:apiClient.rejectOutbox(modelData.id)}
                                        Button{visible:modelData.status==="approved";text:"↗";onClicked:apiClient.dispatchOutbox(modelData.id)}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
