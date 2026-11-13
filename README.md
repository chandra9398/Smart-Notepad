# Smart Notepad 📝

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Flask 3.0](https://img.shields.io/badge/framework-Flask%203.0-green.svg)](https://palletsprojects.com/p/flask/)
[![SQLite](https://img.shields.io/badge/database-SQLite%203-lightgrey.svg)](https://www.sqlite.org/)
[![Bootstrap 5](https://img.shields.io/badge/frontend-Bootstrap%205-purple.svg)](https://getbootstrap.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A modern, fast, and secure personal productivity web application built with **Python Flask** and **SQLite**. Inspired by clean productivity tools like Notion and Google Keep, **Smart Notepad** goes beyond plain notes with an interactive **PDF Reader & Editor**, **Excel (.xlsx) Live Spreadsheet Editor**, encrypted **Password Vault**, and comprehensive **File Hub**.

---

## 🌟 Key Features

### 1. 📝 Rich Notes Editor & Dashboard
- **Contenteditable Rich Text**: Format text seamlessly with headings, bold, italic, underline, strike-through, bullet lists, and ordered lists.
- **Instant Auto-Save**: Real-time debounce auto-saving (3-second buffer) with visual status indicators (*Saved ✓*, *Saving…*, *Unsaved changes*).
- **Live Search**: Instant full-text search across titles and note contents with instant filtering.
- **Single Note Export**: Export individual notes as `.txt` files with 1 click.
- **Custom Sort**: Order notes by Last Updated or Date Created.

### 2. 📁 My Files Hub (Multi-Format Workspace)
- **PDF Reader & Editor**:
  - Embedded multi-page PDF viewer with high fidelity.
  - Interactive PDF annotation and stamping powered by `pdf-lib`.
  - Add custom text notes, stamps (*APPROVED*, *CONFIDENTIAL*, *REVIEWED*, *DRAFT*), set colors, font sizes, and page targets.
  - Save modified PDFs directly back to disk as binary and download them anytime.
- **Excel Spreadsheet (.xlsx) Live Editor**:
  - View and edit `.xlsx` workbooks directly in the browser via `SheetJS`.
  - Full cell editing (`contenteditable`), add rows, delete rows, add columns, and switch between workbook tabs.
  - Direct compile and save back to genuine `.xlsx` format.
- **CSV Data Tables & Text / Code Files**:
  - In-browser code and text editor for `.txt`, `.csv`, `.md`, `.json`, `.py`, `.html`, `.css`, and `.js` with <kbd>Ctrl+S</kbd> hotkey saving.
- **Image Lightbox & Preview**:
  - High-resolution fullscreen lightbox preview and quick download for `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, and `.svg`.
- **Drag & Drop Multi-File Upload**:
  - Upload multiple files simultaneously with category tagging and size tracking.

### 3. 🔐 Password Vault (Credentials Manager)
- **Master Password / PIN Protection**: Secure access requiring a master password before credentials can be unlocked or viewed.
- **Cryptographic Security**: Master password hashed using PBKDF2/SHA-256 via `werkzeug.security`.
- **Store Platform Credentials**: Manage Platform Name, Email or Phone Number, Password, and notes.
- **Mask / Reveal & Copy**: 1-click clipboard copy for email and password fields with visibility toggles.
- **Live Vault Search & Session Timeout**: Lock session anytime or configure automatic timeout.

### 4. ⚙️ Settings, Customization & Backups
- **Theme Switcher**: Smooth transitions between **Dark Mode**, **Light Mode**, and **System Default** (saved in `localStorage`).
- **Full Database Backup (JSON)**: Export your entire database (notes and credentials) into a portable JSON backup file.
- **Restore / Import**: Restore backups with 1 click with validation and duplicate prevention.
- **Danger Zone**: Wipe and reset database with confirmation dialogues.
- **Enterprise Security Headers**: Built-in protection with `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, and `X-XSS-Protection: 1; mode=block`.

---

## 🛠️ Technology Stack

| Layer | Component | Technologies |
| :--- | :--- | :--- |
| **Backend** | REST API & Application Server | Python 3.10+, Flask 3.0.3, Jinja2 |
| **Database** | Persistent ORM Storage | SQLite 3, Flask-SQLAlchemy 3.1.1 |
| **Security & Forms** | Protection & Validation | Flask-WTF 1.2.1, Werkzeug Security (PBKDF2) |
| **Client-side Libraries** | Dynamic In-Browser Document Engines | [SheetJS (xlsx.full.min.js)](https://sheetjs.com/), [pdf-lib](https://pdf-lib.js.org/) |
| **Frontend UI/UX** | Responsive Design & Themes | Bootstrap 5.3, Font Awesome 6.5, Vanilla CSS3 / JavaScript |

---

## 📂 Project Architecture

```
Smart-Notepad/
│
├── app.py                  # Flask application routes, REST API & file handlers
├── config.py               # Development & Production configuration profiles
├── database.py             # SQLAlchemy models (Note, VaultConfig, Credential, FileItem)
├── requirements.txt        # Python dependency manifest
├── test_app.py             # Automated unit & integration test suite (12 tests)
├── README.md               # Project documentation
├── LICENSE                 # MIT License
├── .gitignore              # Git ignore rules for virtualenvs, databases & caches
├── .env.example            # Environment variables template
│
├── instance/               # Local database storage directory
│   ├── .gitkeep
│   └── notes.db            # Auto-generated SQLite database
│
├── uploads/                # Managed user uploaded files
│   └── .gitkeep
│
├── static/
│   ├── css/
│   │   └── style.css       # Custom design system, CSS variables & animations
│   ├── js/
│   │   └── script.js       # Auto-save, theme switcher, modal & toast handlers
│   └── images/
│       ├── logo.svg        # Scalable application brand icon
│       └── logo.png        # Raster application icon
│
└── templates/
    ├── base.html           # Master navigation layout, headers & toast container
    ├── index.html          # Dashboard view with statistics & notes grid
    ├── editor.html         # Rich-text contenteditable note editor
    ├── files.html          # My Files hub with PDF, Excel, and Text live editors
    ├── vault.html          # Password Vault unlock screen & credentials cards
    └── settings.html       # Theme preferences & JSON backup export/import
```

---

## 🚀 Installation & Getting Started

### Prerequisites
- **Python 3.10** or higher ([python.org](https://www.python.org/downloads/))
- **Git** ([git-scm.com](https://git-scm.com/))

### 1. Clone the Repository
```bash
git clone https://github.com/chandra9398/Smart-Notepad.git
cd Smart-Notepad
```

### 2. Set Up a Virtual Environment

#### On Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(If you encounter a PowerShell script execution policy error, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`)*

#### On macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python app.py
```

The database tables are automatically initialized upon startup. Open your browser and navigate to:
👉 **`http://127.0.0.1:5000`** or **`http://localhost:5000`**

---

## 🧪 Running the Automated Test Suite

Smart Notepad includes a comprehensive integration test suite covering page renders, API endpoints, auto-save, PDF/XLSX binary modifications, password vault cryptographic flows, and backup restore:

```bash
python -m unittest test_app.py -v
```

---

## 📸 Screenshots & Interface Walkthrough

```
┌────────────────────────────────────────────────────────────────────────┐
│  Smart Notepad     [Dashboard]  [My Files]  [Password Vault]  [Settings]│
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Welcome back! 📁 5 Files   📝 12 Notes   🔐 8 Accounts   🌙 Theme     │
│                                                                        │
│  [ 🔍 Search notes, headings or files...                     ]         │
│                                                                        │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌───────────────┐ │
│  │ Project Roadmap 2026 │  │ Server Architecture  │  │ Meeting Notes │ │
│  │ Last updated: Today  │  │ Last updated: 2h ago │  │ Updated: Nov13│ │
│  │ -------------------- │  │ -------------------- │  │ ------------- │ │
│  │ Deliver phase 3 ...  │  │ Configured SQLite... │  │ Sync with team│ │
│  │ [Open] [Export .txt] │  │ [Open] [Export .txt] │  │ [Open]        │ │
│  └──────────────────────┘  └──────────────────────┘  └───────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
```

1. **Dashboard (`/`)**: Real-time counters, instant search filter, grid display with card previews, quick export, and creation shortcuts.
2. **Editor (`/note/<id>`)**: Contenteditable canvas with heading input, toolbar for text formatting, auto-save indicator, and word count.
3. **My Files (`/files`)**: File browser segmented into *Notepad*, *Spreadsheets*, *PDF Documents*, and *Images*, with in-browser editing for `.xlsx`, `.pdf`, `.csv`, and `.txt`.
4. **Password Vault (`/vault`)**: PIN/Master password authentication screen protecting platform credentials, email/phone entries, copy buttons, and quick search.
5. **Settings (`/settings`)**: Theme switchers, database backup download (`.json`), backup restore upload, and system information.

---

## 📡 REST API Reference

### Notes Endpoints
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/notes` | List all notes (optional query: `?search=...&sort=updated/created`) |
| `POST` | `/api/notes` | Create a new note (`{"heading": "...", "content": "..."}`) |
| `GET` | `/api/notes/<id>` | Retrieve note by ID |
| `PUT` | `/api/notes/<id>` | Update note heading or content (triggers auto-save) |
| `DELETE` | `/api/notes/<id>` | Permanently delete note |
| `GET` | `/api/notes/<id>/export` | Download note as standalone `.txt` file |

### My Files Endpoints
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/files` | List uploaded files (`?category=notepad|excel|csv|pdf|image`) |
| `POST` | `/api/files/upload` | Upload multiple files via `multipart/form-data` |
| `GET` | `/api/files/<id>/content` | Fetch text content for in-browser editing |
| `PUT` | `/api/files/<id>` | Save updated text content |
| `PUT` | `/api/files/<id>/binary` | Save modified binary files (`{"base64_content": "..."}`) for PDF & Excel |
| `GET` | `/api/files/<id>/raw` | Stream raw file for PDF viewer & image previews |
| `GET` | `/api/files/<id>/download` | Download original or updated file |
| `DELETE` | `/api/files/<id>` | Delete file from database and disk |

### Password Vault Endpoints
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/vault/status` | Check if master password is initialized and vault is unlocked |
| `POST` | `/api/vault/setup` | Set master password for the first time |
| `POST` | `/api/vault/unlock` | Verify master password and establish unlocked session |
| `POST` | `/api/vault/lock` | Terminate vault session immediately |
| `GET` | `/api/vault/credentials` | List saved platform credentials (requires unlocked session) |
| `POST` | `/api/vault/credentials` | Add new credential (`platform`, `account_identifier`, `password`) |
| `PUT` | `/api/vault/credentials/<id>` | Update existing credential |
| `DELETE` | `/api/vault/credentials/<id>` | Delete credential |

### Backup Endpoints
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/backup/export` | Download complete database export in JSON format |
| `POST` | `/api/backup/import` | Upload and restore database from JSON file |

---

## 🔒 Security Best Practices

- **Zero Hardcoded Secrets**: Default development keys are overridable via environment variables (`SECRET_KEY`, `DATABASE_URL`).
- **SQL Injection Prevention**: SQLAlchemy parameterized queries across all database operations.
- **XSS & File Sanitization**: All file uploads are sanitized via `werkzeug.utils.secure_filename` with random UUID prefixes to prevent directory traversal attacks.
- **CSRF Token Validation**: Integrated CSRF protection with Flask-WTF.
- **Isolated Vault Access**: Sensitive credential endpoints strictly enforce server-side session checks (`session.get("vault_unlocked")`).

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

Developed by **Malepati Chandra Obul Reddy** ([@chandra9398](https://github.com/chandra9398))
