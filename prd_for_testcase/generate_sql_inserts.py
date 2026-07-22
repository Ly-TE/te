from pathlib import Path


SOURCE_PATH = Path(r"prd_for_testcase/sql.md")
OUTPUT_PATH = Path(r"prd_for_testcase/sql_batch_insert.sql")

def sql_quote(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"


def build_tbl_game_sql(title: str, package_name: str) -> str:
    return (
        "INSERT INTO `thorfast_config`.`tbl_game` "
        "(`title`, `keywords`, `game_info`, `game_background`, `game_background_url`, `game_background_large_url`, `game_pic`, `game_pic_url`, `game_cover_image`, `game_type`, `game_h1_title`, `game_new_pc_rules`, `game_ss_rules`, `game_ios_rules`, `game_host_rules`, `game_mac_rules`, `game_vpn_rules`, `game_android_rules`, `game_new_host_rules`, `is_support_windows`, `is_support_ios`, `is_support_android`, `is_support_mac`, `is_support_host_game`, `create_time`, `change_time`, `create_staff_id`, `change_staff_id`, `is_valid`, `is_config_id`, `is_hot`, `client_launch_config`, `bandwidth`, `android_package_name`, `android_dns_model`, `sort_num`, `is_free`, `free_include_region_codes`, `free_exclude_region_codes`, `free_datetime`, `is_video`, `include_region_codes`, `exclude_region_codes`, `country_code`, `vpn_prefix_route`, `vpn_process_rule`, `ios_appid`, `bundle_id`, `acc_succ_hint`, `is_perset`, `ios_scheme`, `download_game_url`, `mac_app_id`, `is_hide_bandwidth`, `is_download_game`, `game_category`, `game_label`, `android_package_dependence`, `is_new`, `platform_id`, `publish_time`, `is_ban_ip`, `game_mac_rules_v10`, `line_pic`, `game_report_image`, `is_free_v1`, `charge_area`, `charge_area_city`, `game_title_lang_id`, `is_support_chrome`) VALUES "
        f"({sql_quote(title)}, {sql_quote(title)}, {sql_quote(title)}, NULL, NULL, '', NULL, '/thorfast/images/2026-06-25/1782374782806754.jpeg', '/thorfast/images/2026-06-25/1782374780749331.jpeg', 1, '', '', '', '', '', '', '', '', '', 0, 0, 0, NULL, NULL, '2026-06-25 16:06:25', NULL, 289, NULL, 1, 0, 0, NULL, NULL, {sql_quote(package_name)}, 0, 5000, 0, '', '', NULL, 0, ',1,', '', NULL, NULL, NULL, '', '', NULL, 1, NULL, '', NULL, 0, 0, 0, NULL, '', 0, NULL, NULL, 0, '', '', '', 0, NULL, NULL, 'lang_24340', 0);"
    )


def build_tbl_game_info_v11_sql(title: str) -> str:
    return (
        "INSERT INTO `thorfast_config`.`tbl_game_info_v11` "
        "(`game_id`, `game_cate_id`, `platform_id`, `game_title_v11`, `game_info_v11`, `is_show_v11`, `is_top`, `is_close`, `client_launch_config_v11`, `is_show_new_v11`, `help_news_url`, `download_game_id`, `download_game_url`, `is_show_download_btn`, `button_text`, `is_support_xiaomi`) VALUES "
        f"(@game_id, 0, '0', {sql_quote(title)}, {sql_quote(title)}, 1, 0, 0, NULL, 1, '', 0, '', 1, NULL, 1);"
    )


def build_tbl_game_info_sql(title: str, package_name: str) -> str:
    return (
        "INSERT INTO `thorfast_config`.`tbl_game_info` "
        "(`game_id`, `parent_game_id`, `game_cate_id`, `platform_id`, `is_chinesize`, `game_title_v10`, `game_info_v10`, `is_show_v10`, `process_name`, `game_window_name`, `game_window_cate_name`, `game_news_keyword`, `is_support_rear_speed`, `is_top`, `is_udp_ping`, `before_speed_hint`, `platform_process`, `game_process`, `game_info_type`, `plat_game_id`, `download_game_id`, `game_install_catalogue`, `game_registry_path`, `archive_path`, `platform_app_id`, `game_plat_game_id`, `game_download_site`, `is_record_speed_ip`, `probe_rules`, `is_speed_update`, `bind_down_game_id`, `cloud_game_id`, `cloud_game_pic`, `cloud_game_pic_v11`, `is_copy_mode_ten`, `is_copy_mode_nine`, `is_go_home`, `android_version`, `android_version_name`, `android_package_name`, `download_game_url`, `ios_appid`, `bundle_id`, `is_search`, `android_extend_package_name`, `speed_mode`, `is_low_free`) VALUES "
        f"(@game_id, 0, 0, 0, 0, {sql_quote(title)}, {sql_quote(title)}, 1, NULL, NULL, NULL, '', 0, 0, 0, NULL, '', '', 0, '', 0, '', '', '', '', '', '', 0, NULL, 0, 0, 0, NULL, NULL, 0, 0, 0, NULL, NULL, {sql_quote(package_name)}, NULL, NULL, NULL, 0, NULL, 1, 1);"
    )


def parse_source(text: str):
    lines = [line.strip() for line in text.splitlines()]
    seed_sql = [line for line in lines if line.startswith("INSERT INTO")]
    data_lines = []
    for line in lines:
        if not line or line.startswith("INSERT INTO"):
            continue
        if "\t" in line:
            title, package_name = line.split("\t", 1)
            data_lines.append((title.strip(), package_name.strip()))
    return seed_sql, data_lines


def main() -> None:
    text = SOURCE_PATH.read_text(encoding="utf-8")
    seed_sql, pairs = parse_source(text)

    sql_blocks = [
        "-- Auto generated from prd_for_testcase/sql.md",
        "SET NAMES utf8mb4;",
        "",
        "-- Note: original seed INSERT statements in sql.md are not included here to avoid duplicate primary keys.",
        f"-- Original seed SQL count in source: {len(seed_sql)}",
        "-- Batch insert SQL generated from the title/package list below",
    ]

    for index, (title, package_name) in enumerate(pairs, start=1):
        sql_blocks.extend(
            [
                f"-- {index:02d}. {title} / {package_name}",
                build_tbl_game_sql(title, package_name),
                "SET @game_id = LAST_INSERT_ID();",
                build_tbl_game_info_v11_sql(title),
                build_tbl_game_info_sql(title, package_name),
                "",
            ]
        )

    OUTPUT_PATH.write_text("\n".join(sql_blocks).strip() + "\n", encoding="utf-8")
    print(f"Generated: {OUTPUT_PATH}")
    print(f"Seed SQL count: {len(seed_sql)}")
    print(f"Generated game rows: {len(pairs)}")


if __name__ == "__main__":
    main()