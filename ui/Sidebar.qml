import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: root
    color: "#101218"
    radius: 8

    property var projects: []
    property var files: []

    function setProjects(list) {
        projects = list
        projectModel.clear()
        for (var i=0; i<projects.length; i++)
            projectModel.append({ name: projects[i] })
    }

    function setFiles(list) {
        files = list
        fileModel.clear()
        for (var i=0; i<files.length; i++)
            fileModel.append({ name: files[i] })
    }

    Column {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        Text {
            text: "Projects"
            color: "#00c8ff"
            font.pixelSize: 14
            font.bold: true
        }

        ListView {
            id: projectView
            height: 150
            clip: true
            model: ListModel { id: projectModel }
            delegate: Rectangle {
                width: parent.width
                height: 26
                color: ListView.isCurrentItem ? "#182633" : "transparent"
                radius: 4

                Text {
                    text: name
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: parent.left
                    anchors.leftMargin: 6
                    color: "#e6e6e6"
                    font.pixelSize: 12
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: projectView.currentIndex = index
                }
            }
        }

        Text {
            text: "Files"
            color: "#00c8ff"
            font.pixelSize: 14
            font.bold: true
        }

        ListView {
            id: fileView
            clip: true
            anchors.bottom: parent.bottom
            anchors.topMargin: 4
            model: ListModel { id: fileModel }
            delegate: Rectangle {
                width: parent.width
                height: 24
                color: ListView.isCurrentItem ? "#182633" : "transparent"
                radius: 4

                Text {
                    text: name
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: parent.left
                    anchors.leftMargin: 6
                    color: "#d0d0d0"
                    font.pixelSize: 11
                }
            }
        }
    }
}
