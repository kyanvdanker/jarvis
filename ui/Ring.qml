import QtQuick 2.15
import QtQuick.Particles 2.15
import Qt5Compat.GraphicalEffects

Item {
    id: root
    property bool listening: false

    anchors.horizontalCenter: parent.horizontalCenter
    height: 360
    width: 360

    Rectangle {
        id: bg
        anchors.fill: parent
        color: "transparent"

        Canvas {
            id: canvas
            anchors.fill: parent
            onPaint: {
                var ctx = getContext("2d")
                ctx.reset()
                var cx = width/2
                var cy = height/2

                var outerR = 140
                var innerR = 80

                // background glow
                var gradient = ctx.createRadialGradient(cx, cy, innerR*0.2, cx, cy, outerR*1.2)
                gradient.addColorStop(0, "rgba(0,200,255,0.6)")
                gradient.addColorStop(1, "rgba(0,200,255,0.0)")
                ctx.fillStyle = gradient
                ctx.beginPath()
                ctx.arc(cx, cy, outerR*1.2, 0, Math.PI*2)
                ctx.fill()

                // outer ring
                ctx.strokeStyle = "#00c8ff"
                ctx.lineWidth = 4
                ctx.beginPath()
                ctx.arc(cx, cy, outerR, 0, Math.PI*2)
                ctx.stroke()

                // inner ring
                ctx.strokeStyle = "#0077aa"
                ctx.lineWidth = 2
                ctx.beginPath()
                ctx.arc(cx, cy, innerR, 0, Math.PI*2)
                ctx.stroke()

                // rotating blades
                var blades = 6
                var angleStep = 2*Math.PI / blades
                ctx.save()
                ctx.translate(cx, cy)
                ctx.rotate(rotationAngle)

                for (var i=0; i<blades; i++) {
                    ctx.save()
                    ctx.rotate(i * angleStep)
                    ctx.fillStyle = "rgba(0,200,255,0.35)"
                    ctx.beginPath()
                    ctx.moveTo(innerR, -6)
                    ctx.lineTo(outerR-10, -2)
                    ctx.lineTo(outerR-10, 2)
                    ctx.lineTo(innerR, 6)
                    ctx.closePath()
                    ctx.fill()
                    ctx.restore()
                }
                ctx.restore()

                // core
                var coreGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, innerR*0.7)
                coreGrad.addColorStop(0, "rgba(255,255,255,0.9)")
                coreGrad.addColorStop(1, "rgba(0,200,255,0.0)")
                ctx.fillStyle = coreGrad
                ctx.beginPath()
                ctx.arc(cx, cy, innerR*0.7, 0, Math.PI*2)
                ctx.fill()

                // text
                ctx.fillStyle = "#00e0ff"
                ctx.font = "bold 22px 'Segoe UI'"
                ctx.textAlign = "center"
                ctx.textBaseline = "middle"
                ctx.fillText("J.A.R.V.I.S", cx, cy)
            }

            property real rotationAngle: 0

            Timer {
                interval: 16
                running: true
                repeat: true
                onTriggered: {
                    canvas.rotationAngle += root.listening ? 0.06 : 0.02
                    canvas.requestPaint()
                }
            }
        }

        // particles
        ParticleSystem {
            id: ps
        }

        Emitter {
            system: ps
            anchors.centerIn: parent
            emitRate: root.listening ? 120 : 40
            lifeSpan: 2000
            lifeSpanVariation: 800
            size: 2
            sizeVariation: 3
            velocity: AngleDirection {
                angle: 0
                angleVariation: 360
                magnitude: 40
                magnitudeVariation: 20
            }
        }

        ImageParticle {
            system: ps
            source: "qrc:/particle.png" // small soft dot, or replace with simple circle
            color: "#00c8ff"
            alpha: 0.8
            entryEffect: ImageParticle.Fade
        }
    }
}
