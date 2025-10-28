import pytest
import os
import tempfile
from pathlib import Path
from screenmd2pdf import (
    parse_screenplay_markdown,
    find_mono_font,
    load_font,
    convert_markdown_to_pdf,
    write_shot_list,
    build_shot_list,
    extract_entities,
    write_fcpxml,
    draw_pdf_vector,
)


class TestMarkdownParsing:
    def test_parse_scene_heading(self):
        md = "### INT. KITCHEN - DAY"
        elements = parse_screenplay_markdown(md)
        assert len(elements) == 1
        assert elements[0]["type"] == "scene"
        assert elements[0]["text"] == "INT. KITCHEN - DAY"

    def test_parse_scene_heading_variations(self):
        variations = [
            "# INT. OFFICE - DAY",
            "## EXT. GARDEN - NIGHT",
            "### INT/EXT. CAR - MOVING"
        ]
        for md in variations:
            elements = parse_screenplay_markdown(md)
            assert elements[0]["type"] == "scene"

    def test_parse_action(self):
        md = "The sun rises over the city."
        elements = parse_screenplay_markdown(md)
        assert len(elements) == 1
        assert elements[0]["type"] == "action"
        assert elements[0]["text"] == "The sun rises over the city."

    def test_parse_character_cue(self):
        md = "@ALEX\nHello there."
        elements = parse_screenplay_markdown(md)
        assert len(elements) == 1
        assert elements[0]["type"] == "dialogue"
        assert elements[0]["character"] == "ALEX"
        assert "Hello there." in elements[0]["lines"]

    def test_parse_dialogue_with_parenthetical(self):
        md = "@JORDAN\n(whispering)\nWe need to go."
        elements = parse_screenplay_markdown(md)
        assert len(elements) == 1
        assert elements[0]["type"] == "dialogue"
        assert elements[0]["character"] == "JORDAN"
        assert "(whispering)" in elements[0]["parentheticals"]
        assert "We need to go." in elements[0]["lines"]

    def test_parse_transition(self):
        md = ">> CUT TO:"
        elements = parse_screenplay_markdown(md)
        assert len(elements) == 1
        assert elements[0]["type"] == "transition"
        assert elements[0]["text"] == "CUT TO:"

    def test_parse_transition_adds_colon(self):
        md = ">> FADE OUT"
        elements = parse_screenplay_markdown(md)
        assert elements[0]["text"] == "FADE OUT:"

    def test_parse_shot_heading(self):
        md = "! CLOSE ON"
        elements = parse_screenplay_markdown(md)
        assert len(elements) == 1
        assert elements[0]["type"] == "shot"
        assert elements[0]["text"] == "CLOSE ON"

    def test_parse_page_break(self):
        md = "---"
        elements = parse_screenplay_markdown(md)
        assert len(elements) == 1
        assert elements[0]["type"] == "pagebreak"

    def test_parse_ignores_comments(self):
        md = "// This is a comment\nAction text"
        elements = parse_screenplay_markdown(md)
        assert len(elements) == 1
        assert elements[0]["type"] == "action"
        assert elements[0]["text"] == "Action text"

    def test_parse_ignores_blockquotes(self):
        md = "> This is a note\nAction text"
        elements = parse_screenplay_markdown(md)
        assert len(elements) == 1
        assert elements[0]["type"] == "action"

    def test_parse_complex_screenplay(self):
        md = """### INT. COFFEE SHOP - DAY

The morning rush is in full swing.

@ALEX
(to barista)
Large coffee, please.

>> CUT TO:

! CLOSE ON - COFFEE CUP

Steam rises from the cup.
"""
        elements = parse_screenplay_markdown(md)
        assert len(elements) == 6
        assert elements[0]["type"] == "scene"
        assert elements[1]["type"] == "action"
        assert elements[2]["type"] == "dialogue"
        assert elements[3]["type"] == "transition"
        assert elements[4]["type"] == "shot"
        assert elements[5]["type"] == "action"

    def test_parse_multiple_dialogues(self):
        md = """@ALEX
Hello.

@JORDAN
Hi there."""
        elements = parse_screenplay_markdown(md)
        assert len(elements) == 2
        assert all(e["type"] == "dialogue" for e in elements)


