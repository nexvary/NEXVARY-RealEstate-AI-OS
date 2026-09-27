import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Theme.js" as Theme

Dialog {
    id: root
    property string mode: "proposal"

    modal: true
    focus: true
    width: Math.min(560, parent ? parent.width - 40 : 560)
    padding: 0
    closePolicy: Popup.CloseOnEscape

    function openFor(nextMode) {
        mode = nextMode
        referenceField.text = ""
        titleField.text = ""
        descriptionField.text = ""
        amountField.text = ""
        currencyField.text = "EGP"
        dueField.text = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
        if (leadField.count > 0) leadField.currentIndex = 0
        if (invoiceField.count > 0) invoiceField.currentIndex = 0
        open()
    }

    function modeTitle() {
        if (mode === "proposal") return appState.rtl ? "عرض عقاري جديد" : "New Proposal"
        if (mode === "invoice") return appState.rtl ? "فاتورة جديدة" : "New Invoice"
        if (mode === "payment") return appState.rtl ? "تسجيل دفعة" : "Record Payment"
        if (mode === "ticket") return appState.rtl ? "تذكرة دعم جديدة" : "New Support Ticket"
        if (mode === "reminder") return appState.rtl ? "تذكير جديد" : "New Reminder"
        return appState.rtl ? "تسجيل مصروف" : "Record Expense"
    }

    background: Rectangle {
        radius: 18
        color: Theme.panel
        border.width: 1
        border.color: Qt.rgba(0.72, 0.82, 0.89, 0.34)
    }

    contentItem: ColumnLayout {
        spacing: 12

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 64
            color: "#071522"
            radius: 17
            border.width: 1
            border.color: Theme.borderSoft

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 16
                anchors.rightMargin: 16
                layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight

                Rectangle {
                    width: 34; height: 34; radius: 9
                    color: "#06111C"
                    border.width: 1
                    border.color: mode === "payment" ? Theme.emerald
                        : mode === "expense" ? Theme.gold
                        : mode === "ticket" ? Theme.violet
                        : Theme.electricBlue
                    Text {
                        anchors.centerIn: parent
                        text: mode === "payment" ? "$" : mode === "ticket" ? "!" : mode === "reminder" ? "◷" : "◆"
                        color: parent.border.color
                        font.bold: true
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: root.modeTitle()
                    color: Theme.platinum
                    font.family: appState.rtl ? "Noto Kufi Arabic" : "Segoe UI"
                    font.pixelSize: 18
                    font.bold: true
                    horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
                }

                Button {
                    text: "×"
                    flat: true
                    onClicked: root.close()
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 18
            Layout.rightMargin: 18
            spacing: 9

            ComboBox {
                id: leadField
                visible: root.mode !== "expense" && root.mode !== "payment"
                Layout.fillWidth: true
                model: apiClient.leads
                textRole: "full_name"
                valueRole: "id"
            }

            ComboBox {
                id: invoiceField
                visible: root.mode === "payment"
                Layout.fillWidth: true
                model: apiClient.invoices
                textRole: "invoice_number"
                valueRole: "id"
            }

            TextField {
                id: referenceField
                visible: root.mode === "proposal" || root.mode === "invoice" || root.mode === "payment" || root.mode === "expense"
                Layout.fillWidth: true
                placeholderText: root.mode === "proposal"
                    ? (appState.rtl ? "رقم العرض" : "Proposal number")
                    : root.mode === "invoice"
                        ? (appState.rtl ? "رقم الفاتورة" : "Invoice number")
                        : root.mode === "payment"
                            ? (appState.rtl ? "مرجع الدفع" : "Payment reference")
                            : (appState.rtl ? "تصنيف المصروف" : "Expense category")
                horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
            }

            TextField {
                id: titleField
                visible: root.mode !== "payment"
                Layout.fillWidth: true
                placeholderText: root.mode === "ticket"
                    ? (appState.rtl ? "موضوع التذكرة" : "Ticket subject")
                    : root.mode === "reminder"
                        ? (appState.rtl ? "عنوان التذكير" : "Reminder title")
                        : root.mode === "expense"
                            ? (appState.rtl ? "وصف مختصر للمصروف" : "Expense description")
                            : (appState.rtl ? "العنوان" : "Title")
                horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
            }

            TextArea {
                id: descriptionField
                visible: root.mode === "ticket"
                Layout.fillWidth: true
                Layout.preferredHeight: 90
                placeholderText: appState.rtl ? "تفاصيل التذكرة" : "Ticket details"
                wrapMode: TextEdit.WordWrap
            }

            TextField {
                id: amountField
                visible: root.mode === "proposal" || root.mode === "invoice" || root.mode === "payment" || root.mode === "expense"
                Layout.fillWidth: true
                placeholderText: appState.rtl ? "المبلغ" : "Amount"
                inputMethodHints: Qt.ImhFormattedNumbersOnly
                horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
            }

            TextField {
                id: currencyField
                visible: root.mode === "proposal" || root.mode === "invoice" || root.mode === "expense"
                Layout.fillWidth: true
                placeholderText: "EGP"
                horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
            }

            ComboBox {
                id: methodField
                visible: root.mode === "payment"
                Layout.fillWidth: true
                model: ["bank_transfer", "cash", "card", "online", "other"]
            }

            ComboBox {
                id: priorityField
                visible: root.mode === "ticket"
                Layout.fillWidth: true
                model: ["normal", "high", "urgent", "low"]
            }

            TextField {
                id: dueField
                visible: root.mode === "reminder"
                Layout.fillWidth: true
                placeholderText: "2026-09-28T10:00:00Z"
                horizontalAlignment: appState.rtl ? Text.AlignRight : Text.AlignLeft
            }

            Rectangle {
                visible: apiClient.lastError.length > 0
                Layout.fillWidth: true
                Layout.preferredHeight: errorText.implicitHeight + 18
                radius: 8
                color: Qt.rgba(0.6, 0.12, 0.18, 0.16)
                border.width: 1
                border.color: Qt.rgba(1, 0.45, 0.5, 0.24)

                Text {
                    id: errorText
                    anchors.fill: parent
                    anchors.margins: 9
                    text: apiClient.lastError
                    color: Theme.danger
                    wrapMode: Text.WordWrap
                    font.pixelSize: 10
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: 4
                spacing: 8
                layoutDirection: appState.rtl ? Qt.RightToLeft : Qt.LeftToRight

                Button {
                    Layout.fillWidth: true
                    enabled: !apiClient.busy
                    text: apiClient.busy ? "…" : (appState.rtl ? "حفظ" : "Save")
                    onClicked: {
                        var amount = Number(amountField.text || 0)
                        if (root.mode === "proposal")
                            apiClient.createProposal(leadField.currentValue || "", "", referenceField.text, titleField.text, amount, currencyField.text)
                        else if (root.mode === "invoice")
                            apiClient.createInvoice(leadField.currentValue || "", "", referenceField.text, titleField.text, amount, currencyField.text)
                        else if (root.mode === "payment")
                            apiClient.recordPayment(invoiceField.currentValue || "", amount, methodField.currentText, referenceField.text)
                        else if (root.mode === "ticket")
                            apiClient.createTicket(leadField.currentValue || "", "", titleField.text, descriptionField.text, priorityField.currentText)
                        else if (root.mode === "reminder")
                            apiClient.createReminder(leadField.currentValue || "", "lead", leadField.currentValue || "", titleField.text, dueField.text)
                        else
                            apiClient.createExpense("", referenceField.text, titleField.text, amount, currencyField.text)
                        root.close()
                    }
                }

                Button {
                    text: appState.rtl ? "إلغاء" : "Cancel"
                    onClicked: root.close()
                }
            }
        }

        Item { Layout.preferredHeight: 10 }
    }
}
