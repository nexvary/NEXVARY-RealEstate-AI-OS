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
#include <QStringList>
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

    m_healthTimer.setInterval(2500);
    m_healthTimer.setSingleShot(false);
    connect(&m_healthTimer, &QTimer::timeout, this, &ApiClient::health);
    m_healthTimer.start();
}

QString ApiClient::baseUrl() const { return m_baseUrl; }
QString ApiClient::token() const { return m_token; }
bool ApiClient::loggedIn() const { return !m_token.isEmpty(); }
bool ApiClient::busy() const { return m_busy; }
QString ApiClient::lastError() const { return m_lastError; }
QString ApiClient::userName() const { return m_userName; }
QString ApiClient::userRole() const { return m_userRole; }
QString ApiClient::healthStatus() const { return m_healthStatus; }
bool ApiClient::setupKnown() const { return m_setupKnown; }
bool ApiClient::needsSetup() const { return m_needsSetup; }
bool ApiClient::developmentWorkspace() const { return m_developmentWorkspace; }
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
QVariantList ApiClient::users() const { return m_users; }
QVariantList ApiClient::knowledgeDocuments() const { return m_knowledgeDocuments; }
QVariantList ApiClient::knowledgeHits() const { return m_knowledgeHits; }
QVariantList ApiClient::conversations() const { return m_conversations; }
QVariantList ApiClient::messages() const { return m_messages; }
QVariantList ApiClient::tasks() const { return m_tasks; }
QVariantList ApiClient::outbox() const { return m_outbox; }
QVariantList ApiClient::whatsappChannels() const { return m_whatsappChannels; }
QVariantMap ApiClient::salesState() const { return m_salesState; }
QVariantMap ApiClient::groundedReply() const { return m_groundedReply; }
QString ApiClient::selectedConversationId() const { return m_selectedConversationId; }
QVariantList ApiClient::growthCampaigns() const { return m_growthCampaigns; }
QVariantList ApiClient::growthAttribution() const { return m_growthAttribution; }
QVariantList ApiClient::growthAudiences() const { return m_growthAudiences; }
QVariantList ApiClient::growthMedia() const { return m_growthMedia; }
QVariantList ApiClient::growthPlaybooks() const { return m_growthPlaybooks; }
QVariantList ApiClient::growthFeedback() const { return m_growthFeedback; }
QVariantMap ApiClient::growthFeedbackSummary() const { return m_growthFeedbackSummary; }
QVariantList ApiClient::seoProjects() const { return m_seoProjects; }
QVariantMap ApiClient::seoDashboard() const { return m_seoDashboard; }
QVariantList ApiClient::seoOpportunities() const { return m_seoOpportunities; }
QVariantList ApiClient::seoPlans() const { return m_seoPlans; }
QVariantList ApiClient::seoSnapshots() const { return m_seoSnapshots; }
QVariantMap ApiClient::seoLastResult() const { return m_seoLastResult; }
QString ApiClient::selectedSeoProjectId() const { return m_selectedSeoProjectId; }
QVariantList ApiClient::automationCatalog() const { return m_automationCatalog; }
QVariantList ApiClient::automationWorkflows() const { return m_automationWorkflows; }
QVariantMap ApiClient::automationGraph() const { return m_automationGraph; }
QVariantList ApiClient::automationRuns() const { return m_automationRuns; }
QString ApiClient::selectedAutomationWorkflowId() const { return m_selectedAutomationWorkflowId; }
QVariantMap ApiClient::aiSalesResult() const { return m_aiSalesResult; }
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

void ApiClient::clearError()
{
    setError(QString());
}

void ApiClient::health()
{
    if (m_healthRequestInFlight)
        return;

    m_healthRequestInFlight = true;
    QNetworkRequest request = makeRequest(QStringLiteral("/health"), false);
    request.setTransferTimeout(2200);
    auto *reply = m_network.get(request);

    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        m_healthRequestInFlight = false;

        if (reply->error() != QNetworkReply::NoError) {
            if (m_healthStatus != QStringLiteral("offline")) {
                m_healthStatus = QStringLiteral("offline");
                emit healthChanged();
            }
            if (!loggedIn())
                setError(QString());
        } else {
            const QString nextStatus = QJsonDocument::fromJson(body)
                .object()
                .value(QStringLiteral("status"))
                .toString(QStringLiteral("ok"));
            if (m_healthStatus != nextStatus) {
                m_healthStatus = nextStatus;
                emit healthChanged();
            }
            if (!loggedIn() && !m_setupKnown)
                fetchSetupStatus();
            setError(QString());
        }
        reply->deleteLater();
    });
}

void ApiClient::fetchSetupStatus()
{
    QNetworkRequest request = makeRequest(QStringLiteral("/api/v1/setup/status"), false);
    request.setTransferTimeout(3000);
    auto *reply = m_network.get(request);

    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() == QNetworkReply::NoError) {
            const QJsonObject object = QJsonDocument::fromJson(body).object();
            const bool nextNeedsSetup = object.value(QStringLiteral("needs_setup")).toBool(false);
            const bool nextDevelopmentWorkspace = object.value(QStringLiteral("development_workspace")).toBool(false);
            const bool changed = !m_setupKnown || m_needsSetup != nextNeedsSetup ||
                m_developmentWorkspace != nextDevelopmentWorkspace;
            m_setupKnown = true;
            m_needsSetup = nextNeedsSetup;
            m_developmentWorkspace = nextDevelopmentWorkspace;
            if (changed)
                emit setupStatusChanged();
        }
        reply->deleteLater();
    });
}

