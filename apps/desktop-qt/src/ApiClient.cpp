#include "ApiClient.hpp"

#include <QByteArray>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QNetworkReply>
#include <QNetworkRequest>
#include <QProcessEnvironment>
#include <QUrl>

namespace {
QString normalizeBaseUrl(QString value)
{
    value = value.trimmed();
    while (value.endsWith('/'))
        value.chop(1);
    return value;
}

QString apiErrorMessage(const QByteArray &body, const QString &fallback)
{
    const auto doc = QJsonDocument::fromJson(body);
    if (doc.isObject()) {
        const auto detail = doc.object().value(QStringLiteral("detail"));
        if (detail.isString() && !detail.toString().isEmpty())
            return detail.toString();
    }
    return fallback;
}
}

ApiClient::ApiClient(QObject *parent)
    : QObject(parent)
{
    const QString configured = QProcessEnvironment::systemEnvironment().value(
        QStringLiteral("NEXVARY_API_URL"),
        QStringLiteral("http://127.0.0.1:8000"));
    m_baseUrl = normalizeBaseUrl(configured);
}

QString ApiClient::baseUrl() const { return m_baseUrl; }
QString ApiClient::token() const { return m_token; }
bool ApiClient::loggedIn() const { return !m_token.isEmpty(); }
bool ApiClient::busy() const { return m_busy; }
QString ApiClient::lastError() const { return m_lastError; }
QString ApiClient::userName() const { return m_userName; }
QString ApiClient::userRole() const { return m_userRole; }
QString ApiClient::healthStatus() const { return m_healthStatus; }
QVariantMap ApiClient::overview() const { return m_overview; }
QVariantList ApiClient::leads() const { return m_leads; }
QVariantList ApiClient::units() const { return m_units; }

void ApiClient::setBaseUrl(const QString &value)
{
    const QString normalized = normalizeBaseUrl(value);
    if (normalized.isEmpty() || normalized == m_baseUrl)
        return;
    m_baseUrl = normalized;
    emit baseUrlChanged();
}

QNetworkRequest ApiClient::makeRequest(const QString &path, bool authenticated) const
{
    QNetworkRequest request(QUrl(m_baseUrl + path));
    request.setHeader(QNetworkRequest::ContentTypeHeader, QStringLiteral("application/json"));
    request.setRawHeader("Accept", "application/json");
    if (authenticated && !m_token.isEmpty())
        request.setRawHeader("Authorization", QByteArray("Bearer ") + m_token.toUtf8());
    return request;
}

void ApiClient::setBusy(bool value)
{
    if (m_busy == value)
        return;
    m_busy = value;
    emit busyChanged();
}

void ApiClient::setError(const QString &message)
{
    if (m_lastError == message)
        return;
    m_lastError = message;
    emit lastErrorChanged();
}

void ApiClient::health()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/health"), false));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) {
            m_healthStatus = QStringLiteral("offline");
            setError(apiErrorMessage(body, reply->errorString()));
        } else {
            const auto doc = QJsonDocument::fromJson(body);
            m_healthStatus = doc.object().value(QStringLiteral("status")).toString(QStringLiteral("ok"));
            setError(QString());
        }
        emit healthChanged();
        reply->deleteLater();
    });
}

void ApiClient::login(const QString &tenantSlug, const QString &email, const QString &password)
{
    if (tenantSlug.trimmed().isEmpty() || email.trimmed().isEmpty() || password.isEmpty()) {
        setError(QStringLiteral("Missing credentials"));
        return;
    }

    setBusy(true);
    setError(QString());

    QJsonObject payload{
        {QStringLiteral("tenant_slug"), tenantSlug.trimmed()},
        {QStringLiteral("email"), email.trimmed()},
        {QStringLiteral("password"), password},
    };

    auto *reply = m_network.post(
        makeRequest(QStringLiteral("/api/v1/auth/login"), false),
        QJsonDocument(payload).toJson(QJsonDocument::Compact));

    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) {
            setError(apiErrorMessage(body, reply->errorString()));
            setBusy(false);
            reply->deleteLater();
            return;
        }

        const auto doc = QJsonDocument::fromJson(body);
        const QJsonObject object = doc.object();
        m_token = object.value(QStringLiteral("access_token")).toString();

        const QJsonObject user = object.value(QStringLiteral("user")).toObject();
        m_userName = user.value(QStringLiteral("display_name")).toString();
        m_userRole = user.value(QStringLiteral("role")).toString();

        setBusy(false);
        emit sessionChanged();
        reply->deleteLater();
        refreshAll();
    });
}

void ApiClient::logout()
{
    m_token.clear();
    m_userName.clear();
    m_userRole.clear();
    m_overview.clear();
    m_leads.clear();
    m_units.clear();
    setError(QString());
    emit sessionChanged();
    emit overviewChanged();
    emit leadsChanged();
    emit unitsChanged();
}

void ApiClient::refreshAll()
{
    if (!loggedIn())
        return;
    setError(QString());
    fetchOverview();
    fetchLeads();
    fetchUnits();
}

void ApiClient::fetchOverview()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/overview"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) {
            setError(apiErrorMessage(body, reply->errorString()));
        } else {
            m_overview = QJsonDocument::fromJson(body).object().toVariantMap();
            emit overviewChanged();
        }
        reply->deleteLater();
    });
}

void ApiClient::fetchLeads()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/leads"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) {
            setError(apiErrorMessage(body, reply->errorString()));
        } else {
            m_leads = QJsonDocument::fromJson(body).array().toVariantList();
            emit leadsChanged();
        }
        reply->deleteLater();
    });
}

void ApiClient::fetchUnits()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/units"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) {
            setError(apiErrorMessage(body, reply->errorString()));
        } else {
            m_units = QJsonDocument::fromJson(body).array().toVariantList();
            emit unitsChanged();
        }
        reply->deleteLater();
    });
}
