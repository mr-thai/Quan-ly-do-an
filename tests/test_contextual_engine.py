import pytest
from sqlalchemy import select
from app.core.database import transaction_scope
from app.core.security import hash_password
from app.models import (
    Users,
    Topics,
    UserRoles,
    OrgUnits,
    Periods,
    ThesisTypes,
    TopicMembers,
)
from app.services.contextual_engine import ContextualEngine, TopicUserContext


@pytest.fixture
def engine():
    return ContextualEngine()


# =============================================================================
# 1. Unit Tests on ContextualEngine Domain Logic (with TopicUserContext)
# =============================================================================

def test_engine_topic_not_found(engine):
    """Non-existent topic denies all permissions."""
    ctx = TopicUserContext(user_id=1, topic_id=9999, topic_exists=False)
    assert engine.can_view_topic(ctx) is False
    assert engine.can_view_scores(ctx) is False
    assert engine.can_grade_as_advisor(ctx) is False
    assert engine.can_grade_as_reviewer(ctx) is False
    assert engine.can_grade_as_defense_committee(ctx) is False
    assert engine.can_confirm_eligibility(ctx) is False
    assert engine.can_manage_topic(ctx) is False


def test_engine_admin_and_office_permissions(engine):
    """Admin and Office have broad viewing, management, and score oversight."""
    admin_ctx = TopicUserContext(
        user_id=1, topic_id=10, system_roles=["ADMIN"], topic_exists=True
    )
    office_ctx = TopicUserContext(
        user_id=2, topic_id=10, system_roles=["OFFICE"], topic_exists=True
    )

    for ctx in (admin_ctx, office_ctx):
        assert engine.can_view_topic(ctx) is True
        assert engine.can_view_scores(ctx) is True
        assert engine.can_manage_topic(ctx) is True


def test_engine_head_of_managing_dept(engine):
    """Head of managing department can view, manage, and inspect scores."""
    dept_head_ctx = TopicUserContext(
        user_id=3,
        topic_id=10,
        system_roles=["HEAD_OF_DEPT"],
        is_head_of_managing_dept=True,
        topic_exists=True,
    )
    non_managing_dept_head_ctx = TopicUserContext(
        user_id=4,
        topic_id=10,
        system_roles=["HEAD_OF_DEPT"],
        is_head_of_managing_dept=False,
        topic_exists=True,
    )

    assert engine.can_view_topic(dept_head_ctx) is True
    assert engine.can_view_scores(dept_head_ctx) is True
    assert engine.can_manage_topic(dept_head_ctx) is True

    # Other dept head has no management power over this topic
    assert engine.can_manage_topic(non_managing_dept_head_ctx) is False


def test_engine_advisor_permissions(engine):
    """Advisor can view topic, view scores, grade advisor sheet, and confirm eligibility."""
    advisor_ctx = TopicUserContext(
        user_id=5,
        topic_id=10,
        topic_roles=["ADVISOR"],
        topic_exists=True,
    )

    assert engine.can_view_topic(advisor_ctx) is True
    assert engine.can_view_scores(advisor_ctx) is True
    assert engine.can_grade_as_advisor(advisor_ctx) is True
    assert engine.can_confirm_eligibility(advisor_ctx) is True
    assert engine.can_grade_as_reviewer(advisor_ctx) is False


def test_engine_reviewer_permissions(engine):
    """Reviewer can view topic, view scores, and grade reviewer sheet."""
    reviewer_ctx = TopicUserContext(
        user_id=6,
        topic_id=10,
        topic_roles=["REVIEWER"],
        topic_exists=True,
    )

    assert engine.can_view_topic(reviewer_ctx) is True
    assert engine.can_view_scores(reviewer_ctx) is True
    assert engine.can_grade_as_reviewer(reviewer_ctx) is True
    assert engine.can_grade_as_advisor(reviewer_ctx) is False
    assert engine.can_confirm_eligibility(reviewer_ctx) is False


def test_engine_conflict_of_interest_guard(engine):
    """CRITICAL RULE: Advisor MUST NOT score defense if they also serve on committee."""
    # Case A: Normal committee member who is NOT an advisor -> CAN grade defense
    committee_member_ctx = TopicUserContext(
        user_id=7,
        topic_id=10,
        committee_roles=["MEMBER"],
        topic_exists=True,
    )
    assert engine.can_grade_as_defense_committee(committee_member_ctx) is True

    # Case B: Advisor who is ALSO on the defense committee -> FORBIDDEN from defense scoring
    conflicted_ctx = TopicUserContext(
        user_id=8,
        topic_id=10,
        topic_roles=["ADVISOR"],
        committee_roles=["MEMBER"],
        topic_exists=True,
    )
    assert engine.can_grade_as_advisor(conflicted_ctx) is True
    assert engine.can_grade_as_defense_committee(conflicted_ctx) is False


def test_engine_student_score_visibility_gate(engine):
    """Student cannot see score entries before topic is GRADED/ARCHIVED."""
    in_progress_ctx = TopicUserContext(
        user_id=9,
        topic_id=10,
        topic_roles=["STUDENT"],
        topic_state="IN_PROGRESS",
        topic_exists=True,
    )
    graded_ctx = TopicUserContext(
        user_id=9,
        topic_id=10,
        topic_roles=["STUDENT"],
        topic_state="GRADED",
        topic_exists=True,
    )

    assert engine.can_view_topic(in_progress_ctx) is True
    assert engine.can_view_scores(in_progress_ctx) is False  # Blocked during progress!
    assert engine.can_view_scores(graded_ctx) is True       # Visible once finalized!


