"""
Generate a comprehensive visual architecture diagram of the QA Learning Platform.
Run from project root:  python generate_platform_diagram.py
Requires: matplotlib  (pip install matplotlib)
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from matplotlib.lines import Line2D

# ── Canvas ───────────────────────────────────────────────────────────────────
FIG_W, FIG_H = 34, 26
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.axis("off")
BG = "#0d1117"
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

# ── Palette ───────────────────────────────────────────────────────────────────
C_BG        = "#0d1117"
C_PANEL     = "#161b22"
C_BORDER    = "#30363d"
C_TITLE     = "#f0f6fc"
C_SUBTEXT   = "#8b949e"
C_TEXT      = "#c9d1d9"

# Accent colours per layer
A_CLIENT    = "#ec4899"   # pink
A_APP       = "#3b82f6"   # blue
A_SWAGGER   = "#06b6d4"   # cyan
A_DASH      = "#10b981"   # green
A_TEST      = "#f59e0b"   # amber
A_INFRA     = "#8b5cf6"   # purple
A_DATA      = "#ef4444"   # red
A_REPORT    = "#f97316"   # orange
A_ARROW_H   = "#3b82f6"   # HTTP
A_ARROW_P   = "#f59e0b"   # pytest
A_ARROW_D   = "#10b981"   # data
A_ARROW_R   = "#f97316"   # reporting


# ═══════════════════════════════════════════════════════════════════
# DRAWING PRIMITIVES
# ═══════════════════════════════════════════════════════════════════

def panel(x, y, w, h, border_color, title, title_size=10, zorder=1):
    """Large section panel with coloured border and label."""
    rect = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.12,rounding_size=0.35",
        facecolor=C_PANEL, edgecolor=border_color,
        linewidth=2.2, alpha=0.75, zorder=zorder
    )
    ax.add_patch(rect)
    ax.text(x + 0.28, y + h - 0.3, title,
            ha="left", va="top", fontsize=title_size,
            color=border_color, fontweight="bold", zorder=zorder + 1)


def box(x, y, w, h, face, label,
        sub1=None, sub2=None, sub3=None,
        lfs=9, sfs=7.2, radius=0.18, border=None, zorder=4):
    """Component box with up to 3 subtitle lines."""
    border_c = border if border else face
    rect = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.05,rounding_size={radius}",
        facecolor=face, edgecolor=border_c,
        linewidth=1.1, alpha=0.95, zorder=zorder
    )
    ax.add_patch(rect)

    subs = [s for s in (sub1, sub2, sub3) if s]
    n = len(subs)
    total_h = (1 if n == 0 else n) * 0.22
    label_y = y + h / 2 + (total_h / 2 if subs else 0)

    ax.text(x + w / 2, label_y, label,
            ha="center", va="center", fontsize=lfs,
            color=C_TITLE, fontweight="bold", zorder=zorder + 1)

    for i, sub in enumerate(subs):
        ax.text(x + w / 2, label_y - 0.24 * (i + 1), sub,
                ha="center", va="center", fontsize=sfs,
                color=C_SUBTEXT, zorder=zorder + 1)


def tag(x, y, w, h, face, label, fs=7.5, zorder=5):
    """Compact tag / pill for file names."""
    rect = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.04,rounding_size=0.12",
        facecolor=face, edgecolor="none",
        linewidth=0, alpha=0.85, zorder=zorder
    )
    ax.add_patch(rect)
    ax.text(x + w / 2, y + h / 2, label,
            ha="center", va="center", fontsize=fs,
            color=C_TITLE, zorder=zorder + 1)


def arrow(x1, y1, x2, y2, color, label="", lw=1.6,
          style="->", rad=0.0, ls="-", fs=7):
    """Directed arrow with optional mid-label."""
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(
                    arrowstyle=style, color=color, lw=lw,
                    linestyle=ls,
                    connectionstyle=f"arc3,rad={rad}"
                ), zorder=6)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx + 0.12, my, label,
                ha="left", va="center", fontsize=fs,
                color=color, fontstyle="italic", zorder=7)


def dbl_arrow(x1, y1, x2, y2, color, label="", lw=1.6, rad=0.0, fs=7):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(
                    arrowstyle="<->", color=color, lw=lw,
                    connectionstyle=f"arc3,rad={rad}"
                ), zorder=6)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx + 0.12, my, label,
                ha="left", va="center", fontsize=fs,
                color=color, fontstyle="italic", zorder=7)


def divider(x, y, w, color=C_BORDER):
    ax.plot([x, x + w], [y, y], color=color, lw=0.8, alpha=0.5, zorder=3)


def section_label(x, y, text, color=C_SUBTEXT, fs=7.5):
    ax.text(x, y, text, ha="left", va="center",
            fontsize=fs, color=color,
            fontstyle="italic", zorder=5)


# ═══════════════════════════════════════════════════════════════════
# TITLE BAR
# ═══════════════════════════════════════════════════════════════════
rect = FancyBboxPatch((0.3, 24.5), 33.4, 1.2,
                      boxstyle="round,pad=0.1,rounding_size=0.2",
                      facecolor="#161b22", edgecolor="#30363d",
                      linewidth=1.5, zorder=2)
ax.add_patch(rect)
ax.text(17, 25.18, "QA Learning Platform  —  Full Architecture Overview",
        ha="center", va="center", fontsize=20,
        color=C_TITLE, fontweight="bold", zorder=3)
ax.text(17, 24.72, "Flask · pytest · Playwright · Flasgger/Swagger · Allure · SQLite · Docker · GitHub Actions",
        ha="center", va="center", fontsize=10,
        color=C_SUBTEXT, zorder=3)


# ═══════════════════════════════════════════════════════════════════
# ROW 1 — CLIENTS  (top strip)
# ═══════════════════════════════════════════════════════════════════
panel(0.3, 22.2, 33.4, 2.0, A_CLIENT, "① CLIENTS & ENTRY POINTS", title_size=9)

box(0.7,  22.45, 3.8, 1.4, "#831843",
    "Browser / Human User",
    sub1="Visits http://localhost:8080",
    sub2="Login · Register · Guestbook",
    sub3="Password Reset Flow")

box(4.8,  22.45, 3.8, 1.4, "#831843",
    "API Consumer / curl / Postman",
    sub1="Calls REST endpoints directly",
    sub2="Uses JWT Bearer token",
    sub3="Exercises /api/v1/* routes")

box(8.9,  22.45, 3.8, 1.4, "#831843",
    "Swagger UI  (Flasgger)",
    sub1="http://localhost:8080/apidocs/",
    sub2="Interactive API explorer",
    sub3="Auto-generated from docstrings")

box(12.95, 22.45, 3.8, 1.4, "#831843",
    "pytest Test Runner",
    sub1="Executes all test suites",
    sub2="Sends results → Dashboard",
    sub3="Generates Allure artifacts")

box(17.0,  22.45, 4.0, 1.4, "#831843",
    "GitHub Actions CI/CD",
    sub1=".github/workflows/ci-cd-pipeline.yml",
    sub2=".github/workflows/test.yml",
    sub3="Runs on push / pull-request")

box(21.25, 22.45, 3.8, 1.4, "#831843",
    "Docker / Kubernetes",
    sub1="Dockerfile  ·  docker-compose.yml",
    sub2="k8s-deployment.yaml",
    sub3="Container-based deployment")

box(25.3,  22.45, 4.1, 1.4, "#831843",
    "Locust Load Generator",
    sub1="tests/performance/locustfile.py",
    sub2="Simulates concurrent users",
    sub3="HTTP load against :8080")

box(29.65, 22.45, 3.75, 1.4, "#831843",
    "Dashboard Browser",
    sub1="http://localhost:6001",
    sub2="Views test results & metrics",
    sub3="Bug tracker · AI insights")


# ═══════════════════════════════════════════════════════════════════
# ROW 2 — THREE MAIN PANELS side by side
# ═══════════════════════════════════════════════════════════════════

# ── 2A  MAIN FLASK APP ────────────────────────────────────────────
panel(0.3, 10.2, 12.5, 11.75, A_APP,
      "② MAIN QA APP   src/app.py  ·  Flask  ·  Port 8080", title_size=9)

# Security middleware
box(0.7, 20.8, 11.7, 0.85, "#1c2e4a",
    "Security Middleware  (app.py  after_request hook)",
    sub1="CSP · HSTS · X-Frame-Options · X-XSS-Protection · X-Content-Type-Options · Referrer-Policy",
    lfs=8.5, sfs=7, radius=0.14, border="#3b82f6")

# Auth / Email
box(0.7,  19.65, 5.6, 0.9, "#1d3a6e",
    "JWT Authentication  (auth_helpers.py)",
    sub1="login · register · verify email",
    sub2="password reset tokens · PyJWT HS256")
box(6.6,  19.65, 5.8, 0.9, "#1d3a6e",
    "Email Service  (app.py config)",
    sub1="SMTP / TLS  ·  EMAIL_HOST / PORT",
    sub2="verification & reset token delivery")

divider(0.7, 19.55, 11.7)
section_label(0.7, 19.42, "API v1 Blueprints  (src/blueprints/v1/)")

# Blueprints
bw = 2.7
box(0.7,  18.4, bw, 0.88, "#1e40af", "/api/v1/auth",
    sub1="auth.py",
    sub2="login · logout · register\nverify · reset-password")
box(3.65, 18.4, bw, 0.88, "#1e40af", "/api/v1/guestbook",
    sub1="guestbook.py",
    sub2="GET · POST · PUT · DELETE\nentries  ·  search  ·  paginate")
box(6.6,  18.4, bw, 0.88, "#1e40af", "/api/v1/reactions",
    sub1="reactions.py",
    sub2="POST · DELETE  reactions\nper entry  ·  emoji support")
box(9.55, 18.4, 2.85, 0.88, "#1e40af", "/api/v1/webhooks",
    sub1="webhooks.py  ·  webhooks.py (src)",
    sub2="register · unregister\nlist · dispatch events")

divider(0.7, 18.3, 11.7)
section_label(0.7, 18.18, "Supporting Modules  (src/)")

# Supporting modules
box(0.7,  17.1, 2.7, 0.88, "#172f5e",
    "database.py",
    sub1="get_db()  ·  init_db()",
    sub2="get_db_path()  ·  clear_test_db()")
box(3.65, 17.1, 2.7, 0.88, "#172f5e",
    "logger_config.py",
    sub1="setup_logger()",
    sub2="logs/access.log · app.log\nerror.log")
box(6.6,  17.1, 2.7, 0.88, "#172f5e",
    "health_check.py",
    sub1="setup_health_routes()",
    sub2="/health  ·  /health/detailed\n/health/history")
box(9.55, 17.1, 2.85, 0.88, "#172f5e",
    "utils.py  ·  auth_helpers.py",
    sub1="is_user_authenticated()",
    sub2="helper utilities")

divider(0.7, 16.95, 11.7)
section_label(0.7, 16.83, "Swagger / OpenAPI Documentation  (Flasgger)")

# Swagger
box(0.7, 15.85, 5.6, 0.88, "#164e63",
    "Flasgger  (swagger config in app.py)",
    sub1="swagger_config  ·  swagger_template",
    sub2="Spec auto-built from route docstrings\n→  GET /apispec.json")
box(6.6, 15.85, 5.8, 0.88, "#164e63",
    "Swagger UI  /apidocs/",
    sub1="Interactive browser-based API explorer",
    sub2="JWT Bearer auth support\nTry-it-out for every endpoint")

divider(0.7, 15.72, 11.7)
section_label(0.7, 15.60, "HTML Templates  (templates/)  &  Static assets  (static/)")

# Templates
tw = 1.8
box(0.7,  14.65, tw, 0.75, "#1c3252", "login.html",      sub1="Login form")
box(2.7,  14.65, tw, 0.75, "#1c3252", "register.html",   sub1="Registration")
box(4.7,  14.65, tw, 0.75, "#1c3252", "guestbook.html",  sub1="Main app page")
box(6.7,  14.65, tw, 0.75, "#1c3252", "reset_password\n_request.html", sub1="Forgot pw")
box(8.7,  14.65, tw, 0.75, "#1c3252", "reset_password\n.html",         sub1="New pw")
box(10.7, 14.65, 1.7, 0.75, "#1c3252", "health\n_dashboard", sub1=".html")

divider(0.7, 14.5, 11.7)
section_label(0.7, 14.38, "Data Layer  (SQLite)")

# DB
box(0.7, 12.75, 5.6, 1.42, "#1a0a00",
    "guestbook.db  (production)",
    sub1="TABLE users",
    sub2="  id · username · password_hash · role",
    sub3="  email · verified · created_at")
box(6.6, 12.75, 5.8, 1.42, "#1a0a00",
    "guestbook_test.db  (test mode)",
    sub1="TABLE guestbook_entries",
    sub2="  id · author · message · timestamp",
    sub3="TABLE reactions  ·  TABLE webhooks")

box(0.7, 11.25, 11.7, 1.25, "#150800",
    "data/  directory",
    sub1="data/guestbook.db  ·  data/guestbook_test.db  ·  data/staging_guestbook.db",
    sub2="Database files for production · test · staging environments",
    lfs=8, sfs=7.5, radius=0.14)


# ── 2B  DASHBOARD BACKEND ─────────────────────────────────────────
panel(13.1, 10.2, 10.0, 11.75, A_DASH,
      "③ DASHBOARD BACKEND   dashboard/backend/app.py  ·  Flask  ·  Port 6001", title_size=9)

# CORS note
box(13.4, 20.8, 9.4, 0.85, "#052e16",
    "Flask-CORS  (all origins enabled for local dev)",
    sub1="Allows React frontend on any port to call the API",
    lfs=8.5, sfs=7, radius=0.14, border="#10b981")

# API Blueprints
section_label(13.4, 20.55, "API Blueprints  (registered at /api/*)")
bw2 = 2.9
box(13.4, 19.45, bw2, 1.0, "#064e3b",
    "Test Cases API",
    sub1="test_cases_api.py",
    sub2="CRUD for manual\ntest case management")
box(16.5, 19.45, bw2, 1.0, "#064e3b",
    "Bug Tracking API",
    sub1="bug_tracking_api.py",
    sub2="Create · update · close\nbug reports")
box(19.6, 19.45, 2.9, 1.0, "#064e3b",
    "AI Testing API",
    sub1="ai_testing_api.py",
    sub2="Analyze test failures\nAI improvement hints")

divider(13.4, 19.35, 9.4)
section_label(13.4, 19.22, "Core Dashboard Routes  (app.py  —  inline)")

box(13.4, 18.18, 4.5, 0.9, "#065f46",
    "Test Run Ingestion",
    sub1="POST /api/test-runs",
    sub2="Receives live results from conftest.py\nper-test real-time + session summary")
box(18.1, 18.18, 4.7, 0.9, "#065f46",
    "Dashboard Analytics",
    sub1="GET /api/dashboard/summary",
    sub2="/dashboard/test-types\n/dashboard/performance\n/dashboard/enhanced-summary")

divider(13.4, 18.08, 9.4)
section_label(13.4, 17.95, "Data Model  (models.py  —  DatabaseManager)")

box(13.4, 17.05, 9.4, 0.72, "#022c22",
    "DatabaseManager  (models.py)",
    sub1="init_enhanced_db()  ·  get_dashboard_analytics()  ·  migration helpers",
    lfs=8.5, sfs=7.5)

divider(13.4, 16.88, 9.4)
section_label(13.4, 16.75, "Database  (SQLite  —  dashboard/database/)")

box(13.4, 15.5, 4.5, 1.12, "#011a12",
    "test_dashboard.db",
    sub1="TABLE test_runs",
    sub2="  id · test_type · total · passed",
    sub3="  failed · skipped · duration · branch")
box(18.1, 15.5, 4.7, 1.12, "#011a12",
    "test_dashboard.db  (cont.)",
    sub1="TABLE test_cases  ·  TABLE performance_metrics",
    sub2="TABLE bug_reports",
    sub3="TABLE ai_test_sessions  ·  TABLE integration_settings")

divider(13.4, 15.38, 9.4)
section_label(13.4, 15.25, "Frontend  (served by Flask  ·  Port 6001)")

box(13.4, 14.15, 4.5, 0.9, "#047857",
    "Static HTML Dashboard",
    sub1="dashboard/frontend/index.html",
    sub2="Served at GET /  by Flask\nBasic metrics view")
box(18.1, 14.15, 4.7, 0.9, "#047857",
    "React Dashboard",
    sub1="dashboard/frontend-react/",
    sub2="Charts · live metrics · bug tracker\nAI suggestions  ·  npm run start")

divider(13.4, 14.0, 9.4)
section_label(13.4, 13.88, "Integration  (conftest.py  →  Dashboard)")

box(13.4, 12.6, 9.4, 1.05, "#033321",
    "DashboardReporter  (conftest.py)",
    sub1="pytest plugin: pytest_sessionstart · pytest_collection_finish",
    sub2="pytest_runtest_logreport  →  real-time POST per test",
    sub3="pytest_sessionfinish  →  full session summary  ·  AI failure analysis")

box(13.4, 11.45, 9.4, 0.9, "#011a10",
    "conftest.py  Fixtures",
    sub1="setup_test_database (session)  ·  clean_test_db (function)  ·  auth_token (module)",
    sub2="test_entry  ·  test_entries  (via factories.py)",
    lfs=8, sfs=7.5)


# ── 2C  TEST SUITE ────────────────────────────────────────────────
panel(23.4, 10.2, 10.3, 11.75, A_TEST,
      "④ TEST SUITE   tests/  ·  pytest  ·  Playwright  ·  Allure", title_size=9)

# API Tests
section_label(23.65, 21.55, "API Tests  (tests/api/)  —  pytest + requests")
box(23.65, 20.45, 4.7, 0.88, "#78350f",
    "test_contract_v1.py  +  test_api_contract.py",
    sub1="Contract testing: schema validation",
    sub2="JSON structure · status codes · headers")
box(28.6,  20.45, 4.85, 0.88, "#78350f",
    "test_auth_registration.py",
    sub1="Login · logout · register · token refresh",
    sub2="Invalid creds · expired tokens")

box(23.65, 19.35, 4.7, 0.88, "#92400e",
    "test_guestbook_api.py",
    sub1="CRUD operations on /api/v1/guestbook",
    sub2="Auth required · pagination · sorting")
box(28.6,  19.35, 4.85, 0.88, "#92400e",
    "test_reactions.py",
    sub1="POST/DELETE reactions per entry",
    sub2="Emoji types · duplicate detection")

box(23.65, 18.25, 4.7, 0.88, "#b45309",
    "test_negative_cases.py",
    sub1="400/401/403/404/422 scenarios",
    sub2="Missing fields · wrong types · no auth")
box(28.6,  18.25, 4.85, 0.88, "#b45309",
    "test_integrations.py",
    sub1="End-to-end flow tests",
    sub2="Register → login → post → react")

box(23.65, 17.15, 9.8, 0.88, "#d97706",
    "test_search.py",
    sub1="Search & filter on guestbook entries  ·  GET /api/v1/guestbook?search=  ·  pagination params",
    sub2="Sorting · edge cases · empty results · special characters",
    lfs=8.5, sfs=7.5)

divider(23.65, 17.0, 9.8)
# UI Tests
section_label(23.65, 16.88, "UI Tests  (tests/ui/)  —  Playwright  ·  pytest-playwright  ·  Chromium")

box(23.65, 15.78, 4.7, 0.88, "#064e3b",
    "test_login_ui.py",
    sub1="Login form · validation · redirect",
    sub2="Already-auth redirect guard")
box(28.6,  15.78, 4.85, 0.88, "#064e3b",
    "test_guestbook_ui.py",
    sub1="Add / view / delete entries via browser",
    sub2="Playwright page interactions")

box(23.65, 14.68, 4.7, 0.88, "#065f46",
    "test_search_ui.py  +  test_pagination_ui.py",
    sub1="Search box · filter controls · results",
    sub2="Pagination nav · page size · total count")
box(28.6,  14.68, 4.85, 0.88, "#065f46",
    "test_darkmode_ui.py  +  test_delete_modal.py",
    sub1="Dark/light mode toggle · CSS classes",
    sub2="Delete confirmation modal · cancel flow")

box(23.65, 13.62, 9.8, 0.78, "#022c22",
    "tests/ui/conftest.py  —  Playwright fixtures",
    sub1="browser · page · base_url fixtures  ·  headed / headless config  ·  screenshot on failure",
    lfs=8.5, sfs=7.5)

divider(23.65, 13.42, 9.8)
# Security Tests
section_label(23.65, 13.30, "Security Tests  (tests/security/)  —  pytest")

box(23.65, 12.25, 3.1, 0.88, "#4c0519",
    "test_authentication.py",
    sub1="Token forgery · brute force",
    sub2="Session fixation")
box(26.95, 12.25, 3.1, 0.88, "#4c0519",
    "test_injection.py",
    sub1="SQL injection",
    sub2="Command injection")
box(30.25, 12.25, 3.2, 0.88, "#4c0519",
    "test_input_validation.py",
    sub1="XSS payloads",
    sub2="Boundary values · types")

box(23.65, 11.18, 3.1, 0.88, "#7f1d1d",
    "test_penetration.py",
    sub1="OWASP-style probes",
    sub2="Rate limit bypass attempts")
box(26.95, 11.18, 6.5, 0.88, "#7f1d1d",
    "test_security_headers.py",
    sub1="Validates all security headers on every response",
    sub2="CSP · HSTS · X-Frame · XSS-Protection")

divider(23.65, 11.05, 9.8)
# Performance Tests
section_label(23.65, 10.93, "Performance Tests  (tests/performance/)  —  pytest-benchmark · Locust")

box(23.65, 10.3,  3.1, 0.52, "#451a03", "test_load_testing.py",     sub1="Sustained concurrent users", sfs=7)
box(26.95, 10.3,  3.1, 0.52, "#451a03", "test_stress_testing.py",   sub1="Beyond capacity limits",     sfs=7)
box(30.25, 10.3,  3.2, 0.52, "#451a03", "test_spike_testing.py",    sub1="Sudden traffic bursts",       sfs=7)

box(23.65, 9.65,  4.7, 0.52, "#78350f", "test_endurance_testing.py",   sub1="Long-run stability · memory leaks", sfs=7)
box(28.6,  9.65,  4.85, 0.52, "#78350f", "test_volume_testing.py  +  locustfile.py", sub1="Large datasets · Locust HTTP swarm", sfs=7)


# ═══════════════════════════════════════════════════════════════════
# ROW 3 — INFRASTRUCTURE & DEVOPS (bottom strip)
# ═══════════════════════════════════════════════════════════════════
panel(0.3, 0.3, 33.4, 9.65, A_INFRA,
      "⑤ INFRASTRUCTURE, DEVOPS & REPORTING", title_size=9)

# ── CI/CD ──
section_label(0.6, 9.55, "CI / CD  (.github/workflows/)", color=A_INFRA)
box(0.6, 8.35, 7.8, 0.98, "#2e1065",
    "ci-cd-pipeline.yml",
    sub1="Trigger: push / PR to main",
    sub2="Steps: checkout → setup Python → install deps → run pytest",
    sub3="→ upload Allure results → build Docker image → deploy")
box(8.7, 8.35, 7.8, 0.98, "#3b0764",
    "test.yml",
    sub1="Trigger: push to any branch",
    sub2="Fast feedback: lint (pre-commit) → unit tests",
    sub3="→ security scan (bandit · safety)")

# ── Docker / K8s ──
section_label(0.6, 8.12, "Containerisation & Orchestration", color=A_INFRA)
box(0.6,  6.98, 3.7, 0.92, "#2e1065",
    "Dockerfile",
    sub1="python:3.12-slim base",
    sub2="WORKDIR /app  ·  EXPOSE 8080",
    sub3="CMD python src/app.py")
box(4.5,  6.98, 3.7, 0.92, "#2e1065",
    "docker-compose.yml",
    sub1="app service  ·  port 8080:8080",
    sub2="Mounts ./data for DB persistence",
    sub3="Environment variable injection")
box(8.4,  6.98, 4.0, 0.92, "#3b0764",
    "k8s-deployment.yaml",
    sub1="Deployment · Service · ConfigMap",
    sub2="Replica scaling · health probes",
    sub3="Resource limits / requests")

# ── Scripts ──
section_label(0.6, 6.75, "Utility Scripts  (scripts/)", color=A_INFRA)
box(0.6,  5.65, 3.7, 0.9, "#1e1b4b",
    "seed_data.py",
    sub1="Populates DB with demo users",
    sub2="& sample guestbook entries")
box(4.5,  5.65, 3.7, 0.9, "#1e1b4b",
    "health_monitor.py",
    sub1="Polls /health endpoint",
    sub2="Logs uptime & response times")
box(8.4,  5.65, 3.7, 0.9, "#1e1b4b",
    "deploy.py  ·  deployment_health_check.sh",
    sub1="Orchestrates Docker build & push",
    sub2="Post-deploy smoke test")
box(12.3, 5.65, 4.0, 0.9, "#1e1b4b",
    "check_setup.py  ·  api_test_run.py",
    sub1="Validates env, deps, DB paths",
    sub2="Standalone API smoke runner")
box(16.5, 5.65, 4.0, 0.9, "#1e1b4b",
    "populate_dashboard.py  ·  cleanup_guestbook.py",
    sub1="Inserts demo test-run data",
    sub2="into test_dashboard.db")

# ── Reporting ──
section_label(0.6, 5.42, "Test Reporting  &  Quality Gates", color=A_REPORT)
box(0.6,  4.22, 3.9, 0.98, "#431407",
    "Allure Reports",
    sub1="allure-results/  (raw JSON artifacts)",
    sub2="pytest --alluredir=allure-results",
    sub3="allure serve allure-results")
box(4.7,  4.22, 3.9, 0.98, "#431407",
    "pytest-html  ·  pytest-cov",
    sub1="reports/test_report.html",
    sub2="--cov=src --cov-report=html",
    sub3=".coverage  ·  htmlcov/")
box(8.8,  4.22, 3.9, 0.98, "#7c2d12",
    "Security Reports",
    sub1="reports/security_test_report.html",
    sub2="reports/security_summary.json",
    sub3="bandit · safety scan outputs")
box(12.9, 4.22, 3.9, 0.98, "#7c2d12",
    "Performance Reports",
    sub1="scripts/reports/  directory",
    sub2="Locust HTML report",
    sub3="pytest-benchmark JSON")
box(17.0, 4.22, 3.9, 0.98, "#92400e",
    "Pre-commit Hooks",
    sub1=".pre-commit-config.yaml",
    sub2="black · flake8 · isort · bandit",
    sub3="Runs on git commit")

# ── Fixtures / Config ──
section_label(0.6, 4.0, "Test Infrastructure  &  Configuration", color=A_INFRA)
box(0.6,  2.95, 3.9, 0.82, "#172554",
    "conftest.py  (root)",
    sub1="DashboardReporter plugin",
    sub2="DB fixtures · auth_token fixture")
box(4.7,  2.95, 3.9, 0.82, "#172554",
    "tests/fixtures/factories.py",
    sub1="create_guestbook_entry()",
    sub2="create_multiple_entries(n)")
box(8.8,  2.95, 3.9, 0.82, "#172554",
    "pytest.ini  ·  pyproject.toml",
    sub1="markers: slow·integration·security",
    sub2="performance·ui·contract")
box(12.9, 2.95, 3.9, 0.82, "#172554",
    "requirements.txt",
    sub1="Flask·Playwright·pytest·Flasgger",
    sub2="Allure·Locust·Faker·Bandit·Safety")
box(17.0, 2.95, 3.9, 0.82, "#172554",
    "venv/  (virtual environment)",
    sub1="activate: venv\\Scripts\\activate",
    sub2="Isolates all Python dependencies")

# ── Docs / Roadmap ──
section_label(0.6, 2.72, "Documentation  &  Learning Resources", color=C_SUBTEXT)
box(0.6,  1.62, 3.9, 0.88, "#0f172a",
    "manuals/",
    sub1="student-learning/  · quick-start/",
    sub2="instructor-guide/  · video-scripts/",
    sub3="technical-reference/  · troubleshooting/")
box(4.7,  1.62, 3.9, 0.88, "#0f172a",
    "docs/",
    sub1="guides/  ·  features/  ·  roadmap/",
    sub2="implementation/  ·  registration/",
    sub3="guestbook_index.html")
box(8.8,  1.62, 3.9, 0.88, "#0f172a",
    "qa_platform_roadmap/",
    sub1="fas1…fas5 implementation HTMLs",
    sub2="qa_platform_roadmap.html",
    sub3="interview_questions.html")
box(12.9, 1.62, 3.9, 0.88, "#0f172a",
    "qa_platform_roadmap_v2/",
    sub1="fas1…fas3 v2 implementations",
    sub2="qa_platform_roadmap_v2.html")
box(17.0, 1.62, 3.9, 0.88, "#0f172a",
    "changes/",
    sub1="api_documentation_implementation",
    sub2="logging_monitoring · test_data",
    sub3="dashboard_database · restructure")

# Feature roadmap banner
box(0.6, 0.42, 32.8, 0.95, "#0c0a1e",
    "Feature Roadmap  (FAS = Feature Application Stages)",
    sub1="FAS1: Auth & Guestbook  ·  FAS2: Reactions & Webhooks  ·  FAS3: Security & Performance  ·  FAS4: AI Testing Integration  ·  FAS5: Bug Tracking  ·  FAS6: Pagination & Filtering",
    lfs=9, sfs=8, radius=0.15, border="#4f46e5")


# ═══════════════════════════════════════════════════════════════════
# DATA FLOW ARROWS
# ═══════════════════════════════════════════════════════════════════

# ── Clients → Main App ──
arrow(2.6,  22.45, 2.6,  22.05,  A_CLIENT, lw=1.8)   # Browser
arrow(6.7,  22.45, 6.7,  22.05,  A_CLIENT, lw=1.8)   # API Consumer
arrow(10.8, 22.45, 10.8, 22.05,  A_CLIENT, lw=1.8)   # Swagger UI → App

# ── Clients → Dashboard ──
arrow(31.55, 22.45, 22.8, 21.65, A_CLIENT, lw=1.5, rad=-0.1)  # Dashboard Browser

# ── pytest runner → Main App ──
arrow(14.95, 22.45, 6.0, 22.05, A_ARROW_P, "HTTP requests", lw=1.5, rad=0.15)

# ── pytest runner → Dashboard ──
arrow(15.5, 22.45, 18.0, 21.65, A_ARROW_P, "POST /api/test-runs", lw=1.5, rad=-0.1)

# ── CI/CD → pytest ──
arrow(19.1, 22.45, 15.5, 22.45, A_ARROW_P, "triggers", lw=1.4)

# ── Locust → Main App ──
arrow(27.3, 22.45, 8.0, 22.05, A_ARROW_H, "HTTP load", lw=1.3, rad=0.2)

# ── Main App ↔ Dashboard Backend ──
dbl_arrow(12.8, 17.5, 13.1, 17.5, "#64748b", "HTTP", lw=1.8)

# ── Test Suite ↔ Main App ──
dbl_arrow(23.4, 19.5, 12.8, 19.5, A_ARROW_H, "HTTP /api/v1/*", lw=1.5)

# ── Test Suite → Dashboard ──
arrow(23.4, 13.0, 22.5, 13.0, A_ARROW_P, "results", lw=1.3)

# ── Main App → Infra ──
arrow(6.5,  10.2, 6.5,  9.33, A_APP,   "deploy", lw=1.4)

# ── Dashboard → Infra ──
arrow(18.1, 10.2, 18.1, 9.33, A_DASH,  "deploy", lw=1.4)

# ── Test Suite → Allure ──
arrow(27.0, 9.6,  2.55, 5.2,  A_ARROW_R, "--alluredir", lw=1.3, rad=0.3)

# ── Test Suite → Infra (CI results) ──
arrow(28.5, 9.6,  10.5, 9.33, A_ARROW_P, "CI artifacts", lw=1.2, rad=-0.1)


# ═══════════════════════════════════════════════════════════════════
# LEGEND
# ═══════════════════════════════════════════════════════════════════
legend_y = 25.0
legend_items = [
    (A_CLIENT, "Clients / Entry Points"),
    (A_APP,    "Main Flask App (:8080)"),
    (A_SWAGGER,"Swagger / OpenAPI"),
    (A_DASH,   "Dashboard Backend (:6001)"),
    (A_TEST,   "Test Suite"),
    (A_INFRA,  "Infrastructure / DevOps"),
    (A_DATA,   "Database / Data Layer"),
    (A_REPORT, "Reporting / Artefacts"),
]
arrow_legend = [
    (A_ARROW_H, "HTTP request"),
    (A_ARROW_P, "pytest / CI flow"),
    (A_ARROW_D, "DB read/write"),
    (A_ARROW_R, "Reporting output"),
]

lx = 0.6
for col, label in legend_items:
    rect = FancyBboxPatch((lx, legend_y + 0.08), 0.45, 0.3,
                          boxstyle="round,pad=0.03",
                          facecolor=col, edgecolor="none", zorder=8)
    ax.add_patch(rect)
    ax.text(lx + 0.6, legend_y + 0.22, label,
            ha="left", va="center", fontsize=8,
            color=C_TEXT, zorder=9)
    lx += 3.85

# Arrow legend (right side)
lx = 21.5
for col, label in arrow_legend:
    ax.annotate("", xy=(lx + 0.9, legend_y + 0.22),
                xytext=(lx, legend_y + 0.22),
                arrowprops=dict(arrowstyle="->", color=col, lw=1.8), zorder=8)
    ax.text(lx + 1.05, legend_y + 0.22, label,
            ha="left", va="center", fontsize=8,
            color=C_TEXT, zorder=9)
    lx += 2.9


# ═══════════════════════════════════════════════════════════════════
# SAVE
# ═══════════════════════════════════════════════════════════════════
plt.tight_layout(pad=0)
out = "platform_architecture.png"
plt.savefig(out, dpi=160, bbox_inches="tight",
            facecolor=fig.get_facecolor())
print(f"Saved → {out}  ({FIG_W}x{FIG_H} inches @ 160 dpi)")
