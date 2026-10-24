from typing import Optional
import datetime
import decimal

from sqlalchemy import CHAR, CheckConstraint, Column, Computed, DECIMAL, Date, DateTime, ForeignKeyConstraint, Index, Integer, JSON, SmallInteger, String, Table, Text, Time, text
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, TINYINT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class AuditLog(Base):
    __tablename__ = 'audit_log'
    __table_args__ = (
        Index('ix_audit_actor', 'actor_user_id', 'created_at'),
        Index('ix_audit_entity', 'entity_type', 'entity_id'),
        {'comment': 'US-05, NFR-02'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    action: Mapped[str] = mapped_column(String(60), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DATETIME(fsp=3), nullable=False, server_default=text('CURRENT_TIMESTAMP(3)'))
    actor_user_id: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True), comment='NULL nếu hệ thống tự làm; cố ý không có khóa ngoại để giữ log')
    entity_id: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True))
    old_value: Mapped[Optional[object]] = mapped_column(JSON)
    new_value: Mapped[Optional[object]] = mapped_column(JSON)
    reason: Mapped[Optional[str]] = mapped_column(String(500))


class OrgUnits(Base):
    __tablename__ = 'org_units'
    __table_args__ = (
        ForeignKeyConstraint(['parent_id'], ['org_units.id'], name='fk_org_units_parent'),
        Index('fk_org_units_parent', 'parent_id'),
        Index('uq_org_units_code', 'code', unique=True),
        {'comment': 'Đơn vị (Viện, bộ môn). Giả định A5: một Viện, chừa sẵn cho nhiều '
                'đơn vị'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    unit_type: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'DEPARTMENT'"), comment='INSTITUTE, DEPARTMENT... là dữ liệu')
    parent_id: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True))

    parent: Mapped[Optional['OrgUnits']] = relationship('OrgUnits', remote_side=[id], back_populates='parent_reverse')
    parent_reverse: Mapped[list['OrgUnits']] = relationship('OrgUnits', remote_side=[parent_id], back_populates='parent')
    staff_profiles: Mapped[list['StaffProfiles']] = relationship('StaffProfiles', back_populates='org_unit')
    student_profiles: Mapped[list['StudentProfiles']] = relationship('StudentProfiles', back_populates='org_unit')
    user_roles: Mapped[list['UserRoles']] = relationship('UserRoles', back_populates='org_unit')
    periods: Mapped[list['Periods']] = relationship('Periods', back_populates='org_unit')
    topics: Mapped[list['Topics']] = relationship('Topics', back_populates='org_unit')