def test_engine_unrelated_user(engine):
    """Unrelated lecturer/user has no access to private topic data or scores."""
    unrelated_ctx = TopicUserContext(
        user_id=10,
        topic_id=10,
        system_roles=["ADVISOR_ROLE"],
        topic_roles=[],
        committee_roles=[],
        topic_exists=True,
    )

    assert engine.can_view_topic(unrelated_ctx) is False
    assert engine.can_view_scores(unrelated_ctx) is False
    assert engine.can_manage_topic(unrelated_ctx) is False


# =============================================================================
# 2. Integration Test: resolve_context against MySQL Database
# =============================================================================

@pytest.fixture
def db_context_fixture():
    """Setup a sample topic, org units, and user associations in DB."""
    email_adv = "gv_adv_test_ce@example.com"
    email_dept = "gv_dept_test_ce@example.com"
    org_code = "SE_DEPT_TEST_CE"
    topic_code = "TOPIC_TEST_CE_01"

    with transaction_scope() as session:
        # 1. Org Unit
        existing_org = session.scalar(select(OrgUnits).where(OrgUnits.code == org_code))
        if existing_org:
            session.delete(existing_org)
            session.flush()

        org = OrgUnits(code=org_code, name="Bộ môn CNPM Test", unit_type="DEPARTMENT")
        session.add(org)
        session.flush()

        # 2. Users
        u_adv = Users(
            email=email_adv,
            user_code="GV_ADV_CE",
            password_hash=hash_password("Pass123!"),
            full_name="GVHD Test",
        )
        u_dept = Users(
            email=email_dept,
            user_code="GV_DEPT_CE",
            password_hash=hash_password("Pass123!"),
            full_name="Trưởng BM Test",
        )
        session.add_all([u_adv, u_dept])
        session.flush()

        # Assign HEAD_OF_DEPT role to u_dept
        ur_dept = UserRoles(user_id=u_dept.id, role_code="HEAD_OF_DEPT", org_unit_id=org.id)
        session.add(ur_dept)
        session.flush()

        # 3. Period
        thesis_type = session.scalar(select(ThesisTypes))
        period = Periods(
            thesis_type_id=thesis_type.id,
            name="Đợt 1 2026 Test CE",
            status="OPEN",
            org_unit_id=org.id,
        )
        session.add(period)
        session.flush()

        # 4. Topic
        topic = Topics(
            period_id=period.id,
            code=topic_code,
            title="Đề tài Thử nghiệm Phân quyền Ngữ cảnh",
            state_code="IN_PROGRESS",
            created_by=u_adv.id,
            org_unit_id=org.id,
        )
        session.add(topic)
        session.flush()

        # 5. Topic Member (u_adv is ADVISOR)
        tm = TopicMembers(
            topic_id=topic.id,
            period_id=period.id,
            user_id=u_adv.id,
            role_code="ADVISOR",
            status="ACTIVE",
        )
        session.add(tm)
        session.flush()

        data = {
            "org_id": org.id,
            "u_adv_id": u_adv.id,
            "u_dept_id": u_dept.id,
            "topic_id": topic.id,
            "period_id": period.id,
        }

    yield data

    # Cleanup
    with transaction_scope() as session:
        t = session.get(Topics, data["topic_id"])
        if t:
            session.query(TopicMembers).filter(TopicMembers.topic_id == data["topic_id"]).delete()
            session.delete(t)
        p = session.get(Periods, data["period_id"])
        if p:
            session.delete(p)
        session.query(UserRoles).filter(UserRoles.user_id.in_([data["u_adv_id"], data["u_dept_id"]])).delete()
        for uid in (data["u_adv_id"], data["u_dept_id"]):
            u = session.get(Users, uid)
            if u:
                session.delete(u)
        o = session.get(OrgUnits, data["org_id"])
        if o:
            session.delete(o)


def test_resolve_context_integration(engine, db_context_fixture):
    """Test full context resolution and permission checks against database records."""
    data = db_context_fixture
    topic_id = data["topic_id"]
    adv_id = data["u_adv_id"]
    dept_id = data["u_dept_id"]

    # 1. Resolve for Advisor
    adv_ctx = engine.resolve_context(user_id=adv_id, topic_id=topic_id)
    assert adv_ctx.topic_exists is True
    assert "ADVISOR" in adv_ctx.topic_roles
    assert adv_ctx.is_head_of_managing_dept is False
    assert engine.can_view_topic(adv_ctx) is True
    assert engine.can_grade_as_advisor(adv_ctx) is True
    assert engine.can_confirm_eligibility(adv_ctx) is True

    # 2. Resolve for Head of Dept
    dept_ctx = engine.resolve_context(user_id=dept_id, topic_id=topic_id)
    assert dept_ctx.topic_exists is True
    assert "HEAD_OF_DEPT" in dept_ctx.system_roles
    assert dept_ctx.is_head_of_managing_dept is True
    assert engine.can_view_topic(dept_ctx) is True
    assert engine.can_manage_topic(dept_ctx) is True