void ApiClient::resumeDevelopmentWorkspace()
{
    if (!m_developmentWorkspace || m_busy)
        return;

    setBusy(true);
    setError(QString());
    auto *reply = m_network.post(
        makeRequest(QStringLiteral("/api/v1/auth/development-session"), false),
        QByteArray());

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
        m_userName = object.value(QStringLiteral("user_name")).toString();
        m_userRole = object.value(QStringLiteral("role")).toString();
        setBusy(false);
        emit sessionChanged();
        reply->deleteLater();
        refreshAll();
    });
}

void ApiClient::bootstrapFirstOwner(
    const QString &companyName,
    const QString &companySlug,
    const QString &brandName,
    const QString &ownerName,
    const QString &ownerEmail,
    const QString &ownerPassword)
{
    if (companyName.trimmed().size() < 2 ||
        companySlug.trimmed().size() < 3 ||
        ownerName.trimmed().size() < 2 ||
        ownerEmail.trimmed().size() < 5 ||
        ownerPassword.size() < 10) {
        setError(QStringLiteral("Please complete the required first-owner fields."));
        return;
    }

    setBusy(true);
    setError(QString());

    QJsonObject payload{
        {QStringLiteral("company_name"), companyName.trimmed()},
        {QStringLiteral("company_slug"), companySlug.trimmed().toLower()},
        {QStringLiteral("owner_name"), ownerName.trimmed()},
        {QStringLiteral("owner_email"), ownerEmail.trimmed()},
        {QStringLiteral("owner_password"), ownerPassword},
    };
    if (!brandName.trimmed().isEmpty())
        payload.insert(QStringLiteral("brand_name"), brandName.trimmed());

    auto *reply = m_network.post(
        makeRequest(QStringLiteral("/api/v1/auth/bootstrap"), false),
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
        m_userName = object.value(QStringLiteral("user_name")).toString();
        m_userRole = object.value(QStringLiteral("role")).toString();
        m_setupKnown = true;
        m_needsSetup = false;

        setBusy(false);
        setError(QString());
        emit setupStatusChanged();
        emit sessionChanged();
        reply->deleteLater();
        refreshAll();
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
    m_users.clear();
    m_knowledgeDocuments.clear();
    m_knowledgeHits.clear();
    m_conversations.clear();
    m_messages.clear();
    m_tasks.clear();
    m_outbox.clear();
    m_whatsappChannels.clear();
    m_salesState.clear();
    m_groundedReply.clear();
    m_selectedConversationId.clear();
    m_growthCampaigns.clear();
    m_growthAttribution.clear();
    m_growthAudiences.clear();
    m_growthMedia.clear();
    m_growthPlaybooks.clear();
    m_growthFeedback.clear();
    m_growthFeedbackSummary.clear();
    m_seoProjects.clear();
    m_seoDashboard.clear();
    m_seoOpportunities.clear();
    m_seoPlans.clear();
    m_seoSnapshots.clear();
    m_seoLastResult.clear();
    m_selectedSeoProjectId.clear();
    m_automationCatalog.clear();
    m_automationWorkflows.clear();
    m_automationGraph.clear();
    m_automationRuns.clear();
    m_selectedAutomationWorkflowId.clear();
    m_aiSalesResult.clear();
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
    emit usersChanged();
    emit knowledgeDocumentsChanged();
    emit knowledgeHitsChanged();
    emit conversationsChanged();
    emit messagesChanged();
    emit tasksChanged();
    emit outboxChanged();
    emit whatsappChannelsChanged();
    emit salesStateChanged();
    emit groundedReplyChanged();
    emit growthCampaignsChanged();
    emit growthAttributionChanged();
    emit growthAudiencesChanged();
    emit growthMediaChanged();
    emit growthPlaybooksChanged();
    emit growthFeedbackChanged();
    emit growthFeedbackSummaryChanged();
    emit seoProjectsChanged();
    emit seoDashboardChanged();
    emit seoOpportunitiesChanged();
    emit seoPlansChanged();
    emit seoSnapshotsChanged();
    emit seoLastResultChanged();
    emit automationCatalogChanged();
    emit automationWorkflowsChanged();
    emit automationGraphChanged();
    emit automationRunsChanged();
    emit aiSalesResultChanged();
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
    refreshWorkspace();
    refreshGrowth();
    refreshSeo();
    refreshAutomation();
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


void ApiClient::refreshWorkspace()
{
    if (!loggedIn())
        return;
    fetchUsers();
    fetchKnowledgeDocuments();
    fetchConversations();
    fetchTasks();
    fetchOutbox();
    fetchWhatsAppChannels();
}

void ApiClient::createUser(const QString &email, const QString &displayName, const QString &password, const QString &role)
{
    const QJsonObject payload{
        {QStringLiteral("email"), email.trimmed()},
        {QStringLiteral("display_name"), displayName.trimmed()},
        {QStringLiteral("password"), password},
        {QStringLiteral("role"), role.trimmed().isEmpty() ? QStringLiteral("sales_agent") : role.trimmed()},
    };
    setBusy(true);
    auto *reply = m_network.post(makeRequest(QStringLiteral("/api/v1/users"), true), QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { setError(QString()); fetchUsers(); }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::createKnowledgeDocument(const QString &title, const QString &category, const QString &sourceName, const QString &content)
{
    QJsonObject payload{
        {QStringLiteral("title"), title.trimmed()},
        {QStringLiteral("category"), category.trimmed().isEmpty() ? QStringLiteral("general") : category.trimmed()},
        {QStringLiteral("content"), content},
    };
    if (!sourceName.trimmed().isEmpty()) payload.insert(QStringLiteral("source_name"), sourceName.trimmed());
    setBusy(true);
    auto *reply = m_network.post(makeRequest(QStringLiteral("/api/v1/knowledge/documents"), true), QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { setError(QString()); fetchKnowledgeDocuments(); }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::queryKnowledge(const QString &question)
{
    const QJsonObject payload{
        {QStringLiteral("question"), question.trimmed()},
        {QStringLiteral("limit"), 8},
    };
    setBusy(true);
    auto *reply = m_network.post(makeRequest(QStringLiteral("/api/v1/knowledge/query"), true), QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) {
            setError(apiErrorMessage(body, reply->errorString()));
        } else {
            const QJsonObject object = QJsonDocument::fromJson(body).object();
            m_knowledgeHits = object.value(QStringLiteral("hits")).toArray().toVariantList();
            setError(QString());
            emit knowledgeHitsChanged();
        }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::createConversation(const QString &leadId, const QString &channel, const QString &externalContact, const QString &displayName)
{
    QJsonObject payload{
        {QStringLiteral("channel"), channel.trimmed().isEmpty() ? QStringLiteral("manual") : channel.trimmed()},
        {QStringLiteral("external_contact"), externalContact.trimmed()},
    };
    if (!leadId.trimmed().isEmpty()) payload.insert(QStringLiteral("lead_id"), leadId.trimmed());
    if (!displayName.trimmed().isEmpty()) payload.insert(QStringLiteral("display_name"), displayName.trimmed());
    setBusy(true);
    auto *reply = m_network.post(makeRequest(QStringLiteral("/api/v1/inbox/conversations"), true), QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { setError(QString()); fetchConversations(); }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::loadMessages(const QString &conversationId)
{
    if (conversationId.trimmed().isEmpty())
        return;
    m_selectedConversationId = conversationId.trimmed();
    auto *reply = m_network.get(makeRequest(
        QStringLiteral("/api/v1/inbox/conversations/") + m_selectedConversationId + QStringLiteral("/messages"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) {
            setError(apiErrorMessage(body, reply->errorString()));
        } else {
            m_messages = QJsonDocument::fromJson(body).array().toVariantList();
            setError(QString());
            emit messagesChanged();
        }
        reply->deleteLater();
    });
    loadSalesState(m_selectedConversationId);
}

void ApiClient::sendMessage(const QString &conversationId, const QString &direction, const QString &sender, const QString &body)
{
    const QJsonObject payload{
        {QStringLiteral("direction"), direction.trimmed().isEmpty() ? QStringLiteral("outbound") : direction.trimmed()},
        {QStringLiteral("sender"), sender.trimmed().isEmpty() ? m_userName : sender.trimmed()},
        {QStringLiteral("body"), body},
    };
    setBusy(true);
    auto *reply = m_network.post(
        makeRequest(QStringLiteral("/api/v1/inbox/conversations/") + conversationId + QStringLiteral("/messages"), true),
        QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply, conversationId] {
        const QByteArray response = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(response, reply->errorString()));
        else {
            setError(QString());
            loadMessages(conversationId);
            fetchConversations();
        }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::createTask(const QString &leadId, const QString &assignedUserId, const QString &title, const QString &notes, const QString &dueAtIso)
{
    QJsonObject payload{{QStringLiteral("title"), title.trimmed()}};
    if (!leadId.trimmed().isEmpty()) payload.insert(QStringLiteral("lead_id"), leadId.trimmed());
    if (!assignedUserId.trimmed().isEmpty()) payload.insert(QStringLiteral("assigned_user_id"), assignedUserId.trimmed());
    if (!notes.trimmed().isEmpty()) payload.insert(QStringLiteral("notes"), notes.trimmed());
    if (!dueAtIso.trimmed().isEmpty()) payload.insert(QStringLiteral("due_at"), dueAtIso.trimmed());
    setBusy(true);
    auto *reply = m_network.post(makeRequest(QStringLiteral("/api/v1/tasks"), true), QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { setError(QString()); fetchTasks(); }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::completeTask(const QString &taskId)
{
    setBusy(true);
    auto *reply = m_network.post(makeRequest(QStringLiteral("/api/v1/tasks/") + taskId + QStringLiteral("/complete"), true), QByteArray());
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { setError(QString()); fetchTasks(); }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::loadSalesState(const QString &conversationId)
{
    if (conversationId.trimmed().isEmpty())
        return;
    auto *reply = m_network.get(makeRequest(
        QStringLiteral("/api/v1/omnichannel/conversations/") + conversationId + QStringLiteral("/sales-state"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) {
            setError(apiErrorMessage(body, reply->errorString()));
        } else {
            m_salesState = QJsonDocument::fromJson(body).object().toVariantMap();
            emit salesStateChanged();
        }
        reply->deleteLater();
    });
}

void ApiClient::updateSalesState(const QString &conversationId, const QString &replyPreference, const QString &journeyStage, int leadScore, const QString &assignedUserId, bool autoReplyEnabled)
{
    QJsonObject payload{
        {QStringLiteral("reply_preference"), replyPreference.trimmed()},
        {QStringLiteral("journey_stage"), journeyStage.trimmed()},
        {QStringLiteral("lead_score"), leadScore},
        {QStringLiteral("auto_reply_enabled"), autoReplyEnabled},
    };
    if (!assignedUserId.trimmed().isEmpty()) payload.insert(QStringLiteral("assigned_user_id"), assignedUserId.trimmed());

    setBusy(true);
    auto *reply = m_network.sendCustomRequest(
        makeRequest(QStringLiteral("/api/v1/omnichannel/conversations/") + conversationId + QStringLiteral("/sales-state"), true),
        QByteArray("PATCH"),
        QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else {
            m_salesState = QJsonDocument::fromJson(body).object().toVariantMap();
            setError(QString());
            emit salesStateChanged();
        }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::prepareGroundedReply(const QString &conversationId, const QString &question, const QString &city, double maxPrice, int bedrooms, const QString &unitType, const QString &channelId)
{
    QJsonObject payload{
        {QStringLiteral("question"), question.trimmed()},
        {QStringLiteral("source_confidence"), 1.0},
    };
    if (!city.trimmed().isEmpty()) payload.insert(QStringLiteral("city"), city.trimmed());
    if (maxPrice > 0) payload.insert(QStringLiteral("max_price"), maxPrice);
    if (bedrooms >= 0) payload.insert(QStringLiteral("bedrooms"), bedrooms);
    if (!unitType.trimmed().isEmpty()) payload.insert(QStringLiteral("unit_type"), unitType.trimmed());
    if (!channelId.trimmed().isEmpty()) payload.insert(QStringLiteral("channel_id"), channelId.trimmed());

    setBusy(true);
    auto *reply = m_network.post(
        makeRequest(QStringLiteral("/api/v1/omnichannel/conversations/") + conversationId + QStringLiteral("/grounded-reply"), true),
        QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) {
            setError(apiErrorMessage(body, reply->errorString()));
        } else {
            m_groundedReply = QJsonDocument::fromJson(body).object().toVariantMap();
            setError(QString());
            emit groundedReplyChanged();
            fetchOutbox();
            fetchTasks();
        }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::requestHandoff(const QString &conversationId, const QString &reason, const QString &assignToUserId)
{
    QJsonObject payload{{QStringLiteral("reason"), reason.trimmed()}};
    if (!assignToUserId.trimmed().isEmpty()) payload.insert(QStringLiteral("assign_to_user_id"), assignToUserId.trimmed());
    setBusy(true);
    auto *reply = m_network.post(
        makeRequest(QStringLiteral("/api/v1/omnichannel/conversations/") + conversationId + QStringLiteral("/handoff"), true),
        QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply, conversationId] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { setError(QString()); loadSalesState(conversationId); fetchTasks(); }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::approveOutbox(const QString &outboxId)
{
    setBusy(true);
    auto *reply = m_network.post(makeRequest(QStringLiteral("/api/v1/omnichannel/outbox/") + outboxId + QStringLiteral("/approve"), true), QByteArray());
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { setError(QString()); fetchOutbox(); }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::rejectOutbox(const QString &outboxId)
{
    setBusy(true);
    auto *reply = m_network.post(makeRequest(QStringLiteral("/api/v1/omnichannel/outbox/") + outboxId + QStringLiteral("/reject"), true), QByteArray());
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { setError(QString()); fetchOutbox(); }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::dispatchOutbox(const QString &outboxId)
{
    setBusy(true);
    auto *reply = m_network.post(makeRequest(QStringLiteral("/api/v1/omnichannel/outbox/") + outboxId + QStringLiteral("/dispatch"), true), QByteArray());
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { setError(QString()); fetchOutbox(); }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::createWhatsAppChannel(const QString &displayName, const QString &phoneNumberId, const QString &wabaId, const QString &businessPhone, const QString &graphVersion, const QString &accessToken, const QString &appSecret, bool isDefault, bool enabled)
{
    QJsonObject payload{
        {QStringLiteral("display_name"), displayName.trimmed()},
        {QStringLiteral("phone_number_id"), phoneNumberId.trimmed()},
        {QStringLiteral("graph_api_version"), graphVersion.trimmed().isEmpty() ? QStringLiteral("v23.0") : graphVersion.trimmed()},
        {QStringLiteral("is_default"), isDefault},
        {QStringLiteral("enabled"), enabled},
    };
    if (!wabaId.trimmed().isEmpty()) payload.insert(QStringLiteral("waba_id"), wabaId.trimmed());
    if (!businessPhone.trimmed().isEmpty()) payload.insert(QStringLiteral("business_phone"), businessPhone.trimmed());
    if (!accessToken.trimmed().isEmpty()) payload.insert(QStringLiteral("access_token"), accessToken);
    if (!appSecret.trimmed().isEmpty()) payload.insert(QStringLiteral("app_secret"), appSecret);

    setBusy(true);
    auto *reply = m_network.post(makeRequest(QStringLiteral("/api/v1/whatsapp/channels"), true), QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { setError(QString()); fetchWhatsAppChannels(); }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::fetchUsers()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/users"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { m_users = QJsonDocument::fromJson(body).array().toVariantList(); emit usersChanged(); }
        reply->deleteLater();
    });
}

void ApiClient::fetchKnowledgeDocuments()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/knowledge/documents"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { m_knowledgeDocuments = QJsonDocument::fromJson(body).array().toVariantList(); emit knowledgeDocumentsChanged(); }
        reply->deleteLater();
    });
}

void ApiClient::fetchConversations()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/inbox/conversations"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { m_conversations = QJsonDocument::fromJson(body).array().toVariantList(); emit conversationsChanged(); }
        reply->deleteLater();
    });
}

void ApiClient::fetchTasks()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/tasks"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { m_tasks = QJsonDocument::fromJson(body).array().toVariantList(); emit tasksChanged(); }
        reply->deleteLater();
    });
}

void ApiClient::fetchOutbox()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/omnichannel/outbox"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { m_outbox = QJsonDocument::fromJson(body).array().toVariantList(); emit outboxChanged(); }
        reply->deleteLater();
    });
}

void ApiClient::fetchWhatsAppChannels()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/whatsapp/channels"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { m_whatsappChannels = QJsonDocument::fromJson(body).array().toVariantList(); emit whatsappChannelsChanged(); }
        reply->deleteLater();
    });
}


void ApiClient::refreshGrowth()
{
    if (!loggedIn())
        return;
    fetchGrowthCampaigns();
    fetchGrowthAttribution();
    fetchGrowthAudiences();
    fetchGrowthMedia();
    fetchGrowthPlaybooks();
    fetchGrowthFeedback();
    fetchGrowthFeedbackSummary();
}

void ApiClient::createGrowthCampaign(const QString &name, const QString &channel, const QString &objective, double budget, double spend, const QString &currency, const QString &utmSource, const QString &utmMedium, const QString &utmCampaign)
{
    QJsonObject payload{
        {QStringLiteral("name"), name.trimmed()},
        {QStringLiteral("channel"), channel.trimmed()},
        {QStringLiteral("status"), QStringLiteral("draft")},
        {QStringLiteral("budget"), budget},
        {QStringLiteral("spend"), spend},
        {QStringLiteral("currency"), currency.trimmed().isEmpty() ? QStringLiteral("EGP") : currency.trimmed().toUpper()},
    };
    if (!objective.trimmed().isEmpty()) payload.insert(QStringLiteral("objective"), objective.trimmed());
    if (!utmSource.trimmed().isEmpty()) payload.insert(QStringLiteral("utm_source"), utmSource.trimmed());
    if (!utmMedium.trimmed().isEmpty()) payload.insert(QStringLiteral("utm_medium"), utmMedium.trimmed());
    if (!utmCampaign.trimmed().isEmpty()) payload.insert(QStringLiteral("utm_campaign"), utmCampaign.trimmed());

    setBusy(true);
    auto *reply = m_network.post(makeRequest(QStringLiteral("/api/v1/growth/campaigns"), true), QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { setError(QString()); fetchGrowthCampaigns(); fetchGrowthAttribution(); }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::createGrowthAudience(const QString &name, const QString &description, const QString &source, const QString &status, int minScore, const QString &city, double minBudget, double maxBudget)
{
    QJsonObject rules;
    if (!source.trimmed().isEmpty()) rules.insert(QStringLiteral("sources"), QJsonArray{source.trimmed()});
    if (!status.trimmed().isEmpty()) rules.insert(QStringLiteral("statuses"), QJsonArray{status.trimmed()});
    if (minScore >= 0) rules.insert(QStringLiteral("min_score"), minScore);
    if (!city.trimmed().isEmpty()) rules.insert(QStringLiteral("preferred_city"), city.trimmed());
    if (minBudget > 0) rules.insert(QStringLiteral("min_budget"), minBudget);
    if (maxBudget > 0) rules.insert(QStringLiteral("max_budget"), maxBudget);

    QJsonObject payload{
        {QStringLiteral("name"), name.trimmed()},
        {QStringLiteral("description"), description.trimmed()},
        {QStringLiteral("rules"), rules},
        {QStringLiteral("is_active"), true},
    };
    setBusy(true);
    auto *reply = m_network.post(makeRequest(QStringLiteral("/api/v1/growth/audiences"), true), QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { setError(QString()); fetchGrowthAudiences(); }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::createGrowthMedia(const QString &projectId, const QString &unitId, const QString &title, const QString &mediaType, const QString &url, const QString &sourceKind, bool verified)
{
    QJsonObject payload{
        {QStringLiteral("title"), title.trimmed()},
        {QStringLiteral("media_type"), mediaType.trimmed()},
        {QStringLiteral("url"), url.trimmed()},
        {QStringLiteral("tags"), QJsonArray{}},
        {QStringLiteral("source_kind"), sourceKind.trimmed().isEmpty() ? QStringLiteral("company") : sourceKind.trimmed()},
        {QStringLiteral("is_verified"), verified},
    };
    if (!projectId.trimmed().isEmpty()) payload.insert(QStringLiteral("project_id"), projectId.trimmed());
    if (!unitId.trimmed().isEmpty()) payload.insert(QStringLiteral("unit_id"), unitId.trimmed());

    setBusy(true);
    auto *reply = m_network.post(makeRequest(QStringLiteral("/api/v1/growth/media"), true), QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { setError(QString()); fetchGrowthMedia(); }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::createGrowthPlaybook(const QString &name, const QString &description, const QString &triggerStage, const QString &stepsText)
{
    QJsonArray steps;
    for (const QString &raw : stepsText.split('\n', Qt::SkipEmptyParts)) {
        const QString item = raw.trimmed();
        if (!item.isEmpty())
            steps.append(item);
    }
    QJsonObject payload{
        {QStringLiteral("name"), name.trimmed()},
        {QStringLiteral("description"), description.trimmed()},
        {QStringLiteral("steps"), steps},
        {QStringLiteral("is_active"), true},
    };
    if (!triggerStage.trimmed().isEmpty()) payload.insert(QStringLiteral("trigger_stage"), triggerStage.trimmed());

    setBusy(true);
    auto *reply = m_network.post(makeRequest(QStringLiteral("/api/v1/growth/playbooks"), true), QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { setError(QString()); fetchGrowthPlaybooks(); }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::createGrowthFeedback(const QString &leadId, const QString &conversationId, const QString &channel, const QString &category, int rating, const QString &comment)
{
    QJsonObject payload{
        {QStringLiteral("category"), category.trimmed().isEmpty() ? QStringLiteral("general") : category.trimmed()},
        {QStringLiteral("comment"), comment.trimmed()},
    };
    if (!leadId.trimmed().isEmpty()) payload.insert(QStringLiteral("lead_id"), leadId.trimmed());
    if (!conversationId.trimmed().isEmpty()) payload.insert(QStringLiteral("conversation_id"), conversationId.trimmed());
    if (!channel.trimmed().isEmpty()) payload.insert(QStringLiteral("channel"), channel.trimmed());
    if (rating >= 1 && rating <= 5) payload.insert(QStringLiteral("rating"), rating);

    setBusy(true);
    auto *reply = m_network.post(makeRequest(QStringLiteral("/api/v1/growth/feedback"), true), QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { setError(QString()); fetchGrowthFeedback(); fetchGrowthFeedbackSummary(); }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::fetchGrowthCampaigns()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/growth/campaigns"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { m_growthCampaigns = QJsonDocument::fromJson(body).array().toVariantList(); emit growthCampaignsChanged(); }
        reply->deleteLater();
    });
}

void ApiClient::fetchGrowthAttribution()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/growth/attribution/campaigns"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { m_growthAttribution = QJsonDocument::fromJson(body).array().toVariantList(); emit growthAttributionChanged(); }
        reply->deleteLater();
    });
}

void ApiClient::fetchGrowthAudiences()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/growth/audiences"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { m_growthAudiences = QJsonDocument::fromJson(body).array().toVariantList(); emit growthAudiencesChanged(); }
        reply->deleteLater();
    });
}

void ApiClient::fetchGrowthMedia()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/growth/media"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { m_growthMedia = QJsonDocument::fromJson(body).array().toVariantList(); emit growthMediaChanged(); }
        reply->deleteLater();
    });
}

void ApiClient::fetchGrowthPlaybooks()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/growth/playbooks"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { m_growthPlaybooks = QJsonDocument::fromJson(body).array().toVariantList(); emit growthPlaybooksChanged(); }
        reply->deleteLater();
    });
}

