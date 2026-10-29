"""Everything this project borrows from its two pinned parents, called once.
If an upgrade of either breaks one, this fails first."""


def test_borrowed_from_the_mystery_engine(tmp_path):
    from paperbackwriter.outline import batches, checkpoints, sections
    from paperbackwriter.plan import FIXED, WORD_CAP, check_plan
    assert checkpoints(24) == (7, 12, 17, 21, 24)
    assert batches(24)[0] == (1, 7)
    assert sections("Chapter 1: A\n\nx\n") == {1: ("Chapter 1: A", "x")}
    assert WORD_CAP == 2000 and "canon.md" in FIXED and "audit.md" in FIXED
    assert "Missing 01_solution_and_suspects.md" in check_plan(tmp_path)["errors"]


def test_borrowed_from_the_scifi_engine(tmp_path):
    from pbw_scifi.calibrate import write_chapters
    from pbw_scifi.exposition import DEFAULT_THRESHOLD, _chapter_files
    from pbw_scifi.reads import _load, _quotes, _staged_text
    from pbw_scifi.spoilers import load_terms
    assert DEFAULT_THRESHOLD == 300
    assert write_chapters([(1, "I", "Prose.")], tmp_path) == 1
    assert _chapter_files(tmp_path) == [(1, "Chapter 1: I\n\nProse.\n")]
    assert _staged_text(tmp_path)[1].startswith("Chapter 1: I")
    assert list(_quotes({"a": [{"quote": "q", "chapter": 1}]})) == [{"quote": "q", "chapter": 1}]
    (tmp_path / "t.txt").write_text("# c\n\\bx\\b\n")
    assert load_terms(tmp_path / "t.txt") == [r"\bx\b"]
    (tmp_path / "j.json").write_text('{"a": 1}')
    assert _load(tmp_path / "j.json") == {"a": 1}
