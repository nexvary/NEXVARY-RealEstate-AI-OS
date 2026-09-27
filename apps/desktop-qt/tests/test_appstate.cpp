#include "AppState.hpp"

#include <QtTest/QtTest>

class AppStateTest final : public QObject
{
    Q_OBJECT

private slots:
    void defaultsToArabicRtl()
    {
        AppState state;
        QCOMPARE(state.language(), QStringLiteral("ar"));
        QVERIFY(state.rtl());
        QCOMPARE(state.currentPage(), QStringLiteral("dashboard"));
        QCOMPARE(state.t(QStringLiteral("dashboard")), QStringLiteral("لوحة التحكم"));
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
