#include "ApiClient.hpp"
#include "AppState.hpp"

#include <QCommandLineOption>
#include <QCommandLineParser>
#include <QGuiApplication>
#include <QImage>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include <QQuickStyle>
#include <QQuickWindow>
#include <QTimer>
#include <QProcess>
#include <QFileInfo>
#include <QFile>
#include <QTextStream>
#include <QQmlError>
#include <QDir>
#include <QTcpServer>
#include <QHostAddress>
#include <QIcon>

int main(int argc, char *argv[])
{
    QGuiApplication app(argc, argv);
    QGuiApplication::setOrganizationName(QStringLiteral("FG Machines"));
    QGuiApplication::setOrganizationDomain(QStringLiteral("fgmachines.local"));
    QGuiApplication::setApplicationName(QStringLiteral("FG Machines Real Estate OS"));
    QGuiApplication::setApplicationVersion(QStringLiteral("2.0.2"));
    QGuiApplication::setWindowIcon(QIcon(QStringLiteral(":/qt/qml/Nexvary/RealEstate/assets/nexvary-mark.svg")));

    QQuickStyle::setStyle(QStringLiteral("Basic"));

    QCommandLineParser parser;
    parser.setApplicationDescription(QStringLiteral("FG Machines Real Estate OS — native desktop"));
    parser.addHelpOption();
    parser.addVersionOption();

    QCommandLineOption languageOption(
        QStringList{QStringLiteral("language")},
        QStringLiteral("Initial UI language (ar/en)."),
        QStringLiteral("code"),
        QStringLiteral("ar"));
    QCommandLineOption apiUrlOption(
        QStringList{QStringLiteral("api-url")},
        QStringLiteral("FastAPI base URL."),
        QStringLiteral("url"));
    QCommandLineOption screenshotOption(
        QStringList{QStringLiteral("screenshot")},
        QStringLiteral("Capture the native shell then exit."),
        QStringLiteral("path"));
    QCommandLineOption smokeTestOption(
        QStringList{QStringLiteral("smoke-test")},
        QStringLiteral("Load the packaged QML runtime, wait briefly, then exit successfully."));
    QCommandLineOption widthOption(
        QStringList{QStringLiteral("width")},
        QStringLiteral("Window width."),
        QStringLiteral("pixels"),
        QStringLiteral("1600"));
    QCommandLineOption heightOption(
        QStringList{QStringLiteral("height")},
        QStringLiteral("Window height."),
        QStringLiteral("pixels"),
        QStringLiteral("900"));

    parser.addOption(languageOption);
    parser.addOption(apiUrlOption);
    parser.addOption(screenshotOption);
    parser.addOption(smokeTestOption);
    parser.addOption(widthOption);
    parser.addOption(heightOption);
    parser.process(app);

    AppState state;
    state.setLanguage(parser.value(languageOption));

    ApiClient api;
    QProcess backendProcess;
    QString resolvedApiUrl;

    if (parser.isSet(apiUrlOption)) {
        resolvedApiUrl = parser.value(apiUrlOption);
    } else {
        const QString sidecarName =
#ifdef Q_OS_WIN
            QStringLiteral("FG-Machines-RealEstate-Service.exe");
#else
            QStringLiteral("FG-Machines-RealEstate-Service");
#endif
        const QString sidecarPath = QDir(QCoreApplication::applicationDirPath()).filePath(sidecarName);
        if (QFileInfo::exists(sidecarPath)) {
            QTcpServer probe;
            if (probe.listen(QHostAddress::LocalHost, 0)) {
                const quint16 port = probe.serverPort();
                probe.close();

                resolvedApiUrl = QStringLiteral("http://127.0.0.1:%1").arg(port);
                backendProcess.setProgram(sidecarPath);
                backendProcess.setArguments({QStringLiteral("--port"), QString::number(port)});
                backendProcess.setProcessChannelMode(QProcess::ForwardedErrorChannel);
                backendProcess.start();
            }
        }
    }

    if (!resolvedApiUrl.isEmpty())
        api.setBaseUrl(resolvedApiUrl);

    QQmlApplicationEngine engine;
    engine.rootContext()->setContextProperty(QStringLiteral("appState"), &state);
    engine.rootContext()->setContextProperty(QStringLiteral("apiClient"), &api);

    QStringList qmlDiagnostics;
    QObject::connect(&engine, &QQmlApplicationEngine::warnings, &app, [&qmlDiagnostics](const QList<QQmlError> &warnings) {
        for (const QQmlError &warning : warnings)
            qmlDiagnostics.append(warning.toString());
    });

    engine.loadFromModule(QStringLiteral("Nexvary.RealEstate"), QStringLiteral("Main"));
    if (engine.rootObjects().isEmpty()) {
        const QString logPath = qEnvironmentVariable("NEXVARY_QT_LOG");
        if (!logPath.isEmpty()) {
            QFile logFile(logPath);
            if (logFile.open(QIODevice::WriteOnly | QIODevice::Text)) {
                QTextStream stream(&logFile);
                stream << "FG Machines Qt QML startup failure\n";
                stream << "applicationDir=" << QCoreApplication::applicationDirPath() << "\n";
                stream << "importPaths=" << engine.importPathList().join(QStringLiteral(";")) << "\n";
                for (const QString &line : qmlDiagnostics)
                    stream << line << "\n";
            }
        }
        return 2;
    }

    auto *window = qobject_cast<QQuickWindow *>(engine.rootObjects().constFirst());
    if (!window)
        return 3;

    bool widthOk = false;
    bool heightOk = false;
    const int requestedWidth = parser.value(widthOption).toInt(&widthOk);
    const int requestedHeight = parser.value(heightOption).toInt(&heightOk);
    if (widthOk && requestedWidth > 0)
        window->setWidth(requestedWidth);
    if (heightOk && requestedHeight > 0)
        window->setHeight(requestedHeight);

    api.health();

    QObject::connect(&app, &QCoreApplication::aboutToQuit, [&backendProcess] {
        if (backendProcess.state() != QProcess::NotRunning) {
            backendProcess.terminate();
            if (!backendProcess.waitForFinished(2500))
                backendProcess.kill();
        }
    });

    if (parser.isSet(smokeTestOption)) {
        auto *smokeProbe = new QTimer(&app);
        smokeProbe->setInterval(250);
        QObject::connect(smokeProbe, &QTimer::timeout, &app, [&api, &app, smokeProbe] {
            if (api.healthStatus() == QStringLiteral("ok") && api.setupKnown()) {
                smokeProbe->stop();
                app.exit(0);
            }
        });
        smokeProbe->start();

        QTimer::singleShot(12000, &app, [&api, &app, smokeProbe] {
            if (smokeProbe->isActive()) {
                smokeProbe->stop();
                app.exit(api.healthStatus() == QStringLiteral("ok") ? 6 : 5);
            }
        });
    } else if (parser.isSet(screenshotOption)) {
        const QString path = parser.value(screenshotOption);
        QTimer::singleShot(1500, &app, [window, path, &app] {
            const QImage image = window->grabWindow();
            const bool saved = !image.isNull() && image.save(path);
            app.exit(saved ? 0 : 4);
        });
    }

    return app.exec();
}
