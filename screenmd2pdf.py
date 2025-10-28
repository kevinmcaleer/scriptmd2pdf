#!/usr/bin/env python3

# Kevin McAleer
# 13 August 2025

"""
screenmd2pdf.py (v2)
Convert a screenplay-flavored Markdown file into a PDF in standard screenwriter style.

USAGE:
    python screenmd2pdf.py input.md output.pdf [--title "My Title"] [--font /path/to/mono.ttf] [--size 12]

Markdown conventions:
- Scene heading (slugline): start a paragraph with "### " followed by a standard heading, e.g.
      ### INT. KITCHEN - DAY
- Action: plain paragraphs.
- Character cue: start a paragraph with "@", all-caps name:
      @ALEX
- Parenthetical: on its own line, within dialogue, enclose in parentheses:
      (whispering)
- Dialogue: lines after a character cue (and optional parentheticals) until a blank line.
- Transition: start a paragraph with ">> ":
      >> CUT TO:
- Shot headings: start a paragraph with "! ":
      ! CLOSE ON
- Forced page break: a line with just "---".
- Comments: lines starting with "//" are ignored.

Layout (approximate, in inches):
- Paper: US Letter (8.5" x 11"), default 12pt monospace.
- Action & scene headings: left 1.5", right 1".
- Character: left 3.5".
- Dialogue: left 2.5", right 2.5".
- Parenthetical: left 3.0", right 2.5".
- Transition: flush/right near the right margin.

This version adds *robust wrapping* that falls back to monospaced character counts if precise
text measurement isn't available in your Pillow build. It also supports --font and --size.
"""

import os
import argparse
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Any
import re

def find_mono_font():
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
        "/System/Library/Fonts/Courier New.ttf",
        "/Library/Fonts/Courier New.ttf",
        "/System/Library/Fonts/Supplemental/Courier New.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None

def load_font(size=12, override_path=None):
    if override_path and os.path.exists(override_path):
        try:
            return ImageFont.truetype(override_path, size=size)
        except OSError:
            pass
    path = find_mono_font()
    if path:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            pass
    return ImageFont.load_default()

def load_bold_variant(base_font, base_path: str | None, size: int):  # type: ignore[override]
    """Attempt to load a bold variant of the provided font. Fall back to base_font.
    Heuristics: if a path was supplied or discovered, try common Bold filename patterns.
    """
    if not base_path or not os.path.exists(base_path):
        return base_font
    candidates = []
    root, ext = os.path.splitext(base_path)
    # Common replacements
    if 'Regular' in root:
        candidates.append(root.replace('Regular', 'Bold') + ext)
    if 'Mono' in root and 'Bold' not in root:
        candidates.append(root + '-Bold' + ext)
    # Generic patterns
    candidates.extend([
        root + 'Bold' + ext,
        root + '-Bold' + ext,
        root.replace('-Regular', '-Bold') + ext,
    ])
    tried = set()
    for c in candidates:
        if c in tried:
            continue
        tried.add(c)
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size=size)
            except OSError:  # specific to font loading
                continue
    return base_font

# Types:
# - scene: {"type":"scene","text":...}
# - action: {"type":"action","text":...}
# - dialogue: {"type":"dialogue","character":..., "parentheticals":[...], "lines":[...]} (lines are strings combined)
# - transition: {"type":"transition","text":...}
# - shot: {"type":"shot","text":...}
# - pagebreak: {"type":"pagebreak"}

def parse_screenplay_markdown(md_text: str) -> List[Dict[str, Any]]:
    # Normalize real newlines (previous version used escaped sequences incorrectly)
    lines = md_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    blocks = []
    buf = []
    for raw in lines:
        line = raw.rstrip()
        stripped_line = line.lstrip()
        # Skip comments
        if stripped_line.startswith("//"):
            continue
        # Skip blockquotes/notes (lines starting with '>' that are NOT transitions).
        # Keep transitions that start with '>>'.
        if stripped_line.startswith(">") and not stripped_line.startswith(">>"):
            continue
        if stripped_line == "---":
            if buf:
                blocks.append("\n".join(buf).strip("\n"))
                buf = []
            blocks.append("---")
            continue
        if stripped_line == "":
            if buf:
                blocks.append("\n".join(buf).strip("\n"))
                buf = []
        else:
            buf.append(line)
    if buf:
        blocks.append("\n".join(buf).strip("\n"))

    # Fix: re-split all blocks on real newlines for further parsing
    fixed_blocks = []
    for block in blocks:
        if block == "---":
            fixed_blocks.append(block)
        else:
            fixed_blocks.extend(block.split("\n\n"))
    blocks = fixed_blocks

    elements: List[Dict[str, Any]] = []
    for block in blocks:
        # Always treat a block that is exactly '---' as a pagebreak/horizontal line
        if block.strip() == "---":
            elements.append({"type": "pagebreak"})
            continue

        stripped = block.strip()
        # Remove markdown heading markers for all block types
        if stripped.startswith("### "):
            text = stripped[4:].strip()
            elements.append({"type": "scene", "text": text})
            continue
        if stripped.startswith("## "):
            text = stripped[3:].strip()
            elements.append({"type": "scene", "text": text})
            continue
        if stripped.startswith("# "):
            text = stripped[2:].strip()
            elements.append({"type": "scene", "text": text})
            continue
        if stripped.startswith(">> "):
            text = stripped[3:].strip().upper()
            if not text.endswith(":"):
                text += ":"
            elements.append({"type": "transition", "text": text})
            continue
        # Ignore any blockquote/note lines starting with '>' (with or without leading spaces)
        if stripped.startswith("> ") or stripped.startswith(">"):
            continue
        if stripped.startswith("! "):
            text = stripped[2:].strip().upper()
            elements.append({"type": "shot", "text": text})
            continue
        if stripped.lstrip().startswith("@"):
            lines = [ln for ln in stripped.split("\n")]
            # Remove leading spaces and @ for character cue, then strip and uppercase
            char_line = lines[0].lstrip()
            if char_line.startswith("@"):
                character = char_line[1:].strip().upper()
            else:
                character = char_line.strip().upper()
            parentheticals = []
            dialogue_lines = []
            for ln in lines[1:]:
                st = ln.strip()
                if st.startswith("(") and st.endswith(")"):
                    parentheticals.append(st)
                else:
                    dialogue_lines.append(st)
            elements.append({
                "type": "dialogue",
                "character": character,
                "parentheticals": parentheticals,
                "lines": dialogue_lines
            })
            continue
        # Remove any leading markdown heading or control characters from action blocks
        cleaned = stripped
        for prefix in ["# ", "## ", "### ", "! ", ">> ", "> "]:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
        # Do not add an action block if it is just '---' (with or without whitespace)
        if cleaned.strip() == "---":
            continue
        elements.append({"type": "action", "text": cleaned})
    # Post-process: split any action blocks that contain standalone dash separators into pagebreaks
    processed: List[Dict[str, Any]] = []
    for el in elements:
        if el.get("type") != "action":
            processed.append(el)
            continue
        text_block = el.get("text", "")
        lines_block = text_block.split("\n")
        tmp_buf: List[str] = []
        def flush_tmp(buf: List[str]):
            if buf:
                joined_text = "\n".join(buf).strip()
                if joined_text:
                    processed.append({"type": "action", "text": joined_text})
                buf.clear()
        for ln in lines_block:
            if ln.strip() in {"-", "--", "---"}:
                flush_tmp(tmp_buf)
                processed.append({"type": "pagebreak"})
            else:
                tmp_buf.append(ln)
        flush_tmp(tmp_buf)

    # Final sanitation: remove any residual empty or dash-only action blocks
    sanitized: List[Dict[str, Any]] = []
    for el in processed:
        if el.get("type") == "action" and el.get("text", "").strip(" -\t") in {"", "-", "--", "---"}:
            continue
        sanitized.append(el)
    return sanitized

