"""
app.py – Flask application entry point for Smart Notepad.
"""

import base64
import io
import json
import mimetypes
import os
import uuid
from datetime import datetime, timezone, timedelta
from werkzeug.utils import secure_filename


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    session,
    url_for,
)
from flask_wtf.csrf import CSRFProtect

from config import DevelopmentConfig, config_map
from database import (
    create_credential,
    create_file_item,
    create_note,
    db,
    delete_credential,
    delete_file_item,
    delete_note,
    get_all_credentials,
    get_all_files,
    get_all_notes,
    get_credential,
    get_file_item,
    get_note,
    init_db,
    is_vault_setup,
    search_notes,
    set_vault_password,
    update_credential,
    update_file_item,
    update_note,
    verify_vault_password,
    Credential,
    FileItem,
    Note,
    VaultConfig,
)

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = Flask(__name__)
env = os.environ.get("FLASK_ENV", "development").lower()
app.config.from_object(config_map.get(env, DevelopmentConfig))
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# CSRF protection – API routes are excluded via WTF_CSRF_CHECK_DEFAULT=False
# (set in config); individual view routes that POST HTML forms opt-in manually.
csrf = CSRFProtect(app)

# Initialise and create DB tables
init_db(app)


# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------

@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": "Bad request", "message": str(e)}), 400


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found", "message": str(e)}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error", "message": str(e)}), 500


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    notes = get_all_notes(sort="updated")
    total_notes = len(notes)
    # Recently updated: modified in the last 7 days
    cutoff = utc_now() - timedelta(days=7)
    recently_updated = sum(1 for n in notes if n.updated_at >= cutoff)
    return render_template(
        "index.html",
        notes=notes,
        total_notes=total_notes,
        recently_updated=recently_updated,
    )


@app.route("/note/new")
def note_new():
    return render_template("editor.html", note=None)


@app.route("/note/<int:note_id>")
def note_edit(note_id):
    note = get_note(note_id)
    if note is None:
        return jsonify({"error": "Note not found"}), 404
    return render_template("editor.html", note=note)


@app.route("/settings")
def settings():
    return render_template("settings.html")


@app.route("/vault")
def vault():
    setup = is_vault_setup()
    unlocked = bool(session.get("vault_unlocked"))
    credentials = get_all_credentials() if unlocked else []
    return render_template(
        "vault.html",
        is_setup=setup,
        is_unlocked=unlocked,
        credentials=credentials,
    )


@app.route("/files")
def files():
    category = request.args.get("category", "all")
    search = request.args.get("q", "").strip() or None
    file_items = get_all_files(category=category, search=search)
    return render_template(
        "files.html",
        files=file_items,
        current_category=category,
        search_query=search or "",
    )


# ---------------------------------------------------------------------------
# API – Notes CRUD
# ---------------------------------------------------------------------------

@app.route("/api/notes", methods=["GET"])
def api_list_notes():
    sort = request.args.get("sort", "updated")
    if sort not in ("created", "updated"):
        sort = "updated"
    notes = get_all_notes(sort=sort)
    return jsonify([n.to_dict() for n in notes])


@app.route("/api/notes/search", methods=["GET"])
def api_search_notes():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400
    notes = search_notes(query)
    return jsonify([n.to_dict() for n in notes])


@app.route("/api/notes", methods=["POST"])
def api_create_note():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    heading = (data.get("heading") or "").strip()
    content = (data.get("content") or "").strip()

    if not heading:
        return jsonify({"error": "Field 'heading' is required"}), 422
    if len(heading) > 255:
        return jsonify({"error": "Field 'heading' must be ≤ 255 characters"}), 422

    note = create_note(heading=heading, content=content)
    return jsonify(note.to_dict()), 201


@app.route("/api/notes/<int:note_id>", methods=["GET"])
def api_get_note(note_id):
    note = get_note(note_id)
    if note is None:
        return jsonify({"error": f"Note {note_id} not found"}), 404
    return jsonify(note.to_dict())


