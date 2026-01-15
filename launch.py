from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from pathlib import Path
from launch.actions import LogInfo

def read_config(file_path: str) -> dict:
    import yaml
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

def import_launch_from_folder(folder_name: str):
    try:
        launch_file_path = Path.cwd().parent / folder_name / 'launch.py'
        if launch_file_path.exists():
            launch_description = IncludeLaunchDescription(
                PythonLaunchDescriptionSource(str(launch_file_path))
            )
            return launch_description
    except Exception as e:
        print(f"Error importing launch from {folder_name}, make shure that the folder contains a launch.py file")
    


def generate_launch_description():
    
    current_dir = Path.cwd()
    config = read_config(str(current_dir / 'config' / 'general_launch_config.yaml'))
    verbose = config.get('verbose', False)
    

    # Directory padre
    parent_dir = current_dir.parent

    # Tutte le cartelle allo stesso livello di A
    sibling_dirs = [
        p.name for p in parent_dir.iterdir()
        if p.is_dir()
    ]

    black_list = config.get('exclude', [])

    launch_list = []
    for folder in sibling_dirs:
        if folder not in black_list and folder != current_dir.name:
            launch_list.append(import_launch_from_folder(folder))
    
    if verbose:
        launch_list.append(LogInfo(msg=f"Included launch files from folders: {[f for f in sibling_dirs if f not in black_list and f != current_dir.name]}"))

    return LaunchDescription(launch_list)

