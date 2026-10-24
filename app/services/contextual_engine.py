from dataclasses import dataclass, field
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.core.database import SessionFactory
from app.models import (
    Users,
    Topics,
    UserRoles,
    TopicMembers,
    DefenseSessions,
    CommitteeMembers,
)


@dataclass
class TopicUserContext:
    """Aggregated security context of a user relative to a specific topic."""
    user_id: int
    topic_id: int
    system_roles: list[str] = field(default_factory=list)
    topic_roles: list[str] = field(default_factory=list)
    committee_roles: list[str] = field(default_factory=list)
    is_head_of_managing_dept: bool = False
    topic_org_unit_id: Optional[int] = None
    topic_state: Optional[str] = None
    topic_exists: bool = True


class ContextualEngine:
    """Contextual Access Control Engine for topic and committee operations."""

    def resolve_context(
        self,
        user_id: int,
        topic_id: int,
        session: Optional[Session] = None,
    ) -> TopicUserContext:
        """Resolve all contextual roles and relationships between a user and a topic.
        
        Fetches:
        - Topic details (state, org_unit_id).
        - User's system roles (and checks if user is head of the managing department).
        - User's active roles in the topic (STUDENT, ADVISOR, REVIEWER, etc.).
        - User's roles in any active committee assigned to defend this topic.
        """
        def _resolve(db: Session) -> TopicUserContext:
            # 1. Fetch topic
            topic = db.get(Topics, topic_id)
            if not topic:
                return TopicUserContext(
                    user_id=user_id,
                    topic_id=topic_id,
                    topic_exists=False,
                )

            # 2. Fetch user's system roles
            ur_stmt = select(UserRoles.role_code, UserRoles.org_unit_id).where(
                UserRoles.user_id == user_id
            )
            ur_rows = db.execute(ur_stmt).all()
            system_roles = [r[0] for r in ur_rows]

            # Determine department head authority
            is_head_of_managing_dept = False
            if "HEAD_OF_DEPT" in system_roles:
                for role_code, org_id in ur_rows:
                    if role_code == "HEAD_OF_DEPT":
                        # Head of managing department if org matches or if head has institute-wide scope (None)
                        if org_id is None or org_id == topic.org_unit_id:
                            is_head_of_managing_dept = True
                            break

            # 3. Fetch user's active/pending roles in this topic
            tm_stmt = select(TopicMembers.role_code).where(
                and_(
                    TopicMembers.topic_id == topic_id,
                    TopicMembers.user_id == user_id,
                    TopicMembers.status.in_(["ACTIVE", "PENDING"]),
                )
            )
            topic_roles = list(db.scalars(tm_stmt).all())

            # 4. Fetch user's committee roles for this topic's defense sessions
            cm_stmt = (
                select(CommitteeMembers.role_code)
                .join(
                    DefenseSessions,
                    DefenseSessions.committee_id == CommitteeMembers.committee_id,
                )
                .where(
                    and_(
                        DefenseSessions.topic_id == topic_id,
                        DefenseSessions.status != "CANCELLED",
                        CommitteeMembers.user_id == user_id,
                    )
                )
            )
            committee_roles = list(db.scalars(cm_stmt).all())

            return TopicUserContext(
                user_id=user_id,
                topic_id=topic_id,
                system_roles=system_roles,
                topic_roles=topic_roles,
                committee_roles=committee_roles,
                is_head_of_managing_dept=is_head_of_managing_dept,
                topic_org_unit_id=topic.org_unit_id,
                topic_state=topic.state_code,
                topic_exists=True,
            )

        if session is not None:
            return _resolve(session)
        with SessionFactory() as db:
            return _resolve(db)

    # -------------------------------------------------------------------------
    # Domain Permission Checks
    # -------------------------------------------------------------------------

    def can_view_topic(self, context: TopicUserContext) -> bool:
        """Check if user can view general information of the topic."""
        if not context.topic_exists:
            return False

        # Admin, Office, and Head of managing department have broad oversight
        if "ADMIN" in context.system_roles or "OFFICE" in context.system_roles:
            return True
        if context.is_head_of_managing_dept:
            return True

        # Members directly assigned to topic (Student, Advisor, Reviewer)
        if len(context.topic_roles) > 0:
            return True

        # Committee members assigned to evaluate topic
        if len(context.committee_roles) > 0:
            return True

        return False

    def can_view_scores(self, context: TopicUserContext) -> bool:
        """Check if user can view grading sheets/scores for the topic.
        
        Rules:
        - Admin, Office, Head of managing dept can always view.
        - Advisors and Reviewers of the topic can view.
        - Committee members of the topic can view.
        - Students can only view after scores are finalized (GRADED or ARCHIVED).
        - Unrelated users cannot view scores.
        """
        if not context.topic_exists:
            return False

        if "ADMIN" in context.system_roles or "OFFICE" in context.system_roles:
            return True
        if context.is_head_of_managing_dept:
            return True

        # Instructors involved in the topic
        if any(r in context.topic_roles for r in ("ADVISOR", "CO_ADVISOR", "EXTERNAL_ADVISOR", "REVIEWER")):
            return True

        # Committee members
        if len(context.committee_roles) > 0:
            return True

        # Students only after grades are finalized
        if "STUDENT" in context.topic_roles and context.topic_state in ("GRADED", "ARCHIVED"):
            return True

        return False

    def can_grade_as_advisor(self, context: TopicUserContext) -> bool:
        """Check if user has permission to submit advisor assessment/scores."""
        if not context.topic_exists:
            return False
        return any(r in context.topic_roles for r in ("ADVISOR", "CO_ADVISOR"))

    def can_grade_as_reviewer(self, context: TopicUserContext) -> bool:
        """Check if user has permission to submit reviewer assessment/scores."""
        if not context.topic_exists:
            return False
        return "REVIEWER" in context.topic_roles

    def can_grade_as_defense_committee(self, context: TopicUserContext) -> bool:
        """Check if user has permission to submit defense committee scores.
        
        Conflict of Interest Invariant (Rule H3/I3):
        An advisor (ADVISOR / CO_ADVISOR) CANNOT score their own student in the defense session,
        even if they are a registered member of the committee.
        """
        if not context.topic_exists:
            return False

        # Strictly forbid advisor from defense grading of their own topic
        if any(r in context.topic_roles for r in ("ADVISOR", "CO_ADVISOR")):
            return False

        return len(context.committee_roles) > 0

    def can_confirm_eligibility(self, context: TopicUserContext) -> bool:
        """Check if user can confirm defense eligibility (US-25). Only main advisor."""
        if not context.topic_exists:
            return False
        return "ADVISOR" in context.topic_roles

    def can_manage_topic(self, context: TopicUserContext) -> bool:
        """Check if user can approve, assign, or administratively modify the topic."""
        if not context.topic_exists:
            return False
        if "ADMIN" in context.system_roles or "OFFICE" in context.system_roles:
            return True
        return context.is_head_of_managing_dept
