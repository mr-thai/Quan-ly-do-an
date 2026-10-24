-- =====================================================================
-- EPIC 1: Tài khoản, vai trò, thông báo, nhật ký (8 bảng)
-- =====================================================================

CREATE TABLE org_units (
  id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  parent_id  BIGINT UNSIGNED NULL,
  code       VARCHAR(30)  NOT NULL,
  name       VARCHAR(200) NOT NULL,
  unit_type  VARCHAR(20)  NOT NULL DEFAULT 'DEPARTMENT' COMMENT 'INSTITUTE, DEPARTMENT... là dữ liệu',
  PRIMARY KEY (id),
  UNIQUE KEY uq_org_units_code (code),
  CONSTRAINT fk_org_units_parent FOREIGN KEY (parent_id) REFERENCES org_units (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Đơn vị (Viện, bộ môn). Giả định A5: một Viện, chừa sẵn cho nhiều đơn vị';

CREATE TABLE users (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  email         VARCHAR(255) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  full_name     VARCHAR(200) NOT NULL,
  user_code     VARCHAR(30)  NULL COMMENT 'Mã sinh viên hoặc mã giảng viên',
  phone         VARCHAR(30)  NULL,
  is_active     TINYINT(1)   NOT NULL DEFAULT 1,
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_users_email (email),
  UNIQUE KEY uq_users_code (user_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Người dùng đã tích hợp mật khẩu trực tiếp cho phạm vi đồ án học tập';

CREATE TABLE student_profiles (
  user_id     BIGINT UNSIGNED NOT NULL,
  cohort      VARCHAR(20)  NULL,
  program     VARCHAR(100) NULL,
  class_name  VARCHAR(50)  NULL,
  org_unit_id BIGINT UNSIGNED NULL,
  PRIMARY KEY (user_id),
  CONSTRAINT fk_sp_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
  CONSTRAINT fk_sp_org  FOREIGN KEY (org_unit_id) REFERENCES org_units (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE staff_profiles (
  user_id        BIGINT UNSIGNED NOT NULL,
  academic_title VARCHAR(50)  NULL,
  degree         VARCHAR(50)  NULL,
  org_unit_id    BIGINT UNSIGNED NULL,
  is_external    TINYINT(1)   NOT NULL DEFAULT 0 COMMENT 'Người ngoài Viện (câu B3, E4)',
  organization   VARCHAR(200) NULL,
  PRIMARY KEY (user_id),
  CONSTRAINT fk_staff_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
  CONSTRAINT fk_staff_org  FOREIGN KEY (org_unit_id) REFERENCES org_units (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE roles (
  code  VARCHAR(30)  NOT NULL,
  name  VARCHAR(100) NOT NULL,
  scope VARCHAR(12)  NOT NULL COMMENT 'SYSTEM: gán cho tài khoản; TOPIC: vai trò trong đề tài; COMMITTEE: vai trò trong hội đồng',
  PRIMARY KEY (code),
  CONSTRAINT ck_roles_scope CHECK (scope IN ('SYSTEM','TOPIC','COMMITTEE'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Vai trò là dữ liệu: một người có nhiều vai trò theo từng ngữ cảnh (US-02)';

CREATE TABLE user_roles (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id     BIGINT UNSIGNED NOT NULL,
  role_code   VARCHAR(30) NOT NULL,
  org_unit_id BIGINT UNSIGNED NULL COMMENT 'Phạm vi đơn vị, ví dụ trưởng bộ môn của bộ môn nào',
  org_key     BIGINT UNSIGNED GENERATED ALWAYS AS (COALESCE(org_unit_id, 0)) STORED,
  PRIMARY KEY (id),
  UNIQUE KEY uq_user_role_scope (user_id, role_code, org_key),
  CONSTRAINT fk_ur_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
  CONSTRAINT fk_ur_role FOREIGN KEY (role_code) REFERENCES roles (code),
  CONSTRAINT fk_ur_org  FOREIGN KEY (org_unit_id) REFERENCES org_units (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Vai trò cấp hệ thống: giáo vụ, trưởng bộ môn, quản trị...';

CREATE TABLE notifications (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id     BIGINT UNSIGNED NOT NULL,
  event_type  VARCHAR(60)  NOT NULL,
  title       VARCHAR(200) NOT NULL,
  body        TEXT         NULL,
  ref_type    VARCHAR(40)  NULL,
  ref_id      BIGINT UNSIGNED NULL,
  is_read     TINYINT(1)   NOT NULL DEFAULT 0,
  emailed_at  DATETIME     NULL,
  created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_notif_user (user_id, is_read, created_at),
  CONSTRAINT fk_notif_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='US-04';

CREATE TABLE audit_log (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  actor_user_id BIGINT UNSIGNED NULL COMMENT 'NULL nếu hệ thống tự làm; cố ý không có khóa ngoại để giữ log',
  action        VARCHAR(60)  NOT NULL,
  entity_type   VARCHAR(40)  NOT NULL,
  entity_id     BIGINT UNSIGNED NULL,
  old_value     JSON         NULL,
  new_value     JSON         NULL,
  reason        VARCHAR(500) NULL,
  created_at    DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  KEY ix_audit_entity (entity_type, entity_id),
  KEY ix_audit_actor (actor_user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='US-05, NFR-02';
