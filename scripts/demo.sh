#!/bin/bash
# Demo script for asciinema recording
# This creates a test directory structure with hardlinks to demonstrate hardlink-cleaner

set -e

# Set simple prompt for recording (removes hostname, user, path clutter)
export PS1='$ '
export PS2='> '

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Hardlink Cleaner - Demo                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Create demo directory structure
DEMO_DIR="/tmp/hardlink-cleaner-demo"
echo -e "${GREEN}[1/4] Creating demo directory structure...${NC}"
rm -rf "$DEMO_DIR"
mkdir -p "$DEMO_DIR"/data/{torrent/complete,media/{movies,tv,kids}}

# Create original files in torrent directory
echo -e "${GREEN}[2/4] Creating test movie files...${NC}"
dd if=/dev/urandom of="$DEMO_DIR/data/torrent/complete/action_movie.mkv" bs=1M count=120 2>/dev/null
dd if=/dev/urandom of="$DEMO_DIR/data/torrent/complete/comedy_series_s01.mkv" bs=1M count=150 2>/dev/null
dd if=/dev/urandom of="$DEMO_DIR/data/torrent/complete/kids_cartoon.mkv" bs=1M count=80 2>/dev/null
echo ""
sleep 3
echo -e "${BLUE}Files created in torrent/complete:${NC}"
tree -h "$DEMO_DIR/data" 2>/dev/null || ls -lh "$DEMO_DIR/data/torrent/complete/"

# Create hardlinks in media directories
echo ""
sleep 5
echo -e "${GREEN}[3/4] Creating hardlinks in media library...${NC}"
ln "$DEMO_DIR/data/torrent/complete/action_movie.mkv" "$DEMO_DIR/data/media/movies/Action Movie (2024).mkv"
ln "$DEMO_DIR/data/torrent/complete/comedy_series_s01.mkv" "$DEMO_DIR/data/media/tv/Comedy Series - Season 01.mkv"
ln "$DEMO_DIR/data/torrent/complete/kids_cartoon.mkv" "$DEMO_DIR/data/media/kids/Cartoon Adventures.mkv"
echo ""
sleep 3
echo -e "${BLUE}Hardlinks created - full structure:${NC}"
tree -h "$DEMO_DIR/data" 2>/dev/null || find "$DEMO_DIR/data" -type f | sort

# Show structure
echo ""

echo -e "${GREEN}[4/4] Demo structure created!${NC}"
echo -e "${YELLOW}Important: Files with same inode are hardlinks (not copies).${NC}"
echo -e "${YELLOW}They share the same disk space.${NC}"
echo ""
sleep 3
echo -e "${YELLOW}To free disk space, you must delete ALL hardlinks to a file.${NC}"
echo -e "${YELLOW}Deleting just one hardlink won't free any space!${NC}"
echo ""
sleep 5
echo -e "${YELLOW}Disk usage:${NC}"
du -sh "$DEMO_DIR/data/torrent/complete" "$DEMO_DIR/data/media" "$DEMO_DIR/data"
echo ""
sleep 5
echo -e "${YELLOW}Now you can run:${NC}"
echo -e "  ${GREEN}cd $DEMO_DIR/data${NC}"
echo -e "  ${GREEN}hardlink-cleaner torrent/complete${NC}"
echo ""
sleep 5
echo -e "${YELLOW}This will find and allow you to delete:${NC}"
echo -e "  • All files in ${GREEN}torrent/complete/${NC}"
echo -e "  • AND their hardlinks in ${GREEN}media/*/${NC}"
echo ""
sleep 5
echo -e "${YELLOW}Press Enter to start interactive mode...${NC}"
read

# Run interactive mode
echo -e "${GREEN}Launching interactive mode...${NC}"
echo -e "${YELLOW}Navigate with ↑/↓, Space to mark files, 'd' to delete, 'q' to quit${NC}"
echo ""
sleep 5
# Get script directory before changing to demo dir
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DEMO_DIR/data" || exit 1
python3 "$SCRIPT_DIR/hardlink_cleaner.py" "$DEMO_DIR/data" --xdev

echo ""
echo -e "${GREEN}Demo complete!${NC}"
echo ""
