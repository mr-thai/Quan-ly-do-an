import datetime
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
    Rooms,
    DefenseSlots,
    Committees,
    CommitteeMembers,
    DefenseSessions,
)
from app.services.contextual_engine import ContextualEngine


@pytest.fixture
def engine():
    return ContextualEngine()


@pytest.fixture
def academic_ecosystem():
    """Setup a multi-department, multi-role academic ecosystem in MySQL.
    
    Ecosystem Structure:
    - Dept A (SE): Công nghệ phần mềm
    - Dept B (NW): Mạng & Hệ thống
    - Lecturer An: Multi-role lecturer
      - Topic 1 (Dept A): ADVISOR
      - Topic 2 (Dept A): REVIEWER
      - Topic 3 (Dept B): COMMITTEE MEMBER (Defense Session)
      - Topic 4 (Dept B): Unrelated
    - Head A: Head of Dept A
    - Head B: Head of Dept B
    - Student X: Student on Topic 1
    - Student Y: Student on Topic 2
    """
    prefix = "SEC_BND_"
    dept_a_code = f"{prefix}DEPT_A"
    dept_b_code = f"{prefix}DEPT_B"
    room_name = f"{prefix}ROOM_501"

    with transaction_scope() as session:
        # Cleanup any existing data with prefix
        existing_orgs = list(session.scalars(select(OrgUnits).where(OrgUnits.code.in_([dept_a_code, dept_b_code]))).all())
        for o in existing_orgs:
            session.delete(o)
        session.flush()

        # 1. Departments
        dept_a = OrgUnits(code=dept_a_code, name="Bộ môn CNPM (Bảo mật)", unit_type="DEPARTMENT")
        dept_b = OrgUnits(code=dept_b_code, name="Bộ môn Mạng (Bảo mật)", unit_type="DEPARTMENT")
        session.add_all([dept_a, dept_b])
        session.flush()

        # 2. Users
        def _create_user(code, email, name):
            u = Users(
                user_code=f"{prefix}{code}",
                email=f"{prefix.lower()}{email}@example.com",
                password_hash=hash_password("Pass123!"),
                full_name=name,
            )
            session.add(u)
            return u

        gv_an = _create_user("GV_AN", "an", "TS. Nguyễn Văn An")
        head_a = _create_user("HEAD_A", "head_a", "PGS. Trưởng BM Phần Mềm")
        head_b = _create_user("HEAD_B", "head_b", "PGS. Trưởng BM Mạng")
        sv_x = _create_user("SV_X", "sv_x", "Sinh viên X")
        sv_y = _create_user("SV_Y", "sv_y", "Sinh viên Y")
        session.flush()

        # System roles
        session.add_all([
            UserRoles(user_id=gv_an.id, role_code="ADVISOR_ROLE"),
            UserRoles(user_id=head_a.id, role_code="HEAD_OF_DEPT", org_unit_id=dept_a.id),
            UserRoles(user_id=head_b.id, role_code="HEAD_OF_DEPT", org_unit_id=dept_b.id),
            UserRoles(user_id=sv_x.id, role_code="STUDENT_ROLE"),
            UserRoles(user_id=sv_y.id, role_code="STUDENT_ROLE"),
        ])
        session.flush()

        # 3. Period
        thesis_type = session.scalar(select(ThesisTypes))
        period = Periods(
            thesis_type_id=thesis_type.id,
            name=f"{prefix}Period 2026",
            status="OPEN",
            org_unit_id=dept_a.id,
        )
        session.add(period)
        session.flush()

        # 4. Topics
        def _create_topic(code, title, org_id, state):
            t = Topics(
                period_id=period.id,
                code=f"{prefix}{code}",
                title=title,
                state_code=state,
                created_by=gv_an.id,
                org_unit_id=org_id,
            )
            session.add(t)
            return t

        t1 = _create_topic("T1", "Đề tài 1: An hướng dẫn", dept_a.id, "IN_PROGRESS")
        t2 = _create_topic("T2", "Đề tài 2: An phản biện", dept_a.id, "ELIGIBLE")
        t3 = _create_topic("T3", "Đề tài 3: An chấm hội đồng", dept_b.id, "ELIGIBLE")
        t4 = _create_topic("T4", "Đề tài 4: An không liên quan", dept_b.id, "IN_PROGRESS")
        session.flush()

        # 5. Topic Members
        session.add_all([
            # Topic 1: GV An is Advisor, SV X is Student
            TopicMembers(topic_id=t1.id, period_id=period.id, user_id=gv_an.id, role_code="ADVISOR", status="ACTIVE"),
            TopicMembers(topic_id=t1.id, period_id=period.id, user_id=sv_x.id, role_code="STUDENT", status="ACTIVE"),

            # Topic 2: GV An is Reviewer, SV Y is Student
            TopicMembers(topic_id=t2.id, period_id=period.id, user_id=gv_an.id, role_code="REVIEWER", status="ACTIVE"),
            TopicMembers(topic_id=t2.id, period_id=period.id, user_id=sv_y.id, role_code="STUDENT", status="ACTIVE"),
        ])
        session.flush()

        # 6. Committee & Defense Session for Topic 3
        existing_room = session.scalar(select(Rooms).where(Rooms.name == room_name))
        if not existing_room:
            room = Rooms(name=room_name, is_online=0, location="Tầng 5 Nhà C")
            session.add(room)
            session.flush()
        else:
            room = existing_room

        slot = DefenseSlots(
            period_id=period.id,
            slot_date=datetime.date(2026, 12, 15),
            start_time=datetime.time(8, 30),
            end_time=datetime.time(9, 30),
        )
        session.add(slot)
        session.flush()

        committee = Committees(period_id=period.id, name=f"{prefix}Hội đồng Mạng 01")
        session.add(committee)
        session.flush()

        # GV An is MEMBER of this committee
        session.add(CommitteeMembers(committee_id=committee.id, user_id=gv_an.id, role_code="MEMBER"))
        session.flush()

        defense_session = DefenseSessions(
            committee_id=committee.id,
            room_id=room.id,
            slot_id=slot.id,
            topic_id=t3.id,
            status="SCHEDULED",
        )
        session.add(defense_session)
        session.flush()

        data = {
            "dept_a_id": dept_a.id,
            "dept_b_id": dept_b.id,
            "gv_an_id": gv_an.id,
            "head_a_id": head_a.id,
            "head_b_id": head_b.id,
            "sv_x_id": sv_x.id,
            "sv_y_id": sv_y.id,
            "period_id": period.id,
            "t1_id": t1.id,
            "t2_id": t2.id,
            "t3_id": t3.id,
            "t4_id": t4.id,
            "committee_id": committee.id,
            "defense_session_id": defense_session.id,
            "room_id": room.id,
            "slot_id": slot.id,
        }

    yield data

    # Teardown
    with transaction_scope() as session:
        # Delete defense session
        ds = session.get(DefenseSessions, data["defense_session_id"])
        if ds:
            session.delete(ds)
        session.query(CommitteeMembers).filter(CommitteeMembers.committee_id == data["committee_id"]).delete()
        c = session.get(Committees, data["committee_id"])
        if c:
            session.delete(c)
        s = session.get(DefenseSlots, data["slot_id"])
        if s:
            session.delete(s)
        r = session.get(Rooms, data["room_id"])
        if r:
            session.delete(r)

        session.query(TopicMembers).filter(TopicMembers.topic_id.in_([data["t1_id"], data["t2_id"], data["t3_id"], data["t4_id"]])).delete()
        for tid in (data["t1_id"], data["t2_id"], data["t3_id"], data["t4_id"]):
            t = session.get(Topics, tid)
            if t:
                session.delete(t)

        p = session.get(Periods, data["period_id"])
        if p:
            session.delete(p)

        all_user_ids = [data["gv_an_id"], data["head_a_id"], data["head_b_id"], data["sv_x_id"], data["sv_y_id"]]
        session.query(UserRoles).filter(UserRoles.user_id.in_(all_user_ids)).delete()
        for uid in all_user_ids:
            u = session.get(Users, uid)
            if u:
                session.delete(u)

        for oid in (data["dept_a_id"], data["dept_b_id"]):
            o = session.get(OrgUnits, oid)
            if o:
                session.delete(o)


