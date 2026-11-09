from typing import Generic, TypeVar, Type, List, Optional

from sqlalchemy import and_, or_ #tuple_
from sqlalchemy.types import String
from backend.db.database import Database

from share.util.logger_util import LoggerUtil

T = TypeVar("T")

class BaseRepository(Generic[T]):

    def __init__(self, model: Type[T]):
        self._db = Database()
        self._model = model

    def _validate_string_lengths(self, records: List[dict], auto_truncate: bool = False) -> List[dict]:
        logger = LoggerUtil.get_logger()
        table_name = self._model.__tablename__

        # col_info: {col_name: (max_length, data_type)}
        col_info = {}
        try:
            with self._db.get_session() as session:
                rows = session.execute(
                    __import__('sqlalchemy').text(
                        "SELECT COLUMN_NAME, CHARACTER_MAXIMUM_LENGTH, DATA_TYPE "
                        "FROM INFORMATION_SCHEMA.COLUMNS "
                        "WHERE TABLE_NAME = :table_name "
                        "AND CHARACTER_MAXIMUM_LENGTH IS NOT NULL"
                    ),
                    {"table_name": table_name}
                ).fetchall()
                for row in rows:
                    col_info[row[0]] = (row[1], row[2].lower() if row[2] else "unknown")
                # if col_info:
                #     logger.debug(
                #         f"{self.__class__.__name__}:"
                #         f" DB schema: {({k: f'{v[1]}({v[0]})' for k, v in col_info.items()})}"
                #     )
        except Exception as e:
            logger.warning(
                f"{self.__class__.__name__}:"
                f" Could not query DB schema: {e}. Falling back to model-declared lengths."
            )

        # Fallback to model-declared lengths (assume nvarchar)
        if not col_info:
            for col in self._model.__table__.columns:
                if isinstance(col.type, String) and col.type.length is not None:
                    col_info[col.name] = (col.type.length, "nvarchar")

        if not col_info:
            return []

        violations = []
        truncated_count = 0
        for idx, record in enumerate(records):
            for col_name, (max_len, data_type) in col_info.items():
                value = record.get(col_name)
                if value is None or not isinstance(value, str):
                    continue

                # VARCHAR: max_len is in BYTES, so encode to check byte length
                # NVARCHAR: max_len is in CHARACTERS
                is_nvarchar = "nvarchar" in data_type or "nchar" in data_type
                if is_nvarchar:
                    actual_len = len(value)
                    len_type = "chars"
                else:
                    # varchar, char, etc. — byte-based
                    actual_len = len(value.encode("utf-8"))
                    len_type = "bytes"

                if actual_len > max_len:
                    violation = {
                        "record_index": idx,
                        "column": col_name,
                        "data_type": f"{data_type}({max_len})",
                        "max_length": max_len,
                        f"actual_{len_type}": actual_len,
                        "value_preview": value[:200],
                        "record_keys": {k: str(v)[:80] for k, v in record.items()},
                    }
                    violations.append(violation)

                    if auto_truncate:
                        # Truncate the value in-place within the record dict
                        if is_nvarchar:
                            record[col_name] = value[:max_len]
                        else:
                            # For byte-based columns, truncate safely without
                            # breaking multi-byte characters
                            encoded = value.encode("utf-8")[:max_len]
                            record[col_name] = encoded.decode("utf-8", errors="ignore")
                        truncated_count += 1
                        logger.warning(
                            f"{self.__class__.__name__} AUTO-TRUNCATED:"
                            f" record[{idx}].{col_name}"
                            f" {actual_len} {len_type} -> {max_len}"
                            f" (was: {value[:120]!r}...)"
                        )
                    else:
                        logger.warning(
                            f"{self.__class__.__name__} TRUNCATION RISK: "
                            f" {str(violation)}"
                        )

        if violations:
            if auto_truncate:
                logger.warning(
                    f"{self.__class__.__name__}:"
                    f" Auto-truncated {truncated_count} field(s)"
                    f" across {len(records)} records to fit DB column limits."
                )
            else:
                logger.error(
                    f"{self.__class__.__name__}:"
                    f" Found {len(violations)} field(s) that would be truncated."
                )

        return violations

    def _diagnose_truncation_error(self, session, record: dict, record_idx: int):
        logger = LoggerUtil.get_logger()
        table_name = self._model.__tablename__
        logger.info(f"========== [DIAGNOSIS START: Analyzing record[{record_idx}]] ==========")

        # 1. Check all columns in actual DB table (including hidden/computed/default columns)
        try:
            col_defs = session.execute(__import__('sqlalchemy').text(
                "SELECT c.name, t.name AS type_name, c.max_length, c.is_nullable, "
                "OBJECT_DEFINITION(c.default_object_id) AS default_val, c.is_identity "
                "FROM sys.columns c "
                "JOIN sys.types t ON c.user_type_id = t.user_type_id "
                "WHERE c.object_id = OBJECT_ID(:table_name)"
            ), {"table_name": table_name}).fetchall()
            logger.info(
                f"[DIAGNOSIS 1] sys.columns for '{table_name}':\n" +
                "\n".join([
                    f"   - {c[0]}: {c[1]} (max_length_bytes={c[2]}, is_nullable={c[3]}, identity={c[5]}, default={c[4]})"
                    for c in col_defs
                ])
            )
        except Exception as e:
            logger.error(f"[DIAGNOSIS 1] Could not query sys.columns: {e}")

        # 2. Check for triggers on the table (triggers frequently cause 8152 in audit tables)
        try:
            triggers = session.execute(__import__('sqlalchemy').text(
                "SELECT name, is_disabled FROM sys.triggers WHERE parent_id = OBJECT_ID(:table_name)"
            ), {"table_name": table_name}).fetchall()
            if triggers:
                logger.info(f"[DIAGNOSIS 2] TRIGGERS FOUND on table '{table_name}': {triggers}")
                for trg in triggers:
                    trg_name = trg[0]
                    try:
                        trg_def = session.execute(__import__('sqlalchemy').text(
                            "SELECT OBJECT_DEFINITION(OBJECT_ID(:trg_name))"
                        ), {"trg_name": trg_name}).scalar()
                        logger.info(f"[DIAGNOSIS 2] Trigger '{trg_name}' definition:\n{trg_def}")
                    except Exception:
                        pass
            else:
                logger.info(f"[DIAGNOSIS 2] No triggers found on '{table_name}'.")
        except Exception as e:
            logger.error(f"[DIAGNOSIS 2] Could not query sys.triggers: {e}")

        # 3. Test dummy record where all fields are '1'
        dummy_record = {k: '1' for k in record.keys()}
        dummy_passed = False
        try:
            d_obj = self._model(**dummy_record)
            session.add(d_obj)
            session.flush()
            session.rollback()
            dummy_passed = True
            logger.info("[DIAGNOSIS 3] Dummy record (all fields='1') insert SUCCEEDED. The issue is specific to a value in the record.")
        except Exception as dummy_err:
            session.rollback()
            logger.error(
                f"===> [DIAGNOSIS 3 FAILED: TABLE OR TRIGGER ISSUE, NOT RECORD DATA!] <===\n"
                f"Even an insert where EVERY field was '1' failed with:\n{dummy_err}\n"
                f"This proves the truncation happens inside a TRIGGER or DEFAULT constraint in SQL Server, NOT from your data!"
            )

        # 4. If dummy passed, test each column individually with its actual value
        if dummy_passed:
            culprit_found = False
            for col_name, col_val in record.items():
                test_rec = {k: '1' for k in record.keys()}
                test_rec[col_name] = col_val
                try:
                    t_obj = self._model(**test_rec)
                    session.add(t_obj)
                    session.flush()
                    session.rollback()
                except Exception as col_err:
                    session.rollback()
                    culprit_found = True
                    logger.error(
                        f"===> [DIAGNOSIS 4: CULPRIT COLUMN IDENTIFIED!] <===\n"
                        f"   Column: '{col_name}'\n"
                        f"   Error: {col_err}\n"
                        f"   Value: {col_val!r}\n"
                        f"   Len chars: {len(str(col_val))}\n"
                        f"   Len utf8 bytes: {len(str(col_val).encode('utf-8'))}"
                    )
            if not culprit_found:
                logger.info(
                    "[DIAGNOSIS 4] No single column failed on its own. The error may be caused by a combination of columns or total row size."
                )

        logger.info(f"========== [DIAGNOSIS END] ==========")

    def _bulk_insert_with_fallback(self, session, chunk: List[dict], batch_offset: int = 0):
        """Try bulk insert; on truncation error, retry row-by-row to find the bad record."""
        logger = LoggerUtil.get_logger()
        try:
            session.bulk_insert_mappings(self._model, chunk)
            session.flush()
        except Exception as e:
            error_str = str(e)
            if "22001" in error_str or "truncated" in error_str.lower():
                logger.error(
                    f"{self.__class__.__name__} insert failed with truncation error. "
                    f"Retrying {len(chunk)} records one-by-one to find bad record(s)..."
                )
                session.rollback()
                for idx, record in enumerate(chunk):
                    try:
                        obj = self._model(**record)
                        session.add(obj)
                        session.flush()
                        session.expunge(obj)
                    except Exception as row_err:
                        global_idx = batch_offset + idx
                        logger.error(
                            f"{self.__class__.__name__} INSERT FAILED at record[{global_idx}]:"
                            f" error={row_err}"
                            f" {({k: str(v)[:100] for k, v in record.items()})}"
                        )
                        session.rollback()
                        # Run deep forensic diagnosis on the very first failing record
                        self._diagnose_truncation_error(session, record, global_idx)
                        raise
                raise
            else:
                raise

    # ── Override in subclass to enable key-based CRUD ──────────────
    def _get_unique_key_column_dict(self) -> dict:
        """Return the SQLAlchemy Column used as unique key (e.g. MyModel.id: id).
        Override in subclass."""
        return {}

    def _get_value_by_keys(self, key_value_dict: dict, key_names: List) -> List:
        if not isinstance(key_value_dict, dict):
            LoggerUtil.get_logger().error(
                f"{self.__class__.__name__} _get_value_by_keys key_value_dict: {key_value_dict} must a dict"
            )

            raise ValueError(
                f"app error"
            )
        
        return [key_value_dict.get(key_name, 'N/A') for key_name in key_names]

    def _filter_by_unique_keys_query(self, key_value_dict: dict):
        unique_key_cols = self._get_unique_key_column_dict().keys()
        unique_key_names = self._get_unique_key_column_dict().values()
        key_values = self._get_value_by_keys(key_value_dict, unique_key_names)
        return and_(
            *(key_col == key_value for key_col, key_value in zip(unique_key_cols, key_values))
        )

    def _key_value_from_record(self, item: dict, key_names: List):
        if not isinstance(item, dict):
            return None

        key_values = tuple(item.get(key_name) for key_name in key_names)

        return key_values

    def _key_from_obj(self, obj, key_names: List) -> tuple:
        return tuple(getattr(obj, key_name) for key_name in key_names)

    def _key_in_filter_query(self, key_values: List[tuple]):
        unique_key_cols = list(self._get_unique_key_column_dict().keys())

        # PostgreSQL
        # return tuple_(*unique_key_cols).in_(key_values)

        # SQL Server
        if len(unique_key_cols) == 1:
            return unique_key_cols[0].in_(
                [key[0] for key in key_values]
            )

        return or_(
            *(
                and_(
                    *(
                        key_col == key_value
                        for key_col, key_value in zip(unique_key_cols, key)
                    )
                )
                for key in key_values
            )
        )

    # ── Basic CRUD ─────────────────────────────────────────────────
    def get_all(self) -> List[T]:
        with self._db.get_session() as session:
            return session.query(self._model).all()

    def get_all_with_id(self) -> List[dict]:
        """Fetch all records and return list of dicts including the 'id' column if present."""
        with self._db.get_session() as session:
            records = session.query(self._model).all()
            result = []
            for r in records:
                d = r.to_dict()
                if hasattr(r, 'id') and r.id is not None:
                    d['id'] = r.id
                result.append(d)
            return result
        
    def create(self, data: dict):
        # LoggerUtil.get_logger().info(f"BaseRepository create: {data}")
        with self._db.get_session() as session:
            record = self._model(**data)
            session.add(record)
            session.flush()
            session.refresh(record)
            session.expunge(record)
            return record

    def get_by_id(self, id):
        with self._db.get_session() as session:
            return session.query(self._model) \
                .filter(self._model.id == id).first()

    def update_by_id(self, id, data: dict):
        LoggerUtil.get_logger().info(f"{self.__class__.__name__} update: {data}")
        with self._db.get_session() as session:
            record = session.query(self._model) \
                .filter(self._model.id == id).first()
            if record is None:
                return None
            for key, value in data.items():
                setattr(record, key, value)
            session.flush()
            session.refresh(record)
            session.expunge(record)
            return record

    def delete_by_id(self, id) -> bool:
        LoggerUtil.get_logger().info(f"{self.__class__.__name__} delete: {id}")
        with self._db.get_session() as session:
            record = session.query(self._model) \
                .filter(self._model.id == id).first()
            if record is None:
                return False
            session.delete(record)
            return True
        
    def delete_all(self) -> int:
        LoggerUtil.get_logger().info(f"{self.__class__.__name__} delete all")
        with self._db.get_session() as session:
            deleted_count = session.query(self._model).delete(
                synchronize_session=False
            )
            return deleted_count

    # ── Generic key-based CRUD ─────────────────────────────────────
    def get_by_keys(self, key_value_dict: dict) -> Optional[T]:
        """Get a single record by its unique key."""
        with self._db.get_session() as session:
            return session.query(self._model).filter(
                self._filter_by_unique_keys_query(key_value_dict)
            ).first()

    def update_by_keys(self, key_value_dict: dict, data: dict) -> Optional[T]:
        """Update a single record by its unique key."""
        LoggerUtil.get_logger().info(
            f"{self.__class__.__name__} update_by_keys: {data}")
        with self._db.get_session() as session:
            record = session.query(self._model).filter(
                self._filter_by_unique_keys_query(key_value_dict)
            ).first()
            if record is None:
                return None
            for key, value in data.items():
                setattr(record, key, value)
            session.flush()
            session.refresh(record)
            session.expunge(record)
            return record

    def delete_by_keys(self, key_value_dict: dict) -> bool:
        """Delete a single record by its unique key."""
        LoggerUtil.get_logger().info(
            f"{self.__class__.__name__} delete_by_keys: {key_value_dict}")
        with self._db.get_session() as session:
            record = session.query(self._model).filter(
                self._filter_by_unique_keys_query(key_value_dict)
            ).first()
            if record is None:
                return False
            session.delete(record)
            return True

    # ── Bulk operations ────────────────────────────────────────────
    def bulk_save_import(
        self,
        to_create_dicts: List[dict],
        to_update_dicts: List[dict],
        to_delete_dicts: List[dict],
        batch_size: int = 2000
    ) -> None:
        """Bulk insert/update/delete within a single DB session transaction.
        Used by 'upsert' import strategy."""
        unique_key_names = list(self._get_unique_key_column_dict().values())
        safe_batch_size = min(
            1000,
            2000 // max(1, len(unique_key_names))
        )

        LoggerUtil.get_logger().info(
            f"{self.__class__.__name__} save_import: "
            f" create={len(to_create_dicts)},"
            f" update={len(to_update_dicts)},"
            f" delete={len(to_delete_dicts)}"
        )
        # Validate string lengths before DB operations
        if to_create_dicts:
            self._validate_string_lengths(to_create_dicts, auto_truncate=True)
        if to_update_dicts:
            self._validate_string_lengths(to_update_dicts, auto_truncate=True)

        with self._db.get_session() as session:
            # 1. Bulk Insert
            if to_create_dicts:
                for i in range(0, len(to_create_dicts), batch_size):
                    chunk = to_create_dicts[i:i + batch_size]
                    self._bulk_insert_with_fallback(session, chunk, batch_offset=i)

            # 2. Bulk Update
            if to_update_dicts:
                if "id" in to_update_dicts[0]:
                    for i in range(0, len(to_update_dicts), batch_size):
                        LoggerUtil.get_logger().info(
                            f"{self.__class__.__name__} update range {i}-{i + batch_size}"
                        )
                        chunk = to_update_dicts[i:i + batch_size]
                        session.bulk_update_mappings(self._model, chunk)
                else:
                    for i in range(0, len(to_update_dicts), safe_batch_size):
                        chunk = to_update_dicts[i:i + safe_batch_size]
                        LoggerUtil.get_logger().info(
                            f"{self.__class__.__name__} update range {i}-{i + safe_batch_size}"
                        )

                        key_values = [
                            key for key in (
                                self._key_value_from_record(item, unique_key_names) for item in chunk
                            )
                            if key is not None
                        ]

                        if key_values:
                            existing_objs = session.query(self._model).filter(
                                self._key_in_filter_query(key_values)
                            ).all()

                            obj_map = {
                                self._key_from_obj(obj, unique_key_names): obj
                                for obj in existing_objs
                            }

                            for item in chunk:
                                obj = obj_map.get(self._key_value_from_record(item, unique_key_names))
                                if obj:
                                    for k, val in item.items():
                                        setattr(obj, k, val)

            # 3. Bulk Delete
            if to_delete_dicts:
                delete_batch_size = min(batch_size, 1000)
                if "id" in to_delete_dicts[0]:
                    delete_ids = [item["id"] for item in to_delete_dicts if "id" in item and item["id"] is not None]
                    # LoggerUtil.get_logger().info(
                    #     f"{self.__class__.__name__} fast delete by id: total {len(delete_ids)}"
                    # )
                    for i in range(0, len(delete_ids), delete_batch_size):
                        chunk_ids = delete_ids[i:i + delete_batch_size]
                        if chunk_ids:
                            session.query(self._model).filter(
                                self._model.id.in_(chunk_ids)
                            ).delete(synchronize_session=False)
                else:
                    for i in range(0, len(to_delete_dicts), safe_batch_size):
                        chunk = to_delete_dicts[i:i + safe_batch_size]
                        # LoggerUtil.get_logger().info(
                        #     f"{self.__class__.__name__} delete range {i}-{i + safe_batch_size}"
                        # )

                        key_values = [
                            key for key in (
                                self._key_value_from_record(item, unique_key_names) for item in chunk
                            )
                            if key is not None
                        ]

                        if key_values:
                            session.query(self._model).filter(
                                self._key_in_filter_query(key_values)
                            ).delete(synchronize_session=False)

    def bulk_insert_all(
        self,
        to_create_dicts: List[dict],
        batch_size: int = 5000
    ) -> None:
        """Delete all existing records, then bulk insert new records.
        Used by 'replace-all' import strategy."""
        LoggerUtil.get_logger().info(
            f"{self.__class__.__name__} insert_all: "
            f"create={len(to_create_dicts)}"
        )
        # Validate string lengths before DB operations
        if to_create_dicts:
            self._validate_string_lengths(to_create_dicts, auto_truncate=True)

        with self._db.get_session() as session:
            # 1. Delete all
            session.query(self._model).delete(synchronize_session=False)

            # 2. Bulk Insert
            if to_create_dicts:
                for i in range(0, len(to_create_dicts), batch_size):
                    chunk = to_create_dicts[i:i + batch_size]
                    self._bulk_insert_with_fallback(session, chunk, batch_offset=i)