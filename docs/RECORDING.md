# Recording an asciinema Demo

## Prerequisites

Install asciinema:
```bash
# On Ubuntu/Debian
sudo apt install asciinema

# Or using pipx
pipx install asciinema
```

## Important: Setting Clean Prompt for asciinema

Asciinema starts a new shell which may override your PS1. To ensure clean prompt:

**Option 1: Use command flag (recommended)**
```bash
asciinema rec -c "bash --norc --noprofile" demo.cast
# Then inside the recording:
export PS1='$ '
./scripts/demo.sh
```

**Option 2: Modify shell config temporarily**
```bash
# Add to ~/.bashrc temporarily
if [ -n "$ASCIINEMA_REC" ]; then
    export PS1='$ '
fi

# Then record normally
asciinema rec demo.cast
```

## Quick Recording

### Option 1: Interactive Demo (Recommended)

1. Start recording with clean shell:
```bash
asciinema rec -c "bash --norc --noprofile" hardlink-cleaner-demo.cast
```

2. Set prompt and run demo:
```bash
export PS1='$ '
./scripts/demo.sh
```

3. Stop recording: Press `Ctrl+D` or type `exit`

**Note:** Using `-c "bash --norc --noprofile"` prevents your shell config from overriding PS1. The demo script includes 5-second pauses between steps for readability.

4. Upload to asciinema.org (optional):
```bash
asciinema upload hardlink-cleaner-demo.cast
```

### Option 2: Manual Demo

1. Start recording with clean shell:
```bash
asciinema rec -c "bash --norc --noprofile" -t "Hardlink Cleaner - Interactive TUI Demo" demo.cast
```

2. Set clean prompt:
```bash
export PS1='$ '
```

3. Show help:
```bash
hardlink-cleaner --help
```

4. Create test directory:
```bash
mkdir -p /tmp/test-hardlinks
cd /tmp/test-hardlinks
echo "Test file content" > file1.txt
ln file1.txt file2.txt  # Create hardlink
ln file1.txt file3.txt  # Another hardlink
ls -li  # Show inode numbers (same for all)
```

5. Run hardlink-cleaner:
```bash
hardlink-cleaner /tmp/test-hardlinks
# Navigate with arrows, press 'q' to quit
```

6. Cleanup:
```bash
rm -rf /tmp/test-hardlinks
```

7. Stop recording: `Ctrl+D`

## Recording Tips

- Keep it under 3-4 minutes for best engagement
- Use `asciinema rec --idle-time-limit 2` to limit pauses
- Add title with `-t "Title Here"`
- Use `sleep 5` between major sections for readability
- The demo.sh script already includes proper pauses
- Use comments to explain what you're doing
- Clear screen between sections with `clear`
- Always start with `-c "bash --norc --noprofile"` for clean prompt

## Example Recording Script

```bash
# Start recording with clean shell
asciinema rec -c "bash --norc --noprofile" --idle-time-limit 2 -t "Hardlink Cleaner Demo" demo.cast

# Inside the recording:
export PS1='$ '

# Welcome message
clear
echo "# Hardlink Cleaner - Find and clean hardlinked files"
echo ""
sleep 5

# Show help
hardlink-cleaner --help | head -20
sleep 5

# Run demo
./scripts/demo.sh

# End
echo ""
echo "Thanks for watching! Star on GitHub: https://github.com/wmp/hardlink-cleaner"
sleep 5

# Ctrl+D to stop
```

## Embedding in README

Add to your README.md:
```markdown
## Demo

[![asciicast](https://asciinema.org/a/YOUR_CAST_ID.svg)](https://asciinema.org/a/YOUR_CAST_ID)
```

Or use the local file:
```markdown
## Demo

![Demo](demo.cast)
```
