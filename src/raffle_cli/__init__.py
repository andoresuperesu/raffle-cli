import rich.align
import rich.columns
import rich.panel
import rich.table
import typer
import csv
import os
import yaml
import random
import time
import rich
from pathlib import Path
from typing import Type, Optional
from typing_extensions import Annotated
from pydantic import BaseModel, ValidationError

print=rich.print
Table=rich.table.Table
Console=rich.console.Console
Panel=rich.panel.Panel
Align=rich.align.Align

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
CONSOLE=Console()

app = typer.Typer()

class raffle_config(BaseModel):
    participants_file: str
    prizes_file: str
    winners_file: str
    recreate_from_winners: bool

@app.callback(invoke_without_command=True)
def main(config: Annotated[Optional[Path], typer.Option()] = None):
    cli_ui_title("WELLCOME TO RAFFLE-CLI")
    config_check, config=check_config(config)
    if config_check:
        file_check, par_file, pri_file, win_file=check_files_in_config(config)
    else:
        print(f"Something went wrong reading the config file")
    if file_check:
        participants=read_csv_typed(par_file,PAR_TYPES)
        prizes=read_csv_typed(pri_file, PRI_TYPES)
        winners=read_csv_typed(win_file,WIN_TYPES)
    else:
        print(f"Something went wrong with reading the default files from the {config.name}")
    
    prizes=order_prizes(prizes,"high-low")
    print_delayed(f"Game starting in...")
    print_delayed("3 2 1 Go",1)
    time.sleep(0.5)
    CONSOLE.clear()
    winners=distribute_prizes(prizes,participants,winners)
    cli_ui_title(dictlist_to_table(winners),"raffle-cli Results","Congratulations to all winners!")

    print("This is the end so far...")
    print()
    

    

@app.command("setup")
def setup()->None:
    print("You ran setup command.")

# ----------------------------------------------------------------------
#                           APP MAIN FUNCTIONS
# ----------------------------------------------------------------------
def order_prizes(prize_data:list[dict], order_type:str):
    """
    Orders a list of prize dictionaries based on order_type.

    Parameters:
    - prizes_data (list): List of dictionaries. Each dictionary should contain at least the key 'qty'.
    - order_type (str): Ordering mode. Can be 'shuffle' for random ordering,
                        'low-high' for ascending order by 'qty', or 'high-low' for descending order by 'qty'.

    Returns:
    - list: The ordered list of dictionaries.
    
    Raises:
    - ValueError: If order_type is not one of the allowed options.
    """
    if order_type == "shuffle":
        random.shuffle(prize_data)
    elif order_type == "low-high":
        prize_data.sort(key=lambda x: x["qty"])
    elif order_type == "high-low":
        prize_data.sort(key=lambda x: x["qty"], reverse=True)
    else:
        raise ValueError("Invalid order_type. Choose from 'shuffle', 'low-high', or 'high-low'.")
    
    return prize_data

def distribute_prizes(prizes_data, participant_data,winner_data):
    """
    Distributes prizes among participants.
    
    For each prize (represented as a dict with keys 'item' and 'qty'),
    while its qty > 0, a participant is selected at random from participant_data.
    
    - If the participant hasn't won before, they are added to winner_data with the prize.
    - If the participant already has a prize, then they "swap": their winner entry is updated 
      to the new prize's item, and the prize they previously held gets its qty increased by 1.
      (A new participant will then be selected to eventually claim that returned prize unit.)
    
    The process repeats until every prize in prizes_data has qty equal to 0.
    
    Parameters:
      prizes_data (list of dict): Each dict has structure {"item": str, "qty": int}.
      participant_data (list of dict): Each dict has structure {"name": str, "lastname": str}.
      
    Returns:
      list of dict: The final winners list with each dict in the form
                    {"name": str, "lastname": str, "item": str}.
    """
    winner_data = []
    
    # Helper: locate a participant in winner_data by name and lastname.
    def find_winner_index(name, lastname):
        for i, winner in enumerate(winner_data):
            if winner["name"] == name and winner["lastname"] == lastname:
                return i
        return None
    
    # Continue until all prize quantities are zero.
    while any(prize["qty"] > 0 for prize in prizes_data):
        # Process each prize unit.
        for prize in prizes_data:
            # Award as long as units remain for this prize.
            while prize["qty"] > 0:
                cli_ui_title("ONGOING RAFFLE")
                cli_ui_status(dictlist_to_table(prizes_data),dictlist_to_table(winner_data,"No winner data yet"))
                #print_table(prizes_data)
                #print_table(winner_data,"No winner data yet")
                
                thingy=prize["item"]
                print_delayed(f"Next item to win is... {thingy}")
                participant = random.choice(participant_data)
                print_delayed(f"\tThe winner of {thingy} is.... ")
                input("\tPress enter when ready.")
                pname=participant["name"]
                plastname=participant["lastname"]
                print(f"\t\t{pname} {plastname}")
                
                idx = find_winner_index(participant["name"], participant["lastname"])
                
                if idx is None:
                    # Participant hasn't won yet. Award the prize.
                    winner_data.append({"name": participant["name"],"lastname": participant["lastname"],"item": prize["item"]})
                    prize["qty"] -= 1
                else:
                    print(f"\t{participant} won already!!")
                    # Participant already has a prize.
                    current_item = winner_data[idx]["item"]
                    # If the new prize is the same as the current one, skip to avoid unnecessary swap.
                    if current_item == prize["item"]:
                        # Optionally, you could try selecting another participant.
                        print_delayed("\t\tAlready got that, let's pick somebody else")
                    else:
                        new_item=prize["item"]
                        swap_bool=typer.confirm(f"\t\tWant to swap '{current_item}' for '{new_item}'")
                        
                        if swap_bool:
                            # Swap: update the participant's prize to the new prize.
                            winner_data[idx]["item"] = prize["item"]
                            # Return the previously won prize: increase its quantity by 1.
                            prize["qty"] -= 1
                            for p in prizes_data:
                                if p["item"] == current_item:
                                    p["qty"] += 1
                                    print_delayed(f"\t\tItems switched!")
                                    break
                        else:
                            print("Back to the game!")
                input("Press enter to continue...")


                # Optional: if all prizes have been fully awarded, break out.
                if not any(p["qty"] > 0 for p in prizes_data):
                    break
                    
    return winner_data

