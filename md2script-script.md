# Building ScriptMD2PDF with Claude Code: From Idea to Production

**Target Duration:** 8-10 minutes (~1,200-1,500 words)
**Target Audience:** Developers, technical creators, AI-assisted development enthusiasts
**Key Topics:** Python development, AI pair programming, automation tools, screenplay formatting

---

## HOOK (0:00-0:15)

### COLD OPEN - EDITOR SCREEN

[B-ROLL: Screen recording showing a simple markdown file transforming into a professional screenplay PDF]

What if I told you that **every screenplay you've ever seen** follows an incredibly strict format... and that we built a tool to automate it **entirely using AI pair programming**?

[B-ROLL: Quick cuts of professional screenplays, Final Cut Pro timeline, markdown syntax]

Today I'm showing you how we built ScriptMD2PDF with Claude Code - and why this changes everything about **AI-assisted development**.

---

## INTRO & CONTEXT (0:15-1:00)

### THE PROBLEM

[B-ROLL: Split screen - complex screenplay software on left, simple text editor on right]

Here's the thing about writing screenplays: the **formatting is brutal**. You've got scene headings at 1.5 inches, dialogue at 2.5 inches, character names at 3.5 inches... and if you get it wrong, your script looks **immediately unprofessional**.

Traditional solutions? Either **expensive software** like Final Draft that costs hundreds of dollars, or **complex LaTeX templates** that require a computer science degree to configure.

[B-ROLL: Frustrated user switching between multiple applications]

But what if you just want to **write in markdown** - the simplest, most portable format on earth - and get a **perfectly formatted screenplay PDF** out the other end?

That's exactly what we built. And we did it **with Claude Code as our AI pair programmer**.

---

## WHAT IS SCRIPTMD2PDF? (1:00-2:30)

### CORE CONCEPT

[B-ROLL: Side-by-side comparison - markdown source on left, rendered PDF on right]

ScriptMD2PDF is a **Python-powered conversion tool** that takes screenplay-flavored markdown and outputs **production-ready PDFs** that follow industry-standard formatting.

Here's what the syntax looks like:

[ON-SCREEN TEXT: Markdown example]
```
### INT. KITCHEN - DAY

The morning light filters through venetian blinds.

@ALEX
(whispering)
Did you hear that?

@JORDAN
We need to leave. Now.

>> CUT TO:
```

**Three hash marks** for scene headings. **At-symbol** for character names. **Double arrows** for transitions. That's it.

[B-ROLL: Live conversion demo showing the transformation]

The tool handles all the heavy lifting: **proper margins**, **bold scene headings**, **monospaced fonts**, **page breaks** - everything a professional screenplay needs.

### BONUS FEATURES

[B-ROLL: Showing shot list PDF, Final Cut Pro timeline import]

But here's where it gets **really interesting**. We didn't just build a PDF converter. We built an **entire production pipeline tool**.

**Shot list generation** - extracts every scene and shot heading into structured tables, markdown, CSV, or PDF format.

**Entity extraction** - automatically catalogs every character, location, and prop mentioned in your script.

**Final Cut Pro integration** - exports FCPXML timelines with scene markers and shot keywords, giving you a **head start on your edit** before you've shot a single frame.

---

## THE CLAUDE CODE DEVELOPMENT PROCESS (2:30-5:00)

### CHOOSING THE RIGHT APPROACH

[B-ROLL: Terminal window showing project structure]

When we started this project, we had **three core principles** from the beginning:

**One:** Simplicity over complexity.
**Two:** Clarity over cleverness.
**Three:** Maintainability over optimization.

[B-ROLL: CLAUDE.md file displayed]

These weren't just nice-to-have guidelines - they were **hard requirements** documented in our codebase. And Claude Code helped us **enforce them at every step**.

### DEVELOPMENT WORKFLOW

[B-ROLL: Split screen - Claude Code interface on left, code editor on right]

Here's how the collaboration worked. Instead of writing code from scratch, I would **describe the feature** I wanted - like "I need to parse scene headings from markdown that start with three hash marks."

Claude Code would **analyze the existing codebase**, understand our architectural patterns, and suggest an implementation that **fit our style**.

[B-ROLL: Code being generated, then refined through conversation]

But here's the key: it wasn't just **generating code**. It was having a **conversation about design decisions**.

"Should we use regex or a state machine for parsing?"
"How do we handle edge cases like nested parentheticals in dialogue?"
"What's the right abstraction for rendering engines?"

### MAINTAINING QUALITY STANDARDS

[B-ROLL: Test coverage report, pytest output]

We required **80% code coverage** for all new features. Claude Code didn't just write the implementation - it wrote the **tests alongside it**.

[ON-SCREEN: Test example]

When we added vector PDF rendering using ReportLab, Claude generated:
- Unit tests for font loading
- Integration tests for the full pipeline
- Edge case handling for missing bold fonts

[B-ROLL: Git commit history showing conventional commits]

Every commit followed the **conventional commits specification**: `feat:`, `fix:`, `refactor:`. This meant our changelog was **automatically generated** and our version bumps were **semantically correct**.

### DATABASE EVOLUTION

[B-ROLL: Database schema diagram, migration files]

As we added features like user sessions and conversion history, the database schema evolved. But we never made **manual schema changes**.

Every change went through **proper migrations** - and we kept our `database.dbml` file **up to date** as the single source of truth.

[ON-SCREEN: DBML file excerpt]

Claude Code would update the schema documentation **at the same time** it generated migration scripts. No drift, no confusion, no "wait, what version is production running?"

