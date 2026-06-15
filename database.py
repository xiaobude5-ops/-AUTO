"""SQLite 数据库层 — 建表 + 全部 CRUD 操作"""
import sqlite3
from datetime import datetime
from config import DB_PATH


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


# ── 建表（幂等） ──
def init_db() -> None:
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        username      TEXT    NOT NULL UNIQUE,
        password_hash TEXT    NOT NULL,
        role          TEXT    NOT NULL DEFAULT 'employee',
        nickname      TEXT    NOT NULL,
        created_at    TEXT    DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS submissions (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        aweme_id       TEXT    NOT NULL,
        video_url      TEXT    NOT NULL,
        category       TEXT    NOT NULL,
        payment_amount REAL    DEFAULT NULL,
        submitted_at   TEXT    DEFAULT (datetime('now','localtime')),
        UNIQUE(user_id, aweme_id)
    );
    CREATE INDEX IF NOT EXISTS idx_sub_user ON submissions(user_id);
    CREATE INDEX IF NOT EXISTS idx_sub_cat ON submissions(category);
    CREATE INDEX IF NOT EXISTS idx_sub_date ON submissions(submitted_at);

    CREATE TABLE IF NOT EXISTS submission_collaborators (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        submission_id INTEGER NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
        user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE(submission_id, user_id)
    );
    CREATE INDEX IF NOT EXISTS idx_sc_sub ON submission_collaborators(submission_id);
    CREATE INDEX IF NOT EXISTS idx_sc_user ON submission_collaborators(user_id);

    CREATE TABLE IF NOT EXISTS video_snapshots (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        submission_id INTEGER NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
        likes         INTEGER DEFAULT 0,
        comments      INTEGER DEFAULT 0,
        shares        INTEGER DEFAULT 0,
        collects      INTEGER DEFAULT 0,
        scraped_at    TEXT    NOT NULL,
        UNIQUE(submission_id, scraped_at)
    );
    CREATE INDEX IF NOT EXISTS idx_vs_sub_date ON video_snapshots(submission_id, scraped_at);
    """)
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════
# User CRUD
# ═══════════════════════════════════════════

def create_user(username: str, password_hash: str, nickname: str, role: str = "employee") -> int | None:
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO users (username, password_hash, nickname, role) VALUES (?,?,?,?)",
            (username, password_hash, nickname, role),
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_user_by_username(username: str) -> dict | None:
    conn = get_conn()
    r = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    return dict(r) if r else None


def get_user_by_id(user_id: int) -> dict | None:
    conn = get_conn()
    r = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return dict(r) if r else None


def get_all_users() -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, username, nickname, role, created_at FROM users ORDER BY created_at ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_employees() -> list[dict]:
    """获取所有非终端管理员用户（给协作人员下拉用）"""
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, username, nickname FROM users WHERE username != 'admin' ORDER BY nickname ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_user_role(user_id: int, role: str) -> bool:
    conn = get_conn()
    conn.execute("UPDATE users SET role=? WHERE id=?", (role, user_id))
    conn.commit()
    conn.close()
    return True

def update_user_password(user_id: int, new_password_hash: str) -> bool:
    conn = get_conn()
    conn.execute("UPDATE users SET password_hash=? WHERE id=?", (new_password_hash, user_id))
    conn.commit()
    conn.close()
    return True


# ═══════════════════════════════════════════
# Submission CRUD
# ═══════════════════════════════════════════

def add_submission(user_id: int, aweme_id: str, video_url: str, category: str,
                    collaborator_ids: list[int] | None = None) -> int | None:
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO submissions (user_id, aweme_id, video_url, category) VALUES (?,?,?,?)",
            (user_id, aweme_id, video_url, category),
        )
        conn.commit()
        sid = cur.lastrowid
        if collaborator_ids:
            for cid in collaborator_ids:
                conn.execute(
                    "INSERT OR IGNORE INTO submission_collaborators (submission_id, user_id) VALUES (?,?)",
                    (sid, cid),
                )
            conn.commit()
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()
    return sid


def save_video_snapshot(submission_id: int, likes: int, comments: int,
                        shares: int, collects: int) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_conn()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO video_snapshots (submission_id,likes,comments,shares,collects,scraped_at) "
            "VALUES (?,?,?,?,?,?)",
            (submission_id, likes, comments, shares, collects, now),
        )
        conn.commit()
    finally:
        conn.close()


def get_submissions_by_user(user_id: int) -> list[dict]:
    """员工看自己的提交历史（含最新互动 + 协作人员）"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT s.*,
            vs.likes, vs.comments, vs.shares, vs.collects, vs.scraped_at AS last_scraped
        FROM submissions s
        LEFT JOIN (
            SELECT submission_id, likes, comments, shares, collects, scraped_at
            FROM video_snapshots
            WHERE id IN (SELECT MAX(id) FROM video_snapshots GROUP BY submission_id)
        ) vs ON vs.submission_id = s.id
        WHERE s.user_id = ?
        ORDER BY s.submitted_at DESC
    """, (user_id,)).fetchall()
    results = _attach_collaborators(conn, rows)
    conn.close()
    return results


def _attach_collaborators(conn, rows) -> list[dict]:
    """给结果附加协作人员信息"""
    results = []
    for r in rows:
        d = dict(r)
        subs = conn.execute(
            "SELECT u.id, u.nickname FROM submission_collaborators sc "
            "JOIN users u ON u.id=sc.user_id WHERE sc.submission_id=?",
            (d["id"],),
        ).fetchall()
        d["collaborators"] = [dict(c) for c in subs]
        results.append(d)
    return results


def get_submissions_filtered(user_ids: list[int] | None = None,
                             category: str | None = None,
                             date_from: str | None = None,
                             date_to: str | None = None,
                             engagement_min: int = 0,
                             payment_min: float | None = None,
                             payment_max: float | None = None,
                             page: int = 1, per_page: int = 50) -> tuple[list[dict], int]:
    """管理员筛选查询（带分页）"""
    conn = get_conn()
    where = ["1=1"]
    params: list = []

    if user_ids:
        placeholders = ",".join("?" * len(user_ids))
        where.append(f"s.user_id IN ({placeholders})")
        params.extend(user_ids)
    if category:
        where.append("s.category = ?")
        params.append(category)
    if date_from:
        where.append("s.submitted_at >= ?")
        params.append(date_from)
    if date_to:
        where.append("s.submitted_at <= ?")
        params.append(date_to + " 23:59:59")
    if payment_min is not None:
        where.append("COALESCE(s.payment_amount,0) >= ?")
        params.append(payment_min)
    if payment_max is not None:
        where.append("COALESCE(s.payment_amount,0) <= ?")
        params.append(payment_max)

    where_clause = " AND ".join(where)

    # 总数
    count_row = conn.execute(
        f"SELECT COUNT(*) AS cnt FROM submissions s WHERE {where_clause}", params
    ).fetchone()
    total = count_row["cnt"] if count_row else 0

    # 列表
    offset = (page - 1) * per_page
    rows = conn.execute(f"""
        SELECT s.*, u.nickname AS submitter_name,
            vs.likes, vs.comments, vs.shares, vs.collects,
            COALESCE(vs.likes,0)+COALESCE(vs.comments,0)+COALESCE(vs.shares,0)+COALESCE(vs.collects,0) AS total_engagement,
            vs.scraped_at AS last_scraped
        FROM submissions s
        JOIN users u ON u.id = s.user_id
        LEFT JOIN (
            SELECT submission_id, likes, comments, shares, collects, scraped_at
            FROM video_snapshots
            WHERE id IN (SELECT MAX(id) FROM video_snapshots GROUP BY submission_id)
        ) vs ON vs.submission_id = s.id
        WHERE {where_clause}
        ORDER BY s.submitted_at DESC
        LIMIT ? OFFSET ?
    """, params + [per_page, offset]).fetchall()

    # 互动量过滤（SQL 不能直接用别名）
    filtered_rows = []
    for r in rows:
        d = dict(r)
        eng = (d.get("likes") or 0) + (d.get("comments") or 0) + \
              (d.get("shares") or 0) + (d.get("collects") or 0)
        if eng >= engagement_min:
            d["total_engagement"] = eng
            filtered_rows.append(d)

    # 附加协作人员
    final_rows = _attach_collaborators(conn, filtered_rows)
    conn.close()
    return final_rows, total


def update_payment(submission_id: int, amount: float | None) -> None:
    conn = get_conn()
    conn.execute("UPDATE submissions SET payment_amount=? WHERE id=?", (amount, submission_id))
    conn.commit()
    conn.close()


def delete_submission(submission_id: int) -> bool:
    """删除一条提交（联动删除快照与协作人 — 由外键 ON DELETE CASCADE 处理）"""
    conn = get_conn()
    try:
        cur = conn.execute("DELETE FROM submissions WHERE id=?", (submission_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()

def delete_user(user_id: int) -> bool:
    """删除用户（联动删除其提交、快照、协作关系 — 由外键 ON DELETE CASCADE 处理）"""
    conn = get_conn()
    try:
        cur = conn.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def update_submission_meta(submission_id: int, category: str | None = None,
                           submitted_at: str | None = None) -> bool:
    """更新提交的分类和/或提交日期"""
    conn = get_conn()
    cur = None
    if category and submitted_at:
        cur = conn.execute(
            "UPDATE submissions SET category=?, submitted_at=? WHERE id=?",
            (category, submitted_at, submission_id),
        )
    elif category:
        cur = conn.execute(
            "UPDATE submissions SET category=? WHERE id=?", (category, submission_id),
        )
    elif submitted_at:
        cur = conn.execute(
            "UPDATE submissions SET submitted_at=? WHERE id=?", (submitted_at, submission_id),
        )
    conn.commit()
    ok = cur is not None and cur.rowcount > 0
    conn.close()
    return ok


def get_submission(submission_id: int) -> dict | None:
    conn = get_conn()
    r = conn.execute("""
        SELECT s.*, u.nickname AS submitter_name
        FROM submissions s JOIN users u ON u.id=s.user_id
        WHERE s.id=?
    """, (submission_id,)).fetchone()
    if r:
        d = dict(r)
        subs = conn.execute(
            "SELECT u.id, u.nickname FROM submission_collaborators sc "
            "JOIN users u ON u.id=sc.user_id WHERE sc.submission_id=?",
            (d["id"],),
        ).fetchall()
        d["collaborators"] = [dict(c) for c in subs]
        conn.close()
        return d
    conn.close()
    return None


# ═══════════════════════════════════════════
# 每日变化
# ═══════════════════════════════════════════

def get_daily_changes_for_user(user_id: int) -> list[dict]:
    """单员工：自己视频的最新两次快照对比"""
    conn = get_conn()
    rows = conn.execute("""
        WITH ranked AS (
            SELECT submission_id, likes, comments, shares, collects, scraped_at,
                   ROW_NUMBER() OVER (PARTITION BY submission_id ORDER BY scraped_at DESC) AS rn
            FROM video_snapshots
            WHERE submission_id IN (SELECT id FROM submissions WHERE user_id = ?)
        )
        SELECT s.id AS submission_id, s.aweme_id, s.category,
               r1.likes AS cur_likes, r1.comments AS cur_comments,
               r1.shares AS cur_shares, r1.collects AS cur_collects,
               COALESCE(r2.likes, r1.likes) AS prev_likes,
               COALESCE(r2.comments, r1.comments) AS prev_comments,
               COALESCE(r2.shares, r1.shares) AS prev_shares,
               COALESCE(r2.collects, r1.collects) AS prev_collects
        FROM submissions s
        JOIN ranked r1 ON r1.submission_id = s.id AND r1.rn = 1
        LEFT JOIN ranked r2 ON r2.submission_id = s.id AND r2.rn = 2
        WHERE s.user_id = ?
        ORDER BY s.submitted_at DESC
    """, (user_id, user_id)).fetchall()

    results = []
    for r in rows:
        r = dict(r)
        likes_delta = (r["cur_likes"] or 0) - (r["prev_likes"] or 0)
        comments_delta = (r["cur_comments"] or 0) - (r["prev_comments"] or 0)
        shares_delta = (r["cur_shares"] or 0) - (r["prev_shares"] or 0)
        collects_delta = (r["cur_collects"] or 0) - (r["prev_collects"] or 0)
        total = likes_delta + comments_delta + shares_delta + collects_delta
        if total != 0:
            results.append({
                "submission_id": r["submission_id"],
                "aweme_id": r["aweme_id"],
                "category": r["category"],
                "likes_change": likes_delta,
                "comments_change": comments_delta,
                "shares_change": shares_delta,
                "collects_change": collects_delta,
                "total_change": total,
            })
    conn.close()
    return results


# ═══════════════════════════════════════════
# 月度汇总
# ═══════════════════════════════════════════

def get_admin_monthly_summary(year: int, month: int) -> list[dict]:
    """管理员：按员工 + 分类的月度交叉汇总"""
    from utils import get_month_boundaries
    start, end = get_month_boundaries(year, month)
    sd, ed = start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

    conn = get_conn()
    rows = conn.execute("""
        SELECT s.user_id, u.nickname, s.category,
               COUNT(*) AS count,
               COALESCE(SUM(vs.likes),0) AS total_likes,
               COALESCE(SUM(vs.comments),0) AS total_comments,
               COALESCE(SUM(vs.shares),0) AS total_shares,
               COALESCE(SUM(vs.collects),0) AS total_collects,
               COALESCE(SUM(s.payment_amount),0) AS total_payment
        FROM submissions s
        JOIN users u ON u.id = s.user_id
        LEFT JOIN (
            SELECT submission_id, likes, comments, shares, collects
            FROM video_snapshots
            WHERE id IN (SELECT MAX(id) FROM video_snapshots GROUP BY submission_id)
        ) vs ON vs.submission_id = s.id
        WHERE s.submitted_at >= ? AND s.submitted_at <= ?
        GROUP BY s.user_id, s.category
        ORDER BY u.nickname, s.category
    """, (sd, ed + " 23:59:59")).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════
# 全局刷新
# ═══════════════════════════════════════════

def get_all_submission_aweme_ids() -> list[dict]:
    """获取所有提交的 aweme_id 列表（用于每日刷新）"""
    conn = get_conn()
    rows = conn.execute("SELECT id, aweme_id FROM submissions").fetchall()
    conn.close()
    return [dict(r) for r in rows]
