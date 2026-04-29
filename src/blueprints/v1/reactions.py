"""Entry reactions routes Blueprint (v1)."""

import jwt
from flask import Blueprint, current_app, jsonify, request

from auth_helpers import token_required
from database import get_db
from utils import VALID_REACTIONS

bp = Blueprint("reactions_v1", __name__)


def _get_jwt_user_identifier():
    """Extract user identifier string from the Bearer JWT in the current request."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        raw = auth_header.split(" ", 1)[1]
    else:
        raw = auth_header
    payload = jwt.decode(
        raw, current_app.config["SECRET_KEY"], algorithms=["HS256"]
    )
    return payload.get("user") or payload.get("sub") or ""


@bp.route("/entries/<int:entry_id>/reactions", methods=["GET"])
def get_entry_reactions(entry_id):
    """
    Get reaction counts for a guestbook entry
    ---
    tags:
      - Reactions
    parameters:
      - in: path
        name: entry_id
        type: integer
        required: true
    responses:
      200:
        description: Reaction counts
        schema:
          type: object
          properties:
            like:
              type: integer
            love:
              type: integer
            laugh:
              type: integer
            user_reactions:
              type: array
              items:
                type: string
      404:
        description: Entry not found
    """
    conn = get_db()
    entry = conn.execute(
        "SELECT userId FROM guestbook WHERE userId = ?", (entry_id,)
    ).fetchone()
    if not entry:
        conn.close()
        return jsonify({"message": "Entry not found"}), 404

    rows = conn.execute(
        "SELECT reaction_type, COUNT(*) as count FROM entry_reactions "
        "WHERE entry_id = ? GROUP BY reaction_type",
        (entry_id,),
    ).fetchall()
    counts = {"like": 0, "love": 0, "laugh": 0}
    for row in rows:
        counts[row["reaction_type"]] = row["count"]

    user_reactions = []
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            user_identifier = _get_jwt_user_identifier()
            user_rows = conn.execute(
                "SELECT reaction_type FROM entry_reactions "
                "WHERE entry_id = ? AND user_identifier = ?",
                (entry_id, user_identifier),
            ).fetchall()
            user_reactions = [r["reaction_type"] for r in user_rows]
        except Exception:
            pass

    conn.close()
    result = dict(counts)
    result["user_reactions"] = user_reactions
    return jsonify(result), 200


@bp.route("/entries/<int:entry_id>/reactions", methods=["POST"])
@token_required
def toggle_entry_reaction(entry_id):
    """
    Toggle (add or remove) a reaction on a guestbook entry
    ---
    tags:
      - Reactions
    security:
      - Bearer: []
    parameters:
      - in: path
        name: entry_id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - reaction_type
          properties:
            reaction_type:
              type: string
              enum: [like, love, laugh]
    responses:
      200:
        description: Reaction removed (toggled off)
      201:
        description: Reaction added
      400:
        description: Invalid reaction type
      404:
        description: Entry not found
    """
    conn = get_db()
    entry = conn.execute(
        "SELECT userId FROM guestbook WHERE userId = ?", (entry_id,)
    ).fetchone()
    if not entry:
        conn.close()
        return jsonify({"message": "Entry not found"}), 404

    data = request.get_json(force=True) or {}
    reaction_type = data.get("reaction_type")
    if reaction_type not in VALID_REACTIONS:
        conn.close()
        return (
            jsonify(
                {"message": "Invalid reaction type. Must be one of: like, love, laugh"}
            ),
            400,
        )

    try:
        user_identifier = _get_jwt_user_identifier()
    except Exception:
        conn.close()
        return jsonify({"message": "Token is invalid"}), 401

    existing = conn.execute(
        "SELECT id FROM entry_reactions "
        "WHERE entry_id = ? AND user_identifier = ? AND reaction_type = ?",
        (entry_id, user_identifier, reaction_type),
    ).fetchone()

    cursor = conn.cursor()
    if existing:
        cursor.execute(
            "DELETE FROM entry_reactions "
            "WHERE entry_id = ? AND user_identifier = ? AND reaction_type = ?",
            (entry_id, user_identifier, reaction_type),
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Reaction removed", "action": "removed"}), 200
    else:
        cursor.execute(
            "INSERT INTO entry_reactions (entry_id, user_identifier, reaction_type) "
            "VALUES (?, ?, ?)",
            (entry_id, user_identifier, reaction_type),
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Reaction added", "action": "added"}), 201
