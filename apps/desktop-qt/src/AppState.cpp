#include "AppState.hpp"

#include <QDateTime>
#include <QLocale>
#include <QSettings>
#include <QSet>

namespace {
const QStringList kLanguageCodes{"ar", "en", "tr", "ru", "de", "it", "es", "fr"};
const QStringList kLanguageNames{"العربية", "English", "Türkçe", "Русский", "Deutsch", "Italiano", "Español", "Français"};
const QStringList kThemeCodes{"neon", "blue", "green", "amber", "silver", "violet"};
const QStringList kThemeNames{"Neon Fusion", "Electric Blue", "Neon Green", "Amber", "Metallic Silver", "Violet"};
const QString kLicenseGateVersion{QStringLiteral("2.2.1")};
using TranslationRow = QStringList;

const QHash<QString, TranslationRow> kTranslations{
    {"appTitle", {"نظام إدارة الأعمال العقارية", "Real Estate Business OS", "Gayrimenkul İşletim Sistemi", "Система управления недвижимостью", "Immobilien-Betriebssystem", "Sistema Gestionale Immobiliare", "Sistema de Gestión Inmobiliaria", "Système de Gestion Immobilière"}},
    {"dashboard", {"لوحة التحكم", "Dashboard", "Kontrol Paneli", "Панель управления", "Übersicht", "Pannello", "Panel", "Tableau de bord"}},
    {"leads", {"العملاء المحتملون", "Leads", "Potansiyel Müşteriler", "Лиды", "Interessenten", "Contatti", "Clientes potenciales", "Prospects"}},
    {"inventory", {"الوحدات والمخزون", "Inventory", "Envanter", "Объекты", "Bestand", "Inventario", "Inventario", "Inventaire"}},
    {"appointments", {"المعاينات", "Viewings", "Görüşmeler", "Показы", "Besichtigungen", "Visite", "Visitas", "Visites"}},
    {"finance", {"العقود والتحصيل", "Contracts & Finance", "Sözleşmeler ve Finans", "Договоры и финансы", "Verträge & Finanzen", "Contratti e Finanza", "Contratos y Finanzas", "Contrats et finances"}},
    {"enterpriseCrm", {"مركز إدارة العملاء", "Enterprise CRM", "Kurumsal CRM", "Корпоративная CRM", "Unternehmens-CRM", "CRM Aziendale", "CRM Empresarial", "CRM d’entreprise"}},
    {"customerTimeline", {"السجل الموحد للعميل", "Customer Timeline", "Müşteri Zaman Çizelgesi", "История клиента", "Kundenverlauf", "Cronologia Cliente", "Historial del Cliente", "Parcours Client"}},
    {"proposals", {"العروض", "Proposals", "Teklifler", "Предложения", "Angebote", "Proposte", "Propuestas", "Propositions"}},
    {"invoices", {"الفواتير", "Invoices", "Faturalar", "Счета", "Rechnungen", "Fatture", "Facturas", "Factures"}},
    {"payments", {"المدفوعات", "Payments", "Ödemeler", "Платежи", "Zahlungen", "Pagamenti", "Pagos", "Paiements"}},
    {"expenses", {"المصروفات", "Expenses", "Giderler", "Расходы", "Ausgaben", "Spese", "Gastos", "Dépenses"}},
    {"tickets", {"تذاكر الدعم", "Support Tickets", "Destek Talepleri", "Заявки поддержки", "Support-Tickets", "Ticket di Supporto", "Tickets de Soporte", "Tickets d’assistance"}},
    {"reminders", {"التذكيرات", "Reminders", "Hatırlatıcılar", "Напоминания", "Erinnerungen", "Promemoria", "Recordatorios", "Rappels"}},
    {"receivables", {"مبالغ مستحقة", "Receivables", "Alacaklar", "Дебиторская задолженность", "Forderungen", "Crediti", "Cuentas por cobrar", "Créances"}},
    {"acceptedProposals", {"عروض مقبولة", "Accepted proposals", "Kabul Edilen Teklifler", "Принятые предложения", "Angenommene Angebote", "Proposte Accettate", "Propuestas Aceptadas", "Propositions acceptées"}},
    {"openInvoices", {"فواتير مفتوحة", "Open invoices", "Açık Faturalar", "Открытые счета", "Offene Rechnungen", "Fatture Aperte", "Facturas Abiertas", "Factures ouvertes"}},
    {"openTickets", {"تذاكر مفتوحة", "Open tickets", "Açık Talepler", "Открытые заявки", "Offene Tickets", "Ticket Aperti", "Tickets Abiertos", "Tickets ouverts"}},
    {"pendingReminders", {"تذكيرات معلقة", "Pending reminders", "Bekleyen Hatırlatıcılar", "Ожидающие напоминания", "Ausstehende Erinnerungen", "Promemoria in Attesa", "Recordatorios Pendientes", "Rappels en attente"}},
    {"timelineSelectLead", {"اختر العميل لعرض مساره الكامل", "Select a lead to view the complete journey", "Tam süreci görmek için müşteri seçin", "Выберите лида для просмотра истории", "Interessenten für vollständigen Verlauf wählen", "Seleziona un contatto per il percorso completo", "Selecciona un cliente para ver todo el recorrido", "Sélectionnez un prospect pour voir son parcours"}},
    {"inbox", {"المحادثات", "Inbox", "Gelen Kutusu", "Сообщения", "Posteingang", "Posta in Arrivo", "Bandeja de Entrada", "Boîte de réception"}},
    {"knowledge", {"قاعدة المعرفة", "Knowledge Base", "Bilgi Bankası", "База знаний", "Wissensdatenbank", "Base di Conoscenza", "Base de Conocimiento", "Base de connaissances"}},
    {"tasks", {"المهام والمتابعة", "Tasks & Follow-up", "Görevler ve Takip", "Задачи и контроль", "Aufgaben & Nachverfolgung", "Attività e Follow-up", "Tareas y Seguimiento", "Tâches et suivi"}},
    {"team", {"الفريق والصلاحيات", "Team & Roles", "Ekip ve Roller", "Команда и роли", "Team & Rollen", "Team e Ruoli", "Equipo y Roles", "Équipe et rôles"}},
    {"settings", {"إعدادات الشركة", "Company Settings", "Şirket Ayarları", "Настройки компании", "Unternehmenseinstellungen", "Impostazioni Azienda", "Configuración de la Empresa", "Paramètres de l’entreprise"}},
    {"ai", {"مساعد المبيعات الذكي", "AI Sales Copilot", "Yapay Zekâ Satış Asistanı", "ИИ-ассистент продаж", "KI-Vertriebsassistent", "Assistente Vendite IA", "Asistente de Ventas IA", "Assistant commercial IA"}},
    {"seo", {"تحسين الظهور", "SEO Autopilot", "SEO Otomasyonu", "SEO Автопилот", "SEO-Autopilot", "Pilota Automatico SEO", "Piloto Automático SEO", "Pilote automatique SEO"}},
    {"growth", {"النمو والإسناد", "Growth & Attribution", "Büyüme ve Atıf", "Рост и атрибуция", "Wachstum & Attribution", "Crescita e Attribuzione", "Crecimiento y Atribución", "Croissance et attribution"}},
    {"automation", {"استوديو الأتمتة", "Automation Studio", "Otomasyon Stüdyosu", "Студия автоматизации", "Automatisierungsstudio", "Studio Automazione", "Estudio de Automatización", "Studio d’automatisation"}},
    {"about", {"حول النظام", "About System", "Sistem Hakkında", "О системе", "Über das System", "Informazioni sul Sistema", "Acerca del Sistema", "À propos du système"}},
    {"company", {"عن الشركة", "About Company", "Şirket Hakkında", "О компании", "Über das Unternehmen", "Informazioni sull’Azienda", "Acerca de la Empresa", "À propos de l’entreprise"}},
    {"legal", {"الاتفاقية والترخيص", "Agreement & License", "Sözleşme ve Lisans", "Соглашение и лицензия", "Vereinbarung & Lizenz", "Accordo e Licenza", "Acuerdo y Licencia", "Contrat et licence"}},
    {"license", {"تفعيل الترخيص", "License Activation", "Lisans Aktivasyonu", "Активация лицензии", "Lizenzaktivierung", "Attivazione Licenza", "Activación de Licencia", "Activation de licence"}},
    {"back", {"رجوع", "Back", "Geri", "Назад", "Zurück", "Indietro", "Atrás", "Retour"}},
    {"refresh", {"تحديث", "Refresh", "Yenile", "Обновить", "Aktualisieren", "Aggiorna", "Actualizar", "Actualiser"}},
    {"signIn", {"تسجيل الدخول", "Sign in", "Giriş Yap", "Войти", "Anmelden", "Accedi", "Iniciar sesión", "Se connecter"}},
    {"companyId", {"معرّف الشركة", "Company identifier", "Şirket Kimliği", "Идентификатор компании", "Unternehmenskennung", "Identificativo Azienda", "Identificador de Empresa", "Identifiant de l’entreprise"}},
    {"email", {"البريد الإلكتروني", "Email", "E-posta", "Эл. почта", "E-Mail", "Email", "Correo", "E-mail"}},
    {"password", {"كلمة المرور", "Password", "Şifre", "Пароль", "Passwort", "Password", "Contraseña", "Mot de passe"}},
    {"secureWorkspace", {"مساحة عمل آمنة", "SECURE WORKSPACE", "GÜVENLİ ÇALIŞMA ALANI", "ЗАЩИЩЁННОЕ ПРОСТРАНСТВО", "SICHERER ARBEITSBEREICH", "AREA DI LAVORO SICURA", "ESPACIO DE TRABAJO SEGURO", "ESPACE DE TRAVAIL SÉCURISÉ"}},
    {"loginTitle", {"الدخول إلى مركز الإدارة", "Enter the command center", "Yönetim Merkezine Girin", "Вход в центр управления", "Management-Center öffnen", "Accedi al Centro di Gestione", "Entrar al Centro de Gestión", "Accéder au centre de gestion"}},
    {"loginText", {"استخدم بيانات شركتك للوصول إلى مساحة العمل.", "Use your company credentials to access the workspace.", "Çalışma alanına erişmek için şirket bilgilerinizi kullanın.", "Используйте данные компании для входа.", "Verwenden Sie Ihre Unternehmensdaten für den Zugriff.", "Usa le credenziali aziendali per accedere.", "Usa las credenciales de tu empresa para acceder.", "Utilisez les identifiants de votre entreprise."}},
    {"liveData", {"بيانات حية", "LIVE DATA", "CANLI VERİ", "АКТУАЛЬНЫЕ ДАННЫЕ", "LIVE-DATEN", "DATI LIVE", "DATOS EN VIVO", "DONNÉES EN DIRECT"}},
    {"totalLeads", {"إجمالي العملاء", "Total leads", "Toplam Müşteri", "Всего лидов", "Interessenten gesamt", "Contatti Totali", "Total de Clientes", "Total prospects"}},
    {"hotLeads", {"عملاء جاهزون", "Hot leads", "Sıcak Müşteriler", "Горячие лиды", "Heiße Leads", "Contatti Caldi", "Clientes Prioritarios", "Prospects prioritaires"}},
    {"availableUnits", {"وحدات متاحة", "Available units", "Mevcut Birimler", "Доступные объекты", "Verfügbare Einheiten", "Unità Disponibili", "Unidades Disponibles", "Unités disponibles"}},
    {"viewings", {"إجمالي المعاينات", "Total viewings", "Toplam Görüşme", "Всего показов", "Besichtigungen gesamt", "Visite Totali", "Total de Visitas", "Total des visites"}},
    {"reservations", {"حجوزات نشطة", "Active reservations", "Aktif Rezervasyonlar", "Активные бронирования", "Aktive Reservierungen", "Prenotazioni Attive", "Reservas Activas", "Réservations actives"}},
    {"nativeMigration", {"مساحة العمل", "Business workspace", "İş Alanı", "Рабочее пространство", "Arbeitsbereich", "Area di Lavoro", "Espacio de Trabajo", "Espace de travail"}},
    {"migrationNotice", {"هذه الوحدة قيد التجهيز ضمن مساحة العمل الموحدة.", "This module is being prepared within the unified workspace.", "Bu modül birleşik çalışma alanında hazırlanıyor.", "Этот модуль готовится в едином рабочем пространстве.", "Dieses Modul wird im einheitlichen Arbeitsbereich vorbereitet.", "Questo modulo è in preparazione nell’area unificata.", "Este módulo se está preparando en el espacio unificado.", "Ce module est en préparation dans l’espace unifié."}},
};

const QHash<QString, TranslationRow> kPhrases{
    {"Add", {"Ekle", "Добавить", "Hinzufügen", "Aggiungi", "Añadir", "Ajouter"}},
    {"Save", {"Kaydet", "Сохранить", "Speichern", "Salva", "Guardar", "Enregistrer"}},
    {"Cancel", {"İptal", "Отмена", "Abbrechen", "Annulla", "Cancelar", "Annuler"}},
    {"Create", {"Oluştur", "Создать", "Erstellen", "Crea", "Crear", "Créer"}},
    {"Edit", {"Düzenle", "Изменить", "Bearbeiten", "Modifica", "Editar", "Modifier"}},
    {"Complete", {"Tamamla", "Завершить", "Abschließen", "Completa", "Completar", "Terminer"}},
    {"Open", {"Aç", "Открыть", "Öffnen", "Apri", "Abrir", "Ouvrir"}},
    {"Status", {"Durum", "Статус", "Status", "Stato", "Estado", "Statut"}},
    {"Actions", {"İşlemler", "Действия", "Aktionen", "Azioni", "Acciones", "Actions"}},
    {"Name", {"Ad", "Имя", "Name", "Nome", "Nombre", "Nom"}},
    {"Description", {"Açıklama", "Описание", "Beschreibung", "Descrizione", "Descripción", "Description"}},
    {"Phone", {"Telefon", "Телефон", "Telefon", "Telefono", "Teléfono", "Téléphone"}},
    {"City", {"Şehir", "Город", "Stadt", "Città", "Ciudad", "Ville"}},
    {"Budget", {"Bütçe", "Бюджет", "Budget", "Budget", "Presupuesto", "Budget"}},
    {"Price", {"Fiyat", "Цена", "Preis", "Prezzo", "Precio", "Prix"}},
    {"Notes", {"Notlar", "Примечания", "Notizen", "Note", "Notas", "Notes"}},
    {"Projects", {"Projeler", "Проекты", "Projekte", "Progetti", "Proyectos", "Projets"}},
    {"Units", {"Birimler", "Объекты", "Einheiten", "Unità", "Unidades", "Unités"}},
    {"Reservations", {"Rezervasyonlar", "Бронирования", "Reservierungen", "Prenotazioni", "Reservas", "Réservations"}},
    {"Contracts", {"Sözleşmeler", "Договоры", "Verträge", "Contratti", "Contratos", "Contrats"}},
    {"Appointments", {"Görüşmeler", "Встречи", "Termine", "Appuntamenti", "Citas", "Rendez-vous"}},
    {"Conversations", {"Görüşmeler", "Диалоги", "Unterhaltungen", "Conversazioni", "Conversaciones", "Conversations"}},
    {"Documents", {"Belgeler", "Документы", "Dokumente", "Documenti", "Documentos", "Documents"}},
    {"Website", {"Web Sitesi", "Сайт", "Website", "Sito Web", "Sitio Web", "Site web"}},
    {"Company name", {"Şirket Adı", "Название компании", "Unternehmensname", "Nome Azienda", "Nombre de Empresa", "Nom de l’entreprise"}},
    {"Company Identity", {"Şirket Kimliği", "Фирменный стиль", "Unternehmensidentität", "Identità Aziendale", "Identidad de Empresa", "Identité de l’entreprise"}},
    {"Contact the company", {"Şirketle İletişim", "Связаться с компанией", "Unternehmen kontaktieren", "Contatta l’Azienda", "Contactar con la Empresa", "Contacter l’entreprise"}},
    {"Save Changes", {"Değişiklikleri Kaydet", "Сохранить изменения", "Änderungen speichern", "Salva Modifiche", "Guardar Cambios", "Enregistrer les modifications"}},
    {"Choose Logo", {"Logo Seç", "Выбрать логотип", "Logo wählen", "Scegli Logo", "Elegir Logo", "Choisir le logo"}},
    {"Choose Cover", {"Kapak Seç", "Выбрать обложку", "Titelbild wählen", "Scegli Copertina", "Elegir Portada", "Choisir la couverture"}},
    {"Remove Logo", {"Logoyu Kaldır", "Удалить логотип", "Logo entfernen", "Rimuovi Logo", "Eliminar Logo", "Supprimer le logo"}},
    {"Remove Cover", {"Kapağı Kaldır", "Удалить обложку", "Titelbild entfernen", "Rimuovi Copertina", "Eliminar Portada", "Supprimer la couverture"}},
    {"Loading", {"Yükleniyor", "Загрузка", "Wird geladen", "Caricamento", "Cargando", "Chargement"}},
};

int languageIndex(const QString &language)
{
    const int index = kLanguageCodes.indexOf(language);
    return index < 0 ? 1 : index;
}
}

