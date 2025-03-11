import typer
import csv
import os
import yaml
from rich import print, prompt
from pathlib import Path
from typing import Type, Optional
from typing_extensions import Annotated
from pydantic import BaseModel, ValidationError

CWD:Path=os.getcwd()
DEF_CONFIG_FILE:Path=Path(os.path.join(CWD,"config.yaml"))
DEF_PAR_FILE:Path=Path(os.path.join(CWD,"participants.csv"))
DEF_PRI_FILE:Path=Path(os.path.join(CWD,"prizes.csv"))
DEF_WIN_FILE:Path=Path(os.path.join(CWD,"winners.csv"))
PAR_COLUMNS:list=['name','lastname']
PRI_COLUMNS:list=['item','qty']
WIN_COLUMNS:list=['name','lastname','item']
PAR_SAMPLE:list[dict]=[{'name':'John','lastname':'Doe'},{'name':'Juan','lastname':'Perez'}]
PRI_SAMPLE:list[dict]=[{'item':'Laptop','qty':1},{'item':'Keyboard','qty':1}]
WIN_SAMPLE=None
PAR_TYPES:dict={'name':str,'lastname':str}
PRI_TYPES:dict={'item':str,'qty':int}
WIN_TYPES:dict={'name':str,'lastname':str,'item':str}
RECENTLY_CREATED=False

app = typer.Typer()

class raffle_config(BaseModel):
    participants_file: str
    prizes_file: str
    winners_file: str
    recreate_from_winners: bool

@app.callback(invoke_without_command=True)
def main(config: Annotated[Optional[Path], typer.Option()] = None):
    check_config(config)
    file_checked, par_file, pri_file, win_file=check_files_in_config(config)
    if file_checked:
        participants=read_csv_data(par_file)
        prizes=read_csv_data(pri_file)

    

@app.command("setup")
def setup()->None:
    print("You ran setup command.")


# ----------------------------------------------------------------------
#                           FILE VALIDATION
# ----------------------------------------------------------------------
def check_config(config_file:Path=None)->bool:
    if config_file==None:
        print("No config file was passed, trying default.")
        config_file=DEF_CONFIG_FILE
    if not config_file.name.endswith('.yaml'):
        print(f"Got {config_file.name} as config, [italic]but it wasn't a yaml file.[/]")
        create = typer.confirm("Would you want to create a new one ?")
        create_default_config() if create else print("Alrighty then, work it out and call me back. :vulcan_salute:")
        exit()
    if not config_file==None and not config_file.exists():
        print(f"[bold]Ups[/], it seems {config_file.name} isnt't in the working directory. [italic]Let's create it...[/]")
        create_default_config(config_file)
    if not config_file.exists():
        print("[bold]Ups[/], it seems like no config was provided and there's none to be found. [italic]Let's create one...[/]")
        create_default_config(config_file)
    elif config_file.exists():
        print(f"Hey, we found [bold]{config_file.name}[/bold] file, let's check if it has the correct structure")
    
    checked_structure=check_config_structure(config_file,raffle_config)
    if checked_structure:
        print("    Nice, a correct config file, [bold green]well done![/]")
        return True
    else:
        print(f":task: Please fix [bold]{config_file.name}[/].")
        reset_file=typer.confirm(f"Want to set the default content?",abort=True)
        if reset_file:
            create_default_config(config_file,True)
            return True

def create_default_config(config_file:Path=DEF_CONFIG_FILE, reset:bool=False):
    # Create default config file
    if not reset:
        config_file.touch()
        print(":white_check_mark: Done, file created.")
    raffle_config_instance = raffle_config(participants_file='participants.csv',prizes_file='prizes.csv',winners_file='winners.csv',recreate_from_winners=True)
    raffle_config_dict = raffle_config_instance.model_dump()
    with open(config_file, 'w') as outfile:
        yaml.dump(raffle_config_dict, outfile, default_flow_style=False)
    if reset:
        print(":white_check_mark: Done, content reset.")

def check_config_structure(file_path: Path, model: Type[BaseModel]) -> bool:
    """
    Verifies that a YAML file is well-formed and that its content adheres to
    the structure defined by a Pydantic BaseModel.
    Args:
        file_path (str): Path to the YAML file.
        model (Type[BaseModel]): A Pydantic BaseModel class that defines the expected structure.
    Returns:
        bool: True if the YAML file is valid and conforms to the model's structure; False otherwise.
    """
    try:
        with open(file_path, "r") as file:
            data = yaml.safe_load(file)
        # Validate the data against the provided Pydantic model
        model.model_validate(data)
        return True
    except yaml.YAMLError as e:
        print("    Error parsing YAML:", e)
        return False
    except ValidationError as e:
        print("    Config structure does not match the expected model:", e)
        return False
    except Exception as e:
        print("    Unexpected error:", e)
        return False

