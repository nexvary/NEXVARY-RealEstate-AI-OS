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
    Q_PROPERTY(QString currentPage READ currentPage NOTIFY currentPageChanged)
    Q_PROPERTY(QString currentTime READ currentTime NOTIFY clockChanged)
    Q_PROPERTY(QString currentDate READ currentDate NOTIFY clockChanged)

public:
    explicit AppState(QObject *parent = nullptr);

    QString language() const;
    void setLanguage(const QString &language);
    bool rtl() const;

    QString currentPage() const;
    QString currentTime() const;
    QString currentDate() const;

    Q_INVOKABLE QString t(const QString &key) const;
    Q_INVOKABLE void navigate(const QString &page);
    Q_INVOKABLE void goBack();
    Q_INVOKABLE void resetNavigation();

signals:
    void languageChanged();
    void currentPageChanged();
    void clockChanged();

private:
    void updateClock();

    QString m_language{"ar"};
    QString m_currentPage{"dashboard"};
    QStringList m_history;
    QString m_currentTime;
    QString m_currentDate;
    QTimer m_clock;
};
