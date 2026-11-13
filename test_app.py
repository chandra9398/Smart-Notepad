"""
Comprehensive Test Suite for Smart Notepad
Tests all functional requirements and edge cases.
"""

import io
import json
import unittest
from app import app, db
from database import (
    Credential,
    FileItem,
    Note,
    VaultConfig,
    create_note,
    delete_note,
    get_all_notes,
    get_note,
    search_notes,
    update_note,
)


class SmartNotepadTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        with app.app_context():
            db.create_all()
            Note.query.delete()
            Credential.query.delete()
            VaultConfig.query.delete()
            FileItem.query.delete()
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_pages_render(self):
        """Test that all frontend pages render HTTP 200."""
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Smart Notepad", r.data)

        r = self.client.get("/note/new")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Create New Note", r.data)

        r = self.client.get("/settings")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Settings", r.data)

    def test_create_and_read_note(self):
        """Test note creation and retrieval via API."""
        payload = {"heading": "Project Ideas", "content": "<p>1. AI Notes<br>2. Cloud Sync</p>"}
        r = self.client.post("/api/notes", json=payload)
        self.assertEqual(r.status_code, 201)
        data = r.get_json()
        self.assertEqual(data["heading"], "Project Ideas")
        note_id = data["id"]

        # Read back
        r = self.client.get(f"/api/notes/{note_id}")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["heading"], "Project Ideas")

        # Check editor page for existing note
        r = self.client.get(f"/note/{note_id}")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Edit Note", r.data)

    def test_update_note(self):
        """Test editing/updating note content and heading."""
        r = self.client.post("/api/notes", json={"heading": "Draft", "content": "Initial"})
        note_id = r.get_json()["id"]

        r = self.client.put(f"/api/notes/{note_id}", json={"heading": "Final Draft", "content": "Updated content"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["heading"], "Final Draft")
        self.assertEqual(r.get_json()["content"], "Updated content")

    def test_delete_note(self):
        """Test deleting a note and verifying 404."""
        r = self.client.post("/api/notes", json={"heading": "To Delete", "content": "Temp"})
        note_id = r.get_json()["id"]

        r = self.client.delete(f"/api/notes/{note_id}")
        self.assertEqual(r.status_code, 200)

        r = self.client.get(f"/api/notes/{note_id}")
        self.assertEqual(r.status_code, 404)

    def test_search_notes(self):
        """Test search by heading and content."""
        self.client.post("/api/notes", json={"heading": "Grocery Shopping", "content": "Apples, Milk"})
        self.client.post("/api/notes", json={"heading": "Workout Routine", "content": "Cardio and weights"})

        # Search heading
        r = self.client.get("/api/notes/search?q=Grocery")
        self.assertEqual(r.status_code, 200)
        results = r.get_json()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["heading"], "Grocery Shopping")

        # Search content
        r = self.client.get("/api/notes/search?q=weights")
        self.assertEqual(r.status_code, 200)
        results = r.get_json()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["heading"], "Workout Routine")

    def test_export_txt(self):
        """Test downloading single note as .txt."""
        r = self.client.post("/api/notes", json={"heading": "My Thoughts", "content": "Deep insights here."})
        note_id = r.get_json()["id"]

        r = self.client.get(f"/api/notes/{note_id}/export")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.mimetype, "text/plain")
        self.assertIn(b"Heading: My Thoughts", r.data)
        self.assertIn(b"Deep insights here.", r.data)

    def test_backup_export_and_import(self):
        """Test full database export as JSON and importing it back."""
        self.client.post("/api/notes", json={"heading": "Backup Note 1", "content": "Text 1"})
        self.client.post("/api/notes", json={"heading": "Backup Note 2", "content": "Text 2"})

        # Export backup
        r = self.client.get("/api/backup/export")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.mimetype, "application/json")
        backup = json.loads(r.data)
        self.assertEqual(len(backup["notes"]), 2)

        # Clear database
        self.client.delete("/api/notes/delete_all")
        r = self.client.get("/api/notes")
        self.assertEqual(len(r.get_json()), 0)

        # Import backup
        data_to_send = {"backup": (io.BytesIO(json.dumps(backup).encode("utf-8")), "backup.json")}
        r = self.client.post("/api/backup/import", data=data_to_send, content_type="multipart/form-data")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["imported"], 2)

        # Verify notes restored
        r = self.client.get("/api/notes")
        self.assertEqual(len(r.get_json()), 2)

    def test_security_headers(self):
        """Verify essential security headers are sent on all responses."""
        r = self.client.get("/")
        self.assertEqual(r.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(r.headers.get("X-Frame-Options"), "SAMEORIGIN")
        self.assertEqual(r.headers.get("X-XSS-Protection"), "1; mode=block")

    def test_validation_errors(self):
        """Verify input validation and error responses."""
        # Empty heading
        r = self.client.post("/api/notes", json={"heading": "", "content": "No title"})
        self.assertEqual(r.status_code, 422)

        # Heading too long (>255 chars)
        r = self.client.post("/api/notes", json={"heading": "x" * 300, "content": "Too long"})
        self.assertEqual(r.status_code, 422)

        # Nonexistent note
        r = self.client.get("/api/notes/99999")
        self.assertEqual(r.status_code, 404)

    def test_vault_flow(self):
        """Test the complete password-protected Vault lifecycle."""
        # 1. Initially, vault status should report is_setup=False, is_unlocked=False
        r = self.client.get("/api/vault/status")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.get_json()["is_setup"])
        self.assertFalse(r.get_json()["is_unlocked"])

        # 2. Accessing credentials while locked should return 403 Forbidden
        r = self.client.get("/api/vault/credentials")
        self.assertEqual(r.status_code, 403)

        # 3. Setup master password
        r = self.client.post(
            "/api/vault/setup",
            json={"password": "MyMasterPassword123", "confirm_password": "MyMasterPassword123"},
        )
        self.assertEqual(r.status_code, 201)
        self.assertTrue(r.get_json()["unlocked"])

        # 4. Create new platform credential (platform, email/number, password)
        r = self.client.post(
            "/api/vault/credentials",
            json={
                "platform": "GitHub",
                "identifier": "developer@example.com",
                "password": "SuperSecretGitHubKey!99",
                "notes": "2FA backup keys in safe",
            },
        )
        self.assertEqual(r.status_code, 201)
        data = r.get_json()
        cred_id = data["id"]
        self.assertEqual(data["platform"], "GitHub")
        self.assertEqual(data["identifier"], "developer@example.com")
        self.assertEqual(data["password"], "SuperSecretGitHubKey!99")

        # 5. List credentials (now unlocked)
        r = self.client.get("/api/vault/credentials")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.get_json()), 1)

        # 6. Update credential
        r = self.client.put(
            f"/api/vault/credentials/{cred_id}",
            json={
                "platform": "GitHub Enterprise",
                "identifier": "developer@company.org",
                "password": "NewUpdatedPassword2025!",
                "notes": "Updated account",
            },
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["platform"], "GitHub Enterprise")

        # 7. Lock the vault
        r = self.client.post("/api/vault/lock")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.get_json()["unlocked"])

        # 8. Accessing credentials after lock should be forbidden (403)
        r = self.client.get("/api/vault/credentials")
        self.assertEqual(r.status_code, 403)

        # 9. Try unlocking with wrong password -> 401
        r = self.client.post("/api/vault/unlock", json={"password": "WrongPassword!"})
        self.assertEqual(r.status_code, 401)

        # 10. Unlock with correct password -> 200
        r = self.client.post("/api/vault/unlock", json={"password": "MyMasterPassword123"})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["unlocked"])

        # 11. Delete credential
        r = self.client.delete(f"/api/vault/credentials/{cred_id}")
        self.assertEqual(r.status_code, 200)

        # Verify empty
        r = self.client.get("/api/vault/credentials")
        self.assertEqual(len(r.get_json()), 0)

    def test_files_hub(self):
        """Test file creation, upload, view, edit, save, download, and delete."""
        # 1. Page render
        r = self.client.get("/files")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"My Files", r.data)

        # 2. Create Notepad / text file
        r = self.client.post(
            "/api/files/create",
            json={"name": "meeting_notes.txt", "content": "Action items:\n1. Prepare demo\n2. Ship MVP", "type": "notepad"},
        )
        self.assertEqual(r.status_code, 201)
        txt_file = r.get_json()
        txt_id = txt_file["id"]
        self.assertEqual(txt_file["original_name"], "meeting_notes.txt")
        self.assertEqual(txt_file["file_type"], "notepad")

        # 3. Create CSV file
        r = self.client.post(
            "/api/files/create",
            json={"name": "q4_sales.csv", "content": "Region,Q1,Q2,Q3,Q4\nNorth,100,120,140,200\nSouth,80,95,110,150", "type": "csv"},
        )
        self.assertEqual(r.status_code, 201)
        csv_file = r.get_json()
        csv_id = csv_file["id"]
        self.assertEqual(csv_file["original_name"], "q4_sales.csv")
        self.assertEqual(csv_file["file_type"], "csv")

        # 4. Upload file (simulate image or excel upload)
        dummy_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
        upload_data = {
            "files": (io.BytesIO(dummy_png), "app_icon.png")
        }
        r = self.client.post("/api/files/upload", data=upload_data, content_type="multipart/form-data")
        self.assertEqual(r.status_code, 201)
        uploaded = r.get_json()["files"][0]
        img_id = uploaded["id"]
        self.assertEqual(uploaded["file_type"], "image")

        # 5. List all files
        r = self.client.get("/api/files")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.get_json()), 3)

        # Filter by category
        r = self.client.get("/api/files?category=notepad")
        self.assertEqual(len(r.get_json()), 1)

        r = self.client.get("/api/files?category=csv")
        self.assertEqual(len(r.get_json()), 1)

        r = self.client.get("/api/files?category=image")
        self.assertEqual(len(r.get_json()), 1)

        # 6. Read file content for editing
        r = self.client.get(f"/api/files/{txt_id}/content")
        self.assertEqual(r.status_code, 200)
        self.assertIn("Action items:", r.get_json()["content"])

        # 7. Edit and save file content
        r = self.client.put(
            f"/api/files/{txt_id}",
            json={"content": "Updated content:\nAll action items completed!"},
        )
        self.assertEqual(r.status_code, 200)

        # Verify edited content saved
        r = self.client.get(f"/api/files/{txt_id}/content")
        self.assertEqual(r.get_json()["content"], "Updated content:\nAll action items completed!")

        # 8. Download file
        r = self.client.get(f"/api/files/{txt_id}/download")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers.get("Content-Disposition"), "attachment; filename=meeting_notes.txt")
        self.assertIn(b"All action items completed!", r.data)

        # 9. Raw file endpoint (for image preview)
        r = self.client.get(f"/api/files/{img_id}/raw")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.mimetype, "image/png")

        # 10. Delete file
        r = self.client.delete(f"/api/files/{txt_id}")
        self.assertEqual(r.status_code, 200)

        # Verify deleted
        r = self.client.get(f"/api/files/{txt_id}/content")
        self.assertEqual(r.status_code, 404)

    def test_binary_file_update(self):
        """Test uploading and updating binary files (PDF/XLSX) via /api/files/<id>/binary"""
        import base64

        # 1. Upload sample PDF
        initial_pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< >>\n%%EOF"
        r = self.client.post(
            "/api/files/upload",
            data={"file": (io.BytesIO(initial_pdf_bytes), "sample_doc.pdf")},
            content_type="multipart/form-data",
        )
        self.assertEqual(r.status_code, 201)
        pdf_id = r.get_json()["files"][0]["id"]

        # 2. Update PDF with new binary data via base64 endpoint
        updated_pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Updated true >>\nendobj\ntrailer\n<< >>\n%%EOF"
        b64_payload = base64.b64encode(updated_pdf_bytes).decode("ascii")

        r = self.client.put(
            f"/api/files/{pdf_id}/binary",
            json={"base64_content": b64_payload},
        )
        self.assertEqual(r.status_code, 200)
        resp_json = r.get_json()
        self.assertEqual(resp_json["id"], pdf_id)
        self.assertEqual(resp_json["file_size"], len(updated_pdf_bytes))

        # 3. Download and verify the updated bytes
        r = self.client.get(f"/api/files/{pdf_id}/download")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, updated_pdf_bytes)

        # 4. Clean up
        r = self.client.delete(f"/api/files/{pdf_id}")
        self.assertEqual(r.status_code, 200)


if __name__ == "__main__":
    unittest.main()
