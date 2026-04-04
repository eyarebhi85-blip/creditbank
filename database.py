"""
database.py — MySQL version for EasyPHP 1.8
============================================
EasyPHP 1.8 specs:
  - MySQL  : 4.x  (old protocol, no auth plugin)
  - Host   : localhost
  - Port   : 3306
  - User   : root
  - Password: (empty — no password in EasyPHP 1.8)
  - phpMyAdmin URL: http://localhost/mysql/

Driver used: PyMySQL  →  pip install pymysql
PyMySQL works perfectly with MySQL 4.x / EasyPHP 1.8.
"""

import pymysql
import pymysql.cursors
import hashlib
import datetime
import uuid
from contextlib import contextmanager

# ═══════════════════════════════════════════════════════════════════
#  ⚙️  CONNECTION CONFIG  — EasyPHP 1.8 defaults
#  !! Only change "database" if you used a different name !!
# ═══════════════════════════════════════════════════════════════════
DB_CONFIG = {
    "host":       "localhost",
    "port":       3306,           # EasyPHP 1.8 always uses 3306
    "user":       "root",         # EasyPHP 1.8 default user
    "password":   "",             # EasyPHP 1.8 has NO password
    "database":   "loan_app_db",  # must match what you create in phpMyAdmin
    "charset":    "latin1",       # EasyPHP 1.8 / MySQL 4.x uses latin1
    "cursorclass": pymysql.cursors.DictCursor,
}


# ───────────────────────────────────────────────────────────────────
def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


@contextmanager
def _conn():
    """Open a connection, commit on success, rollback + close always."""
    con = pymysql.connect(**DB_CONFIG)
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


# ═══════════════════════════════════════════════════════════════════
#  SCHEMA  (MySQL 4.x compatible — no foreign key enforcement needed)
# ═══════════════════════════════════════════════════════════════════
def init_db():
    with _conn() as con:
        with con.cursor() as cur:

            # ── USERS ────────────────────────────────────────────────────────
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id          VARCHAR(36)  NOT NULL,
                    username    VARCHAR(80)  NOT NULL,
                    password    VARCHAR(64)  NOT NULL,
                    full_name   VARCHAR(120) NOT NULL,
                    role        VARCHAR(20)  NOT NULL DEFAULT 'agent',
                    email       VARCHAR(120),
                    phone       VARCHAR(30),
                    department  VARCHAR(80),
                    created_at  DATETIME     NOT NULL,
                    is_active   TINYINT(1)   NOT NULL DEFAULT 1,
                    PRIMARY KEY (id),
                    UNIQUE KEY uq_username (username),
                    UNIQUE KEY uq_email    (email)
                ) ENGINE=MyISAM DEFAULT CHARSET=latin1
            """)
            # NOTE: EasyPHP 1.8 / MySQL 4.x uses MyISAM (no InnoDB by default)
            # MyISAM does NOT enforce FOREIGN KEYs — we handle integrity in Python

            # ── CLIENTS ──────────────────────────────────────────────────────
            cur.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id              VARCHAR(36)  NOT NULL,
                    client_id       VARCHAR(20)  NOT NULL,
                    email           VARCHAR(120) NOT NULL,
                    password        VARCHAR(64)  NOT NULL,
                    full_name       VARCHAR(120) NOT NULL,
                    phone           VARCHAR(30),
                    address         TEXT,
                    created_at      DATETIME     NOT NULL,
                    is_active       TINYINT(1)   NOT NULL DEFAULT 1,
                    assigned_agent  VARCHAR(36),
                    PRIMARY KEY (id),
                    UNIQUE KEY uq_client_id (client_id),
                    UNIQUE KEY uq_cl_email  (email)
                ) ENGINE=MyISAM DEFAULT CHARSET=latin1
            """)

            # ── LOAN APPLICATIONS ─────────────────────────────────────────────
            cur.execute("""
                CREATE TABLE IF NOT EXISTS loan_applications (
                    id                        VARCHAR(36)  NOT NULL,
                    client_id                 VARCHAR(36)  NOT NULL,
                    no_of_dependents          INT,
                    education                 VARCHAR(30),
                    self_employed             VARCHAR(10),
                    income_annum              DOUBLE,
                    loan_amount               DOUBLE,
                    loan_term                 INT,
                    cibil_score               INT,
                    residential_assets_value  DOUBLE,
                    commercial_assets_value   DOUBLE,
                    luxury_assets_value       DOUBLE,
                    bank_asset_value          DOUBLE,
                    prediction                VARCHAR(20),
                    probability               DOUBLE,
                    status                    VARCHAR(20)  DEFAULT 'Pending',
                    notes                     TEXT,
                    created_at                DATETIME,
                    reviewed_by               VARCHAR(120),
                    reviewed_at               DATETIME,
                    PRIMARY KEY (id),
                    KEY idx_client (client_id)
                ) ENGINE=MyISAM DEFAULT CHARSET=latin1
            """)

        # ── SEED: default admin ──────────────────────────────────────────────
        if not get_user_by_username("admin"):
            now = datetime.datetime.now()
            with con.cursor() as cur:
                cur.execute("""
                    INSERT INTO users
                    (id, username, password, full_name, role, email, created_at)
                    VALUES (%s, %s, %s, %s, 'admin', %s, %s)
                """, (str(uuid.uuid4()), "admin", _hash("Admin@1234"),
                      "System Administrator", "admin@loanapp.com", now))

        # ── SEED: demo agent ─────────────────────────────────────────────────
        if not get_user_by_username("agent1"):
            now = datetime.datetime.now()
            with con.cursor() as cur:
                cur.execute("""
                    INSERT INTO users
                    (id, username, password, full_name, role, email, department, created_at)
                    VALUES (%s, %s, %s, %s, 'agent', %s, %s, %s)
                """, (str(uuid.uuid4()), "agent1", _hash("Agent@1234"),
                      "Marie Dupont", "agent1@loanapp.com", "Credit Department", now))


