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

    Q_INVOKABLE void health();
    Q_INVOKABLE void login(const QString &tenantSlug, const QString &email, const QString &password);
    Q_INVOKABLE void logout();
    Q_INVOKABLE void refreshAll();

signals:
    void baseUrlChanged();
    void sessionChanged();
    void busyChanged();
    void lastErrorChanged();
    void healthChanged();
    void overviewChanged();
    void leadsChanged();
    void unitsChanged();

private:
    QNetworkRequest makeRequest(const QString &path, bool authenticated) const;
    void setBusy(bool value);
    void setError(const QString &message);
    void fetchOverview();
    void fetchLeads();
    void fetchUnits();

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
};