class TestFontHandling:
    def test_find_mono_font(self):
        font_path = find_mono_font()
        # May be None on systems without standard fonts
        if font_path:
            assert os.path.exists(font_path)
            assert font_path.endswith(('.ttf', '.TTF'))

    def test_load_font_default(self):
        font = load_font()
        assert font is not None

    def test_load_font_with_size(self):
        font = load_font(size=14)
        assert font is not None

    def test_load_font_with_invalid_path(self):
        font = load_font(override_path="/nonexistent/font.ttf")
        assert font is not None  # Should fall back to default


class TestPDFGeneration:
    def test_convert_markdown_to_pdf(self):
        md_content = """### INT. TEST SCENE - DAY

Test action.

@TEST
Test dialogue.
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            md_path = os.path.join(tmpdir, "test.md")
            pdf_path = os.path.join(tmpdir, "test.pdf")

            with open(md_path, "w") as f:
                f.write(md_content)

            elements = convert_markdown_to_pdf(md_path, pdf_path)

            assert os.path.exists(pdf_path)
            assert len(elements) == 3
            assert os.path.getsize(pdf_path) > 0

    def test_convert_with_title(self):
        md_content = "### INT. TEST - DAY"
        with tempfile.TemporaryDirectory() as tmpdir:
            md_path = os.path.join(tmpdir, "test.md")
            pdf_path = os.path.join(tmpdir, "test.pdf")

            with open(md_path, "w") as f:
                f.write(md_content)

            convert_markdown_to_pdf(md_path, pdf_path, title="Test Script")
            assert os.path.exists(pdf_path)

    def test_vector_pdf_generation(self):
        try:
            import reportlab
            md_content = "### INT. TEST - DAY\n\nTest action."
            elements = parse_screenplay_markdown(md_content)

            with tempfile.TemporaryDirectory() as tmpdir:
                pdf_path = os.path.join(tmpdir, "test_vector.pdf")
                draw_pdf_vector(elements, pdf_path, title="Test")
                assert os.path.exists(pdf_path)
                assert os.path.getsize(pdf_path) > 0
        except ImportError:
            pytest.skip("ReportLab not installed")


class TestShotList:
    def test_build_shot_list_scenes(self):
        md = """### INT. KITCHEN - DAY

Making breakfast.

### EXT. GARDEN - DAY

Walking through flowers.
"""
        elements = parse_screenplay_markdown(md)
        rows, entities = build_shot_list(elements, include_entities=False)

        assert len(rows) == 2
        assert rows[0]["type"] == "SCENE"
        assert rows[0]["scene"] == "INT. KITCHEN - DAY"
        assert "breakfast" in rows[0]["summary"].lower()

    def test_build_shot_list_with_shots(self):
        md = """### INT. ROOM - DAY

! CLOSE ON

A detail shot.
"""
        elements = parse_screenplay_markdown(md)
        rows, entities = build_shot_list(elements, include_entities=False)

        assert len(rows) == 2
        assert rows[0]["type"] == "SCENE"
        assert rows[1]["type"] == "SHOT"
        assert rows[1]["shot"] == "CLOSE ON"

    def test_write_shot_list_markdown(self):
        md = "### INT. TEST - DAY\n\nTest action."
        elements = parse_screenplay_markdown(md)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "shots.md")
            write_shot_list(elements, output_path, include_entities=False)

            assert os.path.exists(output_path)
            with open(output_path) as f:
                content = f.read()
                assert "Type" in content
                assert "Scene" in content
                assert "SCENE" in content

    def test_write_shot_list_csv(self):
        md = "### INT. TEST - DAY\n\nTest action."
        elements = parse_screenplay_markdown(md)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "shots.csv")
            write_shot_list(elements, output_path, include_entities=False)

            assert os.path.exists(output_path)
            with open(output_path) as f:
                content = f.read()
                assert "Type" in content
                assert "Scene" in content


class TestEntityExtraction:
    def test_extract_characters(self):
        md = """@ALEX
