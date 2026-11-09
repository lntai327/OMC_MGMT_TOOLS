from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pubsub import pub

from backend.constant import type as T
from backend.db.sqlserver import SqlServer
from backend.db.database import Database

from share.util.logger_util import LoggerUtil
from share.util.time_util import TimeUtil
from share.constant import constant as SC

class DatabaseAdapter(ABC):
    """Abstract base class for database operations"""

    db_keep_all_list = [
        SC.K_TABLE_BC_BTS_MLL_TGHOP, SC.K_TABLE_BC_BTS_MLL_TGHOP_DA_LOAI_TRU
    ]

    @abstractmethod
    def load(self, table_name: str) -> List[Dict[str, Any]]:
        """Load all records from a table"""
        pass

    @abstractmethod
    def get_rows_list_by_value(self, table_name: str, id_value_dict: dict) -> List[Dict[str, Any]]:
        """Get rows matching the specified criteria"""
        pass

    @abstractmethod
    def write_to_db(self, table_name: str, new_record_dict_list: List[Dict[str, Any]]) -> None:
        """Write records to database"""
        pass

    @staticmethod
    def _get_id_key_list(table_name: str) -> List[str]:
        """Get primary key columns for a table"""
        id_key_list = []

        match table_name:
            case SC.K_TABLE_CELL2G | SC.K_TABLE_CELL3G | SC.K_TABLE_CELL4G | SC.K_TABLE_CELL5G | \
                    SC.K_TABLE_BTS2G | SC.K_TABLE_NODEB3G | SC.K_TABLE_ENODEB4G | \
                    SC.K_TABLE_GNODEB5G:
                id_key_list.append(SC.K_TEN_TREN_HE_THONG)
            case SC.K_TABLE_BC_BTS_MLL_TGHOP | SC.K_TABLE_BC_BTS_MLL_TGHOP_DA_LOAI_TRU:
                id_key_list = [SC.K_TTVT, SC.K_HE_THONG, SC.K_NAM,
                               SC.K_RP_TIME_TYPE, SC.K_RP_TIME]
            case SC.K_TABLE_CSHT_CCL | SC.K_TABLE_DMOI_QLY_CSHT | SC.K_TABLE_DMOI_QLY_CSHT_1:
                id_key_list.append(SC.K_MA_CSHT)
            case SC.K_TABLE_TTVT:
                id_key_list.append(SC.K_TTVT)
            case _:
                LoggerUtil.get_logger().error(f"_get_id_key_list failed : Invalid table_name {table_name}")
                raise ValueError(f"_get_id_key_list failed : Invalid table_name {table_name}")

        return id_key_list

