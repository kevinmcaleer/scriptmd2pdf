import os
import io
import tempfile
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Form
from fastapi.responses import Response, HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, Field
import uvicorn

from screenmd2pdf import (
    parse_screenplay_markdown,
    draw_pdf_vector,
    draw_pdf,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 1048576))
RATE_LIMIT = os.getenv("RATE_LIMIT", "5/minute")

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="ScriptMD2PDF API",
    description="Convert screenplay-flavored Markdown to PDF",
    version="1.0.0"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConvertRequest(BaseModel):
    markdown: str = Field(..., max_length=MAX_FILE_SIZE)
    title: Optional[str] = Field(None, max_length=200)
    font_size: int = Field(12, ge=8, le=24)
    use_vector: bool = Field(True)


@app.get("/", response_class=HTMLResponse)
async def index():
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ScriptMD2PDF - Markdown to Screenplay Converter</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }

        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
        }

        .content {
            padding: 30px;
        }

        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }

        .tab {
            padding: 10px 20px;
            cursor: pointer;
            background: none;
            border: none;
            font-size: 1em;
            color: #666;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
        }

        .tab:hover {
            color: #667eea;
        }

        .tab.active {
            color: #667eea;
            border-bottom-color: #667eea;
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        .upload-area {
            border: 3px dashed #667eea;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            background: #f8f9ff;
            transition: all 0.3s;
            cursor: pointer;
        }

        .upload-area:hover,
        .upload-area.dragover {
            background: #e8ebff;
            border-color: #764ba2;
        }

        .upload-icon {
            font-size: 3em;
            margin-bottom: 20px;
        }

        textarea {
            width: 100%;
            min-height: 400px;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            resize: vertical;
        }

        textarea:focus {
            outline: none;
            border-color: #667eea;
        }

        .options {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }

        .option-group {
            display: flex;
            flex-direction: column;
        }

        label {
            font-weight: 600;
            margin-bottom: 5px;
            color: #555;
        }

        input[type="text"],
        input[type="number"],
        select {
            padding: 10px;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            font-size: 14px;
        }

        input[type="text"]:focus,
        input[type="number"]:focus,
        select:focus {
            outline: none;
            border-color: #667eea;
        }

        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        input[type="checkbox"] {
            width: 20px;
            height: 20px;
            cursor: pointer;
        }

        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 5px;
            font-size: 1.1em;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            width: 100%;
            margin-top: 20px;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }

        .btn:active {
            transform: translateY(0);
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .message {
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            display: none;
        }

        .message.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }

        .message.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }

        .syntax-guide {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin-top: 20px;
        }

        .syntax-guide h3 {
            margin-bottom: 15px;
            color: #667eea;
        }

        .syntax-guide code {
            background: #e9ecef;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }

        .syntax-guide ul {
            list-style-position: inside;
            margin-left: 20px;
        }

        .syntax-guide li {
            margin: 8px 0;
        }

        .spinner {
            display: none;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .hidden {
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>ScriptMD2PDF</h1>
            <p class="subtitle">Convert Markdown to Professional Screenplay PDFs</p>
        </header>

        <div class="content">
            <div class="tabs">
                <button class="tab active" onclick="switchTab('upload')">Upload File</button>
                <button class="tab" onclick="switchTab('editor')">Text Editor</button>
                <button class="tab" onclick="switchTab('guide')">Syntax Guide</button>
            </div>

            <div id="upload-tab" class="tab-content active">
                <div class="upload-area" id="dropZone">
                    <div class="upload-icon">📄</div>
                    <h3>Drag & Drop your Markdown file here</h3>
                    <p>or click to browse</p>
                    <input type="file" id="fileInput" accept=".md,.txt" style="display: none;">
                </div>

                <div class="options">
                    <div class="option-group">
                        <label for="uploadTitle">Title (optional):</label>
                        <input type="text" id="uploadTitle" placeholder="Auto-detected from filename">
                    </div>
                    <div class="option-group">
                        <label for="uploadFontSize">Font Size:</label>
                        <input type="number" id="uploadFontSize" value="12" min="8" max="24">
                    </div>
                    <div class="option-group checkbox-group">
                        <input type="checkbox" id="uploadUseVector" checked>
                        <label for="uploadUseVector">Use vector rendering (better quality)</label>
                    </div>
                </div>

                <button class="btn" id="uploadBtn" onclick="convertFile()" disabled>Convert to PDF</button>
                <div class="spinner" id="uploadSpinner"></div>
                <div class="message" id="uploadMessage"></div>
            </div>

            <div id="editor-tab" class="tab-content">
                <textarea id="markdownEditor" placeholder="Paste or type your screenplay Markdown here...

Example:
### INT. COFFEE SHOP - DAY

ALEX sits at a corner table.

@ALEX
(to barista)
One more coffee, please.

>> CUT TO:
"></textarea>

                <div class="options">
                    <div class="option-group">
                        <label for="editorTitle">Title (optional):</label>
                        <input type="text" id="editorTitle" placeholder="My Screenplay">
                    </div>
                    <div class="option-group">
                        <label for="editorFontSize">Font Size:</label>
                        <input type="number" id="editorFontSize" value="12" min="8" max="24">
                    </div>
                    <div class="option-group checkbox-group">
                        <input type="checkbox" id="editorUseVector" checked>
                        <label for="editorUseVector">Use vector rendering (better quality)</label>
                    </div>
                </div>

                <button class="btn" id="editorBtn" onclick="convertText()">Convert to PDF</button>
                <div class="spinner" id="editorSpinner"></div>
                <div class="message" id="editorMessage"></div>
            </div>

            <div id="guide-tab" class="tab-content">
                <div class="syntax-guide">
                    <h3>Markdown Syntax Guide</h3>

                    <h4>Scene Headings</h4>
                    <ul>
                        <li><code>### INT. LOCATION - DAY</code> - Scene heading (slugline)</li>
                        <li>Will be rendered in bold, uppercase</li>
                    </ul>

                    <h4>Action</h4>
                    <ul>
                        <li>Plain paragraphs become action text</li>
                        <li>Separate paragraphs with blank lines</li>
                    </ul>

                    <h4>Dialogue</h4>
                    <ul>
                        <li><code>@CHARACTER</code> - Character cue (name will be uppercase)</li>
                        <li><code>(whispering)</code> - Parenthetical direction</li>
                        <li>Dialogue lines follow the character cue</li>
                        <li>End dialogue with a blank line</li>
                    </ul>

                    <h4>Transitions</h4>
                    <ul>
                        <li><code>>> CUT TO:</code> - Right-aligned transition</li>
                        <li>Colon added automatically if missing</li>
                    </ul>

                    <h4>Shot Headings</h4>
                    <ul>
                        <li><code>! CLOSE ON</code> - Camera direction or shot description</li>
                    </ul>

                    <h4>Other</h4>
                    <ul>
                        <li><code>---</code> - Force page break</li>
                        <li><code>// Comment</code> - Comments (ignored)</li>
                        <li><code>> Note</code> - Notes/blockquotes (ignored)</li>
                    </ul>

                    <h3>Example Screenplay</h3>
                    <pre style="background: #e9ecef; padding: 15px; border-radius: 5px; overflow-x: auto;"><code>### INT. COFFEE SHOP - DAY

The morning rush is in full swing.

@ALEX
(to barista)
Large coffee, please.

@BARISTA
Coming right up.

>> CUT TO:

! CLOSE ON - COFFEE CUP

Steam rises from the fresh brew.

---

### INT. ALEX'S APARTMENT - LATER

Alex works at the laptop.</code></pre>
                </div>
            </div>
        </div>
    </div>

    <script>
        let selectedFile = null;

        function switchTab(tabName) {
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

            event.target.classList.add('active');
            document.getElementById(tabName + '-tab').classList.add('active');
        }

        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const uploadBtn = document.getElementById('uploadBtn');

        dropZone.addEventListener('click', () => fileInput.click());

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFile(files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFile(e.target.files[0]);
            }
        });

        function handleFile(file) {
            if (!file.name.match(/\\.(md|txt)$/i)) {
                showMessage('upload', 'error', 'Please select a Markdown (.md) or text (.txt) file');
                return;
            }

            if (file.size > 1048576) {
                showMessage('upload', 'error', 'File size must be less than 1MB');
                return;
            }

            selectedFile = file;
            uploadBtn.disabled = false;
            dropZone.innerHTML = `
                <div class="upload-icon">✓</div>
                <h3>${file.name}</h3>
                <p>Ready to convert</p>
            `;

            if (!document.getElementById('uploadTitle').value) {
                const title = file.name.replace(/\.(md|txt)$/i, '').replace(/_/g, ' ');
                document.getElementById('uploadTitle').value = title;
            }
        }

        async function convertFile() {
            if (!selectedFile) return;

            const formData = new FormData();
            formData.append('file', selectedFile);

            const title = document.getElementById('uploadTitle').value;
            const fontSize = document.getElementById('uploadFontSize').value;
            const useVector = document.getElementById('uploadUseVector').checked;

            if (title) formData.append('title', title);
            formData.append('font_size', fontSize);
            formData.append('use_vector', useVector);

            await convert('/convert', formData, 'upload');
        }

        async function convertText() {
            const markdown = document.getElementById('markdownEditor').value.trim();

            if (!markdown) {
                showMessage('editor', 'error', 'Please enter some Markdown text');
                return;
            }

            const data = {
                markdown: markdown,
                title: document.getElementById('editorTitle').value || null,
                font_size: parseInt(document.getElementById('editorFontSize').value),
                use_vector: document.getElementById('editorUseVector').checked
            };

            await convert('/convert-text', data, 'editor', false);
        }

        async function convert(endpoint, data, prefix, isFormData = true) {
            const btn = document.getElementById(prefix + 'Btn');
            const spinner = document.getElementById(prefix + 'Spinner');
            const message = document.getElementById(prefix + 'Message');

            btn.disabled = true;
            spinner.style.display = 'block';
            message.style.display = 'none';

            try {
                const options = {
                    method: 'POST',
                    body: isFormData ? data : JSON.stringify(data)
                };

                if (!isFormData) {
                    options.headers = { 'Content-Type': 'application/json' };
                }

                const response = await fetch(endpoint, options);

                if (response.status === 429) {
                    throw new Error('Rate limit exceeded. Please wait a minute and try again.');
                }

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Conversion failed');
                }

                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'screenplay.pdf';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);

                showMessage(prefix, 'success', 'PDF generated successfully!');
            } catch (error) {
                showMessage(prefix, 'error', error.message);
            } finally {
                btn.disabled = false;
                spinner.style.display = 'none';
            }
        }

        function showMessage(prefix, type, text) {
            const message = document.getElementById(prefix + 'Message');
            message.className = 'message ' + type;
            message.textContent = text;
            message.style.display = 'block';

            if (type === 'success') {
                setTimeout(() => {
                    message.style.display = 'none';
                }, 5000);
            }
        }
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/convert")
@limiter.limit(RATE_LIMIT)
async def convert_file(
    request: Request,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    font_size: int = Form(12),
    use_vector: bool = Form(True)
):
    logger.info(f"Conversion request from {get_remote_address(request)}: {file.filename}")

    if not file.filename.endswith(('.md', '.txt')):
        raise HTTPException(status_code=400, detail="Only .md or .txt files are allowed")

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File size exceeds {MAX_FILE_SIZE} bytes")

    try:
        markdown_text = content.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid UTF-8 encoding")

    if not title:
        title = Path(file.filename).stem.replace('_', ' ').title()

    try:
        pdf_bytes = generate_pdf(markdown_text, title, font_size, use_vector)

        logger.info(f"Successfully generated PDF for {file.filename}")

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{Path(file.filename).stem}.pdf"'
            }
        )
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate PDF")


