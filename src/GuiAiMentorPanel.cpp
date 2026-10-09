/*********************************************************************************/
/*!
@file           GuiAiMentorPanel.cpp

@brief          AI Mentor panel implementation inside PianoBooster.
*/
/*********************************************************************************/

#include "GuiAiMentorPanel.h"
#include "Song.h"
#include "Settings.h"
#include "GuiSidePanel.h"
#include "GuiTopBar.h"

#include <QFile>
#include <QFileInfo>
#include <QDir>
#include <QMessageBox>

GuiAiMentorPanel::GuiAiMentorPanel(QWidget *parent, CSettings *settings, AiMentorBridge *bridge)
    : QWidget(parent),
      m_song(nullptr),
      m_settings(settings),
      m_sidePanel(nullptr),
      m_topBar(nullptr),
      m_bridge(bridge),
      m_currentPhaseIndex(2),
      m_ignoreComboChange(false)
{
    setupUi(this);

    // Initial button states
    updatePhaseButtons(2);

    // Initial placeholder message
    displayMentorHtml("<h3>Welcome to PianoBooster AI Mentor!</h3>"
                      "<p>I am <strong>Maestro</strong>, your offline piano mentor. "
                      "As you play your MIDI keyboard, I will analyze your timing, note accuracy, "
                      "and rhythm to give you tailored coaching and adaptive practice drills.</p>"
                      "<p>Select a lesson from above or click <strong>Apply Lesson Setup</strong> to begin!</p>");

    connect(questionEdit, &QLineEdit::returnPressed, this, &GuiAiMentorPanel::on_questionEdit_returnPressed);

    if (m_bridge)
    {
        connect(m_bridge, &AiMentorBridge::statusUpdated, this, &GuiAiMentorPanel::onStatusUpdated);
        connect(m_bridge, &AiMentorBridge::curriculumReceived, this, &GuiAiMentorPanel::onCurriculumReceived);
        connect(m_bridge, &AiMentorBridge::lessonLoaded, this, &GuiAiMentorPanel::onLessonLoaded);
        connect(m_bridge, &AiMentorBridge::evaluationReceived, this, &GuiAiMentorPanel::onEvaluationReceived);
        connect(m_bridge, &AiMentorBridge::answerReceived, this, &GuiAiMentorPanel::onAnswerReceived);
        connect(m_bridge, &AiMentorBridge::directivesReceived, this, &GuiAiMentorPanel::onDirectivesReceived);
        connect(m_bridge, &AiMentorBridge::errorOccurred, this, &GuiAiMentorPanel::onErrorOccurred);

        // Fetch curriculum on startup
        m_bridge->requestCurriculum();
        m_bridge->requestCurrentLesson();
    }
}

GuiAiMentorPanel::~GuiAiMentorPanel()
{
}

void GuiAiMentorPanel::init(CSong *song, GuiSidePanel *sidePanel, GuiTopBar *topBar)
{
    m_song = song;
    m_sidePanel = sidePanel;
    m_topBar = topBar;
}

void GuiAiMentorPanel::displayMentorHtml(const QString &htmlBody)
{
    QString styled = QString(
        "<html><head><style>"
        "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 13px; color: #E0E0E0; background-color: #1E1E24; margin: 8px; line-height: 1.4; }"
        "h3 { color: #4FC3F7; margin-top: 0px; margin-bottom: 6px; font-size: 15px; }"
        "p { margin: 6px 0px; }"
        "strong { color: #FFF; }"
        "em { color: #FFD54F; font-style: normal; }"
        ".card { background-color: #2A2A34; border-radius: 6px; padding: 8px; margin-bottom: 8px; border-left: 4px solid #4FC3F7; }"
        ".tip { background-color: #2E3326; border-left: 4px solid #81C784; padding: 6px; border-radius: 4px; margin: 6px 0px; }"
        ".alert { background-color: #382626; border-left: 4px solid #E57373; padding: 6px; border-radius: 4px; margin: 6px 0px; }"
        "</style></head><body>"
        "<div class='card'>%1</div>"
        "</body></html>"
    ).arg(htmlBody);

    mentorTextBrowser->setHtml(styled);
}

void GuiAiMentorPanel::updatePhaseButtons(int activePhase)
{
    m_currentPhaseIndex = activePhase;
    QString activeStyle = "background-color: #1976D2; color: white; font-weight: bold;";
    QString normalStyle = "";

    phase1Btn->setStyleSheet(activePhase == 0 ? activeStyle : normalStyle);
    phase2Btn->setStyleSheet(activePhase == 1 ? activeStyle : normalStyle);
    phase3Btn->setStyleSheet(activePhase == 2 ? activeStyle : normalStyle);
    phase4Btn->setStyleSheet(activePhase == 3 ? activeStyle : normalStyle);
}

