#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Bringup orchestrator for the Mivia Rover ecosystem.

This launch file conditionally includes the launch file of each module.
For every module you can:
  - enable/disable it
  - select which launch file to include
  - select which LaunchDescriptionSource to use (python/xml/yaml/frontend)

Typical usage:

ros2 launch mivia_rover_bringup bringup_all.launch.py \
  enable_mivia_rover_platform:=true \
  mivia_rover_platform_launch_file:=launch.py \
  mivia_rover_platform_launch_source:=python \
  enable_navigation_map:=true \
  navigation_map_launch_file:=map_server.launch.py \
  navigation_map_launch_source:=python
"""

from dataclasses import dataclass
from typing import List, Optional

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo, OpaqueFunction
from launch.conditions import IfCondition
from launch.launch_description_sources import (
    PythonLaunchDescriptionSource,
    FrontendLaunchDescriptionSource,
)
from launch_yaml.launch_description_sources import YAMLLaunchDescriptionSource
from launch_xml.launch_description_sources import XMLLaunchDescriptionSource

from launch.substitutions import LaunchConfiguration, TextSubstitution


@dataclass(frozen=True)
class ModuleSpec:
    """Descriptor for a module that can be conditionally launched."""
    package: str
    default_launch_file: str = "launch.py"
    default_source: str = "python"  # python|xml|yaml|frontend
    # Optional: pass-through arguments can be added later per-module if you need them
    # default_launch_arguments: Optional[dict] = None


MODULES: List[ModuleSpec] = [
    
    ModuleSpec(package="mivia_rover_visualization", default_launch_file="mivia_rover_visualization.launch.py"),
    ModuleSpec(package="mivia_rover_platform", default_launch_file="mivia_rover.launch.py"),
    ModuleSpec(package="mivia_rover_mapping"),
    ModuleSpec(package="mivia_rover_localization_bringup", default_launch_file="mivia_rover_localization.launch.py"),
    ModuleSpec(package="mivia_rover_sensing_bringup", default_launch_file="mivia_rover_sensing_bringup.launch.py"),
    ModuleSpec(package="mivia_rover_nav2_bringup", default_launch_file="mivia_rover_nav2_bringup.launch.py"),
    ModuleSpec(package="mivia_rover_perception", default_launch_file="perception_visualizer_node.launch.py"),
]


def _make_source(source_kind: str, launch_path: str):
    """Factory for LaunchDescriptionSource."""
    if source_kind == "python":
        return PythonLaunchDescriptionSource(launch_path)
    if source_kind == "xml":
        return XMLLaunchDescriptionSource(launch_path)
    if source_kind == "yaml":
        return YAMLLaunchDescriptionSource(launch_path)
    if source_kind == "frontend":
        return FrontendLaunchDescriptionSource(launch_path)

    # Defensive default: fall back to Python, but emit a warning.
    return PythonLaunchDescriptionSource(launch_path)


def _include_module(context, module: ModuleSpec):
    """
    OpaqueFunction callback to build IncludeLaunchDescription with computed paths.
    We keep path computations in runtime to avoid issues with substitution evaluation.
    """
    enable_key = f"enable_{module.package}"
    file_key = f"{module.package}_launch_file"
    source_key = f"{module.package}_launch_source"

    enabled = LaunchConfiguration(enable_key).perform(context).strip().lower()
    launch_file = LaunchConfiguration(file_key).perform(context).strip()
    source_kind = LaunchConfiguration(source_key).perform(context).strip().lower()

    # If disabled, we still return an empty list; the IfCondition would also work,
    # but this makes it easy to add runtime checks/logging.
    if enabled not in ("true", "1", "yes", "on"):
        return [LogInfo(msg=f"[bringup_all] {module.package}: disabled")]

    pkg_share = get_package_share_directory(module.package)
    launch_dir = os.path.join(pkg_share, "launch")
    launch_path = os.path.join(launch_dir, launch_file)

    if not os.path.isfile(launch_path):
        return [
            LogInfo(
                msg=(
                    f"[bringup_all] ERROR: {module.package}: launch file not found: "
                    f"{launch_path}"
                )
            )
        ]

    src = _make_source(source_kind, launch_path)

    return [
        LogInfo(
            msg=(
                f"[bringup_all] {module.package}: including {launch_file} "
                f"(source={source_kind})"
            )
        ),
        IncludeLaunchDescription(
            src,
            # launch_arguments={...}.items()  # add per-module args here when needed
        ),
    ]


def generate_launch_description():
    declare_args = []
    include_actions = []

    for m in MODULES:
        enable_name = f"enable_{m.package}"
        file_name = f"{m.package}_launch_file"
        source_name = f"{m.package}_launch_source"

        declare_args.append(
            DeclareLaunchArgument(
                enable_name,
                default_value=TextSubstitution(text="true"),
                description=f"Set to true to launch {m.package}, false otherwise.",
            )
        )

        declare_args.append(
            DeclareLaunchArgument(
                file_name,
                default_value=TextSubstitution(text=m.default_launch_file),
                description=f"Launch file name inside {m.package}/launch/.",
            )
        )

        declare_args.append(
            DeclareLaunchArgument(
                source_name,
                default_value=TextSubstitution(text=m.default_source),
                description=(
                    f"Launch source type for {m.package}: "
                    "python|xml|yaml|frontend."
                ),
            )
        )

        # Use OpaqueFunction to compute and validate file existence at runtime
        include_actions.append(
            OpaqueFunction(function=lambda ctx, mod=m: _include_module(ctx, mod))
        )

    return LaunchDescription(
        declare_args + include_actions
    )