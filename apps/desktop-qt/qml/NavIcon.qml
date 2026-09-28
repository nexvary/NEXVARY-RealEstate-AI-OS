import QtQuick

Canvas {
    id: root
    property string iconName: "home"
    property color accent: "#55E4FF"
    antialiasing: true

    onIconNameChanged: requestPaint()
    onAccentChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()

    onPaint: {
        var c = getContext("2d")
        c.reset()
        c.clearRect(0, 0, width, height)
        var sx = width / 24.0
        var sy = height / 24.0
        c.scale(sx, sy)
        c.strokeStyle = accent
        c.fillStyle = accent
        c.lineWidth = 1.8
        c.lineCap = "round"
        c.lineJoin = "round"

        function path(points, closePath) {
            c.beginPath()
            c.moveTo(points[0], points[1])
            for (var i = 2; i < points.length; i += 2)
                c.lineTo(points[i], points[i + 1])
            if (closePath) c.closePath()
            c.stroke()
        }
        function circle(x, y, r) {
            c.beginPath(); c.arc(x, y, r, 0, Math.PI * 2); c.stroke()
        }
        function rect(x, y, w, h) { c.strokeRect(x, y, w, h) }

        switch (iconName) {
        case "home":
            path([3,11,12,3,21,11]); path([6,10,6,21,18,21,18,10]); rect(10,15,4,6); break
        case "leads":
            circle(12,7,3.5); c.beginPath(); c.arc(12,20,7,Math.PI,Math.PI*2); c.stroke(); break
        case "inventory":
            rect(3,3,7,7); rect(14,3,7,7); rect(3,14,7,7); rect(14,14,7,7); break
        case "calendar":
            rect(3,5,18,16); path([3,10,21,10]); path([8,3,8,7]); path([16,3,16,7]); break
        case "finance":
            circle(12,12,9); path([15,8,10,8,8,10,10,12,14,12,16,14,14,17,9,17]); path([12,5,12,19]); break
        case "enterprise":
            path([4,21,4,8,12,3,20,8,20,21]); path([8,10,8,17]); path([12,8,12,17]); path([16,10,16,17]); path([2,21,22,21]); break
        case "timeline":
            path([4,18,9,13,13,15,20,7]); circle(4,18,1.5); circle(9,13,1.5); circle(13,15,1.5); circle(20,7,1.5); break
        case "inbox":
            rect(3,5,18,14); path([3,7,12,14,21,7]); break
        case "book":
            path([3,5,9,4,12,7,15,4,21,5,21,20,15,19,12,21,9,19,3,20,3,5], true); path([12,7,12,21]); break
        case "tasks":
            rect(4,4,16,16); path([7,12,10,15,17,8]); break
        case "team":
            circle(9,8,3); circle(17,9,2.5); c.beginPath(); c.arc(9,20,6,Math.PI,Math.PI*2); c.stroke(); c.beginPath(); c.arc(17,19,4,Math.PI,Math.PI*2); c.stroke(); break
        case "settings":
            circle(12,12,4); circle(12,12,8); path([12,2,12,5]); path([12,19,12,22]); path([2,12,5,12]); path([19,12,22,12]); path([5,5,7,7]); path([17,17,19,19]); path([19,5,17,7]); path([7,17,5,19]); break
        case "ai":
            path([12,2,14,9,21,12,14,15,12,22,10,15,3,12,10,9,12,2], true); break
        case "search":
            circle(10,10,6); path([14.5,14.5,21,21]); break
        case "growth":
            path([3,20,3,5]); path([3,20,21,20]); path([6,16,10,12,13,14,20,6]); path([16,6,20,6,20,10]); break
        case "automation":
            circle(5,7,2.5); circle(19,7,2.5); circle(12,18,2.5); path([7.5,7,16.5,7]); path([18,9.5,13.5,15.5]); path([10.5,15.5,6,9.5]); break
        case "about":
            circle(12,12,9); circle(12,7,0.8); path([12,11,12,18]); break
        case "company":
            path([4,21,4,8,12,3,20,8,20,21]); rect(8,11,3,3); rect(13,11,3,3); rect(10,17,4,4); break
        }
    }
}