@app.route("/api/notes/<int:note_id>", methods=["PUT"])
def api_update_note(note_id):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    heading = (data.get("heading") or "").strip()
    content = (data.get("content") or "").strip()

    if not heading:
        return jsonify({"error": "Field 'heading' is required"}), 422
    if len(heading) > 255:
        return jsonify({"error": "Field 'heading' must be ≤ 255 characters"}), 422

    try:
        note = update_note(note_id, heading=heading, content=content)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404

    return jsonify(note.to_dict())


@app.route("/api/notes/<int:note_id>", methods=["DELETE"])
def api_delete_note(note_id):
    try:
        delete_note(note_id)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    return jsonify({"message": f"Note {note_id} deleted successfully"})


# ---------------------------------------------------------------------------
# API – Vault (Password Manager)
# ---------------------------------------------------------------------------

@app.route("/api/vault/status", methods=["GET"])
def api_vault_status():
    return jsonify({
        "is_setup": is_vault_setup(),
        "is_unlocked": bool(session.get("vault_unlocked")),
    })


@app.route("/api/vault/setup", methods=["POST"])
def api_vault_setup():
    if is_vault_setup():
        return jsonify({"error": "Master password is already configured"}), 400

    data = request.get_json(silent=True) or {}
    password = (data.get("password") or "").strip()
    confirm = (data.get("confirm_password") or "").strip()

    if not password or len(password) < 4:
        return jsonify({"error": "Password must be at least 4 characters long"}), 422
    if password != confirm:
        return jsonify({"error": "Passwords do not match"}), 422

    set_vault_password(password)
    session["vault_unlocked"] = True
    return jsonify({"message": "Master password configured successfully", "unlocked": True}), 201


@app.route("/api/vault/unlock", methods=["POST"])
def api_vault_unlock():
    if not is_vault_setup():
        return jsonify({"error": "Master password has not been configured yet"}), 400

    data = request.get_json(silent=True) or {}
    password = data.get("password") or ""

    if not verify_vault_password(password):
        return jsonify({"error": "Incorrect master password"}), 401

    session["vault_unlocked"] = True
    return jsonify({"message": "Vault unlocked successfully", "unlocked": True})


@app.route("/api/vault/lock", methods=["POST"])
def api_vault_lock():
    session.pop("vault_unlocked", None)
    return jsonify({"message": "Vault locked", "unlocked": False})


@app.route("/api/vault/change-master", methods=["POST"])
def api_vault_change_master():
    if not session.get("vault_unlocked"):
        return jsonify({"error": "Vault must be unlocked to change master password"}), 403

    data = request.get_json(silent=True) or {}
    current_pw = data.get("current_password") or ""
    new_pw = (data.get("new_password") or "").strip()
    confirm_pw = (data.get("confirm_password") or "").strip()

    if not verify_vault_password(current_pw):
        return jsonify({"error": "Current password is incorrect"}), 401
    if not new_pw or len(new_pw) < 4:
        return jsonify({"error": "New password must be at least 4 characters long"}), 422
    if new_pw != confirm_pw:
        return jsonify({"error": "New passwords do not match"}), 422

    set_vault_password(new_pw)
    return jsonify({"message": "Master password changed successfully"})


@app.route("/api/vault/credentials", methods=["GET"])
def api_vault_list_credentials():
    if not session.get("vault_unlocked"):
        return jsonify({"error": "Vault is locked. Enter password to view."}), 403

    q = request.args.get("q", "").strip() or None
    creds = get_all_credentials(search=q)
    return jsonify([c.to_dict() for c in creds])


