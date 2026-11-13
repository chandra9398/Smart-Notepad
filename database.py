"""
database.py – SQLAlchemy models and helper functions for Smart Notepad.
"""

from datetime import datetime, timezone
from werkzeug.security import check_password_hash, generate_password_hash

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    heading = db.Column(db.String(255), nullable=False, default="Untitled")
    content = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "heading": self.heading,
            "content": self.content,
            "created_at": self.created_at.isoformat() + "Z",
            "updated_at": self.updated_at.isoformat() + "Z",
        }

    def __repr__(self):
        return f"<Note id={self.id} heading={self.heading!r}>"


class VaultConfig(db.Model):
    __tablename__ = "vault_config"

    id = db.Column(db.Integer, primary_key=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class Credential(db.Model):
    __tablename__ = "credentials"

    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(150), nullable=False)
    identifier = db.Column(db.String(255), nullable=False)  # email or phone number
    password = db.Column(db.String(500), nullable=False)
    notes = db.Column(db.Text, nullable=True, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "platform": self.platform,
            "identifier": self.identifier,
            "password": self.password,
            "notes": self.notes or "",
            "created_at": self.created_at.isoformat() + "Z",
            "updated_at": self.updated_at.isoformat() + "Z",
        }

    def __repr__(self):
        return f"<Credential id={self.id} platform={self.platform!r} identifier={self.identifier!r}>"


class FileItem(db.Model):
    __tablename__ = "files"

    id = db.Column(db.Integer, primary_key=True)
    original_name = db.Column(db.String(255), nullable=False)
    stored_name = db.Column(db.String(255), nullable=False, unique=True)
    extension = db.Column(db.String(20), nullable=False, default="")
    file_type = db.Column(db.String(50), nullable=False, default="other")  # notepad, excel, csv, image, other
    mime_type = db.Column(db.String(100), nullable=False, default="application/octet-stream")
    file_size = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "original_name": self.original_name,
            "stored_name": self.stored_name,
            "extension": self.extension,
            "file_type": self.file_type,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "created_at": self.created_at.isoformat() + "Z",
            "updated_at": self.updated_at.isoformat() + "Z",
        }

    def __repr__(self):
        return f"<FileItem id={self.id} name={self.original_name!r}>"


# ---------------------------------------------------------------------------
# Initialiser
# ---------------------------------------------------------------------------

def init_db(app):
    """Bind SQLAlchemy to *app* and create all tables."""
    db.init_app(app)
    with app.app_context():
        db.create_all()


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_all_notes(sort="updated"):
    """Return all notes ordered by *sort* ('updated' or 'created'), newest first."""
    if sort == "created":
        return Note.query.order_by(Note.created_at.desc()).all()
    # Default: sort by last updated
    return Note.query.order_by(Note.updated_at.desc()).all()


def get_note(note_id):
    """Return a single Note by primary key, or None."""
    return db.session.get(Note, note_id)


def create_note(heading, content):
    """Insert a new Note and return it."""
    now = utc_now()
    note = Note(heading=heading, content=content, created_at=now, updated_at=now)
    db.session.add(note)
    db.session.commit()
    return note


def update_note(note_id, heading, content):
    """Update an existing Note; raises ValueError if not found."""
    note = db.session.get(Note, note_id)
    if note is None:
        raise ValueError(f"Note {note_id} not found")
    note.heading = heading
    note.content = content
    note.updated_at = utc_now()
    db.session.commit()
    return note


def delete_note(note_id):
    """Delete a Note by id; raises ValueError if not found."""
    note = db.session.get(Note, note_id)
    if note is None:
        raise ValueError(f"Note {note_id} not found")
    db.session.delete(note)
    db.session.commit()


def search_notes(query):
    """Full-text search across heading and content (case-insensitive)."""
    pattern = f"%{query}%"
    return (
        Note.query.filter(
            db.or_(
                Note.heading.ilike(pattern),
                Note.content.ilike(pattern),
            )
        )
        .order_by(Note.updated_at.desc())
        .all()
    )


# ---------------------------------------------------------------------------
# Vault (Password Manager) Helpers
# ---------------------------------------------------------------------------

def is_vault_setup():
    """Return True if a master password has been established."""
    return db.session.query(VaultConfig).first() is not None


def set_vault_password(password):
    """Set or update the master vault password."""
    cfg = db.session.query(VaultConfig).first()
    hashed = generate_password_hash(password)
    if cfg is None:
        cfg = VaultConfig(password_hash=hashed)
        db.session.add(cfg)
    else:
        cfg.password_hash = hashed
        cfg.updated_at = utc_now()
    db.session.commit()
    return True


