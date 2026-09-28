import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Flickable {
    id: root
    contentWidth: width; contentHeight: body.implicitHeight + 28; clip: true
    ColumnLayout {
        id: body; width: root.width; spacing: 14
        Rectangle {
            Layout.fillWidth: true; Layout.preferredHeight: 238; radius: 20
            color: Theme.panel; border.width: 2; border.color: Theme.metallicSilver; clip: true
            gradient: Gradient { GradientStop { position: 0; color: Theme.bg } GradientStop { position: .55; color: Theme.panelAlt } GradientStop { position: 1; color: Theme.shell } }
            RowLayout {
                anchors.fill: parent; anchors.margins: 26; spacing: 24; layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
                Rectangle {
                    Layout.preferredWidth: 132; Layout.preferredHeight: 132; radius: 29; color: "#030A12"; border.width: 2; border.color: Theme.metallicSilverLight
                    Image { anchors.fill: parent; anchors.margins: 10; source: "qrc:/qt/qml/Business/RealEstate/assets/property-mark.svg"; fillMode: Image.PreserveAspectFit }
                }
                ColumnLayout {
                    Layout.fillWidth: true; spacing: 8
                    Text { Layout.fillWidth: true; text: appState.localize(appState.language, "نظام إدارة الأعمال العقارية", "Real Estate Business OS"); color: Theme.platinum; font.pixelSize: 34; font.bold: true; horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft }
                    Text { Layout.fillWidth: true; text: appState.localize(appState.language, "مساحة موحّدة للمبيعات والعقارات وخدمة العملاء والمالية والنمو", "One workspace for sales, property operations, customer service, finance and growth"); color: Theme.electricCyan; font.pixelSize: 15; font.bold: true; wrapMode: Text.WordWrap; horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft }
                    Text { Layout.fillWidth: true; text: appState.localize(appState.language, "مصمم ليمنح الإدارة صورة واضحة، ويقلل العمل المتكرر، ويحافظ على رحلة العميل كاملة من أول تواصل حتى التعاقد والتحصيل وما بعد البيع.", "Designed to give management a clear view, reduce repetitive work and preserve the complete customer journey from first contact through contracting, collection and after-sales service."); color: Theme.silver; font.pixelSize: 13; wrapMode: Text.WordWrap; lineHeight: 1.25; horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft }
                }
                Rectangle { Layout.preferredWidth: 150; Layout.preferredHeight: 84; radius: 14; color: Theme.shellDeep; border.width: 1; border.color: Theme.emerald
                    Column { anchors.centerIn: parent; spacing: 5
                        Text { anchors.horizontalCenter: parent.horizontalCenter; text: appState.localize(appState.language, "الإصدار", "VERSION"); color: Theme.muted; font.pixelSize: 11 }
                        Text { anchors.horizontalCenter: parent.horizontalCenter; text: "2.2.0"; color: Theme.emerald; font.pixelSize: 20; font.bold: true }
                    }
                }
            }
        }
        GridLayout {
            Layout.fillWidth: true; columns: root.width > 1050 ? 3 : root.width > 680 ? 2 : 1; columnSpacing: 12; rowSpacing: 12
            Repeater {
                model: [
                    {icon:"◎", color:Theme.electricBlue, title:appState.localize(appState.language, "المبيعات والعملاء", "Sales & customers"), desc:appState.localize(appState.language, "عملاء محتملون، محادثات، مواعيد، عروض، تذكيرات وسجل موحّد لكل عميل.", "Leads, conversations, appointments, proposals, reminders and a unified history for every customer.")},
                    {icon:"▦", color:Theme.emerald, title:appState.localize(appState.language, "المشروعات والوحدات", "Projects & units"), desc:appState.localize(appState.language, "مخزون عقاري واضح بالحالة والسعر، مع الحجز والتحويل إلى عقد وجدولة الأقساط.", "Clear property inventory by status and price, with reservation, contract conversion and installment schedules.")},
                    {icon:"₤", color:Theme.gold, title:appState.localize(appState.language, "المالية والتحصيل", "Finance & collection"), desc:appState.localize(appState.language, "فواتير ومدفوعات ومصروفات وعمولات وسجل دقيق لحركة التحصيل.", "Invoices, payments, expenses, commissions and a precise collection trail.")},
                    {icon:"✦", color:Theme.violet, title:appState.localize(appState.language, "مساعدة ذكية", "Intelligent assistance"), desc:appState.localize(appState.language, "مساعد للمبيعات وقاعدة معرفة واقتراحات مبنية على معلومات الشركة المتاحة.", "Sales assistance, a knowledge base and suggestions grounded in available company information.")},
                    {icon:"↗", color:Theme.electricCyan, title:appState.localize(appState.language, "النمو والظهور", "Growth & visibility"), desc:appState.localize(appState.language, "متابعة الحملات والإسناد وتحسين الظهور وقياس النتائج من مساحة واحدة.", "Track campaigns, attribution, search visibility and results from one workspace.")},
                    {icon:"◇", color:Theme.silver, title:appState.localize(appState.language, "وايت ليبل حقيقي", "True white label"), desc:appState.localize(appState.language, "اسم وشعار وغلاف وروابط الشركة قابلة للتخصيص، والنسخة المحايدة لا تعرض هوية المورّد.", "Company name, logo, cover and links are customizable; the neutral copy does not display vendor identity.")}
                ]
                Rectangle {
                    required property var modelData; Layout.fillWidth: true; Layout.preferredHeight: 170; radius: 15; color: Theme.panel; border.width: 2; border.color: Theme.metallicSilverDark
                    ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 8
                        Rectangle { width: 43; height: 43; radius: 11; color: Theme.shellDeep; border.width: 1; border.color: modelData.color; Text { anchors.centerIn: parent; text: modelData.icon; color: modelData.color; font.pixelSize: 20; font.bold: true } }
                        Text { Layout.fillWidth: true; text: modelData.title; color: Theme.platinum; font.pixelSize: 16; font.bold: true; horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft }
                        Text { Layout.fillWidth: true; text: modelData.desc; color: Theme.silver; font.pixelSize: 12; wrapMode: Text.WordWrap; lineHeight: 1.25; horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft }
                    }
                }
            }
        }
        Rectangle {
            Layout.fillWidth: true; Layout.preferredHeight: 125; radius: 15; color: Theme.panelAlt; border.width: 2; border.color: Theme.metallicSilver
            RowLayout { anchors.fill: parent; anchors.margins: 18; spacing: 20; layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight
                ColumnLayout { Layout.fillWidth: true
                    Text { text: appState.localize(appState.language, "الخصوصية واستمرارية العمل", "Privacy & business continuity"); color: Theme.platinum; font.pixelSize: 17; font.bold: true }
                    Text { Layout.fillWidth: true; text: appState.localize(appState.language, "تعمل الخدمة محليًا على الجهاز، وتبقى بيانات الشركة تحت إدارتها. يُنصح بنسخ احتياطي دوري، وتحديد صلاحيات المستخدمين، ومراجعة إعدادات قنوات التواصل قبل التشغيل الفعلي.", "The service runs locally and company data remains under its administration. Regular backups, role-based access and a review of communication-channel settings are recommended before production use."); color: Theme.silver; font.pixelSize: 12; wrapMode: Text.WordWrap }
                }
                ColumnLayout {
                    Text { text: appState.localize(appState.language, "حالة الترخيص", "LICENSE STATUS"); color: Theme.muted; font.pixelSize: 11 }
                    Text { text: apiClient.licenseValid ? appState.localize(appState.language, "نشط", "ACTIVE") : appState.localize(appState.language, "غير نشط", "INACTIVE"); color: apiClient.licenseValid ? Theme.emerald : Theme.danger; font.pixelSize: 18; font.bold: true }
                    Text { text: apiClient.licenseInfo.company || "—"; color: Theme.electricCyan; font.pixelSize: 12 }
                }
            }
        }
    }
}
