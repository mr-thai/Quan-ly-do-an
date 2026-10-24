-- =====================================================================
-- SEED DATA: Dữ liệu khởi tạo cấu hình danh mục
-- =====================================================================

INSERT INTO roles (code, name, scope) VALUES
 ('ADMIN',            'Quản trị hệ thống',            'SYSTEM'),
 ('OFFICE',           'Giáo vụ / Văn phòng Viện',     'SYSTEM'),
 ('HEAD_OF_DEPT',     'Trưởng bộ môn',                'SYSTEM'),
 ('ADVISOR_ROLE',     'Giảng viên (có thể hướng dẫn)', 'SYSTEM'),
 ('STUDENT_ROLE',     'Sinh viên / học viên',         'SYSTEM'),
 ('STUDENT',          'Sinh viên của đề tài',         'TOPIC'),
 ('ADVISOR',          'Giảng viên hướng dẫn chính',   'TOPIC'),
 ('CO_ADVISOR',       'Đồng hướng dẫn',               'TOPIC'),
 ('EXTERNAL_ADVISOR', 'Hướng dẫn ngoài Viện',         'TOPIC'),
 ('REVIEWER',         'Giảng viên phản biện',         'TOPIC'),
 ('CHAIR',            'Chủ tịch hội đồng',            'COMMITTEE'),
 ('SECRETARY',        'Thư ký hội đồng',              'COMMITTEE'),
 ('MEMBER',           'Ủy viên hội đồng',             'COMMITTEE');

INSERT INTO topic_states (code, name, is_terminal, sort_order) VALUES
 ('PROPOSED',       'Đề xuất',              0, 10),
 ('APPROVED',       'Đã duyệt',             0, 20),
 ('IN_PROGRESS',    'Đang thực hiện',       0, 30),
 ('ELIGIBLE',       'Đủ điều kiện bảo vệ',  0, 40),
 ('DEFENDED',       'Đã bảo vệ',            0, 50),
 ('GRADED',         'Đã chốt điểm',         0, 60),
 ('ARCHIVED',       'Đã lưu trữ',           1, 70),
 ('ON_HOLD',        'Bảo lưu',              0, 80),
 ('SUSPENDED',      'Đình chỉ',             0, 90),
 ('WITHDRAWN',      'Đã rút',               1, 100),
 ('RETAKE_PENDING', 'Chờ bảo vệ lại',       0, 110);

INSERT INTO topic_transitions (from_state, to_state, role_code, requires_reason) VALUES
 ('PROPOSED',       'APPROVED',       'HEAD_OF_DEPT',     0),
 ('APPROVED',       'IN_PROGRESS',    'OFFICE',           0),
 ('IN_PROGRESS',    'ELIGIBLE',       'ADVISOR',          0),
 ('ELIGIBLE',       'IN_PROGRESS',    'ADVISOR',          1),
 ('ELIGIBLE',       'DEFENDED',       'SECRETARY',        0),
 ('ELIGIBLE',       'DEFENDED',       'OFFICE',           0),
 ('DEFENDED',       'GRADED',         'OFFICE',           0),
 ('GRADED',         'ARCHIVED',       'OFFICE',           0),
 ('GRADED',         'RETAKE_PENDING', 'OFFICE',           1),
 ('RETAKE_PENDING', 'ELIGIBLE',       'OFFICE',           0),
 ('IN_PROGRESS',    'ON_HOLD',        'HEAD_OF_DEPT',     1),
 ('IN_PROGRESS',    'ON_HOLD',        'OFFICE',           1),
 ('ON_HOLD',        'IN_PROGRESS',    'OFFICE',           0),
 ('IN_PROGRESS',    'SUSPENDED',      'HEAD_OF_DEPT',     1),
 ('SUSPENDED',      'IN_PROGRESS',    'HEAD_OF_DEPT',     1),
 ('IN_PROGRESS',    'WITHDRAWN',      'OFFICE',           1),
 ('ON_HOLD',        'WITHDRAWN',      'OFFICE',           1),
 ('PROPOSED',       'WITHDRAWN',      'OFFICE',           1);

INSERT INTO thesis_types (code, name) VALUES
 ('COURSE_PROJECT', 'Đồ án môn học'),
 ('GRADUATION',     'Đồ án tốt nghiệp'),
 ('MASTER_THESIS',  'Luận văn thạc sĩ');

INSERT INTO thesis_type_steps (thesis_type_id, step_code, enabled, sort_order)
SELECT t.id, s.step_code, 1, s.sort_order
FROM thesis_types t
JOIN (SELECT 'PROPOSAL' AS step_code, 10 AS sort_order UNION ALL
      SELECT 'MIDTERM', 20 UNION ALL
      SELECT 'FINAL', 30 UNION ALL
      SELECT 'REVIEW', 40 UNION ALL
      SELECT 'COMMITTEE', 50 UNION ALL
      SELECT 'REVISION', 60) s;

INSERT INTO assignment_rules (thesis_type_id, rule_code, params, severity, description) VALUES
 (NULL, 'REVIEWER_NOT_ADVISOR',       NULL,                  'BLOCK', 'Phản biện không được là GVHD hoặc đồng hướng dẫn của chính đề tài'),
 (NULL, 'REVIEWER_COUNT',             '{"count": 1}',        'BLOCK', 'Số phản biện mỗi đề tài (câu H1)'),
 (NULL, 'REVIEWER_SAME_DEPT_WARN',    NULL,                  'WARN',  'Cảnh báo phản biện cùng bộ môn với GVHD'),
 (NULL, 'COMMITTEE_MIN_SIZE',         '{"min": 3}',          'BLOCK', 'Hội đồng tối thiểu 3 người (câu I1)'),
 (NULL, 'COMMITTEE_REQUIRED_ROLES',   '{"roles": ["CHAIR","SECRETARY"]}', 'BLOCK', 'Phải có chủ tịch và thư ký'),
 (NULL, 'ADVISOR_NOT_IN_OWN_COMMITTEE', NULL,                'BLOCK', 'GVHD không chấm sinh viên mình hướng dẫn (câu I3)'),
 (NULL, 'ADVISOR_MAX_COMMITTEES',     '{"max": null}',       'WARN',  'Giới hạn số hội đồng mỗi giảng viên; null = không giới hạn (câu I4)');

INSERT INTO grading_formulas (thesis_type_id, version, name, scale_max, rounding, combine_rule, pass_threshold, is_sample)
SELECT id, 1, 'Công thức mẫu (chỉ để thử)', 10.00,
       '{"decimals": 1, "mode": "half_up", "stage": "final"}',
       '{"member_aggregate": "mean", "components": "weighted_sum"}',
       NULL, 1
FROM thesis_types;

INSERT INTO grading_criteria (formula_id, code, name, scorer_kind, weight, max_score, sort_order)
SELECT f.id, c.code, c.name, c.scorer_kind, c.weight, 10.00, c.sort_order
FROM grading_formulas f
JOIN (SELECT 'ADVISOR_SCORE' AS code, 'Điểm hướng dẫn' AS name, 'ADVISOR' AS scorer_kind, 0.300 AS weight, 10 AS sort_order UNION ALL
      SELECT 'REVIEWER_SCORE', 'Điểm phản biện', 'REVIEWER', 0.300, 20 UNION ALL
      SELECT 'COMMITTEE_SCORE', 'Điểm hội đồng', 'COMMITTEE', 0.400, 30) c
WHERE f.is_sample = 1;
