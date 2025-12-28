# Frequently Asked Questions (FAQ)

## General Questions

### What is a hardlink?

A hardlink is a directory entry that associates a name with a file on a filesystem. Multiple hardlinks can point to the same file data (same inode). Unlike symbolic links (symlinks), hardlinks:
- Point directly to the data on disk
- Cannot span different filesystems
- Are indistinguishable from the "original" file
- All have equal status (no "original" vs "copy")

Example:
```bash
echo "data" > file1.txt
ln file1.txt file2.txt  # Creates hardlink
ls -li file*.txt
# Both show same inode number and size
```

### How does hardlink-cleaner work?

1. **Scans** the target directory and builds an inode map
2. **Identifies** files by their unique inode (dev, ino) pair
3. **Searches** the entire filesystem for all paths to those inodes
4. **Deletes** all found paths (effectively removing the file)

### Is it safe to use?

Yes, when used properly:
- ✅ Default dry-run mode shows what would be deleted
- ✅ Confirmation prompts before actual deletion
- ✅ Respects filesystem boundaries with `--xdev`
- ✅ Detailed logging available
- ⚠️ Always review the file list before confirming
- ⚠️ Keep backups of important data

### Will it delete my data?

Only if you confirm the deletion. The tool:
1. Shows you exactly what will be deleted
2. Asks for confirmation (unless `--yes` is used)
3. Can run in `--dry-run` mode (shows without deleting)

## Usage Questions

### How does the cleanup work?

The tool operates in **Global Purge** mode:
- Finds ALL hardlinks across the filesystem
- Deletes every single path to the file
- Result: File is completely gone from all locations

### How do I preview what will be deleted?

```bash
# Use --dry-run flag
hardlink-cleaner /directory --dry-run
```

This shows the list of files and estimated space without deleting anything.

### Why does it show less space than `du`?

Because `du` often double-counts hardlinked files. This tool correctly identifies hardlinks and counts each file only once.

Example:
```bash
# Create 100MB file with 3 hardlinks
dd if=/dev/zero of=file1 bs=1M count=100
ln file1 file2
ln file1 file3

# du shows 300MB (wrong)
du -sh .

# hardlink-cleaner shows 100MB (correct)
hardlink-cleaner . --scan-top
```

### Can I undo a deletion?

**No.** Once files are deleted with hardlink-cleaner, they're gone (unless you have backups).

Always:
1. Use `--dry-run` first
2. Review the file list carefully
3. Make backups of important data

### What does "freed size" mean?

The actual disk space that will be reclaimed when the file is completely deleted. 

For hardlinked files:
- If file has 3 hardlinks, each deletion frees 0 bytes
- Only the last hardlink deletion frees the actual space
- This tool finds and deletes ALL hardlinks at once

## Technical Questions

### How is disk space calculated?

The tool uses **disk usage** (st_blocks × 512) to calculate actual space used:
- Accounts for filesystem block size
- Handles sparse files correctly
- Considers compression (on supported filesystems)

This provides accurate space reclamation estimates.

### Why use `--xdev`?

The `--xdev` flag prevents crossing filesystem boundaries (mount points).

Use it when:
- You only want to clean one filesystem
- You have multiple mounted drives
- You want to avoid accidentally touching network mounts

Example:
```bash
# Clean /home but don't touch mounted /home/user/backup
hardlink-cleaner /home --xdev
```

### How does it handle sparse files?

Sparse files (files with holes) are handled correctly:
- Uses `st_blocks` to calculate actual disk usage
- Freed space reflects actual disk usage, not apparent size

### What happens if files change during scanning?

The tool handles this gracefully:
- Files that disappear: Logged as warnings, operation continues
- Files that appear: Not included in this scan
- Files that change: Uses the stat info from scan time

For best results, run on relatively stable directories.

## Performance Questions

### Why is scanning slow?

Scanning speed depends on:
- Number of files and directories
- Filesystem type and health
- Disk I/O speed
- Whether you use `--xdev`

