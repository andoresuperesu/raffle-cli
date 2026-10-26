"""config.yaml loading and scaffolding (`raffle-cli setup`)."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ValidationError

from . import files

DEFAULT_CONFIG = Path("config.yaml")


class ConfigError(Exception):
    pass


class RaffleConfig(BaseModel):
    participants_file: Path = Path("participants.csv")
    prizes_file: Path = Path("prizes.csv")
    winners_file: Path = Path("winners.csv")
    # True: resume from whatever is already in winners_file. False: start fresh each run.
    recreate_from_winners: bool = True

    def resolved(self, base: Path) -> "RaffleConfig":
        """Make relative file paths relative to the config file's folder."""
        return RaffleConfig(
            participants_file=base / self.participants_file,
            prizes_file=base / self.prizes_file,
            winners_file=base / self.winners_file,
            recreate_from_winners=self.recreate_from_winners,
        )


def load_config(path: Path) -> RaffleConfig:
    if path.suffix.lower() not in {".yaml", ".yml"}:
        raise ConfigError(f"{path.name} is not a .yaml file.")
    if not path.exists():
        raise ConfigError(f"{path} does not exist. Run `raffle-cli setup` to create it.")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise ConfigError(f"{path.name} must contain key: value pairs.")
        return RaffleConfig.model_validate(data).resolved(path.resolve().parent)
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path.name} is not valid YAML: {exc}") from exc
    except ValidationError as exc:
        details = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors())
        raise ConfigError(f"{path.name} has an invalid structure ({details}).") from exc


def setup_files(config_path: Path, *, force: bool = False, samples: bool = True) -> list[tuple[Path, str]]:
    """Create config + CSVs next to `config_path`. Returns (path, 'created'|'kept'|'overwritten')."""
    if config_path.suffix.lower() not in {".yaml", ".yml"}:
        raise ConfigError(f"{config_path.name} is not a .yaml file.")
    cfg = RaffleConfig()
    results: list[tuple[Path, str]] = []

    def put(path: Path, writer) -> None:
        existed = path.exists()
        if existed and not force:
            results.append((path, "kept"))
            return
        writer(path)
        results.append((path, "overwritten" if existed else "created"))

    def write_config(path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(cfg.model_dump(mode="json"), sort_keys=False), encoding="utf-8")

    base = config_path.resolve().parent
    put(config_path, write_config)
    put(base / cfg.participants_file, lambda p: files.write_participants(p, files.SAMPLE_PARTICIPANTS if samples else []))
    put(base / cfg.prizes_file, lambda p: files.write_prizes(p, files.SAMPLE_PRIZES if samples else []))
    put(base / cfg.winners_file, lambda p: files.reset_winners(p))
    return results
