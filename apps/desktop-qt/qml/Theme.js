.pragma library

var bg = "#030810"
var shell = "#07111D"
var shellDeep = "#040A12"
var panel = "#0A1A29"
var panelAlt = "#0D2234"
var border = "#6F8293"
var borderSoft = "#24394B"
var platinum = "#EEF5FA"
var silver = "#A8B8C5"
var muted = "#7891A5"
var electricBlue = "#2DBDFF"
var electricCyan = "#55E4FF"
var emerald = "#59DFA9"
var violet = "#AF92FF"
var gold = "#E5BF70"
var danger = "#FF8E9A"

function accentFor(index) {
    var colors = [electricBlue, emerald, violet, gold, electricCyan, "#F19AAF"]
    return colors[index % colors.length]
}
