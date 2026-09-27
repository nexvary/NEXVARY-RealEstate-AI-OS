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
#include <QDir>
#include <QTcpServer>
#include <QHostAddress>

int main(int argc, char *argv[])
{
    QGuiApplication app(argc, argv);
    QGuiApplication::setOrganizationName(QStringLiteral("NEXVARY"));
    QGuiApplication::setOrganizationDomain(QStringLiteral("nexvary.com"));
    QGuiApplication::setApplicationName(QStringLiteral("NEXVARY RealEstate AI OS"));
    QGuiApplication::setApplicationVersion(QStringLiteral("2.0.0-native-preview"));

    QQuickStyle::setStyle(QStringLiteral("Basic"));

    QCommandLineParser parser;
    parser.setApplicationDescription(QStringLiteral("NEXVARY RealEstate AI OS — Qt 6 native migration shell"));
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
            QStringLiteral("NEXVARY-RealEstate-API.exe");
#else
            QStringLiteral("NEXVARY-RealEstate-API");
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

    engine.loadFromModule(QStringLiteral("Nexvary.RealEstate"), QStringLiteral("Main"));
    if (engine.rootObjects().isEmpty())
        return 2;

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
        QTimer::singleShot(1800, &app, [&app] {
            app.exit(0);
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
