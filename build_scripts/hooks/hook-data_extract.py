"""
Custom PyInstaller hook for data_extract package.

Collects CLI preset YAML files and other package data.
"""

from PyInstaller.utils.hooks import collect_data_files

# Collect all data files from data_extract package, including CLI presets
datas = collect_data_files("data_extract", subdir="cli/presets")
