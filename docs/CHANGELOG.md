# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-28

### Added
- Interactive ncdu-style TUI for browsing and selecting files
- Hardlink-aware directory size calculation
- Global hardlink purge mode (delete all hardlinks of selected files)
- Variant A cleanup (delete files where all hardlinks are in directory)
- Symlink removal mode
- Directory size scanning with configurable depth
- Save/load scan results to JSON
- Dry-run mode for safe preview
- Confirmation prompts before deletion
- Filesystem boundary respect (--xdev option)
- Verbose logging and log file support
- Command-line interface with argparse
- Console script entry point for easy installation

### Features
- Navigate with arrow keys, vim keys (j/k), PgUp/PgDn
- Mark/unmark files and directories with Space
- Aggregate size calculation for directories
- Real-time size display in human-readable format
- Cross-filesystem detection and handling
- Inode-based hardlink tracking
- Accurate disk usage calculation (st_blocks)

[1.0.0]: https://github.com/yourusername/hardlink-cleaner/releases/tag/v1.0.0
