-- =====================================================================
-- EPIC 6: Phản biện, hội đồng, lịch bảo vệ (8 bảng)
-- =====================================================================

CREATE TABLE assignment_rules (
  id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  thesis_type_id BIGINT UNSIGNED NULL COMMENT 'NULL = áp dụng cho mọi loại',
  rule_code      VARCHAR(50) NOT NULL,
  params         JSON NULL,
  severity       VARCHAR(5) NOT NULL DEFAULT 'BLOCK',
  enabled        TINYINT(1) NOT NULL DEFAULT 1,
  description    VARCHAR(300) NULL,
  PRIMARY KEY (id),
  KEY ix_ar_code (rule_code, enabled),
  CONSTRAINT fk_ar_type FOREIGN KEY (thesis_type_id) REFERENCES thesis_types (id),
  CONSTRAINT ck_ar_sev CHECK (severity IN ('BLOCK','WARN'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='US-27, US-29';

CREATE TABLE review_reports (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  topic_member_id BIGINT UNSIGNED NOT NULL COMMENT 'Dòng topic_members có role REVIEWER',
  comment         TEXT NULL,
  submitted_at    DATETIME NULL,
  locked_at       DATETIME NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_rr_member (topic_member_id),
  CONSTRAINT fk_rr_member FOREIGN KEY (topic_member_id) REFERENCES topic_members (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='US-28';

CREATE TABLE committees (
  id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  period_id  BIGINT UNSIGNED NOT NULL,
  name       VARCHAR(150) NOT NULL,
  kind       VARCHAR(12) NOT NULL DEFAULT 'DEFENSE' COMMENT 'DEFENSE, APPEAL (hội đồng phúc khảo)',
  created_by BIGINT UNSIGNED NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_committee_name (period_id, name),
  CONSTRAINT fk_com_period FOREIGN KEY (period_id) REFERENCES periods (id),
  CONSTRAINT fk_com_user   FOREIGN KEY (created_by) REFERENCES users (id),
  CONSTRAINT ck_com_kind CHECK (kind IN ('DEFENSE','APPEAL'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='US-29';

CREATE TABLE committee_members (
  committee_id BIGINT UNSIGNED NOT NULL,
  user_id      BIGINT UNSIGNED NOT NULL,
  role_code    VARCHAR(30) NOT NULL COMMENT 'CHAIR, SECRETARY, MEMBER',
  PRIMARY KEY (committee_id, user_id),
  CONSTRAINT fk_cm_com  FOREIGN KEY (committee_id) REFERENCES committees (id) ON DELETE CASCADE,
  CONSTRAINT fk_cm_user FOREIGN KEY (user_id) REFERENCES users (id),
  CONSTRAINT fk_cm_role FOREIGN KEY (role_code) REFERENCES roles (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE rooms (
  id        BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name      VARCHAR(100) NOT NULL,
  location  VARCHAR(200) NULL,
  is_online TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  UNIQUE KEY uq_rooms_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE defense_slots (
  id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  period_id  BIGINT UNSIGNED NOT NULL,
  slot_date  DATE NOT NULL,
  start_time TIME NOT NULL,
  end_time   TIME NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_slot (period_id, slot_date, start_time),
  CONSTRAINT fk_slot_period FOREIGN KEY (period_id) REFERENCES periods (id),
  CONSTRAINT ck_slot_time CHECK (end_time > start_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='US-30';

CREATE TABLE defense_sessions (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  committee_id  BIGINT UNSIGNED NOT NULL,
  room_id       BIGINT UNSIGNED NOT NULL,
  slot_id       BIGINT UNSIGNED NOT NULL,
  topic_id      BIGINT UNSIGNED NOT NULL,
  attempt_no    SMALLINT NOT NULL DEFAULT 1,
  status        VARCHAR(12) NOT NULL DEFAULT 'SCHEDULED',
  meeting_url   VARCHAR(500) NULL,
  postponed_reason VARCHAR(500) NULL,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  active_key    TINYINT GENERATED ALWAYS AS (IF(status IN ('SCHEDULED','HELD'), 1, NULL)) STORED,
  PRIMARY KEY (id),
  UNIQUE KEY uq_ds_room_slot (room_id, slot_id, active_key),
  UNIQUE KEY uq_ds_committee_slot (committee_id, slot_id, active_key),
  UNIQUE KEY uq_ds_topic_attempt (topic_id, attempt_no, active_key),
  CONSTRAINT fk_ds_com   FOREIGN KEY (committee_id) REFERENCES committees (id),
  CONSTRAINT fk_ds_room  FOREIGN KEY (room_id) REFERENCES rooms (id),
  CONSTRAINT fk_ds_slot  FOREIGN KEY (slot_id) REFERENCES defense_slots (id),
  CONSTRAINT fk_ds_topic FOREIGN KEY (topic_id) REFERENCES topics (id),
  CONSTRAINT ck_ds_status CHECK (status IN ('SCHEDULED','HELD','POSTPONED','CANCELLED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='US-30, US-32';

CREATE TABLE defense_session_participants (
  id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  session_id BIGINT UNSIGNED NOT NULL,
  slot_id    BIGINT UNSIGNED NOT NULL,
  user_id    BIGINT UNSIGNED NOT NULL,
  role_code  VARCHAR(30) NOT NULL,
  active_key TINYINT NULL COMMENT 'Ứng dụng đặt 1 khi buổi còn hiệu lực, NULL khi hoãn/hủy',
  PRIMARY KEY (id),
  UNIQUE KEY uq_dsp_person_slot (user_id, slot_id, active_key),
  UNIQUE KEY uq_dsp_session_user (session_id, user_id),
  CONSTRAINT fk_dsp_session FOREIGN KEY (session_id) REFERENCES defense_sessions (id) ON DELETE CASCADE,
  CONSTRAINT fk_dsp_slot    FOREIGN KEY (slot_id) REFERENCES defense_slots (id),
  CONSTRAINT fk_dsp_user    FOREIGN KEY (user_id) REFERENCES users (id),
  CONSTRAINT fk_dsp_role    FOREIGN KEY (role_code) REFERENCES roles (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='US-30';
