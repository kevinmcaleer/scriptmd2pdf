# Shot List PDF Underline Fix

## Issue
The horizontal lines that underline the column headers (Name, Count, First) in the Entity Inventory section of shot list PDFs were appearing too close to the data rows, causing text to appear struck through or overlapping with the underline.

## Root Cause
In the `render_shot_list_pdf()` function (raster/Pillow version), the spacing after drawing the horizontal line was hardcoded to 4 pixels:

```python
y += line_h          # Position after headers
dr.line((MARGIN_L, y, PAGE_W - MARGIN_R, y), fill="black")
y += 4               # Only 4 pixels - TOO SMALL!
```

This fixed spacing didn't scale with font size, causing overlap issues especially at larger font sizes.

## Solution
Changed the spacing to be proportional to the line height, matching the approach used in the vector version:

```python
y += line_h          # Position after headers
dr.line((MARGIN_L, y, PAGE_W - MARGIN_R, y), fill="black")
y += int(line_h * 0.3)  # Adequate space after underline - SCALES WITH FONT SIZE
```

### Spacing by Font Size
- Font size 10: ~4 pixels
- Font size 12: ~5 pixels
- Font size 14: ~5-6 pixels

## Files Changed
- `screenmd2pdf.py` (line 850)

## Testing
Tested with example screenplay at font sizes 10, 12, and 14:
- ✅ Characters section: Proper spacing between underline and character names
- ✅ Locations section: Proper spacing between underline and location names
- ✅ Objects/Props section: Proper spacing between underline and object names
- ✅ All entity data rows display clearly without overlap

## Technical Details
- **Function**: `render_shot_list_pdf()` at line 677
- **Change**: Line 850 changed from `y += 4` to `y += int(line_h * 0.3)`
- **Consistency**: Vector version (`render_shot_list_pdf_vector()`) already used proportional spacing with `y -= line_h*0.8` before the line and `y -= line_h*0.2` after
- **Line height calculation**: `line_h = ascent + descent + 4` (approximately 1.3 × font_size)

## Deployment
No breaking changes. The fix improves visual quality without affecting functionality or API.
