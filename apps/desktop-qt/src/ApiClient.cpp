#include "ApiClient.hpp"

#include <QByteArray>
#include <QDateTime>
#include <QFile>
#include <QMimeDatabase>
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
QVariantList ApiClient::projects() const { return m_projects; }
QVariantList ApiClient::reservations() const { return m_reservations; }
QVariantList ApiClient::contracts() const { return m_contracts; }
QVariantList ApiClient::installments() const { return m_installments; }
QVariantList ApiClient::commissions() const { return m_commissions; }
QVariantList ApiClient::appointments() const { return m_appointments; }
QVariantMap ApiClient::tenantSettings() const { return m_tenantSettings; }
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
    m_projects.clear();
    m_reservations.clear();
    m_contracts.clear();
    m_installments.clear();
    m_commissions.clear();
    m_appointments.clear();
    m_tenantSettings.clear();
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
    emit projectsChanged();
    emit reservationsChanged();
    emit contractsChanged();
    emit installmentsChanged();
    emit commissionsChanged();
    emit appointmentsChanged();
    emit tenantSettingsChanged();
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
    fetchProjects();
    fetchReservations();
    fetchContracts();
    fetchCommissions();
    fetchAppointments();
    fetchTenantSettings();
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


void ApiClient::createLead(const QString &fullName, const QString &phone, const QString &email, const QString &source, const QString &city, double budget, int bedrooms, const QString &notes)
{
    QJsonObject payload{
        {QStringLiteral("full_name"), fullName.trimmed()},
        {QStringLiteral("phone"), phone.trimmed()},
        {QStringLiteral("source"), source.trimmed().isEmpty() ? QStringLiteral("manual") : source.trimmed()},
    };
    if (!email.trimmed().isEmpty()) payload.insert(QStringLiteral("email"), email.trimmed());
    if (!city.trimmed().isEmpty()) payload.insert(QStringLiteral("preferred_city"), city.trimmed());
    if (budget > 0) payload.insert(QStringLiteral("budget"), budget);
    if (bedrooms >= 0) payload.insert(QStringLiteral("bedrooms"), bedrooms);
    if (!notes.trimmed().isEmpty()) payload.insert(QStringLiteral("notes"), notes.trimmed());

    setBusy(true);
    auto *reply = m_network.post(makeRequest(QStringLiteral("/api/v1/leads"), true), QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { setError(QString()); fetchLeads(); fetchOverview(); }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::updateLead(const QString &leadId, const QString &status, const QString &city, double budget, int bedrooms, const QString &notes)
{
    QJsonObject payload;
    if (!status.trimmed().isEmpty()) payload.insert(QStringLiteral("status"), status.trimmed());
    if (!city.trimmed().isEmpty()) payload.insert(QStringLiteral("preferred_city"), city.trimmed());
    if (budget >= 0) payload.insert(QStringLiteral("budget"), budget);
    if (bedrooms >= 0) payload.insert(QStringLiteral("bedrooms"), bedrooms);
    if (!notes.trimmed().isEmpty()) payload.insert(QStringLiteral("notes"), notes.trimmed());

    setBusy(true);
    auto *reply = m_network.sendCustomRequest(
        makeRequest(QStringLiteral("/api/v1/leads/") + leadId, true),
        QByteArray("PATCH"),
        QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply, leadId] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else {
            setError(QString());
            fetchLeads();
            fetchOverview();
            if (m_timelineLeadId == leadId) loadTimeline(leadId);
        }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::createProject(const QString &name, const QString &city, const QString &developer, const QString &description)
{
    QJsonObject payload{
        {QStringLiteral("name"), name.trimmed()},
        {QStringLiteral("city"), city.trimmed()},
    };
    if (!developer.trimmed().isEmpty()) payload.insert(QStringLiteral("developer"), developer.trimmed());
    if (!description.trimmed().isEmpty()) payload.insert(QStringLiteral("description"), description.trimmed());

    setBusy(true);
    auto *reply = m_network.post(makeRequest(QStringLiteral("/api/v1/projects"), true), QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { setError(QString()); fetchProjects(); }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::createUnit(const QString &projectId, const QString &code, const QString &unitType, int bedrooms, double areaSqm, double price, const QString &currency)
{
    QJsonObject payload{
        {QStringLiteral("project_id"), projectId.trimmed()},
        {QStringLiteral("code"), code.trimmed()},
        {QStringLiteral("unit_type"), unitType.trimmed()},
        {QStringLiteral("area_sqm"), areaSqm},
        {QStringLiteral("price"), price},
        {QStringLiteral("currency"), currency.trimmed().isEmpty() ? QStringLiteral("EGP") : currency.trimmed().toUpper()},
    };
    if (bedrooms >= 0) payload.insert(QStringLiteral("bedrooms"), bedrooms);

    setBusy(true);
    auto *reply = m_network.post(makeRequest(QStringLiteral("/api/v1/units"), true), QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { setError(QString()); fetchUnits(); fetchOverview(); }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::createAppointment(const QString &leadId, const QString &projectId, const QString &startsAtIso, const QString &notes)
{
    QJsonObject payload{
        {QStringLiteral("lead_id"), leadId.trimmed()},
        {QStringLiteral("starts_at"), startsAtIso.trimmed()},
    };
    if (!projectId.trimmed().isEmpty()) payload.insert(QStringLiteral("project_id"), projectId.trimmed());
    if (!notes.trimmed().isEmpty()) payload.insert(QStringLiteral("notes"), notes.trimmed());

    setBusy(true);
    auto *reply = m_network.post(makeRequest(QStringLiteral("/api/v1/appointments"), true), QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply, leadId] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else {
            setError(QString());
            fetchAppointments();
            fetchOverview();
            if (!leadId.isEmpty()) loadTimeline(leadId);
        }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::createReservation(const QString &leadId, const QString &unitId, double reservationAmount)
{
    const QJsonObject payload{
        {QStringLiteral("lead_id"), leadId.trimmed()},
        {QStringLiteral("unit_id"), unitId.trimmed()},
        {QStringLiteral("reservation_amount"), reservationAmount},
    };
    setBusy(true);
    auto *reply = m_network.post(makeRequest(QStringLiteral("/api/v1/reservations"), true), QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply, leadId] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else {
            setError(QString());
            fetchReservations();
            fetchUnits();
            fetchOverview();
            if (!leadId.isEmpty()) loadTimeline(leadId);
        }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::cancelReservation(const QString &reservationId)
{
    setBusy(true);
    auto *reply = m_network.post(makeRequest(QStringLiteral("/api/v1/reservations/") + reservationId + QStringLiteral("/cancel"), true), QByteArray());
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { setError(QString()); fetchReservations(); fetchUnits(); fetchOverview(); }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::convertReservationToContract(const QString &reservationId, const QString &contractNumber)
{
    const QJsonObject payload{{QStringLiteral("contract_number"), contractNumber.trimmed()}};
    setBusy(true);
    auto *reply = m_network.post(
        makeRequest(QStringLiteral("/api/v1/contracts/from-reservation/") + reservationId, true),
        QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else {
            setError(QString());
            fetchReservations();
            fetchContracts();
            fetchUnits();
            fetchOverview();
        }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::loadInstallments(const QString &contractId)
{
    if (contractId.trimmed().isEmpty())
        return;
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/contracts/") + contractId + QStringLiteral("/installments"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else {
            m_installments = QJsonDocument::fromJson(body).array().toVariantList();
            setError(QString());
            emit installmentsChanged();
        }
        reply->deleteLater();
    });
}

void ApiClient::createInstallmentSchedule(const QString &contractId, const QString &firstDueAtIso, int installmentCount, int frequencyMonths)
{
    const QJsonObject payload{
        {QStringLiteral("first_due_at"), firstDueAtIso.trimmed()},
        {QStringLiteral("installment_count"), installmentCount},
        {QStringLiteral("frequency_months"), frequencyMonths},
    };
    setBusy(true);
    auto *reply = m_network.post(
        makeRequest(QStringLiteral("/api/v1/contracts/") + contractId + QStringLiteral("/schedule"), true),
        QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply, contractId] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { setError(QString()); loadInstallments(contractId); }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::payInstallment(const QString &installmentId)
{
    setBusy(true);
    auto *reply = m_network.post(makeRequest(QStringLiteral("/api/v1/installments/") + installmentId + QStringLiteral("/pay"), true), QByteArray());
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else {
            setError(QString());
            const QJsonObject item = QJsonDocument::fromJson(body).object();
            loadInstallments(item.value(QStringLiteral("contract_id")).toString());
        }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::createCommission(const QString &contractId, const QString &brokerName, double ratePercent)
{
    const QJsonObject payload{
        {QStringLiteral("broker_name"), brokerName.trimmed()},
        {QStringLiteral("rate_percent"), ratePercent},
    };
    setBusy(true);
    auto *reply = m_network.post(
        makeRequest(QStringLiteral("/api/v1/contracts/") + contractId + QStringLiteral("/commissions"), true),
        QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { setError(QString()); fetchCommissions(); }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::payCommission(const QString &commissionId)
{
    setBusy(true);
    auto *reply = m_network.post(makeRequest(QStringLiteral("/api/v1/commissions/") + commissionId + QStringLiteral("/pay"), true), QByteArray());
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { setError(QString()); fetchCommissions(); }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::fetchProjects()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/projects"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { m_projects = QJsonDocument::fromJson(body).array().toVariantList(); emit projectsChanged(); }
        reply->deleteLater();
    });
}

void ApiClient::fetchReservations()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/reservations"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { m_reservations = QJsonDocument::fromJson(body).array().toVariantList(); emit reservationsChanged(); }
        reply->deleteLater();
    });
}

void ApiClient::fetchContracts()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/contracts"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { m_contracts = QJsonDocument::fromJson(body).array().toVariantList(); emit contractsChanged(); }
        reply->deleteLater();
    });
}

void ApiClient::fetchCommissions()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/commissions"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { m_commissions = QJsonDocument::fromJson(body).array().toVariantList(); emit commissionsChanged(); }
        reply->deleteLater();
    });
}

void ApiClient::fetchAppointments()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/appointments"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { m_appointments = QJsonDocument::fromJson(body).array().toVariantList(); emit appointmentsChanged(); }
        reply->deleteLater();
    });
}


