"""Transactional signed append only. Verifier/export remain item 10."""

import hashlib
from datetime import datetime
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils
from sqlalchemy.ext.asyncio import AsyncConnection

from hirz import db
from hirz.pipeline.hashing import digest, timestamp, wire
from hirz.pipeline.models import Decision, EventType


class PipelineError(RuntimeError):
    """Safe fail-closed error: no committed authorization is returned."""


class AuditWriter:
    def __init__(self, key: ec.EllipticCurvePrivateKey):
        if not isinstance(key.curve, ec.SECP256R1):
            raise PipelineError("Audit signing requires P-256")
        self.key = key
        self.fingerprint = hashlib.sha256(
            key.public_key().public_bytes(
                serialization.Encoding.DER,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        ).hexdigest()

    async def append(
        self,
        connection: AsyncConnection,
        household_id: UUID,
        at: datetime,
        event: EventType,
        payload: dict[str, Any] | Decision,
    ) -> int:
        # The caller already owns the graph transaction lock, before this row lock.
        pointer = (
            (
                await connection.execute(
                    sa.select(db.audit_pointer)
                    .where(db.audit_pointer.c.household_id == household_id)
                    .with_for_update()
                )
            )
            .mappings()
            .one_or_none()
        )
        head = (
            (
                await connection.execute(
                    sa.select(db.audit_log)
                    .where(db.audit_log.c.household_id == household_id)
                    .order_by(db.audit_log.c.seq.desc())
                    .limit(1)
                )
            )
            .mappings()
            .one_or_none()
        )
        if pointer is None:
            if head is not None:
                raise PipelineError("Invalid audit pointer")
            await connection.execute(
                db.audit_pointer.insert().values(household_id=household_id)
            )
            seq, previous = 1, "0" * 64
        else:
            seq, previous = pointer["seq"] + 1, pointer["curr_hash"]
            if (head is None and (seq != 1 or previous != "0" * 64)) or (
                head is not None
                and (
                    head["seq"] != seq - 1
                    or head["curr_hash"] != previous
                    or head["key_fingerprint"] != self.fingerprint
                    or head["created_at"] > at
                )
            ):
                raise PipelineError("Invalid audit pointer or incompatible signing key")
        if isinstance(payload, Decision):
            payload = payload.model_copy(update={"audit_id": seq}).model_dump(
                mode="json", by_alias=True
            )
        envelope = dict(
            household_id=str(household_id),
            seq=seq,
            event_type=event.value,
            payload=wire(payload),
            prev_hash=previous,
            key_fingerprint=self.fingerprint,
            created_at=timestamp(at),
        )
        current = digest(envelope)
        signature = self.key.sign(
            bytes.fromhex(current), ec.ECDSA(utils.Prehashed(hashes.SHA256()))
        )
        await connection.execute(
            db.audit_log.insert().values(
                **(envelope | {"household_id": household_id, "created_at": at}),
                curr_hash=current,
                signature=signature,
            )
        )
        await connection.execute(
            db.audit_pointer.update()
            .where(db.audit_pointer.c.household_id == household_id)
            .values(seq=seq, curr_hash=current)
        )
        return seq
