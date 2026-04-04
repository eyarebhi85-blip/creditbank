# ════════════════════════════════════════════════════════════════════
#  loan_app_db.sql  —  FOR EasyPHP 1.8  (MySQL 4.x / MyISAM)
#
#  HOW TO RUN:
#  1. Open browser  →  http://localhost/mysql/
#  2. Click "SQL" tab at the top
#  3. Paste ALL this file content  →  click "Execute"
# ════════════════════════════════════════════════════════════════════

CREATE DATABASE IF NOT EXISTS loan_app_db;

USE loan_app_db;

# TABLE 1 — users (admins + agents)
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
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

# TABLE 2 — clients
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
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

# TABLE 3 — loan_applications
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
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

# Done! 3 tables created.
# Default admin/agent accounts will be created automatically
# the first time you run:  streamlit run app.py