class Roles(Base):
    __tablename__ = 'roles'
    __table_args__ = (
        CheckConstraint("(`scope` in (_utf8mb4'SYSTEM',_utf8mb4'TOPIC',_utf8mb4'COMMITTEE'))", name='ck_roles_scope'),
        {'comment': 'Vai trò là dữ liệu: một người có nhiều vai trò theo từng ngữ cảnh '
                '(US-02)'}
    )

    code: Mapped[str] = mapped_column(String(30), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    scope: Mapped[str] = mapped_column(String(12), nullable=False, comment='SYSTEM: gán cho tài khoản; TOPIC: vai trò trong đề tài; COMMITTEE: vai trò trong hội đồng')

    topic_transitions: Mapped[list['TopicTransitions']] = relationship('TopicTransitions', back_populates='roles')
    user_roles: Mapped[list['UserRoles']] = relationship('UserRoles', back_populates='roles')
    committee_members: Mapped[list['CommitteeMembers']] = relationship('CommitteeMembers', back_populates='roles')
    topic_members: Mapped[list['TopicMembers']] = relationship('TopicMembers', back_populates='roles')
    defense_session_participants: Mapped[list['DefenseSessionParticipants']] = relationship('DefenseSessionParticipants', back_populates='roles')
    change_request_approvals: Mapped[list['ChangeRequestApprovals']] = relationship('ChangeRequestApprovals', back_populates='roles')


class Rooms(Base):
    __tablename__ = 'rooms'
    __table_args__ = (
        Index('uq_rooms_name', 'name', unique=True),
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_online: Mapped[int] = mapped_column(TINYINT(1), nullable=False, server_default=text("'0'"))
    location: Mapped[Optional[str]] = mapped_column(String(200))

    defense_sessions: Mapped[list['DefenseSessions']] = relationship('DefenseSessions', back_populates='room')


class ThesisTypes(Base):
    __tablename__ = 'thesis_types'
    __table_args__ = (
        Index('uq_thesis_types_code', 'code', unique=True),
        {'comment': 'Loại đồ án là dữ liệu (A1, A2): thêm loại là thêm một dòng'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    is_active: Mapped[int] = mapped_column(TINYINT(1), nullable=False, server_default=text("'1'"))

    assignment_rules: Mapped[list['AssignmentRules']] = relationship('AssignmentRules', back_populates='thesis_type')
    grading_formulas: Mapped[list['GradingFormulas']] = relationship('GradingFormulas', back_populates='thesis_type')
    thesis_type_steps: Mapped[list['ThesisTypeSteps']] = relationship('ThesisTypeSteps', back_populates='thesis_type')
    document_templates: Mapped[list['DocumentTemplates']] = relationship('DocumentTemplates', back_populates='thesis_type')
    periods: Mapped[list['Periods']] = relationship('Periods', back_populates='thesis_type')


class TopicStates(Base):
    __tablename__ = 'topic_states'
    __table_args__ = {'comment': 'Trạng thái đề tài là dữ liệu (US-14, câu K6)'}

    code: Mapped[str] = mapped_column(String(30), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_terminal: Mapped[int] = mapped_column(TINYINT(1), nullable=False, server_default=text("'0'"))
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("'0'"))

    topic_transitions_from_state: Mapped[list['TopicTransitions']] = relationship('TopicTransitions', foreign_keys='[TopicTransitions.from_state]', back_populates='topic_states')
    topic_transitions_to_state: Mapped[list['TopicTransitions']] = relationship('TopicTransitions', foreign_keys='[TopicTransitions.to_state]', back_populates='topic_states_')
    topics: Mapped[list['Topics']] = relationship('Topics', back_populates='topic_states')
    topic_state_history_from_state: Mapped[list['TopicStateHistory']] = relationship('TopicStateHistory', foreign_keys='[TopicStateHistory.from_state]', back_populates='topic_states')
    topic_state_history_to_state: Mapped[list['TopicStateHistory']] = relationship('TopicStateHistory', foreign_keys='[TopicStateHistory.to_state]', back_populates='topic_states_')


class Users(Base):
    __tablename__ = 'users'
    __table_args__ = (
        Index('uq_users_code', 'user_code', unique=True),
        Index('uq_users_email', 'email', unique=True),
        {'comment': 'Người dùng đã tích hợp mật khẩu trực tiếp cho phạm vi đồ án học '
                'tập'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[int] = mapped_column(TINYINT(1), nullable=False, server_default=text("'1'"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    user_code: Mapped[Optional[str]] = mapped_column(String(30), comment='Mã sinh viên hoặc mã giảng viên')
    phone: Mapped[Optional[str]] = mapped_column(String(30))

    files: Mapped[list['Files']] = relationship('Files', back_populates='users')
    grading_formulas: Mapped[list['GradingFormulas']] = relationship('GradingFormulas', back_populates='users')
    notifications: Mapped[list['Notifications']] = relationship('Notifications', back_populates='user')
    user_roles: Mapped[list['UserRoles']] = relationship('UserRoles', back_populates='user')
    advisor_quota_overrides_approved_by: Mapped[list['AdvisorQuotaOverrides']] = relationship('AdvisorQuotaOverrides', foreign_keys='[AdvisorQuotaOverrides.approved_by]', back_populates='users')
    advisor_quota_overrides_user: Mapped[list['AdvisorQuotaOverrides']] = relationship('AdvisorQuotaOverrides', foreign_keys='[AdvisorQuotaOverrides.user_id]', back_populates='user')
    committees: Mapped[list['Committees']] = relationship('Committees', back_populates='users')
    topics: Mapped[list['Topics']] = relationship('Topics', foreign_keys='[Topics.created_by]', back_populates='users')
    archive_records: Mapped[list['ArchiveRecords']] = relationship('ArchiveRecords', foreign_keys='[ArchiveRecords.archived_by]', back_populates='users')
    committee_members: Mapped[list['CommitteeMembers']] = relationship('CommitteeMembers', back_populates='user')
    defense_eligibility_advisor_confirmed_by: Mapped[list['DefenseEligibility']] = relationship('DefenseEligibility', foreign_keys='[DefenseEligibility.advisor_confirmed_by]', back_populates='users')
    defense_eligibility_office_confirmed_by: Mapped[list['DefenseEligibility']] = relationship('DefenseEligibility', foreign_keys='[DefenseEligibility.office_confirmed_by]', back_populates='users_')
    final_submissions: Mapped[list['FinalSubmissions']] = relationship('FinalSubmissions', back_populates='users')
    grade_appeals: Mapped[list['GradeAppeals']] = relationship('GradeAppeals', back_populates='student_user')
    grade_results: Mapped[list['GradeResults']] = relationship('GradeResults', back_populates='users')
    milestone_extensions: Mapped[list['MilestoneExtensions']] = relationship('MilestoneExtensions', back_populates='users')
    milestone_submissions: Mapped[list['MilestoneSubmissions']] = relationship('MilestoneSubmissions', back_populates='users')
    revision_submissions: Mapped[list['RevisionSubmissions']] = relationship('RevisionSubmissions', back_populates='users')
    score_entries: Mapped[list['ScoreEntries']] = relationship('ScoreEntries', back_populates='scorer_user')
    supervision_meetings: Mapped[list['SupervisionMeetings']] = relationship('SupervisionMeetings', back_populates='users')
    topic_members_decided_by: Mapped[list['TopicMembers']] = relationship('TopicMembers', foreign_keys='[TopicMembers.decided_by]', back_populates='users')
    topic_members_user: Mapped[list['TopicMembers']] = relationship('TopicMembers', foreign_keys='[TopicMembers.user_id]', back_populates='user')
    topic_state_history: Mapped[list['TopicStateHistory']] = relationship('TopicStateHistory', back_populates='actor_user')
    change_requests: Mapped[list['ChangeRequests']] = relationship('ChangeRequests', back_populates='to_advisor')
    defense_minutes: Mapped[list['DefenseMinutes']] = relationship('DefenseMinutes', back_populates='secretary')
    defense_session_participants: Mapped[list['DefenseSessionParticipants']] = relationship('DefenseSessionParticipants', back_populates='user')
    milestone_reviews: Mapped[list['MilestoneReviews']] = relationship('MilestoneReviews', back_populates='reviewer')
    similarity_checks: Mapped[list['SimilarityChecks']] = relationship('SimilarityChecks', back_populates='users')
    change_request_approvals: Mapped[list['ChangeRequestApprovals']] = relationship('ChangeRequestApprovals', back_populates='approver')


class AssignmentRules(Base):
    __tablename__ = 'assignment_rules'
    __table_args__ = (
        CheckConstraint("(`severity` in (_utf8mb4'BLOCK',_utf8mb4'WARN'))", name='ck_ar_sev'),
        ForeignKeyConstraint(['thesis_type_id'], ['thesis_types.id'], name='fk_ar_type'),
        Index('fk_ar_type', 'thesis_type_id'),
        Index('ix_ar_code', 'rule_code', 'enabled'),
        {'comment': 'US-27, US-29'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    rule_code: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(5), nullable=False, server_default=text("'BLOCK'"))
    enabled: Mapped[int] = mapped_column(TINYINT(1), nullable=False, server_default=text("'1'"))
    thesis_type_id: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True), comment='NULL = áp dụng cho mọi loại')
    params: Mapped[Optional[object]] = mapped_column(JSON)
    description: Mapped[Optional[str]] = mapped_column(String(300))

    thesis_type: Mapped[Optional['ThesisTypes']] = relationship('ThesisTypes', back_populates='assignment_rules')


class Files(Base):
    __tablename__ = 'files'
    __table_args__ = (
        ForeignKeyConstraint(['uploaded_by'], ['users.id'], name='fk_files_user'),
        Index('fk_files_user', 'uploaded_by'),
        Index('ix_files_sha', 'sha256'),
        Index('uq_files_storage', 'storage_key', unique=True),
        {'comment': 'NFR-05. Chỉ lưu metadata và mã băm; nội dung nằm ở kho tệp (đã '
                'tinh giản scan_status)'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    storage_key: Mapped[str] = mapped_column(String(300), nullable=False, comment='Đường dẫn trong kho; KHÔNG phục vụ công khai, tải xuống qua kiểm tra quyền')
    original_name: Mapped[str] = mapped_column(String(300), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    sha256: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    uploaded_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    mime_type: Mapped[Optional[str]] = mapped_column(String(120))
    uploaded_by: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True))

    users: Mapped[Optional['Users']] = relationship('Users', back_populates='files')
    submission: Mapped[list['MilestoneSubmissions']] = relationship('MilestoneSubmissions', secondary='submission_files', back_populates='file')
    document_templates: Mapped[list['DocumentTemplates']] = relationship('DocumentTemplates', back_populates='file')
    revision_submissions: Mapped[list['RevisionSubmissions']] = relationship('RevisionSubmissions', back_populates='file')
    final_submission_files: Mapped[list['FinalSubmissionFiles']] = relationship('FinalSubmissionFiles', back_populates='file')
    similarity_checks: Mapped[list['SimilarityChecks']] = relationship('SimilarityChecks', back_populates='report_file')


class GradingFormulas(Base):
    __tablename__ = 'grading_formulas'
    __table_args__ = (
        ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_formula_user'),
        ForeignKeyConstraint(['thesis_type_id'], ['thesis_types.id'], name='fk_formula_type'),
        Index('fk_formula_user', 'created_by'),
        Index('uq_formula_version', 'thesis_type_id', 'version', unique=True),
        {'comment': 'US-08. Bất biến: đổi công thức là tạo version mới, đợt cũ giữ '
                'công thức cũ (câu J8)'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    thesis_type_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    scale_max: Mapped[decimal.Decimal] = mapped_column(DECIMAL(5, 2), nullable=False, server_default=text("'10.00'"))
    is_sample: Mapped[int] = mapped_column(TINYINT(1), nullable=False, server_default=text("'0'"), comment='1 = công thức mẫu để thử, KHÔNG dùng chấm thật')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    rounding: Mapped[Optional[object]] = mapped_column(JSON, comment='Quy tắc làm tròn từng bước (câu J2)')
    combine_rule: Mapped[Optional[object]] = mapped_column(JSON, comment='Cách gộp điểm thành viên và thành phần (câu J3)')
    pass_threshold: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(5, 2), comment='Câu J4: chưa biết')
    created_by: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True))

    users: Mapped[Optional['Users']] = relationship('Users', back_populates='grading_formulas')
    thesis_type: Mapped['ThesisTypes'] = relationship('ThesisTypes', back_populates='grading_formulas')
    grading_criteria: Mapped[list['GradingCriteria']] = relationship('GradingCriteria', back_populates='formula')
    periods: Mapped[list['Periods']] = relationship('Periods', back_populates='formula')
    grade_results: Mapped[list['GradeResults']] = relationship('GradeResults', back_populates='formula')


class Notifications(Base):
    __tablename__ = 'notifications'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='fk_notif_user'),
        Index('ix_notif_user', 'user_id', 'is_read', 'created_at'),
        {'comment': 'US-04'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    is_read: Mapped[int] = mapped_column(TINYINT(1), nullable=False, server_default=text("'0'"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    body: Mapped[Optional[str]] = mapped_column(Text)
    ref_type: Mapped[Optional[str]] = mapped_column(String(40))
    ref_id: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True))
    emailed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    user: Mapped['Users'] = relationship('Users', back_populates='notifications')


class StaffProfiles(Users):
    __tablename__ = 'staff_profiles'
    __table_args__ = (
        ForeignKeyConstraint(['org_unit_id'], ['org_units.id'], name='fk_staff_org'),
        ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='fk_staff_user'),
        Index('fk_staff_org', 'org_unit_id')
    )

    user_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    is_external: Mapped[int] = mapped_column(TINYINT(1), nullable=False, server_default=text("'0'"), comment='Người ngoài Viện (câu B3, E4)')
    academic_title: Mapped[Optional[str]] = mapped_column(String(50))
    degree: Mapped[Optional[str]] = mapped_column(String(50))
    org_unit_id: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True))
    organization: Mapped[Optional[str]] = mapped_column(String(200))

    org_unit: Mapped[Optional['OrgUnits']] = relationship('OrgUnits', back_populates='staff_profiles')


class StudentProfiles(Users):
    __tablename__ = 'student_profiles'
    __table_args__ = (
        ForeignKeyConstraint(['org_unit_id'], ['org_units.id'], name='fk_sp_org'),
        ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='fk_sp_user'),
        Index('fk_sp_org', 'org_unit_id')
    )

    user_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    cohort: Mapped[Optional[str]] = mapped_column(String(20))
    program: Mapped[Optional[str]] = mapped_column(String(100))
    class_name: Mapped[Optional[str]] = mapped_column(String(50))
    org_unit_id: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True))

    org_unit: Mapped[Optional['OrgUnits']] = relationship('OrgUnits', back_populates='student_profiles')


class ThesisTypeSteps(Base):
    __tablename__ = 'thesis_type_steps'
    __table_args__ = (
        ForeignKeyConstraint(['thesis_type_id'], ['thesis_types.id'], ondelete='CASCADE', name='fk_tts_type'),
    )

    thesis_type_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    step_code: Mapped[str] = mapped_column(String(30), primary_key=True, comment='PROPOSAL, MIDTERM, REVIEW, COMMITTEE, FINAL, REVISION...')
    enabled: Mapped[int] = mapped_column(TINYINT(1), nullable=False, server_default=text("'1'"), comment='Bật/tắt bước theo loại, ví dụ loại không có phản biện')
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("'0'"))
    params: Mapped[Optional[object]] = mapped_column(JSON)

    thesis_type: Mapped['ThesisTypes'] = relationship('ThesisTypes', back_populates='thesis_type_steps')