void ApiClient::fetchGrowthFeedback()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/growth/feedback"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { m_growthFeedback = QJsonDocument::fromJson(body).array().toVariantList(); emit growthFeedbackChanged(); }
        reply->deleteLater();
    });
}

void ApiClient::fetchGrowthFeedbackSummary()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/growth/feedback/summary"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { m_growthFeedbackSummary = QJsonDocument::fromJson(body).object().toVariantMap(); emit growthFeedbackSummaryChanged(); }
        reply->deleteLater();
    });
}


void ApiClient::refreshSeo()
{
    if (!loggedIn())
        return;
    fetchSeoProjects();
    if (!m_selectedSeoProjectId.isEmpty()) {
        fetchSeoDashboard(m_selectedSeoProjectId);
        fetchSeoPlans(m_selectedSeoProjectId);
        fetchSeoSnapshots(m_selectedSeoProjectId);
    }
}

void ApiClient::selectSeoProject(const QString &projectId)
{
    const QString id = projectId.trimmed();
    if (id.isEmpty())
        return;
    m_selectedSeoProjectId = id;
    m_seoOpportunities.clear();
    emit seoOpportunitiesChanged();
    fetchSeoDashboard(id);
    fetchSeoPlans(id);
    fetchSeoSnapshots(id);
}