AppState::AppState(QObject *parent) : QObject(parent)
{
    QSettings settings;
    const QString savedLanguage = settings.value(QStringLiteral("appearance/language"), QStringLiteral("en")).toString().toLower();
    const QString savedTheme = settings.value(QStringLiteral("appearance/theme"), QStringLiteral("neon")).toString().toLower();
    m_language = kLanguageCodes.contains(savedLanguage) ? savedLanguage : QStringLiteral("en");
    m_theme = kThemeCodes.contains(savedTheme) ? savedTheme : QStringLiteral("neon");
    m_licenseGateAccepted = settings.value(QStringLiteral("onboarding/license-gate-version")).toString() == kLicenseGateVersion;
    m_clock.setInterval(1000);
    connect(&m_clock, &QTimer::timeout, this, &AppState::updateClock);
    updateClock();
    m_clock.start();
}

QString AppState::language() const { return m_language; }

void AppState::setLanguage(const QString &language)
{
    const QString normalized = language.toLower();
    const QString accepted = kLanguageCodes.contains(normalized) ? normalized : QStringLiteral("en");
    if (m_language == accepted)
        return;
    m_language = accepted;
    QSettings().setValue(QStringLiteral("appearance/language"), m_language);
    updateClock();
    emit languageChanged();
}