QString ApiClient::imageFileToDataUrl(const QUrl &fileUrl, int maxBytes)
{
    const QString path = fileUrl.isLocalFile() ? fileUrl.toLocalFile() : fileUrl.toString();
    QFile file(path);
    if (!file.open(QIODevice::ReadOnly)) {
        setError(QStringLiteral("Unable to read image file"));
        return QString();
    }
    if (maxBytes > 0 && file.size() > maxBytes) {
        setError(QStringLiteral("Image file is too large"));
        return QString();
    }

    const QByteArray bytes = file.readAll();
    QMimeDatabase db;
    const QString mime = db.mimeTypeForData(bytes).name();
    if (mime != QStringLiteral("image/png") &&
        mime != QStringLiteral("image/jpeg") &&
        mime != QStringLiteral("image/webp")) {
        setError(QStringLiteral("Only PNG, JPEG and WEBP images are supported"));
        return QString();
    }

    setError(QString());
    return QStringLiteral("data:") + mime + QStringLiteral(";base64,") + QString::fromLatin1(bytes.toBase64());
}

void ApiClient::updateTenantSettings(
    const QString &brandName,
    const QString &primaryColor,
    const QString &logoDataUrl,
    const QString &coverDataUrl,
    const QString &email,
    const QString &website,
    const QString &facebook,
    const QString &linkedin,
    const QString &youtube,
    const QString &xUrl,
    const QString &tiktok)
{
    QJsonObject payload{
        {QStringLiteral("brand_name"), brandName.trimmed()},
        {QStringLiteral("primary_color"), primaryColor.trimmed()},
        {QStringLiteral("logo_data_url"), logoDataUrl},
        {QStringLiteral("cover_data_url"), coverDataUrl},
        {QStringLiteral("contact_email"), email.trimmed()},
        {QStringLiteral("website_url"), website.trimmed()},
        {QStringLiteral("facebook_url"), facebook.trimmed()},
        {QStringLiteral("linkedin_url"), linkedin.trimmed()},
        {QStringLiteral("youtube_url"), youtube.trimmed()},
        {QStringLiteral("x_url"), xUrl.trimmed()},
        {QStringLiteral("tiktok_url"), tiktok.trimmed()},
    };

    setBusy(true);
    auto *reply = m_network.sendCustomRequest(
        makeRequest(QStringLiteral("/api/v1/tenant/settings"), true),
        QByteArray("PATCH"),
        QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) {
            setError(apiErrorMessage(body, reply->errorString()));
        } else {
            m_tenantSettings = QJsonDocument::fromJson(body).object().toVariantMap();
            setError(QString());
            emit tenantSettingsChanged();
        }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::fetchTenantSettings()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/tenant/settings"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) {
            setError(apiErrorMessage(body, reply->errorString()));
        } else {
            m_tenantSettings = QJsonDocument::fromJson(body).object().toVariantMap();
            emit tenantSettingsChanged();
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
