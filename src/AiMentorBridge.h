/*********************************************************************************/
/*!
@file           AiMentorBridge.h

@brief          Bridge connecting PianoBooster with the offline AI Mentor agent
                and Ollama LLM service. Captures MIDI telemetry, manages curriculum,
                and executes pedagogical directives.

@author         PianoBooster AI Mentor Integration
*/
/*********************************************************************************/

#ifndef __AI_MENTOR_BRIDGE_H__
#define __AI_MENTOR_BRIDGE_H__

#include <QObject>
#include <QString>
#include <QJsonObject>
#include <QJsonArray>
#include <QJsonDocument>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QNetworkRequest>
#include <QProcess>
#include <QVector>
#include <QMap>
#include <QTimer>

struct MidiNoteTelemetry
{
    int bar;
    int expectedNote;
    int playedNote;
    qint64 offsetMs;
    QString result; // "hit", "wrong", "late"
};

struct MidiSessionTelemetry
{
    int totalNotes = 0;
    int wrongNotes = 0;
    int lateNotes = 0;
    double accuracy = 100.0;
    float speed = 1.0f;
    QString playMode = "followYou";
    QString hand = "right";
    QString songTitle;
    double avgOffsetMs = 0.0;
    double timingJitterMs = 0.0;
    QVector<int> problemBars;
    QVector<MidiNoteTelemetry> notesHistory;

    QJsonObject toJson() const
    {
        QJsonObject obj;
        obj["total_notes"] = totalNotes;
        obj["wrong_notes"] = wrongNotes;
        obj["late_notes"] = lateNotes;
        obj["accuracy"] = accuracy;
        obj["speed"] = static_cast<double>(speed);
        obj["play_mode"] = playMode;
        obj["hand"] = hand;
        obj["song_title"] = songTitle;
        obj["avg_offset_ms"] = avgOffsetMs;
        obj["timing_jitter_ms"] = timingJitterMs;

        QJsonArray barsArr;
        for (int b : problemBars)
            barsArr.append(b);
        obj["problem_bars"] = barsArr;

        QJsonArray histArr;
        for (const auto &n : notesHistory)
        {
            QJsonObject no;
            no["bar"] = n.bar;
            no["expected"] = n.expectedNote;
            no["played"] = n.playedNote;
            no["offset_ms"] = static_cast<double>(n.offsetMs);
            no["result"] = n.result;
            histArr.append(no);
        }
        obj["notes_history"] = histArr;
        return obj;
    }
};

class AiMentorBridge : public QObject
{
    Q_OBJECT

public:
    explicit AiMentorBridge(QObject *parent = nullptr, const QString &serverUrl = "http://127.0.0.1:8765");
    ~AiMentorBridge();

    void checkServerStatus();
    void requestCurriculum();
    void requestCurrentLesson();
    void selectLesson(const QString &lessonId);
    void selectPhase(int phaseIndex);
    void nextLesson();
    void previousLesson();
    void submitTelemetry(const MidiSessionTelemetry &telemetry);
    void askQuestion(const QString &question);
    void generateCustomDrill(const QString &drillType = "scale", int rootNote = 60, int bpm = 85);

    void recordNoteEvent(int bar, int expectedNote, int playedNote, qint64 offsetMs, const QString &result);
    void startNewSession(const QString &songTitle, float speed, const QString &playMode, const QString &hand);
    void finalizeSession(int totalNotes, int wrongNotes, int lateNotes, double accuracy);
    MidiSessionTelemetry getCurrentSession() const { return m_currentSession; }

    bool isConnected() const { return m_connected; }
    QString getServerUrl() const { return m_serverUrl; }
    void setServerUrl(const QString &url) { m_serverUrl = url; }

    void ensureServerRunning();

signals:
    void statusUpdated(bool connected, const QString &llmStatus, const QString &activeModel);
    void curriculumReceived(const QJsonObject &curriculumData);
    void lessonLoaded(const QJsonObject &lessonData, const QJsonObject &directives, const QString &coachingHtml);
    void evaluationReceived(const QJsonObject &report, const QString &coachingHtml, const QJsonObject &directives);
    void answerReceived(const QString &question, const QString &answer);
    void directivesReceived(const QJsonObject &directives);
    void errorOccurred(const QString &errorMessage);

private slots:
    void onNetworkReplyFinished(QNetworkReply *reply);
    void onHeartbeatTimer();

private:
    void sendPost(const QString &endpoint, const QJsonObject &payload, const QString &actionTag);
    void sendGet(const QString &endpoint, const QString &actionTag);

    QString m_serverUrl;
    QNetworkAccessManager *m_netManager;
    bool m_connected;
    QProcess *m_serverProcess;
    MidiSessionTelemetry m_currentSession;
    QMap<QNetworkReply*, QString> m_activeRequests;
    QTimer *m_heartbeatTimer;
    qint64 m_sessionTotalOffsetMs;
    int m_sessionOffsetCount;
    QMap<int, int> m_barErrorCounts;
};

#endif // __AI_MENTOR_BRIDGE_H__
