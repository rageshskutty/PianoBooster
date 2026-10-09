/*********************************************************************************/
/*!
@file           AiMentorBridge.cpp

@brief          Bridge implementation connecting PianoBooster with the offline AI Mentor.
*/
/*********************************************************************************/

#include "AiMentorBridge.h"
#include <QCoreApplication>
#include <QDir>
#include <QFileInfo>
#include <cmath>
#include <iostream>

AiMentorBridge::AiMentorBridge(QObject *parent, const QString &serverUrl)
    : QObject(parent),
      m_serverUrl(serverUrl),
      m_connected(false),
      m_serverProcess(nullptr),
      m_sessionTotalOffsetMs(0),
      m_sessionOffsetCount(0)
{
    m_netManager = new QNetworkAccessManager(this);
    connect(m_netManager, &QNetworkAccessManager::finished, this, &AiMentorBridge::onNetworkReplyFinished);

    m_heartbeatTimer = new QTimer(this);
    connect(m_heartbeatTimer, &QTimer::timeout, this, &AiMentorBridge::onHeartbeatTimer);
    m_heartbeatTimer->start(8000); // Check status every 8 seconds

    // Initial check
    checkServerStatus();
}

AiMentorBridge::~AiMentorBridge()
{
    if (m_serverProcess && m_serverProcess->state() != QProcess::NotRunning)
    {
        m_serverProcess->terminate();
        m_serverProcess->waitForFinished(1000);
    }
}

void AiMentorBridge::onHeartbeatTimer()
{
    checkServerStatus();
}

void AiMentorBridge::ensureServerRunning()
{
    if (m_connected)
        return;

    // Locate ai_mentor/server.py
    QString appDir = QCoreApplication::applicationDirPath();
    QStringList candidates = {
        appDir + "/ai_mentor/server.py",
        appDir + "/../ai_mentor/server.py",
        QDir::currentPath() + "/ai_mentor/server.py",
        "d:/Git/PianoBooster/PianoBooster/ai_mentor/server.py"
    };

    QString scriptPath;
    for (const QString &p : candidates)
    {
        if (QFile::exists(p))
        {
            scriptPath = QFileInfo(p).absoluteFilePath();
            break;
        }
    }

    if (scriptPath.isEmpty())
        return;

    if (!m_serverProcess)
    {
        m_serverProcess = new QProcess(this);
    }

    if (m_serverProcess->state() == QProcess::NotRunning)
    {
        QStringList args;
        args << scriptPath;
        m_serverProcess->start("python", args);
    }
}

void AiMentorBridge::sendGet(const QString &endpoint, const QString &actionTag)
{
    QUrl url(m_serverUrl + endpoint);
    QNetworkRequest request(url);
    request.setHeader(QNetworkRequest::ContentTypeHeader, "application/json");
    request.setAttribute(QNetworkRequest::HttpPipeliningAllowedAttribute, true);

    QNetworkReply *reply = m_netManager->get(request);
    m_activeRequests[reply] = actionTag;
}

void AiMentorBridge::sendPost(const QString &endpoint, const QJsonObject &payload, const QString &actionTag)
{
    QUrl url(m_serverUrl + endpoint);
    QNetworkRequest request(url);
    request.setHeader(QNetworkRequest::ContentTypeHeader, "application/json");

    QByteArray data = QJsonDocument(payload).toJson(QJsonDocument::Compact);
    QNetworkReply *reply = m_netManager->post(request, data);
    m_activeRequests[reply] = actionTag;
}

void AiMentorBridge::checkServerStatus()
{
    sendGet("/api/status", "STATUS");
}

void AiMentorBridge::requestCurriculum()
{
    sendGet("/api/curriculum", "CURRICULUM");
}

void AiMentorBridge::requestCurrentLesson()
{
    sendGet("/api/lesson/current", "CURRENT_LESSON");
}

void AiMentorBridge::selectLesson(const QString &lessonId)
{
    QJsonObject obj;
    obj["lesson_id"] = lessonId;
    sendPost("/api/lesson/select", obj, "SELECT_LESSON");
}

void AiMentorBridge::selectPhase(int phaseIndex)
{
    QJsonObject obj;
    obj["phase_index"] = phaseIndex;
    sendPost("/api/lesson/phase", obj, "SELECT_PHASE");
}

void AiMentorBridge::nextLesson()
{
    QJsonObject obj;
    sendPost("/api/lesson/next", obj, "NEXT_LESSON");
}

void AiMentorBridge::previousLesson()
{
    QJsonObject obj;
    sendPost("/api/lesson/previous", obj, "PREV_LESSON");
}

void AiMentorBridge::submitTelemetry(const MidiSessionTelemetry &telemetry)
{
    sendPost("/api/evaluate", telemetry.toJson(), "EVALUATE");
}

void AiMentorBridge::askQuestion(const QString &question)
{
    QJsonObject obj;
    obj["question"] = question;
    sendPost("/api/ask", obj, "ASK");
}

