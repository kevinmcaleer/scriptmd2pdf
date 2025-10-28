# Additional Export Features

The web interface now supports generating multiple export formats in addition to the screenplay PDF.

## Features Added

### 1. Shot List (CSV)

Generate a CSV file containing all scene headings and shot headings with:
- Scene/Shot type
- Heading text
- First action summary
- Sequential numbering

**When to use**: For production planning, creating call sheets, or organizing your shoot.

### 2. Shot List (PDF)

A professionally formatted PDF version of the shot list with:
- Table layout with proper wrapping
- Scene and shot information
- Action summaries
- Optional entity inventory

**When to use**: For printable shot lists to distribute to crew.

### 3. Entity Inventory

Automatically extracts and lists:
- **Characters**: From dialogue cues (`@CHARACTER`)
- **Locations**: From scene headings (`### INT. LOCATION - DAY`)
- **Objects/Props**: Heuristically detected from uppercase tokens in action text

Each entity includes:
- Occurrence count
- First mention (element index)

**When to use**: For production planning, prop lists, character tracking, or script breakdown.

### 4. FCPXML Export

Generate a Final Cut Pro XML file with:
- Scene headings as chapter markers
- Shot headings as keyword ranges
- Estimated timing based on word count
- Compatible with Final Cut Pro X

**When to use**: When editing your video and want to pre-structure your timeline based on the screenplay.

## How to Use

### Web Interface

1. Upload your screenplay Markdown file or use the text editor
2. Under "Additional Exports", check the boxes for desired outputs:
   - ✓ Generate shot list (CSV)
   - ✓ Shot list as PDF
   - ✓ Include entity inventory (characters, locations, props)
   - ✓ Generate FCPXML (Final Cut Pro)
3. Click "Convert to PDF"
4. If any additional exports are selected, a ZIP file will download containing:
   - The screenplay PDF
   - Any selected additional files

### API Usage

#### File Upload Endpoint

```bash
curl -X POST http://localhost:8000/convert \
  -F "file=@screenplay.md" \
  -F "shot_list=true" \
  -F "shot_list_pdf=true" \
  -F "entities=true" \
  -F "fcpxml=true" \
  -o screenplay-exports.zip
```

#### Text Conversion Endpoint

```bash
curl -X POST http://localhost:8000/convert-text \
  -H "Content-Type: application/json" \
  -d '{
    "markdown": "### INT. ROOM - DAY\n\nAction here.",
    "title": "My Screenplay",
    "shot_list": true,
    "fcpxml": true
  }' \
  -o screenplay-exports.zip
```

### Response Types

- **PDF only**: Returns `application/pdf` with single PDF file
- **With additional exports**: Returns `application/zip` containing all requested files

## File Naming Convention

When multiple exports are generated, files are named:
- `{title}.pdf` - Screenplay
- `{title}-shotlist.csv` - Shot list CSV
- `{title}-shotlist.pdf` - Shot list PDF
- `{title}.fcpxml` - Final Cut Pro XML

## Example Workflow

### Production Planning

1. Upload screenplay
2. Select: ✓ Shot list (PDF), ✓ Entity inventory
3. Download and print for production meeting
4. Use character list for casting
5. Use location list for location scouting
6. Use object list for prop procurement

### Video Editing

1. Upload screenplay
2. Select: ✓ FCPXML
3. Import FCPXML into Final Cut Pro
4. Timeline is pre-structured with:
   - Chapter markers at each scene
   - Keyword ranges for each shot
5. Start editing by filling in actual footage

### Script Breakdown

1. Upload screenplay
2. Select: ✓ Shot list (CSV), ✓ Entity inventory
3. Open CSV in spreadsheet
4. Add columns for:
   - Shooting day
   - Location
   - Cast required
   - Props needed
5. Export as shooting schedule

## Technical Details

### Entity Extraction Algorithm

- **Characters**: Extracted from `@CHARACTER` dialogue cues
- **Locations**: Parsed from scene headings, removing INT/EXT and time descriptors
- **Objects**: Uppercase tokens (3+ chars) from action text, excluding common words

### FCPXML Timing

- Based on word count estimation
- Default: 160 words per minute
- Adjustable via CLI (not yet in web interface)
- Adds minimum duration per block

### Shot List Generation

- Includes all `### Scene Headings`
- Includes all `! Shot Headings`
- Captures first action paragraph as summary
- Numbered sequentially

## Limitations

- Entity extraction is heuristic (may miss some items or include false positives)
- FCPXML timing is estimated (adjust markers in Final Cut Pro as needed)
- Shot list summaries are truncated to ~120 characters
- Maximum file size still 1MB for uploads

## Future Enhancements

Potential additions:
- Character breakdown by scene
- Scene length estimation
- Dialogue word count per character
- Location-based shooting schedule
- Configurable FCPXML timing parameters
- Markdown shot list format
- JSON export for custom tools

## Troubleshooting

**Q: ZIP file is empty**
A: Make sure at least one additional export checkbox is selected

**Q: FCPXML won't import to Final Cut Pro**
A: Ensure you're using Final Cut Pro X (not older versions)

**Q: Entity inventory has incorrect items**
A: The extraction is heuristic. You can edit the CSV/PDF after generation

**Q: Shot list is missing some scenes**
A: Ensure scene headings use `###` Markdown syntax

**Q: Rate limit exceeded**
A: Wait 1 minute between requests (5 requests per minute limit)

## API Documentation

Full API documentation available at: `http://localhost:8000/docs`

Interactive API explorer allows you to test all parameters and see request/response formats.

## Examples

### Minimal (PDF only)

```json
{
  "markdown": "### INT. ROOM - DAY\n\nAction.",
  "title": "Test"
}
```

Returns: Single PDF file

### Full Export

```json
{
  "markdown": "### INT. ROOM - DAY\n\n@ALEX\nHello.",
  "title": "Full Test",
  "shot_list": true,
  "shot_list_pdf": true,
  "entities": true,
  "fcpxml": true
}
```

Returns: ZIP file with:
- Full Test.pdf
- Full Test-shotlist.csv
- Full Test-shotlist.pdf (with entity inventory)
- Full Test.fcpxml

---

**Last Updated**: 2025-10-28