bool AppState::rtl() const { return m_language == QStringLiteral("ar"); }
QStringList AppState::languageCodes() const { return kLanguageCodes; }
QStringList AppState::languageNames() const { return kLanguageNames; }
QString AppState::theme() const { return m_theme; }

void AppState::setTheme(const QString &theme)
{
    const QString normalized = theme.toLower();
    const QString accepted = kThemeCodes.contains(normalized) ? normalized : QStringLiteral("neon");
    if (m_theme == accepted)
        return;
    m_theme = accepted;
    QSettings().setValue(QStringLiteral("appearance/theme"), m_theme);
    emit themeChanged();
}

QStringList AppState::themeCodes() const { return kThemeCodes; }
QStringList AppState::themeNames() const { return kThemeNames; }
bool AppState::licenseGateAccepted() const { return m_licenseGateAccepted; }
QString AppState::currentPage() const { return m_currentPage; }
QString AppState::currentTime() const { return m_currentTime; }
QString AppState::currentDate() const { return m_currentDate; }

QString AppState::t(const QString &key) const
{
    const auto it = kTranslations.constFind(key);
    if (it == kTranslations.constEnd())
        return key;
    const int index = languageIndex(m_language);
    return index < it.value().size() ? it.value().at(index) : it.value().value(1, key);
}