Tips to speed up:
```bash
# Use --xdev to limit scope
hardlink-cleaner /dir --xdev

# Save scan results for reuse
hardlink-cleaner /dir --save-scan results.json --dry-run
```

### Can I cancel during operation?

Yes:
- During scanning: Press `Ctrl+C`
- During deletion: Press `Ctrl+C` (files deleted so far are gone)
- In interactive mode: Press `q` to quit

### How much RAM does it use?

RAM usage depends on number of files:
- ~100 bytes per file (rough estimate)
- For 1 million files: ~100 MB RAM
- For 10 million files: ~1 GB RAM

For very large filesystems, consider:
```bash
# Scan in smaller chunks
hardlink-cleaner /dir/subdir1
hardlink-cleaner /dir/subdir2
```

## Error Messages

### "Permission denied"

You don't have permission to read or delete files.

Solutions:
```bash
# Run with sudo (careful!)
sudo hardlink-cleaner /protected-dir

# Or change ownership
sudo chown -R $USER /directory
```

### "Operation not permitted" when deleting

File is protected or you lack permissions.

Check:
```bash
# Check file attributes
lsattr filename

# Check if file is open
lsof filename

# Check ownership
ls -l filename
```

### "Cannot cross filesystem boundary"

You're trying to operate across different filesystems without `--xdev`.

Either:
```bash
# Allow crossing filesystems (remove --xdev)
hardlink-cleaner /dir

# Or operate on each filesystem separately
hardlink-cleaner /filesystem1 --xdev
hardlink-cleaner /filesystem2 --xdev
```

## Use Case Questions

### Can I use this for backups?

Yes, if your backup system uses hardlinks (like rsync hardlink backups):

```bash
# Clean old backup snapshots
hardlink-cleaner /backups/old-snapshot
```

But be careful:
- Understand which hardlinks are shared between snapshots
- Test with `--dry-run` first
- Consider using `--clean-hardlinks` (variant A) for safety

### Is this useful for torrent clients?

Yes! Many torrent clients create hardlinks when:
- Seeding and organizing files
- Moving completed downloads
- Creating multiple views of same file

Perfect use case:
```bash
hardlink-cleaner ~/torrents/completed
```

### Can I use this on network filesystems (NFS, CIFS)?

It depends:
- **NFS**: Yes, hardlinks work normally
- **CIFS/SMB**: Usually no hardlink support
- **SSHFS**: Depends on configuration

Best practice: Use `--xdev` to avoid network mounts if unsure.

## Installation Questions

### Do I need root/sudo?

- **Installation**: No (use `pipx install`)
- **Running**: Only if cleaning protected files

### What Python version is required?

Python 3.7 or higher. Check your version:
```bash
python3 --version
```

### Can I use this on Windows?

No, this tool is designed for Linux/Unix filesystems. Windows handles hardlinks differently and has different filesystem semantics.

## Contributing Questions

### How can I report a bug?

Open an issue on GitHub: https://github.com/yourusername/hardlink-cleaner/issues

Include:
- Command you ran
- Error message or unexpected behavior
- Operating system and Python version
- Log output (`--verbose --log file.log`)

### Can I contribute?

Yes! Pull requests welcome. See CONTRIBUTING.md (if available) or just fork and submit PRs.

### Where can I get help?

- GitHub Issues: For bugs and feature requests
- GitHub Discussions: For questions and general help
- Stack Overflow: Tag with `hardlink-cleaner`

## Other Questions

### Does it work on macOS?

Yes, but macOS filesystem semantics may differ. Test thoroughly with `--dry-run` first.

### What about BSD/FreeBSD?

Should work, but not extensively tested. Report issues on GitHub.

### Can I use this in a script?

Yes:
```bash
#!/bin/bash
hardlink-cleaner /directory \
    --yes \
    --no-interactive \
    --log cleanup.log
```

### Is there a GUI version?

No, this is a TUI (Text User Interface) tool designed for terminal use.
