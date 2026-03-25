from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException
from sqlalchemy import and_, delete, insert, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import DatabaseError, NotFoundError

logger = logging.getLogger(__name__)


async def commit_transaction(db: AsyncSession) -> None:
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Data upload failed") from e


async def insert_instance(model: type, db: AsyncSession, **kwargs: Any) -> None:
    try:
        stmt = insert(model).values(**kwargs)
        await db.execute(stmt)
        await commit_transaction(db=db)
    except IntegrityError:
        await db.rollback()
        raise
    except SQLAlchemyError:
        await db.rollback()
        raise


async def bulk_insert_instance(model: type, db: AsyncSession, data: list[dict[str, Any]]) -> None:
    try:
        stmt = insert(model)
        await db.execute(stmt, data)
        await commit_transaction(db=db)
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseError("Bulk insertion failed") from e


async def update_instance_by_id(id: int, model: type, db: AsyncSession, **kwargs: Any) -> None:
    try:
        stmt = update(model).where(model.id == id).values(**kwargs)
        result = await db.execute(stmt)
        if result.rowcount == 0:
            raise NotFoundError("record not found")
        await commit_transaction(db=db)
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseError("update failed") from e


async def bulk_update_instance(
    model: type, db: AsyncSession, filter: dict[str, Any], data: dict[str, Any]
) -> None:
    try:
        stmt = update(model)
        for key, value in filter.items():
            stmt = stmt.where(getattr(model, key, value))
        stmt = stmt.values(**data)
        results = await db.execute(stmt)
        if results.rowcount == 0:
            raise NotFoundError("Record not found")
        await commit_transaction(db=db)
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseError("Bulk update failed") from e


async def delete_instance_by_id(id: int, model: type, db: AsyncSession) -> None:
    try:
        stmt = delete(model).where(model.id == id)
        result = await db.execute(stmt)
        if result.rowcount == 0:
            raise NotFoundError("Record not found")
        await commit_transaction(db=db)
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseError("delete failed") from e


async def bulk_delete_instance(model: type, db: AsyncSession, ids: list[int]) -> None:
    try:
        stmt = delete(model).where(model.id.in_(ids))
        results = await db.execute(stmt)
        if results.rowcount == 0:
            raise NotFoundError("Record not found")
        await commit_transaction(db=db)
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseError("Bulk delete failed") from e


async def get_instance_by_id(id: int, model: type, db: AsyncSession) -> Any:
    try:
        stmt = select(model).where(model.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    except SQLAlchemyError as exc:
        raise DatabaseError("Get data failed") from exc


async def get_instance_by_any(model: type, db: AsyncSession, data: dict[str, Any]) -> Any:
    try:
        conditions = []
        for key, value in data.items():
            column = getattr(model, key)
            conditions.append(column == value)
        stmt = select(model).where(and_(*conditions))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    except SQLAlchemyError as exc:
        raise DatabaseError(f"Get data failed: {exc}") from exc


async def bulk_get_instance(model: type, db: AsyncSession, **kwargs: Any) -> list[Any]:
    try:
        stmt = select(model)
        for key, value in kwargs.items():
            if hasattr(model, key):
                stmt = stmt.where(getattr(model, key) == value)
        result = await db.execute(stmt)
        return list(result.scalars().all())
    except SQLAlchemyError as exc:
        raise DatabaseError("Get data failed") from exc