QString AppState::localize(const QString &language, const QString &arabic, const QString &english) const
{
    const QString normalized = kLanguageCodes.contains(language) ? language : QStringLiteral("en");
    if (normalized == QStringLiteral("ar"))
        return arabic;
    if (normalized == QStringLiteral("en"))
        return english;
    const auto it = kPhrases.constFind(english);
    if (it == kPhrases.constEnd())
        return english;
    const int phraseIndex = languageIndex(normalized) - 2;
    return phraseIndex >= 0 && phraseIndex < it.value().size() ? it.value().at(phraseIndex) : english;
}

void AppState::navigate(const QString &page)
{
    if (page.isEmpty() || page == m_currentPage)
        return;
    m_history.append(m_currentPage);
    if (m_history.size() > 32)
        m_history.removeFirst();
    m_currentPage = page;
    emit currentPageChanged();
}

void AppState::goBack()
{
    if (m_history.isEmpty()) {
        if (m_currentPage != QStringLiteral("dashboard")) {
            m_currentPage = QStringLiteral("dashboard");
            emit currentPageChanged();
        }
        return;
    }
    m_currentPage = m_history.takeLast();
    emit currentPageChanged();
}

void AppState::resetNavigation()
{
    m_history.clear();
    if (m_currentPage != QStringLiteral("dashboard")) {
        m_currentPage = QStringLiteral("dashboard");
        emit currentPageChanged();
    }
}

