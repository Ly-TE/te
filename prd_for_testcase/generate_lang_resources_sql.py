from pathlib import Path


SOURCE_PATH = Path(r"prd_for_testcase/sql.md")
OUTPUT_PATH = Path(r"prd_for_testcase/lang_resources_batch_insert.sql")

RU_TITLE_MAP = {
    "Doomsday × Ghost in the Shell": "Doomsday × Призрак в доспехах",
    "Mobile Legends: Bang Bang": "Mobile Legends: Bang Bang",
    "Standoff 2": "Standoff 2",
    "Last Day on Earth: Survival": "Последний день на Земле: Выживание",
    "Tiles Survive!": "Выживание на плитках!",
    "Grand Mobile- RP Open World": "Grand Mobile — RP Открытый мир",
    "Soul Knight": "Рыцарь души",
    "The Ants: Underground Kingdom": "Муравьи: Подземное королевство",
    "Game of Khans": "Игра ханов",
    "Evony: The King's Return": "Evony: Возвращение короля",
    "АФИНА: Кровные сестры": "АФИНА: Кровные сестры",
    "Her.AI - Funny Chat Friend": "Her.AI — Забавный друг для чата",
    "Слава легиона": "Слава легиона",
    "MoboReels": "MoboReels",
    "Gossip Harbor®: Merge & Story": "Gossip Harbor®: Слияние и история",
    "Comic AI-Anime Roleplay Chat": "Comic AI — аниме чат с ролевой игрой",
    "Kupid AI - Anime Roleplay Chat": "Kupid AI — аниме чат с ролевой игрой",
    "Luna Fantasy": "Luna Fantasy",
    "Honor of Kings": "Honor of Kings",
    "Viking Rise": "Viking Rise",
    "Zombie Waves": "Волны зомби",
    "Gods and Glory": "Боги и слава",
    "Klondike Adventures": "Приключения Клондайка",
    "Pixel Overlord: 4096 Draws": "Пиксельный повелитель: 4096 призывов",
    "MU: Dark Epoch": "MU: Тёмная эпоха",
    "Guns of Glory: Lost Island": "Guns of Glory: Затерянный остров",
    "Infinite Magicraid": "Infinite Magicraid",
    "War and Magic: Kingdom Reborn": "Война и магия: Возрождение королевства",
    "State of Survival - Mistore": "State of Survival - Mistore",
    "Legend of the Phoenix": "Легенда о Фениксе",
    "Mobile Legends: Adventure": "Mobile Legends: Приключение",
    "Zombie.io - Potato Shooting": "Zombie.io — Картофельная стрельба",
    "Demon Slayer 4: Ultra": "Истребитель демонов 4: Ультра",
    "Game of Sultans": "Игра султанов",
    "Vikingard": "Vikingard",
    "Z Day- Hearts of Heroes": "Z Day — Сердца героев",
    "Russian Topo Maps": "Топографические карты России",
    "Legacy of Discord-FuriousWings": "Наследие Discord: Яростные крылья",
    "Juice AI - Anime Friend Chat": "Juice AI — аниме чат с другом",
}


def sql_quote(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"


def parse_titles(text: str):
    titles = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("INSERT INTO"):
            continue
        if "\t" in line:
            title, _package_name = line.split("\t", 1)
            titles.append(title.strip())
    return titles


def to_russian_title(title: str) -> str:
    return RU_TITLE_MAP.get(title, title)


def build_sql_for_title(title: str) -> list[str]:
    ru_title = to_russian_title(title)
    return [
        f"-- {title}",
        "INSERT INTO `thorfast_config`.`tbl_lang_resources` "
        "(`pid`, `title`, `type`, `lang`, `create_staff_id`, `create_time`, `change_staff_id`, `change_time`, `delete_staff_id`, `delete_time`, `lang_type`) VALUES "
        f"(0, {sql_quote(title)}, 2, '', 289, NOW(), 0, NULL, 0, NULL, 1);",
        "SET @lang_pid = LAST_INSERT_ID();",
        "INSERT INTO `thorfast_config`.`tbl_lang_resources` "
        "(`pid`, `title`, `type`, `lang`, `create_staff_id`, `create_time`, `change_staff_id`, `change_time`, `delete_staff_id`, `delete_time`, `lang_type`) VALUES "
        f"(@lang_pid, {sql_quote(title)}, 2, 'zh_CN', 289, NOW(), 0, NULL, 0, NULL, 1);",
        "INSERT INTO `thorfast_config`.`tbl_lang_resources` "
        "(`pid`, `title`, `type`, `lang`, `create_staff_id`, `create_time`, `change_staff_id`, `change_time`, `delete_staff_id`, `delete_time`, `lang_type`) VALUES "
        f"(@lang_pid, {sql_quote(title)}, 2, 'zh_TW', 289, NOW(), 0, NULL, 0, NULL, 1);",
        "INSERT INTO `thorfast_config`.`tbl_lang_resources` "
        "(`pid`, `title`, `type`, `lang`, `create_staff_id`, `create_time`, `change_staff_id`, `change_time`, `delete_staff_id`, `delete_time`, `lang_type`) VALUES "
        f"(@lang_pid, {sql_quote(title)}, 2, 'en', 289, NOW(), 0, NULL, 0, NULL, 1);",
        "INSERT INTO `thorfast_config`.`tbl_lang_resources` "
        "(`pid`, `title`, `type`, `lang`, `create_staff_id`, `create_time`, `change_staff_id`, `change_time`, `delete_staff_id`, `delete_time`, `lang_type`) VALUES "
        f"(@lang_pid, {sql_quote(ru_title)}, 2, 'ru', 289, NOW(), 0, NULL, 0, NULL, 1);",
        "",
    ]


def main() -> None:
    text = SOURCE_PATH.read_text(encoding="utf-8")
    titles = parse_titles(text)

    sql_lines = [
        "-- Auto generated multi-language insert SQL for tbl_lang_resources",
        "SET NAMES utf8mb4;",
        "",
    ]

    for title in titles:
        sql_lines.extend(build_sql_for_title(title))

    OUTPUT_PATH.write_text("\n".join(sql_lines).strip() + "\n", encoding="utf-8")
    print(f"Generated: {OUTPUT_PATH}")
    print(f"Generated title count: {len(titles)}")


if __name__ == "__main__":
    main()