Hello.

@JORDAN
Hi there.

@ALEX
How are you?
"""
        elements = parse_screenplay_markdown(md)
        entities = extract_entities(elements)

        assert "characters" in entities
        assert "ALEX" in entities["characters"]
        assert "JORDAN" in entities["characters"]
        assert entities["characters"]["ALEX"]["count"] == 2
        assert entities["characters"]["JORDAN"]["count"] == 1

    def test_extract_locations(self):
        md = """### INT. KITCHEN - DAY

Action.

### EXT. GARDEN - NIGHT

More action.

### INT. KITCHEN - LATER

Back to kitchen.
"""
        elements = parse_screenplay_markdown(md)
        entities = extract_entities(elements)

        assert "locations" in entities
        assert "KITCHEN" in entities["locations"]
        assert entities["locations"]["KITCHEN"]["count"] == 2

    def test_extract_objects(self):
        md = """### INT. ROOM - DAY

He picks up the LAPTOP and opens the BRIEFCASE.
The PHONE rings loudly.
"""
        elements = parse_screenplay_markdown(md)
        entities = extract_entities(elements)

        assert "objects" in entities
        # Should extract uppercase nouns that aren't characters/locations
        assert any(obj in entities["objects"] for obj in ["LAPTOP", "BRIEFCASE", "PHONE"])

    def test_entities_first_index(self):
        md = """### INT. ROOM - DAY

@ALEX
Hello.

@JORDAN
Hi.

@ALEX
Bye.
"""
        elements = parse_screenplay_markdown(md)
        entities = extract_entities(elements)

        # ALEX appears first at index 1, JORDAN at index 2
        assert entities["characters"]["ALEX"]["first_index"] < entities["characters"]["JORDAN"]["first_index"]


class TestFCPXMLExport:
    def test_write_fcpxml(self):
        try:
            import xml.etree.ElementTree as ET

            md = """### INT. SCENE ONE - DAY

Action one.

### INT. SCENE TWO - DAY

Action two.
"""
            elements = parse_screenplay_markdown(md)

            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = os.path.join(tmpdir, "test.fcpxml")
                result = write_fcpxml(elements, output_path, title="Test Script")

                assert os.path.exists(output_path)
                assert result["scene_markers"] == 2

                # Validate XML structure
                tree = ET.parse(output_path)
                root = tree.getroot()
                assert root.tag == "fcpxml"

        except ImportError:
            pytest.skip("XML module not available")

    def test_fcpxml_with_shots(self):
        try:
            md = """### INT. ROOM - DAY

! CLOSE ON

Detail shot.
"""
            elements = parse_screenplay_markdown(md)

            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = os.path.join(tmpdir, "test.fcpxml")
                result = write_fcpxml(elements, output_path, title="Test")

                assert result["scene_markers"] == 1
                assert result["shot_keywords"] == 1

        except ImportError:
            pytest.skip("XML module not available")

    def test_fcpxml_timing_estimation(self):
        md = """### INT. ROOM - DAY