@app.route("/api/vault/credentials", methods=["POST"])
def api_vault_create_credential():
    if not session.get("vault_unlocked"):
        return jsonify({"error": "Vault is locked"}), 403

    data = request.get_json(silent=True) or {}
    platform = (data.get("platform") or "").strip()
    identifier = (data.get("identifier") or "").strip()
    password = data.get("password") or ""
    notes = (data.get("notes") or "").strip()

    if not platform:
        return jsonify({"error": "Platform name is required"}), 422
    if not identifier:
        return jsonify({"error": "Email or phone number is required"}), 422

    cred = create_credential(platform=platform, identifier=identifier, password=password, notes=notes)
    return jsonify(cred.to_dict()), 201


@app.route("/api/vault/credentials/<int:cred_id>", methods=["PUT"])
def api_vault_update_credential(cred_id):
    if not session.get("vault_unlocked"):
        return jsonify({"error": "Vault is locked"}), 403

    data = request.get_json(silent=True) or {}
    platform = (data.get("platform") or "").strip()
    identifier = (data.get("identifier") or "").strip()
    password = data.get("password") or ""
    notes = (data.get("notes") or "").strip()

    if not platform:
        return jsonify({"error": "Platform name is required"}), 422
    if not identifier:
        return jsonify({"error": "Email or phone number is required"}), 422

    try:
        cred = update_credential(cred_id, platform=platform, identifier=identifier, password=password, notes=notes)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404

    return jsonify(cred.to_dict())


@app.route("/api/vault/credentials/<int:cred_id>", methods=["DELETE"])
def api_vault_delete_credential(cred_id):
    if not session.get("vault_unlocked"):
        return jsonify({"error": "Vault is locked"}), 403

    try:
        delete_credential(cred_id)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404

    return jsonify({"message": f"Credential {cred_id} deleted successfully"})


# ---------------------------------------------------------------------------
# API – My Files (Notepad, Excel, CSV, Images)
# ---------------------------------------------------------------------------

@app.route("/api/files", methods=["GET"])
def api_list_files():
    category = request.args.get("category", "all")
    q = request.args.get("q", "").strip() or None
    files = get_all_files(category=category, search=q)
    return jsonify([f.to_dict() for f in files])


@app.route("/api/files/upload", methods=["POST"])
def api_upload_files():
    uploaded_files = request.files.getlist("files") or request.files.getlist("file")
    if not uploaded_files or (len(uploaded_files) == 1 and uploaded_files[0].filename == ""):
        return jsonify({"error": "No files provided for upload"}), 400

    saved_items = []
    for file in uploaded_files:
        if not file.filename:
            continue
        orig_name = secure_filename(file.filename) or f"file_{uuid.uuid4().hex[:6]}"
        ext = orig_name.rsplit(".", 1)[-1].lower() if "." in orig_name else ""
        stored_name = f"{uuid.uuid4().hex[:12]}_{orig_name}"
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], stored_name)
        file.save(save_path)

        file_size = os.path.getsize(save_path)
        mime = file.mimetype or mimetypes.guess_type(orig_name)[0] or "application/octet-stream"
        item = create_file_item(
            original_name=orig_name,
            stored_name=stored_name,
            extension=ext,
            mime_type=mime,
            file_size=file_size,
        )
        saved_items.append(item.to_dict())

    return jsonify({"message": f"Uploaded {len(saved_items)} file(s)", "files": saved_items}), 201


@app.route("/api/files/create", methods=["POST"])
def api_create_file():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    content = data.get("content") or ""
    file_type = (data.get("type") or "notepad").lower()

    if not name:
        return jsonify({"error": "File name is required"}), 422

    # Ensure appropriate extension
    if "." not in name:
        if file_type == "csv":
            name += ".csv"
        else:
            name += ".txt"

    orig_name = secure_filename(name) or f"new_file_{uuid.uuid4().hex[:6]}.txt"
    ext = orig_name.rsplit(".", 1)[-1].lower() if "." in orig_name else ""
    stored_name = f"{uuid.uuid4().hex[:12]}_{orig_name}"
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], stored_name)

    with open(save_path, "w", encoding="utf-8") as f:
        f.write(content)

    file_size = os.path.getsize(save_path)
    mime = mimetypes.guess_type(orig_name)[0] or "text/plain"
    item = create_file_item(
        original_name=orig_name,
        stored_name=stored_name,
        extension=ext,
        mime_type=mime,
        file_size=file_size,
    )
    return jsonify(item.to_dict()), 201


