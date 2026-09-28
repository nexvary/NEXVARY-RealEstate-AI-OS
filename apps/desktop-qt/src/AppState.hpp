#pragma once

#include <QObject>
#include <QHash>
#include <QString>
#include <QStringList>
#include <QTimer>

class AppState final : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QString language READ language WRITE setLanguage NOTIFY languageChanged)
    Q_PROPERTY(bool rtl READ rtl NOTIFY languageChanged)
    Q_PROPERTY(QStringList languageCodes READ languageCodes CONSTANT)
    Q_PROPERTY(QStringList languageNames READ languageNames CONSTANT)
    Q_PROPERTY(QString theme READ theme WRITE setTheme NOTIFY themeChanged)
    Q_PROPERTY(QStringList themeCodes READ themeCodes CONSTANT)
    Q_PROPERTY(QStringList themeNames READ themeNames CONSTANT)
    Q_PROPERTY(bool licenseGateAccepted READ licenseGateAccepted NOTIFY licenseGateAcceptedChanged)
    Q_PROPERTY(QString currentPage READ currentPage NOTIFY currentPageChanged)
    Q_PROPERTY(QString currentTime READ currentTime NOTIFY clockChanged)
    Q_PROPERTY(QString currentDate READ currentDate NOTIFY clockChanged)

public:
    explicit AppState(QObject *parent = nullptr);

    QString language() const;
    void setLanguage(const QString &language);
    bool rtl() const;
    QStringList languageCodes() const;
    QStringList languageNames() const;
    QString theme() const;
    void setTheme(const QString &theme);
    QStringList themeCodes() const;
    QStringList themeNames() const;
    bool licenseGateAccepted() const;

    QString currentPage() const;
    QString currentTime() const;
    QString currentDate() const;

    Q_INVOKABLE QString t(const QString &key) const;
    Q_INVOKABLE QString localize(const QString &language, const QString &arabic, const QString &english) const;
    Q_INVOKABLE void navigate(const QString &page);
    Q_INVOKABLE void goBack();
    Q_INVOKABLE void resetNavigation();
    Q_INVOKABLE void acceptCurrentLicense();

signals:
    void languageChanged();
    void themeChanged();
    void licenseGateAcceptedChanged();
    void currentPageChanged();
    void clockChanged();

private:
    void updateClock();

    QString m_language{"en"};
    QString m_theme{"neon"};
    bool m_licenseGateAccepted{false};
    QString m_currentPage{"dashboard"};
    QStringList m_history;
    QString m_currentTime;
    QString m_currentDate;
    QTimer m_clock;
};