class TopicTransitions(Base):
    __tablename__ = 'topic_transitions'
    __table_args__ = (
        ForeignKeyConstraint(['from_state'], ['topic_states.code'], name='fk_tt_from'),
        ForeignKeyConstraint(['role_code'], ['roles.code'], name='fk_tt_role'),
        ForeignKeyConstraint(['to_state'], ['topic_states.code'], name='fk_tt_to'),
        Index('fk_tt_role', 'role_code'),
        Index('fk_tt_to', 'to_state'),
        {'comment': 'Bảng chuyển trạng thái hợp lệ; mọi chuyển phải đi qua một hàm duy '
                'nhất ở ứng dụng'}
    )

    from_state: Mapped[str] = mapped_column(String(30), primary_key=True)
    to_state: Mapped[str] = mapped_column(String(30), primary_key=True)
    role_code: Mapped[str] = mapped_column(String(30), primary_key=True, comment='Vai trò được phép thực hiện chuyển này')
    requires_reason: Mapped[int] = mapped_column(TINYINT(1), nullable=False, server_default=text("'0'"))

    topic_states: Mapped['TopicStates'] = relationship('TopicStates', foreign_keys=[from_state], back_populates='topic_transitions_from_state')
    roles: Mapped['Roles'] = relationship('Roles', back_populates='topic_transitions')
    topic_states_: Mapped['TopicStates'] = relationship('TopicStates', foreign_keys=[to_state], back_populates='topic_transitions_to_state')


class UserRoles(Base):
    __tablename__ = 'user_roles'
    __table_args__ = (
        ForeignKeyConstraint(['org_unit_id'], ['org_units.id'], name='fk_ur_org'),
        ForeignKeyConstraint(['role_code'], ['roles.code'], name='fk_ur_role'),
        ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='fk_ur_user'),
        Index('fk_ur_org', 'org_unit_id'),
        Index('fk_ur_role', 'role_code'),
        Index('uq_user_role_scope', 'user_id', 'role_code', 'org_key', unique=True),
        {'comment': 'Vai trò cấp hệ thống: giáo vụ, trưởng bộ môn, quản trị...'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    role_code: Mapped[str] = mapped_column(String(30), nullable=False)
    org_unit_id: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True), comment='Phạm vi đơn vị, ví dụ trưởng bộ môn của bộ môn nào')
    org_key: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True), Computed('(coalesce(`org_unit_id`,0))', persisted=True))

    org_unit: Mapped[Optional['OrgUnits']] = relationship('OrgUnits', back_populates='user_roles')
    roles: Mapped['Roles'] = relationship('Roles', back_populates='user_roles')
    user: Mapped['Users'] = relationship('Users', back_populates='user_roles')


class DocumentTemplates(Base):
    __tablename__ = 'document_templates'
    __table_args__ = (
        ForeignKeyConstraint(['file_id'], ['files.id'], name='fk_tpl_file'),
        ForeignKeyConstraint(['thesis_type_id'], ['thesis_types.id'], name='fk_tpl_type'),
        Index('fk_tpl_file', 'file_id'),
        Index('fk_tpl_type', 'thesis_type_id'),
        Index('uq_tpl', 'code', 'thesis_type_id', 'version', unique=True),
        {'comment': 'US-43'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(40), nullable=False, comment='ASSIGNMENT_DECISION, COMMITTEE_DECISION, MINUTES, SCORE_SHEET...')
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    file_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("'1'"))
    is_active: Mapped[int] = mapped_column(TINYINT(1), nullable=False, server_default=text("'1'"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    thesis_type_id: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True))

    file: Mapped['Files'] = relationship('Files', back_populates='document_templates')
    thesis_type: Mapped[Optional['ThesisTypes']] = relationship('ThesisTypes', back_populates='document_templates')


class GradingCriteria(Base):
    __tablename__ = 'grading_criteria'
    __table_args__ = (
        CheckConstraint('(`weight` >= 0)', name='ck_criteria_weight'),
        ForeignKeyConstraint(['formula_id'], ['grading_formulas.id'], ondelete='CASCADE', name='fk_criteria_formula'),
        Index('uq_criteria_code', 'formula_id', 'code', unique=True)
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    formula_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    scorer_kind: Mapped[str] = mapped_column(String(20), nullable=False, comment='ADVISOR, REVIEWER, COMMITTEE, PROCESS')
    weight: Mapped[decimal.Decimal] = mapped_column(DECIMAL(6, 3), nullable=False)
    max_score: Mapped[decimal.Decimal] = mapped_column(DECIMAL(5, 2), nullable=False, server_default=text("'10.00'"))
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("'0'"))

    formula: Mapped['GradingFormulas'] = relationship('GradingFormulas', back_populates='grading_criteria')
    score_entries: Mapped[list['ScoreEntries']] = relationship('ScoreEntries', back_populates='criterion')


