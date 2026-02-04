import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Particles 2.15

import "."

ApplicationWindow {
    id: root
    visible: true
    width: 1100
    height: 700
    color: "#05070b"
    title: "J.A.R.V.I.S"

    Rectangle {
        id: topBar
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: 40
        color: "#101218"

        Text {
            text: "J.A.R.V.I.S (Online)"
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            anchors.leftMargin: 16
            color: "#00c8ff"
            font.pixelSize: 14
            font.bold: true
        }

        Text {
            id: timeText
            anchors.verticalCenter: parent.verticalCenter
            anchors.right: parent.right
            anchors.rightMargin: 16
            color: "#cccccc"
            font.pixelSize: 12
            text: Qt.formatDateTime(new Date(), "hh:mm:ss | d MMM yyyy")

            Timer {
                interval: 1000
                running: true
                repeat: true
                onTriggered: timeText.text = Qt.formatDateTime(new Date(), "hh:mm:ss | d MMM yyyy")
            }
        }
    }

    RowLayout {
        anchors.top: topBar.bottom
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 20
        spacing: 20

        // --- Left: Arc Reactor + Chat ---
        ColumnLayout {
            spacing: 20
            Layout.fillWidth: true
            Layout.preferredWidth: 0.7 * root.width

            Ring {
                id: reactor
                Layout.preferredHeight: 360
                Layout.fillWidth: true
            }

            ChatPanel {
                id: chat
                Layout.fillWidth: true
                Layout.fillHeight: true
            }
        }

        // --- Right: Sidebar ---
        Sidebar {
            id: sidebar
            Layout.preferredWidth: 260
            Layout.fillHeight: true
        }
    }

    // ---- Connect backend signals ----
    Connections {
        target: backend
        function onMessageAdded(sender, text) {
            chat.addMessage(sender, text)
        }
        function onProjectsUpdated(projects) {
            sidebar.setProjects(projects)
        }
        function onFilesUpdated(files) {
            sidebar.setFiles(files)
        }
        function onListeningChanged(state) {
            reactor.listening = state
        }
    }
}
