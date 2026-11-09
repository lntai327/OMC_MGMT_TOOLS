from typing import List, Optional, Tuple

from backend.repositories.base_repo import BaseRepository
from backend.util.ex_handle_util import ExcelHandleUtil
from share.constant import constant as SC
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil
from share.util.convert import normalize_str_input_value
from share.util.logger_util import LoggerUtil
from share.util.time_util import TimeUtil


class BaseService:
    _model_class = None
    _repo: BaseRepository = None

    def get_all(self) -> List[dict]:
        record_list = self._repo.get_all()
        return [item.to_dict() for item in record_list]

    def get_by_keys(self, key_value_dict) -> Optional[dict]:
        record = self._repo.get_by_keys(key_value_dict)
        return record.to_dict() if record else None

    def delete_by_keys(self, key_value_dict) -> bool:
        return self._repo.delete_by_keys(key_value_dict)

    def delete_all(self) -> int:
        return self._repo.delete_all()

    def _get_excel_config(self) -> Tuple[str, str, int]:
        """Return (excel_info_key, sheet_info_key, header_row_range).
        header_row_range defaults to 1 if not relevant."""
        raise NotImplementedError

    def _get_data_payload_key(self) -> List:
        """Return tuple of keys that form the data payload for create/update."""
        raise NotImplementedError

    def _get_unique_record_key(self) -> List:
        """Return the constant used as the unique dedup key."""
        raise NotImplementedError
    
    ###

    def _get_must_valid_record_key(self) -> List:
        """Return list keyd must valid."""
        return []

    def _filter_record(self, record: dict) -> bool:
        """Return True to KEEP the record, False to skip it.
        Override for domain-specific filtering. Default keeps all."""
        return True

    def _use_replace_all_strategy(self) -> bool:
        """Return True to use delete-all + re-insert strategy.
        Default uses upsert (diff-based) strategy."""
        return False

    def _is_same_import_record(self, existing_record: dict, imported_record: dict) -> bool:
        compare_keys = self._get_data_payload_key()
        return all(
            normalize_str_input_value(existing_record.get(key, "N/A"))
            == normalize_str_input_value(imported_record.get(key, "N/A"))
            for key in compare_keys
        )

    def _get_import_record_key(self, record: dict, unique_keys: List) -> tuple | None:
        key_val = tuple(
            normalize_str_input_value(record.get(key))
            for key in unique_keys
        )

        return key_val

    def import_from_excel(self) -> dict:
        excel_info_key, sheet_info_key, header_row_range = self._get_excel_config()

        excel_path = ExplorerUtil().get_cache_file_path(
            DynamicInfoUtil().get_value(2, excel_info_key, SC.K_NAME)
        )

        sheet_name_value = DynamicInfoUtil().get_value(
            4, excel_info_key, SC.K_REQUIRE_SHEET,
            sheet_info_key, SC.K_NAME
        )

        sheet_names = sheet_name_value

        # Load data from all matching sheets
        record_list: list[dict] = []
        for sheet_name in sheet_names:
            load_kwargs = dict(
                sheet_name=sheet_name,
                sheet_info_key=sheet_info_key,
                excel_info_key=excel_info_key,
                excel_path=excel_path,
            )
            if header_row_range > 1:
                load_kwargs["header_row_range"] = header_row_range

            sheet_records = ExcelHandleUtil().load_items(**load_kwargs)
            LoggerUtil.get_logger().info(
                f"{self.__class__.__name__} loaded {len(sheet_records)} records from sheet '{sheet_name}'"
            )
            record_list.extend(sheet_records)

        # Parse raw records through model
        raw_records = [self._model_class().load(x).to_dict() for x in record_list]

        # Domain-specific filtering
        raw_records = [r for r in raw_records if self._filter_record(r)]

        if self._use_replace_all_strategy():
            return self._import_replace_all(raw_records)
        else:
            return self._import_upsert(raw_records)

    # ── Replace-all strategy ───────────────────────────────────────
    def _import_replace_all(self, raw_records: List[dict]) -> dict:
        must_valid_keys = self._get_must_valid_record_key()
        data_keys = self._get_data_payload_key()

        # Deduplicate
        valid_records = []
        seen = set()
        for record in raw_records:
            if not record or all(
                v is None or str(v).strip() == "" for v in record.values()
            ):
                continue

            valid_record = True
            for k in must_valid_keys:
                v = normalize_str_input_value(record.get(k))

                if not v or v == "":
                    valid_record = False
                    break
            if not valid_record:
                continue

            # Use frozenset of data for dedup (since no single unique key for replace-all)
            record_tuple = tuple(
                normalize_str_input_value(record.get(k, "N/A"))
                for k in data_keys
            )
            if record_tuple not in seen:
                seen.add(record_tuple)
                to_create_dict = {
                    k: normalize_str_input_value(record.get(k, "N/A"))
                    for k in data_keys
                }
                valid_records.append(to_create_dict)

        # Bulk operation: delete all + insert all
        self._repo.bulk_insert_all(valid_records)

        added_count = len(valid_records)
        return {
            "total": added_count,
            "added": added_count,
            "updated": 0,
            "unchanged": 0,
            "deleted": 0,  # delete_all count not tracked here for simplicity
        }

    # ── Upsert strategy ───────────────────────────────────────────
    def _import_upsert(self, raw_records: List[dict]) -> dict:
        unique_keys = self._get_unique_record_key()
        must_valid_keys = self._get_must_valid_record_key()
        data_keys = self._get_data_payload_key()

        # Deduplicate by unique key (keep first occurrence)
        valid_records_by_key = {}
        for record in raw_records:
            if not record or all(
                v is None or str(v).strip() == "" for v in record.values()
            ):
                continue

            valid_record = True
            for k in must_valid_keys:
                v = normalize_str_input_value(record.get(k))

                if not v or v == "":
                    valid_record = False
                    break
            if not valid_record:
                continue

            key_val = self._get_import_record_key(record, unique_keys)
            if key_val is None:
                continue

            if key_val not in valid_records_by_key:
                valid_records_by_key[key_val] = record
            else:
                LoggerUtil.get_logger().warning(
                    f"{self.__class__.__name__} duplicate record found for record: {record}, key {key_val}, keeping first occurrence"
                )

        # Build fast in-memory map of existing DB records (including primary key 'id' if present)
        all_existing = self._repo.get_all_with_id()
        existing_map = {}
        for record in all_existing:
            key_val = self._get_import_record_key(record, unique_keys)
            if key_val is None:
                continue

            existing_map[key_val] = record

        all_existing_keys = set(existing_map.keys())
        imported_keys = set(valid_records_by_key.keys())

        to_create: list[dict] = []
        to_update: list[dict] = []
        to_delete: list[dict] = []
        unchanged_count = 0
        current_time_str = TimeUtil().get_detail_current_time_str()

        # Categorize records into create, update, or unchanged
        for key_val, imported_rec in valid_records_by_key.items():
            data_dict = {
                k: normalize_str_input_value(imported_rec.get(k, "N/A"))
                for k in data_keys
            }

            if key_val in existing_map:
                existing_rec = existing_map[key_val]
                if self._is_same_import_record(existing_rec, imported_rec):
                    unchanged_count += 1
                else:
                    data_dict[SC.K_LAST_UPDATE] = current_time_str
                    if "id" in existing_rec:
                        data_dict["id"] = existing_rec["id"]
                    to_update.append(data_dict)
            else:
                to_create.append(data_dict)

        to_delete_keys = list(all_existing_keys - imported_keys)
        for item in to_delete_keys:
            to_delete.append(existing_map.get(item, {}))

        # Execute bulk save within single DB session transaction
        self._repo.bulk_save_import(to_create, to_update, to_delete)

        added_count = len(to_create)
        updated_count = len(to_update)
        deleted_count = len(to_delete)

        total = added_count + updated_count + unchanged_count

        LoggerUtil.get_logger().info(
            f"{self.__class__.__name__} total record valid {total}, added {added_count}, updated {updated_count}"
            f", unchanged {unchanged_count}, deleted {deleted_count}"
        )

        return {
            "total": total,
            "added": added_count,
            "updated": updated_count,
            "unchanged": unchanged_count,
            "deleted": deleted_count,
        }