def test_multirole_lecturer_across_topics(engine, academic_ecosystem):
    """Confirm Acceptance Criteria: Lecturer sees only their specific function per topic

    and cannot view or evaluate topics they have no relationship with.
    """
    eco = academic_ecosystem
    an_id = eco["gv_an_id"]

    # 1. Topic 1: GV An is ADVISOR
    ctx1 = engine.resolve_context(user_id=an_id, topic_id=eco["t1_id"])
    assert "ADVISOR" in ctx1.topic_roles
    assert engine.can_view_topic(ctx1) is True
    assert engine.can_view_scores(ctx1) is True
    assert engine.can_grade_as_advisor(ctx1) is True
    assert engine.can_grade_as_reviewer(ctx1) is False
    assert engine.can_grade_as_defense_committee(ctx1) is False
    assert engine.can_confirm_eligibility(ctx1) is True

    # 2. Topic 2: GV An is REVIEWER
    ctx2 = engine.resolve_context(user_id=an_id, topic_id=eco["t2_id"])
    assert "REVIEWER" in ctx2.topic_roles
    assert engine.can_view_topic(ctx2) is True
    assert engine.can_view_scores(ctx2) is True
    assert engine.can_grade_as_advisor(ctx2) is False
    assert engine.can_grade_as_reviewer(ctx2) is True
    assert engine.can_grade_as_defense_committee(ctx2) is False
    assert engine.can_confirm_eligibility(ctx2) is False

    # 3. Topic 3: GV An is DEFENSE COMMITTEE MEMBER
    ctx3 = engine.resolve_context(user_id=an_id, topic_id=eco["t3_id"])
    assert "MEMBER" in ctx3.committee_roles
    assert engine.can_view_topic(ctx3) is True
    assert engine.can_view_scores(ctx3) is True
    assert engine.can_grade_as_advisor(ctx3) is False
    assert engine.can_grade_as_reviewer(ctx3) is False
    assert engine.can_grade_as_defense_committee(ctx3) is True

    # 4. Topic 4: GV An has NO relationship (Strict outsider boundary!)
    ctx4 = engine.resolve_context(user_id=an_id, topic_id=eco["t4_id"])
    assert len(ctx4.topic_roles) == 0
    assert len(ctx4.committee_roles) == 0
    assert engine.can_view_topic(ctx4) is False
    assert engine.can_view_scores(ctx4) is False
    assert engine.can_grade_as_advisor(ctx4) is False
    assert engine.can_grade_as_reviewer(ctx4) is False
    assert engine.can_grade_as_defense_committee(ctx4) is False
    assert engine.can_manage_topic(ctx4) is False