def cli_ui_title(panelInput="[purple]RAFFLE-CLI[/]",panelTitle:str="raffle-cli",panelSubtitle:str="Let's Raffle!"):
    CONSOLE.clear()
    print(Panel(Align.center(panelInput), title=panelTitle, subtitle=panelSubtitle,title_align="left",subtitle_align="right"))

def cli_ui_status(prizesTable:rich.table.Table|str,winnerTable:rich.table.Table|str):
    panelColumns=rich.columns.Columns([prizesTable,winnerTable])
    print(Panel(panelColumns))


# ----------------------------------------------------------------------
#                           FILE VALIDATION
# ----------------------------------------------------------------------

# CONFIG FILE VALIDATION
def check_config(config_file:Path=None)->tuple[bool, Path]:
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
        return True, config_file
    else:
        print(f":task: Please fix [bold]{config_file.name}[/].")
        reset_file=typer.confirm(f"Want to set the default content?",abort=False)
        if reset_file:
            create_default_config(config_file,True)
            return True, config_file
        else:
            return False, None

# CONFIG FILE CREATION
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

# CONFIG YAML Model VALIDATION
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

# WORK FILES VALIDATION
def check_files_in_config(config_file:Path)->tuple[bool,Path,Path,Path]:
    try:
        with open(config_file, 'r') as file:
            yaml_data = yaml.safe_load(file)
    except Exception as e:
        print(f"    Error reading YAML file: {e}")
        return False, None, None, None
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

#POPULATE WORK FILE
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

#CREATE ANY FILE
def create_file_ifdoesntexist(file_to_create:Path,printoffset:int=4):
    global RECENTLY_CREATED
    if file_to_create.exists():
        print(f"{printoffset*' '}:white_check_mark: Found [bold]{file_to_create.name}[/]")
    else:
        file_to_create.touch()
        RECENTLY_CREATED=True
        print(f"{printoffset*' '}:white_check_mark: Created [bold]{file_to_create.name}[/]")

#POPULATE CSV FILE
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

#VERIFY CSV FILE
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

# HELPER FUNCTIONS

def print_delayed(text, delay=0.3):
    """
    Prints the given text one word at a time with a delay between words.
    
    Parameters:
      text (str): The full text to print.
      delay (float): Time in seconds to wait between printing each word.
    """
    words = text.split(" ")
    for word in words:
        print(word, end=' ')
        time.sleep(delay)
    print()  # Ensure newline at the end

def read_csv_data(filepath:Path) -> list[dict]:
    with open(filepath, 'r') as file:
        reader = csv.DictReader(file)
        data_list = [row for row in reader]
        return data_list

def read_csv_typed(filepath, field_types):
    """
    Reads a CSV file into a list of dictionaries and casts each field to its corresponding data type.

    Parameters:
      filepath (str): Path to the CSV file.
      field_types (dict): Dictionary where keys are CSV field names and values are the functions
                          used to cast the field values (e.g., int, float, str).

    Returns:
      list: A list of dictionaries with properly typed values.

    Raises:
      KeyError: If a field specified in field_types is missing in the CSV.
      ValueError: If a field value cannot be cast to the specified type.
    """
    result = []
    with open(filepath, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            new_row = {}
            for field, cast_func in field_types.items():
                if field not in row:
                    raise KeyError(f"Field '{field}' not found in the CSV file.")
                try:
                    new_row[field] = cast_func(row[field])
                except Exception as e:
                    raise ValueError(f"Error casting field '{field}' with value '{row[field]}': {e}")
            result.append(new_row)
    return result

def dictlist_to_table(data:list[dict],no_data_str:str="No data to display"):
    """
    Prints a list of dictionaries as a Rich table.
    
    Assumes all dictionaries have the same structure.
    
    Parameters:
        data (list of dict): The list of dictionaries to print.
    """
    if not data:
        return no_data_str

    # Create a table and use keys from the first dict as column headers
    dictlistTable = Table(show_header=True, header_style="bold magenta")
    for key in data[0].keys():
        dictlistTable.add_column(str(key))

    # Add rows to the table
    for row in data:
        # Ensure that each value is converted to a string
        dictlistTable.add_row(*(str(row[key]) for key in data[0].keys()))

    return dictlistTable

def main_cli():
    app()

if __name__=='__main__':
    app()