def verify_vault_password(password):
    """Check master password against the stored hash."""
    cfg = db.session.query(VaultConfig).first()
    if cfg is None:
        return False
    return check_password_hash(cfg.password_hash, password)


def get_all_credentials(search=None):
    """Return list of credentials, optionally filtered by search term."""
    q = Credential.query
    if search:
        pattern = f"%{search}%"
        q = q.filter(
            db.or_(
                Credential.platform.ilike(pattern),
                Credential.identifier.ilike(pattern),
                Credential.notes.ilike(pattern),
            )
        )
    return q.order_by(Credential.platform.asc()).all()


def get_credential(cred_id):
    """Return a single credential by primary key."""
    return db.session.get(Credential, cred_id)


def create_credential(platform, identifier, password, notes=""):
    """Create and return a new stored credential."""
    now = utc_now()
    cred = Credential(
        platform=platform,
        identifier=identifier,
        password=password,
        notes=notes or "",
        created_at=now,
        updated_at=now,
    )
    db.session.add(cred)
    db.session.commit()
    return cred


def update_credential(cred_id, platform, identifier, password, notes=""):
    """Update an existing credential; raises ValueError if not found."""
    cred = db.session.get(Credential, cred_id)
    if cred is None:
        raise ValueError(f"Credential {cred_id} not found")
    cred.platform = platform
    cred.identifier = identifier
    cred.password = password
    cred.notes = notes or ""
    cred.updated_at = utc_now()
    db.session.commit()
    return cred


def delete_credential(cred_id):
    """Delete a credential by primary key; raises ValueError if not found."""
    cred = db.session.get(Credential, cred_id)
    if cred is None:
        raise ValueError(f"Credential {cred_id} not found")
    db.session.delete(cred)
    db.session.commit()


# ---------------------------------------------------------------------------
# My Files (Documents, Excel, CSV, Images) Helpers
# ---------------------------------------------------------------------------

NOTEPAD_EXTENSIONS = {
    "txt", "md", "json", "py", "js", "html", "css", "log", "xml",
    "yaml", "yml", "ini", "cfg", "conf", "sql", "sh", "bat", "env",
}
CSV_EXTENSIONS = {"csv", "tsv"}
EXCEL_EXTENSIONS = {"xlsx", "xls", "xlsm", "xlsb"}
IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "svg", "bmp", "ico", "tiff"}
PDF_EXTENSIONS = {"pdf"}


def categorize_file_extension(ext):
    """Categorize file extension into notepad, csv, excel, image, pdf, or other."""
    clean_ext = (ext or "").lower().lstrip(".")
    if clean_ext in NOTEPAD_EXTENSIONS:
        return "notepad"
    if clean_ext in CSV_EXTENSIONS:
        return "csv"
    if clean_ext in EXCEL_EXTENSIONS:
        return "excel"
    if clean_ext in IMAGE_EXTENSIONS:
        return "image"
    if clean_ext in PDF_EXTENSIONS:
        return "pdf"
    return "other"


def get_all_files(category=None, search=None):
    """Return all FileItems, optionally filtered by category and search term."""
    q = FileItem.query
    if category and category != "all":
        q = q.filter(FileItem.file_type == category)
    if search:
        pattern = f"%{search}%"
        q = q.filter(FileItem.original_name.ilike(pattern))
    return q.order_by(FileItem.updated_at.desc()).all()


def get_file_item(file_id):
    """Retrieve FileItem by id."""
    return db.session.get(FileItem, file_id)


def create_file_item(original_name, stored_name, extension, mime_type, file_size):
    """Insert new FileItem record."""
    file_type = categorize_file_extension(extension)
    now = utc_now()
    item = FileItem(
        original_name=original_name,
        stored_name=stored_name,
        extension=extension.lower().lstrip("."),
        file_type=file_type,
        mime_type=mime_type or "application/octet-stream",
        file_size=file_size,
        created_at=now,
        updated_at=now,
    )
    db.session.add(item)
    db.session.commit()
    return item


def update_file_item(file_id, file_size=None, original_name=None):
    """Update FileItem size or name; raises ValueError if not found."""
    item = db.session.get(FileItem, file_id)
    if item is None:
        raise ValueError(f"File {file_id} not found")
    if file_size is not None:
        item.file_size = file_size
    if original_name is not None:
        item.original_name = original_name
        item.extension = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
        item.file_type = categorize_file_extension(item.extension)
    item.updated_at = utc_now()
    db.session.commit()
    return item


def delete_file_item(file_id):
    """Delete FileItem record; raises ValueError if not found."""
    item = db.session.get(FileItem, file_id)
    if item is None:
        raise ValueError(f"File {file_id} not found")
    db.session.delete(item)
    db.session.commit()
