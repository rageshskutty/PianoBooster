/*********************************************************************************/
/*!
@file           GuiAiMentorPanel.h

@brief          AI Mentor panel widget inside PianoBooster. Displays live lesson scripts,
                pedagogical feedback, and student-mentor dialog.
*/
/*********************************************************************************/

#ifndef __GUIAIMENTORPANEL_H__
#define __GUIAIMENTORPANEL_H__

#include <QWidget>
#include <QJsonObject>
#include <QJsonArray>

#include "ui_GuiAiMentorPanel.ui"
#include "AiMentorBridge.h"

class CSong;
class CSettings;
class GuiSidePanel;
class GuiTopBar;

class GuiAiMentorPanel : public QWidget, private Ui::GuiAiMentorPanel
{
    Q_OBJECT

public:
    explicit GuiAiMentorPanel(QWidget *parent, CSettings *settings, AiMentorBridge *bridge);
    ~GuiAiMentorPanel();

    void init(CSong *song, GuiSidePanel *sidePanel, GuiTopBar *topBar);
    void applyDirectives(const QJsonObject &directives);

public slots:
    void onStatusUpdated(bool connected, const QString &llmStatus, const QString &activeModel);
    void onCurriculumReceived(const QJsonObject &curriculumData);
    void onLessonLoaded(const QJsonObject &lessonData, const QJsonObject &directives, const QString &coachingHtml);
    void onEvaluationReceived(const QJsonObject &report, const QString &coachingHtml, const QJsonObject &directives);
    void onAnswerReceived(const QString &question, const QString &answer);
    void onDirectivesReceived(const QJsonObject &directives);
    void onErrorOccurred(const QString &errorMessage);

private slots:
    void on_lessonCombo_activated(int index);
    void on_phase1Btn_clicked();
    void on_phase2Btn_clicked();
    void on_phase3Btn_clicked();
    void on_phase4Btn_clicked();
    void on_applySetupBtn_clicked();
    void on_nextLessonBtn_clicked();
    void on_remedialDrillBtn_clicked();
    void on_generateDrillBtn_clicked();
    void on_askBtn_clicked();
    void on_questionEdit_returnPressed();

private:
    void updatePhaseButtons(int activePhase);
    void displayMentorHtml(const QString &htmlBody);

    CSong *m_song;
    CSettings *m_settings;
    GuiSidePanel *m_sidePanel;
    GuiTopBar *m_topBar;
    AiMentorBridge *m_bridge;

    QJsonObject m_currentLesson;
    QJsonObject m_currentDirectives;
    QJsonArray m_curriculumLessons;
    int m_currentPhaseIndex;
    bool m_ignoreComboChange;
};

#endif // __GUIAIMENTORPANEL_H__