void AppState::acceptCurrentLicense()
{
    if (m_licenseGateAccepted)
        return;
    QSettings().setValue(QStringLiteral("onboarding/license-gate-version"), kLicenseGateVersion);
    m_licenseGateAccepted = true;
    emit licenseGateAcceptedChanged();
}

void AppState::updateClock()
{
    const QDateTime now = QDateTime::currentDateTime();
    QLocale dateLocale;
    if (m_language == "ar") dateLocale = QLocale(QLocale::Arabic);
    else if (m_language == "tr") dateLocale = QLocale(QLocale::Turkish);
    else if (m_language == "ru") dateLocale = QLocale(QLocale::Russian);
    else if (m_language == "de") dateLocale = QLocale(QLocale::German);
    else if (m_language == "it") dateLocale = QLocale(QLocale::Italian);
    else if (m_language == "es") dateLocale = QLocale(QLocale::Spanish);
    else if (m_language == "fr") dateLocale = QLocale(QLocale::French);
    else dateLocale = QLocale(QLocale::English);
    m_currentTime = QLocale(QLocale::English).toString(now.time(), QStringLiteral("HH:mm:ss"));
    m_currentDate = dateLocale.toString(now.date(), QStringLiteral("ddd dd MMM"));
    emit clockChanged();
}
