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

import sys
import os
import argparse
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Any, Tuple

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
        except Exception:
            pass
    path = find_mono_font()
    if path:
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            pass
    return ImageFont.load_default()

def load_bold_variant(base_font: ImageFont.ImageFont, base_path: str | None, size: int) -> ImageFont.ImageFont:
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
            except Exception:  # noqa: BLE001
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
        text = el.get("text", "")
        lines = text.split("\n")
        buffer: List[str] = []
        def flush_buffer():
            if buffer:
                joined = "\n".join(buffer).strip()
                if joined:
                    processed.append({"type": "action", "text": joined})
                buffer.clear()
        for ln in lines:
            if ln.strip() in {"-", "--", "---"}:  # treat as break marker
                flush_buffer()
                processed.append({"type": "pagebreak"})
            else:
                buffer.append(ln)
        flush_buffer()

    # Final sanitation: remove any residual empty or dash-only action blocks
    sanitized: List[Dict[str, Any]] = []
    for el in processed:
        if el.get("type") == "action" and el.get("text", "").strip(" -\t") in {"", "-", "--", "---"}:
            continue
        sanitized.append(el)
    return sanitized

def draw_pdf(elements: List[Dict[str, Any]], out_path: str, title: str = "", font_path: str = None, font_size: int = 12, break_style: str = "page", transition_right_in: float = 1.0):
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
    ascent, descent = font.getmetrics()
    line_h = ascent + descent + 2  # small leading

    # Create canvas
    pages: List[Image.Image] = []
    img = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    draw = ImageDraw.Draw(img)
    y = MARGIN_T

    # Robust width measurement (works across Pillow variants)
    def text_width(s: str) -> float:
        try:
            return draw.textlength(s, font=font)
        except Exception:
            try:
                return font.getlength(s)
            except Exception:
                try:
                    # getbbox returns (l, t, r, b)
                    l, t, r, b = font.getbbox(s)
                    return r - l
                except Exception:
                    # worst-case fallback: approximate
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
        for l in wrapped:
            if align_right:
                tw = text_width(l)
                x = PAGE_W - right_margin - tw
            else:
                x = left
            if use_bold and bold_font != font:
                draw.text((x, y), l, font=bold_font, fill="black")
            elif use_bold and bold_font == font:
                # Simulate bold by overdrawing with slight offsets
                draw.text((x, y), l, font=font, fill="black")
                draw.text((x+0.6, y), l, font=font, fill="black")
            else:
                draw.text((x, y), l, font=font, fill="black")
            y += line_h
        y += extra_after

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

def convert_markdown_to_pdf(md_path: str, pdf_path: str, title: str = "", font_path: str = None, font_size: int = 12, break_style: str = "page", transition_right_in: float = 1.0):
    with open(md_path, "r", encoding="utf-8") as f:
        md = f.read()
    elements = parse_screenplay_markdown(md)
    draw_pdf(elements, pdf_path, title=title, font_path=font_path, font_size=font_size, break_style=break_style, transition_right_in=transition_right_in)
    return elements

def write_shot_list(elements: List[Dict[str, Any]], out_path: str):
    """Generate a shot list file (CSV or Markdown) from parsed elements.

    Strategy:
    - Each scene heading becomes a row (type=SCENE)
    - Each explicit shot heading (! ...) becomes a row (type=SHOT)
    - Optionally include a short action summary that immediately follows (first action block after the heading) truncated.
    """
    rows = []
    current_scene = ""
    for idx, el in enumerate(elements):
        t = el.get("type")
        if t == "scene":
            current_scene = el.get("text", "").upper()
            # Add scene as its own row
            summary = _next_action_snippet(elements, idx)
            rows.append({"no": len(rows)+1, "type": "SCENE", "scene": current_scene, "shot": "", "summary": summary})
        elif t == "shot":
            shot_text = el.get("text", "").upper()
            summary = _next_action_snippet(elements, idx)
            rows.append({"no": len(rows)+1, "type": "SHOT", "scene": current_scene, "shot": shot_text, "summary": summary})

    # Decide format
    if out_path.lower().endswith(".csv"):
        import csv
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["#", "Type", "Scene", "Shot", "Summary"])
            for r in rows:
                writer.writerow([r["no"], r["type"], r["scene"], r["shot"], r["summary"]])
    else:  # markdown table
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("| # | Type | Scene | Shot | Summary |\n")
            f.write("|---|------|-------|------|---------|\n")
            for r in rows:
                f.write(f"| {r['no']} | {r['type']} | {r['scene']} | {r['shot']} | {r['summary']} |\n")

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
    args = parser.parse_args()

    title = args.title
    if title is None:
        title = os.path.splitext(os.path.basename(args.input_md))[0].replace("_", " ").title()

    elements = convert_markdown_to_pdf(args.input_md, args.output_pdf, title=title, font_path=args.font, font_size=args.size, break_style=args.break_style, transition_right_in=args.transition_right)
    if args.shot_list:
        write_shot_list(elements, args.shot_list)
        print(f"Wrote shot list {args.shot_list}")
    print(f"Wrote {args.output_pdf}")

if __name__ == "__main__":
    main()