void GuiAiMentorPanel::onStatusUpdated(bool connected, const QString &llmStatus, const QString &activeModel)
{
    Q_UNUSED(activeModel)
    if (connected)
    {
        statusBadgeLabel->setText(QString("🟢 AI Mentor: %1").arg(llmStatus));
        statusBadgeLabel->setStyleSheet("color: #4CAF50; font-weight: bold;");
    }
    else
    {
        statusBadgeLabel->setText("🟡 Offline Fallback");
        statusBadgeLabel->setStyleSheet("color: #FFB300; font-weight: bold;");
    }
}

void GuiAiMentorPanel::onCurriculumReceived(const QJsonObject &curriculumData)
{
    m_curriculumLessons = curriculumData.value("lessons").toArray();
    m_ignoreComboChange = true;
    lessonCombo->clear();

    for (int i = 0; i < m_curriculumLessons.size(); ++i)
    {
        QJsonObject les = m_curriculumLessons[i].toObject();
        QString title = les.value("title").toString();
        lessonCombo->addItem(title, les.value("id").toString());
    }

    int curIdx = curriculumData.value("current_lesson_index").toInt(0);
    if (curIdx >= 0 && curIdx < lessonCombo->count())
    {
        lessonCombo->setCurrentIndex(curIdx);
    }
    m_ignoreComboChange = false;
}

void GuiAiMentorPanel::onLessonLoaded(const QJsonObject &lessonData, const QJsonObject &directives, const QString &coachingHtml)
{
    m_currentLesson = lessonData;
    m_currentDirectives = directives;

    QString lessonId = lessonData.value("id").toString();
    m_ignoreComboChange = true;
    for (int i = 0; i < lessonCombo->count(); ++i)
    {
        if (lessonCombo->itemData(i).toString() == lessonId)
        {
            lessonCombo->setCurrentIndex(i);
            break;
        }
    }
    m_ignoreComboChange = false;

    int phaseIdx = directives.value("phase_index").toInt(2);
    updatePhaseButtons(phaseIdx);

    if (!coachingHtml.isEmpty())
    {
        displayMentorHtml(coachingHtml);
    }
    else
    {
        QString title = lessonData.value("title").toString();
        QString theory = lessonData.value("theory_notes").toString();
        QString tips = lessonData.value("fingering_tips").toString();
        QString body = QString("<h3>%1</h3><p>%2</p><div class='tip'><strong>Fingering Technique:</strong> %3</div>")
                           .arg(title, theory, tips);
        displayMentorHtml(body);
    }
}

void GuiAiMentorPanel::onEvaluationReceived(const QJsonObject &report, const QString &coachingHtml, const QJsonObject &directives)
{
    m_currentDirectives = directives;

    double acc = report.value("accuracy").toDouble(0.0);
    QString grade = report.value("grade").toString("--");
    QString timingDiag = report.value("timing_diagnosis").toString();

    accuracyLabel->setText(QString("Accuracy: %1%").arg(acc, 0, 'f', 1));
    gradeLabel->setText(QString("Grade: %1").arg(grade));
    timingDiagLabel->setText(timingDiag);

    if (report.value("passed").toBool())
    {
        accuracyLabel->setStyleSheet("color: #4CAF50; font-weight: bold;");
    }
    else
    {
        accuracyLabel->setStyleSheet("color: #FFB300; font-weight: bold;");
    }

    displayMentorHtml(coachingHtml);
}

void GuiAiMentorPanel::onAnswerReceived(const QString &question, const QString &answer)
{
    QString content = QString("<h3>Q: %1</h3><p>%2</p>").arg(question, answer);
    displayMentorHtml(content);
}

void GuiAiMentorPanel::onDirectivesReceived(const QJsonObject &directives)
{
    m_currentDirectives = directives;
    // Auto-apply if requested
    if (directives.value("auto_apply").toBool(false))
    {
        applyDirectives(directives);
    }
}

void GuiAiMentorPanel::onErrorOccurred(const QString &errorMessage)
{
    statusBadgeLabel->setText("⚠️ Error");
    statusBadgeLabel->setStyleSheet("color: #E57373;");
}

