# scriptmd2pdf

Convert a screenplay‑flavoured Markdown file into a properly formatted PDF (monospaced US Letter layout) using a lightweight Python script (no LaTeX / no external formatter required).

## Features

* Scene headings (`### INT. LOCATION - TIME`)
* Action paragraphs (plain text)
* Character cues (`@CHARACTER`)
* Parentheticals inside dialogue lines (`(whispering)`)
* Dialogue (lines following a character cue until a blank line)
* Transitions (`>> CUT TO:`) – right aligned
* Shot headings (`! CLOSE ON`)
* Forced page breaks (`---`) – always start a new page
* Bold scene headings (auto bold font variant; simulated if bold face missing)
* Block comments starting with `//` are ignored
* Block quotes / notes starting with single `>` are ignored (except `>>` transitions)
* Adjustable font, size, and transition right margin
* Optional shot list export (`--shot-list markdown|csv`) capturing scenes & shot headings with a first action summary snippet

## Installation

Requires Python 3.8+ and Pillow.

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install Pillow
```

(If Pillow is already installed you can skip.)

## Command Line Usage

```bash
python screenmd2pdf.py INPUT.md OUTPUT.pdf [options]
```

### Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `--title "My Title"` | (Derived from input filename) | Title printed centered on each page. |
| `--font /path/to/mono.ttf` | Auto-detected / built-in default | Use a specific TTF monospace font (e.g., DejaVuSansMono.ttf, Courier). |
| `--size 12` | 12 | Font size (points). |
| `--break-style page` | page | (Currently page breaks for `---` are always forced; this remains for forward compatibility.) |
| `--transition-right 1.0` | 1.0 | Right margin in inches for right‑aligned transitions. Smaller values pull transitions further left. |
| `--shot-list markdown` | (none) | Write a shot list beside the PDF. Pass `markdown` (table) or `csv`. Filename auto-derived next to output PDF. |

### Example

```bash
python screenmd2pdf.py example_screenplay.md script.pdf
```

## Shot List Export

Generate a structured list of all scene headings and shot headings (lines starting with `!`) in script order. Each row includes:

* Type: `SCENE` or `SHOT`
* Heading: The raw heading text (e.g. `INT. KITCHEN - DAY`, `CLOSE ON`)
* Summary: First non-empty action line following that heading (trimmed to ~120 chars)

### Markdown Shot List

```bash
python screenmd2pdf.py example_screenplay.md script.pdf --shot-list markdown
```

Produces (example):

```markdown
| Type  | Heading               | Summary                           |
| ----- | --------------------- | --------------------------------- |
| SCENE | INT. KITCHEN - DAY    | The sun burns through the mist... |
| SHOT  | CLOSE ON              | A detail description.             |
```

### CSV Shot List

```bash
python screenmd2pdf.py example_screenplay.md script.pdf --shot-list csv
```

Writes a `.csv` file (UTF-8) with columns: `type,heading,summary`.

Filenames are derived from the output PDF name, e.g. `script_shots.md` or `script_shots.csv` placed alongside the PDF.

If no descriptive action follows a heading, the summary cell is left blank.

## Markdown Syntax Reference

```markdown
### INT. KITCHEN - DAY        # Scene heading

Plain action text forms action paragraphs.

@ALEX                         # Character cue (leading '@' is stripped)
(whispering)                  # Optional parenthetical
We can't keep pretending...

@JORDAN
We stopped being normal...

>> CUT TO:                    # Transition (auto uppercased + colon if missing)

! CLOSE ON                    # Shot heading
A detail description.

---                           # Forced page break
```

### Notes

* Blank line separates blocks (scene, action, dialogue groups, etc.).
* Dialogue ends at the first blank line after a character cue (excluding parentheticals).
* Multiple consecutive parentheticals are allowed.
* Lines starting with `//` are removed before parsing.
* Lines starting with `>` (single) are treated as notes and removed; `>>` is reserved for transitions.

## Output Formatting (Approx.)

* Paper: US Letter 8.5" × 11".
* Margins / indents (approx):
  * Scene & Action: Left 1.5", Right 1".
  * Character: Left 3.5".
  * Dialogue: Left 2.5", Right 2.5".
  * Parenthetical: Left 3.0".
  * Transition: Right aligned (right margin adjustable with `--transition-right`).
* Monospaced layout using chosen / detected font.
* Scene headings rendered in bold (if a bold TTF variant of the chosen font is found; otherwise a simulated bold via overdraw).

### Bold Scene Headings

The script tries to locate a bold variant of the supplied (or auto-detected) font using common filename patterns (e.g. replacing *Regular* with *Bold*). If it cannot find one, it simulates bold by drawing the heading text twice with a very slight horizontal offset. This keeps dependencies minimal while giving headings visual weight.


### Page Breaks

`---` always forces a new page regardless of `--break-style`. The option is retained for future flexibility (line / space rendering modes could be re-enabled later).

## Example Minimal Script

```markdown
### INT. KITCHEN - DAY

@ALEX
(quietly)
Morning.

@JORDAN
Morning.

>> CUT TO:

### EXT. GARDEN - LATER

The sun burns through the mist.

---

### INT. OFFICE - DAY

@ALEX
We made it.
```

Run:

```bash
python screenmd2pdf.py sample.md sample.pdf
```

## Troubleshooting

| Issue | Cause | Fix |
| ----- | ----- | --- |
| PDF shows `@` before names | Cached old PDF / not re-run | Re-run command; ensure you saved the Markdown. |
| Transition missing | Line started with single `>` not `>>` | Use `>> CUT TO:`. |
| Font looks different | System font not found | Supply explicit `--font` pointing to a monospace TTF. |
| Page break not happening | Used `----` (4 dashes) or spaces | Use exactly `---` on its own line. |

## Extending

Ideas you can add:

* Scene numbering
* Title page (detect first heading / metadata block)
* Automatic continued markers (CONT'D)
* Fountain format import
* Revision colors / A-pages

## License

MIT (add a LICENSE file if distributing).

## Quick One-Liner

```bash
python screenmd2pdf.py my_script.md my_script.pdf --font /Library/Fonts/Courier\ New.ttf --size 12 --transition-right 1.0
```

Enjoy writing!
