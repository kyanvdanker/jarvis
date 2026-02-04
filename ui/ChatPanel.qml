import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: root
    color: "#101218"
    radius: 8

    function addMessage(sender, text) {
        chatModel.append({ sender: sender, text: text })
        listView.positionViewAtEnd()
    }

    ListModel { id: chatModel }

    Column {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 6

        ListView {
            id: listView
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            clip: true
            model: chatModel
            delegate: Column {
                width: parent.width
                spacing: 2

                Text {
                    text: sender + ":"
                    color: sender === "User" ? "#00c8ff" : "#fffbcc"
                    font.pixelSize: 11
                }

                Rectangle {
                    width: parent.width
                    color: sender === "User" ? "#182633" : "#1b1a10"
                    radius: 6
                    border.color: "#00c8ff"
                    border.width: sender === "User" ? 1 : 0

                    Text {
                        text: model.text
                        wrapMode: Text.Wrap
                        color: "#e6e6e6"
                        anchors.margins: 6
                        anchors.fill: parent
                        font.pixelSize: 12
                    }
                }
            }
        }
    }
}
