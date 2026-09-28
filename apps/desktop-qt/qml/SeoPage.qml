import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Flickable {
    id: root
    contentWidth: width
    contentHeight: body.implicitHeight + 24
    clip: true
    property bool canOperate: apiClient.userRole === "owner" || apiClient.userRole === "admin" || apiClient.userRole === "sales_manager"

    function siteUrl() {
        return apiClient.seoDashboard.project && apiClient.seoDashboard.project.site_url
            ? apiClient.seoDashboard.project.site_url : ""
    }

    Dialog {
        id: projectDialog
        modal: true; width: Math.min(520, root.width - 40); anchors.centerIn: parent
        background: Rectangle { radius:18; color:Theme.panel; border.width:1; border.color:Qt.rgba(.72,.82,.89,.34) }
        contentItem: ColumnLayout {
            spacing:9
            Text{text:appState.localize(appState.language, "موقع SEO جديد", "New SEO Website");color:Theme.platinum;font.pixelSize:19;font.bold:true}
            TextField{id:projectName;Layout.fillWidth:true;placeholderText:appState.localize(appState.language, "اسم المشروع", "Project name")}
            TextField{id:siteField;Layout.fillWidth:true;placeholderText:"https://example.com"}
            Text{text:appState.localize(appState.language, "سيبقى Autopilot في وضع التخطيط الآمن بدون Live Writes.", "Autopilot remains guarded: plans only, no exposed live writes.");color:Theme.gold;font.pixelSize: 11;wrapMode:Text.WordWrap;Layout.fillWidth:true}
            RowLayout{
                Layout.fillWidth:true
                Button{Layout.fillWidth:true;enabled:projectName.text.length>=2&&siteField.text.length>=8;text:appState.localize(appState.language, "إضافة", "Add");onClicked:{apiClient.createSeoProject(projectName.text,siteField.text);projectDialog.close()}}
                Button{text:appState.localize(appState.language, "إلغاء", "Cancel");onClicked:projectDialog.close()}
            }
        }
    }

    Dialog {
        id: planDialog
        modal:true;width:Math.min(560,root.width-40);anchors.centerIn:parent
        background:Rectangle{radius:18;color:Theme.panel;border.width:1;border.color:Qt.rgba(.72,.82,.89,.34)}
        contentItem:ColumnLayout{
            spacing:9
            Text{text:appState.localize(appState.language, "خطة تغيير محكومة", "Guarded Change Plan");color:Theme.platinum;font.pixelSize:19;font.bold:true}
            TextField{id:planTarget;Layout.fillWidth:true;text:root.siteUrl();placeholderText:"https://..."}
            TextField{id:planAction;Layout.fillWidth:true;placeholderText:appState.localize(appState.language, "الإجراء مثل update_meta", "Action e.g. update_meta")}
            TextArea{id:planReason;Layout.fillWidth:true;Layout.preferredHeight:90;placeholderText:appState.localize(appState.language, "سبب التغيير", "Reason");wrapMode:TextEdit.WordWrap}
            Text{text:appState.localize(appState.language, "Dry-run فقط: لا يتم تعديل الموقع مباشرة.", "Dry-run only: this does not modify the live website.");color:Theme.gold;font.pixelSize: 11}
            RowLayout{
                Layout.fillWidth:true
                Button{Layout.fillWidth:true;enabled:root.canOperate&&planAction.text.length>0&&planReason.text.length>=3;text:appState.localize(appState.language, "إنشاء الخطة", "Create Plan");onClicked:{apiClient.planSeoChange(apiClient.selectedSeoProjectId,planTarget.text,planAction.text,planReason.text);planDialog.close()}}
                Button{text:appState.localize(appState.language, "إلغاء", "Cancel");onClicked:planDialog.close()}
            }
        }
    }

    ColumnLayout {
        id: body
        width: root.width
        spacing: 10

        RowLayout {
            Layout.fillWidth:true;layoutDirection:appState.rtl?Qt.RightToLeft:Qt.LeftToRight
            ColumnLayout {
                Layout.fillWidth:true
                Text{text:(appState.language, appState.t("seo"));color:Theme.platinum;font.family:appState.localize(appState.language, "Noto Kufi Arabic", "Segoe UI");font.pixelSize:29;font.bold:true}
                Text{text:appState.localize(appState.language, "تدقيق تقني · زحف محدود · فرص · Autopilot محكوم", "Technical audit · bounded crawl · opportunities · guarded Autopilot");color:Theme.muted;font.pixelSize:12}
            }
            Button{visible:root.canOperate;text:appState.localize(appState.language, "+ موقع", "+ Website");onClicked:projectDialog.open()}
            Button{text:(appState.language, appState.t("refresh"));onClicked:apiClient.refreshSeo()}
        }

        RowLayout {
            Layout.fillWidth:true;spacing:8;layoutDirection:appState.rtl?Qt.RightToLeft:Qt.LeftToRight
            ComboBox {
                id: projectPicker
                Layout.fillWidth:true
                model:apiClient.seoProjects
                textRole:"name";valueRole:"id"
                onActivated:apiClient.selectSeoProject(currentValue)
                Component.onCompleted: if(count>0) apiClient.selectSeoProject(currentValue)
            }
            Button{visible:root.canOperate&&apiClient.selectedSeoProjectId.length>0;text:appState.localize(appState.language, "تدقيق", "Audit");enabled:!apiClient.busy;onClicked:apiClient.runSeoAudit(apiClient.selectedSeoProjectId,"")}
            Button{visible:root.canOperate&&apiClient.selectedSeoProjectId.length>0;text:appState.localize(appState.language, "زحف", "Crawl");enabled:!apiClient.busy;onClicked:apiClient.runSeoCrawl(apiClient.selectedSeoProjectId,60,4)}
            Button{text:appState.localize(appState.language, "الفرص", "Opportunities");enabled:apiClient.selectedSeoProjectId.length>0;onClicked:apiClient.loadSeoOpportunities(apiClient.selectedSeoProjectId)}
            Button{visible:root.canOperate&&apiClient.selectedSeoProjectId.length>0;text:"Autopilot +";onClicked:planDialog.open()}
        }

        GridLayout {
            Layout.fillWidth:true;columns:4;columnSpacing:8
            Repeater {
                model:[
                    {v:apiClient.seoDashboard.latest_audit&&apiClient.seoDashboard.latest_audit.score!==undefined?apiClient.seoDashboard.latest_audit.score:"—",l:appState.localize(appState.language, "SEO Score", "SEO Score"),c:Theme.electricBlue},
                    {v:apiClient.seoDashboard.latest_audit&&apiClient.seoDashboard.latest_audit.grade?apiClient.seoDashboard.latest_audit.grade:"—",l:appState.localize(appState.language, "التقييم", "Grade"),c:Theme.emerald},
                    {v:apiClient.seoSnapshots.length,l:appState.localize(appState.language, "Snapshots", "Snapshots"),c:Theme.violet},
                    {v:apiClient.seoDashboard.planned_changes||0,l:appState.localize(appState.language, "خطط معلقة", "Planned Changes"),c:Theme.gold}
                ]
                Rectangle{
                    required property var modelData
                    Layout.fillWidth:true;Layout.preferredHeight:88;radius:12;color:Theme.panel;border.width:1;border.color:Qt.rgba(.67,.76,.83,.25)
                    RowLayout{anchors.fill:parent;anchors.margins:12;layoutDirection:appState.rtl?Qt.RightToLeft:Qt.LeftToRight
                        Rectangle{width:30;height:30;radius:8;color:"#071522";border.width:1;border.color:modelData.c;Text{anchors.centerIn:parent;text:"⌕";color:modelData.c;font.bold:true}}
                        ColumnLayout{Layout.fillWidth:true;Text{text:String(modelData.v);color:Theme.platinum;font.pixelSize:20;font.bold:true}Text{text:modelData.l;color:Theme.muted;font.pixelSize: 11}}
                    }
                }
            }
        }

        GridLayout {
            Layout.fillWidth:true;columns:root.width>1040?2:1;columnSpacing:9;rowSpacing:9

            Rectangle{
                Layout.fillWidth:true;Layout.preferredHeight:320;radius:14;color:Theme.panel;border.width:1;border.color:Qt.rgba(.67,.76,.83,.25)
                ColumnLayout{
                    anchors.fill:parent;anchors.margins:12;spacing:6
                    Text{text:appState.localize(appState.language, "فرص التحسين", "SEO Opportunities");color:Theme.platinum;font.pixelSize:16;font.bold:true}
                    Text{visible:apiClient.seoOpportunities.length===0;text:appState.localize(appState.language, "تحتاج بيانات Search Console قبل ظهور الفرص.", "Search Console data is required before opportunities can be calculated.");color:Theme.muted;font.pixelSize: 11;wrapMode:Text.WordWrap;Layout.fillWidth:true}
                    ListView{
                        id:oppList;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;spacing:5;model:apiClient.seoOpportunities
                        delegate:Rectangle{
                            required property var modelData
                            width:oppList.width;height:64;radius:8;color:index%2?"#071521":"#0A1B2A"
                            ColumnLayout{anchors.fill:parent;anchors.margins:8;spacing:2
                                Text{Layout.fillWidth:true;text:modelData.query||modelData.page||modelData.title||"Opportunity";color:Theme.platinum;font.pixelSize: 11;font.bold:true;elide:Text.ElideRight}
                                Text{Layout.fillWidth:true;text:JSON.stringify(modelData).slice(0,180);color:Theme.muted;font.pixelSize:8;elide:Text.ElideRight}
                            }
                        }
                    }
                }
            }

            Rectangle{
                Layout.fillWidth:true;Layout.preferredHeight:320;radius:14;color:Theme.panel;border.width:1;border.color:Qt.rgba(.67,.76,.83,.25)
                ColumnLayout{
                    anchors.fill:parent;anchors.margins:12;spacing:6
                    Text{text:appState.localize(appState.language, "Autopilot Plans", "Autopilot Plans");color:Theme.platinum;font.pixelSize:16;font.bold:true}
                    ListView{
                        id:planList;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;spacing:5;model:apiClient.seoPlans
                        delegate:Rectangle{
                            required property var modelData
                            width:planList.width;height:65;radius:8;color:index%2?"#071521":"#0A1B2A"
                            RowLayout{anchors.fill:parent;anchors.margins:8;layoutDirection:appState.rtl?Qt.RightToLeft:Qt.LeftToRight
                                ColumnLayout{Layout.fillWidth:true;Text{Layout.fillWidth:true;text:modelData.action||"—";color:Theme.platinum;font.pixelSize: 11;font.bold:true;elide:Text.ElideRight}Text{Layout.fillWidth:true;text:modelData.target_url||"";color:Theme.muted;font.pixelSize:8;elide:Text.ElideRight}}
                                Text{text:modelData.risk||"—";color:modelData.risk==="high"?Theme.danger:modelData.risk==="medium"?Theme.gold:Theme.emerald;font.pixelSize:8;font.bold:true}
                                Text{text:modelData.status||"planned";color:Theme.electricCyan;font.pixelSize:8}
                            }
                        }
                    }
                }
            }

            Rectangle{
                Layout.fillWidth:true;Layout.preferredHeight:245;radius:14;color:Theme.panel;border.width:1;border.color:Qt.rgba(.67,.76,.83,.25)
                ColumnLayout{
                    anchors.fill:parent;anchors.margins:12;spacing:6
                    Text{text:appState.localize(appState.language, "سجل القياسات", "Snapshot History");color:Theme.platinum;font.pixelSize:16;font.bold:true}
                    ListView{
                        id:snapList;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;spacing:4;model:apiClient.seoSnapshots
                        delegate:Rectangle{
                            required property var modelData
                            width:snapList.width;height:46;radius:7;color:index%2?"#071521":"#0A1B2A"
                            RowLayout{anchors.fill:parent;anchors.margins:7;layoutDirection:appState.rtl?Qt.RightToLeft:Qt.LeftToRight
                                Text{Layout.fillWidth:true;text:modelData.kind||"—";color:Theme.silver;font.pixelSize: 11}
                                Text{text:modelData.score===null||modelData.score===undefined?"—":String(modelData.score);color:Theme.electricBlue;font.pixelSize: 11;font.bold:true}
                                Text{text:modelData.grade||"";color:Theme.emerald;font.pixelSize: 11}
                            }
                        }
                    }
                }
            }

            Rectangle{
                Layout.fillWidth:true;Layout.preferredHeight:245;radius:14;color:Theme.panel;border.width:1;border.color:Qt.rgba(.67,.76,.83,.25)
                ColumnLayout{
                    anchors.fill:parent;anchors.margins:12;spacing:6
                    Text{text:appState.localize(appState.language, "آخر نتيجة تشغيل", "Last Operation");color:Theme.platinum;font.pixelSize:16;font.bold:true}
                    Text{
                        Layout.fillWidth:true;Layout.fillHeight:true
                        text:Object.keys(apiClient.seoLastResult).length?JSON.stringify(apiClient.seoLastResult,null,2):(appState.localize(appState.language, "لا توجد نتيجة بعد.", "No operation result yet."))
                        color:Theme.silver;font.family:"Consolas";font.pixelSize: 11;wrapMode:Text.WordWrap;elide:Text.ElideRight
                    }
                }
            }
        }

        Text{visible:apiClient.lastError.length>0;Layout.fillWidth:true;text:apiClient.lastError;color:Theme.danger;font.pixelSize: 11;wrapMode:Text.WordWrap}
    }
}
