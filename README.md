# raffle-cli

raffle-cli is a rethink of a raffle executing cli for meetup giveaways (no money invoved, mainly thought as a transparent way to give away swag).

## Install

I'm fairly new to this, but you should be able to install it going `uv pip install <repo-url>`.

## How it works
`raffle-cli`is a Typer app (Thank you @tiangolo) and also makes heavy use of `rich` (thank you @willmcgugan).

It requires 4 files config.yaml, participants.csv, prizes.csv and winner.csv. The app validates they exist and there will also be a setup command see it's subtitle to understand how to use it. However, the main cli app will check if any or all files exist and setup default values if not.

The `config.yaml`file should contain the following parameters:
```yaml
participants_file: path_to_participants.csv
prizes_file: path_to_prizes.csv
recreate_from_winners: true
winners_file: path_to_winners.csv
```

The `prizes.csv` file should contain the following columns:
```csv
item,qty
Prize1,1
Prize2,1
Prize3,3
```
The `participants.csv` file should contain the following columns:
```csv
name,lastname
John,Doe
```
The `winners.csv` file should contain the columns:
```csv
name,lastname,item

```

### `raffle-cli`

Running the cli without arguments will default to a config file named `'config.yaml'`. Will

```bash
raffle-cli
```

You can also pass a `--config`parameter ponting to a different config.yaml file.
```bash
raffle-cli --config config.yaml
```

### `raffle-cli setup`

This command doesn't exist yet but it's purpose is to create a `config.yaml`and it's corresponding csv files. The `config.yaml` can actually be `<any_valid_name>.yaml` as long as it has the correct structure. The setup program will create the correct structure.

```bash
raffle-cli setup
```

## Contribute

Feel free to do a PR, however it's extremely early and things are a little convoluted, but I'll be ecstatic to have anyone contribute. Nomatter whether the PR is accepted or not, thank you!

