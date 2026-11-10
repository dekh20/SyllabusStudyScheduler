# Study Assessment — Unit Test Report

Run: 2026-11-10 14:14  
Framework: pytest  
Result: **43 / 43 passed**

| # | Class | Test | Case | What it checks | Result |
|---|-------|------|------|----------------|--------|
| 1 | StudyScheduler | `test_add_availability` |  |  | PASSED |
| 2 | StudyScheduler | `test_conflict` |  |  | PASSED |
| 3 | StudyScheduler | `test_empty_schedule` |  |  | PASSED |
| 4 | StudyScheduler | `test_generate_schedule` |  |  | PASSED |
| 5 | StudyScheduler | `test_invalid_time` |  |  | PASSED |
| 6 | StudyScheduler | `test_modify_schedule` |  |  | PASSED |
| 7 | StudyScheduler | `test_no_conflict` |  |  | PASSED |
| 8 |  | `test_save_update_and_remove_event` |  |  | PASSED |
| 9 |  | `test_export_calendar` |  |  | PASSED |
| 10 |  | `test_export_empty_calendar` |  |  | PASSED |
| 11 |  | `test_reminder_at_due_time` |  |  | PASSED |
| 12 |  | `test_export_large_calendar` |  |  | PASSED |
| 13 |  | `test_invalid_event_titles` |  |  | PASSED |
| 14 |  | `test_invalid_event_times` |  |  | PASSED |
| 15 |  | `test_regenerating_plan_replaces_sessions_without_removing_other_events` |  |  | PASSED |
| 16 |  | `test_invalid_plan_leaves_current_calendar_unchanged` |  |  | PASSED |
| 17 |  | `test_replaying_plan_preserves_delivery_of_unchanged_reminder` |  |  | PASSED |
| 18 |  | `test_ics_exports_deadline_at_due_time_and_keeps_uid_after_edit` |  |  | PASSED |
| 19 |  | `test_ics_folds_utf8_lines_and_escapes_event_text` |  |  | PASSED |
| 20 |  | `test_ics_export_requires_an_event` |  |  | PASSED |
| 21 |  | `test_fall_back_uses_actual_instants_for_event_and_reminder` |  |  | PASSED |
| 22 | Authentication | `test_01_valid_login_and_two_factor` |  |  | PASSED |
| 23 | Authentication | `test_02_invalid_password_and_none` |  |  | PASSED |
| 24 | Authentication | `test_03_code_expiration_boundary` |  |  | PASSED |
| 25 | Authentication | `test_04_wrong_reused_and_bad_format_codes` |  |  | PASSED |
| 26 | ProgressAndReminders | `test_05_progress_transition` |  |  | PASSED |
| 27 | ProgressAndReminders | `test_06_invalid_status_inputs` |  |  | PASSED |
| 28 | ProgressAndReminders | `test_07_reminder_normal_boundary_empty_and_bad_entry` |  |  | PASSED |
| 29 | AssessmentResult | `test_score_calculation` | Normal | calculateScore: A,B,C,D -> 50; lowercase 'd','c' -> 83. | PASSED |
| 30 | AssessmentResult | `test_retake_creates_new_result_and_stores_history` | Normal | Retaking makes a new result; both attempts are stored in history in order. | PASSED |
| 31 | AssessmentResult | `test_score_boundaries` | Edge | All 'A' -> 0, all 'D' -> 100, single answer and exactly MAX_QUESTIONS answers are scored. | PASSED |
| 32 | AssessmentResult | `test_many_retakes_history` | Edge | 100 completed assessments are all stored, oldest first; empty history before any. | PASSED |
| 33 | AssessmentResult | `test_invalid_answers_and_retake` | Invalid | Empty, oversized, or bad-letter answers raise; retake before a first attempt raises. | PASSED |
| 34 | AssessmentService | `test_submit_answers_returns_scored_result` | Normal | submitAnswers turns the student's answers into a scored AssessmentResult. | PASSED |
| 35 | AssessmentService | `test_submit_answers_sets_study_preference` | Normal | Submitting answers creates the StudyProfile with the student's study preferences. | PASSED |
| 36 | AssessmentService | `test_single_answer_submission` | Edge | A single answer is enough to produce a result and a study preference. | PASSED |
| 37 | AssessmentService | `test_none_and_wrong_type_answers_rejected` | Invalid | None, a list, or a non-UUID student ID is rejected and no profile is made. | PASSED |
| 38 | AssessmentService | `test_large_input_rejected_and_preference_unchanged` | Invalid | A 10,000-answer submission is rejected; the existing study preference stays the same. | PASSED |
| 39 | StudyProfile | `test_profile_id_is_student_uuid` | Normal | profileId is the student's UUID; preferences start empty until a result is applied. | PASSED |
| 40 | StudyProfile | `test_update_from_result_sets_int_values` | Normal | updateFromResult sets session minutes, break minutes and sessions/week as ints. | PASSED |
| 41 | StudyProfile | `test_tier_boundaries` | Edge | Score 0 -> 25 min, score 50 -> 45 min (not 30), score 100 -> 60 min. | PASSED |
| 42 | StudyProfile | `test_accept_sessions_per_week_limits` | Edge | Student can accept exactly 1 or 14 sessions/week; 0 and 15 are rejected. | PASSED |
| 43 | StudyProfile | `test_invalid_profile_id_and_result` | Invalid | Non-UUID profileId, None result, or another student's result is rejected. | PASSED |
