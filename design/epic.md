# ScriptMD2PDF - Epic Documentation

## Overview

A free and open-source tool for converting Markdown documents into professional screenplays in PDF format. The tool provides both CLI and web interfaces for maximum flexibility.

## Web Interface

A web interface is available at https://md2script.kevs.wtf to either drag and drop a markdown file or edit directly in the browser.

### Security Features

- Only markdown files accepted for upload (security validation)
- File size limit: 1MB per file
- Rate limiting: Maximum 5 requests per minute from a single IP address
- No file storage on server (processed in-memory)

### Technology Stack

- **Backend**: FastAPI (Python web framework)
- **PDF Generation**: screenmd2pdf.py core library
- **Containerization**: Docker with docker-compose
- **Deployment**: Raspberry Pi compatible ARM64/ARM32 images
- **CI/CD**: GitHub Actions for automated builds
- **Container Registry**: Private registry at 192.168.2.1:5000/md2script:latest

## Core Features

### Screenplay Formatting

The screenmd2pdf.py module provides comprehensive screenplay formatting:

1. **Scene Headings** (screenmd2pdf.py:163-174)
   - Markdown syntax: `### INT. LOCATION - DAY`
   - Rendered in bold, left margin 1.5"
   - Auto-uppercase formatting

2. **Action Paragraphs** (screenmd2pdf.py:404-405)
   - Plain text paragraphs
   - Left margin 1.5", right margin 1"
   - Wraps text intelligently

3. **Character Cues** (screenmd2pdf.py:188-210)
   - Markdown syntax: `@CHARACTER`
   - Left margin 3.5"
   - Auto-uppercase

4. **Dialogue** (screenmd2pdf.py:406-414)
   - Lines following character cue
   - Left margin 2.5", right margin 2.5"
   - Supports parentheticals `(whispering)`

5. **Transitions** (screenmd2pdf.py:175-180, 415-416)
   - Markdown syntax: `>> CUT TO:`
   - Right-aligned near right margin
   - Auto-uppercase with colon

6. **Shot Headings** (screenmd2pdf.py:184-187)
   - Markdown syntax: `! CLOSE ON`
   - Auto-uppercase formatting

7. **Page Breaks** (screenmd2pdf.py:130-134, 157-159)
   - Markdown syntax: `---`
   - Forces new page

### Font Handling

- **Font Discovery** (screenmd2pdf.py:47-59)
  - Auto-detects system monospace fonts
  - Supports custom TTF fonts via `--font` parameter

- **Bold Variants** (screenmd2pdf.py:75-104)
  - Attempts to load bold font variants for scene headings
  - Falls back to simulated bold if not available

### Rendering Engines

#### Vector PDF (Default) (screenmd2pdf.py:421-603)
- Uses ReportLab for crisp, selectable text
- Proper font embedding
- Smaller file sizes
- Professional output quality

#### Raster PDF (Fallback) (screenmd2pdf.py:251-419)
- Uses Pillow for image-based PDF
- No external dependencies beyond Pillow
- Guaranteed compatibility

### Export Features

#### Shot List Generation (screenmd2pdf.py:612-659)
- Extracts all scene and shot headings
- Includes action summaries
- Output formats: Markdown table, CSV, or PDF
- Optional landscape orientation for wider columns

#### Entity Extraction (screenmd2pdf.py:1046-1104)
- **Characters**: Extracted from dialogue cues
- **Locations**: Parsed from scene headings
- **Objects/Props**: Heuristic detection from uppercase tokens in action text
- Tracks occurrence count and first mention

#### FCPXML Export (screenmd2pdf.py:1118-1241)
- Final Cut Pro timeline format
- Scene headings as chapter markers
- Shot headings as keyword ranges
- Timing estimation based on word count (configurable WPM)
- Optional title clips for each scene

## Web Application Architecture

### API Endpoints

1. **POST /convert**
   - Accepts: multipart/form-data with .md file
   - Validates: file type, size, rate limit
   - Returns: PDF file
   - Processing: In-memory, no disk storage

2. **POST /convert-text**
   - Accepts: JSON with markdown text
   - Validates: text length, rate limit
   - Returns: PDF file
   - Processing: In-memory

3. **GET /**
   - Returns: Web interface HTML
   - Features: Drag-and-drop, live editor

### Rate Limiting Implementation

- Token bucket algorithm
- Per-IP tracking using X-Forwarded-For header
- 5 requests per minute limit
- 429 status code when exceeded

### Error Handling

- 400: Invalid file format
- 413: File too large
- 429: Rate limit exceeded
- 500: Internal processing error

## Deployment

### Docker Configuration

The application runs in a Docker container with:
- Python 3.11 slim base image
- Multi-stage build for smaller image size
- Non-root user for security
- Health check endpoint

### Raspberry Pi Compatibility

- ARM64 and ARM32 architecture support
- Multi-platform builds via Docker buildx
- Optimized dependencies for ARM

### CI/CD Pipeline

GitHub Actions workflow:
1. Run tests on push/PR
2. Build multi-platform Docker images
3. Push to private registry (192.168.2.1:5000)
4. Tag with version and 'latest'

### Environment Variables

- `MAX_FILE_SIZE`: Upload limit in bytes (default: 1048576)
- `RATE_LIMIT_REQUESTS`: Requests per window (default: 5)
- `RATE_LIMIT_WINDOW`: Window in seconds (default: 60)
- `HOST`: Bind address (default: 0.0.0.0)
- `PORT`: Port number (default: 8000)

## Testing Strategy

### Unit Tests

- Markdown parsing functions
- PDF rendering engines
- Font loading and fallback
- Entity extraction logic

### Integration Tests

- Full MD to PDF conversion
- Shot list generation
- FCPXML export
- All output format combinations

### API Tests

- File upload validation
- Rate limiting behavior
- Error responses
- Security validations

### Test Coverage Target

Minimum 80% code coverage as per project guidelines

## Future Enhancements

Potential features mentioned in README.md:
- Scene numbering
- Title page generation
- Automatic CONT'D markers
- Fountain format import
- Revision colors / A-pages

## Security Considerations

1. File type validation (whitelist approach)
2. Size limits to prevent DoS
3. Rate limiting per IP
4. No file persistence on server
5. Input sanitization for markdown content
6. Container runs as non-root user
7. Minimal attack surface in Docker image

## Performance Optimization

1. In-memory processing (no disk I/O)
2. Async FastAPI handlers
3. Connection pooling
4. Efficient text wrapping algorithms
5. Font caching

## Monitoring and Logging

- Request logging with timestamps
- Error tracking with stack traces
- Rate limit violations logged
- Processing time metrics
- Health check endpoint for uptime monitoring
