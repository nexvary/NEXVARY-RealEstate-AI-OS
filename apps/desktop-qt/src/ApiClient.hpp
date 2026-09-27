#pragma once

#include <QNetworkAccessManager>
#include <QNetworkRequest>
#include <QObject>
#include <QString>
#include <QVariantList>
#include <QVariantMap>
#include <QUrl>

class QJsonObject;

class ApiClient final : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QString baseUrl READ baseUrl WRITE setBaseUrl NOTIFY baseUrlChanged)
    Q_PROPERTY(QString token READ token NOTIFY sessionChanged)
    Q_PROPERTY(bool loggedIn READ loggedIn NOTIFY sessionChanged)
    Q_PROPERTY(bool busy READ busy NOTIFY busyChanged)
    Q_PROPERTY(QString lastError READ lastError NOTIFY lastErrorChanged)
    Q_PROPERTY(QString userName READ userName NOTIFY sessionChanged)
    Q_PROPERTY(QString userRole READ userRole NOTIFY sessionChanged)
    Q_PROPERTY(QString healthStatus READ healthStatus NOTIFY healthChanged)
    Q_PROPERTY(QVariantMap overview READ overview NOTIFY overviewChanged)
    Q_PROPERTY(QVariantList leads READ leads NOTIFY leadsChanged)
    Q_PROPERTY(QVariantList units READ units NOTIFY unitsChanged)
    Q_PROPERTY(QVariantList projects READ projects NOTIFY projectsChanged)
    Q_PROPERTY(QVariantList reservations READ reservations NOTIFY reservationsChanged)
    Q_PROPERTY(QVariantList contracts READ contracts NOTIFY contractsChanged)
    Q_PROPERTY(QVariantList installments READ installments NOTIFY installmentsChanged)
    Q_PROPERTY(QVariantList commissions READ commissions NOTIFY commissionsChanged)
    Q_PROPERTY(QVariantList appointments READ appointments NOTIFY appointmentsChanged)
    Q_PROPERTY(QVariantMap tenantSettings READ tenantSettings NOTIFY tenantSettingsChanged)
    Q_PROPERTY(QVariantMap enterpriseSummary READ enterpriseSummary NOTIFY enterpriseSummaryChanged)
    Q_PROPERTY(QVariantList proposals READ proposals NOTIFY proposalsChanged)
    Q_PROPERTY(QVariantList invoices READ invoices NOTIFY invoicesChanged)
    Q_PROPERTY(QVariantList tickets READ tickets NOTIFY ticketsChanged)
    Q_PROPERTY(QVariantList reminders READ reminders NOTIFY remindersChanged)
    Q_PROPERTY(QVariantList timeline READ timeline NOTIFY timelineChanged)
    Q_PROPERTY(QString timelineLeadId READ timelineLeadId NOTIFY timelineChanged)

