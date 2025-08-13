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
* Block comments starting with `//` are ignored
* Block quotes / notes starting with single `>` are ignored (except `>>` transitions)
* Adjustable font, size, and transition right margin

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

### Example

```bash
python screenmd2pdf.py example_screenplay.md script.pdf
```

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