void ApiClient::createSeoProject(const QString &name, const QString &siteUrl)
{
    const QJsonObject payload{
        {QStringLiteral("name"), name.trimmed()},
        {QStringLiteral("site_url"), siteUrl.trimmed()},
    };
    setBusy(true);
    auto *reply = m_network.post(makeRequest(QStringLiteral("/api/v1/seo/projects"), true), QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) {
            setError(apiErrorMessage(body, reply->errorString()));
        } else {
            const QJsonObject row = QJsonDocument::fromJson(body).object();
            m_selectedSeoProjectId = row.value(QStringLiteral("id")).toString();
            setError(QString());
            fetchSeoProjects();
            if (!m_selectedSeoProjectId.isEmpty())
                selectSeoProject(m_selectedSeoProjectId);
        }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::runSeoAudit(const QString &projectId, const QString &targetUrl)
{
    QJsonObject payload;
    if (!targetUrl.trimmed().isEmpty())
        payload.insert(QStringLiteral("target_url"), targetUrl.trimmed());
    setBusy(true);
    auto *reply = m_network.post(
        makeRequest(QStringLiteral("/api/v1/seo/projects/") + projectId + QStringLiteral("/audit"), true),
        QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply, projectId] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else {
            m_seoLastResult = QJsonDocument::fromJson(body).object().toVariantMap();
            setError(QString());
            emit seoLastResultChanged();
            fetchSeoDashboard(projectId);
            fetchSeoSnapshots(projectId);
        }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::runSeoCrawl(const QString &projectId, int maxPages, int concurrency)
{
    const QJsonObject payload{
        {QStringLiteral("max_pages"), qBound(1, maxPages, 300)},
        {QStringLiteral("concurrency"), qBound(1, concurrency, 10)},
    };
    setBusy(true);
    auto *reply = m_network.post(
        makeRequest(QStringLiteral("/api/v1/seo/projects/") + projectId + QStringLiteral("/crawl"), true),
        QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply, projectId] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else {
            m_seoLastResult = QJsonDocument::fromJson(body).object().toVariantMap();
            setError(QString());
            emit seoLastResultChanged();
            fetchSeoDashboard(projectId);
            fetchSeoSnapshots(projectId);
        }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::loadSeoOpportunities(const QString &projectId)
{
    auto *reply = m_network.get(makeRequest(
        QStringLiteral("/api/v1/seo/projects/") + projectId + QStringLiteral("/opportunities?limit=50"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) {
            setError(apiErrorMessage(body, reply->errorString()));
        } else {
            m_seoOpportunities = QJsonDocument::fromJson(body).array().toVariantList();
            setError(QString());
            emit seoOpportunitiesChanged();
        }
        reply->deleteLater();
    });
}

void ApiClient::planSeoChange(const QString &projectId, const QString &targetUrl, const QString &action, const QString &reason)
{
    const QJsonObject payload{
        {QStringLiteral("target_url"), targetUrl.trimmed()},
        {QStringLiteral("action"), action.trimmed()},
        {QStringLiteral("before"), QJsonObject{}},
        {QStringLiteral("after"), QJsonObject{}},
        {QStringLiteral("reason"), reason.trimmed()},
    };
    setBusy(true);
    auto *reply = m_network.post(
        makeRequest(QStringLiteral("/api/v1/seo/projects/") + projectId + QStringLiteral("/autopilot/plan"), true),
        QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply, projectId] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else {
            m_seoLastResult = QJsonDocument::fromJson(body).object().toVariantMap();
            setError(QString());
            emit seoLastResultChanged();
            fetchSeoPlans(projectId);
            fetchSeoDashboard(projectId);
        }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::fetchSeoProjects()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/seo/projects"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) {
            setError(apiErrorMessage(body, reply->errorString()));
        } else {
            m_seoProjects = QJsonDocument::fromJson(body).array().toVariantList();
            emit seoProjectsChanged();
            if (m_selectedSeoProjectId.isEmpty() && !m_seoProjects.isEmpty()) {
                m_selectedSeoProjectId = m_seoProjects.constFirst().toMap().value(QStringLiteral("id")).toString();
                if (!m_selectedSeoProjectId.isEmpty()) {
                    fetchSeoDashboard(m_selectedSeoProjectId);
                    fetchSeoPlans(m_selectedSeoProjectId);
                    fetchSeoSnapshots(m_selectedSeoProjectId);
                }
            }
        }
        reply->deleteLater();
    });
}

