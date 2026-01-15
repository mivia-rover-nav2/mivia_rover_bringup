## Launch Package

This package provides a generic launch entrypoint (`launch.py`) responsible for orchestrating the startup of multiple ROS 2 launch files.

At runtime, the launch script reads configuration from `config/general_launch_config` configuration file to determine whether any packages or directories are explicitly excluded from the launch process. It then automatically discovers and launches all eligible launch files located in the same directory of the containing package

Each non-excluded package is expected to provide a `launch.py` file, which will be included and executed as part of the overall launch procedure.
