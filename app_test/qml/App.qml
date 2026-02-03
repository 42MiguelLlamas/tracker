import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform as Platform
import Qt5Compat.GraphicalEffects
import QtQuick.Window
import QtQuick.Particles


ApplicationWindow {
    id: win
    width: 900
    height: 560
    visible: true
    title: "Poker Assistant"

    // Mínimo base (nunca menos que esto)
    minimumWidth: 720
    minimumHeight: 480

    Rectangle {
        id: titleBar
        height: 44
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        color: "#0b1020"

        MouseArea {
            anchors.fill: parent
            onPressed: { win.startSystemMove() }
        }

        RowLayout {
            anchors.fill: parent
            Label { text: "Poker Assistant"; color: "white"; padding: 12; Layout.fillWidth: true }

            ToolButton { text: "—"; onClicked: win.showMinimized() }
            ToolButton { text: "□"; onClicked: win.visibility = (win.visibility === Window.Maximized ? Window.Windowed : Window.Maximized) }
            ToolButton { text: "✕"; onClicked: win.close() }
        }
    }
    StackView {
        id: stack
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.top: titleBar.bottom
    }


    Component.onCompleted: {
        stack.replace(mainMenuPage)
    }

    Component {
        id: mainMenuPage
        Page {
            background: Item {
                id: bg
                anchors.fill: parent

                // ---- Base ----
                Rectangle {
                    anchors.fill: parent
                    color: "#070A14"
                }

                Rectangle {
                    anchors.fill: parent
                    gradient: Gradient {
                        GradientStop { position: 0.0; color: "#070A14" }
                        GradientStop { position: 0.5; color: "#0B1330" }
                        GradientStop { position: 1.0; color: "#070A14" }
                    }
                    opacity: 1.0
                }

                // ---- Blobs (luces) ----
                // 1) Indigo
                Rectangle {
                    id: blob1
                    width: 380; height: 380
                    radius: 190
                    color: "#4f46e5"
                    opacity: 0.22
                    x: -160; y: 60
                }
                DropShadow {
                    anchors.fill: blob1
                    source: blob1
                    radius: 64
                    samples: 64
                    color: "#804f46e5"
                    horizontalOffset: 0
                    verticalOffset: 0
                }

                // 2) Cyan
                Rectangle {
                    id: blob2
                    width: 460; height: 460
                    radius: 230
                    color: "#06b6d4"
                    opacity: 0.16
                    x: bg.width - 320
                    y: bg.height - 320
                }
                DropShadow {
                    anchors.fill: blob2
                    source: blob2
                    radius: 72
                    samples: 72
                    color: "#8006b6d4"
                    horizontalOffset: 0
                    verticalOffset: 0
                }

                // 3) Green
                Rectangle {
                    id: blob3
                    width: 300; height: 300
                    radius: 150
                    color: "#22c55e"
                    opacity: 0.10
                    x: bg.width * 0.58
                    y: 40
                }
                DropShadow {
                    anchors.fill: blob3
                    source: blob3
                    radius: 60
                    samples: 60
                    color: "#8022c55e"
                    horizontalOffset: 0
                    verticalOffset: 0
                }

                // ---- Animaciones (ida y vuelta) ----
                // blob1 x/y
                SequentialAnimation {
                    loops: Animation.Infinite; running: true
                    PropertyAnimation { target: blob1; property: "x"; from: -190; to: -110; duration: 14000; easing.type: Easing.InOutSine }
                    PropertyAnimation { target: blob1; property: "x"; from: -110; to: -190; duration: 14000; easing.type: Easing.InOutSine }
                }
                SequentialAnimation {
                    loops: Animation.Infinite; running: true
                    PropertyAnimation { target: blob1; property: "y"; from: 40; to: 110; duration: 17000; easing.type: Easing.InOutSine }
                    PropertyAnimation { target: blob1; property: "y"; from: 110; to: 40; duration: 17000; easing.type: Easing.InOutSine }
                }

                // blob2 x/y
                SequentialAnimation {
                    loops: Animation.Infinite; running: true
                    PropertyAnimation { target: blob2; property: "x"; from: bg.width - 360; to: bg.width - 280; duration: 19000; easing.type: Easing.InOutSine }
                    PropertyAnimation { target: blob2; property: "x"; from: bg.width - 280; to: bg.width - 360; duration: 19000; easing.type: Easing.InOutSine }
                }
                SequentialAnimation {
                    loops: Animation.Infinite; running: true
                    PropertyAnimation { target: blob2; property: "y"; from: bg.height - 360; to: bg.height - 290; duration: 21000; easing.type: Easing.InOutSine }
                    PropertyAnimation { target: blob2; property: "y"; from: bg.height - 290; to: bg.height - 360; duration: 21000; easing.type: Easing.InOutSine }
                }

                // blob3 x/y
                SequentialAnimation {
                    loops: Animation.Infinite; running: true
                    PropertyAnimation { target: blob3; property: "x"; from: bg.width * 0.54; to: bg.width * 0.62; duration: 16000; easing.type: Easing.InOutSine }
                    PropertyAnimation { target: blob3; property: "x"; from: bg.width * 0.62; to: bg.width * 0.54; duration: 16000; easing.type: Easing.InOutSine }
                }
                SequentialAnimation {
                    loops: Animation.Infinite; running: true
                    PropertyAnimation { target: blob3; property: "y"; from: 30; to: 90; duration: 18000; easing.type: Easing.InOutSine }
                    PropertyAnimation { target: blob3; property: "y"; from: 90; to: 30; duration: 18000; easing.type: Easing.InOutSine }
                }

                // ---- Partículas (neón sutil) ----
                ParticleSystem { id: ps }

                Emitter {
                    system: ps
                    width: bg.width
                    height: 2
                    anchors.bottom: parent.bottom
                    emitRate: 40
                    lifeSpan: 4500
                    lifeSpanVariation: 2000
                    size: 2
                    sizeVariation: 2
                    velocity: AngleDirection {
                        angle: 270
                        angleVariation: 20
                        magnitude: 25
                        magnitudeVariation: 20
                    }
                }

                ImageParticle {
                    system: ps
                    // sin imagen externa: partícula cuadrada simple
                    // Si quieres textura (brillito) luego te paso una imagen pequeña.
                    color: "#66a5b4fc"  // lila translúcido
                    colorVariation: 0.35
                    rotationVariation: 360
                    alpha: 0.0
                    entryEffect: ImageParticle.Fade
                }

                Emitter {
                    system: ps
                    width: bg.width
                    height: bg.height
                    emitRate: 18
                    lifeSpan: 6000
                    lifeSpanVariation: 2500
                    size: 1
                    sizeVariation: 2
                    velocity: AngleDirection {
                        angle: 0
                        angleVariation: 360
                        magnitude: 12
                        magnitudeVariation: 18
                    }
                }

                // ---- Vignette (oscurecer bordes) ----
                Rectangle {
                    anchors.fill: parent
                    gradient: Gradient {
                        GradientStop { position: 0.0; color: "#A0000000" }
                        GradientStop { position: 0.35; color: "#20000000" }
                        GradientStop { position: 1.0; color: "#B0000000" }
                    }
                    opacity: 0.55
                }

                // ---- Grain (ruido) sin imagen externa: pequeño dithering con rects ----
                // (ligero, para que no consuma; si quieres grain "real", mejor con una imagen noise)
                Repeater {
                    model: 80
                    Rectangle {
                        width: 2
                        height: 2
                        radius: 1
                        opacity: 0.06
                        color: "white"
                        x: Math.random() * bg.width
                        y: Math.random() * bg.height
                    }
                }
            }



            // Centro (igual que lo tienes, pero en una card)
            Item {
                anchors.fill: parent

                Rectangle {
                    width: Math.min(parent.width * 0.86, 520)
                    height: Math.min(parent.height * 0.78, 340)
                    anchors.centerIn: parent
                    radius: 18
                    color: "#111827"
                    border.width: 1
                    border.color: "#1f2937"
                    opacity: 0.96

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 12

                        Label {
                            text: "Menú principal"
                            font.pixelSize: 40
                            color: "white"
                            Layout.fillWidth: true
                            horizontalAlignment: Text.AlignHCenter
                        }

                        Button { text: "Estadísticas Individuales"; font.pixelSize: 22; Layout.fillWidth: true; onClicked: stack.push(statsPage) }
                        Button { text: "Poker Solver"; font.pixelSize: 22; Layout.fillWidth: true; onClicked: stack.push(solverPage) }
                        Button { text: "HUD de torneo"; font.pixelSize: 22; Layout.fillWidth: true; onClicked: stack.push(livePage) }
                        Button { text: "Ajustes"; font.pixelSize: 22; Layout.fillWidth: true; onClicked: stack.push(settingsPage) }
                    }
                }
            }
        }
    }


    // --------- STATS ----------
    Component {
        id: statsPage
        Page {
            // Ajusta mínimos si estás usando los minW/minH por página
            property int minW: 900
            property int minH: 560

            header: ToolBar {
                RowLayout {
                    anchors.fill: parent
                    ToolButton { text: "←"; onClicked: stack.pop() }
                    Label { text: "Estadísticas"; Layout.fillWidth: true; padding: 12 }
                }
            }

            // Estado "simulado" para ver el look en vivo
            property string liveTimestamp: ""
            property int handsRead: 0
            property int handsParsed: 0
            property real vpip: 0.0

            function refreshMockData() {
                // Fecha/hora actual
                liveTimestamp = Qt.formatDateTime(new Date(), "yyyy-MM-dd  HH:mm:ss")

                // Mock: contadores que cambian
                handsRead += Math.floor(Math.random() * 4)   // 0..3
                handsParsed += Math.floor(Math.random() * 3) // 0..2

                // Mock: VPIP fluctuando un poco
                var delta = (Math.random() - 0.5) * 2.0  // -1..+1
                vpip = Math.max(0, Math.min(100, vpip + delta))
            }

            Timer {
                interval: 5000       // 5 segundos (pon 10000 si quieres 10s)
                running: true
                repeat: true
                onTriggered: refreshMockData()
            }

            Component.onCompleted: refreshMockData()

            Rectangle {
                anchors.fill: parent
                color: "transparent"

                // Contenedor con márgenes
                Item {
                    anchors.fill: parent
                    anchors.margins: 18

                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 12

                        // Título pequeño arriba
                        RowLayout {
                            Layout.fillWidth: true
                            Label {
                                text: "Resumen"
                                font.pixelSize: 18
                                Layout.fillWidth: true
                            }
                            Label {
                                text: "Stats"
                                font.pixelSize: 12
                                opacity: 0.6
                            }
                        }

                        // Grid de cards
                        GridLayout {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            columns: 2
                            rowSpacing: 12
                            columnSpacing: 12

                            // --- Card 1: Timestamp live ---
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                radius: 16
                                color: "#111827"
                                border.width: 1
                                border.color: "#1f2937"

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 16
                                    spacing: 8

                                    Label {
                                        text: "Actualización (cada 5s)"
                                        font.pixelSize: 14
                                        opacity: 0.75
                                    }

                                    Label {
                                        text: liveTimestamp
                                        font.pixelSize: 22
                                        font.bold: true
                                        wrapMode: Text.WordWrap
                                    }

                                    Item { Layout.fillHeight: true }

                                    Label {
                                        text: "Luego aquí irá: última mano leída / mesa activa / etc."
                                        font.pixelSize: 12
                                        opacity: 0.6
                                        wrapMode: Text.WordWrap
                                    }
                                }
                            }

                            // --- Card 2: Manos leídas ---
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                radius: 16
                                color: "#111827"
                                border.width: 1
                                border.color: "#1f2937"

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 16
                                    spacing: 8

                                    Label { text: "Manos leídas"; font.pixelSize: 14; opacity: 0.75 }
                                    Label { text: handsRead.toString(); font.pixelSize: 38; font.bold: true }
                                    Item { Layout.fillHeight: true }
                                    ProgressBar {
                                        from: 0
                                        to: 200
                                        value: Math.min(200, handsRead)
                                        Layout.fillWidth: true
                                    }
                                }
                            }

                            // --- Card 3: Manos parseadas ---
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                radius: 16
                                color: "#111827"
                                border.width: 1
                                border.color: "#1f2937"

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 16
                                    spacing: 8

                                    Label { text: "Manos parseadas"; font.pixelSize: 14; opacity: 0.75 }
                                    Label { text: handsParsed.toString(); font.pixelSize: 38; font.bold: true }
                                    Item { Layout.fillHeight: true }
                                    Label {
                                        text: "Simula el estado del parser."
                                        font.pixelSize: 12
                                        opacity: 0.6
                                    }
                                }
                            }

                            // --- Card 4: VPIP mock ---
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                radius: 16
                                color: "#111827"
                                border.width: 1
                                border.color: "#1f2937"

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 16
                                    spacing: 8

                                    Label { text: "VPIP (mock)"; font.pixelSize: 14; opacity: 0.75 }
                                    Label {
                                        text: vpip.toFixed(1) + " %"
                                        font.pixelSize: 38
                                        font.bold: true
                                    }
                                    Item { Layout.fillHeight: true }
                                    ProgressBar {
                                        from: 0
                                        to: 100
                                        value: vpip
                                        Layout.fillWidth: true
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }


    // --------- SOLVER ----------
    Component {
        id: solverPage
        Page {
            header: ToolBar {
                RowLayout {
                    anchors.fill: parent
                    ToolButton { text: "←"; onClicked: stack.pop() }
                    Label { text: "Solver"; Layout.fillWidth: true; padding: 12 }
                }
            }
            Label { anchors.centerIn: parent; text: "Aquí irá el solver." }
        }
    }

    // --------- LIVE ----------
    Component {
        id: livePage
        Page {
            header: ToolBar {
                RowLayout {
                    anchors.fill: parent
                    ToolButton { text: "←"; onClicked: stack.pop() }
                    Label { text: "Asistente en vivo"; Layout.fillWidth: true; padding: 12 }
                }
            }
            Label { anchors.centerIn: parent; text: "Aquí irá el HUD/lector en vivo." }
        }
    }

    // --------- SETTINGS ----------
    Component {
        id: settingsPage
        Page {
            header: ToolBar {
                RowLayout {
                    anchors.fill: parent
                    ToolButton { text: "←"; onClicked: stack.pop() }
                    Label { text: "Ajustes"; Layout.fillWidth: true; padding: 12 }
                }
            }
            Label { anchors.centerIn: parent; text: "Aquí irán usuario/carpeta si algún día quieres cambiarlos." }
        }
    }
    Item {
        id: resizeHandles
        anchors.fill: parent
        z: 9999
        property int m: 8   // grosor de borde “clicable”

        // Borde izquierdo
        MouseArea {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: resizeHandles.m
            cursorShape: Qt.SizeHorCursor
            onPressed: win.startSystemResize(Qt.LeftEdge)
        }

        // Borde derecho
        MouseArea {
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: resizeHandles.m
            cursorShape: Qt.SizeHorCursor
            onPressed: win.startSystemResize(Qt.RightEdge)
        }

        // Borde superior (ojo: no tapes tu titleBar si quieres drag ahí)
        MouseArea {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: resizeHandles.m
            cursorShape: Qt.SizeVerCursor
            onPressed: win.startSystemResize(Qt.TopEdge)
        }

        // Borde inferior
        MouseArea {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: resizeHandles.m
            cursorShape: Qt.SizeVerCursor
            onPressed: win.startSystemResize(Qt.BottomEdge)
        }

        // Esquina superior izquierda
        MouseArea {
            anchors.left: parent.left
            anchors.top: parent.top
            width: resizeHandles.m
            height: resizeHandles.m
            cursorShape: Qt.SizeFDiagCursor
            onPressed: win.startSystemResize(Qt.TopEdge | Qt.LeftEdge)
        }

        // Esquina superior derecha
        MouseArea {
            anchors.right: parent.right
            anchors.top: parent.top
            width: resizeHandles.m
            height: resizeHandles.m
            cursorShape: Qt.SizeBDiagCursor
            onPressed: win.startSystemResize(Qt.TopEdge | Qt.RightEdge)
        }

        // Esquina inferior izquierda
        MouseArea {
            anchors.left: parent.left
            anchors.bottom: parent.bottom
            width: resizeHandles.m
            height: resizeHandles.m
            cursorShape: Qt.SizeBDiagCursor
            onPressed: win.startSystemResize(Qt.BottomEdge | Qt.LeftEdge)
        }

        // Esquina inferior derecha
        MouseArea {
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            width: resizeHandles.m
            height: resizeHandles.m
            cursorShape: Qt.SizeFDiagCursor
            onPressed: win.startSystemResize(Qt.BottomEdge | Qt.RightEdge)
        }
    }

}