void ApiClient::fetchSeoDashboard(const QString &projectId)
{
    auto *reply = m_network.get(makeRequest(
        QStringLiteral("/api/v1/seo/projects/") + projectId + QStringLiteral("/dashboard"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { m_seoDashboard = QJsonDocument::fromJson(body).object().toVariantMap(); emit seoDashboardChanged(); }
        reply->deleteLater();
    });
}

void ApiClient::fetchSeoPlans(const QString &projectId)
{
    auto *reply = m_network.get(makeRequest(
        QStringLiteral("/api/v1/seo/projects/") + projectId + QStringLiteral("/autopilot/plans"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { m_seoPlans = QJsonDocument::fromJson(body).array().toVariantList(); emit seoPlansChanged(); }
        reply->deleteLater();
    });
}

void ApiClient::fetchSeoSnapshots(const QString &projectId)
{
    auto *reply = m_network.get(makeRequest(
        QStringLiteral("/api/v1/seo/projects/") + projectId + QStringLiteral("/snapshots"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { m_seoSnapshots = QJsonDocument::fromJson(body).array().toVariantList(); emit seoSnapshotsChanged(); }
        reply->deleteLater();
    });
}


void ApiClient::refreshAutomation()
{
    if (!loggedIn())
        return;
    fetchAutomationCatalog();
    fetchAutomationWorkflows();
    if (!m_selectedAutomationWorkflowId.isEmpty()) {
        fetchAutomationGraph(m_selectedAutomationWorkflowId);
        fetchAutomationRuns(m_selectedAutomationWorkflowId);
    }
}

void ApiClient::selectAutomationWorkflow(const QString &workflowId)
{
    const QString id = workflowId.trimmed();
    if (id.isEmpty())
        return;
    m_selectedAutomationWorkflowId = id;
    fetchAutomationGraph(id);
    fetchAutomationRuns(id);
}

void ApiClient::createAutomationWorkflow(const QString &name, const QString &description)
{
    const QJsonObject payload{
        {QStringLiteral("name"), name.trimmed()},
        {QStringLiteral("description"), description.trimmed()},
    };
    setBusy(true);
    auto *reply = m_network.post(makeRequest(QStringLiteral("/api/v1/automations"), true), QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) {
            setError(apiErrorMessage(body, reply->errorString()));
        } else {
            const QJsonObject row = QJsonDocument::fromJson(body).object();
            m_selectedAutomationWorkflowId = row.value(QStringLiteral("id")).toString();
            setError(QString());
            fetchAutomationWorkflows();
            if (!m_selectedAutomationWorkflowId.isEmpty())
                selectAutomationWorkflow(m_selectedAutomationWorkflowId);
        }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::duplicateAutomationWorkflow(const QString &workflowId)
{
    setBusy(true);
    auto *reply = m_network.post(
        makeRequest(QStringLiteral("/api/v1/automations/") + workflowId + QStringLiteral("/duplicate"), true),
        QByteArray());
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) {
            setError(apiErrorMessage(body, reply->errorString()));
        } else {
            const QJsonObject graph = QJsonDocument::fromJson(body).object();
            m_automationGraph = graph.toVariantMap();
            const QJsonObject workflow = graph.value(QStringLiteral("workflow")).toObject();
            m_selectedAutomationWorkflowId = workflow.value(QStringLiteral("id")).toString();
            setError(QString());
            emit automationGraphChanged();
            fetchAutomationWorkflows();
            fetchAutomationRuns(m_selectedAutomationWorkflowId);
        }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::replaceAutomationGraph(const QString &workflowId, const QVariantList &nodes, const QVariantList &edges)
{
    const QJsonObject payload{
        {QStringLiteral("nodes"), QJsonArray::fromVariantList(nodes)},
        {QStringLiteral("edges"), QJsonArray::fromVariantList(edges)},
    };
    setBusy(true);
    auto *reply = m_network.sendCustomRequest(
        makeRequest(QStringLiteral("/api/v1/automations/") + workflowId + QStringLiteral("/graph"), true),
        QByteArray("PUT"),
        QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply, workflowId] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) {
            setError(apiErrorMessage(body, reply->errorString()));
        } else {
            m_automationGraph = QJsonDocument::fromJson(body).object().toVariantMap();
            setError(QString());
            emit automationGraphChanged();
            fetchAutomationWorkflows();
            fetchAutomationRuns(workflowId);
        }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::runAutomationWorkflow(const QString &workflowId, const QString &leadId)
{
    QJsonObject input;
    if (!leadId.trimmed().isEmpty())
        input.insert(QStringLiteral("lead_id"), leadId.trimmed());
    const QJsonObject payload{
        {QStringLiteral("trigger_type"), QStringLiteral("manual")},
        {QStringLiteral("input"), input},
    };
    setBusy(true);
    auto *reply = m_network.post(
        makeRequest(QStringLiteral("/api/v1/automations/") + workflowId + QStringLiteral("/run"), true),
        QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply, workflowId] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { setError(QString()); fetchAutomationRuns(workflowId); }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::decideAutomationApproval(const QString &approvalId, const QString &decision, const QString &note)
{
    const QJsonObject payload{
        {QStringLiteral("decision"), decision.trimmed()},
        {QStringLiteral("note"), note.trimmed()},
    };
    setBusy(true);
    auto *reply = m_network.post(
        makeRequest(QStringLiteral("/api/v1/automations/approvals/") + approvalId + QStringLiteral("/decision"), true),
        QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else {
            setError(QString());
            if (!m_selectedAutomationWorkflowId.isEmpty())
                fetchAutomationRuns(m_selectedAutomationWorkflowId);
        }
        setBusy(false);
        reply->deleteLater();
    });
}

void ApiClient::fetchAutomationCatalog()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/automations/catalog"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else {
            const QJsonObject object = QJsonDocument::fromJson(body).object();
            m_automationCatalog = object.value(QStringLiteral("nodes")).toArray().toVariantList();
            emit automationCatalogChanged();
        }
        reply->deleteLater();
    });
}