void AiMentorBridge::generateCustomDrill(const QString &drillType, int rootNote, int bpm)
{
    QJsonObject obj;
    obj["drill_type"] = drillType;
    obj["root_note"] = rootNote;
    obj["bpm"] = bpm;
    sendPost("/api/generate_drill", obj, "GENERATE_DRILL");
}

void AiMentorBridge::startNewSession(const QString &songTitle, float speed, const QString &playMode, const QString &hand)
{
    m_currentSession = MidiSessionTelemetry();
    m_currentSession.songTitle = songTitle;
    m_currentSession.speed = speed;
    m_currentSession.playMode = playMode;
    m_currentSession.hand = hand;
    m_sessionTotalOffsetMs = 0;
    m_sessionOffsetCount = 0;
    m_barErrorCounts.clear();
}

void AiMentorBridge::recordNoteEvent(int bar, int expectedNote, int playedNote, qint64 offsetMs, const QString &result)
{
    MidiNoteTelemetry note;
    note.bar = bar;
    note.expectedNote = expectedNote;
    note.playedNote = playedNote;
    note.offsetMs = offsetMs;
    note.result = result;

    if (m_currentSession.notesHistory.size() < 200)
    {
        m_currentSession.notesHistory.append(note);
    }

    if (result == "hit" && offsetMs != 0)
    {
        m_sessionTotalOffsetMs += offsetMs;
        m_sessionOffsetCount++;
    }

    if (result == "wrong" || result == "late")
    {
        m_barErrorCounts[bar] = m_barErrorCounts.value(bar, 0) + 1;
    }
}

void AiMentorBridge::finalizeSession(int totalNotes, int wrongNotes, int lateNotes, double accuracy)
{
    m_currentSession.totalNotes = totalNotes;
    m_currentSession.wrongNotes = wrongNotes;
    m_currentSession.lateNotes = lateNotes;
    m_currentSession.accuracy = accuracy;

    if (m_sessionOffsetCount > 0)
    {
        m_currentSession.avgOffsetMs = static_cast<double>(m_sessionTotalOffsetMs) / m_sessionOffsetCount;
    }
    else
    {
        m_currentSession.avgOffsetMs = 0.0;
    }

    m_currentSession.problemBars.clear();
    for (auto it = m_barErrorCounts.begin(); it != m_barErrorCounts.end(); ++it)
    {
        if (it.value() >= 1 && it.key() > 0)
        {
            m_currentSession.problemBars.append(it.key());
        }
    }

    // Submit telemetry automatically
    submitTelemetry(m_currentSession);
}

void AiMentorBridge::onNetworkReplyFinished(QNetworkReply *reply)
{
    QString actionTag = m_activeRequests.take(reply);
    reply->deleteLater();

    if (reply->error() != QNetworkReply::NoError)
    {
        if (actionTag == "STATUS")
        {
            m_connected = false;
            emit statusUpdated(false, "Offline", "None");
            ensureServerRunning();
        }
        else
        {
            emit errorOccurred(QString("AI Mentor Network Error: %1").arg(reply->errorString()));
        }
        return;
    }

    QByteArray data = reply->readAll();
    QJsonDocument doc = QJsonDocument::fromJson(data);
    if (!doc.isObject())
    {
        return;
    }
    QJsonObject root = doc.object();

    if (actionTag == "STATUS")
    {
        m_connected = true;
        QJsonObject llmObj = root.value("llm").toObject();
        bool llmOnline = llmObj.value("online").toBool();
        QString model = llmObj.value("active_model").toString();
        QString statusText = llmOnline ? QString("Online (%1)").arg(model) : QString("Rule Pedagogy Fallback");
        emit statusUpdated(true, statusText, model);
    }
    else if (actionTag == "CURRICULUM")
    {
        emit curriculumReceived(root);
    }
    else if (actionTag == "CURRENT_LESSON" || actionTag == "SELECT_LESSON" || actionTag == "NEXT_LESSON" || actionTag == "PREV_LESSON")
    {
        QJsonObject lessonData = root.value("lesson").toObject();
        QJsonObject directives = root.value("directives").toObject();
        QString coachingHtml = root.value("coaching_html").toString();
        emit lessonLoaded(lessonData, directives, coachingHtml);
        if (!directives.isEmpty())
        {
            emit directivesReceived(directives);
        }
    }
    else if (actionTag == "EVALUATE")
    {
        QJsonObject report = root.value("report").toObject();
        QString coachingHtml = root.value("coaching_html").toString();
        QJsonObject directives = root.value("directives").toObject();
        emit evaluationReceived(report, coachingHtml, directives);
    }
    else if (actionTag == "ASK")
    {
        QString question = root.value("question").toString();
        QString answer = root.value("answer").toString();
        emit answerReceived(question, answer);
    }
    else if (actionTag == "GENERATE_DRILL" || actionTag == "SELECT_PHASE")
    {
        QJsonObject directives = root.value("directives").toObject();
        if (!directives.isEmpty())
        {
            emit directivesReceived(directives);
        }
    }
}
