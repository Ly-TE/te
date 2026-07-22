from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

try:
    import pymysql
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "缺少依赖 pymysql，请先执行: python -m pip install pymysql"
    ) from exc


load_dotenv()

HOST = os.getenv("TEST_DB_HOST", "localhost")
PORT = int(os.getenv("TEST_DB_PORT", "3306"))
USER = os.getenv("TEST_DB_USER", "root")
PASSWORD = os.getenv("TEST_DB_PASSWORD", "")
DATABASE = os.getenv("TEST_DB_NAME", "thorfast_config")


def get_connection():
    return pymysql.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        database=DATABASE,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=10,
        read_timeout=10,
        write_timeout=10,
        autocommit=False,
    )


def test_connection() -> None:
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT DATABASE() AS db, NOW() AS now_time")
            row = cursor.fetchone()
            print("数据库连接成功")
            print(f"当前库: {row['db']}")
            print(f"数据库时间: {row['now_time']}")
    finally:
        connection.close()


def save_connection_info() -> None:
    output = Path("prd_for_testcase/mysql_connection_info.txt")
    output.write_text(
        "\n".join(
            [
                f"host={HOST}",
                f"port={PORT}",
                f"user={USER}",
                f"database={DATABASE}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    save_connection_info()
    test_connection()