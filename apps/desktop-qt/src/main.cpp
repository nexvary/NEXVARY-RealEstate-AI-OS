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
    parser.addOption(widthOption);
    parser.addOption(heightOption);
    parser.process(app);

    AppState state;
    state.setLanguage(parser.value(languageOption));

    ApiClient api;
    if (parser.isSet(apiUrlOption))
        api.setBaseUrl(parser.value(apiUrlOption));

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

    if (parser.isSet(screenshotOption)) {
        const QString path = parser.value(screenshotOption);
        QTimer::singleShot(1500, &app, [window, path, &app] {
            const QImage image = window->grabWindow();
            const bool saved = !image.isNull() && image.save(path);
            app.exit(saved ? 0 : 4);
        });
    }

    return app.exec();
}