This is a longer action paragraph with many words to test the timing estimation feature.
It should result in a longer duration based on word count and words per minute calculation.
"""
        elements = parse_screenplay_markdown(md)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.fcpxml")
            result = write_fcpxml(elements, output_path, title="Test", wpm=160)

            assert result["total_seconds"] > 0


class TestEdgeCases:
    def test_empty_markdown(self):
        elements = parse_screenplay_markdown("")
        assert len(elements) == 0

    def test_only_whitespace(self):
        elements = parse_screenplay_markdown("   \n\n   \n")
        assert len(elements) == 0

    def test_multiple_blank_lines(self):
        md = "### INT. ROOM - DAY\n\n\n\nAction."
        elements = parse_screenplay_markdown(md)
        assert len(elements) == 2

    def test_dialogue_without_lines(self):
        md = "@CHARACTER"
        elements = parse_screenplay_markdown(md)
        assert len(elements) == 1
        assert elements[0]["type"] == "dialogue"
        assert elements[0]["lines"] == []

    def test_very_long_line(self):
        long_text = "A" * 500
        md = f"### INT. ROOM - DAY\n\n{long_text}"
        elements = parse_screenplay_markdown(md)
        assert len(elements) == 2

    def test_special_characters(self):
        md = "### INT. CAFÉ - DAY\n\n@RENÉ\nBonjour!"
        elements = parse_screenplay_markdown(md)
        assert elements[0]["text"] == "INT. CAFÉ - DAY"
        assert elements[1]["character"] == "RENÉ"

    def test_mixed_line_endings(self):
        md = "### INT. ROOM - DAY\r\n\r\nAction.\n\n@ALEX\r\nHello."
        elements = parse_screenplay_markdown(md)
        assert len(elements) == 3

    def test_consecutive_page_breaks(self):
        md = "---\n\n---\n\n---"
        elements = parse_screenplay_markdown(md)
        assert len(elements) == 3
        assert all(e["type"] == "pagebreak" for e in elements)


class TestIntegration:
    def test_full_screenplay_workflow(self):
        screenplay = """### INT. COFFEE SHOP - DAY

ALEX sits at a corner table, laptop open.

@ALEX
(to himself)
Just one more line of code.

The BARISTA approaches.

@BARISTA
Another refill?

@ALEX
Please. Make it a double.

>> CUT TO:

### EXT. STREET - LATER

Alex walks home, energized.

! CLOSE ON - COFFEE CUP

Empty, but still warm.

---

### INT. ALEX'S APARTMENT - NIGHT

The laptop screen glows in the darkness.

@ALEX
(typing furiously)
Finally. It works!
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            md_path = os.path.join(tmpdir, "screenplay.md")
            pdf_path = os.path.join(tmpdir, "screenplay.pdf")
            shots_path = os.path.join(tmpdir, "shots.md")
            fcpxml_path = os.path.join(tmpdir, "screenplay.fcpxml")

            with open(md_path, "w") as f:
                f.write(screenplay)

            # Generate PDF
            elements = convert_markdown_to_pdf(md_path, pdf_path, title="Test Screenplay")
            assert os.path.exists(pdf_path)

            # Generate shot list
            write_shot_list(elements, shots_path, include_entities=True)
            assert os.path.exists(shots_path)

            # Generate FCPXML
            write_fcpxml(elements, fcpxml_path, title="Test Screenplay")
            assert os.path.exists(fcpxml_path)

            # Verify entity extraction
            entities = extract_entities(elements)
            assert "ALEX" in entities["characters"]
            assert "BARISTA" in entities["characters"]
            assert entities["characters"]["ALEX"]["count"] == 3


class TestShotListPDF:
    def test_render_shot_list_pdf(self):
        from screenmd2pdf import render_shot_list_pdf

        md = """### INT. ROOM - DAY

Action here.

! CLOSE ON

Detail.
"""
        elements = parse_screenplay_markdown(md)
        rows, entities = build_shot_list(elements, include_entities=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "shotlist.pdf")
            render_shot_list_pdf(rows, entities, pdf_path, title="Shot List")

            assert os.path.exists(pdf_path)
            assert os.path.getsize(pdf_path) > 0

    def test_render_shot_list_pdf_landscape(self):
        from screenmd2pdf import render_shot_list_pdf

        md = "### INT. ROOM - DAY\n\nAction."
        elements = parse_screenplay_markdown(md)
        rows, entities = build_shot_list(elements, include_entities=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "shotlist_landscape.pdf")
            render_shot_list_pdf(rows, entities, pdf_path, title="Shot List", landscape=True)

            assert os.path.exists(pdf_path)

    def test_render_shot_list_pdf_with_entities(self):
        from screenmd2pdf import render_shot_list_pdf

        md = """### INT. ROOM - DAY

@ALEX
Hello.

@JORDAN
Hi.
"""
        elements = parse_screenplay_markdown(md)
        rows, entities = build_shot_list(elements, include_entities=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "shotlist_entities.pdf")
            render_shot_list_pdf(rows, entities, pdf_path, title="Shot List", include_entities=True)

            assert os.path.exists(pdf_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