class Periods(Base):
    __tablename__ = 'periods'
    __table_args__ = (
        CheckConstraint("(`status` in (_utf8mb4'DRAFT',_utf8mb4'OPEN',_utf8mb4'CLOSED',_utf8mb4'ARCHIVED'))", name='ck_periods_status'),
        ForeignKeyConstraint(['formula_id'], ['grading_formulas.id'], name='fk_periods_formula'),
        ForeignKeyConstraint(['org_unit_id'], ['org_units.id'], name='fk_periods_org'),
        ForeignKeyConstraint(['thesis_type_id'], ['thesis_types.id'], name='fk_periods_type'),
        Index('fk_periods_formula', 'formula_id'),
        Index('fk_periods_org', 'org_unit_id'),
        Index('ix_periods_type', 'thesis_type_id', 'status'),
        {'comment': 'US-06'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    thesis_type_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    status: Mapped[str] = mapped_column(String(12), nullable=False, server_default=text("'DRAFT'"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    org_unit_id: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True))
    academic_year: Mapped[Optional[str]] = mapped_column(String(9))
    term: Mapped[Optional[str]] = mapped_column(String(20))
    formula_id: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True))
    default_advisor_quota: Mapped[Optional[int]] = mapped_column(SmallInteger, comment='Hạn mức mặc định mỗi GVHD (câu E1)')
    params: Mapped[Optional[object]] = mapped_column(JSON, comment='Tham số của đợt: số lần bảo vệ lại, hạn phúc khảo, hạn nộp chỉnh sửa, ngưỡng trùng lặp...')

    formula: Mapped[Optional['GradingFormulas']] = relationship('GradingFormulas', back_populates='periods')
    org_unit: Mapped[Optional['OrgUnits']] = relationship('OrgUnits', back_populates='periods')
    thesis_type: Mapped['ThesisTypes'] = relationship('ThesisTypes', back_populates='periods')
    advisor_quota_overrides: Mapped[list['AdvisorQuotaOverrides']] = relationship('AdvisorQuotaOverrides', back_populates='period')
    committees: Mapped[list['Committees']] = relationship('Committees', back_populates='period')
    defense_slots: Mapped[list['DefenseSlots']] = relationship('DefenseSlots', back_populates='period')
    period_milestones: Mapped[list['PeriodMilestones']] = relationship('PeriodMilestones', back_populates='period')
    topics: Mapped[list['Topics']] = relationship('Topics', back_populates='period')


class AdvisorQuotaOverrides(Base):
    __tablename__ = 'advisor_quota_overrides'
    __table_args__ = (
        ForeignKeyConstraint(['approved_by'], ['users.id'], name='fk_aqo_appr'),
        ForeignKeyConstraint(['period_id'], ['periods.id'], ondelete='CASCADE', name='fk_aqo_period'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_aqo_user'),
        Index('fk_aqo_appr', 'approved_by'),
        Index('fk_aqo_user', 'user_id'),
        {'comment': 'Ngoại lệ hạn mức có ghi lý do (US-07, câu E2)'}
    )

    period_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    user_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    max_students: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    reason: Mapped[Optional[str]] = mapped_column(String(300))
    approved_by: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True))

    users: Mapped[Optional['Users']] = relationship('Users', foreign_keys=[approved_by], back_populates='advisor_quota_overrides_approved_by')
    period: Mapped['Periods'] = relationship('Periods', back_populates='advisor_quota_overrides')
    user: Mapped['Users'] = relationship('Users', foreign_keys=[user_id], back_populates='advisor_quota_overrides_user')


class Committees(Base):
    __tablename__ = 'committees'
    __table_args__ = (
        CheckConstraint("(`kind` in (_utf8mb4'DEFENSE',_utf8mb4'APPEAL'))", name='ck_com_kind'),
        ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_com_user'),
        ForeignKeyConstraint(['period_id'], ['periods.id'], name='fk_com_period'),
        Index('fk_com_user', 'created_by'),
        Index('uq_committee_name', 'period_id', 'name', unique=True),
        {'comment': 'US-29'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    period_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    kind: Mapped[str] = mapped_column(String(12), nullable=False, server_default=text("'DEFENSE'"), comment='DEFENSE, APPEAL (hội đồng phúc khảo)')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    created_by: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True))

    users: Mapped[Optional['Users']] = relationship('Users', back_populates='committees')
    period: Mapped['Periods'] = relationship('Periods', back_populates='committees')
    committee_members: Mapped[list['CommitteeMembers']] = relationship('CommitteeMembers', back_populates='committee')
    defense_sessions: Mapped[list['DefenseSessions']] = relationship('DefenseSessions', back_populates='committee')
    grade_appeals: Mapped[list['GradeAppeals']] = relationship('GradeAppeals', back_populates='appeal_committee')


class DefenseSlots(Base):
    __tablename__ = 'defense_slots'
    __table_args__ = (
        CheckConstraint('(`end_time` > `start_time`)', name='ck_slot_time'),
        ForeignKeyConstraint(['period_id'], ['periods.id'], name='fk_slot_period'),
        Index('uq_slot', 'period_id', 'slot_date', 'start_time', unique=True),
        {'comment': 'US-30'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    period_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    slot_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    start_time: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    end_time: Mapped[datetime.time] = mapped_column(Time, nullable=False)

    period: Mapped['Periods'] = relationship('Periods', back_populates='defense_slots')
    defense_sessions: Mapped[list['DefenseSessions']] = relationship('DefenseSessions', back_populates='slot')
    defense_session_participants: Mapped[list['DefenseSessionParticipants']] = relationship('DefenseSessionParticipants', back_populates='slot')


class PeriodMilestones(Base):
    __tablename__ = 'period_milestones'
    __table_args__ = (
        ForeignKeyConstraint(['period_id'], ['periods.id'], ondelete='CASCADE', name='fk_ms_period'),
        Index('uq_milestone_code', 'period_id', 'code', unique=True),
        {'comment': 'Mốc là dữ liệu theo đợt (câu C1)'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    period_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    due_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    hard_lock: Mapped[int] = mapped_column(TINYINT(1), nullable=False, server_default=text("'0'"), comment='Câu C2: tạm chỉ cảnh báo, không khóa cứng')
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("'0'"))

    period: Mapped['Periods'] = relationship('Periods', back_populates='period_milestones')
    milestone_extensions: Mapped[list['MilestoneExtensions']] = relationship('MilestoneExtensions', back_populates='milestone')
    milestone_submissions: Mapped[list['MilestoneSubmissions']] = relationship('MilestoneSubmissions', back_populates='milestone')


class Topics(Base):
    __tablename__ = 'topics'
    __table_args__ = (
        CheckConstraint('(`capacity` >= 1)', name='ck_topics_capacity'),
        CheckConstraint("(`source` in (_utf8mb4'ADVISOR',_utf8mb4'STUDENT'))", name='ck_topics_source'),
        ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_topics_creator'),
        ForeignKeyConstraint(['org_unit_id'], ['org_units.id'], name='fk_topics_org'),
        ForeignKeyConstraint(['period_id'], ['periods.id'], name='fk_topics_period'),
        ForeignKeyConstraint(['state_code'], ['topic_states.code'], name='fk_topics_state'),
        Index('fk_topics_creator', 'created_by'),
        Index('fk_topics_org', 'org_unit_id'),
        Index('fk_topics_state', 'state_code'),
        Index('ix_topics_state', 'period_id', 'state_code'),
        Index('ix_topics_title', 'title', mysql_length={'title': 100}),
        Index('uq_topics_code', 'period_id', 'code', unique=True),
        Index('uq_topics_id_period', 'id', 'period_id', unique=True),
        {'comment': 'US-09, US-11'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    period_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False, comment='Mã đề tài tự sinh theo đợt (câu D8)')
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'ADVISOR'"), comment='ADVISOR: giảng viên công bố; STUDENT: sinh viên đề xuất')
    capacity: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("'1'"), comment='Số sinh viên nhận; khóa dòng này khi đăng ký chỗ cuối (US-10)')
    state_code: Mapped[str] = mapped_column(String(30), nullable=False)
    current_attempt: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("'1'"), comment='Lượt bảo vệ hiện tại (US-39)')
    created_by: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    description: Mapped[Optional[str]] = mapped_column(Text)
    requirements: Mapped[Optional[str]] = mapped_column(Text)
    org_unit_id: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True))
    decision_no: Mapped[Optional[str]] = mapped_column(String(60))
    decision_date: Mapped[Optional[datetime.date]] = mapped_column(Date)

    users: Mapped['Users'] = relationship('Users', foreign_keys=[created_by], back_populates='topics')
    org_unit: Mapped[Optional['OrgUnits']] = relationship('OrgUnits', back_populates='topics')
    period: Mapped['Periods'] = relationship('Periods', back_populates='topics')
    topic_states: Mapped['TopicStates'] = relationship('TopicStates', back_populates='topics')
    defense_sessions: Mapped[list['DefenseSessions']] = relationship('DefenseSessions', back_populates='topic')
    final_submissions: Mapped[list['FinalSubmissions']] = relationship('FinalSubmissions', back_populates='topic')
    grade_appeals: Mapped[list['GradeAppeals']] = relationship('GradeAppeals', back_populates='topic')
    grade_results: Mapped[list['GradeResults']] = relationship('GradeResults', back_populates='topic')
    milestone_extensions: Mapped[list['MilestoneExtensions']] = relationship('MilestoneExtensions', back_populates='topic')
    milestone_submissions: Mapped[list['MilestoneSubmissions']] = relationship('MilestoneSubmissions', back_populates='topic')
    revision_submissions: Mapped[list['RevisionSubmissions']] = relationship('RevisionSubmissions', back_populates='topic')
    score_entries: Mapped[list['ScoreEntries']] = relationship('ScoreEntries', back_populates='topic')
    supervision_meetings: Mapped[list['SupervisionMeetings']] = relationship('SupervisionMeetings', back_populates='topic')
    topic_members: Mapped[list['TopicMembers']] = relationship('TopicMembers', back_populates='topics')
    topic_state_history: Mapped[list['TopicStateHistory']] = relationship('TopicStateHistory', back_populates='topic')
    change_requests: Mapped[list['ChangeRequests']] = relationship('ChangeRequests', back_populates='to_topic')


