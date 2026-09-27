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
    Q_PROPERTY(QVariantList users READ users NOTIFY usersChanged)
    Q_PROPERTY(QVariantList knowledgeDocuments READ knowledgeDocuments NOTIFY knowledgeDocumentsChanged)
    Q_PROPERTY(QVariantList knowledgeHits READ knowledgeHits NOTIFY knowledgeHitsChanged)
    Q_PROPERTY(QVariantList conversations READ conversations NOTIFY conversationsChanged)
    Q_PROPERTY(QVariantList messages READ messages NOTIFY messagesChanged)
    Q_PROPERTY(QVariantList tasks READ tasks NOTIFY tasksChanged)
    Q_PROPERTY(QVariantList outbox READ outbox NOTIFY outboxChanged)
    Q_PROPERTY(QVariantList whatsappChannels READ whatsappChannels NOTIFY whatsappChannelsChanged)
    Q_PROPERTY(QVariantMap salesState READ salesState NOTIFY salesStateChanged)
    Q_PROPERTY(QVariantMap groundedReply READ groundedReply NOTIFY groundedReplyChanged)
    Q_PROPERTY(QString selectedConversationId READ selectedConversationId NOTIFY messagesChanged)
    Q_PROPERTY(QVariantList growthCampaigns READ growthCampaigns NOTIFY growthCampaignsChanged)
    Q_PROPERTY(QVariantList growthAttribution READ growthAttribution NOTIFY growthAttributionChanged)
    Q_PROPERTY(QVariantList growthAudiences READ growthAudiences NOTIFY growthAudiencesChanged)
    Q_PROPERTY(QVariantList growthMedia READ growthMedia NOTIFY growthMediaChanged)
    Q_PROPERTY(QVariantList growthPlaybooks READ growthPlaybooks NOTIFY growthPlaybooksChanged)
    Q_PROPERTY(QVariantList growthFeedback READ growthFeedback NOTIFY growthFeedbackChanged)
    Q_PROPERTY(QVariantMap growthFeedbackSummary READ growthFeedbackSummary NOTIFY growthFeedbackSummaryChanged)
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
    QVariantList users() const;
    QVariantList knowledgeDocuments() const;
    QVariantList knowledgeHits() const;
    QVariantList conversations() const;
    QVariantList messages() const;
    QVariantList tasks() const;
    QVariantList outbox() const;
    QVariantList whatsappChannels() const;
    QVariantMap salesState() const;
    QVariantMap groundedReply() const;
    QString selectedConversationId() const;
    QVariantList growthCampaigns() const;
    QVariantList growthAttribution() const;
    QVariantList growthAudiences() const;
    QVariantList growthMedia() const;
    QVariantList growthPlaybooks() const;
    QVariantList growthFeedback() const;
    QVariantMap growthFeedbackSummary() const;
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
    Q_INVOKABLE void refreshWorkspace();
    Q_INVOKABLE void createUser(const QString &email, const QString &displayName, const QString &password, const QString &role);
    Q_INVOKABLE void createKnowledgeDocument(const QString &title, const QString &category, const QString &sourceName, const QString &content);
    Q_INVOKABLE void queryKnowledge(const QString &question);
    Q_INVOKABLE void createConversation(const QString &leadId, const QString &channel, const QString &externalContact, const QString &displayName);
    Q_INVOKABLE void loadMessages(const QString &conversationId);
    Q_INVOKABLE void sendMessage(const QString &conversationId, const QString &direction, const QString &sender, const QString &body);
    Q_INVOKABLE void createTask(const QString &leadId, const QString &assignedUserId, const QString &title, const QString &notes, const QString &dueAtIso);
    Q_INVOKABLE void completeTask(const QString &taskId);
    Q_INVOKABLE void loadSalesState(const QString &conversationId);
    Q_INVOKABLE void updateSalesState(const QString &conversationId, const QString &replyPreference, const QString &journeyStage, int leadScore, const QString &assignedUserId, bool autoReplyEnabled);
    Q_INVOKABLE void prepareGroundedReply(const QString &conversationId, const QString &question, const QString &city, double maxPrice, int bedrooms, const QString &unitType, const QString &channelId);
    Q_INVOKABLE void requestHandoff(const QString &conversationId, const QString &reason, const QString &assignToUserId);
    Q_INVOKABLE void approveOutbox(const QString &outboxId);
    Q_INVOKABLE void rejectOutbox(const QString &outboxId);
    Q_INVOKABLE void dispatchOutbox(const QString &outboxId);
    Q_INVOKABLE void createWhatsAppChannel(const QString &displayName, const QString &phoneNumberId, const QString &wabaId, const QString &businessPhone, const QString &graphVersion, const QString &accessToken, const QString &appSecret, bool isDefault, bool enabled);
    Q_INVOKABLE void refreshGrowth();
    Q_INVOKABLE void createGrowthCampaign(const QString &name, const QString &channel, const QString &objective, double budget, double spend, const QString &currency, const QString &utmSource, const QString &utmMedium, const QString &utmCampaign);
    Q_INVOKABLE void createGrowthAudience(const QString &name, const QString &description, const QString &source, const QString &status, int minScore, const QString &city, double minBudget, double maxBudget);
    Q_INVOKABLE void createGrowthMedia(const QString &projectId, const QString &unitId, const QString &title, const QString &mediaType, const QString &url, const QString &sourceKind, bool verified);
    Q_INVOKABLE void createGrowthPlaybook(const QString &name, const QString &description, const QString &triggerStage, const QString &stepsText);
    Q_INVOKABLE void createGrowthFeedback(const QString &leadId, const QString &conversationId, const QString &channel, const QString &category, int rating, const QString &comment);

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
    void usersChanged();
    void knowledgeDocumentsChanged();
    void knowledgeHitsChanged();
    void conversationsChanged();
    void messagesChanged();
    void tasksChanged();
    void outboxChanged();
    void whatsappChannelsChanged();
    void salesStateChanged();
    void groundedReplyChanged();
    void growthCampaignsChanged();
    void growthAttributionChanged();
    void growthAudiencesChanged();
    void growthMediaChanged();
    void growthPlaybooksChanged();
    void growthFeedbackChanged();
    void growthFeedbackSummaryChanged();
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
    void fetchUsers();
    void fetchKnowledgeDocuments();
    void fetchConversations();
    void fetchTasks();
    void fetchOutbox();
    void fetchWhatsAppChannels();
    void fetchGrowthCampaigns();
    void fetchGrowthAttribution();
    void fetchGrowthAudiences();
    void fetchGrowthMedia();
    void fetchGrowthPlaybooks();
    void fetchGrowthFeedback();
    void fetchGrowthFeedbackSummary();
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
    QVariantList m_users;
    QVariantList m_knowledgeDocuments;
    QVariantList m_knowledgeHits;
    QVariantList m_conversations;
    QVariantList m_messages;
    QVariantList m_tasks;
    QVariantList m_outbox;
    QVariantList m_whatsappChannels;
    QVariantMap m_salesState;
    QVariantMap m_groundedReply;
    QString m_selectedConversationId;
    QVariantList m_growthCampaigns;
    QVariantList m_growthAttribution;
    QVariantList m_growthAudiences;
    QVariantList m_growthMedia;
    QVariantList m_growthPlaybooks;
    QVariantList m_growthFeedback;
    QVariantMap m_growthFeedbackSummary;
    QVariantMap m_enterpriseSummary;
    QVariantList m_proposals;
    QVariantList m_invoices;
    QVariantList m_tickets;
    QVariantList m_reminders;
    QVariantList m_timeline;
    QString m_timelineLeadId;
};
