import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Controls.Material

import org.electrum 1.0


Item {
    id: root

    property bool showAutoselectServer: true
    property alias address: address_tf.text
    property alias serverConnectMode: server_connect_mode_cb.currentValue

    implicitHeight: rootLayout.height

    ColumnLayout {
        id: rootLayout

        width: parent.width
        height: parent.height
        spacing: constants.paddingLarge


        RowLayout {
            Layout.fillWidth: true

            ServerConnectModeComboBox {
                id: server_connect_mode_cb
            }

            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: 1
            }

            HelpButton {
                Layout.alignment: Qt.AlignRight
                heading: qsTr('Connection mode')+':'
                helptext: Config.getTranslatedMessage('MSG_CONNECTMODE_SERVER_HELP') + '<br/><br/>' +
                    Config.getTranslatedMessage('MSG_CONNECTMODE_NODES_HELP') + '<ul>' +
                    '<li><b>' + Config.getTranslatedMessage('MSG_CONNECTMODE_AUTOCONNECT') +
                    '</b>: ' + Config.getTranslatedMessage('MSG_CONNECTMODE_AUTOCONNECT_HELP') + '</li>' +
                    '<li><b>' + Config.getTranslatedMessage('MSG_CONNECTMODE_MANUAL') +
                    '</b>: ' + Config.getTranslatedMessage('MSG_CONNECTMODE_MANUAL_HELP') + '</li>' +
                    '<li><b>' + Config.getTranslatedMessage('MSG_CONNECTMODE_ONESERVER') +
                    '</b>: ' + Config.getTranslatedMessage('MSG_CONNECTMODE_ONESERVER_HELP') + '</li>' +
                    '</ul>'
            }
        }

        RowLayout {
            Layout.fillWidth: true

            Label {
                text: qsTr("Server")
                enabled: address_tf.enabled
                Layout.fillWidth: true
            }

            ToolButton {
                icon.source: '../../../icons/delete.png'
                ToolTip.text: qsTr('Reset network data')
                ToolTip.visible: hovered
                onClicked: resetMenu.open()

                Menu {
                    id: resetMenu

                    MenuItem {
                        text: qsTr('SSL certificates')
                        onTriggered: {
                            var dialog = app.messageDialog.createObject(app, {
                                title: qsTr('Are you sure?'),
                                text: qsTr('This will remove cached SSL certificates for servers and reconnect to fetch them again.'),
                                yesno: true
                            })
                            dialog.accepted.connect(function() {
                                var removed = Network.clearPinnedServerCertificates()
                                var msg = removed < 0
                                    ? qsTr('Failed to reset SSL certificates.')
                                    : removed > 0
                                        ? qsTr('%1 certificate files were removed.').arg(removed)
                                        : qsTr('No cached certificate files were found.')
                                app.messageDialog.createObject(app, {
                                    title: qsTr('Reset SSL certificates'),
                                    text: msg
                                }).open()
                            })
                            dialog.open()
                        }
                    }

                    MenuItem {
                        text: qsTr('Known servers')
                        onTriggered: {
                            var dialog = app.messageDialog.createObject(app, {
                                title: qsTr('Are you sure?'),
                                text: qsTr('This will remove the list of known servers.'),
                                yesno: true
                            })
                            dialog.accepted.connect(function() {
                                var removed = Network.clearRecentServers()
                                var msg = removed < 0
                                    ? qsTr('Failed to reset known servers.')
                                    : removed > 0
                                        ? qsTr('%1 server(s) were removed.').arg(removed)
                                        : qsTr('No known servers were found.')
                                app.messageDialog.createObject(app, {
                                    title: qsTr('Reset known servers'),
                                    text: msg
                                }).open()
                            })
                            dialog.open()
                        }
                    }
                }
            }
        }

        TextHighlightPane {
            Layout.fillWidth: true

            TextField {
                id: address_tf
                enabled: server_connect_mode_cb.currentValue != ServerConnectModeComboBox.Mode.Autoconnect
                width: parent.width
                inputMethodHints: Qt.ImhNoPredictiveText
            }
        }

        ColumnLayout {
            Heading {
                text: qsTr('Servers')
            }

            Frame {
                background: PaneInsetBackground { baseColor: Material.dialogColor }
                clip: true
                verticalPadding: 0
                horizontalPadding: 0
                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.bottomMargin: constants.paddingLarge

                ElListView {
                    id: serversListView
                    anchors.fill: parent
                    model: Network.serverListModel
                    delegate: ServerDelegate {
                        onClicked: {
                            address_tf.text = model.name
                        }
                    }

                    section.property: 'chain'
                    section.criteria: ViewSection.FullString
                    section.delegate: RowLayout {
                        width: ListView.view.width
                        required property string section
                        Label {
                            text: section
                                ? serversListView.model.chaintips > 1
                                    ? qsTr('Connected @%1').arg(section)
                                    : qsTr('Connected')
                                : qsTr('Other known servers')
                            Layout.alignment: Qt.AlignLeft
                            Layout.topMargin: constants.paddingXSmall
                            Layout.leftMargin: constants.paddingSmall
                            font.pixelSize: constants.fontSizeMedium
                            color: Material.accentColor
                        }
                    }

                }
            }
        }
    }

    Component.onCompleted: {
        root.address = Network.server
    }
}