class ArchiveRecords(Topics):
    __tablename__ = 'archive_records'
    __table_args__ = (
        CheckConstraint("(`visibility` in (_utf8mb4'INTERNAL',_utf8mb4'PUBLIC',_utf8mb4'RESTRICTED'))", name='ck_arc_vis'),
        ForeignKeyConstraint(['archived_by'], ['users.id'], name='fk_arc_user'),
        ForeignKeyConstraint(['topic_id'], ['topics.id'], name='fk_arc_topic'),
        Index('fk_arc_user', 'archived_by'),
        {'comment': 'US-40, US-42'}
    )

    topic_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    archived_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    visibility: Mapped[str] = mapped_column(String(10), nullable=False, server_default=text("'INTERNAL'"))
    consent_public: Mapped[int] = mapped_column(TINYINT(1), nullable=False, server_default=text("'0'"))
    is_hidden: Mapped[int] = mapped_column(TINYINT(1), nullable=False, server_default=text("'0'"))
    archived_by: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True))
    retention_until: Mapped[Optional[datetime.date]] = mapped_column(Date)
    embargo_until: Mapped[Optional[datetime.date]] = mapped_column(Date)
    hidden_reason: Mapped[Optional[str]] = mapped_column(String(500))

    users: Mapped[Optional['Users']] = relationship('Users', foreign_keys=[archived_by], back_populates='archive_records')


class CommitteeMembers(Base):
    __tablename__ = 'committee_members'
    __table_args__ = (
        ForeignKeyConstraint(['committee_id'], ['committees.id'], ondelete='CASCADE', name='fk_cm_com'),
        ForeignKeyConstraint(['role_code'], ['roles.code'], name='fk_cm_role'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_cm_user'),
        Index('fk_cm_role', 'role_code'),
        Index('fk_cm_user', 'user_id')
    )

    committee_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    user_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    role_code: Mapped[str] = mapped_column(String(30), nullable=False, comment='CHAIR, SECRETARY, MEMBER')

    committee: Mapped['Committees'] = relationship('Committees', back_populates='committee_members')
    roles: Mapped['Roles'] = relationship('Roles', back_populates='committee_members')
    user: Mapped['Users'] = relationship('Users', back_populates='committee_members')


class DefenseEligibility(Topics):
    __tablename__ = 'defense_eligibility'
    __table_args__ = (
        ForeignKeyConstraint(['advisor_confirmed_by'], ['users.id'], name='fk_de_adv'),
        ForeignKeyConstraint(['office_confirmed_by'], ['users.id'], name='fk_de_off'),
        ForeignKeyConstraint(['topic_id'], ['topics.id'], name='fk_de_topic'),
        Index('fk_de_adv', 'advisor_confirmed_by'),
        Index('fk_de_off', 'office_confirmed_by'),
        {'comment': 'US-25'}
    )

    topic_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    advisor_confirmed_by: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True))
    advisor_confirmed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    office_confirmed_by: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True))
    office_confirmed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    note: Mapped[Optional[str]] = mapped_column(String(500))

    users: Mapped[Optional['Users']] = relationship('Users', foreign_keys=[advisor_confirmed_by], back_populates='defense_eligibility_advisor_confirmed_by')
    users_: Mapped[Optional['Users']] = relationship('Users', foreign_keys=[office_confirmed_by], back_populates='defense_eligibility_office_confirmed_by')


class DefenseSessions(Base):
    __tablename__ = 'defense_sessions'
    __table_args__ = (
        CheckConstraint("(`status` in (_utf8mb4'SCHEDULED',_utf8mb4'HELD',_utf8mb4'POSTPONED',_utf8mb4'CANCELLED'))", name='ck_ds_status'),
        ForeignKeyConstraint(['committee_id'], ['committees.id'], name='fk_ds_com'),
        ForeignKeyConstraint(['room_id'], ['rooms.id'], name='fk_ds_room'),
        ForeignKeyConstraint(['slot_id'], ['defense_slots.id'], name='fk_ds_slot'),
        ForeignKeyConstraint(['topic_id'], ['topics.id'], name='fk_ds_topic'),
        Index('fk_ds_slot', 'slot_id'),
        Index('uq_ds_committee_slot', 'committee_id', 'slot_id', 'active_key', unique=True),
        Index('uq_ds_room_slot', 'room_id', 'slot_id', 'active_key', unique=True),
        Index('uq_ds_topic_attempt', 'topic_id', 'attempt_no', 'active_key', unique=True),
        {'comment': 'US-30, US-32'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    committee_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    room_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    slot_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    topic_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    attempt_no: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("'1'"))
    status: Mapped[str] = mapped_column(String(12), nullable=False, server_default=text("'SCHEDULED'"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    meeting_url: Mapped[Optional[str]] = mapped_column(String(500))
    postponed_reason: Mapped[Optional[str]] = mapped_column(String(500))
    active_key: Mapped[Optional[int]] = mapped_column(TINYINT, Computed("(if((`status` in (_utf8mb4'SCHEDULED',_utf8mb4'HELD')),1,NULL))", persisted=True))

    committee: Mapped['Committees'] = relationship('Committees', back_populates='defense_sessions')
    room: Mapped['Rooms'] = relationship('Rooms', back_populates='defense_sessions')
    slot: Mapped['DefenseSlots'] = relationship('DefenseSlots', back_populates='defense_sessions')
    topic: Mapped['Topics'] = relationship('Topics', back_populates='defense_sessions')
    defense_minutes: Mapped[list['DefenseMinutes']] = relationship('DefenseMinutes', back_populates='session')
    defense_session_participants: Mapped[list['DefenseSessionParticipants']] = relationship('DefenseSessionParticipants', back_populates='session')


class FinalSubmissions(Base):
    __tablename__ = 'final_submissions'
    __table_args__ = (
        ForeignKeyConstraint(['submitted_by'], ['users.id'], name='fk_fs_user'),
        ForeignKeyConstraint(['topic_id'], ['topics.id'], name='fk_fs_topic'),
        Index('fk_fs_user', 'submitted_by'),
        Index('uq_final_one_current', 'current_key', unique=True),
        Index('uq_final_version', 'topic_id', 'version_no', unique=True),
        {'comment': 'US-24'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    topic_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    submitted_by: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    submitted_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    is_current: Mapped[int] = mapped_column(TINYINT(1), nullable=False, server_default=text("'1'"))
    hardcopy_received_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='Ô đánh dấu bản cứng (câu G7)')
    current_key: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True), Computed('(if((`is_current` = 1),`topic_id`,NULL))', persisted=True))

    users: Mapped['Users'] = relationship('Users', back_populates='final_submissions')
    topic: Mapped['Topics'] = relationship('Topics', back_populates='final_submissions')
    final_submission_files: Mapped[list['FinalSubmissionFiles']] = relationship('FinalSubmissionFiles', back_populates='final_submission')
    similarity_checks: Mapped[list['SimilarityChecks']] = relationship('SimilarityChecks', back_populates='final_submission')


class GradeAppeals(Base):
    __tablename__ = 'grade_appeals'
    __table_args__ = (
        CheckConstraint("(`status` in (_utf8mb4'SUBMITTED',_utf8mb4'IN_REVIEW',_utf8mb4'UPHELD',_utf8mb4'CHANGED',_utf8mb4'REJECTED'))", name='ck_ga_status'),
        ForeignKeyConstraint(['appeal_committee_id'], ['committees.id'], name='fk_ga_com'),
        ForeignKeyConstraint(['student_user_id'], ['users.id'], name='fk_ga_user'),
        ForeignKeyConstraint(['topic_id'], ['topics.id'], name='fk_ga_topic'),
        Index('fk_ga_com', 'appeal_committee_id'),
        Index('fk_ga_topic', 'topic_id'),
        Index('fk_ga_user', 'student_user_id'),
        {'comment': 'US-38'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    topic_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    attempt_no: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("'1'"))
    student_user_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    reason: Mapped[str] = mapped_column(String(2000), nullable=False)
    status: Mapped[str] = mapped_column(String(12), nullable=False, server_default=text("'SUBMITTED'"))
    submitted_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    appeal_committee_id: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True))
    old_score: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(6, 2))
    new_score: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(6, 2))
    decision_note: Mapped[Optional[str]] = mapped_column(String(1000))
    decided_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    appeal_committee: Mapped[Optional['Committees']] = relationship('Committees', back_populates='grade_appeals')
    student_user: Mapped['Users'] = relationship('Users', back_populates='grade_appeals')
    topic: Mapped['Topics'] = relationship('Topics', back_populates='grade_appeals')


