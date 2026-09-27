import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Theme.js" as Theme

Rectangle {
    id: root
    required property string label
    required property string iconName
    required property string pageId
    required property int itemIndex
    property bool active: appState.currentPage === pageId
    property bool enabledForSession: apiClient.loggedIn || pageId === "about"

    Layout.fillWidth: true
    Layout.preferredHeight: 48
    radius: 11
    color: active ? Qt.rgba(0.10, 0.45, 0.72, 0.18) : mouse.containsMouse ? "#0B2030" : "transparent"
    border.width: active ? 1 : 0
    border.color: active ? Qt.rgba(0.35, 0.80, 1.0, 0.30) : "transparent"
    opacity: enabledForSession ? 1.0 : 0.48

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 10
        anchors.rightMargin: 10
        spacing: 10
        layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight

        Rectangle {
            Layout.preferredWidth: 30
            Layout.preferredHeight: 30
            radius: 8
            color: Qt.rgba(0.05, 0.12, 0.18, 0.92)
            border.width: 1
            border.color: Qt.rgba(0.55, 0.70, 0.80, 0.18)

            NavIcon {
                anchors.centerIn: parent
                width: 21
                height: 21
                iconName: root.iconName
                accent: Theme.accentFor(root.itemIndex)
            }
        }

        Text {
            Layout.fillWidth: true
            text: root.label
            color: root.active ? Theme.platinum : Theme.silver
            font.family: appState.rtl ? "Noto Kufi Arabic" : "Segoe UI"
            font.pixelSize: 13
            font.bold: root.active
            horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
            elide: Text.ElideRight
        }

        Text {
            visible: root.active
            text: appState.rtl ? "‹" : "›"
            color: Theme.electricCyan
            font.pixelSize: 22
        }
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        enabled: root.enabledForSession
        cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: appState.navigate(root.pageId)
    }
}
