#include "ApiClient.hpp"

#include <QByteArray>
#include <QDateTime>
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
    m_baseUrl = normalizeBaseUrl(
        QProcessEnvironment::systemEnvironment().value(
            QStringLiteral("NEXVARY_API_URL"),
            QStringLiteral("http://127.0.0.1:8000")));
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
QVariantMap ApiClient::enterpriseSummary() const { return m_enterpriseSummary; }
QVariantList ApiClient::proposals() const { return m_proposals; }
QVariantList ApiClient::invoices() const { return m_invoices; }
QVariantList ApiClient::tickets() const { return m_tickets; }
QVariantList ApiClient::reminders() const { return m_reminders; }
QVariantList ApiClient::timeline() const { return m_timeline; }
QString ApiClient::timelineLeadId() const { return m_timelineLeadId; }

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
            m_healthStatus = QJsonDocument::fromJson(body).object().value(QStringLiteral("status")).toString(QStringLiteral("ok"));
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

    const QJsonObject payload{
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

        const QJsonObject object = QJsonDocument::fromJson(body).object();
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
    m_enterpriseSummary.clear();
    m_proposals.clear();
    m_invoices.clear();
    m_tickets.clear();
    m_reminders.clear();
    m_timeline.clear();
    m_timelineLeadId.clear();
    setError(QString());
    emit sessionChanged();
    emit overviewChanged();
    emit leadsChanged();
    emit unitsChanged();
    emit enterpriseSummaryChanged();
    emit proposalsChanged();
    emit invoicesChanged();
    emit ticketsChanged();
    emit remindersChanged();
    emit timelineChanged();
}

void ApiClient::refreshAll()
{
    if (!loggedIn())
        return;
    setError(QString());
    fetchOverview();
    fetchLeads();
    fetchUnits();
    refreshEnterprise();
}

void ApiClient::refreshEnterprise()
{
    if (!loggedIn())
        return;
    fetchEnterpriseSummary();
    fetchProposals();
    fetchInvoices();
    fetchTickets();
    fetchReminders();
}

void ApiClient::loadTimeline(const QString &leadId)
{
    if (!loggedIn() || leadId.trimmed().isEmpty())
        return;

    m_timelineLeadId = leadId.trimmed();
    auto *reply = m_network.get(
        makeRequest(QStringLiteral("/api/v1/enterprise-crm/leads/") + m_timelineLeadId + QStringLiteral("/timeline"), true));

    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) {
            setError(apiErrorMessage(body, reply->errorString()));
        } else {
            m_timeline = QJsonDocument::fromJson(body).array().toVariantList();
            setError(QString());
            emit timelineChanged();
        }
        reply->deleteLater();
    });
}


void ApiClient::postEnterprise(const QString &path, const QJsonObject &payload)
{
    if (!loggedIn())
        return;

    setBusy(true);
    setError(QString());
    auto *reply = m_network.post(
        makeRequest(path, true),
        QJsonDocument(payload).toJson(QJsonDocument::Compact));

    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) {
            setError(apiErrorMessage(body, reply->errorString()));
        } else {
            setError(QString());
            refreshEnterprise();
            if (!m_timelineLeadId.isEmpty())
                loadTimeline(m_timelineLeadId);
        }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::createProposal(const QString &leadId, const QString &unitId, const QString &number, const QString &title, double amount, const QString &currency)
{
    QJsonObject payload{
        {QStringLiteral("lead_id"), leadId},
        {QStringLiteral("proposal_number"), number.trimmed()},
        {QStringLiteral("title"), title.trimmed()},
        {QStringLiteral("amount"), amount},
        {QStringLiteral("currency"), currency.trimmed().isEmpty() ? QStringLiteral("EGP") : currency.trimmed().toUpper()},
    };
    if (!unitId.trimmed().isEmpty())
        payload.insert(QStringLiteral("unit_id"), unitId.trimmed());
    postEnterprise(QStringLiteral("/api/v1/enterprise-crm/proposals"), payload);
}

void ApiClient::createInvoice(const QString &leadId, const QString &contractId, const QString &number, const QString &title, double amount, const QString &currency)
{
    QJsonObject payload{
        {QStringLiteral("lead_id"), leadId},
        {QStringLiteral("invoice_number"), number.trimmed()},
        {QStringLiteral("title"), title.trimmed()},
        {QStringLiteral("total_amount"), amount},
        {QStringLiteral("currency"), currency.trimmed().isEmpty() ? QStringLiteral("EGP") : currency.trimmed().toUpper()},
    };
    if (!contractId.trimmed().isEmpty())
        payload.insert(QStringLiteral("contract_id"), contractId.trimmed());
    postEnterprise(QStringLiteral("/api/v1/enterprise-crm/invoices"), payload);
}

