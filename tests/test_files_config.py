import pytest

from raffle_cli import files
from raffle_cli.config import ConfigError, load_config, setup_files
from raffle_cli.files import DataFileError
from raffle_cli.raffle import Winner


def write(path, text):
    path.write_text(text, encoding="utf-8")
    return path


def test_read_participants_strips_and_warns_on_duplicates(tmp_path):
    p = write(tmp_path / "p.csv", "name,lastname\n Ada , Lovelace\nada,lovelace\n\n")
    people, warnings = files.read_participants(p)
    assert [x.full_name for x in people] == ["Ada Lovelace", "ada lovelace"]
    assert len(warnings) == 1 and "line 3" in warnings[0]


def test_excel_bom_and_header_case(tmp_path):
    p = write(tmp_path / "p.csv", "﻿Name,LastName\nAda,L\n")
    assert files.read_participants(p)[0][0].name == "Ada"


@pytest.mark.parametrize(
    "text,fragment",
    [
        ("", "missing header"),
        ("name,lastname\n", "no participants"),
        ("name,surname\nA,B\n", "expected columns"),
        ("name,lastname\nAda,\n", "line 2"),
    ],
)
def test_participants_problems(tmp_path, text, fragment):
    with pytest.raises(DataFileError, match=fragment):
        files.read_participants(write(tmp_path / "p.csv", text))


def test_missing_file_points_to_setup(tmp_path):
    with pytest.raises(DataFileError, match="raffle-cli setup"):
        files.read_prizes(tmp_path / "nope.csv")


def test_prizes_validation_reports_every_problem(tmp_path):
    p = write(tmp_path / "pr.csv", "item,qty\nLaptop,1\nMug,two\nPen,0\n,3\n")
    with pytest.raises(DataFileError) as exc:
        files.read_prizes(p)
    assert len(exc.value.problems) == 3
    ok = write(tmp_path / "ok.csv", "item,qty\nLaptop,2\n")
    assert files.read_prizes(ok)[0].qty == 2


def test_winners_roundtrip_and_backup(tmp_path):
    path = tmp_path / "w.csv"
    assert files.read_winners(path) == []
    files.append_winner(path, Winner("Ada", "L", "Laptop"))
    files.append_winner(path, Winner("Bob", "M", "Mug, large"))
    assert files.read_winners(path)[1].item == "Mug, large"
    files.reset_winners(path)
    assert files.read_winners(path) == []
    assert "Ada" in (tmp_path / "w.csv.bak").read_text()


def test_setup_creates_valid_files_and_keeps_existing(tmp_path):
    cfg = tmp_path / "my.yaml"
    assert {s for _, s in setup_files(cfg)} == {"created"}
    loaded = load_config(cfg)
    assert files.read_participants(loaded.participants_file)[0]
    assert files.read_prizes(loaded.prizes_file)
    (tmp_path / "participants.csv").write_text("name,lastname\nZed,Z\n")
    again = dict((p.name, s) for p, s in setup_files(cfg))
    assert set(again.values()) == {"kept"}
    assert (tmp_path / "participants.csv").read_text().startswith("name,lastname\nZed")
    assert dict((p.name, s) for p, s in setup_files(cfg, force=True))["participants.csv"] == "overwritten"


def test_setup_empty(tmp_path):
    setup_files(tmp_path / "c.yaml", samples=False)
    with pytest.raises(DataFileError, match="no participants"):
        files.read_participants(tmp_path / "participants.csv")


@pytest.mark.parametrize(
    "name,text,fragment",
    [
        ("c.txt", "", "not a .yaml"),
        ("c.yaml", "garbage: [", "not valid YAML"),
        ("c.yaml", "- a\n- b\n", "key: value"),
        ("c.yaml", "recreate_from_winners: maybe-not\n", "invalid structure"),
    ],
)
def test_bad_configs(tmp_path, name, text, fragment):
    with pytest.raises(ConfigError, match=fragment):
        load_config(write(tmp_path / name, text))


def test_config_paths_resolve_next_to_config(tmp_path):
    sub = tmp_path / "event"
    sub.mkdir()
    write(sub / "c.yaml", "participants_file: p.csv\n")
    assert load_config(sub / "c.yaml").participants_file == sub / "p.csv"