@app.post("/convert-text")
@limiter.limit(RATE_LIMIT)
async def convert_text(request: Request, data: ConvertRequest):
    logger.info(f"Text conversion request from {get_remote_address(request)}")

    title = data.title or "Screenplay"

    try:
        pdf_bytes = generate_pdf(data.markdown, title, data.font_size, data.use_vector)

        logger.info(f"Successfully generated PDF from text input")

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="screenplay.pdf"'
            }
        )
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate PDF")


def generate_pdf(markdown_text: str, title: str, font_size: int, use_vector: bool) -> bytes:
    elements = parse_screenplay_markdown(markdown_text)

    if not elements:
        raise ValueError("No valid screenplay elements found in markdown")

    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        tmp_path = tmp_file.name

    try:
        if use_vector:
            try:
                draw_pdf_vector(
                    elements,
                    tmp_path,
                    title=title,
                    font_size=font_size
                )
            except (ImportError, SystemExit):
                logger.warning("ReportLab not available, falling back to raster rendering")
                draw_pdf(
                    elements,
                    tmp_path,
                    title=title,
                    font_size=font_size
                )
        else:
            draw_pdf(
                elements,
                tmp_path,
                title=title,
                font_size=font_size
            )

        with open(tmp_path, 'rb') as f:
            pdf_bytes = f.read()

        return pdf_bytes

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))

    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=os.getenv("RELOAD", "false").lower() == "true"
    )
