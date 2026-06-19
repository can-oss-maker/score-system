"""
游戏角色管理系统 - Streamlit Web 应用
TiDB Cloud 云端部署版
支持 st.secrets（Streamlit Cloud）/ 环境变量 / 默认值 三级配置
"""

import streamlit as st
import pymysql
import pandas as pd
import os

# ============================================================
# TiDB Cloud 数据库配置
# 优先级：st.secrets > 环境变量 > 默认值
#
# ┌─────────────────────┬──────────────────────┬──────────────────────┐
# │ 场景                │ 配置方式              │ 使用的 TiDB          │
# ├─────────────────────┼──────────────────────┼──────────────────────┤
# │ 本地（不做任何设置）  │ 走默认值              │ TiDB A（默认）        │
# │ 本地临时切换         │ 设环境变量             │ 任意 TiDB            │
# │ Streamlit Cloud      │ App Settings→Secrets  │ 任意 TiDB            │
# └─────────────────────┴──────────────────────┴──────────────────────┘
#
# Streamlit Cloud Secrets 示例（在 App Settings → Secrets 粘贴）：
#   TIDB_HOST = "gateway01.ap-northeast-1.prod.aws.tidbcloud.com"
#   TIDB_USER = "4St8sEfasa8nHKP.root"
#   TIDB_PASSWORD = "BmMEYLCoMTtnoc53"
#   TIDB_DATABASE = "score_system"
# ============================================================

def _cfg(key, default):
    """读取配置：st.secrets → 环境变量 → 默认值"""
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, default)


DB_CONFIG = {
    "host": _cfg("TIDB_HOST", "gateway01.ap-northeast-1.prod.aws.tidbcloud.com"),
    "port": int(_cfg("TIDB_PORT", "4000")),
    "user": _cfg("TIDB_USER", "2brjp82BnLhgU4V.root"),
    "password": _cfg("TIDB_PASSWORD", "gMF0RVozQGZ5TcGX"),
    "database": _cfg("TIDB_DATABASE", "test"),
    "charset": "utf8mb4",
    "ssl": {"ssl": True},
    "autocommit": True,
}


def get_connection():
    """获取 TiDB Cloud 数据库连接"""
    return pymysql.connect(**DB_CONFIG)


def get_db_label():
    """返回当前使用的数据库标识"""
    user = DB_CONFIG["user"]
    db = DB_CONFIG["database"]
    if "2brjp82" in user:
        return f"TiDB A ({db})"
    else:
        return f"TiDB B ({db})"


