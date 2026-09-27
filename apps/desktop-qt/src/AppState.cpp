#include "AppState.hpp"

#include <QDateTime>
#include <QLocale>

namespace {
using TranslationPair = QPair<QString, QString>;

const QHash<QString, TranslationPair> kTranslations{
    {"appTitle", {"NEXVARY RealEstate AI OS", "NEXVARY RealEstate AI OS"}},
    {"dashboard", {"لوحة التحكم", "Dashboard"}},
    {"leads", {"العملاء المحتملون", "Leads"}},
    {"inventory", {"الوحدات والمخزون", "Inventory"}},
    {"appointments", {"المعاينات", "Viewings"}},
    {"finance", {"العقود والتحصيل", "Contracts & Finance"}},
    {"inbox", {"المحادثات", "Inbox"}},
    {"knowledge", {"قاعدة المعرفة", "Knowledge Base"}},
    {"tasks", {"المهام والمتابعة", "Tasks & Follow-up"}},
    {"team", {"الفريق والصلاحيات", "Team & Roles"}},
    {"settings", {"إعدادات الشركة", "Company Settings"}},
    {"ai", {"مساعد الذكاء الاصطناعي", "AI Sales Copilot"}},
    {"seo", {"SEO Autopilot", "SEO Autopilot"}},
    {"growth", {"النمو والإسناد", "Growth & Attribution"}},
    {"automation", {"Automation Studio", "Automation Studio"}},
    {"about", {"عن النظام", "About System"}},
    {"company", {"عن الشركة", "About Company"}},
    {"back", {"رجوع", "Back"}},
    {"refresh", {"تحديث", "Refresh"}},
    {"signIn", {"تسجيل الدخول", "Sign in"}},
    {"companyId", {"معرّف الشركة", "Company identifier"}},
    {"email", {"البريد الإلكتروني", "Email"}},
    {"password", {"كلمة المرور", "Password"}},
    {"secureWorkspace", {"مساحة عمل آمنة", "SECURE WORKSPACE"}},
    {"loginTitle", {"الدخول إلى مركز القيادة", "Enter the command center"}},
    {"loginText", {"استخدم بيانات شركتك للوصول إلى مساحة العمل المعزولة.", "Use your company credentials to access the isolated workspace."}},
    {"liveData", {"بيانات حية", "LIVE DATA"}},
    {"totalLeads", {"إجمالي العملاء", "Total leads"}},
    {"hotLeads", {"عملاء جاهزون", "Hot leads"}},
    {"availableUnits", {"وحدات متاحة", "Available units"}},
    {"viewings", {"إجمالي المعاينات", "Total viewings"}},
    {"reservations", {"حجوزات نشطة", "Active reservations"}},
    {"nativeMigration", {"واجهة Qt الأصلية", "Native Qt workspace"}},
    {"migrationNotice", {"يتم نقل هذه الوحدة إلى QML مع إبقاء النظام الحالي متاحًا حتى اكتمال التكافؤ الوظيفي.", "This module is being migrated to QML while the current system remains available until feature parity."}},
};
}

AppState::AppState(QObject *parent)
    : QObject(parent)
{
    m_clock.setInterval(1000);
    connect(&m_clock, &QTimer::timeout, this, &AppState::updateClock);
    updateClock();
    m_clock.start();
}

QString AppState::language() const
{
    return m_language;
}

void AppState::setLanguage(const QString &language)
{
    const QString normalized = language.toLower() == QStringLiteral("ar")
        ? QStringLiteral("ar")
        : QStringLiteral("en");
    if (m_language == normalized)
        return;

    m_language = normalized;
    updateClock();
    emit languageChanged();
}

bool AppState::rtl() const
{
    return m_language == QStringLiteral("ar");
}

QString AppState::currentPage() const
{
    return m_currentPage;
}

QString AppState::currentTime() const
{
    return m_currentTime;
}

QString AppState::currentDate() const
{
    return m_currentDate;
}

QString AppState::t(const QString &key) const
{
    const auto it = kTranslations.constFind(key);
    if (it == kTranslations.constEnd())
        return key;
    return rtl() ? it.value().first : it.value().second;
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

void AppState::updateClock()
{
    const QDateTime now = QDateTime::currentDateTime();
    const QLocale dateLocale(rtl() ? QLocale::Arabic : QLocale::English);
    const QLocale timeLocale(QLocale::English);

    m_currentTime = timeLocale.toString(now.time(), QStringLiteral("HH:mm:ss"));
    m_currentDate = dateLocale.toString(now.date(), QStringLiteral("ddd dd MMM"));
    emit clockChanged();
}
