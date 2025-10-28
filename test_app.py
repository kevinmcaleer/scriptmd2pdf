import pytest
import io
import time
from fastapi.testclient import TestClient
from app import app

@pytest.fixture(autouse=True)
def reset_rate_limit():
    # Yield to run the test
    yield
    # Wait a bit between tests to avoid rate limit issues
    time.sleep(0.1)

client = TestClient(app, raise_server_exceptions=False)


class TestHealthEndpoint:
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestIndexEndpoint:
    def test_index_returns_html(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert b"ScriptMD2PDF" in response.content
        assert b"Markdown to Screenplay" in response.content


class TestFileConversion:
    def test_convert_valid_markdown_file(self):
        md_content = b"""### INT. TEST SCENE - DAY

Test action paragraph.

@ALEX
Hello, world!
"""
        files = {"file": ("test.md", io.BytesIO(md_content), "text/markdown")}
        data = {"font_size": "12", "use_vector": "true"}

        response = client.post("/convert", files=files, data=data)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert len(response.content) > 0
        assert response.content[:4] == b"%PDF"

    def test_convert_with_custom_title(self):
        md_content = b"### INT. ROOM - DAY\n\nAction."
        files = {"file": ("test.md", io.BytesIO(md_content), "text/markdown")}
        data = {"title": "My Custom Title", "font_size": "12"}

        response = client.post("/convert", files=files, data=data)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_convert_with_custom_font_size(self):
        md_content = b"### INT. ROOM - DAY\n\nAction."
        files = {"file": ("test.md", io.BytesIO(md_content), "text/markdown")}
        data = {"font_size": "14"}

        response = client.post("/convert", files=files, data=data)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_convert_invalid_file_type(self):
        files = {"file": ("test.pdf", io.BytesIO(b"fake pdf"), "application/pdf")}

        response = client.post("/convert", files=files)

        assert response.status_code == 400
        assert "Only .md or .txt files" in response.json()["detail"]

    def test_convert_file_too_large(self):
        large_content = b"#" * (1048577)  # Just over 1MB
        files = {"file": ("large.md", io.BytesIO(large_content), "text/markdown")}

        response = client.post("/convert", files=files)

        assert response.status_code == 413
        assert "exceeds" in response.json()["detail"]

    def test_convert_invalid_encoding(self):
        invalid_content = b'\xff\xfe\x00\x00'
        files = {"file": ("test.md", io.BytesIO(invalid_content), "text/markdown")}

        response = client.post("/convert", files=files)

        assert response.status_code == 400
        assert "encoding" in response.json()["detail"].lower()

    def test_convert_empty_file(self):
        files = {"file": ("empty.md", io.BytesIO(b""), "text/markdown")}

        response = client.post("/convert", files=files)

        assert response.status_code == 500
        assert "Failed to generate PDF" in response.json()["detail"]


class TestTextConversion:
    def test_convert_text_valid_markdown(self):
        data = {
            "markdown": "### INT. TEST - DAY\n\nAction text.\n\n@ALEX\nDialogue.",
            "title": "Test Script",
            "font_size": 12,
            "use_vector": True
        }

        response = client.post("/convert-text", json=data)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 0
        assert response.content[:4] == b"%PDF"

    def test_convert_text_minimal(self):
        data = {
            "markdown": "### INT. ROOM - DAY\n\nSimple action."
        }

        response = client.post("/convert-text", json=data)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_convert_text_with_raster_rendering(self):
        data = {
            "markdown": "### INT. ROOM - DAY\n\nAction.",
            "use_vector": False
        }

        response = client.post("/convert-text", json=data)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_convert_text_empty_markdown(self):
        data = {
            "markdown": "   \n\n   "
        }

        response = client.post("/convert-text", json=data)

        assert response.status_code == 500
        assert "Failed to generate PDF" in response.json()["detail"]

    def test_convert_text_too_large(self):
        data = {
            "markdown": "A" * (1048577)
        }

        response = client.post("/convert-text", json=data)

        assert response.status_code == 422  # Validation error


class TestRateLimiting:
    def test_rate_limit_enforced(self):
        md_content = b"### INT. ROOM - DAY\n\nAction."
        files = {"file": ("test.md", io.BytesIO(md_content), "text/markdown")}

        responses = []
        for i in range(10):
            response = client.post("/convert", files={"file": ("test.md", io.BytesIO(md_content), "text/markdown")})
            responses.append(response.status_code)

        assert 429 in responses


class TestEdgeCases:
    def test_convert_complex_screenplay(self):
        md_content = b"""### INT. COFFEE SHOP - DAY

ALEX sits at a corner table.

@ALEX
(to barista)
One more coffee, please.

The BARISTA nods.

>> CUT TO:

### EXT. STREET - LATER

! CLOSE ON - COFFEE CUP

Empty.

---

### INT. OFFICE - DAY

@ALEX
I'm done!
"""
        files = {"file": ("complex.md", io.BytesIO(md_content), "text/markdown")}

        response = client.post("/convert", files=files)

        assert response.status_code == 200
        assert len(response.content) > 1000

    def test_convert_unicode_characters(self):
        md_content = "### INT. CAFÉ - DAY\n\n@RENÉ\nBonjour!".encode('utf-8')
        files = {"file": ("unicode.md", io.BytesIO(md_content), "text/markdown")}

        response = client.post("/convert", files=files)

        assert response.status_code == 200

    def test_convert_long_dialogue(self):
        long_dialogue = " ".join(["word"] * 200)
        md_content = f"### INT. ROOM - DAY\n\n@CHARACTER\n{long_dialogue}".encode('utf-8')
        files = {"file": ("long.md", io.BytesIO(md_content), "text/markdown")}

        response = client.post("/convert", files=files)

        assert response.status_code == 200

    def test_convert_many_scenes(self):
        scenes = "\n\n".join([f"### INT. SCENE {i} - DAY\n\nAction {i}." for i in range(50)])
        files = {"file": ("many_scenes.md", io.BytesIO(scenes.encode('utf-8')), "text/markdown")}

        response = client.post("/convert", files=files)

        assert response.status_code == 200


class TestCORS:
    def test_cors_headers_present(self):
        response = client.options("/convert", headers={"Origin": "http://example.com"})
        assert "access-control-allow-origin" in response.headers


class TestContentType:
    def test_pdf_content_type(self):
        md_content = b"### INT. ROOM - DAY\n\nAction."
        files = {"file": ("test.md", io.BytesIO(md_content), "text/markdown")}

        response = client.post("/convert", files=files)

        assert response.headers["content-type"] == "application/pdf"

    def test_pdf_content_disposition(self):
        md_content = b"### INT. ROOM - DAY\n\nAction."
        files = {"file": ("my_script.md", io.BytesIO(md_content), "text/markdown")}

        response = client.post("/convert", files=files)

        assert "attachment" in response.headers["content-disposition"]
        assert "my_script.pdf" in response.headers["content-disposition"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