def test_cross_department_head_isolation(engine, academic_ecosystem):
    """Department heads can only manage topics within their assigned department."""
    eco = academic_ecosystem
    head_a_id = eco["head_a_id"]
    head_b_id = eco["head_b_id"]

    # Head A on Topic 1 (Dept A): ALLOWED
    ctx_ha_t1 = engine.resolve_context(user_id=head_a_id, topic_id=eco["t1_id"])
    assert ctx_ha_t1.is_head_of_managing_dept is True
    assert engine.can_view_topic(ctx_ha_t1) is True
    assert engine.can_manage_topic(ctx_ha_t1) is True

    # Head A on Topic 3 (Dept B): FORBIDDEN
    ctx_ha_t3 = engine.resolve_context(user_id=head_a_id, topic_id=eco["t3_id"])
    assert ctx_ha_t3.is_head_of_managing_dept is False
    assert engine.can_manage_topic(ctx_ha_t3) is False

    # Head B on Topic 1 (Dept A): FORBIDDEN
    ctx_hb_t1 = engine.resolve_context(user_id=head_b_id, topic_id=eco["t1_id"])
    assert ctx_hb_t1.is_head_of_managing_dept is False
    assert engine.can_manage_topic(ctx_hb_t1) is False

    # Head B on Topic 3 (Dept B): ALLOWED
    ctx_hb_t3 = engine.resolve_context(user_id=head_b_id, topic_id=eco["t3_id"])
    assert ctx_hb_t3.is_head_of_managing_dept is True
    assert engine.can_manage_topic(ctx_hb_t3) is True


def test_student_isolation_and_score_leakage_protection(engine, academic_ecosystem):
    """Students cannot view other students' topics or unfinalized score sheets."""
    eco = academic_ecosystem
    sv_x_id = eco["sv_x_id"]
    sv_y_id = eco["sv_y_id"]

    # Student X on their own topic (Topic 1): Can view topic, but NOT scores while IN_PROGRESS
    ctx_sx_t1 = engine.resolve_context(user_id=sv_x_id, topic_id=eco["t1_id"])
    assert "STUDENT" in ctx_sx_t1.topic_roles
    assert engine.can_view_topic(ctx_sx_t1) is True
    assert engine.can_view_scores(ctx_sx_t1) is False  # In progress -> scores hidden

    # Student X attempting to view Student Y's topic (Topic 2): BLOCKED!
    ctx_sx_t2 = engine.resolve_context(user_id=sv_x_id, topic_id=eco["t2_id"])
    assert len(ctx_sx_t2.topic_roles) == 0
    assert engine.can_view_topic(ctx_sx_t2) is False
    assert engine.can_view_scores(ctx_sx_t2) is False

    # When Topic 1 reaches GRADED: Student X can now view finalized scores
    with transaction_scope() as session:
        t1 = session.get(Topics, eco["t1_id"])
        t1.state_code = "GRADED"
        session.flush()

    ctx_sx_t1_graded = engine.resolve_context(user_id=sv_x_id, topic_id=eco["t1_id"])
    assert ctx_sx_t1_graded.topic_state == "GRADED"
    assert engine.can_view_scores(ctx_sx_t1_graded) is True


def test_cancelled_defense_session_revokes_defense_grading(engine, academic_ecosystem):
    """Cancelled defense sessions immediately invalidate committee grading permissions."""
    eco = academic_ecosystem
    an_id = eco["gv_an_id"]

    # When SCHEDULED: GV An can grade defense
    ctx_scheduled = engine.resolve_context(user_id=an_id, topic_id=eco["t3_id"])
    assert "MEMBER" in ctx_scheduled.committee_roles
    assert engine.can_grade_as_defense_committee(ctx_scheduled) is True

    # Cancel the defense session
    with transaction_scope() as session:
        ds = session.get(DefenseSessions, eco["defense_session_id"])
        ds.status = "CANCELLED"
        session.flush()

    # When CANCELLED: Committee role is filtered out and permission is revoked!
    ctx_cancelled = engine.resolve_context(user_id=an_id, topic_id=eco["t3_id"])
    assert len(ctx_cancelled.committee_roles) == 0
    assert engine.can_grade_as_defense_committee(ctx_cancelled) is False
    assert engine.can_view_scores(ctx_cancelled) is False