void ApiClient::fetchAutomationWorkflows()
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/automations"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) {
            setError(apiErrorMessage(body, reply->errorString()));
        } else {
            m_automationWorkflows = QJsonDocument::fromJson(body).array().toVariantList();
            emit automationWorkflowsChanged();
            if (m_selectedAutomationWorkflowId.isEmpty() && !m_automationWorkflows.isEmpty()) {
                m_selectedAutomationWorkflowId = m_automationWorkflows.constFirst().toMap().value(QStringLiteral("id")).toString();
                if (!m_selectedAutomationWorkflowId.isEmpty())
                    selectAutomationWorkflow(m_selectedAutomationWorkflowId);
            }
        }
        reply->deleteLater();
    });
}

void ApiClient::fetchAutomationGraph(const QString &workflowId)
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/automations/") + workflowId, true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { m_automationGraph = QJsonDocument::fromJson(body).object().toVariantMap(); emit automationGraphChanged(); }
        reply->deleteLater();
    });
}

void ApiClient::fetchAutomationRuns(const QString &workflowId)
{
    auto *reply = m_network.get(makeRequest(QStringLiteral("/api/v1/automations/") + workflowId + QStringLiteral("/runs"), true));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) setError(apiErrorMessage(body, reply->errorString()));
        else { m_automationRuns = QJsonDocument::fromJson(body).array().toVariantList(); emit automationRunsChanged(); }
        reply->deleteLater();
    });
}


