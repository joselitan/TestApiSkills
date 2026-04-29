"""Guestbook CRUD routes Blueprint (v1)."""

import datetime
import json
import re

import pandas as pd
from flask import Blueprint, current_app, jsonify, request

from auth_helpers import token_required
from database import get_db
from utils import sanitize_html, validate_filename, validate_json_payload
from webhooks import dispatch

bp = Blueprint("guestbook_v1", __name__)


def _parse_date(value, param_name):
    try:
        return datetime.datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None


@bp.route("/guestbook", methods=["POST"])
@token_required
def create_entry():
    """
    Create a new guestbook entry
    ---
    tags:
      - Guestbook
    security:
      - Bearer: []
    parameters:
      - in: body
        name: entry
        required: true
        schema:
          type: object
          required:
            - name
            - email
            - comment
          properties:
            name:
              type: string
              example: "John Doe"
            email:
              type: string
              example: "john@example.com"
            comment:
              type: string
              example: "Great API!"
    responses:
      201:
        description: Entry created successfully
        schema:
          type: object
          properties:
            userId:
              type: integer
              example: 1
            name:
              type: string
              example: "John Doe"
            email:
              type: string
              example: "john@example.com"
            comment:
              type: string
              example: "Great API!"
            created_at:
              type: string
              example: "2026-03-06 10:30:00"
      400:
        description: Bad request - missing required fields
      401:
        description: Unauthorized - invalid or missing token
    """
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"message": "Invalid JSON payload"}), 400

        is_valid, message = validate_json_payload(data)
        if not is_valid:
            return jsonify({"message": message}), 400

    except (json.JSONDecodeError, Exception) as e:
        current_app.logger.warning(f"Invalid JSON in create entry request: {str(e)}")
        return jsonify({"message": "Invalid JSON payload"}), 400

    name = data.get("name")
    email = data.get("email")
    comment = data.get("comment")

    if not name or not email:
        return jsonify({"message": "Name and email are required"}), 400

    if (
        not isinstance(name, str)
        or not isinstance(email, str)
        or not isinstance(comment, str)
    ):
        return jsonify({"message": "Name, email, and comment must be strings"}), 400

    comment = comment or ""

    name = sanitize_html(name)
    email = sanitize_html(email)
    comment = sanitize_html(comment)

    if len(name) > 100 or len(email) > 100 or len(comment) > 1000:
        return jsonify({"message": "Input too long"}), 400

    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        return jsonify({"message": "Invalid email format"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO guestbook (name, email, comment) VALUES (?, ?, ?)",
        (name, email, comment),
    )
    conn.commit()
    entry_id = cursor.lastrowid
    entry = conn.execute(
        "SELECT * FROM guestbook WHERE userId = ?", (entry_id,)
    ).fetchone()
    conn.close()

    dispatch("entry.created", dict(entry))
    return jsonify(dict(entry)), 201


@bp.route("/guestbook", methods=["GET"])
@token_required
def get_all_entries():
    """
    Get all guestbook entries with pagination, keyword search and advanced filters
    ---
    tags:
      - Guestbook
    security:
      - Bearer: []
    parameters:
      - in: query
        name: page
        type: integer
        default: 1
        description: Page number
      - in: query
        name: limit
        type: integer
        default: 10
        description: Number of entries per page
      - in: query
        name: search
        type: string
        description: Keyword search (matches name, email, comment — case-insensitive partial match)
      - in: query
        name: author
        type: string
        description: Filter by author name (partial match)
      - in: query
        name: from_date
        type: string
        description: Start of date range (ISO 8601, e.g. 2024-01-01)
      - in: query
        name: to_date
        type: string
        description: End of date range (ISO 8601, e.g. 2024-12-31)
      - in: query
        name: sort
        type: string
        enum: [newest, oldest]
        default: newest
        description: Sort order
    responses:
      200:
        description: List of guestbook entries
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                type: object
                properties:
                  userId:
                    type: integer
                  name:
                    type: string
                  email:
                    type: string
                  comment:
                    type: string
                  created_at:
                    type: string
            meta:
              type: object
              properties:
                page:
                  type: integer
                limit:
                  type: integer
                total:
                  type: integer
                pages:
                  type: integer
      400:
        description: Bad request (invalid date format, date range, or oversized input)
      401:
        description: Unauthorized
    """
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)
    search = request.args.get("search", None, type=str)
    author = request.args.get("author", None, type=str)
    from_date = request.args.get("from_date", None, type=str)
    to_date = request.args.get("to_date", None, type=str)
    sort = request.args.get("sort", "newest", type=str)

    if search is not None:
        search = search.strip() or None
    if author is not None:
        author = author.strip() or None

    if search and len(search) > 500:
        return jsonify({"message": "Search query too long (max 500 characters)"}), 400
    if author and len(author) > 500:
        return jsonify({"message": "Author filter too long (max 500 characters)"}), 400

    from_dt = to_dt = None
    if from_date:
        from_dt = _parse_date(from_date, "from_date")
        if from_dt is None:
            return (
                jsonify({"message": "Invalid from_date format; expected YYYY-MM-DD"}),
                400,
            )
    if to_date:
        to_dt = _parse_date(to_date, "to_date")
        if to_dt is None:
            return (
                jsonify({"message": "Invalid to_date format; expected YYYY-MM-DD"}),
                400,
            )
    if from_dt and to_dt and from_dt > to_dt:
        return jsonify({"message": "from_date must not be after to_date"}), 400

    if sort not in ("newest", "oldest"):
        sort = "newest"

    conditions = []
    params = []

    if search:
        search_term = f"%{search}%"
        conditions.append("(name LIKE ? OR email LIKE ? OR comment LIKE ?)")
        params.extend([search_term, search_term, search_term])

    if author:
        conditions.append("name LIKE ?")
        params.append(f"%{author}%")

    if from_dt:
        conditions.append("created_at >= ?")
        params.append(from_date)

    if to_dt:
        conditions.append("created_at <= ?")
        params.append(to_date + " 23:59:59")

    where_clause = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    order_clause = " ORDER BY created_at " + ("ASC" if sort == "oldest" else "DESC")

    offset = (page - 1) * limit
    conn = get_db()

    base_query = "FROM guestbook"
    count_query = f"SELECT COUNT(*) {base_query}{where_clause}"
    total_count = conn.execute(count_query, params).fetchone()[0]

    data_query = f"SELECT * {base_query}{where_clause}{order_clause} LIMIT ? OFFSET ?"
    entries = conn.execute(data_query, params + [limit, offset]).fetchall()
    conn.close()

    return jsonify(
        {
            "data": [dict(entry) for entry in entries],
            "meta": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit if limit > 0 else 0,
            },
        }
    )