---

## TECHNICAL DEEP DIVE (5:00-7:00)

### THE RENDERING CHALLENGE

[B-ROLL: Code walkthrough of rendering engines]

One of the **trickiest challenges** was rendering. We needed two engines:

**Vector rendering** - using ReportLab for crisp, selectable text that looks **razor-sharp** at any zoom level.

**Raster rendering** - using Pillow as a fallback with **zero external dependencies** beyond the Python standard library.

[B-ROLL: Side-by-side PDF comparison - vector vs raster]

The vector output is **objectively better** - smaller file size, searchable text, perfect fonts. But the raster version **just works** even on systems without ReportLab installed.

### INTELLIGENT FONT HANDLING

[B-ROLL: Font detection code, system fonts directory]

Here's a detail most people wouldn't notice: **bold scene headings**.

The tool attempts to **auto-detect** a bold variant of your monospace font by pattern-matching filenames. `DejaVuSansMono-Regular.ttf` becomes `DejaVuSansMono-Bold.ttf`.

If it can't find one? It **simulates bold** by drawing the text twice with a tiny horizontal offset. Clever, right?

[ON-SCREEN: Before/after comparison showing simulated bold]

This is the kind of **thoughtful detail** that emerged from iterating with Claude Code. It suggested the fallback approach when we were stuck on font variants.

### WEB INTERFACE & DEPLOYMENT

[B-ROLL: Web interface demo - drag and drop, live editor]

We didn't stop at the CLI. We built a **FastAPI web application** with drag-and-drop upload and a **live markdown editor**.

[B-ROLL: Docker build process, Raspberry Pi]

The entire stack runs in **Docker containers** deployed to a **Raspberry Pi** - yes, a Raspberry Pi - using our **local container registry** at `192.168.2.1:5000`.

**Security features:**
- File type validation (markdown only)
- 1MB upload limit
- Rate limiting (5 requests per minute)
- **No file storage** - everything processed in-memory

[B-ROLL: GitHub Actions workflow]

Our **CI/CD pipeline** runs tests on every commit, builds multi-platform Docker images for ARM and x86, and pushes to our registry - all automated through **GitHub Actions**.

---

## KEY TAKEAWAYS (7:00-8:30)

### WHAT WE LEARNED

[B-ROLL: Montage of development highlights]

Building ScriptMD2PDF with Claude Code taught us **three major lessons** about AI-assisted development:

**Number one:** AI is **not a replacement** for architectural thinking. We still made the big decisions about rendering engines, data structures, and API design. But Claude Code **accelerated implementation** by 3-4x.

**Number two:** Documentation and conventions **multiply AI effectiveness**. Our CLAUDE.md principles, conventional commits, and schema documentation meant Claude always knew **what good code looked like** for our project.

**Number three:** Test-driven development **works beautifully** with AI assistance. When you require tests for everything, the AI writes **more robust code** because it's thinking about edge cases from the start.

### THE REAL MAGIC

[B-ROLL: Live conversion demo - markdown to final PDF]

Here's what still amazes me: we built a tool that handles **screenplay parsing**, **vector PDF rendering**, **entity extraction**, **FCPXML timeline generation**, **web APIs**, **Docker deployment**, and **CI/CD automation**...

...in a codebase that's **clean**, **well-tested**, and **maintainable**.

That's the promise of AI-assisted development when you do it **thoughtfully**.

---

## CALL TO ACTION (8:30-9:00)

### WRAP UP

[B-ROLL: GitHub repository page]

ScriptMD2PDF is **free and open source** on GitHub at `kevinmcaleer/scriptmd2pdf`. You can use the CLI tool locally, or try the **web interface** at `md2script.kevs.wtf`.

If you're interested in **AI-assisted development**, building **automation tools**, or just want to see **clean Python architecture** in action - check out the repo.

[B-ROLL: Subscribe button animation]

And if you found this valuable, **subscribe** for more deep dives into development tools, AI workflows, and building things that **actually work in production**.

### FINAL THOUGHT

[ON-SCREEN: Simple markdown converting to beautiful PDF one last time]

The future of software development isn't AI **replacing** developers. It's AI **amplifying** what good developers can build.

We just proved it with ScriptMD2PDF.

Thanks for watching. Now go build something.

---

## PRODUCTION NOTES

**Visual Style:**
- Clean screen recordings with highlighted code sections
- Side-by-side comparisons (before/after, source/output)
- Subtle zoom-ins on key details
- Fast-paced cuts during feature showcases (1-2 second holds)
- Slower pace during technical explanations (3-4 second holds)

**Music:**
- Upbeat, tech-focused instrumental for intro/outro
- Softer background track during explanations
- Brief silence during key technical moments for emphasis

**Graphics Needed:**
- Animated logo reveal for ScriptMD2PDF
- Text overlays for key statistics (80% coverage, 3-4x speed)
- Highlighting for code snippets
- Comparison charts (traditional tools vs ScriptMD2PDF)

**Estimated Reading Time:** 1,450 words @ 160 WPM = ~9 minutes

**B-Roll Capture Checklist:**
- [ ] Markdown to PDF conversion (multiple examples)
- [ ] Web interface walkthrough
- [ ] Shot list generation in all formats
- [ ] FCPXML import into Final Cut Pro
- [ ] Docker build and deployment process
- [ ] GitHub repository tour
- [ ] Test suite execution
- [ ] Database schema visualization
- [ ] Font detection and rendering comparison
