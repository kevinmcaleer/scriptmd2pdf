# Visual Preview - ScriptMD2PDF Web Interface

## Complete Page Layout

```
╔══════════════════════════════════════════════════════════════╗
║                      ScriptMD2PDF                            ║
║     Convert Markdown to Professional Screenplay PDFs         ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║              [Your Banner Image Here]                        ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  📄 Upload File  |  ✏️ Text Editor  |  📖 Syntax Guide     ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Upload Tab:                                                 ║
║  ┌────────────────────────────────────┐                     ║
║  │         📄                          │                     ║
║  │  Drag & Drop your Markdown file    │                     ║
║  │         here                        │                     ║
║  │    or click to browse               │                     ║
║  └────────────────────────────────────┘                     ║
║                                                              ║
║  Title: [________________]  Font Size: [12]                 ║
║  ☑ Use vector rendering (better quality)                    ║
║                                                              ║
║  ─────────── Additional Exports: ────────────               ║
║  ☐ Generate shot list (CSV)                                 ║
║  ☐ Shot list as PDF                                         ║
║  ☐ Include entity inventory (characters, locations, props)  ║
║  ☐ Generate FCPXML (Final Cut Pro)                          ║
║                                                              ║
║  ┌────────────────────────────────────┐                     ║
║  │      Convert to PDF                │                     ║
║  └────────────────────────────────────┘                     ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║                         FOOTER                               ║
║                                                              ║
║  ┌────────────────────────────────────────────────────┐    ║
║  │  ⚠️ Privacy Notice                                  │    ║
║  │  No data is saved or retained by this web          │    ║
║  │  application. All processing happens in-memory     │    ║
║  │  and files are immediately deleted after           │    ║
║  │  conversion. This service is provided for free     │    ║
║  │  and at your own risk. No warranty or guarantee    │    ║
║  │  is provided.                                       │    ║
║  └────────────────────────────────────────────────────┘    ║
║                                                              ║
║           ScriptMD2PDF - Free & Open Source                  ║
║              Screenplay Converter                            ║
║        Written by Kevin McAleer (kevsrobots.com)            ║
║                                                              ║
║  📦 View Source Code on GitHub  |  🐛 Report Issues         ║
║              🤖 More Projects                                ║
║                                                              ║
║              © 2025 Kevin McAleer | MIT License             ║
╚══════════════════════════════════════════════════════════════╝
```

## Syntax Guide Tab

```
╔══════════════════════════════════════════════════════════════╗
║  📄 Upload File  |  ✏️ Text Editor  |  📖 Syntax Guide     ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Markdown Syntax Guide                                       ║
║                                                              ║
║  Scene Headings                                              ║
║  • ### INT. LOCATION - DAY - Scene heading (slugline)       ║
║  • Will be rendered in bold, uppercase                       ║
║                                                              ║
║  Action                                                      ║
║  • Plain paragraphs become action text                       ║
║  • Separate paragraphs with blank lines                      ║
║                                                              ║
║  Dialogue                                                    ║
║  • @CHARACTER - Character cue (name will be uppercase)      ║
║  • (whispering) - Parenthetical direction                   ║
║  • Dialogue lines follow the character cue                   ║
║  • End dialogue with a blank line                            ║
║                                                              ║
║  Transitions                                                 ║
║  • >> CUT TO: - Right-aligned transition                    ║
║  • Colon added automatically if missing                      ║
║                                                              ║
║  Shot Headings                                               ║
║  • ! CLOSE ON - Camera direction or shot description        ║
║                                                              ║
║  Other                                                       ║
║  • --- - Force page break                                    ║
║  • // Comment - Comments (ignored)                           ║
║  • > Note - Notes/blockquotes (ignored)                     ║
║                                                              ║
║  Example Screenplay                                          ║
║                                                              ║
║         ┌─────────────────────────────────┐                 ║
║         │  📥 Download Example Screenplay  │                 ║
║         └─────────────────────────────────┘                 ║
║                                                              ║
║  ┌────────────────────────────────────────────────┐        ║
║  │  ### INT. COFFEE SHOP - DAY                    │        ║
║  │                                                 │        ║
║  │  The morning rush is in full swing.            │        ║
║  │                                                 │        ║
║  │  @ALEX                                          │        ║
║  │  (to barista)                                   │        ║
║  │  Large coffee, please.                          │        ║
║  │  ...                                            │        ║
║  └────────────────────────────────────────────────┘        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

## Color Scheme

### Primary Colors
- **Purple Gradient**: #667eea → #764ba2
- **Background**: White (#ffffff)
- **Text**: Dark gray (#333)

### Accent Colors
- **Links**: Purple (#667eea)
- **Success**: Green (#d4edda)
- **Error**: Red (#f8d7da)
- **Warning/Privacy**: Yellow (#fff3cd)

### UI Elements
- **Borders**: Light gray (#e0e0e0)
- **Hover**: Transform translateY(-2px)
- **Footer Background**: #f8f9fa

## Interactive Elements

### Buttons
```
┌──────────────────────────┐
│    Convert to PDF        │  ← Main action button
└──────────────────────────┘
    Purple gradient
    Hover: lifts up 2px
    Disabled: 50% opacity

