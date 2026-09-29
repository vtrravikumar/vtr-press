from digitization.spellcheck import (
    apply_corrections,
    check_markdown,
    correct_prose,
    load_vocabulary,
)


class FakeEngine:
    def __init__(self, mapping):
        self.mapping = mapping

    def candidates(self, word):
        return set(self.mapping.get(word, ()))


def test_corrects_only_unique_one_edit_prose_candidates():
    source = "The enginer reviewed the manuscrpt."
    result = correct_prose(
        source,
        engine=FakeEngine({"enginer": {"engineer"}, "manuscrpt": {"manuscript"}}),
    )
    assert result.text == "The engineer reviewed the manuscript."
    assert [item.original for item in result.corrections] == ["enginer", "manuscrpt"]


def test_none_candidate_lookup_is_treated_as_no_suggestions():
    class EmptyLookupEngine:
        def candidates(self, word):
            return None

    source = "A manuscript sentence."
    result = correct_prose(source, engine=EmptyLookupEngine())
    assert result.text == source
    assert result.corrections == ()


def test_leaves_ambiguous_or_far_candidates_unchanged():
    source = "teh qzxpl"
    result = correct_prose(
        source,
        engine=FakeEngine({"teh": {"the", "ten"}, "qzxpl": {"example"}}),
    )
    assert result.text == source
    assert result.corrections == ()


def test_preserves_capitalized_names_and_custom_vocabulary():
    source = "Chennai Ravi Kumar OpenAl vtr-press"
    result = correct_prose(
        source,
        vocabulary={"OpenAl"},
        engine=FakeEngine({"chennai": {"chenna"}, "ravi": {"raiv"}}),
    )
    assert result.text == source
    assert result.corrections == ()


def test_excludes_code_url_path_table_and_abbreviation_lines():
    source = (
        "Code: recieve_data = parse(input_value)\n"
        "URL: https://example.com/teh-path\n"
        "Path: /tmp/manuscrpt.txt\n"
        "Field | teh\n"
        "Abbreviation: OCR, PDF, API\n"
        "The teh word is prose.\n"
    )
    result = correct_prose(source, engine=FakeEngine({"teh": {"the"}}))
    assert result.text.endswith("The the word is prose.\n")
    assert result.text.count("the") == 1
    assert len(result.corrections) == 1


def test_excludes_fenced_and_inline_code():
    source = "The teh word.\n```python\nteh = 1\n```\nUse `teh` literally.\n"
    result = correct_prose(source, engine=FakeEngine({"teh": {"the"}}))
    assert result.text == "The the word.\n```python\nteh = 1\n```\nUse `teh` literally.\n"
    assert len(result.corrections) == 1


def test_original_and_corrected_offsets_support_reversal():
    source = "teh and teh"
    result = correct_prose(source, engine=FakeEngine({"teh": {"the"}}))
    assert result.text == "the and the"
    first, second = result.corrections
    assert source[first.start:first.end] == first.original
    assert result.text[first.corrected_start:first.corrected_end] == first.corrected
    assert result.text[second.corrected_start:second.corrected_end] == second.corrected


def test_report_is_json_serializable_shape():
    result = correct_prose("teh", engine=FakeEngine({"teh": {"the"}}))
    report = result.to_report()
    assert report["engine"] == "pyspellchecker"
    assert report["correction_count"] == 1
    assert report["corrections"][0]["original"] == "teh"


def test_load_vocabulary_ignores_comments_and_blank_lines(tmp_path):
    vocab = tmp_path / "terms.txt"
    vocab.write_text("# project terms\n\nOpenAI\nvtr-press \n", encoding="utf-8")
    assert load_vocabulary(vocab) == frozenset({"openai", "vtr-press"})


def test_editing_does_not_change_input():
    source = "teh sentence"
    original = source[:]
    correct_prose(source, engine=FakeEngine({"teh": {"the"}}))
    assert source == original



def test_check_markdown_checks_headings_paragraphs_lists_and_link_labels():
    source = (
        "# Chagnes to the Manuscrpt\n\n"
        "This is teh opening paragraph. Please recieve it.\n\n"
        "- Review the chagnes\n"
        "- Correct teh spelling\n\n"
        "See [the manuscrpt](https://example.com/teh-path).\n"
    )
    result = check_markdown(
        source,
        engine=FakeEngine({
            "chagnes": {"changes"},
            "manuscrpt": {"manuscript"},
            "teh": {"the"},
            "recieve": {"receive"},
        }),
    )
    assert result.text == source
    assert [item.original for item in result.corrections] == [
        "Chagnes", "Manuscrpt", "teh", "recieve",
        "chagnes", "teh", "manuscrpt",
    ]
    assert all(
        source[item.start:item.end] == item.original
        for item in result.corrections
    )


