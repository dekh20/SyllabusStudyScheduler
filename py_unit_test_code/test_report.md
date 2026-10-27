# Study Assessment — Unit Test Report

Run: 2026-10-26 22:49  
Framework: pytest  
Result: **5 / 5 passed**

| # | Class | Test | Case | What it checks | Result |
|---|-------|------|------|----------------|--------|
| 1 | StudyProfile | `test_profile_id_is_student_uuid` | Normal | profileId is the student's UUID; preferences start empty until a result is applied. | PASSED |
| 2 | StudyProfile | `test_update_from_result_sets_int_values` | Normal | updateFromResult sets session minutes, break minutes and sessions/week as ints. | PASSED |
| 3 | StudyProfile | `test_tier_boundaries` | Edge | Score 0 -> 25 min, score 50 -> 45 min (not 30), score 100 -> 60 min. | PASSED |
| 4 | StudyProfile | `test_accept_sessions_per_week_limits` | Edge | Student can accept exactly 1 or 14 sessions/week; 0 and 15 are rejected. | PASSED |
| 5 | StudyProfile | `test_invalid_profile_id_and_result` | Invalid | Non-UUID profileId, None result, or another student's result is rejected. | PASSED |