void ApiClient::recordPayment(const QString &invoiceId, double amount, const QString &method, const QString &reference)
{
    const QJsonObject payload{
        {QStringLiteral("amount"), amount},
        {QStringLiteral("method"), method.trimmed().isEmpty() ? QStringLiteral("bank_transfer") : method.trimmed()},
        {QStringLiteral("reference"), reference.trimmed()},
    };
    postEnterprise(QStringLiteral("/api/v1/enterprise-crm/invoices/") + invoiceId + QStringLiteral("/payments"), payload);
}

void ApiClient::createTicket(const QString &leadId, const QString &contractId, const QString &subject, const QString &description, const QString &priority)
{
    QJsonObject payload{
        {QStringLiteral("subject"), subject.trimmed()},
        {QStringLiteral("description"), description.trimmed()},
        {QStringLiteral("priority"), priority.trimmed().isEmpty() ? QStringLiteral("normal") : priority.trimmed()},
    };
    if (!leadId.trimmed().isEmpty())
        payload.insert(QStringLiteral("lead_id"), leadId.trimmed());
    if (!contractId.trimmed().isEmpty())
        payload.insert(QStringLiteral("contract_id"), contractId.trimmed());
    postEnterprise(QStringLiteral("/api/v1/enterprise-crm/tickets"), payload);
}

void ApiClient::createReminder(const QString &leadId, const QString &entityType, const QString &entityId, const QString &title, const QString &dueAtIso)
{
    QJsonObject payload{
        {QStringLiteral("title"), title.trimmed()},
        {QStringLiteral("due_at"), dueAtIso.trimmed()},
    };
    if (!leadId.trimmed().isEmpty())
        payload.insert(QStringLiteral("lead_id"), leadId.trimmed());
    if (!entityType.trimmed().isEmpty())
        payload.insert(QStringLiteral("entity_type"), entityType.trimmed());
    if (!entityId.trimmed().isEmpty())
        payload.insert(QStringLiteral("entity_id"), entityId.trimmed());
    postEnterprise(QStringLiteral("/api/v1/enterprise-crm/reminders"), payload);
}

void ApiClient::createExpense(const QString &projectId, const QString &category, const QString &description, double amount, const QString &currency)
{
    QJsonObject payload{
        {QStringLiteral("category"), category.trimmed()},
        {QStringLiteral("description"), description.trimmed()},
        {QStringLiteral("amount"), amount},
        {QStringLiteral("currency"), currency.trimmed().isEmpty() ? QStringLiteral("EGP") : currency.trimmed().toUpper()},
        {QStringLiteral("incurred_at"), QDateTime::currentDateTimeUtc().toString(Qt::ISODate)},
    };
    if (!projectId.trimmed().isEmpty())
        payload.insert(QStringLiteral("project_id"), projectId.trimmed());
    postEnterprise(QStringLiteral("/api/v1/enterprise-crm/expenses"), payload);
}

void ApiClient::fetchOverview()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/overview"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError)
            setError(apiErrorMessage(body, reply->errorString()));
        else {
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
        if (reply->error() != QNetworkReply::NoError)
            setError(apiErrorMessage(body, reply->errorString()));
        else {
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
        if (reply->error() != QNetworkReply::NoError)
            setError(apiErrorMessage(body, reply->errorString()));
        else {
            m_units = QJsonDocument::fromJson(body).array().toVariantList();
            emit unitsChanged();
        }
        reply->deleteLater();
    });
}

void ApiClient::fetchEnterpriseSummary()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/enterprise-crm/summary"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError)
            setError(apiErrorMessage(body, reply->errorString()));
        else {
            m_enterpriseSummary = QJsonDocument::fromJson(body).object().toVariantMap();
            emit enterpriseSummaryChanged();
        }
        reply->deleteLater();
    });
}

void ApiClient::fetchProposals()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/enterprise-crm/proposals"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError)
            setError(apiErrorMessage(body, reply->errorString()));
        else {
            m_proposals = QJsonDocument::fromJson(body).array().toVariantList();
            emit proposalsChanged();
        }
        reply->deleteLater();
    });
}

void ApiClient::fetchInvoices()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/enterprise-crm/invoices"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError)
            setError(apiErrorMessage(body, reply->errorString()));
        else {
            m_invoices = QJsonDocument::fromJson(body).array().toVariantList();
            emit invoicesChanged();
        }
        reply->deleteLater();
    });
}

void ApiClient::fetchTickets()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/enterprise-crm/tickets"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError)
            setError(apiErrorMessage(body, reply->errorString()));
        else {
            m_tickets = QJsonDocument::fromJson(body).array().toVariantList();
            emit ticketsChanged();
        }
        reply->deleteLater();
    });
}

void ApiClient::fetchReminders()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/enterprise-crm/reminders?pending_only=true"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError)
            setError(apiErrorMessage(body, reply->errorString()));
        else {
            m_reminders = QJsonDocument::fromJson(body).array().toVariantList();
            emit remindersChanged();
        }
        reply->deleteLater();
    });
}