@bp.route("/guestbook/<int:user_id>", methods=["GET"])
@token_required
def get_entry(user_id):
    """
    Get a single guestbook entry by ID
    ---
    tags:
      - Guestbook
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
        description: The entry ID
    responses:
      200:
        description: Guestbook entry found
        schema:
          type: object
          properties:
            userId:
              type: integer
            name:
              type: string
            email:
              type: string
            comment:
              type: string
            created_at:
              type: string
      404:
        description: Entry not found
      401:
        description: Unauthorized
    """
    conn = get_db()
    entry = conn.execute(
        "SELECT * FROM guestbook WHERE userId = ?", (user_id,)
    ).fetchone()
    conn.close()

    if entry:
        return jsonify(dict(entry))
    return jsonify({"message": "Entry not found"}), 404


@bp.route("/guestbook/<int:user_id>", methods=["PUT"])
@token_required
def update_entry(user_id):
    """
    Update a guestbook entry
    ---
    tags:
      - Guestbook
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
        description: The entry ID to update
      - in: body
        name: entry
        required: true
        schema:
          type: object
          required:
            - name
            - email
            - comment
          properties:
            name:
              type: string
              example: "Jane Doe"
            email:
              type: string
              example: "jane@example.com"
            comment:
              type: string
              example: "Updated comment"
    responses:
      200:
        description: Entry updated successfully
        schema:
          type: object
          properties:
            userId:
              type: integer
            name:
              type: string
            email:
              type: string
            comment:
              type: string
            created_at:
              type: string
      400:
        description: Bad request
      404:
        description: Entry not found
      401:
        description: Unauthorized
    """
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"message": "Invalid JSON payload"}), 400

        is_valid, message = validate_json_payload(data)
        if not is_valid:
            return jsonify({"message": message}), 400

    except (json.JSONDecodeError, Exception) as e:
        current_app.logger.warning(f"Invalid JSON in update entry request: {str(e)}")
        return jsonify({"message": "Invalid JSON payload"}), 400

    name = data.get("name")
    email = data.get("email")
    comment = data.get("comment")

    if not name or not email or not comment:
        return jsonify({"message": "Name, email, and comment are required"}), 400

    name = sanitize_html(name)
    email = sanitize_html(email)
    comment = sanitize_html(comment)

    if len(name) > 100 or len(email) > 100 or len(comment) > 1000:
        return jsonify({"message": "Input too long"}), 400

    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        return jsonify({"message": "Invalid email format"}), 400

    conn = get_db()
    conn.execute(
        "UPDATE guestbook SET name = ?, email = ?, comment = ? WHERE userId = ?",
        (name, email, comment, user_id),
    )
    conn.commit()
    entry = conn.execute(
        "SELECT * FROM guestbook WHERE userId = ?", (user_id,)
    ).fetchone()
    conn.close()

    if entry:
        return jsonify(dict(entry))
    return jsonify({"message": "Entry not found"}), 404