class GradeResults(Base):
    __tablename__ = 'grade_results'
    __table_args__ = (
        CheckConstraint("(`status` in (_utf8mb4'DRAFT',_utf8mb4'LOCKED',_utf8mb4'PUBLISHED',_utf8mb4'REOPENED'))", name='ck_gr_status'),
        ForeignKeyConstraint(['formula_id'], ['grading_formulas.id'], name='fk_gr_formula'),
        ForeignKeyConstraint(['locked_by'], ['users.id'], name='fk_gr_user'),
        ForeignKeyConstraint(['topic_id'], ['topics.id'], name='fk_gr_topic'),
        Index('fk_gr_formula', 'formula_id'),
        Index('fk_gr_user', 'locked_by'),
        Index('uq_gr', 'topic_id', 'attempt_no', unique=True),
        {'comment': 'US-35, US-36'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    topic_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    attempt_no: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("'1'"))
    formula_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, server_default=text("'DRAFT'"))
    component_scores: Mapped[Optional[object]] = mapped_column(JSON)
    final_score: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(6, 2))
    grade_label: Mapped[Optional[str]] = mapped_column(String(10))
    passed: Mapped[Optional[int]] = mapped_column(TINYINT(1))
    locked_by: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True))
    locked_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    published_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    formula: Mapped['GradingFormulas'] = relationship('GradingFormulas', back_populates='grade_results')
    users: Mapped[Optional['Users']] = relationship('Users', back_populates='grade_results')
    topic: Mapped['Topics'] = relationship('Topics', back_populates='grade_results')
    grade_result_history: Mapped[list['GradeResultHistory']] = relationship('GradeResultHistory', back_populates='grade_result')


