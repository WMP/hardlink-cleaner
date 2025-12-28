# 🧹 Hardlink Cleaner

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

Interactive TUI tool for finding and cleaning hardlinked files to reclaim disk space.

Perfect for cleaning up torrent directories, deduplication systems, or any filesystem with extensive hardlinks.

**[Quick Start](docs/QUICKSTART.md)** | **[Examples](docs/EXAMPLES.md)** | **[FAQ](docs/FAQ.md)** | **[Installation Guide](docs/INSTALL.md)**

## ✨ Features

- **Interactive ncdu-style TUI** - Browse directories, see aggregated sizes, select files/folders for deletion
- **Hardlink-aware** - Doesn't double-count hardlinked files when calculating sizes
- **Global hardlink cleanup** - Delete all hardlinks of selected files across the entire filesystem
- **Safe by default** - Dry-run mode, confirmation prompts, respects filesystem boundaries
- **Save/load scans** - Analyze scan results offline without re-scanning

## 🚀 Installation

### Using pipx (recommended)
```bash
pipx install hardlink-cleaner
```

### Using pip
```bash
pip install hardlink-cleaner
```

### From source
```bash
git clone https://github.com/wmp/hardlink-cleaner.git
cd hardlink-cleaner
pip install .
```

## 📖 Usage

### Interactive mode (default)
```bash
# Launch interactive browser for directory
hardlink-cleaner /path/to/directory

# Navigate with arrow keys, Space to select, 'd' to delete, 'q' to quit
```

### Non-interactive purge
```bash
# Dry run (shows what would be deleted)
hardlink-cleaner /path/to/directory --dry-run

# Actually delete (with confirmation)
hardlink-cleaner /path/to/directory

# Skip confirmation
hardlink-cleaner /path/to/directory --yes
```

### Save scan for later analysis
```bash
# Save scan results
hardlink-cleaner /path/to/directory --save-scan results.json --dry-run

# Load and analyze saved scan
hardlink-cleaner /path/to/directory --load-scan results.json
```

## 🎮 Interactive Mode Controls

| Key | Action |
|-----|--------|
| `↑`/`↓` or `j`/`k` | Navigate up/down |
| `Enter` or `→` | Enter directory |
| `Backspace` or `←` | Go to parent directory |
| `Space` | Mark/unmark file or directory |
| `d` | Delete selected items |
| `q` | Quit without changes |
| `PgUp`/`PgDn` | Page up/down |
| `Home`/`End` or `g`/`G` | Jump to first/last item |

## ⚙️ Options

```
  --xdev                Stay on same filesystem (don't cross mount points)
  -i, --interactive     Enable interactive mode (default)
  --no-interactive      Disable interactive mode
  -y, --yes             Skip confirmation prompts
  --dry-run             Show what would be deleted without actually deleting
  --save-scan FILE      Save scan results to JSON file
  --load-scan FILE      Load scan results from JSON file
  -v, --verbose         Enable debug logging
  --log FILE            Write logs to file
```

## 💡 Use Cases

### Clean up torrent directory
Remove hardlinked torrent files and their duplicates across your filesystem:
```bash
hardlink-cleaner ~/torrents
```

### Clean up deduplicated storage
```bash
hardlink-cleaner /mnt/storage --xdev --save-scan analysis.json
```

## ⚠️ Safety Features

- **Dry-run mode**: Preview changes before committing
- **Confirmation prompts**: Double-check before deletion
- **Filesystem boundaries**: `--xdev` prevents crossing mount points
- **Hardlink-aware sizing**: Accurate space calculation
- **Logging**: Track all operations with `--verbose` and `--log`

## 🔧 How It Works

1. **Scanning**: Walks directory tree, building inode map (hardlink-aware)
2. **Size calculation**: Aggregates sizes without double-counting hardlinks
3. **Interactive selection**: ncdu-style browser for selecting files/directories
4. **Global search**: Finds all hardlinks across filesystem for selected files
5. **Safe deletion**: Removes all hardlinks of selected files

## 📚 Documentation

- **[Quick Start Guide](docs/QUICKSTART.md)** - Get started in 30 seconds
- **[Usage Examples](docs/EXAMPLES.md)** - Real-world usage scenarios
- **[FAQ](docs/FAQ.md)** - Frequently asked questions
- **[Installation Guide](docs/INSTALL.md)** - Detailed installation and publishing instructions
- **[Recording Guide](docs/RECORDING.md)** - How to record asciinema demos
- **[Publishing Guide](docs/PUBLISHING.md)** - Steps to publish to GitHub and PyPI
- **[Changelog](docs/CHANGELOG.md)** - Version history

## 📝 License

MIT - see [LICENSE](LICENSE) file for details

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## 🐛 Issues

Found a bug or have a feature request? [Open an issue](https://github.com/wmp/hardlink-cleaner/issues)

## ⭐ Support

If you find this tool useful, please consider giving it a star on GitHub!
