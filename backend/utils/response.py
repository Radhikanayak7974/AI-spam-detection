"""
Standardized API response helpers.
All routes should use these helpers for consistency.
"""
from flask import jsonify


def success_response(data=None, message="Success", status_code=200, meta=None):
    """Return a standard success JSON response."""
    response = {
        "success": True,
        "message": message,
        "data": data,
    }
    if meta:
        response["meta"] = meta
    return jsonify(response), status_code


def error_response(message="An error occurred", status_code=400, errors=None):
    """Return a standard error JSON response."""
    response = {
        "success": False,
        "message": message,
        "data": None,
    }
    if errors:
        response["errors"] = errors
    return jsonify(response), status_code


def paginated_response(items, total, page, per_page, message="Success"):
    """Return a paginated list response."""
    return success_response(
        data=items,
        message=message,
        meta={
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
            "has_next": page * per_page < total,
            "has_prev": page > 1,
        },
    )