class MilestoneExtensions(Base):
    __tablename__ = 'milestone_extensions'
    __table_args__ = (
        CheckConstraint("(`status` in (_utf8mb4'PENDING',_utf8mb4'APPROVED',_utf8mb4'REJECTED'))", name='ck_mext_status'),
        ForeignKeyConstraint(['decided_by'], ['users.id'], name='fk_mext_user'),
        ForeignKeyConstraint(['milestone_id'], ['period_milestones.id'], name='fk_mext_ms'),
        ForeignKeyConstraint(['topic_id'], ['topics.id'], name='fk_mext_topic'),
        Index('fk_mext_ms', 'milestone_id'),
        Index('fk_mext_user', 'decided_by'),
        Index('uq_mext', 'topic_id', 'milestone_id', 'new_due_at', unique=True),
        {'comment': 'US-23'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    topic_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    milestone_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    new_due_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, server_default=text("'PENDING'"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    decided_by: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True))

    users: Mapped[Optional['Users']] = relationship('Users', back_populates='milestone_extensions')
    milestone: Mapped['PeriodMilestones'] = relationship('PeriodMilestones', back_populates='milestone_extensions')
    topic: Mapped['Topics'] = relationship('Topics', back_populates='milestone_extensions')


class MilestoneSubmissions(Base):
    __tablename__ = 'milestone_submissions'
    __table_args__ = (
        ForeignKeyConstraint(['milestone_id'], ['period_milestones.id'], name='fk_msub_ms'),
        ForeignKeyConstraint(['submitted_by'], ['users.id'], name='fk_msub_user'),
        ForeignKeyConstraint(['topic_id'], ['topics.id'], name='fk_msub_topic'),
        Index('fk_msub_ms', 'milestone_id'),
        Index('fk_msub_user', 'submitted_by'),
        Index('uq_msub', 'topic_id', 'milestone_id', 'version_no', unique=True),
        {'comment': 'US-18, giữ mọi lần nộp'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    topic_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    milestone_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("'1'"))
    submitted_by: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    is_late: Mapped[int] = mapped_column(TINYINT(1), nullable=False, server_default=text("'0'"))
    submitted_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    note: Mapped[Optional[str]] = mapped_column(Text)

    file: Mapped[list['Files']] = relationship('Files', secondary='submission_files', back_populates='submission')
    milestone: Mapped['PeriodMilestones'] = relationship('PeriodMilestones', back_populates='milestone_submissions')
    users: Mapped['Users'] = relationship('Users', back_populates='milestone_submissions')
    topic: Mapped['Topics'] = relationship('Topics', back_populates='milestone_submissions')
    milestone_reviews: Mapped[list['MilestoneReviews']] = relationship('MilestoneReviews', back_populates='submission')


class RevisionSubmissions(Base):
    __tablename__ = 'revision_submissions'
    __table_args__ = (
        ForeignKeyConstraint(['confirmed_by'], ['users.id'], name='fk_rs_user'),
        ForeignKeyConstraint(['file_id'], ['files.id'], name='fk_rs_file'),
        ForeignKeyConstraint(['topic_id'], ['topics.id'], name='fk_rs_topic'),
        Index('fk_rs_file', 'file_id'),
        Index('fk_rs_topic', 'topic_id'),
        Index('fk_rs_user', 'confirmed_by'),
        {'comment': 'US-37'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    topic_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    attempt_no: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("'1'"))
    file_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    submitted_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    confirmed_by: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True))
    confirmed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    users: Mapped[Optional['Users']] = relationship('Users', back_populates='revision_submissions')
    file: Mapped['Files'] = relationship('Files', back_populates='revision_submissions')
    topic: Mapped['Topics'] = relationship('Topics', back_populates='revision_submissions')


class ScoreEntries(Base):
    __tablename__ = 'score_entries'
    __table_args__ = (
        CheckConstraint('(`score` >= 0)', name='ck_se_score'),
        ForeignKeyConstraint(['criterion_id'], ['grading_criteria.id'], name='fk_se_crit'),
        ForeignKeyConstraint(['scorer_user_id'], ['users.id'], name='fk_se_user'),
        ForeignKeyConstraint(['topic_id'], ['topics.id'], name='fk_se_topic'),
        Index('fk_se_crit', 'criterion_id'),
        Index('fk_se_user', 'scorer_user_id'),
        Index('uq_score', 'topic_id', 'attempt_no', 'criterion_id', 'scorer_user_id', unique=True),
        {'comment': 'US-33'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    topic_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    attempt_no: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("'1'"))
    criterion_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    scorer_user_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    score: Mapped[decimal.Decimal] = mapped_column(DECIMAL(6, 2), nullable=False)
    submitted_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    comment: Mapped[Optional[str]] = mapped_column(String(1000))
    locked_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    criterion: Mapped['GradingCriteria'] = relationship('GradingCriteria', back_populates='score_entries')
    scorer_user: Mapped['Users'] = relationship('Users', back_populates='score_entries')
    topic: Mapped['Topics'] = relationship('Topics', back_populates='score_entries')


class SupervisionMeetings(Base):
    __tablename__ = 'supervision_meetings'
    __table_args__ = (
        ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_sm_user'),
        ForeignKeyConstraint(['topic_id'], ['topics.id'], name='fk_sm_topic'),
        Index('fk_sm_user', 'created_by'),
        Index('ix_sm_topic', 'topic_id', 'held_at'),
        {'comment': 'US-20'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    topic_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    held_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    created_by: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    action_items: Mapped[Optional[str]] = mapped_column(Text)
    student_confirmed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    users: Mapped['Users'] = relationship('Users', back_populates='supervision_meetings')
    topic: Mapped['Topics'] = relationship('Topics', back_populates='supervision_meetings')


class TopicMembers(Base):
    __tablename__ = 'topic_members'
    __table_args__ = (
        CheckConstraint("(`status` in (_utf8mb4'PENDING',_utf8mb4'ACTIVE',_utf8mb4'REJECTED',_utf8mb4'WITHDRAWN',_utf8mb4'REPLACED'))", name='ck_tm_status'),
        ForeignKeyConstraint(['decided_by'], ['users.id'], name='fk_tm_decider'),
        ForeignKeyConstraint(['role_code'], ['roles.code'], name='fk_tm_role'),
        ForeignKeyConstraint(['topic_id', 'period_id'], ['topics.id', 'topics.period_id'], name='fk_tm_topic'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_tm_user'),
        Index('fk_tm_decider', 'decided_by'),
        Index('fk_tm_role', 'role_code'),
        Index('fk_tm_topic', 'topic_id', 'period_id'),
        Index('ix_tm_user', 'user_id', 'role_code', 'status'),
        Index('uq_tm_one_active_role', 'topic_id', 'user_id', 'role_code', 'member_active_key', unique=True),
        Index('uq_tm_one_main_advisor', 'topic_id', 'advisor_active_key', unique=True),
        Index('uq_tm_student_one_per_period', 'period_id', 'student_active_key', unique=True),
        {'comment': 'Nhiều-nhiều đề tài-người có vai trò (câu E3, E7, B6)'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    topic_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    period_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False, comment='Lặp lại từ đề tài; khóa ngoại kép bảo đảm khớp')
    user_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    role_code: Mapped[str] = mapped_column(String(30), nullable=False, comment='STUDENT, ADVISOR, CO_ADVISOR, EXTERNAL_ADVISOR, REVIEWER')
    status: Mapped[str] = mapped_column(String(12), nullable=False, server_default=text("'PENDING'"))
    registered_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    preference_rank: Mapped[Optional[int]] = mapped_column(TINYINT, comment='Thứ tự nguyện vọng (câu D1)')
    decision_reason: Mapped[Optional[str]] = mapped_column(String(500))
    decided_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    decided_by: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True))
    ended_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    member_active_key: Mapped[Optional[int]] = mapped_column(TINYINT, Computed("(if((`status` in (_utf8mb4'PENDING',_utf8mb4'ACTIVE')),1,NULL))", persisted=True))
    student_active_key: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True), Computed("(if(((`role_code` = _utf8mb4'STUDENT') and (`status` in (_utf8mb4'PENDING',_utf8mb4'ACTIVE'))),`user_id`,NULL))", persisted=True))
    advisor_active_key: Mapped[Optional[int]] = mapped_column(TINYINT, Computed("(if(((`role_code` = _utf8mb4'ADVISOR') and (`status` = _utf8mb4'ACTIVE')),1,NULL))", persisted=True))

    users: Mapped[Optional['Users']] = relationship('Users', foreign_keys=[decided_by], back_populates='topic_members_decided_by')
    roles: Mapped['Roles'] = relationship('Roles', back_populates='topic_members')
    topics: Mapped['Topics'] = relationship('Topics', back_populates='topic_members')
    user: Mapped['Users'] = relationship('Users', foreign_keys=[user_id], back_populates='topic_members_user')
    change_requests: Mapped[list['ChangeRequests']] = relationship('ChangeRequests', back_populates='topic_member')
    review_reports: Mapped[list['ReviewReports']] = relationship('ReviewReports', back_populates='topic_member')


class TopicStateHistory(Base):
    __tablename__ = 'topic_state_history'
    __table_args__ = (
        ForeignKeyConstraint(['actor_user_id'], ['users.id'], name='fk_tsh_actor'),
        ForeignKeyConstraint(['from_state'], ['topic_states.code'], name='fk_tsh_from'),
        ForeignKeyConstraint(['to_state'], ['topic_states.code'], name='fk_tsh_to'),
        ForeignKeyConstraint(['topic_id'], ['topics.id'], name='fk_tsh_topic'),
        Index('fk_tsh_actor', 'actor_user_id'),
        Index('fk_tsh_from', 'from_state'),
        Index('fk_tsh_to', 'to_state'),
        Index('ix_tsh_topic', 'topic_id', 'created_at'),
        {'comment': 'Mọi chuyển trạng thái ghi người làm và lý do (US-14)'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    topic_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    to_state: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    from_state: Mapped[Optional[str]] = mapped_column(String(30))
    actor_user_id: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True))
    reason: Mapped[Optional[str]] = mapped_column(String(500))

    actor_user: Mapped[Optional['Users']] = relationship('Users', back_populates='topic_state_history')
    topic_states: Mapped[Optional['TopicStates']] = relationship('TopicStates', foreign_keys=[from_state], back_populates='topic_state_history_from_state')
    topic_states_: Mapped['TopicStates'] = relationship('TopicStates', foreign_keys=[to_state], back_populates='topic_state_history_to_state')
    topic: Mapped['Topics'] = relationship('Topics', back_populates='topic_state_history')


class ChangeRequests(Base):
    __tablename__ = 'change_requests'
    __table_args__ = (
        CheckConstraint("(`request_type` in (_utf8mb4'CHANGE_TOPIC',_utf8mb4'CHANGE_ADVISOR'))", name='ck_cr_type'),
        CheckConstraint("(`status` in (_utf8mb4'PENDING',_utf8mb4'APPROVED',_utf8mb4'REJECTED',_utf8mb4'CANCELLED'))", name='ck_cr_status'),
        ForeignKeyConstraint(['to_advisor_id'], ['users.id'], name='fk_cr_adv'),
        ForeignKeyConstraint(['to_topic_id'], ['topics.id'], name='fk_cr_topic'),
        ForeignKeyConstraint(['topic_member_id'], ['topic_members.id'], name='fk_cr_member'),
        Index('fk_cr_adv', 'to_advisor_id'),
        Index('fk_cr_member', 'topic_member_id'),
        Index('fk_cr_topic', 'to_topic_id'),
        {'comment': 'US-16'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    topic_member_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False, comment='Đăng ký của sinh viên xin đổi')
    request_type: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[str] = mapped_column(String(12), nullable=False, server_default=text("'PENDING'"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    to_topic_id: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True))
    to_advisor_id: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True))
    resolved_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    to_advisor: Mapped[Optional['Users']] = relationship('Users', back_populates='change_requests')
    to_topic: Mapped[Optional['Topics']] = relationship('Topics', back_populates='change_requests')
    topic_member: Mapped['TopicMembers'] = relationship('TopicMembers', back_populates='change_requests')
    change_request_approvals: Mapped[list['ChangeRequestApprovals']] = relationship('ChangeRequestApprovals', back_populates='request')


class DefenseMinutes(Base):
    __tablename__ = 'defense_minutes'
    __table_args__ = (
        ForeignKeyConstraint(['secretary_id'], ['users.id'], name='fk_dm_sec'),
        ForeignKeyConstraint(['session_id'], ['defense_sessions.id'], name='fk_dm_session'),
        Index('fk_dm_sec', 'secretary_id'),
        Index('uq_dm_session', 'session_id', unique=True),
        {'comment': 'US-34'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    secretary_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    content: Mapped[Optional[str]] = mapped_column(Text)
    revision_requests: Mapped[Optional[str]] = mapped_column(Text)
    finalized_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    secretary: Mapped['Users'] = relationship('Users', back_populates='defense_minutes')
    session: Mapped['DefenseSessions'] = relationship('DefenseSessions', back_populates='defense_minutes')


class DefenseSessionParticipants(Base):
    __tablename__ = 'defense_session_participants'
    __table_args__ = (
        ForeignKeyConstraint(['role_code'], ['roles.code'], name='fk_dsp_role'),
        ForeignKeyConstraint(['session_id'], ['defense_sessions.id'], ondelete='CASCADE', name='fk_dsp_session'),
        ForeignKeyConstraint(['slot_id'], ['defense_slots.id'], name='fk_dsp_slot'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_dsp_user'),
        Index('fk_dsp_role', 'role_code'),
        Index('fk_dsp_slot', 'slot_id'),
        Index('uq_dsp_person_slot', 'user_id', 'slot_id', 'active_key', unique=True),
        Index('uq_dsp_session_user', 'session_id', 'user_id', unique=True),
        {'comment': 'US-30'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    slot_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    user_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    role_code: Mapped[str] = mapped_column(String(30), nullable=False)
    active_key: Mapped[Optional[int]] = mapped_column(TINYINT, comment='Ứng dụng đặt 1 khi buổi còn hiệu lực, NULL khi hoãn/hủy')

    roles: Mapped['Roles'] = relationship('Roles', back_populates='defense_session_participants')
    session: Mapped['DefenseSessions'] = relationship('DefenseSessions', back_populates='defense_session_participants')
    slot: Mapped['DefenseSlots'] = relationship('DefenseSlots', back_populates='defense_session_participants')
    user: Mapped['Users'] = relationship('Users', back_populates='defense_session_participants')


class FinalSubmissionFiles(Base):
    __tablename__ = 'final_submission_files'
    __table_args__ = (
        CheckConstraint("(`kind` in (_utf8mb4'REPORT',_utf8mb4'SLIDES',_utf8mb4'SOURCE',_utf8mb4'OTHER'))", name='ck_fsf_kind'),
        ForeignKeyConstraint(['file_id'], ['files.id'], name='fk_fsf_file'),
        ForeignKeyConstraint(['final_submission_id'], ['final_submissions.id'], ondelete='CASCADE', name='fk_fsf_fs'),
        Index('fk_fsf_file', 'file_id')
    )

    final_submission_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    file_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    kind: Mapped[str] = mapped_column(String(10), nullable=False, server_default=text("'OTHER'"))

    file: Mapped['Files'] = relationship('Files', back_populates='final_submission_files')
    final_submission: Mapped['FinalSubmissions'] = relationship('FinalSubmissions', back_populates='final_submission_files')


class GradeResultHistory(Base):
    __tablename__ = 'grade_result_history'
    __table_args__ = (
        ForeignKeyConstraint(['grade_result_id'], ['grade_results.id'], name='fk_grh_gr'),
        Index('ix_grh', 'grade_result_id', 'changed_at'),
        {'comment': 'US-36'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    grade_result_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    snapshot: Mapped[object] = mapped_column(JSON, nullable=False)
    changed_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    change_reason: Mapped[Optional[str]] = mapped_column(String(500))
    changed_by: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True))

    grade_result: Mapped['GradeResults'] = relationship('GradeResults', back_populates='grade_result_history')


class MilestoneReviews(Base):
    __tablename__ = 'milestone_reviews'
    __table_args__ = (
        CheckConstraint("(`verdict` in (_utf8mb4'PASS',_utf8mb4'NEEDS_REVISION'))", name='ck_mrev_verdict'),
        ForeignKeyConstraint(['reviewer_id'], ['users.id'], name='fk_mrev_user'),
        ForeignKeyConstraint(['submission_id'], ['milestone_submissions.id'], name='fk_mrev_sub'),
        Index('fk_mrev_user', 'reviewer_id'),
        Index('ix_mrev_sub', 'submission_id'),
        {'comment': 'US-19'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    submission_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    reviewer_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    verdict: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    comment: Mapped[Optional[str]] = mapped_column(Text)

    reviewer: Mapped['Users'] = relationship('Users', back_populates='milestone_reviews')
    submission: Mapped['MilestoneSubmissions'] = relationship('MilestoneSubmissions', back_populates='milestone_reviews')


class ReviewReports(Base):
    __tablename__ = 'review_reports'
    __table_args__ = (
        ForeignKeyConstraint(['topic_member_id'], ['topic_members.id'], name='fk_rr_member'),
        Index('uq_rr_member', 'topic_member_id', unique=True),
        {'comment': 'US-28'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    topic_member_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False, comment='Dòng topic_members có role REVIEWER')
    comment: Mapped[Optional[str]] = mapped_column(Text)
    submitted_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    locked_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    topic_member: Mapped['TopicMembers'] = relationship('TopicMembers', back_populates='review_reports')


class SimilarityChecks(Base):
    __tablename__ = 'similarity_checks'
    __table_args__ = (
        ForeignKeyConstraint(['checked_by'], ['users.id'], name='fk_sim_user'),
        ForeignKeyConstraint(['final_submission_id'], ['final_submissions.id'], name='fk_sim_fs'),
        ForeignKeyConstraint(['report_file_id'], ['files.id'], name='fk_sim_file'),
        Index('fk_sim_file', 'report_file_id'),
        Index('fk_sim_fs', 'final_submission_id'),
        Index('fk_sim_user', 'checked_by'),
        {'comment': 'US-26'}
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    final_submission_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    checked_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    score: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(5, 2))
    matches: Mapped[Optional[object]] = mapped_column(JSON)
    report_file_id: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True))
    checked_by: Mapped[Optional[int]] = mapped_column(BIGINT(unsigned=True))

    users: Mapped[Optional['Users']] = relationship('Users', back_populates='similarity_checks')
    final_submission: Mapped['FinalSubmissions'] = relationship('FinalSubmissions', back_populates='similarity_checks')
    report_file: Mapped[Optional['Files']] = relationship('Files', back_populates='similarity_checks')


t_submission_files = Table(
    'submission_files', Base.metadata,
    Column('submission_id', BIGINT(unsigned=True), primary_key=True),
    Column('file_id', BIGINT(unsigned=True), primary_key=True),
    ForeignKeyConstraint(['file_id'], ['files.id'], name='fk_sf_file'),
    ForeignKeyConstraint(['submission_id'], ['milestone_submissions.id'], ondelete='CASCADE', name='fk_sf_sub'),
    Index('fk_sf_file', 'file_id')
)


class ChangeRequestApprovals(Base):
    __tablename__ = 'change_request_approvals'
    __table_args__ = (
        CheckConstraint("((`decision` is null) or (`decision` in (_utf8mb4'APPROVE',_utf8mb4'REJECT')))", name='ck_cra_decision'),
        ForeignKeyConstraint(['approver_id'], ['users.id'], name='fk_cra_user'),
        ForeignKeyConstraint(['approver_role'], ['roles.code'], name='fk_cra_role'),
        ForeignKeyConstraint(['request_id'], ['change_requests.id'], ondelete='CASCADE', name='fk_cra_req'),
        Index('fk_cra_role', 'approver_role'),
        Index('fk_cra_user', 'approver_id'),
        Index('uq_cra', 'request_id', 'approver_id', 'approver_role', unique=True)
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    request_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    approver_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    approver_role: Mapped[str] = mapped_column(String(30), nullable=False, comment='GVHD cũ, GVHD mới, trưởng bộ môn (câu E6)')
    decision: Mapped[Optional[str]] = mapped_column(String(10))
    comment: Mapped[Optional[str]] = mapped_column(String(500))
    decided_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    approver: Mapped['Users'] = relationship('Users', back_populates='change_request_approvals')
    roles: Mapped['Roles'] = relationship('Roles', back_populates='change_request_approvals')
    request: Mapped['ChangeRequests'] = relationship('ChangeRequests', back_populates='change_request_approvals')
