-- =====================================================================
-- EPIC 7: Chấm điểm, biên bản, sau bảo vệ (6 bảng)
-- =====================================================================

CREATE TABLE score_entries (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  topic_id      BIGINT UNSIGNED NOT NULL,
  attempt_no    SMALLINT NOT NULL DEFAULT 1,
  criterion_id  BIGINT UNSIGNED NOT NULL,
  scorer_user_id BIGINT UNSIGNED NOT NULL,
  score         DECIMAL(6,2) NOT NULL,
  comment       VARCHAR(1000) NULL,
  submitted_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  locked_at     DATETIME NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_score (topic_id, attempt_no, criterion_id, scorer_user_id),
  CONSTRAINT fk_se_topic FOREIGN KEY (topic_id) REFERENCES topics (id),
  CONSTRAINT fk_se_crit  FOREIGN KEY (criterion_id) REFERENCES grading_criteria (id),
  CONSTRAINT fk_se_user  FOREIGN KEY (scorer_user_id) REFERENCES users (id),
  CONSTRAINT ck_se_score CHECK (score >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='US-33';

CREATE TABLE grade_results (
  id               BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  topic_id         BIGINT UNSIGNED NOT NULL,
  attempt_no       SMALLINT NOT NULL DEFAULT 1,
  formula_id       BIGINT UNSIGNED NOT NULL,
  component_scores JSON NULL,
  final_score      DECIMAL(6,2) NULL,
  grade_label      VARCHAR(10) NULL,
  passed           TINYINT(1) NULL,
  status           VARCHAR(10) NOT NULL DEFAULT 'DRAFT',
  locked_by        BIGINT UNSIGNED NULL,
  locked_at        DATETIME NULL,
  published_at     DATETIME NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_gr (topic_id, attempt_no),
  CONSTRAINT fk_gr_topic   FOREIGN KEY (topic_id) REFERENCES topics (id),
  CONSTRAINT fk_gr_formula FOREIGN KEY (formula_id) REFERENCES grading_formulas (id),
  CONSTRAINT fk_gr_user    FOREIGN KEY (locked_by) REFERENCES users (id),
  CONSTRAINT ck_gr_status CHECK (status IN ('DRAFT','LOCKED','PUBLISHED','REOPENED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='US-35, US-36';

CREATE TABLE grade_result_history (
  id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  grade_result_id BIGINT UNSIGNED NOT NULL,
  snapshot       JSON NOT NULL,
  change_reason  VARCHAR(500) NULL,
  changed_by     BIGINT UNSIGNED NULL,
  changed_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_grh (grade_result_id, changed_at),
  CONSTRAINT fk_grh_gr FOREIGN KEY (grade_result_id) REFERENCES grade_results (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='US-36';

CREATE TABLE defense_minutes (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  session_id   BIGINT UNSIGNED NOT NULL,
  secretary_id BIGINT UNSIGNED NOT NULL,
  content      TEXT NULL,
  revision_requests TEXT NULL,
  finalized_at DATETIME NULL,
  created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_dm_session (session_id),
  CONSTRAINT fk_dm_session FOREIGN KEY (session_id) REFERENCES defense_sessions (id),
  CONSTRAINT fk_dm_sec     FOREIGN KEY (secretary_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='US-34';

CREATE TABLE revision_submissions (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  topic_id     BIGINT UNSIGNED NOT NULL,
  attempt_no   SMALLINT NOT NULL DEFAULT 1,
  file_id      BIGINT UNSIGNED NOT NULL,
  submitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  confirmed_by BIGINT UNSIGNED NULL,
  confirmed_at DATETIME NULL,
  PRIMARY KEY (id),
  CONSTRAINT fk_rs_topic FOREIGN KEY (topic_id) REFERENCES topics (id),
  CONSTRAINT fk_rs_file  FOREIGN KEY (file_id) REFERENCES files (id),
  CONSTRAINT fk_rs_user  FOREIGN KEY (confirmed_by) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='US-37';

CREATE TABLE grade_appeals (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  topic_id        BIGINT UNSIGNED NOT NULL,
  attempt_no      SMALLINT NOT NULL DEFAULT 1,
  student_user_id BIGINT UNSIGNED NOT NULL,
  reason          VARCHAR(2000) NOT NULL,
  status          VARCHAR(12) NOT NULL DEFAULT 'SUBMITTED',
  appeal_committee_id BIGINT UNSIGNED NULL,
  old_score       DECIMAL(6,2) NULL,
  new_score       DECIMAL(6,2) NULL,
  decision_note   VARCHAR(1000) NULL,
  submitted_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  decided_at      DATETIME NULL,
  PRIMARY KEY (id),
  CONSTRAINT fk_ga_topic FOREIGN KEY (topic_id) REFERENCES topics (id),
  CONSTRAINT fk_ga_user  FOREIGN KEY (student_user_id) REFERENCES users (id),
  CONSTRAINT fk_ga_com   FOREIGN KEY (appeal_committee_id) REFERENCES committees (id),
  CONSTRAINT ck_ga_status CHECK (status IN ('SUBMITTED','IN_REVIEW','UPHELD','CHANGED','REJECTED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='US-38';