┌──────────────────────────┐
│ 📥 Download Example      │  ← Download button
└──────────────────────────┘
    Purple solid
    Hover: darker purple
    Transform on hover
```

### Upload Area
```
┌────────────────────────┐
│         📄              │
│  Drag & Drop file      │
│   or click to browse   │
└────────────────────────┘
    Dashed border
    Hover: background changes
    Dragover: border color changes
```

### Checkboxes
```
☑ Use vector rendering (better quality)
☐ Generate shot list (CSV)
☐ Shot list as PDF
☐ Include entity inventory
☐ Generate FCPXML (Final Cut Pro)
```

## Footer Sections

### 1. Privacy Notice (Yellow Warning Box)
```
┌────────────────────────────────────────────┐
│  ⚠️ Privacy Notice                         │
│  No data is saved or retained...           │
│  [Full privacy text]                        │
└────────────────────────────────────────────┘
```
- Background: #fff3cd
- Border: #ffc107
- Text color: #856404

### 2. Credits Section
```
ScriptMD2PDF - Free & Open Source
      Screenplay Converter
Written by Kevin McAleer
    (link to kevsrobots.com)
```

### 3. Links Section
```
📦 View Source Code on GitHub
    |
🐛 Report Issues
    |
🤖 More Projects
```
- All links open in new tab
- Purple color with hover underline

### 4. Copyright
```
© 2025 Kevin McAleer | MIT License
```
- Smaller text (0.85em)
- Gray color (#999)

## Responsive Features

### Desktop (>1200px)
- Full width container
- 3-column option layout
- Banner full width

### Tablet (768px - 1200px)
- Container adapts
- 2-column option layout
- Banner responsive

### Mobile (<768px)
- Single column layout
- Stack all options
- Banner scales appropriately
- Footer remains readable

## Accessibility

- ✓ Alt text on banner image
- ✓ Semantic HTML (header, footer)
- ✓ Clear labels on all inputs
- ✓ High contrast text
- ✓ Focus states on interactive elements
- ✓ rel="noopener" on external links
- ✓ Descriptive link text

## Browser Support

Tested and working on:
- ✓ Chrome/Edge (Chromium)
- ✓ Firefox
- ✓ Safari
- ✓ Mobile browsers

## File Size Budget

- index.html: 25 KB
- banner.jpg: 41.5 KB
- example_screenplay.md: 857 bytes
- **Total**: ~67 KB

All assets load quickly even on slower connections.

---

The interface now presents a complete, professional appearance with clear branding, privacy information, and helpful resources for users! 🎨✨