def init_database():
    """初始化数据库表结构和示例数据"""
    conn = get_connection()
    cursor = conn.cursor()

    # 建表
    tables_sql = [
        """CREATE TABLE IF NOT EXISTS `characters` (
            `character_id`   BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
            `character_name` VARCHAR(64)      NOT NULL,
            `level`          INT UNSIGNED     NOT NULL DEFAULT 1,
            `hp`             INT UNSIGNED     NOT NULL DEFAULT 100,
            `attack`         INT UNSIGNED     NOT NULL DEFAULT 10,
            `defense`        INT UNSIGNED     NOT NULL DEFAULT 5,
            `total_power`    INT UNSIGNED     NOT NULL DEFAULT 0,
            `created_at`     DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (`character_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",

        """CREATE TABLE IF NOT EXISTS `equipment` (
            `equipment_id`   BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
            `equipment_name` VARCHAR(64)      NOT NULL,
            `equipment_type` VARCHAR(32)      NOT NULL,
            `attack_bonus`   INT UNSIGNED     NOT NULL DEFAULT 0,
            `defense_bonus`  INT UNSIGNED     NOT NULL DEFAULT 0,
            `quality`        VARCHAR(16)      NOT NULL DEFAULT '普通',
            PRIMARY KEY (`equipment_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",

        """CREATE TABLE IF NOT EXISTS `skills` (
            `skill_id`       BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
            `skill_name`     VARCHAR(64)      NOT NULL,
            `skill_damage`   INT UNSIGNED     NOT NULL DEFAULT 0,
            `skill_type`     VARCHAR(32)      NOT NULL,
            `cooldown`       INT UNSIGNED     NOT NULL DEFAULT 0,
            PRIMARY KEY (`skill_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",

        """CREATE TABLE IF NOT EXISTS `character_equipment` (
            `id`            BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
            `character_id`  BIGINT UNSIGNED  NOT NULL,
            `equipment_id`  BIGINT UNSIGNED  NOT NULL,
            `status`        TINYINT UNSIGNED NOT NULL DEFAULT 1,
            `equipped_at`   DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (`id`),
            UNIQUE KEY `uk_equipment_status` (`equipment_id`, `status`),
            KEY `idx_character_id` (`character_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",

        """CREATE TABLE IF NOT EXISTS `character_skill` (
            `id`            BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
            `character_id`  BIGINT UNSIGNED  NOT NULL,
            `skill_id`      BIGINT UNSIGNED  NOT NULL,
            `learned_at`    DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (`id`),
            UNIQUE KEY `uk_char_skill` (`character_id`, `skill_id`),
            KEY `idx_skill_id` (`skill_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    ]

    for sql in tables_sql:
        cursor.execute(sql)

    conn.commit()

    # 检查是否需要插入示例数据
    cursor.execute("SELECT COUNT(*) FROM characters")
    if cursor.fetchone()[0] == 0:
        sample_data = [
            "INSERT IGNORE INTO `characters` (`character_id`, `character_name`, `level`, `hp`, `attack`, `defense`) VALUES (1,'亚瑟',15,3500,180,120),(2,'冰霜女巫',12,2200,320,80),(3,'暗影刺客',18,1800,450,60),(4,'圣光骑士',20,5000,200,250),(5,'森林游侠',10,1600,250,90),(6,'烈焰法师',14,2000,380,70)",
            "INSERT IGNORE INTO `equipment` (`equipment_id`, `equipment_name`, `equipment_type`, `attack_bonus`, `defense_bonus`, `quality`) VALUES (1,'烈焰之剑','武器',150,0,'传说'),(2,'寒冰法杖','武器',200,0,'史诗'),(3,'暗影匕首','武器',180,0,'史诗'),(4,'圣盾铠甲','防具',0,120,'传说'),(5,'龙鳞护甲','防具',0,80,'稀有'),(6,'力量戒指','饰品',50,30,'稀有'),(7,'风暴之弓','武器',160,0,'传说')",
            "INSERT IGNORE INTO `skills` (`skill_id`, `skill_name`, `skill_damage`, `skill_type`, `cooldown`) VALUES (1,'旋风斩',300,'物理',8),(2,'暴风雪',450,'魔法',12),(3,'致命一击',600,'物理',15),(4,'神圣之光',200,'治疗',20),(5,'多重射击',250,'物理',6),(6,'火焰风暴',500,'魔法',14),(7,'暗影步',350,'物理',10)",
            "INSERT IGNORE INTO `character_equipment` (`character_id`, `equipment_id`, `status`) VALUES (1,1,1),(1,5,1),(2,2,1),(3,3,1),(4,4,1),(4,6,1),(5,7,1)",
            "INSERT IGNORE INTO `character_skill` (`character_id`, `skill_id`) VALUES (1,1),(1,7),(2,2),(3,3),(3,7),(4,4),(5,5),(6,6)",
        ]
        for sql in sample_data:
            cursor.execute(sql)
        conn.commit()

        # 计算战力
        cursor.execute("""
            UPDATE `characters` c
            SET `total_power` = (
                SELECT COALESCE(SUM(sub.base_power), 0)
                FROM (
                    SELECT (c2.attack + c2.defense) AS base_power
                    FROM `characters` c2 WHERE c2.character_id = c.character_id
                    UNION ALL
                    SELECT (e.attack_bonus + e.defense_bonus) AS base_power
                    FROM `character_equipment` ce
                    JOIN `equipment` e ON ce.equipment_id = e.equipment_id
                    WHERE ce.character_id = c.character_id AND ce.status = 1
                ) sub
            )
        """)
        conn.commit()
        st.success("示例数据已初始化！")
    else:
        st.info("数据库已有数据，跳过初始化。")

    cursor.close()
    conn.close()


def recalc_total_power():
    """重新计算所有角色总战力"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE `characters` c
        SET `total_power` = (
            COALESCE(c.attack, 0) + COALESCE(c.defense, 0) +
            COALESCE((
                SELECT SUM(e.attack_bonus + e.defense_bonus)
                FROM `character_equipment` ce
                JOIN `equipment` e ON ce.equipment_id = e.equipment_id
                WHERE ce.character_id = c.character_id AND ce.status = 1
            ), 0)
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()


# ============================================================
# Streamlit 页面配置
# ============================================================
st.set_page_config(
    page_title="游戏角色管理系统",
    page_icon="🎮",
    layout="wide",
)

st.title("🎮 游戏角色管理系统")
st.markdown("---")

# 侧边栏 - 导航
menu = st.sidebar.radio(
    "📋 功能导航",
    ["🏠 首页概览", "👤 角色管理", "⚔️ 装备管理", "✨ 技能管理", "🔗 角色装备关联", "📚 角色技能关联"],
)

# 侧边栏底部 - 数据库信息
st.sidebar.markdown("---")
st.sidebar.caption(f"数据库：{get_db_label()}")

if st.sidebar.button("🔄 初始化/重置数据库"):
    init_database()
    st.rerun() if hasattr(st, 'rerun') else st.experimental_rerun()


# ============================================================
# 首页概览
# ============================================================
if menu == "🏠 首页概览":
    col1, col2, col3, col4 = st.columns(4)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM characters")
    col1.metric("👤 角色总数", cursor.fetchone()[0])

    cursor.execute("SELECT COUNT(*) FROM equipment")
    col2.metric("⚔️ 装备总数", cursor.fetchone()[0])

    cursor.execute("SELECT COUNT(*) FROM skills")
    col3.metric("✨ 技能总数", cursor.fetchone()[0])

    cursor.execute("SELECT AVG(total_power) FROM characters")
    avg_power = cursor.fetchone()[0] or 0
    col4.metric("📊 平均战力", f"{int(avg_power)}")

    cursor.close()
    conn.close()

    st.markdown("---")

    # 战力排行
    st.subheader("🏆 角色战力排行")
    conn = get_connection()
    df_rank = pd.read_sql(
        "SELECT character_name AS 角色, level AS 等级, hp AS 生命值, "
        "attack AS 攻击, defense AS 防御, total_power AS 总战力 "
        "FROM characters ORDER BY total_power DESC",
        conn,
    )
    conn.close()

    if not df_rank.empty:
        st.dataframe(df_rank, use_container_width=True, hide_index=True)

        # 柱状图
        chart_data = df_rank.set_index("角色")["总战力"]
        st.bar_chart(chart_data, use_container_width=True)
    else:
        st.info("暂无角色数据，请先初始化数据库。")


# ============================================================
# 角色管理
# ============================================================
elif menu == "👤 角色管理":
    tab1, tab2 = st.tabs(["📋 角色列表", "➕ 添加角色"])

    with tab1:
        st.subheader("角色列表")

        # 搜索
        search = st.text_input("🔍 搜索角色名称", key="char_search")

        conn = get_connection()
        if search:
            df = pd.read_sql(
                "SELECT character_id, character_name, level, hp, attack, defense, total_power, created_at "
                "FROM characters WHERE character_name LIKE %s ORDER BY total_power DESC",
                conn,
                params=(f"%{search}%",),
            )
        else:
            df = pd.read_sql(
                "SELECT character_id, character_name, level, hp, attack, defense, total_power, created_at "
                "FROM characters ORDER BY total_power DESC",
                conn,
            )
        conn.close()

        if not df.empty:
            df.columns = ["ID", "角色名", "等级", "生命值", "攻击", "防御", "总战力", "创建时间"]
            st.dataframe(df, use_container_width=True, hide_index=True)

            # 编辑/删除
            st.markdown("---")
            st.subheader("✏️ 编辑角色")
            char_names = df["角色名"].tolist()
            selected_char = st.selectbox("选择要编辑的角色", char_names, key="edit_char")
            selected_id = df[df["角色名"] == selected_char]["ID"].values[0]

            col1, col2, col3, col4 = st.columns(4)
            new_name = col1.text_input("新名称", value=selected_char)
            new_level = col2.number_input("新等级", min_value=1, max_value=100,
                                          value=int(df[df["角色名"] == selected_char]["等级"].values[0]))
            new_hp = col3.number_input("新生命值", min_value=1, value=int(df[df["角色名"] == selected_char]["生命值"].values[0]))
            new_attack = col4.number_input("新攻击力", min_value=0, value=int(df[df["角色名"] == selected_char]["攻击"].values[0]))
            new_defense = st.number_input("新防御力", min_value=0, value=int(df[df["角色名"] == selected_char]["防御"].values[0]))

            col_btn1, col_btn2 = st.columns(2)
            if col_btn1.button("💾 保存修改", use_container_width=True):
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE characters SET character_name=%s, level=%s, hp=%s, attack=%s, defense=%s "
                    "WHERE character_id=%s",
                    (new_name, new_level, new_hp, new_attack, new_defense, int(selected_id)),
                )
                conn.commit()
                cursor.close()
                conn.close()
                recalc_total_power()
                st.success(f"角色「{new_name}」已更新！")
                st.rerun() if hasattr(st, 'rerun') else st.experimental_rerun()

            if col_btn2.button("🗑️ 删除角色", use_container_width=True):
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM characters WHERE character_id=%s", (int(selected_id),))
                conn.commit()
                cursor.close()
                conn.close()
                recalc_total_power()
                st.warning(f"角色「{selected_char}」已删除！")
                st.rerun() if hasattr(st, 'rerun') else st.experimental_rerun()
        else:
            st.info("暂无角色数据。")

    with tab2:
        st.subheader("添加新角色")
        with st.form("add_character_form"):
            col1, col2 = st.columns(2)
            name = col1.text_input("角色名称 *", placeholder="请输入角色名")
            level = col2.number_input("等级", min_value=1, max_value=100, value=1)
            col3, col4 = st.columns(2)
            hp = col3.number_input("生命值", min_value=1, value=100)
            attack = col4.number_input("攻击力", min_value=0, value=10)
            defense = st.number_input("防御力", min_value=0, value=5)

            submitted = st.form_submit_button("✅ 添加角色", use_container_width=True)
            if submitted:
                if not name.strip():
                    st.error("角色名称不能为空！")
                else:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO characters (character_name, level, hp, attack, defense) VALUES (%s, %s, %s, %s, %s)",
                        (name.strip(), level, hp, attack, defense),
                    )
                    conn.commit()
                    cursor.close()
                    conn.close()
                    recalc_total_power()
                    st.success(f"角色「{name}」添加成功！")
                    st.rerun() if hasattr(st, 'rerun') else st.experimental_rerun()


# ============================================================
# 装备管理
# ============================================================
elif menu == "⚔️ 装备管理":
    tab1, tab2 = st.tabs(["📋 装备列表", "➕ 添加装备"])

    with tab1:
        st.subheader("装备列表")

        conn = get_connection()
        df = pd.read_sql(
            "SELECT equipment_id, equipment_name, equipment_type, attack_bonus, defense_bonus, quality "
            "FROM equipment ORDER BY FIELD(quality,'传说','史诗','稀有','普通'), equipment_id",
            conn,
        )
        conn.close()

        if not df.empty:
            df.columns = ["ID", "装备名", "类型", "攻击加成", "防御加成", "品质"]
            st.dataframe(df, use_container_width=True, hide_index=True)

            # 品质分布图
            st.markdown("---")
            st.subheader("📊 装备品质分布")
            quality_counts = df["品质"].value_counts()
            st.bar_chart(quality_counts, use_container_width=True)

            # 删除装备
            st.markdown("---")
            st.subheader("🗑️ 删除装备")
            eq_names = df["装备名"].tolist()
            selected_eq = st.selectbox("选择要删除的装备", eq_names, key="del_equip")
            if st.button("确认删除装备", use_container_width=True):
                eq_id = df[df["装备名"] == selected_eq]["ID"].values[0]
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM equipment WHERE equipment_id=%s", (int(eq_id),))
                conn.commit()
                cursor.close()
                conn.close()
                recalc_total_power()
                st.warning(f"装备「{selected_eq}」已删除！")
                st.rerun() if hasattr(st, 'rerun') else st.experimental_rerun()
        else:
            st.info("暂无装备数据。")

    with tab2:
        st.subheader("添加新装备")
        with st.form("add_equipment_form"):
            col1, col2 = st.columns(2)
            name = col1.text_input("装备名称 *", placeholder="请输入装备名")
            eq_type = col2.selectbox("装备类型", ["武器", "防具", "饰品"])
            quality = st.selectbox("品质", ["普通", "稀有", "史诗", "传说"])
            col3, col4 = st.columns(2)
            attack_bonus = col3.number_input("攻击加成", min_value=0, value=0)
            defense_bonus = col4.number_input("防御加成", min_value=0, value=0)

            submitted = st.form_submit_button("✅ 添加装备", use_container_width=True)
            if submitted:
                if not name.strip():
                    st.error("装备名称不能为空！")
                else:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO equipment (equipment_name, equipment_type, attack_bonus, defense_bonus, quality) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (name.strip(), eq_type, attack_bonus, defense_bonus, quality),
                    )
                    conn.commit()
                    cursor.close()
                    conn.close()
                    st.success(f"装备「{name}」添加成功！")
                    st.rerun() if hasattr(st, 'rerun') else st.experimental_rerun()


# ============================================================
# 技能管理
# ============================================================
elif menu == "✨ 技能管理":
    tab1, tab2 = st.tabs(["📋 技能列表", "➕ 添加技能"])

    with tab1:
        st.subheader("技能列表")

        conn = get_connection()
        df = pd.read_sql(
            "SELECT skill_id, skill_name, skill_damage, skill_type, cooldown "
            "FROM skills ORDER BY skill_id",
            conn,
        )
        conn.close()

        if not df.empty:
            df.columns = ["ID", "技能名", "伤害", "类型", "冷却(秒)"]
            st.dataframe(df, use_container_width=True, hide_index=True)

            # 技能类型分布
            st.markdown("---")
            st.subheader("📊 技能类型分布")
            type_counts = df["类型"].value_counts()
            st.bar_chart(type_counts, use_container_width=True)

            # 删除技能
            st.markdown("---")
            st.subheader("🗑️ 删除技能")
            sk_names = df["技能名"].tolist()
            selected_sk = st.selectbox("选择要删除的技能", sk_names, key="del_skill")
            if st.button("确认删除技能", use_container_width=True):
                sk_id = df[df["技能名"] == selected_sk]["ID"].values[0]
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM skills WHERE skill_id=%s", (int(sk_id),))
                conn.commit()
                cursor.close()
                conn.close()
                st.warning(f"技能「{selected_sk}」已删除！")
                st.rerun() if hasattr(st, 'rerun') else st.experimental_rerun()
        else:
            st.info("暂无技能数据。")

    with tab2:
        st.subheader("添加新技能")
        with st.form("add_skill_form"):
            col1, col2 = st.columns(2)
            name = col1.text_input("技能名称 *", placeholder="请输入技能名")
            skill_type = col2.selectbox("技能类型", ["物理", "魔法", "治疗"])
            col3, col4 = st.columns(2)
            damage = col3.number_input("技能伤害", min_value=0, value=100)
            cooldown = col4.number_input("冷却时间(秒)", min_value=0, value=10)

            submitted = st.form_submit_button("✅ 添加技能", use_container_width=True)
            if submitted:
                if not name.strip():
                    st.error("技能名称不能为空！")
                else:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO skills (skill_name, skill_damage, skill_type, cooldown) VALUES (%s, %s, %s, %s)",
                        (name.strip(), damage, skill_type, cooldown),
                    )
                    conn.commit()
                    cursor.close()
                    conn.close()
                    st.success(f"技能「{name}」添加成功！")
                    st.rerun() if hasattr(st, 'rerun') else st.experimental_rerun()


# ============================================================
# 角色装备关联
# ============================================================
elif menu == "🔗 角色装备关联":
    st.subheader("角色装备关联管理")

    conn = get_connection()

    # 获取角色列表
    chars_df = pd.read_sql("SELECT character_id, character_name FROM characters", conn)
    equips_df = pd.read_sql("SELECT equipment_id, equipment_name, quality FROM equipment", conn)

    if chars_df.empty:
        st.warning("请先添加角色！")
    elif equips_df.empty:
        st.warning("请先添加装备！")
    else:
        # 显示当前关联
        st.markdown("### 📋 当前穿戴情况")
        rel_df = pd.read_sql("""
            SELECT c.character_name AS 角色, e.equipment_name AS 装备,
                   e.equipment_type AS 类型, e.quality AS 品质,
                   e.attack_bonus AS 攻击加成, e.defense_bonus AS 防御加成,
                   ce.equipped_at AS 穿戴时间
            FROM character_equipment ce
            JOIN characters c ON ce.character_id = c.character_id
            JOIN equipment e ON ce.equipment_id = e.equipment_id
            WHERE ce.status = 1
            ORDER BY c.character_name
        """, conn)

        if not rel_df.empty:
            st.dataframe(rel_df, use_container_width=True, hide_index=True)
        else:
            st.info("暂无装备穿戴记录。")

        st.markdown("---")

        # 穿戴装备
        st.markdown("### ⚔️ 穿戴装备")
        col1, col2 = st.columns(2)
        selected_char = col1.selectbox("选择角色", chars_df["character_name"].tolist(), key="wear_char")
        selected_equip = col2.selectbox("选择装备", equips_df["equipment_name"].tolist(), key="wear_equip")

        if st.button("🔧 穿戴装备", use_container_width=True):
            char_id = int(chars_df[chars_df["character_name"] == selected_char]["character_id"].values[0])
            equip_id = int(equips_df[equips_df["equipment_name"] == selected_equip]["equipment_id"].values[0])
            cursor = conn.cursor()
            try:
                # 先卸下该装备（如果有角色穿戴中）
                cursor.execute(
                    "UPDATE character_equipment SET status=0 WHERE equipment_id=%s AND status=1",
                    (equip_id,),
                )
                # 插入新穿戴记录
                cursor.execute(
                    "INSERT INTO character_equipment (character_id, equipment_id, status) VALUES (%s, %s, 1)",
                    (char_id, equip_id),
                )
                conn.commit()
                recalc_total_power()
                st.success(f"「{selected_char}」已装备「{selected_equip}」！")
                st.rerun() if hasattr(st, 'rerun') else st.experimental_rerun()
            except pymysql.err.IntegrityError:
                st.error("该角色已穿戴此装备！")
            finally:
                cursor.close()

        # 卸下装备
        if not rel_df.empty:
            st.markdown("### 🔓 卸下装备")
            selected_rel = st.selectbox(
                "选择要卸下的记录",
                [f"{r['角色']} → {r['装备']}" for _, r in rel_df.iterrows()],
                key="unequip",
            )
            if st.button("🔓 卸下装备", use_container_width=True):
                char_name = selected_rel.split(" → ")[0]
                equip_name = selected_rel.split(" → ")[1]
                char_id = int(chars_df[chars_df["character_name"] == char_name]["character_id"].values[0])
                equip_id = int(equips_df[equips_df["equipment_name"] == equip_name]["equipment_id"].values[0])
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE character_equipment SET status=0 WHERE character_id=%s AND equipment_id=%s AND status=1",
                    (char_id, equip_id),
                )
                conn.commit()
                cursor.close()
                recalc_total_power()
                st.success(f"「{char_name}」已卸下「{equip_name}」！")
                st.rerun() if hasattr(st, 'rerun') else st.experimental_rerun()

    conn.close()


# ============================================================
# 角色技能关联
# ============================================================
elif menu == "📚 角色技能关联":
    st.subheader("角色技能关联管理")

    conn = get_connection()

    chars_df = pd.read_sql("SELECT character_id, character_name FROM characters", conn)
    skills_df = pd.read_sql("SELECT skill_id, skill_name, skill_type, skill_damage FROM skills", conn)

    if chars_df.empty:
        st.warning("请先添加角色！")
    elif skills_df.empty:
        st.warning("请先添加技能！")
    else:
        # 显示当前关联
        st.markdown("### 📋 当前已学技能")
        rel_df = pd.read_sql("""
            SELECT c.character_name AS 角色, s.skill_name AS 技能,
                   s.skill_type AS 类型, s.skill_damage AS 伤害,
                   s.cooldown AS 冷却秒, cs.learned_at AS 学习时间
            FROM character_skill cs
            JOIN characters c ON cs.character_id = c.character_id
            JOIN skills s ON cs.skill_id = s.skill_id
            ORDER BY c.character_name
        """, conn)

        if not rel_df.empty:
            st.dataframe(rel_df, use_container_width=True, hide_index=True)
        else:
            st.info("暂无技能学习记录。")

        st.markdown("---")

        # 学习技能
        st.markdown("### 📖 学习技能")
        col1, col2 = st.columns(2)
        selected_char = col1.selectbox("选择角色", chars_df["character_name"].tolist(), key="learn_char")
        selected_skill = col2.selectbox("选择技能", skills_df["skill_name"].tolist(), key="learn_skill")

        if st.button("📖 学习技能", use_container_width=True):
            char_id = int(chars_df[chars_df["character_name"] == selected_char]["character_id"].values[0])
            skill_id = int(skills_df[skills_df["skill_name"] == selected_skill]["skill_id"].values[0])
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO character_skill (character_id, skill_id) VALUES (%s, %s)",
                    (char_id, skill_id),
                )
                conn.commit()
                st.success(f"「{selected_char}」学会了「{selected_skill}」！")
                st.rerun() if hasattr(st, 'rerun') else st.experimental_rerun()
            except pymysql.err.IntegrityError:
                st.error("该角色已学会此技能！")
            finally:
                cursor.close()

        # 遗忘技能
        if not rel_df.empty:
            st.markdown("### 🗑️ 遗忘技能")
            selected_rel = st.selectbox(
                "选择要遗忘的记录",
                [f"{r['角色']} → {r['技能']}" for _, r in rel_df.iterrows()],
                key="forget",
            )
            if st.button("🗑️ 遗忘技能", use_container_width=True):
                char_name = selected_rel.split(" → ")[0]
                skill_name = selected_rel.split(" → ")[1]
                char_id = int(chars_df[chars_df["character_name"] == char_name]["character_id"].values[0])
                skill_id = int(skills_df[skills_df["skill_name"] == skill_name]["skill_id"].values[0])
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM character_skill WHERE character_id=%s AND skill_id=%s",
                    (char_id, skill_id),
                )
                conn.commit()
                cursor.close()
                st.success(f"「{char_name}」遗忘了「{skill_name}」！")
                st.rerun() if hasattr(st, 'rerun') else st.experimental_rerun()

    conn.close()


# ============================================================
# 页脚
# ============================================================
st.markdown("---")
st.caption(
    f"🎮 游戏角色管理系统 | 数据库：TiDB Cloud ({get_db_label()}) | "
    "Powered by Streamlit + PyMySQL"
)
