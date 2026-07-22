from pathlib import Path

from connect_mysql import get_connection


SQL_FILE = Path("prd_for_testcase/lang_resources_batch_insert.sql")


def load_statements() -> list[str]:
    content = SQL_FILE.read_text(encoding="utf-8")
    statements = []
    for chunk in content.split(";"):
        statement = chunk.strip()
        if not statement:
            continue
        if statement.startswith("--") and "\n" not in statement:
            continue
        lines = [line for line in statement.splitlines() if not line.strip().startswith("--")]
        cleaned = "\n".join(lines).strip()
        if cleaned:
            statements.append(cleaned)
    return statements


def main() -> None:
    statements = load_statements()
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            for index, statement in enumerate(statements, start=1):
                cursor.execute(statement)
                print(f"[{index}/{len(statements)}] OK")
        connection.commit()
        print(f"执行完成，共提交 {len(statements)} 条 SQL")
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()