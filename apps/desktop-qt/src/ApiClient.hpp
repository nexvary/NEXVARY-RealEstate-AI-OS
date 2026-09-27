#pragma once

#include <QNetworkAccessManager>
#include <QNetworkRequest>
#include <QObject>
#include <QString>
#include <QVariantList>
#include <QVariantMap>

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

signals:
    void baseUrlChanged();
    void sessionChanged();
    void busyChanged();
    void lastErrorChanged();
    void healthChanged();
    void overviewChanged();
    void leadsChanged();
    void unitsChanged();
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
    void fetchEnterpriseSummary();
    void fetchProposals();
    void fetchInvoices();
    void fetchTickets();
    void fetchReminders();

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
    QVariantMap m_enterpriseSummary;
    QVariantList m_proposals;
    QVariantList m_invoices;
    QVariantList m_tickets;
    QVariantList m_reminders;
    QVariantList m_timeline;
    QString m_timelineLeadId;
};
