#include "AppState.hpp"

#include <QCoreApplication>
#include <QSettings>
#include <QStandardPaths>
#include <QtTest/QtTest>

class AppStateTest final : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase()
    {
        QStandardPaths::setTestModeEnabled(true);
        QCoreApplication::setOrganizationName(QStringLiteral("White Label Business Software Tests"));
        QCoreApplication::setApplicationName(QStringLiteral("Real Estate Business OS Tests"));
        QSettings().clear();
    }

    void init()
    {
        QSettings().clear();
    }

    void cleanupTestCase()
    {
        QSettings().clear();
    }

    void defaultsToEnglishLtr()
    {
        AppState state;
        QCOMPARE(state.language(), QStringLiteral("en"));
        QVERIFY(!state.rtl());
        QCOMPARE(state.currentPage(), QStringLiteral("dashboard"));
        QCOMPARE(state.t(QStringLiteral("dashboard")), QStringLiteral("Dashboard"));
        QCOMPARE(state.theme(), QStringLiteral("neon"));
    }

    void themeSelectionPersists()
    {
        AppState state;
        const QStringList themes{"neon", "blue", "green", "amber", "silver", "violet"};
        QCOMPARE(state.themeCodes(), themes);
        state.setTheme(QStringLiteral("amber"));
        QCOMPARE(state.theme(), QStringLiteral("amber"));

        AppState restored;
        QCOMPARE(restored.theme(), QStringLiteral("amber"));

        restored.setTheme(QStringLiteral("unsupported"));
        QCOMPARE(restored.theme(), QStringLiteral("neon"));
    }

    void languageSwitchesDirection()
    {
        AppState state;
        state.setLanguage(QStringLiteral("en"));
        QCOMPARE(state.language(), QStringLiteral("en"));
        QVERIFY(!state.rtl());
        QCOMPARE(state.t(QStringLiteral("dashboard")), QStringLiteral("Dashboard"));

        state.setLanguage(QStringLiteral("unsupported"));
        QCOMPARE(state.language(), QStringLiteral("en"));
    }

    void supportsAllRequestedLanguages()
    {
        AppState state;
        const QStringList codes{"ar", "en", "tr", "ru", "de", "it", "es", "fr"};
        QCOMPARE(state.languageCodes(), codes);
        for (const QString &code : codes) {
            state.setLanguage(code);
            QCOMPARE(state.language(), code);
            QVERIFY(!state.t(QStringLiteral("dashboard")).isEmpty());
            QVERIFY(!state.t(QStringLiteral("legal")).isEmpty());
        }
        state.setLanguage(QStringLiteral("de"));
        QCOMPARE(state.localize(QStringLiteral("de"), QStringLiteral("حفظ"), QStringLiteral("Save")), QStringLiteral("Speichern"));
    }

    void navigationKeepsBackStack()
    {
        AppState state;
        state.navigate(QStringLiteral("leads"));
        state.navigate(QStringLiteral("inventory"));
        QCOMPARE(state.currentPage(), QStringLiteral("inventory"));

        state.goBack();
        QCOMPARE(state.currentPage(), QStringLiteral("leads"));

        state.goBack();
        QCOMPARE(state.currentPage(), QStringLiteral("dashboard"));

        state.goBack();
        QCOMPARE(state.currentPage(), QStringLiteral("dashboard"));
    }
};

QTEST_MAIN(AppStateTest)
#include "test_appstate.moc"
