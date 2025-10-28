# Static Files Update

## Changes Made

The HTML interface has been extracted from `app.py` into a separate file for easier maintenance.

### File Structure

```
scriptmd2pdf/
├── app.py                    # FastAPI backend (now simplified)
├── static/
│   └── index.html           # Web interface (HTML, CSS, JavaScript)
├── screenmd2pdf.py          # Core PDF generator
└── ...
```

### Benefits

1. **Easier Editing**: Edit HTML/CSS/JavaScript in `static/index.html` without touching Python code
2. **Better Separation**: Clean separation between backend API and frontend UI
3. **Simpler Deployment**: Static files can be cached by browsers and CDNs
4. **Maintainability**: Frontend developers can work on UI without touching backend code

### How It Works

- `app.py` now uses `FileResponse` to serve `static/index.html`
- The `/static` directory is mounted for serving static assets
- Fallback embedded HTML remains in `app.py` for backward compatibility

### For Developers

To modify the web interface:

1. Edit `static/index.html`
2. No need to restart the server (with `--reload`)
3. Simply refresh your browser

To modify the API:

1. Edit `app.py`
2. Server will auto-reload if using `--reload` flag

### Deployment Notes

The Dockerfile has been updated to copy the `static/` directory:

```dockerfile
COPY --chown=scriptmd2pdf:scriptmd2pdf static ./static
```

No other deployment changes needed - docker-compose works as before.

### Testing

Confirmed working:
- ✅ Static HTML file served correctly
- ✅ API endpoints functional
- ✅ File upload works
- ✅ Text editor works
- ✅ All styling intact

## Quick Test

```bash
# Start the server
make dev

# Or manually
source venv/bin/activate
uvicorn app:app --reload

# Visit http://localhost:8000
```

The interface should load with:
- Three tabs: Upload File, Text Editor, Syntax Guide
- Drag-and-drop file upload
- All functionality working as before