void ApiClient::runAiSalesAssist(const QString &question, const QString &city, double minPrice, double maxPrice, int bedrooms, const QString &unitType)
{
    QJsonObject payload{
        {QStringLiteral("question"), question.trimmed()},
        {QStringLiteral("limit"), 8},
    };
    if (!city.trimmed().isEmpty()) payload.insert(QStringLiteral("city"), city.trimmed());
    if (minPrice > 0) payload.insert(QStringLiteral("min_price"), minPrice);
    if (maxPrice > 0) payload.insert(QStringLiteral("max_price"), maxPrice);
    if (bedrooms >= 0) payload.insert(QStringLiteral("bedrooms"), bedrooms);
    if (!unitType.trimmed().isEmpty()) payload.insert(QStringLiteral("unit_type"), unitType.trimmed());

    setBusy(true);
    setError(QString());
    auto *reply = m_network.post(
        makeRequest(QStringLiteral("/api/v1/ai/sales/assist"), true),
        QJsonDocument(payload).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, this, [this, reply] {
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) {
            setError(apiErrorMessage(body, reply->errorString()));
        } else {
            m_aiSalesResult = QJsonDocument::fromJson(body).object().toVariantMap();
            setError(QString());
            emit aiSalesResultChanged();
        }
        setBusy(false);
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
