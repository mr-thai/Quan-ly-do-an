-- =====================================================================
-- EPIC 8: Lưu trữ, mẫu văn bản (2 bảng)
-- =====================================================================

CREATE TABLE archive_records (
  topic_id       BIGINT UNSIGNED NOT NULL,
  archived_by    BIGINT UNSIGNED NULL,
  archived_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  retention_until DATE NULL,
  visibility     VARCHAR(10) NOT NULL DEFAULT 'INTERNAL',
  embargo_until  DATE NULL,
  consent_public TINYINT(1) NOT NULL DEFAULT 0,
  is_hidden      TINYINT(1) NOT NULL DEFAULT 0,
  hidden_reason  VARCHAR(500) NULL,
  PRIMARY KEY (topic_id),
  CONSTRAINT fk_arc_topic FOREIGN KEY (topic_id) REFERENCES topics (id),
  CONSTRAINT fk_arc_user  FOREIGN KEY (archived_by) REFERENCES users (id),
  CONSTRAINT ck_arc_vis CHECK (visibility IN ('INTERNAL','PUBLIC','RESTRICTED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='US-40, US-42';

CREATE TABLE document_templates (
  id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  code           VARCHAR(40)  NOT NULL COMMENT 'ASSIGNMENT_DECISION, COMMITTEE_DECISION, MINUTES, SCORE_SHEET...',
  name           VARCHAR(150) NOT NULL,
  thesis_type_id BIGINT UNSIGNED NULL,
  file_id        BIGINT UNSIGNED NOT NULL,
  version        INT NOT NULL DEFAULT 1,
  is_active      TINYINT(1) NOT NULL DEFAULT 1,
  created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_tpl (code, thesis_type_id, version),
  CONSTRAINT fk_tpl_type FOREIGN KEY (thesis_type_id) REFERENCES thesis_types (id),
  CONSTRAINT fk_tpl_file FOREIGN KEY (file_id) REFERENCES files (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='US-43';
