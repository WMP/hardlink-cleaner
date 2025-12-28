# Usage Examples

## Basic Usage

### Quick Start - Interactive Mode
```bash
# Launch interactive browser
hardlink-cleaner /path/to/directory

# Navigate:
#   ↑/↓ or j/k - move cursor
#   Enter or → - enter directory
#   Backspace or ← - go back
#   Space - mark/unmark file or directory
#   d - delete selected items
#   q - quit
```

## Real-World Examples

### Example 1: Clean Torrent Directory

You have a torrent client that creates hardlinks:
```
/data/torrent/complete/movie.mkv (original)
/data/media/movies/movie.mkv (hardlink)
```

To remove all copies:
```bash
# Interactive mode (recommended)
hardlink-cleaner /data/torrent/complete

# Navigate, press Space to mark items
# Press 'd' to delete all hardlinks globally
```

Or non-interactive:
```bash
# Preview what will be deleted
hardlink-cleaner /data/torrent/complete --dry-run

# Actually delete (with confirmation)
hardlink-cleaner /data/torrent/complete

# Skip confirmation
hardlink-cleaner /data/torrent/complete --yes
```

### Example 2: Analyze Without Deleting

Save scan results for later analysis:
```bash
# Scan and save
hardlink-cleaner /large-directory --save-scan analysis.json --dry-run

# Load and browse saved results
hardlink-cleaner /large-directory --load-scan analysis.json
```

### Example 3: Clean Deduplication Storage

You have a deduplicated backup system with hardlinks:
```bash
# Stay on same filesystem
hardlink-cleaner /mnt/backup --xdev

# Interactive selection with filesystem boundary
hardlink-cleaner /mnt/backup --xdev --interactive
```

## Common Workflows

### Workflow 1: Safe Cleanup

1. **Preview deletions**:
   ```bash
   hardlink-cleaner /directory --dry-run
   ```

2. **Review and confirm**:
   ```bash
   hardlink-cleaner /directory
   # It will ask for confirmation
   ```

### Workflow 2: Interactive Selection

1. **Launch TUI**:
   ```bash
   hardlink-cleaner /directory
   ```

2. **Browse and mark**:
   - Navigate to files/directories you want to delete
   - Press `Space` to mark them
   - Green `[X]` indicates selected items

3. **Review selection**:
   - Top of screen shows: `Selected: 42 files, 15.3 GiB`

4. **Delete**:
   - Press `d` to delete
   - Confirm when prompted

### Workflow 3: Scheduled Cleanup

Create a script for automated cleanup:

```bash
#!/bin/bash
# cleanup-script.sh

# Clean old torrents automatically
hardlink-cleaner /data/torrent/completed \
    --yes \
    --no-interactive \
    --log /var/log/hardlink-cleanup.log \
    --xdev

# Email results (optional)
mail -s "Cleanup Report" admin@example.com < /var/log/hardlink-cleanup.log
```

Schedule with cron:
```cron
# Run every Sunday at 3 AM
0 3 * * 0 /path/to/cleanup-script.sh
```

## Tips & Tricks

### Tip 1: Check Before Deleting
Always use `--dry-run` first on important data.

### Tip 2: Use --xdev for Mounted Filesystems
Prevents accidentally crossing into other mounted filesystems.

### Tip 3: Save Scans for Large Directories
For very large directories, save the scan once and analyze multiple times:
```bash
hardlink-cleaner /huge-dir --save-scan scan.json --dry-run
# Analyze later without re-scanning
hardlink-cleaner /huge-dir --load-scan scan.json
```

### Tip 4: Monitor Progress with Logs
```bash
# In one terminal
hardlink-cleaner /large-dir --verbose --log cleanup.log

# In another terminal
tail -f cleanup.log
```

## Troubleshooting

### Problem: "Permission denied" errors
```bash
# Run with sudo (be careful!)
sudo hardlink-cleaner /protected-directory

# Or fix permissions first
sudo chown -R $USER /directory
```

### Problem: Operation too slow
```bash
# Use --xdev to avoid crossing filesystems
hardlink-cleaner /dir --xdev

# Save scan for later analysis
hardlink-cleaner /dir --save-scan scan.json --dry-run
```

### Problem: Can't find all hardlinks
Make sure you're not using `--xdev` if hardlinks are on the same logical filesystem but different mount points.

## Safety Reminders

- ⚠️ Always test with `--dry-run` first
- ⚠️ Review the list of files before confirming deletion
- ⚠️ Keep backups of important data
- ⚠️ Use `--verbose --log file.log` for audit trail
- ⚠️ Be careful with `--yes` flag (skips confirmation)