public:
    explicit ApiClient(QObject *parent = nullptr);

    QString baseUrl() const;
    void setBaseUrl(const QString &value);
    QString token() const;
    bool loggedIn() const;
    bool busy() const;
    QString lastError() const;
    QString userName() const;
    QString userRole() const;
    QString healthStatus() const;
    QVariantMap overview() const;
    QVariantList leads() const;
    QVariantList units() const;
    QVariantList projects() const;
    QVariantList reservations() const;
    QVariantList contracts() const;
    QVariantList installments() const;
    QVariantList commissions() const;
    QVariantList appointments() const;
    QVariantMap tenantSettings() const;
    QVariantMap enterpriseSummary() const;
    QVariantList proposals() const;
    QVariantList invoices() const;
    QVariantList tickets() const;
    QVariantList reminders() const;
    QVariantList timeline() const;
    QString timelineLeadId() const;

    Q_INVOKABLE void health();
    Q_INVOKABLE void login(const QString &tenantSlug, const QString &email, const QString &password);
    Q_INVOKABLE void logout();
    Q_INVOKABLE void refreshAll();
    Q_INVOKABLE void refreshEnterprise();
    Q_INVOKABLE void loadTimeline(const QString &leadId);
    Q_INVOKABLE void createProposal(const QString &leadId, const QString &unitId, const QString &number, const QString &title, double amount, const QString &currency);
    Q_INVOKABLE void createInvoice(const QString &leadId, const QString &contractId, const QString &number, const QString &title, double amount, const QString &currency);
    Q_INVOKABLE void recordPayment(const QString &invoiceId, double amount, const QString &method, const QString &reference);
    Q_INVOKABLE void createTicket(const QString &leadId, const QString &contractId, const QString &subject, const QString &description, const QString &priority);
    Q_INVOKABLE void createReminder(const QString &leadId, const QString &entityType, const QString &entityId, const QString &title, const QString &dueAtIso);
    Q_INVOKABLE void createExpense(const QString &projectId, const QString &category, const QString &description, double amount, const QString &currency);
    Q_INVOKABLE void createLead(const QString &fullName, const QString &phone, const QString &email, const QString &source, const QString &city, double budget, int bedrooms, const QString &notes);
    Q_INVOKABLE void updateLead(const QString &leadId, const QString &status, const QString &city, double budget, int bedrooms, const QString &notes);
    Q_INVOKABLE void createProject(const QString &name, const QString &city, const QString &developer, const QString &description);
    Q_INVOKABLE void createUnit(const QString &projectId, const QString &code, const QString &unitType, int bedrooms, double areaSqm, double price, const QString &currency);
    Q_INVOKABLE void createAppointment(const QString &leadId, const QString &projectId, const QString &startsAtIso, const QString &notes);
    Q_INVOKABLE void createReservation(const QString &leadId, const QString &unitId, double reservationAmount);
    Q_INVOKABLE void cancelReservation(const QString &reservationId);
    Q_INVOKABLE void convertReservationToContract(const QString &reservationId, const QString &contractNumber);
    Q_INVOKABLE void loadInstallments(const QString &contractId);
    Q_INVOKABLE void createInstallmentSchedule(const QString &contractId, const QString &firstDueAtIso, int installmentCount, int frequencyMonths);
    Q_INVOKABLE void payInstallment(const QString &installmentId);
    Q_INVOKABLE void createCommission(const QString &contractId, const QString &brokerName, double ratePercent);
    Q_INVOKABLE void payCommission(const QString &commissionId);
    Q_INVOKABLE void updateTenantSettings(const QString &brandName, const QString &primaryColor, const QString &logoDataUrl, const QString &coverDataUrl, const QString &email, const QString &website, const QString &facebook, const QString &linkedin, const QString &youtube, const QString &xUrl, const QString &tiktok);
    Q_INVOKABLE QString imageFileToDataUrl(const QUrl &fileUrl, int maxBytes);

signals:
    void baseUrlChanged();
    void sessionChanged();
    void busyChanged();
    void lastErrorChanged();
    void healthChanged();
    void overviewChanged();
    void leadsChanged();
    void unitsChanged();
    void projectsChanged();
    void reservationsChanged();
    void contractsChanged();
    void installmentsChanged();
    void commissionsChanged();
    void appointmentsChanged();
    void tenantSettingsChanged();
    void enterpriseSummaryChanged();
    void proposalsChanged();
    void invoicesChanged();
    void ticketsChanged();
    void remindersChanged();
    void timelineChanged();

private:
    QNetworkRequest makeRequest(const QString &path, bool authenticated) const;
    void setBusy(bool value);
    void setError(const QString &message);
    void fetchOverview();
    void fetchLeads();
    void fetchUnits();
    void fetchProjects();
    void fetchReservations();
    void fetchContracts();
    void fetchCommissions();
    void fetchAppointments();
    void fetchTenantSettings();
    void fetchEnterpriseSummary();
    void fetchProposals();
    void fetchInvoices();
    void fetchTickets();
    void fetchReminders();
    void postEnterprise(const QString &path, const QJsonObject &payload);

    QNetworkAccessManager m_network;
    QString m_baseUrl;
    QString m_token;
    bool m_busy{false};
    QString m_lastError;
    QString m_userName;
    QString m_userRole;
    QString m_healthStatus{"unknown"};
    QVariantMap m_overview;
    QVariantList m_leads;
    QVariantList m_units;
    QVariantList m_projects;
    QVariantList m_reservations;
    QVariantList m_contracts;
    QVariantList m_installments;
    QVariantList m_commissions;
    QVariantList m_appointments;
    QVariantMap m_tenantSettings;
    QVariantMap m_enterpriseSummary;
    QVariantList m_proposals;
    QVariantList m_invoices;
    QVariantList m_tickets;
    QVariantList m_reminders;
    QVariantList m_timeline;
    QString m_timelineLeadId;
};