def check_files_in_config(config_file:Path)->tuple[bool,Path,Path,Path]:
    try:
        with open(config_file, 'r') as file:
            yaml_data = yaml.safe_load(file)
    except Exception as e:
        print(f"    Error reading YAML file: {e}")
        exit()
    par_file=Path(yaml_data['participants_file'])
    pri_file=Path(yaml_data['prizes_file'])
    win_file=Path(yaml_data['winners_file'])
    par_check=verify_csv(par_file,PAR_TYPES)
    if not par_check:
        reset_work_file('PAR',par_file)
    pri_check=verify_csv(pri_file,PRI_TYPES)
    if not pri_check:
        reset_work_file('PRI',pri_file)
    win_check=verify_csv(win_file,WIN_TYPES)
    if not win_check:
        reset_work_file('WIN',win_file)
    return True, par_file,pri_file,win_file

def reset_work_file(filetype:str,file:Path=DEF_PAR_FILE,check_failed:bool=False):
    filetypes=['PAR','PRI','WIN']
    if filetype not in filetypes:
        raise ValueError(f"    Invalid filetype. Expected one of {filetypes}.")
    # Check/Create default file based on type
    overwrite=typer.confirm(f"      Want to set the default content of the {file.name} file?")
    if overwrite:
        populate_csv(file,eval(f"{filetype}_COLUMNS"),eval(f"{filetype}_SAMPLE"))
    else:
        print("      Ok, fix it on your own, see you back later!")

def create_file_ifdoesntexist(file_to_create:Path,printoffset:int=4):
    global RECENTLY_CREATED
    if file_to_create.exists():
        print(f"{printoffset*' '}:white_check_mark: Found [bold]{file_to_create.name}[/]")
    else:
        file_to_create.touch()
        RECENTLY_CREATED=True
        print(f"{printoffset*' '}:white_check_mark: Created [bold]{file_to_create.name}[/]")


def populate_csv(filename:Path, columns:list, rows:list[dict]=None):
    """
    Creates a CSV file with the specified columns as the header.
    Parameters:
      filename (str): The path to the CSV file to create.
      columns (list): A list of column names to use as the header.
      rows (list of dict, optional): A list of dictionaries representing rows of data.
                                     Each dictionary should use the column names as keys.
                                     If not provided, only the header is written.
    """
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writeheader()
        if rows:
            for row in rows:
                writer.writerow(row)

def verify_csv(filename: Path, expected_types: dict) -> bool:
    """
    Verifies that a CSV file has the expected columns and that each row's data 
    can be cast to the specified datatypes.
    
    Parameters:
      filename (Path): Path to the CSV file.
      expected_types (dict): A dictionary mapping column names to expected type 
                             constructors (e.g., int, float, str).
                             For example: {'Age': int, 'Name': str, 'Email': str}
    
    Returns:
      bool: True if the CSV file has the correct columns and all data rows match 
            the expected datatypes; False otherwise.
    """
    try:
        create_file_ifdoesntexist(filename)
        with open(filename, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            
            # Check if header exists
            file_columns = reader.fieldnames
            if file_columns is None:
                print("      Error: CSV file does not have a header.")
                return False

            # Use the keys of expected_types as the expected columns
            expected_columns = list(expected_types.keys())
            if set(file_columns) != set(expected_columns):
                print(f"      Error: Column mismatch.\nExpected columns: {expected_columns}\nFound columns: {file_columns}")
                return False

            # Iterate over each row and check datatypes
            row_number = 2  # starting from 2 because header is row 1
            for row in reader:
                for col, expected_type in expected_types.items():
                    value = row.get(col)
                    # Check for missing or empty values
                    if value is None or value == '':
                        print(f"      Error: Missing value for column '{col}' in row {row_number}.")
                        return False
                    try:
                        # Attempt to cast the value to the expected type
                        expected_type(value)
                    except Exception as e:
                        print(f"      Error: Data type mismatch in row {row_number} for column '{col}'. "
                              f"      Expected {expected_type.__name__}, got value '{value}'. Exception: {e}")
                        return False
                row_number += 1
        return True
    except FileNotFoundError:
        print(f"      Error: File '{filename}' not found.")
        return False
    except Exception as e:
        print(f"      An unexpected error occurred: {e}")
        return False


def read_csv_data(filepath:Path) -> list[dict]:
    with open(f'{filepath}.csv', 'r') as file:
        reader = csv.DictReader(file)
        data_list = [row for row in reader]
        return data_list

def main_cli():
    app()