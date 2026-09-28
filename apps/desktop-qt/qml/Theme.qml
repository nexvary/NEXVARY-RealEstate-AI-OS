pragma Singleton
import QtQuick

QtObject {
    property string currentTheme: "neon"

    property color bg: "#010302"
    property color shell: "#050907"
    property color shellDeep: "#020403"
    property color panel: "#09100C"
    property color panelAlt: "#101A13"
    property color border: "#D6E0E5"
    property color borderSoft: "#718087"
    property color metallicSilverLight: "#F2F7F9"
    property color metallicSilver: "#C5D0D5"
    property color metallicSilverDark: "#7C898F"
    property color platinum: "#F7FBF8"
    property color silver: "#C5D0D5"
    property color muted: "#8FA29A"
    property color electricBlue: "#28BFFF"
    property color electricCyan: "#68F7D4"
    property color emerald: "#39FF88"
    property color violet: "#B79AFF"
    property color gold: "#FFB321"
    property color danger: "#FF6474"
    property color glow: "#A8FFE0"

    function apply(name) {
        currentTheme = name
        if (name === "blue") {
            bg = "#02060B"; shell = "#06101A"; shellDeep = "#02070D"
            panel = "#091925"; panelAlt = "#0D2333"; border = "#B9D6E5"; borderSoft = "#4E6A79"
            metallicSilverLight = "#E8F4FA"; metallicSilver = "#AFC5D0"; metallicSilverDark = "#607986"
            platinum = "#F1F8FC"; silver = "#B2C6D1"; muted = "#7892A1"
            electricBlue = "#2DBDFF"; electricCyan = "#55E4FF"; emerald = "#4AE1A0"
            violet = "#AF92FF"; gold = "#E8B95C"; danger = "#FF7281"; glow = "#75D8FF"
        } else if (name === "green") {
            bg = "#010402"; shell = "#041008"; shellDeep = "#010703"
            panel = "#07160D"; panelAlt = "#0B2113"; border = "#C2DBCC"; borderSoft = "#476A56"
            metallicSilverLight = "#ECF6F0"; metallicSilver = "#B1C8BA"; metallicSilverDark = "#60786A"
            platinum = "#F1FFF5"; silver = "#B7CCBE"; muted = "#7FA38A"
            electricBlue = "#42CFFF"; electricCyan = "#64FFD2"; emerald = "#2DFF73"
            violet = "#BFA0FF"; gold = "#EBC45B"; danger = "#FF6877"; glow = "#65FF9A"
        } else if (name === "amber") {
            bg = "#050301"; shell = "#100B04"; shellDeep = "#080501"
            panel = "#1A1207"; panelAlt = "#261A09"; border = "#E3D5BC"; borderSoft = "#796847"
            metallicSilverLight = "#F8F2E8"; metallicSilver = "#CFC3AD"; metallicSilverDark = "#84745A"
            platinum = "#FFF9EE"; silver = "#D4C7AF"; muted = "#AD9670"
            electricBlue = "#55C7FF"; electricCyan = "#75EDE2"; emerald = "#71E59C"
            violet = "#C2A1FF"; gold = "#FFB000"; danger = "#FF6C66"; glow = "#FFD06A"
        } else if (name === "silver") {
            bg = "#030506"; shell = "#0A0E10"; shellDeep = "#050708"
            panel = "#11171A"; panelAlt = "#182125"; border = "#E3EBEF"; borderSoft = "#708087"
            metallicSilverLight = "#FFFFFF"; metallicSilver = "#CCD6DB"; metallicSilverDark = "#7E8D94"
            platinum = "#F8FBFC"; silver = "#CBD5DA"; muted = "#93A2A9"
            electricBlue = "#6CCBFF"; electricCyan = "#8BEBDD"; emerald = "#69ECA4"
            violet = "#B9A5FF"; gold = "#E9BD65"; danger = "#FF7884"; glow = "#E5F6FF"
        } else if (name === "violet") {
            bg = "#030207"; shell = "#0B0714"; shellDeep = "#050309"
            panel = "#151025"; panelAlt = "#201735"; border = "#D4CAE8"; borderSoft = "#685B80"
            metallicSilverLight = "#F3EEFC"; metallicSilver = "#C7BDDA"; metallicSilverDark = "#786A91"
            platinum = "#FBF7FF"; silver = "#CFC4DF"; muted = "#9987B2"
            electricBlue = "#51BEFF"; electricCyan = "#76E8F1"; emerald = "#62E7A7"
            violet = "#B37CFF"; gold = "#EABD68"; danger = "#FF718D"; glow = "#CC9CFF"
        } else {
            currentTheme = "neon"
            bg = "#010302"; shell = "#050907"; shellDeep = "#020403"
            panel = "#09100C"; panelAlt = "#101A13"; border = "#D6E0E5"; borderSoft = "#718087"
            metallicSilverLight = "#F2F7F9"; metallicSilver = "#C5D0D5"; metallicSilverDark = "#7C898F"
            platinum = "#F7FBF8"; silver = "#C5D0D5"; muted = "#8FA29A"
            electricBlue = "#28BFFF"; electricCyan = "#68F7D4"; emerald = "#39FF88"
            violet = "#B79AFF"; gold = "#FFB321"; danger = "#FF6474"; glow = "#A8FFE0"
        }
    }

    function accentFor(index) {
        var colors = [electricBlue, emerald, gold, violet, electricCyan, metallicSilverLight]
        return colors[index % colors.length]
    }
}