def test_check_markdown_skips_inline_fenced_code_tables_and_destinations():
    source = (
        "Use `teh` literally, but correct teh here.\n"
        "```python\n"
        "teh = 'manuscrpt'\n"
        "```\n"
        "| Field | Value |\n"
        "| Chagnes | teh |\n"
        "[label teh](https://example.com/teh-path)\n"
    )
    result = check_markdown(
        source,
        engine=FakeEngine({"teh": {"the"}, "chagnes": {"changes"}}),
    )
    assert result.text == source
    assert [item.original for item in result.corrections] == ["teh", "teh"]
    assert [source[item.start:item.end] for item in result.corrections] == ["teh", "teh"]


def test_check_markdown_preserves_custom_terms_and_original_offsets():
    source = "# vtr-press\n\nOpenAI and chagnes.\n"
    result = check_markdown(
        source,
        vocabulary={"OpenAI"},
        engine=FakeEngine({"chagnes": {"changes"}, "openai": {"open"} }),
    )
    assert result.text is source
    assert len(result.corrections) == 1
    item = result.corrections[0]
    assert source[item.start:item.end] == "chagnes"
    assert item.context == source[max(0, item.start - 36):item.end + 36]


def test_check_markdown_masks_double_backtick_inline_code():
    source = "Keep ``teh`` as code, but correct teh outside.\n"
    result = check_markdown(source, engine=FakeEngine({"teh": {"the"}}))
    assert result.text == source
    assert [item.original for item in result.corrections] == ["teh"]
    item = result.corrections[0]
    assert source[item.start:item.end] == "teh"


def test_check_markdown_masks_reference_style_identifier_but_checks_label():
    source = "[manuscrpt][ref-manuscrpt]\n\n[ref-manuscrpt]: https://example.com/teh\n"
    result = check_markdown(
        source,
        engine=FakeEngine({"manuscrpt": {"manuscript"}, "ref": {"red"}, "teh": {"the"}}),
    )
    assert result.text == source
    assert [item.original for item in result.corrections] == ["manuscrpt"]


def test_check_markdown_fence_closer_must_match_opening_length():
    source = (
        "````python\n"
        "teh = 1\n"
        "```\n"
        "manuscrpt = 2\n"
        "````\n"
        "Correct teh here.\n"
    )
    result = check_markdown(
        source,
        engine=FakeEngine({"teh": {"the"}, "manuscrpt": {"manuscript"}}),
    )
    assert result.text == source
    assert [item.original for item in result.corrections] == ["teh"]
    item = result.corrections[0]
    assert source[item.start:item.end] == item.original


def test_apply_corrections_uses_original_offsets_right_to_left():
    source = "teh and manuscrpt"
    result = check_markdown(
        source,
        engine=FakeEngine({"teh": {"the"}, "manuscrpt": {"manuscript"}}),
    )
    assert apply_corrections(source, result.corrections) == "the and manuscript"
    assert source == "teh and manuscrpt"


def test_apply_corrections_rejects_stale_or_overlapping_spans():
    result = correct_prose("teh teh", engine=FakeEngine({"teh": {"the"}}))
    first, second = result.corrections
    import pytest
    with pytest.raises(ValueError, match="no longer matches"):
        apply_corrections("xxx teh", (first,))
    overlapping = (first, first.__class__(
        original="h", corrected="e", start=1, end=2,
        corrected_start=1, corrected_end=2, context="", reason="test",
        engine="test", engine_version="test",
    ))
    with pytest.raises(ValueError, match="overlap"):
        apply_corrections("teh teh", overlapping)


def test_no_spellcheck_markup_excludes_term_and_is_removed_from_temporary_text():
    from digitization.spellcheck import strip_no_spellcheck_markup

    source = "The herb is known as <no-spellcheck>baricum</no-spellcheck>."
    result = check_markdown(
        source,
        engine=FakeEngine({"baricum": {"barium"}, "known": {"knows"}}),
    )
    assert [item.original for item in result.corrections] == ["known"]
    corrected = apply_corrections(source, result.corrections)
    temporary = strip_no_spellcheck_markup(corrected)
    assert temporary == "The herb is knows as baricum."
    assert "<no-spellcheck>" not in temporary
    assert "</no-spellcheck>" not in temporary
    assert source == "The herb is known as <no-spellcheck>baricum</no-spellcheck>."