@app.route("/api/files/<int:file_id>/content", methods=["GET"])
def api_get_file_content(file_id):
    item = get_file_item(file_id)
    if not item:
        return jsonify({"error": f"File {file_id} not found"}), 404

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], item.stored_name)
    if not os.path.exists(file_path):
        return jsonify({"error": "File missing from disk"}), 404

    # Only text/code/csv/json/notepad files can be edited as text
    if item.file_type not in ("notepad", "csv") and item.extension not in ("txt", "csv", "json", "md", "py", "html", "css", "js", "log"):
        return jsonify({"error": "This file type cannot be opened in the text editor"}), 400

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, "r", encoding="latin-1") as f:
                content = f.read()
        except Exception as exc:
            return jsonify({"error": f"Could not read file: {exc}"}), 500

    return jsonify({
        "id": item.id,
        "name": item.original_name,
        "extension": item.extension,
        "type": item.file_type,
        "size": item.file_size,
        "content": content,
    })


@app.route("/api/files/<int:file_id>", methods=["PUT"])
def api_update_file_content(file_id):
    item = get_file_item(file_id)
    if not item:
        return jsonify({"error": f"File {file_id} not found"}), 404

    data = request.get_json(silent=True) or {}
    content = data.get("content")
    new_name = (data.get("name") or "").strip()

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], item.stored_name)

    if content is not None:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            new_size = os.path.getsize(file_path)
            item = update_file_item(file_id, file_size=new_size)
        except Exception as exc:
            return jsonify({"error": f"Failed to save file: {exc}"}), 500

    if new_name and new_name != item.original_name:
        safe_new_name = secure_filename(new_name) or item.original_name
        item = update_file_item(file_id, original_name=safe_new_name)

    return jsonify(item.to_dict())


@app.route("/api/files/<int:file_id>/binary", methods=["PUT"])
def api_update_file_binary(file_id):
    item = get_file_item(file_id)
    if not item:
        return jsonify({"error": f"File {file_id} not found"}), 404

    data = request.get_json(silent=True) or {}
    b64_content = data.get("base64_content")
    if not b64_content:
        return jsonify({"error": "No base64_content provided"}), 400

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], item.stored_name)

    try:
        binary_data = base64.b64decode(b64_content)
        with open(file_path, "wb") as f:
            f.write(binary_data)
        new_size = os.path.getsize(file_path)
        item = update_file_item(file_id, file_size=new_size)
    except Exception as exc:
        return jsonify({"error": f"Failed to save binary file: {exc}"}), 500

    return jsonify(item.to_dict())


@app.route("/api/files/<int:file_id>/download", methods=["GET"])
def api_download_file(file_id):
    item = get_file_item(file_id)
    if not item:
        return jsonify({"error": f"File {file_id} not found"}), 404

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        item.stored_name,
        as_attachment=True,
        download_name=item.original_name,
    )


@app.route("/api/files/<int:file_id>/raw", methods=["GET"])
def api_raw_file(file_id):
    item = get_file_item(file_id)
    if not item:
        return jsonify({"error": f"File {file_id} not found"}), 404

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        item.stored_name,
        as_attachment=False,
        mimetype=item.mime_type,
    )


@app.route("/api/files/<int:file_id>", methods=["DELETE"])
def api_delete_file(file_id):
    item = get_file_item(file_id)
    if not item:
        return jsonify({"error": f"File {file_id} not found"}), 404

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], item.stored_name)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass

    delete_file_item(file_id)
    return jsonify({"message": f"File {file_id} deleted successfully"})


# ---------------------------------------------------------------------------
# API – Export single note as .txt
# ---------------------------------------------------------------------------