class SqlServerAdapter(DatabaseAdapter):
    """SQL Server implementation of DatabaseAdapter"""

    def __init__(self):
        pass

    def _get_connection(self):
        """Return a raw DBAPI (pyodbc) connection from the shared SqlServer engine."""
        return Database().get_raw_connection()

    def load(self, table_name: str) -> List[Dict[str, Any]]:
        rows_as_dicts = []
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(f'SELECT * FROM [{table_name}]')
            item_list = cursor.fetchall()
            headers = [desc[0] for desc in cursor.description]
            rows_as_dicts = [dict(zip(headers, row)) for row in item_list]
        except Exception as e:
            LoggerUtil.get_logger().info(f'SqlServerAdapter load failed {e}')
            raise RuntimeError(f'SqlServerAdapter load failed {e}')
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
            cursor = None
        return rows_as_dicts

    def get_rows_list_by_value(self, table_name: str, id_value_dict: dict) -> List[Dict[str, Any]]:
        row_as_dict_list = []
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            where_clause = " AND ".join([f'[{key}] = ?' for key in id_value_dict.keys()])
            where_values = [id_value_dict.get(key, "") for key in id_value_dict.keys()]

            cursor.execute(f'SELECT * FROM [{table_name}] WHERE {where_clause}', where_values)

            row_values = cursor.fetchall()
            if row_values:
                headers = [desc[0] for desc in cursor.description]
                row_as_dict_list = [dict(zip(headers, row)) for row in row_values]
        except Exception as e:
            LoggerUtil.get_logger().error(f'SqlServerAdapter get_rows_list_by_value failed {e}')
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
            cursor = None

        return row_as_dict_list

    def write_to_db(self, table_name: str, new_record_dict_list: List[Dict[str, Any]]) -> None:
        if len(new_record_dict_list) == 0:
            LoggerUtil.get_logger().info(f"write_to_db new_record_list is empty")

        id_key_list = self._get_id_key_list(table_name)

        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Get table columns from INFORMATION_SCHEMA
            cursor.execute(
                f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                f"WHERE TABLE_NAME = '{table_name}' "
                f"ORDER BY ORDINAL_POSITION"
            )
            table_info = cursor.fetchall()
            table_columns = [row[0] for row in table_info] if table_info else []
            cr_date_time = TimeUtil().get_detail_current_time_str()

            if not table_columns:
                self._create_table_if_not_exists(table_name, new_record_dict_list[0])
                cursor.execute(
                    f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                    f"WHERE TABLE_NAME = '{table_name}' "
                    f"ORDER BY ORDINAL_POSITION"
                )
                table_info = cursor.fetchall()
                table_columns = [row[0] for row in table_info]

            canonical_column = [c for c in table_columns if c not in [SC.K_ID, SC.K_LAST_UPDATE]]

            # Load existing records
            existing_records = self.load(table_name)
            existing_dict = {tuple(rec[k] for k in id_key_list): rec for rec in existing_records}

            # make dict for new records with id tuple as key for easy comparison
            new_dict = {
                tuple(rec[k] for k in id_key_list): rec for rec in new_record_dict_list
            }

            # Process new records: update if changed, insert if new
            for key, new_rec in new_dict.items():
                if key in existing_dict:
                    existing_rec = existing_dict[key]

                    # Check if any value changed
                    same = all(
                        existing_rec.get(col, SC.K_UI_MSG_MISS_DB) == new_rec.get(col, SC.K_UI_MSG_MISS_DB) \
                            for col in canonical_column
                    )
                    if not same:
                        # Update
                        set_clause = ", ".join([f'[{col}] = ?' for col in canonical_column])
                        values = [new_rec.get(col, SC.K_UI_MSG_MISS_DB) for col in canonical_column] \
                            + [cr_date_time, existing_rec[SC.K_ID]]
                        cursor.execute(
                            f'UPDATE [{table_name}] SET {set_clause}, [{SC.K_LAST_UPDATE}] = ? \
                            WHERE [{SC.K_ID}] = ?', values
                        )
                else:
                    # Insert
                    insert_cols = [f'[{c}]' for c in canonical_column] + [f'[{SC.K_LAST_UPDATE}]']
                    placeholders = ", ".join(["?" for _ in canonical_column]) + ", ?"
                    insert_values = [new_rec.get(c, SC.K_UI_MSG_MISS_DB) for c in canonical_column] + [cr_date_time]
                    cursor.execute(
                        f"INSERT INTO [{table_name}] ({', '.join(insert_cols)}) VALUES ({placeholders})", insert_values
                    )

            # Delete (noted that delete is only performed for tables not in db_keep_all_list)
            if table_name not in self.db_keep_all_list:
                for key, existing_rec in existing_dict.items():
                    if key not in new_dict:
                        cursor.execute(f'DELETE FROM [{table_name}] WHERE [{SC.K_ID}] = ?', (existing_rec[SC.K_ID],))

            conn.commit()
        except Exception as e:
            LoggerUtil.get_logger().error(f'SqlServerAdapter write_to_db failed {e}')
            raise RuntimeError(f'SqlServerAdapter write_to_db failed {e}')
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
            cursor = None

    def _create_table_if_not_exists(self, table_name: str, sample_item: dict) -> None:
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Check if table exists
            cursor.execute(
                f"SELECT 1 FROM INFORMATION_SCHEMA.TABLES "
                f"WHERE TABLE_NAME = '{table_name}'"
            )

            if cursor.fetchone() is None:
                # Table doesn't exist, create it
                columns = [f'[{SC.K_ID}] INT PRIMARY KEY IDENTITY(1,1)']
                columns += [f'[{key}] NVARCHAR(MAX)' for key in sample_item.keys()]
                columns += [f'[{SC.K_LAST_UPDATE}] NVARCHAR(MAX)']

                create_table_sql = f"CREATE TABLE [{table_name}] ({', '.join(columns)})"
                cursor.execute(create_table_sql)
                conn.commit()
        except Exception as e:
            LoggerUtil.get_logger().error(f'SqlServerAdapter _create_table_if_not_exists failed {e}')
            raise RuntimeError(f'SqlServerAdapter _create_table_if_not_exists failed {e}')
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
            cursor = None

class DatabaseFactory:
    @staticmethod
    def create_adapter() -> DatabaseAdapter:
        db_cf = SqlServer().get_db_config() or {}
        variant = db_cf.get(SC.K_VARIANT, '').lower()

        match variant:
            # case 'sqlite':
            #     db_path = ExplorerUtil().get_dt_file_path(SC.K_APP_ETILQS)
            #     if not db_path:
            #         raise ValueError("SQLite configuration requires 'path' parameter")
            #     return SqliteAdapter(db_path)

            case 'sql_server' | 'sql_server_test':
                return SqlServerAdapter()

            case _:
                raise ValueError(f"DatabaseFactory: unsupported db variant '{variant}'")
