"""Repository layer for database access patterns."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from operational_semantics.persistence.tables import (
    ApprovalTable,
    AuditRecordTable,
    EvidenceTable,
    ExecutionTable,
    OutcomeTable,
    PolicyDecisionTable,
    ProposalTable,
    SaasResourceTable,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProposalRepository:
    """Repository for proposal CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, proposal: dict[str, Any]) -> ProposalTable:
        record = ProposalTable(**proposal)
        self.session.add(record)
        await self.session.flush()
        return record

    async def get(self, proposal_id: str) -> ProposalTable | None:
        result = await self.session.execute(
            select(ProposalTable).where(ProposalTable.id == proposal_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[ProposalTable]:
        result = await self.session.execute(select(ProposalTable))
        return list(result.scalars().all())


class EvidenceRepository:
    """Repository for evidence CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, evidence: dict[str, Any]) -> EvidenceTable:
        record = EvidenceTable(**evidence)
        self.session.add(record)
        await self.session.flush()
        return record

    async def get(self, evidence_id: str) -> EvidenceTable | None:
        result = await self.session.execute(
            select(EvidenceTable).where(EvidenceTable.id == evidence_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[EvidenceTable]:
        result = await self.session.execute(select(EvidenceTable))
        return list(result.scalars().all())

    async def get_by_ids(self, ids: list[str]) -> list[EvidenceTable]:
        result = await self.session.execute(
            select(EvidenceTable).where(EvidenceTable.id.in_(ids))
        )
        return list(result.scalars().all())


class PolicyDecisionRepository:
    """Repository for policy decision CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, decision: dict[str, Any]) -> PolicyDecisionTable:
        record = PolicyDecisionTable(**decision)
        self.session.add(record)
        await self.session.flush()
        return record

    async def get(self, decision_id: str) -> PolicyDecisionTable | None:
        result = await self.session.execute(
            select(PolicyDecisionTable).where(PolicyDecisionTable.id == decision_id)
        )
        return result.scalar_one_or_none()

    async def get_by_proposal(self, proposal_id: str) -> PolicyDecisionTable | None:
        result = await self.session.execute(
            select(PolicyDecisionTable).where(
                PolicyDecisionTable.proposal_id == proposal_id
            ).order_by(PolicyDecisionTable.evaluated_at.desc())
        )
        return result.scalar_one_or_none()


class ApprovalRepository:
    """Repository for approval CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, approval: dict[str, Any]) -> ApprovalTable:
        record = ApprovalTable(**approval)
        self.session.add(record)
        await self.session.flush()
        return record

    async def get(self, approval_id: str) -> ApprovalTable | None:
        result = await self.session.execute(
            select(ApprovalTable).where(ApprovalTable.id == approval_id)
        )
        return result.scalar_one_or_none()

    async def get_by_proposal(self, proposal_id: str) -> list[ApprovalTable]:
        result = await self.session.execute(
            select(ApprovalTable)
            .where(ApprovalTable.proposal_id == proposal_id)
            .order_by(ApprovalTable.requested_at.desc())
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[ApprovalTable]:
        result = await self.session.execute(select(ApprovalTable))
        return list(result.scalars().all())

    async def update_status(
        self,
        approval_id: str,
        status: str,
        decided_by: str | None = None,
    ) -> ApprovalTable | None:
        record = await self.get(approval_id)
        if record is None:
            return None
        record.status = status
        record.decided_at = _utcnow()
        record.decided_by_actor_id = decided_by
        await self.session.flush()
        return record


class ExecutionRepository:
    """Repository for execution CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, execution: dict[str, Any]) -> ExecutionTable:
        record = ExecutionTable(**execution)
        self.session.add(record)
        await self.session.flush()
        return record

    async def get(self, execution_id: str) -> ExecutionTable | None:
        result = await self.session.execute(
            select(ExecutionTable).where(ExecutionTable.id == execution_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[ExecutionTable]:
        result = await self.session.execute(select(ExecutionTable))
        return list(result.scalars().all())

    async def get_by_proposal(self, proposal_id: str) -> list[ExecutionTable]:
        result = await self.session.execute(
            select(ExecutionTable).where(ExecutionTable.proposal_id == proposal_id)
        )
        return list(result.scalars().all())


class OutcomeRepository:
    """Repository for outcome CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, outcome: dict[str, Any]) -> OutcomeTable:
        record = OutcomeTable(**outcome)
        self.session.add(record)
        await self.session.flush()
        return record

    async def get_by_execution(self, execution_id: str) -> OutcomeTable | None:
        result = await self.session.execute(
            select(OutcomeTable).where(OutcomeTable.execution_id == execution_id)
        )
        return result.scalar_one_or_none()


class AuditRepository:
    """Repository for audit record CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, record: dict[str, Any]) -> AuditRecordTable:
        entry = AuditRecordTable(**record)
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def list_all(self) -> list[AuditRecordTable]:
        result = await self.session.execute(
            select(AuditRecordTable).order_by(AuditRecordTable.timestamp)
        )
        return list(result.scalars().all())

    async def get_by_aggregate(self, aggregate_id: str) -> list[AuditRecordTable]:
        result = await self.session.execute(
            select(AuditRecordTable)
            .where(AuditRecordTable.aggregate_id == aggregate_id)
            .order_by(AuditRecordTable.timestamp)
        )
        return list(result.scalars().all())


class SaasResourceRepository:
    """Repository for synthetic SaaS resource CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, resource: dict[str, Any]) -> SaasResourceTable:
        record = SaasResourceTable(**resource)
        self.session.add(record)
        await self.session.flush()
        return record

    async def get(self, resource_id: str) -> SaasResourceTable | None:
        result = await self.session.execute(
            select(SaasResourceTable).where(SaasResourceTable.id == resource_id)
        )
        return result.scalar_one_or_none()

    async def get_by_system(self, system_type: str) -> list[SaasResourceTable]:
        result = await self.session.execute(
            select(SaasResourceTable).where(SaasResourceTable.system_type == system_type)
        )
        return list(result.scalars().all())

    async def update_state(self, resource_id: str, state: dict[str, Any]) -> SaasResourceTable | None:
        record = await self.get(resource_id)
        if record is None:
            return None
        record.state = state
        await self.session.flush()
        return record

    async def list_all(self) -> list[SaasResourceTable]:
        result = await self.session.execute(select(SaasResourceTable))
        return list(result.scalars().all())
