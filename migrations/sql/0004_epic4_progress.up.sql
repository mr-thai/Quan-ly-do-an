-- =====================================================================
-- EPIC 4: Theo dõi tiến độ (5 bảng)
-- =====================================================================

CREATE TABLE milestone_submissions (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  topic_id     BIGINT UNSIGNED NOT NULL,
  milestone_id BIGINT UNSIGNED NOT NULL,
  version_no   INT NOT NULL DEFAULT 1,
  submitted_by BIGINT UNSIGNED NOT NULL,
  note         TEXT NULL,
  is_late      TINYINT(1) NOT NULL DEFAULT 0,
  submitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_msub (topic_id, milestone_id, version_no),
  CONSTRAINT fk_msub_topic FOREIGN KEY (topic_id) REFERENCES topics (id),
  CONSTRAINT fk_msub_ms    FOREIGN KEY (milestone_id) REFERENCES period_milestones (id),
  CONSTRAINT fk_msub_user  FOREIGN KEY (submitted_by) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='US-18, giữ mọi lần nộp';

CREATE TABLE submission_files (
  submission_id BIGINT UNSIGNED NOT NULL,
  file_id       BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (submission_id, file_id),
  CONSTRAINT fk_sf_sub  FOREIGN KEY (submission_id) REFERENCES milestone_submissions (id) ON DELETE CASCADE,
  CONSTRAINT fk_sf_file FOREIGN KEY (file_id) REFERENCES files (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE milestone_reviews (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  submission_id BIGINT UNSIGNED NOT NULL,
  reviewer_id   BIGINT UNSIGNED NOT NULL,
  verdict       VARCHAR(20) NOT NULL,
  comment       TEXT NULL,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_mrev_sub (submission_id),
  CONSTRAINT fk_mrev_sub  FOREIGN KEY (submission_id) REFERENCES milestone_submissions (id),
  CONSTRAINT fk_mrev_user FOREIGN KEY (reviewer_id) REFERENCES users (id),
  CONSTRAINT ck_mrev_verdict CHECK (verdict IN ('PASS','NEEDS_REVISION'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='US-19';

CREATE TABLE supervision_meetings (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  topic_id    BIGINT UNSIGNED NOT NULL,
  held_at     DATETIME NOT NULL,
  summary     TEXT NULL,
  action_items TEXT NULL,
  student_confirmed_at DATETIME NULL,
  created_by  BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (id),
  KEY ix_sm_topic (topic_id, held_at),
  CONSTRAINT fk_sm_topic FOREIGN KEY (topic_id) REFERENCES topics (id),
  CONSTRAINT fk_sm_user  FOREIGN KEY (created_by) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='US-20';

CREATE TABLE milestone_extensions (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  topic_id     BIGINT UNSIGNED NOT NULL,
  milestone_id BIGINT UNSIGNED NOT NULL,
  new_due_at   DATETIME NOT NULL,
  reason       VARCHAR(500) NOT NULL,
  status       VARCHAR(10) NOT NULL DEFAULT 'PENDING',
  decided_by   BIGINT UNSIGNED NULL,
  created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_mext (topic_id, milestone_id, new_due_at),
  CONSTRAINT fk_mext_topic FOREIGN KEY (topic_id) REFERENCES topics (id),
  CONSTRAINT fk_mext_ms    FOREIGN KEY (milestone_id) REFERENCES period_milestones (id),
  CONSTRAINT fk_mext_user  FOREIGN KEY (decided_by) REFERENCES users (id),
  CONSTRAINT ck_mext_status CHECK (status IN ('PENDING','APPROVED','REJECTED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='US-23';