# ═══════════════════════════════════════════════════════════════════
#  USERS
# ═══════════════════════════════════════════════════════════════════
def authenticate_user(username: str, password: str):
    with _conn() as con:
        with con.cursor() as cur:
            cur.execute(
                "SELECT * FROM users WHERE username=%s AND password=%s AND is_active=1",
                (username, _hash(password))
            )
            return cur.fetchone()   # DictCursor → dict or None


def get_user_by_username(username: str):
    with _conn() as con:
        with con.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username=%s", (username,))
            return cur.fetchone()


def get_all_users():
    with _conn() as con:
        with con.cursor() as cur:
            cur.execute("SELECT * FROM users ORDER BY created_at DESC")
            return cur.fetchall()


def add_user(username, password, full_name, role, email, phone="", department=""):
    uid = str(uuid.uuid4())
    now = datetime.datetime.now()
    with _conn() as con:
        with con.cursor() as cur:
            cur.execute("""
                INSERT INTO users
                (id, username, password, full_name, role, email, phone, department, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (uid, username, _hash(password), full_name, role,
                  email, phone, department, now))
    return uid


def update_user(uid, full_name, role, email, phone, department, is_active):
    with _conn() as con:
        with con.cursor() as cur:
            cur.execute("""
                UPDATE users
                SET full_name=%s, role=%s, email=%s, phone=%s,
                    department=%s, is_active=%s
                WHERE id=%s
            """, (full_name, role, email, phone, department, int(is_active), uid))


def delete_user(uid):
    with _conn() as con:
        with con.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id=%s", (uid,))


def reset_user_password(uid, new_password):
    with _conn() as con:
        with con.cursor() as cur:
            cur.execute("UPDATE users SET password=%s WHERE id=%s",
                        (_hash(new_password), uid))


# ═══════════════════════════════════════════════════════════════════
#  CLIENTS
# ═══════════════════════════════════════════════════════════════════
def authenticate_client(identifier: str, password: str):
    with _conn() as con:
        with con.cursor() as cur:
            cur.execute("""
                SELECT * FROM clients
                WHERE (email=%s OR client_id=%s)
                  AND password=%s
                  AND is_active=1
            """, (identifier, identifier, _hash(password)))
            return cur.fetchone()


def get_client_by_email(email: str):
    with _conn() as con:
        with con.cursor() as cur:
            cur.execute("SELECT * FROM clients WHERE email=%s", (email,))
            return cur.fetchone()


def get_client_by_id(cid: str):
    with _conn() as con:
        with con.cursor() as cur:
            cur.execute("SELECT * FROM clients WHERE id=%s", (cid,))
            return cur.fetchone()


def get_all_clients():
    with _conn() as con:
        with con.cursor() as cur:
            cur.execute("SELECT * FROM clients ORDER BY created_at DESC")
            return cur.fetchall()


def add_client(full_name, email, password, phone="", address="", assigned_agent=None):
    uid = str(uuid.uuid4())
    now = datetime.datetime.now()
    with _conn() as con:
        with con.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM clients")
            count = cur.fetchone()["cnt"]
            cid   = "CLT-%05d" % (count + 1)      # Python 2-style format — safe for old MySQL
            cur.execute("""
                INSERT INTO clients
                (id, client_id, email, password, full_name,
                 phone, address, created_at, assigned_agent, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
            """, (uid, cid, email, _hash(password), full_name,
                  phone, address, now, assigned_agent))
    return uid, cid


def update_client(uid, full_name, email, phone, address, is_active, assigned_agent):
    with _conn() as con:
        with con.cursor() as cur:
            cur.execute("""
                UPDATE clients
                SET full_name=%s, email=%s, phone=%s, address=%s,
                    is_active=%s, assigned_agent=%s
                WHERE id=%s
            """, (full_name, email, phone, address,
                  int(is_active), assigned_agent, uid))


def delete_client(uid):
    with _conn() as con:
        with con.cursor() as cur:
            cur.execute("DELETE FROM clients WHERE id=%s", (uid,))


# ═══════════════════════════════════════════════════════════════════
#  LOAN APPLICATIONS
# ═══════════════════════════════════════════════════════════════════
def add_loan_application(client_id, features: dict, prediction, probability):
    aid = str(uuid.uuid4())
    now = datetime.datetime.now()
    with _conn() as con:
        with con.cursor() as cur:
            cur.execute("""
                INSERT INTO loan_applications
                (id, client_id, no_of_dependents, education, self_employed,
                 income_annum, loan_amount, loan_term, cibil_score,
                 residential_assets_value, commercial_assets_value,
                 luxury_assets_value, bank_asset_value,
                 prediction, probability, status, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (aid, client_id,
                  features.get("no_of_dependents"),
                  features.get("education"),
                  features.get("self_employed"),
                  features.get("income_annum"),
                  features.get("loan_amount"),
                  features.get("loan_term"),
                  features.get("cibil_score"),
                  features.get("residential_assets_value"),
                  features.get("commercial_assets_value"),
                  features.get("luxury_assets_value"),
                  features.get("bank_asset_value"),
                  prediction, probability, "Pending", now))
    return aid


def get_applications_by_client(client_id):
    with _conn() as con:
        with con.cursor() as cur:
            cur.execute("""
                SELECT * FROM loan_applications
                WHERE client_id=%s ORDER BY created_at DESC
            """, (client_id,))
            return cur.fetchall()


def get_all_applications():
    with _conn() as con:
        with con.cursor() as cur:
            cur.execute("""
                SELECT la.*, c.full_name AS client_name, c.client_id AS client_code
                FROM loan_applications la
                JOIN clients c ON la.client_id = c.id
                ORDER BY la.created_at DESC
            """)
            return cur.fetchall()


def update_application_status(app_id, status, notes, reviewed_by):
    now = datetime.datetime.now()
    with _conn() as con:
        with con.cursor() as cur:
            cur.execute("""
                UPDATE loan_applications
                SET status=%s, notes=%s, reviewed_by=%s, reviewed_at=%s
                WHERE id=%s
            """, (status, notes, reviewed_by, now, app_id))


def get_application_by_id(app_id):
    with _conn() as con:
        with con.cursor() as cur:
            cur.execute("SELECT * FROM loan_applications WHERE id=%s", (app_id,))
            return cur.fetchone()


# ── Auto-initialise tables when this module is imported ─────────────
init_db()