def draw_pdf(elements: List[Dict[str, Any]], out_path: str, title: str = "", font_path: str | None = None, font_size: int = 12, break_style: str = "page", transition_right_in: float = 1.0):
    # Page setup
    PAGE_W, PAGE_H = int(8.5*72), int(11*72)  # 612x792
    MARGIN_T, MARGIN_B = int(1*72), int(1*72)
    # Indents (in points)
    LEFT_SCENE = int(1.5*72)
    LEFT_ACTION = int(1.5*72)
    LEFT_CHAR = int(3.5*72)
    LEFT_DIALOGUE = int(2.5*72)
    LEFT_PAREN = int(3.0*72)
    RIGHT_DIALOGUE = int(2.5*72)
    RIGHT_ACTION = int(1.0*72)
    RIGHT_PAREN = int(2.5*72)
    RIGHT_TRANSITION = int(transition_right_in*72)

    # Font
    font = load_font(size=font_size, override_path=font_path)
    # Try to get a bold variant for scene headings
    bold_font = load_bold_variant(font, font_path, font_size) if font_path else font
    try:
        ascent, descent = font.getmetrics()  # type: ignore[attr-defined]
        line_h = ascent + descent + 2
    except AttributeError:
        line_h = int(font_size * 1.2)

    # Create canvas
    pages: List[Image.Image] = []
    img = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    draw = ImageDraw.Draw(img)
    y = MARGIN_T

    # Robust width measurement (works across Pillow variants)
    def text_width(s: str) -> float:
        # Layered fallbacks based on Pillow capabilities
        try:  # Preferred modern Pillow
            return draw.textlength(s, font=font)  # type: ignore[attr-defined]
        except AttributeError:
            pass
        try:  # Fallback older API
            return font.getlength(s)  # type: ignore[attr-defined]
        except AttributeError:
            pass
        try:  # Last resort bbox
            left, _top, right, _bottom = font.getbbox(s)  # type: ignore[attr-defined]
            return right - left
        except AttributeError:
            return 8.0 * len(s)

    # Wrapper that honors explicit newlines and falls back to monospaced character counts
    def wrap_text(text: str, max_width: int) -> list:
        lines_out = []
        # Split on real newlines, not the string '\\n'
        for raw_line in text.split("\n"):
            # If the line already fits, keep it
            if text_width(raw_line) <= max_width:
                if raw_line != "":
                    lines_out.append(raw_line)
                else:
                    lines_out.append("")  # preserve blank line
                continue
            # Word-wrapping with measurement
            words = raw_line.split()
            if not words:
                lines_out.append("")
                continue
            line = ""
            for w in words:
                test = w if not line else line + " " + w
                if text_width(test) <= max_width:
                    line = test
                else:
                    if line:
                        lines_out.append(line)
                    # If single word longer than width, hard-wrap by characters
                    if text_width(w) > max_width:
                        chunk = ""
                        for ch in w:
                            t2 = chunk + ch
                            if text_width(t2) <= max_width:
                                chunk = t2
                            else:
                                if chunk:
                                    lines_out.append(chunk)
                                chunk = ch
                        if chunk:
                            line = chunk
                        else:
                            line = ""
                    else:
                        line = w
            if line:
                lines_out.append(line)
        return lines_out

    def new_page():
        nonlocal img, draw, y
        pages.append(img)
        img = Image.new("RGB", (PAGE_W, PAGE_H), "white")
        draw = ImageDraw.Draw(img)
        if title:
            tw = text_width(title)
            draw.text(((PAGE_W - tw)//2, int(0.5*72)), title, font=font, fill="black")
        y = MARGIN_T

    def ensure_space(req_h):
        nonlocal y
        if y + req_h > PAGE_H - MARGIN_B:
            new_page()

    def draw_block(text: str, left: int, right_margin: int, extra_before=0, extra_after=0, align_right=False, use_bold=False):
        nonlocal y
        width = PAGE_W - left - right_margin
        wrapped = wrap_text(text, width) if text else [""]
        block_h = extra_before + (len(wrapped) * line_h) + extra_after
        ensure_space(block_h)

        y += extra_before
        for line_text in wrapped:
            if align_right:
                tw = text_width(line_text)
                x = PAGE_W - right_margin - tw
            else:
                x = left
            if use_bold and bold_font != font:
                draw.text((x, y), line_text, font=bold_font, fill="black")
            elif use_bold and bold_font == font:
                draw.text((x, y), line_text, font=font, fill="black")
                draw.text((x+0.6, y), line_text, font=font, fill="black")
            else:
                draw.text((x, y), line_text, font=font, fill="black")
            y += line_h
        y += extra_after

    # Reference break_style to avoid lint about unused param (future compatibility)
    _ = break_style  # noqa: F841

    # Optional header on first page
    if title:
        tw = text_width(title)
        draw.text(((PAGE_W - tw)//2, int(0.5*72)), title, font=font, fill="black")

    # Render
    for el in elements:
        t = el["type"]
        if t == "pagebreak":
            # Force a new page for screenplay page break markers (---)
            new_page()
            continue

        if t == "scene":
            draw_block(el["text"].upper(), LEFT_SCENE, RIGHT_ACTION, extra_before=int(0.25*line_h), extra_after=int(0.25*line_h), use_bold=True)
        elif t == "shot":
            draw_block(el["text"].upper(), LEFT_ACTION, RIGHT_ACTION, extra_before=int(0.1*line_h), extra_after=int(0.1*line_h))
        elif t == "action":
            draw_block(el["text"], LEFT_ACTION, RIGHT_ACTION, extra_before=int(0.2*line_h), extra_after=int(0.2*line_h))
        elif t == "dialogue":
            # Character cue (already stripped of @ in parser)
            draw_block(el["character"].upper(), LEFT_CHAR, RIGHT_DIALOGUE, extra_before=int(0.3*line_h), extra_after=0)
            # Parentheticals
            for p in el.get("parentheticals", []):
                draw_block(p, LEFT_PAREN, RIGHT_PAREN, extra_before=0, extra_after=0)
            # Dialogue lines: preserve line returns
            dial = "\n".join(el.get("lines", []))
            draw_block(dial, LEFT_DIALOGUE, RIGHT_DIALOGUE, extra_before=0, extra_after=int(0.3*line_h))
        elif t == "transition":
            draw_block(el["text"], LEFT_ACTION, RIGHT_TRANSITION, extra_before=int(0.3*line_h), extra_after=int(0.1*line_h), align_right=True)

    pages.append(img)
    pages[0].save(out_path, save_all=True, append_images=pages[1:])

def draw_pdf_vector(elements: List[Dict[str, Any]], out_path: str, title: str = "", font_path: str | None = None, font_size: int = 12, transition_right_in: float = 1.0):
    """Vector (text) PDF rendering using ReportLab for razor sharp output.

    Falls back to Courier if no font path provided. Attempts bold variant registration for scene headings.
    """
    try:
        from reportlab.pdfgen import canvas  # type: ignore
        from reportlab.lib.pagesizes import letter  # type: ignore
        from reportlab.pdfbase import pdfmetrics  # type: ignore
        from reportlab.pdfbase.ttfonts import TTFont  # type: ignore
    except ImportError as exc:  # pragma: no cover - dependency missing
        raise SystemExit("ReportLab not installed. Install with: pip install reportlab") from exc

    PAGE_W, PAGE_H = letter  # 612x792 points
    # Indents
    LEFT_SCENE = 1.5 * 72
    LEFT_ACTION = 1.5 * 72
    LEFT_CHAR = 3.5 * 72
    LEFT_DIALOGUE = 2.5 * 72
    LEFT_PAREN = 3.0 * 72
    RIGHT_DIALOGUE = 2.5 * 72
    RIGHT_ACTION = 1.0 * 72
    RIGHT_TRANSITION = transition_right_in * 72
    RIGHT_PAREN = 2.5 * 72
    TOP_MARGIN = 1.0 * 72
    BOTTOM_MARGIN = 1.0 * 72

    # Font registration
    base_font_name = "Courier"
    bold_font_name = "Courier-Bold"
    if font_path and os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont("ScriptMono", font_path))
            base_font_name = "ScriptMono"
            # Try bold variant
            bold_variant = None
            root, ext = os.path.splitext(font_path)
            for cand in [root.replace("Regular","Bold")+ext, root+"-Bold"+ext, root+"Bold"+ext]:
                if os.path.exists(cand):
                    try:
                        pdfmetrics.registerFont(TTFont("ScriptMonoBold", cand))
                        bold_variant = "ScriptMonoBold"
                        break
                    except OSError:
                        continue
            if bold_variant:
                bold_font_name = bold_variant
        except OSError:
            pass

    line_h = font_size * 1.2  # approximate leading

    def string_width(txt: str, font_name: str, size: int) -> float:
        try:
            return pdfmetrics.stringWidth(txt, font_name, size)
        except (KeyError, ValueError):
            return len(txt) * (size * 0.6)

    def wrap(txt: str, font_name: str, size: int, max_width: float) -> List[str]:
        lines_out: List[str] = []
        for raw_line in txt.split("\n"):
            if string_width(raw_line, font_name, size) <= max_width:
                lines_out.append(raw_line)
                continue
            words = raw_line.split()
            if not words:
                lines_out.append("")
                continue
            line = ""
            for w in words:
                test = w if not line else line+" "+w
                if string_width(test, font_name, size) <= max_width:
                    line = test
                else:
                    if line:
                        lines_out.append(line)
                    # Hard wrap very long token
                    if string_width(w, font_name, size) > max_width:
                        chunk = ""
                        for ch in w:
                            t2 = chunk + ch
                            if string_width(t2, font_name, size) <= max_width:
                                chunk = t2
                            else:
                                if chunk:
                                    lines_out.append(chunk)
                                chunk = ch
                        if chunk:
                            line = chunk
                        else:
                            line = ""
                    else:
                        line = w
            if line:
                lines_out.append(line)
        return lines_out

    c = canvas.Canvas(out_path, pagesize=letter)

    def new_page():
        c.showPage()
        if title:
            c.setFont(base_font_name, font_size)
            title_w = string_width(title, base_font_name, font_size)
            c.drawString((PAGE_W - title_w)/2, PAGE_H - TOP_MARGIN + (font_size*0.2), title)

    # Title first page
    if title:
        c.setFont(base_font_name, font_size)
        title_w = string_width(title, base_font_name, font_size)
        c.drawString((PAGE_W - title_w)/2, PAGE_H - TOP_MARGIN + (font_size*0.2), title)

    y = PAGE_H - TOP_MARGIN - line_h

    def ensure_space(lines_needed: int):
        nonlocal y
        if y - (lines_needed * line_h) < BOTTOM_MARGIN:
            new_page()
            y = PAGE_H - TOP_MARGIN - line_h

    for el in elements:
        t = el["type"]
        if t == "pagebreak":
            new_page()
            y = PAGE_H - TOP_MARGIN - line_h
            continue
        if t == "scene":
            txt = el["text"].upper()
            wrapped = wrap(txt, bold_font_name, font_size, PAGE_W - LEFT_SCENE - RIGHT_ACTION)
            ensure_space(len(wrapped)+1)
            c.setFont(bold_font_name, font_size)
            for line in wrapped:
                c.drawString(LEFT_SCENE, y, line)
                y -= line_h
            y -= line_h * 0.25
        elif t == "shot":
            txt = el["text"].upper()
            wrapped = wrap(txt, base_font_name, font_size, PAGE_W - LEFT_ACTION - RIGHT_ACTION)
            ensure_space(len(wrapped)+1)
            c.setFont(base_font_name, font_size)
            for line in wrapped:
                c.drawString(LEFT_ACTION, y, line)
                y -= line_h
            y -= line_h * 0.1
        elif t == "action":
            txt = el["text"]
            wrapped = wrap(txt, base_font_name, font_size, PAGE_W - LEFT_ACTION - RIGHT_ACTION)
            ensure_space(len(wrapped)+1)
            c.setFont(base_font_name, font_size)
            for line in wrapped:
                c.drawString(LEFT_ACTION, y, line)
                y -= line_h
            y -= line_h * 0.2
        elif t == "dialogue":
            # Character
            c.setFont(base_font_name, font_size)
            char_lines = wrap(el["character"].upper(), base_font_name, font_size, PAGE_W - LEFT_CHAR - RIGHT_DIALOGUE)
            ensure_space(len(char_lines)+len(el.get("parentheticals", []))+len(el.get("lines", []))+2)
            for line in char_lines:
                c.drawString(LEFT_CHAR, y, line)
                y -= line_h
            # Parentheticals
            for p in el.get("parentheticals", []):
                for line in wrap(p, base_font_name, font_size, PAGE_W - LEFT_PAREN - RIGHT_PAREN):
                    c.drawString(LEFT_PAREN, y, line)
                    y -= line_h
            # Dialogue body
            dial_text = "\n".join(el.get("lines", []))
            for line in wrap(dial_text, base_font_name, font_size, PAGE_W - LEFT_DIALOGUE - RIGHT_DIALOGUE):
                c.drawString(LEFT_DIALOGUE, y, line)
                y -= line_h
            y -= line_h * 0.3
        elif t == "transition":
            txt = el["text"]
            wrapped = wrap(txt, base_font_name, font_size, PAGE_W - LEFT_ACTION - RIGHT_TRANSITION)
            ensure_space(len(wrapped)+1)
            for line in wrapped:
                w = string_width(line, base_font_name, font_size)
                c.drawString(PAGE_W - RIGHT_TRANSITION - w, y, line)
                y -= line_h
            y -= line_h * 0.2

    c.save()

def convert_markdown_to_pdf(md_path: str, pdf_path: str, title: str = "", font_path: str | None = None, font_size: int = 12, break_style: str = "page", transition_right_in: float = 1.0):
    with open(md_path, "r", encoding="utf-8") as f:
        md = f.read()
    elements = parse_screenplay_markdown(md)
    draw_pdf(elements, pdf_path, title=title, font_path=font_path, font_size=font_size, break_style=break_style, transition_right_in=transition_right_in)
    return elements

def write_shot_list(elements: List[Dict[str, Any]], out_path: str, include_entities: bool = False):
    """Generate a shot list file (CSV or Markdown) from parsed elements.

    Strategy:
    - Each scene heading becomes a row (type=SCENE)
    - Each explicit shot heading (! ...) becomes a row (type=SHOT)
    - Include short action summary snippet (first following action block)
    - Optionally append entity inventories (characters, locations, objects) when include_entities=True
    """
    rows, entities = build_shot_list(elements, include_entities=include_entities)

    is_csv = out_path.lower().endswith(".csv")
    if is_csv:
        import csv
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["#", "Type", "Scene", "Shot", "Summary"])
            for r in rows:
                writer.writerow([r["no"], r["type"], r["scene"], r["shot"], r["summary"]])
            if include_entities:
                # Insert blank separator row
                writer.writerow([])
                writer.writerow(["Inventory", "Category", "Name", "Count", "First Mention"])
                for cat in ("characters", "locations", "objects"):
                    for name, meta in entities.get(cat, {}).items():
                        writer.writerow(["", cat[:-1].title(), name, meta["count"], meta["first_index"]])
    else:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("| # | Type | Scene | Shot | Summary |\n")
            f.write("|---|------|-------|------|---------|\n")
            for r in rows:
                f.write(f"| {r['no']} | {r['type']} | {r['scene']} | {r['shot']} | {r['summary']} |\n")
            if include_entities and entities:
                f.write("\n## Entity Inventory\n\n")
                def write_subtable(cat: str, title: str):
                    items = entities.get(cat, {})
                    if not items:
                        return
                    f.write(f"### {title}\n\n")
                    f.write("| Name | Count | First Mention (element index) |\n")
                    f.write("|------|-------|------------------------------|\n")
                    for name, meta in sorted(items.items(), key=lambda kv: (-kv[1]['count'], kv[1]['first_index'])):
                        f.write(f"| {name} | {meta['count']} | {meta['first_index']} |\n")
                    f.write("\n")
                write_subtable("characters", "Characters")
                write_subtable("locations", "Locations")
                write_subtable("objects", "Objects / Props")

def build_shot_list(elements: List[Dict[str, Any]], include_entities: bool = False):
    """Build rows and optional entities for a shot list without writing files."""
    rows = []
    current_scene = ""
    for idx, el in enumerate(elements):
        t = el.get("type")
        if t == "scene":
            current_scene = el.get("text", "").upper()
            summary = _next_action_snippet(elements, idx)
            rows.append({"no": len(rows)+1, "type": "SCENE", "scene": current_scene, "shot": "", "summary": summary})
        elif t == "shot":
            shot_text = el.get("text", "").upper()
            summary = _next_action_snippet(elements, idx)
            rows.append({"no": len(rows)+1, "type": "SHOT", "scene": current_scene, "shot": shot_text, "summary": summary})
    entities = extract_entities(elements) if include_entities else {}
    return rows, entities

def render_shot_list_pdf(rows: List[Dict[str, Any]], entities: Dict[str, Any], out_path: str, font_path: str | None = None, font_size: int = 12, title: str = "Shot List", include_entities: bool = False, landscape: bool = False):
    """Render the shot list (and optionally entity inventories) into a PDF using Pillow.

    landscape: if True, page size is 11" x 8.5" to provide wider columns.
    """
    if landscape:
        PAGE_W, PAGE_H = int(11*72), int(8.5*72)
    else:
        PAGE_W, PAGE_H = int(8.5*72), int(11*72)
    MARGIN_L, MARGIN_R = int(0.75*72), int(0.75*72)
    MARGIN_T, MARGIN_B = int(0.75*72), int(0.75*72)
    font = load_font(size=font_size, override_path=font_path)
    bold_font = load_bold_variant(font, font_path, font_size) if font_path else font
    try:
        ascent, descent = font.getmetrics()  # type: ignore[attr-defined]
        line_h = ascent + descent + 4
    except AttributeError:
        line_h = int(font_size * 1.3)

    def measure(text: str, fnt) -> int:
        img_tmp = Image.new("RGB", (10,10))
        dr = ImageDraw.Draw(img_tmp)
        try:
            return int(dr.textlength(text, font=fnt))  # type: ignore[attr-defined]
        except AttributeError:
            try:
                left, _top, right, _bottom = fnt.getbbox(text)  # type: ignore[attr-defined]
                return right-left
            except (AttributeError, OSError):
                return len(text)*8

    # Determine column widths (max content up to a cap)
    col_keys = ["no", "type", "scene", "shot", "summary"]
    headers = {"no": "#", "type": "Type", "scene": "Scene", "shot": "Shot", "summary": "Summary"}
    max_widths = {k: measure(headers[k], bold_font) for k in col_keys}
    for r in rows:
        scene_txt = str(r["scene"]).replace("\n", " ")
        shot_txt = str(r["shot"]).replace("\n", " ")
        summary_txt = str(r["summary"]).replace("\n", " ")
        max_widths["no"] = max(max_widths["no"], measure(str(r["no"]), font))
        max_widths["type"] = max(max_widths["type"], measure(r["type"], font))
        max_widths["scene"] = max(max_widths["scene"], measure(scene_txt, font))
        max_widths["shot"] = max(max_widths["shot"], measure(shot_txt, font))
        max_widths["summary"] = max(max_widths["summary"], measure(summary_txt, font))

    # Cap some columns to leave room for summary
    # Allow wider caps in landscape mode
    cap_scene = int(PAGE_W*(0.18 if not landscape else 0.25))
    cap_shot = int(PAGE_W*(0.14 if not landscape else 0.20))
    cap_summary = int(PAGE_W*(0.38 if not landscape else 0.50))
    max_widths["scene"] = min(max_widths["scene"], cap_scene)
    max_widths["shot"] = min(max_widths["shot"], cap_shot)
    max_widths["summary"] = min(max_widths["summary"], cap_summary)

    gap = 16
    table_width = sum(max_widths[k] for k in col_keys) + gap*(len(col_keys)-1)
    if table_width > (PAGE_W - MARGIN_L - MARGIN_R):
        # Scale down proportionally
        scale = (PAGE_W - MARGIN_L - MARGIN_R) / table_width
        for k in max_widths:
            max_widths[k] = int(max_widths[k]*scale)
        table_width = sum(max_widths[k] for k in col_keys) + gap*(len(col_keys)-1)

    pages: List[Image.Image] = []
    img = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    dr = ImageDraw.Draw(img)
    y = MARGIN_T

    def new_page():
        nonlocal img, dr, y
        pages.append(img)
        img = Image.new("RGB", (PAGE_W, PAGE_H), "white")
        dr = ImageDraw.Draw(img)
        y = MARGIN_T
        if title:
            tw = measure(title, bold_font)
            dr.text(((PAGE_W - tw)//2, int(0.4*72)), title, font=bold_font, fill="black")
            y = int(0.4*72) + line_h + 10

    # Title on first page
    if title:
        tw = measure(title, bold_font)
        dr.text(((PAGE_W - tw)//2, int(0.4*72)), title, font=bold_font, fill="black")
        y = int(0.4*72) + line_h + 10

    def wrap_cell(text: str, width: int) -> List[str]:
        if not text:
            return [""]
        words = text.split()
        lines = []
        cur = ""
        for w in words:
            test = w if not cur else cur+" "+w
            if measure(test, font) <= width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                # If single word longer than width, hard break
                if measure(w, font) > width:
                    chunk = ""
                    for ch in w:
                        t2 = chunk+ch
                        if measure(t2, font) <= width:
                            chunk = t2
                        else:
                            if chunk:
                                lines.append(chunk)
                            chunk = ch
                    if chunk:
                        cur = chunk
                    else:
                        cur = ""
                else:
                    cur = w
        if cur:
            lines.append(cur)
        return lines or [""]

    def ensure_space(req_height: int):
        nonlocal y
        if y + req_height > PAGE_H - MARGIN_B:
            new_page()

    # Draw header row
    header_h = line_h
    ensure_space(header_h)
    x = MARGIN_L
    for k in col_keys:
        dr.text((x, y), headers[k], font=bold_font, fill="black")
        x += max_widths[k] + gap
    y += line_h + 2
    # Divider line
    dr.line((MARGIN_L, y, PAGE_W - MARGIN_R, y), fill="black")
    y += 6

    # Draw rows
    for r in rows:
        # Wrap cells
        wrapped_cells = {k: wrap_cell(str(r[k]), max_widths[k]) for k in col_keys}
        row_lines = max(len(v) for v in wrapped_cells.values())
        req_h = row_lines * line_h + 4
        ensure_space(req_h)
        for i_line in range(row_lines):
            x = MARGIN_L
            for k in col_keys:
                txt_line = wrapped_cells[k][i_line] if i_line < len(wrapped_cells[k]) else ""
                dr.text((x, y), txt_line, font=font, fill="black")
                x += max_widths[k] + gap
            y += line_h
        y += 4

    # Entities inventory (optionally) each category with subheading
    if include_entities and entities:
        # Add separator line before Entity Inventory section
        y += 10
        dr.line((MARGIN_L, y, PAGE_W - MARGIN_R, y), fill="black", width=2)
        y += 10
        # Start new page if insufficient space
        ensure_space(line_h * 5)
        dr.text((MARGIN_L, y), "Entity Inventory", font=bold_font, fill="black")
        y += line_h + 4
        for cat, title_cat in (("characters", "Characters"), ("locations", "Locations"), ("objects", "Objects / Props")):
            items = entities.get(cat, {})
            if not items:
                continue
            ensure_space(line_h * 4)
            dr.text((MARGIN_L, y), title_cat, font=bold_font, fill="black")
            y += line_h
            # Column headers
            hdrs = ["Name", "Count", "First"]
            colw = [int(PAGE_W*0.45), int(PAGE_W*0.12), int(PAGE_W*0.15)]
            x_positions = [MARGIN_L, MARGIN_L + colw[0] + 12, MARGIN_L + colw[0] + 12 + colw[1] + 12]
            for i, htxt in enumerate(hdrs):
                dr.text((x_positions[i], y), htxt, font=bold_font, fill="black")
            y += line_h + 2
            dr.line((MARGIN_L, y, PAGE_W - MARGIN_R, y), fill="black")
            y += 6
            for name, meta in sorted(items.items(), key=lambda kv: (-kv[1]['count'], kv[1]['first_index'])):
                ensure_space(line_h)
                dr.text((x_positions[0], y), name, font=font, fill="black")
                dr.text((x_positions[1], y), str(meta['count']), font=font, fill="black")
                dr.text((x_positions[2], y), str(meta['first_index']), font=font, fill="black")
                y += line_h
            # Add separator line between entity categories
            y += 10
            dr.line((MARGIN_L, y, PAGE_W - MARGIN_R, y), fill="black", width=1)
            y += 10

    pages.append(img)
    pages[0].save(out_path, save_all=True, append_images=pages[1:])

def render_shot_list_pdf_vector(rows: List[Dict[str, Any]], entities: Dict[str, Any], out_path: str, font_path: str | None = None, font_size: int = 12, title: str = "Shot List", include_entities: bool = False, landscape: bool = False):
    """Vector (ReportLab) version of shot list PDF. Falls back by raising ImportError if reportlab missing."""
    from reportlab.pdfgen import canvas  # type: ignore
    from reportlab.lib.pagesizes import letter, landscape as rl_landscape  # type: ignore
    from reportlab.pdfbase import pdfmetrics  # type: ignore
    from reportlab.pdfbase.ttfonts import TTFont  # type: ignore

    PAGE_W, PAGE_H = (letter if not landscape else rl_landscape(letter))
    margin_l = 36
    margin_r = 36
    margin_t = 54
    margin_b = 54

    base_font = "Courier"
    bold_font = "Courier-Bold"
    if font_path and os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont("SLMono", font_path))
            base_font = "SLMono"
            # Bold attempt
            root, ext = os.path.splitext(font_path)
            for cand in [root.replace("Regular","Bold")+ext, root+"-Bold"+ext, root+"Bold"+ext]:
                if os.path.exists(cand):
                    try:
                        pdfmetrics.registerFont(TTFont("SLMonoBold", cand))
                        bold_font = "SLMonoBold"
                        break
                    except OSError:
                        continue
        except OSError:
            pass

    line_h = font_size * 1.25

    def sw(txt: str, font_name: str = base_font, size: int = font_size) -> float:
        try:
            return pdfmetrics.stringWidth(txt, font_name, size)
        except (KeyError, ValueError):
            return len(txt) * (size * 0.6)

    # Column setup (reuse logic from raster but recompute widths with stringWidth)
    col_keys = ["no", "type", "scene", "shot", "summary"]
    headers = {"no": "#", "type": "Type", "scene": "Scene", "shot": "Shot", "summary": "Summary"}
    max_widths = {k: sw(headers[k], bold_font) for k in col_keys}
    for r in rows:
        scene_txt = str(r["scene"]).replace("\n", " ")
        shot_txt = str(r["shot"]).replace("\n", " ")
        summary_txt = str(r["summary"]).replace("\n", " ")
        max_widths["no"] = max(max_widths["no"], sw(str(r["no"])) )
        max_widths["type"] = max(max_widths["type"], sw(r["type"]))
        max_widths["scene"] = max(max_widths["scene"], sw(scene_txt))
        max_widths["shot"] = max(max_widths["shot"], sw(shot_txt))
        max_widths["summary"] = max(max_widths["summary"], sw(summary_txt))

    cap_scene = PAGE_W * (0.18 if not landscape else 0.25)
    cap_shot = PAGE_W * (0.14 if not landscape else 0.20)
    cap_summary = PAGE_W * (0.38 if not landscape else 0.50)
    max_widths["scene"] = min(max_widths["scene"], cap_scene)
    max_widths["shot"] = min(max_widths["shot"], cap_shot)
    max_widths["summary"] = min(max_widths["summary"], cap_summary)

    gap = 14
    table_width = sum(max_widths[k] for k in col_keys) + gap*(len(col_keys)-1)
    content_width = PAGE_W - margin_l - margin_r
    if table_width > content_width:
        scale = content_width / table_width
        for k in max_widths:
            max_widths[k] *= scale

    def wrap_cell(text: str, width: float) -> List[str]:
        if not text:
            return [""]
        words = text.split()
        lines: List[str] = []
        cur = ""
        for w in words:
            test = w if not cur else cur+" "+w
            if sw(test) <= width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                if sw(w) > width:
                    chunk = ""
                    for ch in w:
                        t2 = chunk+ch
                        if sw(t2) <= width:
                            chunk = t2
                        else:
                            if chunk:
                                lines.append(chunk)
                            chunk = ch
                    if chunk:
                        cur = chunk
                    else:
                        cur = ""
                else:
                    cur = w
        if cur:
            lines.append(cur)
        return lines or [""]

    c = canvas.Canvas(out_path, pagesize=(PAGE_W, PAGE_H))

    def draw_header(page_title: str, y_top: float) -> float:
        if page_title:
            c.setFont(base_font, font_size)
            title_w = sw(page_title)
            c.drawString((PAGE_W - title_w)/2, y_top, page_title)
            return y_top - line_h
        return y_top

    y = PAGE_H - margin_t
    y = draw_header(title, y)
    y -= line_h * 0.3

    def new_page():
        nonlocal y
        c.showPage()
        y = PAGE_H - margin_t
        y = draw_header(title, y)
        y -= line_h * 0.3

    def ensure_space(req_h: float):
        nonlocal y
        if y - req_h < margin_b:
            new_page()

    # Header row (draw text, then a line with consistent padding)
    ensure_space(line_h*2)
    x = margin_l
    c.setFont(bold_font, font_size)
    header_baseline = y
    for k in col_keys:
        c.drawString(x, header_baseline, headers[k])
        x += max_widths[k] + gap
    y = header_baseline - line_h * 0.25  # slightly larger baseline retention
    c.line(margin_l, y, PAGE_W - margin_r, y)
    y -= line_h * 0.75  # extra vertical space before first row

    # Rows
    c.setFont(base_font, font_size)
    for r in rows:
        cells_wrapped = {k: wrap_cell(str(r[k]), max_widths[k]) for k in col_keys}
        row_lines = max(len(v) for v in cells_wrapped.values())
        req_h = row_lines * line_h + line_h*0.2
        ensure_space(req_h)
        for i_line in range(row_lines):
            x = margin_l
            for k in col_keys:
                txt_line = cells_wrapped[k][i_line] if i_line < len(cells_wrapped[k]) else ""
                c.drawString(x, y, txt_line)
                x += max_widths[k] + gap
            y -= line_h
        y -= line_h*0.2

    # Entities
    if include_entities and entities:
        for cat, title_cat in (("characters","Characters"),("locations","Locations"),("objects","Objects / Props")):
            items = entities.get(cat, {})
            if not items:
                continue
            ensure_space(line_h*4)
            c.setFont(bold_font, font_size)
            c.drawString(margin_l, y, title_cat)
            y -= line_h
            c.setFont(bold_font, font_size-1)
            c.drawString(margin_l, y, "Name")
            c.drawString(margin_l+260, y, "Count")
            c.drawString(margin_l+320, y, "First")
            y -= line_h*0.8
            c.line(margin_l, y, PAGE_W - margin_r, y)
            y -= line_h*0.2
            c.setFont(base_font, font_size-1)
            for name, meta in sorted(items.items(), key=lambda kv: (-kv[1]['count'], kv[1]['first_index'])):
                ensure_space(line_h)
                c.drawString(margin_l, y, name)
                c.drawString(margin_l+260, y, str(meta['count']))
                c.drawString(margin_l+320, y, str(meta['first_index']))
                y -= line_h
            y -= line_h*0.3

    c.save()

def extract_entities(elements: List[Dict[str, Any]]) -> Dict[str, Dict[str, Dict[str, int]]]:
    """Heuristically extract characters, locations, and objects/props from parsed elements.

    Characters: from dialogue character cues.
    Locations: from scene headings (portion after INT./EXT. up to '-' time part).
    Objects: uppercase tokens (>=3 chars) appearing in action or shot text, excluding ignored words and already-known characters/locations.
    Returns mapping category -> name -> {count, first_index}.
    """
    char_map: Dict[str, Dict[str, int]] = {}
    loc_map: Dict[str, Dict[str, int]] = {}
    obj_map: Dict[str, Dict[str, int]] = {}

    time_words = {"DAY", "NIGHT", "MORNING", "EVENING", "LATER", "CONTINUOUS", "SAME TIME", "MOMENTS LATER", "DAWN", "DUSK"}
    ignore_obj = time_words | {"INT", "EXT", "INT/EXT", "AND", "THE", "A", "AN", "CUT", "TO", "FADE", "ON", "IN", "OUT", "ANGLE", "CLOSE", "UP", "POV", "WIDE", "TRACKING", "SHOT"}

    # Extract characters & locations first
    for idx, el in enumerate(elements):
        t = el.get("type")
        if t == "dialogue":
            name = el.get("character", "").upper()
            if name:
                entry = char_map.setdefault(name, {"count": 0, "first_index": idx})
                entry["count"] += 1
        elif t == "scene":
            raw = el.get("text", "").upper()
            # Strip leading INT./EXT. prefixes
            loc = re.sub(r"^(INT\.?/EXT\.?|INT\.?|EXT\.?)\s+", "", raw).strip()
            # Split off time segment using ' - '
            parts = [p.strip() for p in loc.split("-")]
            if parts:
                # Filter out trailing time words sequences
                # Reconstruct location excluding trailing time descriptors
                filtered = []
                for p in parts:
                    if p.replace(" ", "") in time_words:
                        break
                    filtered.append(p)
                loc_clean = " - ".join(filtered) if filtered else parts[0]
                loc_clean = loc_clean.strip()
                if loc_clean:
                    entry = loc_map.setdefault(loc_clean, {"count": 0, "first_index": idx})
                    entry["count"] += 1

    # Gather objects from action and shot text
    known_names = set(char_map.keys()) | set(loc_map.keys()) | ignore_obj
    token_re = re.compile(r"[A-Z][A-Z0-9'&]{2,}")
    for idx, el in enumerate(elements):
        if el.get("type") in {"action", "shot"}:
            txt = el.get("text", "").upper()
            for token in token_re.findall(txt):
                if token in known_names:
                    continue
                # Ignore if token is part of a longer location name (substring) or pure number
                if token.isdigit():
                    continue
                entry = obj_map.setdefault(token, {"count": 0, "first_index": idx})
                entry["count"] += 1

    return {"characters": char_map, "locations": loc_map, "objects": obj_map}

def _next_action_snippet(elements: List[Dict[str, Any]], start_index: int, max_len: int = 120) -> str:
    """Find the first action element after the given index and return a short snippet."""
    for el in elements[start_index+1:]:
        if el.get("type") == "action":
            txt = " ".join(el.get("text", "").split())
            if len(txt) > max_len:
                return txt[:max_len-1] + "…"
            return txt
        if el.get("type") in {"scene", "shot"}:  # stop at next heading
            break
    return ""

def write_fcpxml(elements: List[Dict[str, Any]], out_path: str, title: str, wpm: int = 160, fps: int = 25, include_titles: bool = False, title_seconds: float = 2.0, title_uid: str | None = None):
    """Export a minimal FCPXML (Final Cut Pro) document with:

    - Each scene heading as a chapter marker (blue) at its estimated start time.
    - Each shot heading as a keyword range (keyword: SHOT:<text>) spanning its estimated duration.

    Timing Heuristic:
    We estimate per-element duration based on word counts in action + dialogue blocks.
    Words per minute (wpm) -> words per second (wps). Each block gets duration = max(min_dur, words / wps).
    Scene/shot markers placed at cumulative time of first element belonging to that section.

    FCPXML Version: 1.10 (sufficient for markers & keyword ranges).
    """
    import xml.etree.ElementTree as ET
    # Compute word counts for timing
    wps = max(wpm / 60.0, 1e-6)
    min_block = 1.0  # seconds minimal duration for any textual block

    # Build a flattened list of timed segments
    segments = []  # (index, type, text, duration_seconds)
    for idx, el in enumerate(elements):
        t = el.get("type")
        if t == "action":
            words = len(el.get("text", "").split())
        elif t == "dialogue":
            words = len(" ".join(el.get("lines", [])).split()) + len(el.get("character"," ").split())
        elif t in {"scene", "shot"}:
            # scene & shot headings negligible duration but keep a token time slice
            words = max(len(el.get("text"," ").split()), 1)
        else:
            words = 0
        dur = max(words / wps, min_block if words>0 else 0.2)
        segments.append((idx, t, el, dur))

    # Total duration and mapping index->start time
    start_times = {}
    cursor = 0.0
    for idx, t, el, dur in segments:
        start_times[idx] = cursor
        cursor += dur
    total_seconds = cursor

    def sec_to_rational(seconds: float) -> str:
        """Return FCPXML rational time value with 's' suffix (e.g. '954/24s')."""
        frames = int(round(seconds * fps))
        return f"{frames}/{fps}s"

    # Build scene list with start/end times
    scenes = []  # {name,start,end}
    for idx, t, el, dur in segments:
        if t == "scene":
            scenes.append({
                "name": el.get("text", ""),
                "start": start_times[idx],
                "end": None  # fill later
            })
    for i, sc in enumerate(scenes):
        if i < len(scenes)-1:
            sc["end"] = scenes[i+1]["start"]
        else:
            sc["end"] = total_seconds

    # Gather shots for keyword ranges (assign later inside scene gaps)
    shots = []  # (start_sec,dur_sec,name)
    for idx, t, el, dur in segments:
        if t == "shot":
            shots.append((start_times[idx], dur, el.get("text", "").upper()))

    # Minimal FCPXML structure
    fcpxml = ET.Element("fcpxml", version="1.10")
    resources = ET.SubElement(fcpxml, "resources")
    format_id = "r1"
    ET.SubElement(resources, "format", id=format_id, frameDuration=f"1/{fps}s", width="1920", height="1080", colorSpace="1-1-1 (Rec. 709)")
    effect_id = "rTitle" if include_titles else ""
    if include_titles:
        # Provide a uid; FCPXML DTD requires uid attribute on effect resources.
        # Default corresponds to the built-in Basic Title. Allow override via CLI.
        resolved_uid = title_uid or "/Titles.localized/Basic Title.localized/Basic Title.moti"
        ET.SubElement(resources, "effect", id=effect_id, name="Basic Title", uid=resolved_uid)
    library = ET.SubElement(fcpxml, "library")
    event = ET.SubElement(library, "event", name=title)
    # Represent script as a single gap clip with duration
    timeline = ET.SubElement(event, "project", name=title)
    sequence = ET.SubElement(timeline, "sequence", duration=sec_to_rational(total_seconds), format=format_id, tcStart="0s", tcFormat="NDF")
    spine = ET.SubElement(sequence, "spine")
    # Color cycle for scene markers (visual differentiation via emoji prefix)
    color_emojis = ["🟥", "🟧", "🟨", "🟩", "🟦", "🟪"]

    for i, sc in enumerate(scenes):
        sc_start = sc["start"]
        sc_end = sc["end"] or sc_start
        sc_dur = max(sc_end - sc_start, 0.1)
        gap = ET.SubElement(spine, "gap", name=sc["name"], offset=sec_to_rational(sc_start), start="0s", duration=sec_to_rational(sc_dur))
        # Optional title first (media elements precede markers per DTD ordering)
        if include_titles and effect_id:
            frames_title = max(1, int(round(min(title_seconds, sc_dur) * fps)))
            dur_title = f"{frames_title}/{fps}s"
            title_el = ET.SubElement(gap, "title", name=sc["name"], ref=effect_id, offset="0s", start="0s", duration=dur_title, lane="1")
            text_container = ET.SubElement(title_el, "text")
            style_id = f"ts{i}"
            text_style_run = ET.SubElement(text_container, "text-style", attrib={"ref": style_id})
            text_style_run.text = sc["name"]
            style_def = ET.SubElement(title_el, "text-style-def", id=style_id)
            ET.SubElement(style_def, "text-style", font="Helvetica", fontSize="80")
        # Scene marker(s) follow media
        marker_label = f"{color_emojis[i % len(color_emojis)]} {sc['name']}"
        ET.SubElement(gap, "marker", start="0s", duration="0s", value=marker_label[:255], completed="0")
        # Shots within this scene range (keywords after markers allowed, but maintain ordering)
        for shot_start, shot_dur, shot_name in shots:
            if sc_start <= shot_start < sc_end:
                rel_start = max(0.0, shot_start - sc_start)
                ET.SubElement(gap, "keyword", start=sec_to_rational(rel_start), duration=sec_to_rational(shot_dur), value=f"SHOT:{shot_name}"[:255])

    # Write XML
    tree = ET.ElementTree(fcpxml)
    ET.indent(tree, space="  ", level=0)  # Python 3.9+
    with open(out_path, "w", encoding="utf-8") as f:
        tree.write(f, encoding="unicode")

    return {
        "total_seconds": total_seconds,
    "scene_markers": len(scenes),
    "shot_keywords": len(shots)
    }

def main():
    parser = argparse.ArgumentParser(description="Convert screenplay-flavored Markdown to PDF.")
    parser.add_argument("input_md")
    parser.add_argument("output_pdf")
    parser.add_argument("--title", default=None, help="Optional title to show on each page")
    parser.add_argument("--font", default=None, help="Path to a .ttf monospace font (e.g., DejaVuSansMono.ttf)")
    parser.add_argument("--size", type=int, default=12, help="Font size in points")
    parser.add_argument("--break-style", choices=["line", "page", "space"], default="page", help="How to render --- markers (default page break)")
    parser.add_argument("--transition-right", type=float, default=1.0, help="Right margin (in inches) for right-aligned transitions")
    parser.add_argument("--shot-list", default=None, help="Optional path to write a shot list (CSV or Markdown)")
    parser.add_argument("--shot-list-pdf", default=None, help="Optional path to write the shot list as a PDF (vector by default)")
    parser.add_argument("--shot-list-landscape", action="store_true", help="Render shot list PDF in landscape orientation")
    parser.add_argument("--vector", action="store_true", help="(Deprecated) Force vector screenplay PDF; now the default when ReportLab installed")
    parser.add_argument("--raster", action="store_true", help="Force legacy raster (image) screenplay PDF output")
    parser.add_argument("--shot-list-raster", action="store_true", help="Force raster shot list PDF (fallback)")
    parser.add_argument("--entities", action="store_true", help="Include extracted characters, locations, and objects in the shot list output")
    parser.add_argument("--fcpxml", default=None, help="Optional path to write a Final Cut Pro FCPXML with scene markers & shot keyword ranges")
    parser.add_argument("--wpm", type=int, default=160, help="Estimated words per minute for timing estimates in FCPXML export")
    parser.add_argument("--fps", type=int, default=25, help="Frame rate for FCPXML timecode (e.g. 24, 25, 30)")
    parser.add_argument("--fcpxml-titles", action="store_true", help="Include a title clip at the start of each scene in FCPXML")
    parser.add_argument("--fcpxml-title-duration", type=float, default=2.0, help="Duration (seconds) of each generated title clip (capped by scene length)")
    parser.add_argument("--fcpxml-title-uid", default=None, help="Override the effect uid for title clips (advanced; defaults to built-in Basic Title uid)")
    parser.add_argument("--fcpxml-title-ref", default=None, help="Path to an existing FCPXML to auto-detect a title effect uid from its <resources>")
    parser.add_argument("--fcpxml-title-auto", action="store_true", help="Attempt automatic common UID list if no explicit or reference UID provided")
    args = parser.parse_args()

    title = args.title
    if title is None:
        title = os.path.splitext(os.path.basename(args.input_md))[0].replace("_", " ").title()

    # Determine screenplay rendering mode (vector default if available, unless --raster forces image)
    use_vector = not args.raster  # default vector
    if args.vector:
        use_vector = True
    try:
        if use_vector:
            with open(args.input_md, "r", encoding="utf-8") as f:
                md_src = f.read()
            elements = parse_screenplay_markdown(md_src)
            draw_pdf_vector(elements, args.output_pdf, title=title, font_path=args.font, font_size=args.size, transition_right_in=args.transition_right)
        else:
            elements = convert_markdown_to_pdf(args.input_md, args.output_pdf, title=title, font_path=args.font, font_size=args.size, break_style=args.break_style, transition_right_in=args.transition_right)
    except SystemExit:  # ReportLab missing
        # Fallback to raster if vector requested but lib unavailable
        elements = convert_markdown_to_pdf(args.input_md, args.output_pdf, title=title, font_path=args.font, font_size=args.size, break_style=args.break_style, transition_right_in=args.transition_right)
        print("ReportLab not available, fell back to raster rendering.")
    if args.shot_list:
        write_shot_list(elements, args.shot_list, include_entities=args.entities)
        print(f"Wrote shot list {args.shot_list}{' (with entities)' if args.entities else ''}")
    if args.shot_list_pdf:
        rows, ents = build_shot_list(elements, include_entities=args.entities)
        if not args.shot_list_raster:
            try:
                render_shot_list_pdf_vector(rows, ents, args.shot_list_pdf, font_path=args.font, font_size=args.size, title=f"{title} - Shot List", include_entities=args.entities, landscape=args.shot_list_landscape)
                mode = "vector"
            except (RuntimeError, OSError):
                render_shot_list_pdf(rows, ents, args.shot_list_pdf, font_path=args.font, font_size=args.size, title=f"{title} - Shot List", include_entities=args.entities, landscape=args.shot_list_landscape)
                mode = "raster (fallback)"
        else:
            render_shot_list_pdf(rows, ents, args.shot_list_pdf, font_path=args.font, font_size=args.size, title=f"{title} - Shot List", include_entities=args.entities, landscape=args.shot_list_landscape)
            mode = "raster"
        orient = " landscape" if args.shot_list_landscape else ""
        print(f"Wrote shot list PDF{orient} ({mode}) {args.shot_list_pdf}{' (with entities)' if args.entities else ''}")
    if args.fcpxml:
        try:
            # Resolve title UID (priority: explicit > ref file > auto list > default basic UID)
            resolved_uid = args.fcpxml_title_uid
            if not resolved_uid and args.fcpxml_title_ref:
                def _detect_uid_from_xml(path: str) -> str | None:
                    import xml.etree.ElementTree as ET
                    try:
                        tree = ET.parse(path)
                    except (OSError, ET.ParseError):
                        return None
                    root = tree.getroot()
                    # Accept typical names in order
                    preferred = ["Basic Title", "Basic", "Build In/Out", "Build In:Out"]
                    effects = root.findall('.//resources/effect')
                    chosen_uid = None
                    for name in preferred:
                        for eff in effects:
                            if eff.get('name') == name and eff.get('uid'):
                                return eff.get('uid')
                    # fallback first effect with uid
                    for eff in effects:
                        if eff.get('uid'):
                            chosen_uid = eff.get('uid')
                            break
                    return chosen_uid
                resolved_uid = _detect_uid_from_xml(args.fcpxml_title_ref)
                if resolved_uid:
                    print(f"Detected title uid from reference: {resolved_uid}")
                else:
                    print("Could not detect title uid from reference file.")
            if not resolved_uid and args.fcpxml_title_auto:
                # Common built-in candidates (will still need to exist on system)
                common_uids = [
                    "/Titles.localized/Basic Title.localized/Basic Title.moti",
                    "/Titles.localized/Build In:Out.localized/Build In:Out.moti",
                    "/Titles.localized/Build In-Out.localized/Build In-Out.moti",
                    "/Titles.localized/Basic.localized/Basic.moti",
                ]
                resolved_uid = common_uids[0]
                print(f"Auto-selected title uid candidate: {resolved_uid}")
            write_fcpxml(
                elements,
                args.fcpxml,
                title=title,
                wpm=args.wpm,
                fps=args.fps,
                include_titles=args.fcpxml_titles,
                title_seconds=args.fcpxml_title_duration,
                title_uid=resolved_uid,
            )
            extra = " + titles" if args.fcpxml_titles else ""
            print(f"Wrote FCPXML {args.fcpxml} (markers & keyword ranges{extra}, {args.fps}fps, {args.wpm}wpm)")
        except (OSError, ValueError) as exc:
            print(f"Failed to write FCPXML: {exc}")
    print(f"Wrote {args.output_pdf}")

if __name__ == "__main__":
    main()
