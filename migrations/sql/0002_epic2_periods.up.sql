-- =====================================================================
-- EPIC 2: Loại đồ án, công thức điểm, đợt, mốc (7 bảng)
-- =====================================================================

CREATE TABLE thesis_types (
  id        BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  code      VARCHAR(30)  NOT NULL,
  name      VARCHAR(150) NOT NULL,
  is_active TINYINT(1)   NOT NULL DEFAULT 1,
  PRIMARY KEY (id),
  UNIQUE KEY uq_thesis_types_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Loại đồ án là dữ liệu (A1, A2): thêm loại là thêm một dòng';

CREATE TABLE thesis_type_steps (
  thesis_type_id BIGINT UNSIGNED NOT NULL,
  step_code      VARCHAR(30) NOT NULL COMMENT 'PROPOSAL, MIDTERM, REVIEW, COMMITTEE, FINAL, REVISION...',
  enabled        TINYINT(1)  NOT NULL DEFAULT 1 COMMENT 'Bật/tắt bước theo loại, ví dụ loại không có phản biện',
  sort_order     SMALLINT    NOT NULL DEFAULT 0,
  params         JSON        NULL,
  PRIMARY KEY (thesis_type_id, step_code),
  CONSTRAINT fk_tts_type FOREIGN KEY (thesis_type_id) REFERENCES thesis_types (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE grading_formulas (
  id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  thesis_type_id BIGINT UNSIGNED NOT NULL,
  version        INT           NOT NULL,
  name           VARCHAR(150)  NOT NULL,
  scale_max      DECIMAL(5,2)  NOT NULL DEFAULT 10.00,
  rounding       JSON          NULL COMMENT 'Quy tắc làm tròn từng bước (câu J2)',
  combine_rule   JSON          NULL COMMENT 'Cách gộp điểm thành viên và thành phần (câu J3)',
  pass_threshold DECIMAL(5,2)  NULL COMMENT 'Câu J4: chưa biết',
  is_sample      TINYINT(1)    NOT NULL DEFAULT 0 COMMENT '1 = công thức mẫu để thử, KHÔNG dùng chấm thật',
  created_by     BIGINT UNSIGNED NULL,
  created_at     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_formula_version (thesis_type_id, version),
  CONSTRAINT fk_formula_type FOREIGN KEY (thesis_type_id) REFERENCES thesis_types (id),
  CONSTRAINT fk_formula_user FOREIGN KEY (created_by) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='US-08. Bất biến: đổi công thức là tạo version mới, đợt cũ giữ công thức cũ (câu J8)';

CREATE TABLE grading_criteria (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  formula_id  BIGINT UNSIGNED NOT NULL,
  code        VARCHAR(30)  NOT NULL,
  name        VARCHAR(150) NOT NULL,
  scorer_kind VARCHAR(20)  NOT NULL COMMENT 'ADVISOR, REVIEWER, COMMITTEE, PROCESS',
  weight      DECIMAL(6,3) NOT NULL,
  max_score   DECIMAL(5,2) NOT NULL DEFAULT 10.00,
  sort_order  SMALLINT     NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  UNIQUE KEY uq_criteria_code (formula_id, code),
  CONSTRAINT fk_criteria_formula FOREIGN KEY (formula_id) REFERENCES grading_formulas (id) ON DELETE CASCADE,
  CONSTRAINT ck_criteria_weight CHECK (weight >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE periods (
  id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  thesis_type_id BIGINT UNSIGNED NOT NULL,
  org_unit_id    BIGINT UNSIGNED NULL,
  name           VARCHAR(150) NOT NULL,
  academic_year  VARCHAR(9)   NULL,
  term           VARCHAR(20)  NULL,
  status         VARCHAR(12)  NOT NULL DEFAULT 'DRAFT',
  formula_id     BIGINT UNSIGNED NULL,
  default_advisor_quota SMALLINT NULL COMMENT 'Hạn mức mặc định mỗi GVHD (câu E1)',
  params         JSON NULL COMMENT 'Tham số của đợt: số lần bảo vệ lại, hạn phúc khảo, hạn nộp chỉnh sửa, ngưỡng trùng lặp...',
  created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_periods_type (thesis_type_id, status),
  CONSTRAINT fk_periods_type    FOREIGN KEY (thesis_type_id) REFERENCES thesis_types (id),
  CONSTRAINT fk_periods_org     FOREIGN KEY (org_unit_id) REFERENCES org_units (id),
  CONSTRAINT fk_periods_formula FOREIGN KEY (formula_id) REFERENCES grading_formulas (id),
  CONSTRAINT ck_periods_status CHECK (status IN ('DRAFT','OPEN','CLOSED','ARCHIVED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='US-06';

CREATE TABLE period_milestones (
  id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  period_id  BIGINT UNSIGNED NOT NULL,
  code       VARCHAR(30)  NOT NULL,
  name       VARCHAR(150) NOT NULL,
  due_at     DATETIME     NOT NULL,
  hard_lock  TINYINT(1)   NOT NULL DEFAULT 0 COMMENT 'Câu C2: tạm chỉ cảnh báo, không khóa cứng',
  sort_order SMALLINT     NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  UNIQUE KEY uq_milestone_code (period_id, code),
  CONSTRAINT fk_ms_period FOREIGN KEY (period_id) REFERENCES periods (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Mốc là dữ liệu theo đợt (câu C1)';

CREATE TABLE advisor_quota_overrides (
  period_id    BIGINT UNSIGNED NOT NULL,
  user_id      BIGINT UNSIGNED NOT NULL,
  max_students SMALLINT NOT NULL,
  reason       VARCHAR(300) NULL,
  approved_by  BIGINT UNSIGNED NULL,
  created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (period_id, user_id),
  CONSTRAINT fk_aqo_period FOREIGN KEY (period_id) REFERENCES periods (id) ON DELETE CASCADE,
  CONSTRAINT fk_aqo_user   FOREIGN KEY (user_id) REFERENCES users (id),
  CONSTRAINT fk_aqo_appr   FOREIGN KEY (approved_by) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Ngoại lệ hạn mức có ghi lý do (US-07, câu E2)';
