-- =====================================================================
-- EPIC 5: Bản cuối, điều kiện bảo vệ (4 bảng)
-- =====================================================================

CREATE TABLE final_submissions (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  topic_id    BIGINT UNSIGNED NOT NULL,
  version_no  INT NOT NULL,
  submitted_by BIGINT UNSIGNED NOT NULL,
  submitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  is_current  TINYINT(1) NOT NULL DEFAULT 1,
  hardcopy_received_at DATETIME NULL COMMENT 'Ô đánh dấu bản cứng (câu G7)',
  current_key BIGINT UNSIGNED GENERATED ALWAYS AS (IF(is_current = 1, topic_id, NULL)) STORED,
  PRIMARY KEY (id),
  UNIQUE KEY uq_final_version (topic_id, version_no),
  UNIQUE KEY uq_final_one_current (current_key),
  CONSTRAINT fk_fs_topic FOREIGN KEY (topic_id) REFERENCES topics (id),
  CONSTRAINT fk_fs_user  FOREIGN KEY (submitted_by) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='US-24';

CREATE TABLE final_submission_files (
  final_submission_id BIGINT UNSIGNED NOT NULL,
  file_id BIGINT UNSIGNED NOT NULL,
  kind    VARCHAR(10) NOT NULL DEFAULT 'OTHER',
  PRIMARY KEY (final_submission_id, file_id),
  CONSTRAINT fk_fsf_fs   FOREIGN KEY (final_submission_id) REFERENCES final_submissions (id) ON DELETE CASCADE,
  CONSTRAINT fk_fsf_file FOREIGN KEY (file_id) REFERENCES files (id),
  CONSTRAINT ck_fsf_kind CHECK (kind IN ('REPORT','SLIDES','SOURCE','OTHER'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE defense_eligibility (
  topic_id              BIGINT UNSIGNED NOT NULL,
  advisor_confirmed_by  BIGINT UNSIGNED NULL,
  advisor_confirmed_at  DATETIME NULL,
  office_confirmed_by   BIGINT UNSIGNED NULL,
  office_confirmed_at   DATETIME NULL,
  note                  VARCHAR(500) NULL,
  PRIMARY KEY (topic_id),
  CONSTRAINT fk_de_topic FOREIGN KEY (topic_id) REFERENCES topics (id),
  CONSTRAINT fk_de_adv   FOREIGN KEY (advisor_confirmed_by) REFERENCES users (id),
  CONSTRAINT fk_de_off   FOREIGN KEY (office_confirmed_by) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='US-25';

CREATE TABLE similarity_checks (
  id                  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  final_submission_id BIGINT UNSIGNED NOT NULL,
  score               DECIMAL(5,2) NULL,
  matches             JSON NULL,
  report_file_id      BIGINT UNSIGNED NULL,
  checked_by          BIGINT UNSIGNED NULL,
  checked_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  CONSTRAINT fk_sim_fs   FOREIGN KEY (final_submission_id) REFERENCES final_submissions (id),
  CONSTRAINT fk_sim_file FOREIGN KEY (report_file_id) REFERENCES files (id),
  CONSTRAINT fk_sim_user FOREIGN KEY (checked_by) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='US-26';
