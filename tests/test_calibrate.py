from pbw_romance.calibrate import split_gutenberg
from pbw_romance.cli import main

SAMPLE = ("Header\r\n*** START OF THE PROJECT GUTENBERG EBOOK PERSUASION ***\r\n\r\n"
          "Contents\r\n\r\n CHAPTER I.\r\n CHAPTER II.\r\n\r\n"
          "CHAPTER I.\r\n\r\n\r\nSir Walter Elliot, of _Kellynch_\r\nHall, was vain.\r\n\r\nHe read.\r\n\r\n"
          "CHAPTER II.\r\n\r\n\r\nMr Shepherd spoke.\r\n\r\n"
          "*** END OF THE PROJECT GUTENBERG EBOOK PERSUASION ***\r\nLicence")


def test_untitled_chapters_split_and_the_contents_are_skipped():
    assert split_gutenberg(SAMPLE) == [
        (1, "I", "Sir Walter Elliot, of *Kellynch* Hall, was vain.\n\nHe read."),
        (2, "II", "Mr Shepherd spoke."),
    ]


def test_import_reference_command(tmp_path):
    src = tmp_path / "pg105.txt"
    src.write_text(SAMPLE)
    assert main(["import-reference", str(src), str(tmp_path / "out")]) == 0
    assert (tmp_path / "out" / "ch02.txt").read_text() == "Chapter 2: II\n\nMr Shepherd spoke.\n"
