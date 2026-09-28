import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Theme.js" as Theme

Item {
    id: root
    property string selectedContractId: ""

    Dialog {
        id: reserveDialog
        modal: true
        width: Math.min(520, root.width - 40)
        anchors.centerIn: parent
        background: Rectangle { radius:17; color:Theme.panel; border.width:1; border.color:Qt.rgba(.7,.8,.88,.32) }
        contentItem: ColumnLayout {
            spacing:9
            Text { text:appState.localize(appState.language, "حجز وحدة", "Reserve Unit"); color:Theme.platinum; font.pixelSize:19; font.bold:true }
            ComboBox { id: reserveLead; Layout.fillWidth:true; model:apiClient.leads; textRole:"full_name"; valueRole:"id" }
            ComboBox { id: reserveUnit; Layout.fillWidth:true; model:apiClient.units.filter(function(x){return x.status === "available"}); textRole:"code"; valueRole:"id" }
            TextField { id: reserveAmount; Layout.fillWidth:true; placeholderText:appState.localize(appState.language, "قيمة الحجز", "Reservation amount"); inputMethodHints:Qt.ImhFormattedNumbersOnly }
            RowLayout {
                Layout.fillWidth:true
                Button { Layout.fillWidth:true; text:appState.localize(appState.language, "تأكيد الحجز", "Create Reservation"); enabled:reserveLead.count>0 && reserveUnit.count>0; onClicked:{apiClient.createReservation(reserveLead.currentValue||"", reserveUnit.currentValue||"", Number(reserveAmount.text||0)); reserveDialog.close()} }
                Button { text:appState.localize(appState.language, "إلغاء", "Cancel"); onClicked:reserveDialog.close() }
            }
        }
    }

    Dialog {
        id: contractDialog
        modal: true
        width: 450
        anchors.centerIn: parent
        property string reservationId: ""
        background: Rectangle { radius:17; color:Theme.panel; border.width:1; border.color:Qt.rgba(.7,.8,.88,.32) }
        contentItem: ColumnLayout {
            spacing:9
            Text { text:appState.localize(appState.language, "تحويل الحجز إلى عقد", "Convert Reservation to Contract"); color:Theme.platinum; font.pixelSize:18; font.bold:true }
            TextField { id: contractNumber; Layout.fillWidth:true; placeholderText:appState.localize(appState.language, "رقم العقد", "Contract number") }
            RowLayout {
                Layout.fillWidth:true
                Button { Layout.fillWidth:true; text:appState.localize(appState.language, "إنشاء العقد", "Create Contract"); onClicked:{apiClient.convertReservationToContract(contractDialog.reservationId, contractNumber.text); contractDialog.close()} }
                Button { text:appState.localize(appState.language, "إلغاء", "Cancel"); onClicked:contractDialog.close() }
            }
        }
    }

    Dialog {
        id: scheduleDialog
        modal: true
        width: 470
        anchors.centerIn: parent
        property string contractId: ""
        background: Rectangle { radius:17; color:Theme.panel; border.width:1; border.color:Qt.rgba(.7,.8,.88,.32) }
        contentItem: ColumnLayout {
            spacing:9
            Text { text:appState.localize(appState.language, "إنشاء جدول أقساط", "Generate Installment Schedule"); color:Theme.platinum; font.pixelSize:18; font.bold:true }
            TextField { id:firstDue; Layout.fillWidth:true; text:new Date(Date.now()+30*24*3600*1000).toISOString(); placeholderText:"2026-10-27T12:00:00Z" }
            SpinBox { id:installmentCount; Layout.fillWidth:true; from:1; to:240; value:12; editable:true }
            SpinBox { id:frequencyMonths; Layout.fillWidth:true; from:1; to:12; value:1; editable:true }
            RowLayout {
                Layout.fillWidth:true
                Button { Layout.fillWidth:true; text:appState.localize(appState.language, "إنشاء الجدول", "Generate"); onClicked:{apiClient.createInstallmentSchedule(scheduleDialog.contractId, firstDue.text, installmentCount.value, frequencyMonths.value); scheduleDialog.close()} }
                Button { text:appState.localize(appState.language, "إلغاء", "Cancel"); onClicked:scheduleDialog.close() }
            }
        }
    }

    Dialog {
        id: commissionDialog
        modal:true
        width:440
        anchors.centerIn:parent
        property string contractId:""
        background:Rectangle{radius:17;color:Theme.panel;border.width:1;border.color:Qt.rgba(.7,.8,.88,.32)}
        contentItem:ColumnLayout{
            spacing:9
            Text{text:appState.localize(appState.language, "إضافة عمولة وسيط", "Add Broker Commission");color:Theme.platinum;font.pixelSize:18;font.bold:true}
            TextField{id:brokerName;Layout.fillWidth:true;placeholderText:appState.localize(appState.language, "اسم الوسيط", "Broker name")}
            TextField{id:commissionRate;Layout.fillWidth:true;placeholderText:appState.localize(appState.language, "النسبة %", "Rate %");inputMethodHints:Qt.ImhFormattedNumbersOnly}
            RowLayout{
                Layout.fillWidth:true
                Button{Layout.fillWidth:true;text:appState.localize(appState.language, "حفظ", "Save");onClicked:{apiClient.createCommission(commissionDialog.contractId,brokerName.text,Number(commissionRate.text||0));commissionDialog.close()}}
                Button{text:appState.localize(appState.language, "إلغاء", "Cancel");onClicked:commissionDialog.close()}
            }
        }
    }

    ColumnLayout {
        anchors.fill:parent
        spacing:10

        RowLayout {
            Layout.fillWidth:true
            layoutDirection:appState.rtl?Qt.RightToLeft:Qt.LeftToRight
            ColumnLayout {
                Layout.fillWidth:true
                Text { text:(appState.language, appState.t("finance"));color:Theme.platinum;font.family:appState.localize(appState.language, "Noto Kufi Arabic", "Segoe UI");font.pixelSize:29;font.bold:true }
                Text { text:appState.localize(appState.language, "الحجوزات والعقود والأقساط والعمولات", "Reservations, contracts, installments and commissions");color:Theme.muted;font.pixelSize:12 }
            }
            Button{text:appState.localize(appState.language, "+ حجز", "+ Reservation");enabled:apiClient.leads.length>0&&apiClient.units.length>0;onClicked:reserveDialog.open()}
            Button{text:(appState.language, appState.t("refresh"));onClicked:apiClient.refreshAll()}
        }

        GridLayout {
            Layout.fillWidth:true
            columns:4
            columnSpacing:8
            Repeater {
                model:[
                    {v:apiClient.reservations.length,l:appState.localize(appState.language, "الحجوزات", "Reservations"),c:Theme.electricBlue},
                    {v:apiClient.contracts.length,l:appState.localize(appState.language, "العقود", "Contracts"),c:Theme.emerald},
                    {v:apiClient.installments.length,l:appState.localize(appState.language, "الأقساط المعروضة", "Loaded installments"),c:Theme.gold},
                    {v:apiClient.commissions.length,l:appState.localize(appState.language, "العمولات", "Commissions"),c:Theme.violet}
                ]
                Rectangle {
                    required property var modelData
                    Layout.fillWidth:true;Layout.preferredHeight:80;radius:12;color:Theme.panel;border.width:1;border.color:Qt.rgba(.66,.76,.83,.24)
                    RowLayout{anchors.fill:parent;anchors.margins:12;layoutDirection:appState.rtl?Qt.RightToLeft:Qt.LeftToRight
                        Rectangle{width:28;height:28;radius:7;color:"#071522";border.width:1;border.color:modelData.c;Text{anchors.centerIn:parent;text:"◆";color:modelData.c}}
                        ColumnLayout{Layout.fillWidth:true;Text{text:String(modelData.v);color:Theme.platinum;font.pixelSize:20;font.bold:true}Text{text:modelData.l;color:Theme.muted;font.pixelSize: 11}}
                    }
                }
            }
        }

        GridLayout {
            Layout.fillWidth:true
            Layout.fillHeight:true
            columns:root.width>1100?3:1
            columnSpacing:9
            rowSpacing:9

            Rectangle {
                Layout.fillWidth:true;Layout.fillHeight:true;radius:14;color:Theme.panel;border.width:1;border.color:Qt.rgba(.66,.76,.83,.24)
                ColumnLayout {
                    anchors.fill:parent;anchors.margins:12;spacing:6
                    Text{text:appState.localize(appState.language, "الحجوزات", "Reservations");color:Theme.platinum;font.pixelSize:16;font.bold:true}
                    ListView {
                        id:reservationList;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;spacing:5;model:apiClient.reservations
                        delegate:Rectangle{
                            required property var modelData;width:reservationList.width;height:66;radius:8;color:index%2?"#071521":"#0A1B2A"
                            ColumnLayout{anchors.fill:parent;anchors.margins:8;spacing:2
                                RowLayout{Layout.fillWidth:true;layoutDirection:appState.rtl?Qt.RightToLeft:Qt.LeftToRight
                                    Text{Layout.fillWidth:true;text:(modelData.unit_id||"").slice(0,8)+" · "+(modelData.status||"");color:Theme.platinum;font.pixelSize: 11;font.bold:true}
                                    Text{text:String(modelData.reservation_amount||0)+" EGP";color:Theme.gold;font.pixelSize: 11}
                                }
                                RowLayout{Layout.fillWidth:true;layoutDirection:appState.rtl?Qt.RightToLeft:Qt.LeftToRight
                                    Button{visible:modelData.status==="active";text:appState.localize(appState.language, "عقد", "Contract");onClicked:{contractDialog.reservationId=modelData.id;contractDialog.open()}}
                                    Button{visible:modelData.status==="active";text:appState.localize(appState.language, "إلغاء", "Cancel");onClicked:apiClient.cancelReservation(modelData.id)}
                                    Item{Layout.fillWidth:true}
                                }
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth:true;Layout.fillHeight:true;radius:14;color:Theme.panel;border.width:1;border.color:Qt.rgba(.66,.76,.83,.24)
                ColumnLayout {
                    anchors.fill:parent;anchors.margins:12;spacing:6
                    Text{text:appState.localize(appState.language, "العقود", "Contracts");color:Theme.platinum;font.pixelSize:16;font.bold:true}
                    ListView {
                        id:contractList;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;spacing:5;model:apiClient.contracts
                        delegate:Rectangle{
                            required property var modelData;width:contractList.width;height:78;radius:8;color:index%2?"#071521":"#0A1B2A"
                            ColumnLayout{anchors.fill:parent;anchors.margins:8;spacing:2
                                RowLayout{Layout.fillWidth:true;layoutDirection:appState.rtl?Qt.RightToLeft:Qt.LeftToRight
                                    Text{Layout.fillWidth:true;text:modelData.contract_number||"—";color:Theme.platinum;font.pixelSize:11;font.bold:true}
                                    Text{text:Number(modelData.total_price||0).toLocaleString(Qt.locale("en_US"),"f",0)+" "+(modelData.currency||"");color:Theme.emerald;font.pixelSize: 11}
                                }
                                RowLayout{Layout.fillWidth:true;layoutDirection:appState.rtl?Qt.RightToLeft:Qt.LeftToRight
                                    Button{text:appState.localize(appState.language, "الأقساط", "Installments");onClicked:{root.selectedContractId=modelData.id;apiClient.loadInstallments(modelData.id)}}
                                    Button{text:appState.localize(appState.language, "جدول", "Schedule");onClicked:{scheduleDialog.contractId=modelData.id;scheduleDialog.open()}}
                                    Button{text:appState.localize(appState.language, "عمولة", "Commission");onClicked:{commissionDialog.contractId=modelData.id;commissionDialog.open()}}
                                    Item{Layout.fillWidth:true}
                                }
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth:true;Layout.fillHeight:true;radius:14;color:Theme.panel;border.width:1;border.color:Qt.rgba(.66,.76,.83,.24)
                ColumnLayout {
                    anchors.fill:parent;anchors.margins:12;spacing:6
                    Text{text:appState.localize(appState.language, "الأقساط والعمولات", "Installments & Commissions");color:Theme.platinum;font.pixelSize:16;font.bold:true}
                    ListView {
                        id:installmentList;Layout.fillWidth:true;Layout.preferredHeight:Math.max(140,parent.height*.55);clip:true;spacing:4;model:apiClient.installments
                        delegate:Rectangle{
                            required property var modelData;width:installmentList.width;height:48;radius:7;color:index%2?"#071521":"#0A1B2A"
                            RowLayout{anchors.fill:parent;anchors.margins:7;layoutDirection:appState.rtl?Qt.RightToLeft:Qt.LeftToRight
                                Text{text:"#"+String(modelData.sequence||"");color:Theme.silver;font.pixelSize: 11}
                                Text{Layout.fillWidth:true;text:Number(modelData.amount||0).toLocaleString(Qt.locale("en_US"),"f",0);color:Theme.platinum;font.pixelSize: 11}
                                Text{text:modelData.status||"";color:modelData.status==="paid"?Theme.emerald:Theme.gold;font.pixelSize: 11}
                                Button{visible:modelData.status==="due";text:appState.localize(appState.language, "سداد", "Pay");onClicked:apiClient.payInstallment(modelData.id)}
                            }
                        }
                    }
                    Rectangle{Layout.fillWidth:true;height:1;color:Theme.borderSoft}
                    ListView {
                        id:commissionList;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;spacing:4;model:apiClient.commissions
                        delegate:Rectangle{
                            required property var modelData;width:commissionList.width;height:48;radius:7;color:index%2?"#071521":"#0A1B2A"
                            RowLayout{anchors.fill:parent;anchors.margins:7;layoutDirection:appState.rtl?Qt.RightToLeft:Qt.LeftToRight
                                Text{Layout.fillWidth:true;text:(modelData.broker_name||"—")+" · "+String(modelData.rate_percent||0)+"%";color:Theme.platinum;font.pixelSize: 11;elide:Text.ElideRight}
                                Text{text:modelData.status||"";color:modelData.status==="paid"?Theme.emerald:Theme.violet;font.pixelSize: 11}
                                Button{visible:modelData.status==="pending";text:appState.localize(appState.language, "سداد", "Pay");onClicked:apiClient.payCommission(modelData.id)}
                            }
                        }
                    }
                }
            }
        }
    }
}