@bp.route("/guestbook/<int:user_id>", methods=["DELETE"])
@token_required
def delete_entry(user_id):
    """
    Delete a guestbook entry
    ---
    tags:
      - Guestbook
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
        description: The entry ID to delete
    responses:
      200:
        description: Entry deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Entry deleted successfully"
      404:
        description: Entry not found
      401:
        description: Unauthorized
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM guestbook WHERE userId = ?", (user_id,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()

    if deleted:
        return jsonify({"message": "Entry deleted successfully"})
    return jsonify({"message": "Entry not found"}), 404


@bp.route("/guestbook/bulk", methods=["DELETE"])
@token_required
def bulk_delete_entries():
    """
    Delete multiple guestbook entries
    ---
    tags:
      - Guestbook
    security:
      - Bearer: []
    parameters:
      - in: body
        name: ids
        required: true
        schema:
          type: object
          required:
            - ids
          properties:
            ids:
              type: array
              items:
                type: integer
              example: [1, 2, 3]
    responses:
      200:
        description: Entries deleted successfully
        schema:
          type: object
          properties:
            deleted:
              type: integer
              example: 3
            message:
              type: string
              example: "3 entries deleted successfully"
      400:
        description: Bad request - IDs array required
      401:
        description: Unauthorized
    """
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"message": "Invalid JSON payload"}), 400

        is_valid, message = validate_json_payload(data)
        if not is_valid:
            return jsonify({"message": message}), 400

    except (json.JSONDecodeError, Exception) as e:
        current_app.logger.warning(f"Invalid JSON in bulk delete request: {str(e)}")
        return jsonify({"message": "Invalid JSON payload"}), 400

    ids = data.get("ids", [])

    if not ids or not isinstance(ids, list):
        return jsonify({"message": "IDs array is required"}), 400

    conn = get_db()
    cursor = conn.cursor()
    placeholders = ",".join("?" * len(ids))
    cursor.execute(f"DELETE FROM guestbook WHERE userId IN ({placeholders})", ids)
    conn.commit()
    deleted = cursor.rowcount
    conn.close()

    return jsonify(
        {"deleted": deleted, "message": f"{deleted} entries deleted successfully"}
    )


@bp.route("/guestbook/cleanup", methods=["DELETE"])
@token_required
def cleanup_all_entries():
    """
    Delete ALL guestbook entries (cleanup database)
    ---
    tags:
      - Guestbook
    security:
      - Bearer: []
    parameters:
      - in: query
        name: test_mode
        type: boolean
        default: false
        description: Whether to cleanup test database (true) or production database (false)
    responses:
      200:
        description: All entries deleted successfully
        schema:
          type: object
          properties:
            deleted:
              type: integer
              example: 25
            message:
              type: string
              example: "25 entries deleted successfully"
            database:
              type: string
              example: "production"
      401:
        description: Unauthorized
      500:
        description: Database error
    """
    test_mode = request.args.get("test_mode", "false").lower() == "true"

    try:
        conn = get_db()
        cursor = conn.cursor()

        count_before = cursor.execute("SELECT COUNT(*) FROM guestbook").fetchone()[0]

        if count_before == 0:
            conn.close()
            return jsonify(
                {
                    "deleted": 0,
                    "message": "No entries to delete",
                    "database": "test" if test_mode else "production",
                }
            )

        cursor.execute("DELETE FROM guestbook")
        conn.commit()

        count_after = cursor.execute("SELECT COUNT(*) FROM guestbook").fetchone()[0]
        deleted = count_before - count_after

        conn.close()

        current_app.logger.info(
            f"Cleanup completed: {deleted} entries deleted from "
            f"{'test' if test_mode else 'production'} database"
        )

        return jsonify(
            {
                "deleted": deleted,
                "message": f"{deleted} entries deleted successfully",
                "database": "test" if test_mode else "production",
            }
        )

    except Exception as e:
        current_app.logger.error(f"Cleanup failed: {str(e)}")
        return jsonify({"message": f"Cleanup failed: {str(e)}"}), 500


@bp.route("/guestbook/import", methods=["POST"])
@token_required
def import_excel():
    """
    Import guestbook entries from Excel file
    ---
    tags:
      - Guestbook
    security:
      - Bearer: []
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: file
        type: file
        required: true
        description: Excel file with columns 'name', 'email', and optionally 'comment'
    responses:
      200:
        description: Entries imported successfully
        schema:
          type: object
          properties:
            imported:
              type: integer
              example: 5
            message:
              type: string
              example: "5 entries imported successfully"
      400:
        description: Bad request - invalid file or format
      401:
        description: Unauthorized
    """
    if "file" not in request.files:
        return jsonify({"message": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"message": "No file selected"}), 400

    is_valid, result = validate_filename(file.filename)
    if not is_valid:
        return jsonify({"message": result}), 400

    try:
        df = pd.read_excel(file)
        required_columns = ["name", "email"]
        if not all(col in df.columns for col in required_columns):
            return (
                jsonify({"message": "Excel must contain name and email columns"}),
                400,
            )

        conn = get_db()
        cursor = conn.cursor()
        imported = 0

        for _, row in df.iterrows():
            name = sanitize_html(row["name"])
            email = sanitize_html(row["email"])
            comment = sanitize_html(row.get("comment", ""))
            cursor.execute(
                "INSERT INTO guestbook (name, email, comment) VALUES (?, ?, ?)",
                (name, email, comment),
            )
            imported += 1

        conn.commit()
        conn.close()

        return jsonify(
            {
                "imported": imported,
                "message": f"{imported} entries imported successfully",
            }
        )
    except Exception as e:
        return jsonify({"message": f"Error processing file: {str(e)}"}), 400
