# Quick Start Guide

## Install in 30 seconds

```bash
pipx install hardlink-cleaner
```

Or from source:
```bash
git clone https://github.com/wmp/hardlink-cleaner.git
cd hardlink-cleaner
pip install .
```

## Use in 3 steps

### 1. Preview (Safe - Nothing Deleted)
```bash
hardlink-cleaner /path/to/directory --dry-run
```

### 2. Interactive Selection
```bash
hardlink-cleaner /path/to/directory
```
- Use `↑/↓` to navigate
- Press `Space` to mark files/folders
- Press `d` to delete selected items
- Press `q` to quit

### 3. Confirm and Clean
The tool will show you:
- How many files will be deleted
- How much space will be freed
- Ask for confirmation

Press `y` to confirm.

## Common Commands

```bash
# Clean with confirmation (interactive)
hardlink-cleaner /directory

# Clean without confirmation (dangerous!)
hardlink-cleaner /directory --yes

# Stay on same filesystem
hardlink-cleaner /directory --xdev

# Save scan for later
hardlink-cleaner /directory --save-scan results.json --dry-run
```

## Keyboard Shortcuts (Interactive Mode)

| Key | Action |
|-----|--------|
| `↑/↓` | Navigate |
| `Space` | Mark/unmark |
| `d` | Delete |
| `q` | Quit |
| `Enter` | Enter directory |
| `Backspace` | Go back |

## Safety Features

✅ **Dry-run mode** - Preview before deleting  
✅ **Confirmation prompts** - Won't delete without asking  
✅ **Filesystem boundaries** - Stays on same filesystem with `--xdev`  
✅ **Verbose logging** - Track everything with `--verbose --log file.log`

## Example Session

```bash
$ hardlink-cleaner ~/Downloads --dry-run
2025-12-28 18:00:00 INFO Mode: global hardlink purge in /home/user/Downloads
2025-12-28 18:00:01 INFO FS root: /home
2025-12-28 18:00:05 INFO To delete: 42 inodes, 128 paths. Est. freed: 15.30 GiB
2025-12-28 18:00:05 INFO [PURGE] /home/user/Downloads/movie.mkv
2025-12-28 18:00:05 INFO [PURGE] /home/user/media/movie.mkv
2025-12-28 18:00:05 INFO [PURGE] /home/user/backup/movie.mkv
...
2025-12-28 18:00:05 INFO DRY-RUN enabled. Nothing was deleted.

$ hardlink-cleaner ~/Downloads
...
Delete ALL above paths (purge)? [y/N]: y
2025-12-28 18:01:00 INFO Deleted paths: 128. Estimated freed size: 15.30 GiB
```

## Need Help?

- Full documentation: [README.md](README.md)
- More examples: [EXAMPLES.md](EXAMPLES.md)
- FAQs: [FAQ.md](FAQ.md)
- Installation: [INSTALL.md](INSTALL.md)

```bash
# Built-in help
hardlink-cleaner --help
```

## Quick Tips

💡 Always test with `--dry-run` first  
💡 Use interactive mode for precision selection  
💡 Add `--xdev` to stay on one filesystem  
💡 Keep backups of important data