void GuiAiMentorPanel::applyDirectives(const QJsonObject &directives)
{
    if (!m_song || directives.isEmpty())
        return;

    QString songPath = directives.value("song_path").toString();
    if (!songPath.isEmpty() && QFile::exists(songPath))
    {
        if (m_settings)
        {
            m_settings->openSongFile(songPath);
        }
        else
        {
            m_song->loadSong(songPath);
        }
    }

    // Apply speed
    if (directives.contains("speed"))
    {
        float speed = static_cast<float>(directives.value("speed").toDouble(1.0));
        m_song->setSpeed(speed);
        if (m_topBar)
        {
            m_topBar->setSpeed(static_cast<int>(speed * 100.0f + 0.5f));
        }
    }

    // Apply hand
    if (directives.contains("hand") && m_sidePanel)
    {
        QString handStr = directives.value("hand").toString();
        if (handStr == "right")
            m_sidePanel->setActiveHand(PB_PART_right);
        else if (handStr == "left")
            m_sidePanel->setActiveHand(PB_PART_left);
        else
            m_sidePanel->setActiveHand(PB_PART_both);
    }

    // Apply play mode
    if (directives.contains("play_mode"))
    {
        QString modeStr = directives.value("play_mode").toString();
        playMode_t mode = PB_PLAY_MODE_followYou;
        if (modeStr == "listen")
            mode = PB_PLAY_MODE_listen;
        else if (modeStr == "rhythmTapping")
            mode = PB_PLAY_MODE_rhythmTapping;
        else if (modeStr == "followYou")
            mode = PB_PLAY_MODE_followYou;
        else if (modeStr == "playAlong")
            mode = PB_PLAY_MODE_playAlong;

        m_song->setPlayMode(mode);
    }

    // Apply looping range
    if (directives.contains("loop_from") && directives.contains("loop_to"))
    {
        double fromBar = directives.value("loop_from").toDouble(0.0);
        double toBar = directives.value("loop_to").toDouble(0.0);

        m_song->setPlayFromBar(fromBar);
        if (toBar > fromBar)
        {
            m_song->setPlayUptoBar(toBar);
            m_song->setLoopingBars(toBar - fromBar);
        }
        else
        {
            m_song->setLoopingBars(0.0);
        }
    }
}

void GuiAiMentorPanel::on_applySetupBtn_clicked()
{
    if (!m_currentDirectives.isEmpty())
    {
        applyDirectives(m_currentDirectives);
    }
    else if (m_bridge)
    {
        m_bridge->requestCurrentLesson();
    }
}

void GuiAiMentorPanel::on_lessonCombo_activated(int index)
{
    if (m_ignoreComboChange || !m_bridge)
        return;
    QString lessonId = lessonCombo->itemData(index).toString();
    if (!lessonId.isEmpty())
    {
        m_bridge->selectLesson(lessonId);
    }
}

void GuiAiMentorPanel::on_phase1Btn_clicked()
{
    updatePhaseButtons(0);
    if (m_bridge) m_bridge->selectPhase(0);
}

void GuiAiMentorPanel::on_phase2Btn_clicked()
{
    updatePhaseButtons(1);
    if (m_bridge) m_bridge->selectPhase(1);
}

void GuiAiMentorPanel::on_phase3Btn_clicked()
{
    updatePhaseButtons(2);
    if (m_bridge) m_bridge->selectPhase(2);
}

void GuiAiMentorPanel::on_phase4Btn_clicked()
{
    updatePhaseButtons(3);
    if (m_bridge) m_bridge->selectPhase(3);
}

void GuiAiMentorPanel::on_nextLessonBtn_clicked()
{
    if (m_bridge)
    {
        m_bridge->nextLesson();
    }
}

void GuiAiMentorPanel::on_remedialDrillBtn_clicked()
{
    if (m_bridge)
    {
        // Re-evaluate last session to produce adaptive remedial drill
        MidiSessionTelemetry session = m_bridge->getCurrentSession();
        m_bridge->submitTelemetry(session);
    }
}

void GuiAiMentorPanel::on_generateDrillBtn_clicked()
{
    if (m_bridge)
    {
        m_bridge->generateCustomDrill("scale", 60, 85);
    }
}

void GuiAiMentorPanel::on_askBtn_clicked()
{
    on_questionEdit_returnPressed();
}

void GuiAiMentorPanel::on_questionEdit_returnPressed()
{
    QString q = questionEdit->text().trimmed();
    if (q.isEmpty() || !m_bridge)
        return;

    questionEdit->clear();
    displayMentorHtml(QString("<p><em>Thinking... Consulting Maestro on: '%1'</em></p>").arg(q));
    m_bridge->askQuestion(q);
}
