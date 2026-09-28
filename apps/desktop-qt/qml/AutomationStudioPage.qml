import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Theme.js" as Theme

Item {
    id: root
    property bool canEdit: apiClient.userRole === "owner" || apiClient.userRole === "admin" || apiClient.userRole === "sales_manager"
    property var selectedNode: null

    ListModel { id: draftNodes }
    ListModel { id: draftEdges }

    function syncGraph() {
        draftNodes.clear()
        draftEdges.clear()
        var nodes = apiClient.automationGraph.nodes || []
        var edges = apiClient.automationGraph.edges || []
        for (var i = 0; i < nodes.length; ++i) {
            var n = nodes[i]
            draftNodes.append({
                node_key: n.node_key,
                node_type: n.node_type,
                title: n.title,
                position_x: Number(n.position_x || 80),
                position_y: Number(n.position_y || 80)
            })
        }
        for (var j = 0; j < edges.length; ++j) {
            var e = edges[j]
            draftEdges.append({
                source_node_key: e.source_node_key,
                target_node_key: e.target_node_key,
                route: e.route || "success"
            })
        }
        selectedNode = null
    }

    function addCatalogNode(item) {
        if (!root.canEdit || apiClient.selectedAutomationWorkflowId.length === 0)
            return
        var count = draftNodes.count
        var safeType = String(item.type || "node").replace(/[^a-zA-Z0-9]/g, "_")
        var key = safeType + "_" + Date.now()
        var previousKey = count > 0 ? draftNodes.get(count - 1).node_key : ""
        draftNodes.append({
            node_key: key,
            node_type: item.type,
            title: appState.rtl ? (item.label_ar || item.type) : (item.label_en || item.type),
            position_x: 60 + (count % 3) * 235,
            position_y: 60 + Math.floor(count / 3) * 145
        })
        if (previousKey.length)
            draftEdges.append({source_node_key: previousKey, target_node_key: key, route: "success"})
    }

    function saveGraph() {
        var nodes = []
        var edges = []
        for (var i = 0; i < draftNodes.count; ++i) {
            var n = draftNodes.get(i)
            nodes.push({
                node_key:n.node_key,
                node_type:n.node_type,
                title:n.title,
                config:{},
                position_x:n.position_x,
                position_y:n.position_y
            })
        }
        for (var j = 0; j < draftEdges.count; ++j) {
            var e = draftEdges.get(j)
            edges.push({
                source_node_key:e.source_node_key,
                target_node_key:e.target_node_key,
                route:e.route
            })
        }
        apiClient.replaceAutomationGraph(apiClient.selectedAutomationWorkflowId, nodes, edges)
    }

    Connections {
        target: apiClient
        function onAutomationGraphChanged() { root.syncGraph() }
    }
    Component.onCompleted: root.syncGraph()

    Dialog {
        id: createDialog
        modal:true; width:Math.min(520,root.width-40);anchors.centerIn:parent
        background:Rectangle{radius:18;color:Theme.panel;border.width:1;border.color:Qt.rgba(.72,.82,.89,.34)}
        contentItem:ColumnLayout{
            spacing:9
            Text{text:appState.localize(appState.language, "Workflow جديد", "New Workflow");color:Theme.platinum;font.pixelSize:20;font.bold:true}
            TextField{id:wfName;Layout.fillWidth:true;placeholderText:appState.localize(appState.language, "اسم الـWorkflow", "Workflow name")}
            TextArea{id:wfDescription;Layout.fillWidth:true;Layout.preferredHeight:90;placeholderText:appState.localize(appState.language, "الوصف", "Description");wrapMode:TextEdit.WordWrap}
            RowLayout{
                Layout.fillWidth:true
                Button{Layout.fillWidth:true;enabled:wfName.text.length>=2;text:appState.localize(appState.language, "إنشاء", "Create");onClicked:{apiClient.createAutomationWorkflow(wfName.text,wfDescription.text);createDialog.close()}}
                Button{text:appState.localize(appState.language, "إلغاء", "Cancel");onClicked:createDialog.close()}
            }
        }
    }

    ColumnLayout {
        anchors.fill:parent
        spacing:9

        RowLayout {
            Layout.fillWidth:true
            layoutDirection:appState.rtl?Qt.RightToLeft:Qt.LeftToRight
            ColumnLayout{
                Layout.fillWidth:true
                Text{text:(appState.language, appState.t("automation"));color:Theme.platinum;font.family:appState.localize(appState.language, "Noto Kufi Arabic", "Segoe UI");font.pixelSize:29;font.bold:true}
                Text{text:appState.localize(appState.language, "Workflow Editor أصلي · تنفيذ داخلي آمن · اعتماد بشري", "Native workflow editor · safe internal actions · human approvals");color:Theme.muted;font.pixelSize:12}
            }
            Button{visible:root.canEdit;text:appState.localize(appState.language, "+ Workflow", "+ Workflow");onClicked:createDialog.open()}
            Button{text:(appState.language, appState.t("refresh"));onClicked:apiClient.refreshAutomation()}
        }

        Rectangle {
            Layout.fillWidth:true
            Layout.preferredHeight:58
            radius:12;color:Theme.panel;border.width:1;border.color:Qt.rgba(.67,.76,.83,.25)
            RowLayout{
                anchors.fill:parent;anchors.margins:8;spacing:7
                layoutDirection:appState.rtl?Qt.RightToLeft:Qt.LeftToRight
                ComboBox{
                    id:wfPicker;Layout.fillWidth:true
                    model:apiClient.automationWorkflows;textRole:"name";valueRole:"id"
                    onActivated:apiClient.selectAutomationWorkflow(currentValue)
                    Component.onCompleted:if(count>0)apiClient.selectAutomationWorkflow(currentValue)
                }
                Button{visible:root.canEdit&&apiClient.selectedAutomationWorkflowId.length>0;text:appState.localize(appState.language, "نسخ", "Duplicate");onClicked:apiClient.duplicateAutomationWorkflow(apiClient.selectedAutomationWorkflowId)}
                Button{visible:root.canEdit&&draftNodes.count>0;text:appState.localize(appState.language, "حفظ الرسم", "Save Graph");onClicked:root.saveGraph()}
                ComboBox{id:runLead;Layout.preferredWidth:190;model:[{id:"",full_name:appState.localize(appState.language, "تشغيل عام", "General run")}].concat(apiClient.leads);textRole:"full_name";valueRole:"id"}
                Button{visible:root.canEdit&&apiClient.selectedAutomationWorkflowId.length>0;text:"▶ Run";onClicked:apiClient.runAutomationWorkflow(apiClient.selectedAutomationWorkflowId,runLead.currentValue||"")}
            }
        }

        GridLayout {
            Layout.fillWidth:true
            Layout.fillHeight:true
            columns:3
            columnSpacing:8

            Rectangle {
                Layout.preferredWidth:275
                Layout.fillHeight:true
                radius:14;color:Theme.panel;border.width:1;border.color:Qt.rgba(.67,.76,.83,.26)
                ColumnLayout{
                    anchors.fill:parent;anchors.margins:11;spacing:7
                    Text{text:appState.localize(appState.language, "العناصر", "Node Catalog");color:Theme.platinum;font.pixelSize:16;font.bold:true}
                    Text{text:appState.localize(appState.language, "اضغط لإضافة العنصر إلى الـCanvas", "Click to add to the canvas");color:Theme.muted;font.pixelSize: 11}
                    ListView{
                        id:catalogList;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;spacing:5;model:apiClient.automationCatalog
                        delegate:Rectangle{
                            required property var modelData
                            width:catalogList.width;height:62;radius:9;color:mouse.containsMouse?"#102A3D":index%2?"#071521":"#0A1B2A"
                            border.width:1;border.color:modelData.category==="approval"?Theme.gold:modelData.category==="trigger"?Theme.emerald:modelData.category==="logic"?Theme.violet:Qt.rgba(.45,.65,.78,.22)
                            ColumnLayout{
                                anchors.fill:parent;anchors.margins:8;spacing:2
                                Text{Layout.fillWidth:true;text:appState.rtl?(modelData.label_ar||modelData.type):(modelData.label_en||modelData.type);color:Theme.platinum;font.pixelSize:11;font.bold:true;elide:Text.ElideRight}
                                Text{Layout.fillWidth:true;text:modelData.category+" · "+modelData.type;color:Theme.muted;font.pixelSize:8;elide:Text.ElideRight}
                            }
                            MouseArea{id:mouse;anchors.fill:parent;hoverEnabled:true;cursorShape:Qt.PointingHandCursor;onClicked:root.addCatalogNode(modelData)}
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth:true
                Layout.fillHeight:true
                Layout.minimumWidth:550
                radius:14;color:"#050D16";border.width:1;border.color:Qt.rgba(.67,.76,.83,.30)
                ColumnLayout{
                    anchors.fill:parent;anchors.margins:8;spacing:6
                    RowLayout{
                        Layout.fillWidth:true
                        Text{text:appState.localize(appState.language, "Canvas", "Canvas");color:Theme.platinum;font.pixelSize:16;font.bold:true}
                        Item{Layout.fillWidth:true}
                        Text{text:String(draftNodes.count)+" nodes · "+String(draftEdges.count)+" edges";color:Theme.electricCyan;font.pixelSize: 11}
                    }
                    Flickable{
                        id:canvas
                        Layout.fillWidth:true;Layout.fillHeight:true
                        contentWidth:850;contentHeight:Math.max(620,120+Math.ceil(draftNodes.count/3)*145)
                        clip:true
                        Rectangle{
                            width:canvas.contentWidth;height:canvas.contentHeight;color:"#030910"
                            Repeater{
                                model:draftNodes
                                Rectangle{
                                    required property string node_key
                                    required property string node_type
                                    required property string title
                                    required property real position_x
                                    required property real position_y
                                    x:position_x;y:position_y
                                    width:205;height:92;radius:12
                                    color:"#0B1D2C"
                                    border.width:2
                                    border.color:node_type.indexOf("approval.")===0?Theme.gold:node_type.indexOf("trigger.")===0?Theme.emerald:node_type.indexOf("condition.")===0?Theme.violet:Theme.electricBlue
                                    ColumnLayout{
                                        anchors.fill:parent;anchors.margins:10;spacing:3
                                        Text{Layout.fillWidth:true;text:title;color:Theme.platinum;font.pixelSize:12;font.bold:true;elide:Text.ElideRight}
                                        Text{Layout.fillWidth:true;text:node_type;color:Theme.muted;font.pixelSize:8;elide:Text.ElideRight}
                                        Item{Layout.fillHeight:true}
                                        Text{text:"#"+node_key.slice(-8);color:Theme.silver;font.pixelSize:8}
                                    }
                                    MouseArea{
                                        anchors.fill:parent;cursorShape:Qt.PointingHandCursor
                                        drag.target:parent;drag.minimumX:0;drag.minimumY:0;drag.maximumX:canvas.contentWidth-parent.width;drag.maximumY:canvas.contentHeight-parent.height
                                        onClicked:root.selectedNode={node_key:node_key,node_type:node_type,title:title}
                                        onReleased:{
                                            draftNodes.setProperty(index,"position_x",Math.round(parent.x))
                                            draftNodes.setProperty(index,"position_y",Math.round(parent.y))
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.preferredWidth:330
                Layout.fillHeight:true
                radius:14;color:Theme.panel;border.width:1;border.color:Qt.rgba(.67,.76,.83,.26)
                ScrollView{
                    anchors.fill:parent;anchors.margins:10;clip:true
                    ColumnLayout{
                        width:parent.width;spacing:8
                        Text{text:appState.localize(appState.language, "التشغيل والموافقات", "Runs & Approvals");color:Theme.platinum;font.pixelSize:16;font.bold:true}
                        Text{
                            visible:root.selectedNode!==null
                            Layout.fillWidth:true
                            text:root.selectedNode?((appState.localize(appState.language, "العنصر: ", "Node: "))+root.selectedNode.title):""
                            color:Theme.electricCyan;font.pixelSize: 11;wrapMode:Text.WordWrap
                        }
                        Repeater{
                            model:apiClient.automationRuns.slice(0,16)
                            Rectangle{
                                required property var modelData
                                Layout.fillWidth:true
                                Layout.preferredHeight:Math.max(70,70+((modelData.approvals||[]).length*58))
                                radius:9;color:"#071521";border.width:1
                                border.color:modelData.status==="failed"?Theme.danger:modelData.status==="waiting_approval"?Theme.gold:Theme.borderSoft
                                ColumnLayout{
                                    anchors.fill:parent;anchors.margins:8;spacing:4
                                    RowLayout{
                                        Layout.fillWidth:true
                                        Text{Layout.fillWidth:true;text:(modelData.trigger_type||"manual")+" · "+String(modelData.id||"").slice(0,8);color:Theme.platinum;font.pixelSize: 11;font.bold:true}
                                        Text{text:modelData.status||"";color:modelData.status==="succeeded"?Theme.emerald:modelData.status==="failed"?Theme.danger:Theme.gold;font.pixelSize:8;font.bold:true}
                                    }
                                    Text{visible:!!modelData.error;Layout.fillWidth:true;text:modelData.error||"";color:Theme.danger;font.pixelSize:8;wrapMode:Text.WordWrap}
                                    Repeater{
                                        model:modelData.approvals||[]
                                        Rectangle{
                                            required property var modelData
                                            Layout.fillWidth:true;Layout.preferredHeight:54;radius:7;color:"#0A1B2A";border.width:1;border.color:modelData.status==="pending"?Theme.gold:Theme.borderSoft
                                            RowLayout{
                                                anchors.fill:parent;anchors.margins:6;spacing:4
                                                Text{Layout.fillWidth:true;text:modelData.prompt||"Approval";color:Theme.silver;font.pixelSize:8;elide:Text.ElideRight}
                                                Button{visible:root.canEdit&&modelData.status==="pending";text:"✓";onClicked:apiClient.decideAutomationApproval(modelData.id,"approved","Approved from Qt Studio")}
                                                Button{visible:root.canEdit&&modelData.status==="pending";text:"×";onClicked:apiClient.decideAutomationApproval(modelData.id,"rejected","Rejected from Qt Studio")}
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

        Text{visible:apiClient.lastError.length>0;Layout.fillWidth:true;text:apiClient.lastError;color:Theme.danger;font.pixelSize: 11;wrapMode:Text.WordWrap}
    }
}