@app.route("/api/notes/<int:note_id>/export", methods=["GET"])
def api_export_note(note_id):
    note = get_note(note_id)
    if note is None:
        return jsonify({"error": f"Note {note_id} not found"}), 404

    text_content = (
        f"Heading: {note.heading}\n"
        f"Created: {note.created_at.isoformat()}Z\n"
        f"Updated: {note.updated_at.isoformat()}Z\n"
        f"\n{'-' * 60}\n\n"
        f"{note.content}\n"
    )
    buffer = io.BytesIO(text_content.encode("utf-8"))
    safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in note.heading)
    filename = f"{safe_name[:50]}.txt"
    return send_file(
        buffer,
        mimetype="text/plain",
        as_attachment=True,
        download_name=filename,
    )


# ---------------------------------------------------------------------------
# API – Backup export / import
# ---------------------------------------------------------------------------

@app.route("/api/backup/export", methods=["GET"])
def api_backup_export():
    notes = get_all_notes(sort="created")
    credentials = get_all_credentials()
    now = utc_now()
    payload = {
        "version": "1.0",
        "exported_at": now.isoformat() + "Z",
        "notes": [n.to_dict() for n in notes],
        "credentials": [c.to_dict() for c in credentials],
    }
    json_bytes = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
    buffer = io.BytesIO(json_bytes)
    filename = f"smart-notepad-backup-{now.strftime('%Y%m%d-%H%M%S')}.json"
    return send_file(
        buffer,
        mimetype="application/json",
        as_attachment=True,
        download_name=filename,
    )


@app.route("/api/backup/import", methods=["POST"])
def api_backup_import():
    if "file" not in request.files and "backup" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files.get("file") or request.files.get("backup")
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    if not file.filename.lower().endswith(".json"):
        return jsonify({"error": "Only .json backup files are accepted"}), 400

    try:
        raw = file.read().decode("utf-8")
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return jsonify({"error": f"Invalid JSON file: {exc}"}), 400

    notes_data = payload.get("notes")
    if not isinstance(notes_data, list):
        return jsonify({"error": "Backup file must contain a 'notes' list"}), 422

    imported = 0
    skipped = 0
    for item in notes_data:
        heading = (item.get("heading") or "").strip()
        content = (item.get("content") or "").strip()
        if not heading:
            skipped += 1
            continue
        try:
            created_at = datetime.fromisoformat(
                item["created_at"].rstrip("Z")
            ) if item.get("created_at") else utc_now()
            updated_at = datetime.fromisoformat(
                item["updated_at"].rstrip("Z")
            ) if item.get("updated_at") else utc_now()
        except (ValueError, KeyError):
            created_at = updated_at = utc_now()

        note = Note(
            heading=heading,
            content=content,
            created_at=created_at,
            updated_at=updated_at,
        )
        db.session.add(note)
        imported += 1

    # Import credentials if present
    creds_imported = 0
    creds_data = payload.get("credentials")
    if isinstance(creds_data, list):
        for c in creds_data:
            platform = (c.get("platform") or "").strip()
            identifier = (c.get("identifier") or "").strip()
            password = c.get("password") or ""
            notes = c.get("notes") or ""
            if platform and identifier:
                create_credential(platform, identifier, password, notes)
                creds_imported += 1

    db.session.commit()
    return jsonify(
        {
            "message": "Backup imported successfully",
            "imported": imported,
            "skipped": skipped,
            "credentials_imported": creds_imported,
        }
    )


# ---------------------------------------------------------------------------
# API – Delete ALL notes (used by settings danger zone)
# ---------------------------------------------------------------------------

@app.route("/api/notes/delete_all", methods=["DELETE"])
def api_delete_all_notes():
    count = Note.query.count()
    Note.query.delete()
    db.session.commit()
    return jsonify({"message": f"Deleted {count} note(s) successfully", "count": count})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)
