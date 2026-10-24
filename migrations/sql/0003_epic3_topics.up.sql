-- =====================================================================
-- EPIC 3: Đề tài, đăng ký, vòng đời trạng thái + Tệp dùng chung (8 bảng)
-- =====================================================================

CREATE TABLE files (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  storage_key   VARCHAR(300) NOT NULL COMMENT 'Đường dẫn trong kho; KHÔNG phục vụ công khai, tải xuống qua kiểm tra quyền',
  original_name VARCHAR(300) NOT NULL,
  mime_type     VARCHAR(120) NULL,
  size_bytes    BIGINT UNSIGNED NOT NULL,
  sha256        CHAR(64) NOT NULL,
  uploaded_by   BIGINT UNSIGNED NULL,
  uploaded_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_files_storage (storage_key),
  KEY ix_files_sha (sha256),
  CONSTRAINT fk_files_user FOREIGN KEY (uploaded_by) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='NFR-05. Chỉ lưu metadata và mã băm; nội dung nằm ở kho tệp (đã tinh giản scan_status)';

CREATE TABLE topic_states (
  code        VARCHAR(30)  NOT NULL,
  name        VARCHAR(100) NOT NULL,
  is_terminal TINYINT(1)   NOT NULL DEFAULT 0,
  sort_order  SMALLINT     NOT NULL DEFAULT 0,
  PRIMARY KEY (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Trạng thái đề tài là dữ liệu (US-14, câu K6)';

CREATE TABLE topic_transitions (
  from_state      VARCHAR(30) NOT NULL,
  to_state        VARCHAR(30) NOT NULL,
  role_code       VARCHAR(30) NOT NULL COMMENT 'Vai trò được phép thực hiện chuyển này',
  requires_reason TINYINT(1)  NOT NULL DEFAULT 0,
  PRIMARY KEY (from_state, to_state, role_code),
  CONSTRAINT fk_tt_from FOREIGN KEY (from_state) REFERENCES topic_states (code),
  CONSTRAINT fk_tt_to   FOREIGN KEY (to_state)   REFERENCES topic_states (code),
  CONSTRAINT fk_tt_role FOREIGN KEY (role_code)  REFERENCES roles (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Bảng chuyển trạng thái hợp lệ; mọi chuyển phải đi qua một hàm duy nhất ở ứng dụng';

CREATE TABLE topics (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  period_id       BIGINT UNSIGNED NOT NULL,
  code            VARCHAR(40)  NOT NULL COMMENT 'Mã đề tài tự sinh theo đợt (câu D8)',
  title           VARCHAR(500) NOT NULL,
  description     TEXT NULL,
  requirements    TEXT NULL,
  source          VARCHAR(20)  NOT NULL DEFAULT 'ADVISOR' COMMENT 'ADVISOR: giảng viên công bố; STUDENT: sinh viên đề xuất',
  capacity        SMALLINT     NOT NULL DEFAULT 1 COMMENT 'Số sinh viên nhận; khóa dòng này khi đăng ký chỗ cuối (US-10)',
  state_code      VARCHAR(30)  NOT NULL,
  org_unit_id     BIGINT UNSIGNED NULL,
  current_attempt SMALLINT     NOT NULL DEFAULT 1 COMMENT 'Lượt bảo vệ hiện tại (US-39)',
  decision_no     VARCHAR(60)  NULL,
  decision_date   DATE         NULL,
  created_by      BIGINT UNSIGNED NOT NULL,
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_topics_code (period_id, code),
  UNIQUE KEY uq_topics_id_period (id, period_id),
  KEY ix_topics_state (period_id, state_code),
  KEY ix_topics_title (title(100)),
  CONSTRAINT fk_topics_period FOREIGN KEY (period_id) REFERENCES periods (id),
  CONSTRAINT fk_topics_state  FOREIGN KEY (state_code) REFERENCES topic_states (code),
  CONSTRAINT fk_topics_org    FOREIGN KEY (org_unit_id) REFERENCES org_units (id),
  CONSTRAINT fk_topics_creator FOREIGN KEY (created_by) REFERENCES users (id),
  CONSTRAINT ck_topics_capacity CHECK (capacity >= 1),
  CONSTRAINT ck_topics_source CHECK (source IN ('ADVISOR','STUDENT'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='US-09, US-11';

CREATE TABLE topic_state_history (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  topic_id    BIGINT UNSIGNED NOT NULL,
  from_state  VARCHAR(30) NULL,
  to_state    VARCHAR(30) NOT NULL,
  actor_user_id BIGINT UNSIGNED NULL,
  reason      VARCHAR(500) NULL,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_tsh_topic (topic_id, created_at),
  CONSTRAINT fk_tsh_topic FOREIGN KEY (topic_id) REFERENCES topics (id),
  CONSTRAINT fk_tsh_from  FOREIGN KEY (from_state) REFERENCES topic_states (code),
  CONSTRAINT fk_tsh_to    FOREIGN KEY (to_state) REFERENCES topic_states (code),
  CONSTRAINT fk_tsh_actor FOREIGN KEY (actor_user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Mọi chuyển trạng thái ghi người làm và lý do (US-14)';

CREATE TABLE topic_members (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  topic_id        BIGINT UNSIGNED NOT NULL,
  period_id       BIGINT UNSIGNED NOT NULL COMMENT 'Lặp lại từ đề tài; khóa ngoại kép bảo đảm khớp',
  user_id         BIGINT UNSIGNED NOT NULL,
  role_code       VARCHAR(30) NOT NULL COMMENT 'STUDENT, ADVISOR, CO_ADVISOR, EXTERNAL_ADVISOR, REVIEWER',
  status          VARCHAR(12) NOT NULL DEFAULT 'PENDING',
  preference_rank TINYINT NULL COMMENT 'Thứ tự nguyện vọng (câu D1)',
  decision_reason VARCHAR(500) NULL,
  registered_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  decided_at      DATETIME NULL,
  decided_by      BIGINT UNSIGNED NULL,
  ended_at        DATETIME NULL,
  member_active_key  TINYINT GENERATED ALWAYS AS (IF(status IN ('PENDING','ACTIVE'), 1, NULL)) STORED,
  student_active_key BIGINT UNSIGNED GENERATED ALWAYS AS
    (IF(role_code = 'STUDENT' AND status IN ('PENDING','ACTIVE'), user_id, NULL)) STORED,
  advisor_active_key TINYINT GENERATED ALWAYS AS
    (IF(role_code = 'ADVISOR' AND status = 'ACTIVE', 1, NULL)) STORED,
  PRIMARY KEY (id),
  UNIQUE KEY uq_tm_one_active_role (topic_id, user_id, role_code, member_active_key),
  UNIQUE KEY uq_tm_student_one_per_period (period_id, student_active_key),
  UNIQUE KEY uq_tm_one_main_advisor (topic_id, advisor_active_key),
  KEY ix_tm_user (user_id, role_code, status),
  CONSTRAINT fk_tm_topic  FOREIGN KEY (topic_id, period_id) REFERENCES topics (id, period_id),
  CONSTRAINT fk_tm_user   FOREIGN KEY (user_id) REFERENCES users (id),
  CONSTRAINT fk_tm_role   FOREIGN KEY (role_code) REFERENCES roles (code),
  CONSTRAINT fk_tm_decider FOREIGN KEY (decided_by) REFERENCES users (id),
  CONSTRAINT ck_tm_status CHECK (status IN ('PENDING','ACTIVE','REJECTED','WITHDRAWN','REPLACED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Nhiều-nhiều đề tài-người có vai trò (câu E3, E7, B6)';

CREATE TABLE change_requests (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  topic_member_id BIGINT UNSIGNED NOT NULL COMMENT 'Đăng ký của sinh viên xin đổi',
  request_type  VARCHAR(20) NOT NULL,
  to_topic_id   BIGINT UNSIGNED NULL,
  to_advisor_id BIGINT UNSIGNED NULL,
  reason        VARCHAR(1000) NOT NULL,
  status        VARCHAR(12) NOT NULL DEFAULT 'PENDING',
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  resolved_at   DATETIME NULL,
  PRIMARY KEY (id),
  CONSTRAINT fk_cr_member FOREIGN KEY (topic_member_id) REFERENCES topic_members (id),
  CONSTRAINT fk_cr_topic  FOREIGN KEY (to_topic_id) REFERENCES topics (id),
  CONSTRAINT fk_cr_adv    FOREIGN KEY (to_advisor_id) REFERENCES users (id),
  CONSTRAINT ck_cr_type   CHECK (request_type IN ('CHANGE_TOPIC','CHANGE_ADVISOR')),
  CONSTRAINT ck_cr_status CHECK (status IN ('PENDING','APPROVED','REJECTED','CANCELLED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='US-16';

CREATE TABLE change_request_approvals (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  request_id  BIGINT UNSIGNED NOT NULL,
  approver_id BIGINT UNSIGNED NOT NULL,
  approver_role VARCHAR(30) NOT NULL COMMENT 'GVHD cũ, GVHD mới, trưởng bộ môn (câu E6)',
  decision    VARCHAR(10) NULL,
  comment     VARCHAR(500) NULL,
  decided_at  DATETIME NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_cra (request_id, approver_id, approver_role),
  CONSTRAINT fk_cra_req  FOREIGN KEY (request_id) REFERENCES change_requests (id) ON DELETE CASCADE,
  CONSTRAINT fk_cra_user FOREIGN KEY (approver_id) REFERENCES users (id),
  CONSTRAINT fk_cra_role FOREIGN KEY (approver_role) REFERENCES roles (code),
  CONSTRAINT ck_cra_decision CHECK (decision IS NULL OR decision IN ('APPROVE','REJECT'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
