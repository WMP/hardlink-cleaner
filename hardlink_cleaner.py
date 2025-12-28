#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hardlink_cleaner.py
Script for:
- finding directories using the most space (without double-counting hardlinks),
- deleting files that have ALL hardlinks inside the specified directory (variant A),
- deleting symlinks in the specified directory,
- globally deleting all paths (hardlinks) for files in a given directory within the same filesystem.
with argparse support, logging, verbose, dry-run and confirmation.
"""

import argparse
import curses
import logging
import os
import stat
import sys
from collections import defaultdict, deque
from typing import Dict, List, Optional, Set, Tuple

# -------------- Logging --------------


def setup_logging(verbose: bool, log_file: Optional[str]) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=handlers,
    )


# -------------- Size utilities --------------


def file_disk_usage(st: os.stat_result) -> int:
    """Return disk usage in bytes, based on st_blocks if available; otherwise st_size."""
    blocks = getattr(st, "st_blocks", None)
    if blocks is not None and blocks > 0:
        return int(blocks) * 512
    return int(st.st_size)


def dir_size(
    root: str,
    depth: int = 1,
    apparent: bool = False,
    xdev: bool = True,
) -> List[Tuple[str, int]]:
    """
    Return a list of (path, size) for root directory and its subdirectories
    up to a given max depth level (depth counted relative to root).
    Size calculated without double-counting hardlinks.
    If apparent=True, uses st_size instead of st_blocks.
    If xdev=True, doesn't cross to other filesystems (checks st_dev).
    """
    root = os.path.abspath(root)
    try:
        root_dev = os.stat(root, follow_symlinks=False).st_dev
    except FileNotFoundError:
        raise SystemExit(f"Not found: {root}")
    except PermissionError as e:
        raise SystemExit(f"No permission to: {root} ({e})")

    size_map: Dict[str, int] = defaultdict(int)
    seen_inodes: Set[Tuple[int, int]] = set()

    q = deque([(root, 0)])
    while q:
        current, d = q.popleft()
        try:
            with os.scandir(current) as it:
                for entry in it:
                    try:
                        st = entry.stat(follow_symlinks=False)
                    except FileNotFoundError:
                        logging.debug("File vanished: %s", entry.path)
                        continue
                    except PermissionError:
                        logging.warning("No permission: %s", entry.path)
                        continue

                    if xdev and st.st_dev != root_dev:
                        logging.debug("Skipped different FS: %s", entry.path)
                        continue

                    if entry.is_symlink():
                        if apparent:
                            size_map[current] += st.st_size
                        else:
                            size_map[current] += file_disk_usage(st)
                        continue

                    if stat.S_ISDIR(st.st_mode):
                        size_map[current] += (
                            file_disk_usage(st) if not apparent else st.st_size
                        )
                        if d < depth:
                            q.append((entry.path, d + 1))
                    elif stat.S_ISREG(st.st_mode):
                        key = (st.st_dev, st.st_ino)
                        if key in seen_inodes:
                            continue
                        seen_inodes.add(key)
                        size_map[current] += (
                            file_disk_usage(st) if not apparent else st.st_size
                        )
                    else:
                        size_map[current] += (
                            file_disk_usage(st) if not apparent else st.st_size
                        )
        except FileNotFoundError:
            logging.debug("Directory vanished: %s", current)
            continue
        except NotADirectoryError:
            logging.debug("Not a directory (race): %s", current)
            continue
        except PermissionError:
            logging.warning("No permission to directory: %s", current)
            continue

    return list(size_map.items())


# -------------- Variant A: deleting files whose ALL links are in directory --------------


def find_deletable_inodes_variant_a(
    target_dir: str, xdev: bool = True
) -> Tuple[Dict[Tuple[int, int], List[str]], Dict[Tuple[int, int], os.stat_result]]:
    target_dir = os.path.abspath(target_dir)
    try:
        root_stat = os.stat(target_dir, follow_symlinks=False)
    except FileNotFoundError:
        raise SystemExit(f"Not found: {target_dir}")
    except PermissionError as e:
        raise SystemExit(f"No permission to: {target_dir} ({e})")

    root_dev = root_stat.st_dev
    inode_to_paths: Dict[Tuple[int, int], List[str]] = defaultdict(list)
    inode_to_stat: Dict[Tuple[int, int], os.stat_result] = {}

    for curdir, dirs, files in os.walk(target_dir, followlinks=False):
        try:
            curdir_dev = os.stat(curdir, follow_symlinks=False).st_dev
        except Exception:
            curdir_dev = root_dev
        if xdev and curdir_dev != root_dev:
            dirs[:] = []
            continue

        for fname in files:
            path = os.path.join(curdir, fname)
            try:
                st = os.stat(path, follow_symlinks=False)
            except FileNotFoundError:
                continue
            except PermissionError:
                logging.warning("No permission to file: %s", path)
                continue
            if not stat.S_ISREG(st.st_mode):
                continue
            key = (st.st_dev, st.st_ino)
            inode_to_paths[key].append(path)
            inode_to_stat[key] = st

    deletable: Dict[Tuple[int, int], List[str]] = {}
    for key, paths in inode_to_paths.items():
        st = inode_to_stat[key]
        if st.st_nlink == len(paths):
            deletable[key] = sorted(paths)

    return deletable, inode_to_stat


def delete_variant_a(
    target_dir: str,
    yes: bool = False,
    dry_run: bool = True,
    xdev: bool = True,
) -> Tuple[int, int, int]:
    deletable, inode_to_stat = find_deletable_inodes_variant_a(target_dir, xdev=xdev)

    total_inodes = len(deletable)
    total_paths = sum(len(v) for v in deletable.values())
    freed_bytes = 0
    for key in deletable:
        st = inode_to_stat[key]
        freed_bytes += file_disk_usage(st)

    if total_inodes == 0:
        logging.info("No files qualifying for complete deletion in: %s", target_dir)
        return (0, 0, 0)

    logging.info(
        "Qualifying for complete deletion: %d inodes, %d paths",
        total_inodes,
        total_paths,
    )
    logging.info(
        "Estimated freed size: %d B (%.2f MiB)",
        freed_bytes,
        freed_bytes / 1024 / 1024,
    )

    for key, paths in deletable.items():
        logging.debug("INODE %s has %d paths to delete", key, len(paths))
        for p in paths:
            logging.info("[DEL] %s", p)

    if dry_run:
        logging.info("DRY-RUN enabled. Nothing was deleted.")
        return (total_inodes, total_paths, freed_bytes)

    if not yes:
        ans = input("Delete above files completely? [y/N]: ").strip().lower()
        if ans not in ("y", "yes"):
            logging.info("Cancelled by user.")
            return (0, 0, 0)

    removed_paths = 0
    for paths in deletable.values():
        for p in paths:
            try:
                os.unlink(p)
                removed_paths += 1
            except FileNotFoundError:
                logging.warning("Already doesn't exist: %s", p)
            except PermissionError:
                logging.error("No permission to delete: %s", p)
            except IsADirectoryError:
                logging.error("This is a directory (expected file): %s", p)
            except OSError as e:
                logging.error("Error deleting %s: %s", p, e)

    logging.info(
        "Deleted paths: %d. Estimated freed size: %.2f MiB",
        removed_paths,
        freed_bytes / 1024 / 1024,
    )
    return (total_inodes, removed_paths, freed_bytes)


# -------------- Global hardlink group cleanup --------------


def detect_fs_root(path: str) -> str:
    """
    Find "root" of current filesystem (highest directory with the same st_dev).
    """
    path = os.path.abspath(path)
    try:
        target_dev = os.stat(path, follow_symlinks=False).st_dev
    except Exception as e:
        raise SystemExit(f"Cannot stat() path {path}: {e}")

    cur = path
    parent = os.path.dirname(cur)
    while True:
        try:
            parent_dev = os.stat(parent, follow_symlinks=False).st_dev
        except Exception:
            break
        if parent_dev != target_dev or parent == cur:
            break
        cur = parent
        parent = os.path.dirname(cur)
    return cur


def collect_target_inodes(
    target_dir: str, xdev: bool = True
) -> Tuple[Set[Tuple[int, int]], Dict[Tuple[int, int], os.stat_result]]:
    """
    Collect set of inodes (dev, ino) for ALL regular files in target_dir.
    Also returns inode -> stat map for size estimation.
    """
    target_dir = os.path.abspath(target_dir)
    try:
        root_stat = os.stat(target_dir, follow_symlinks=False)
    except FileNotFoundError:
        raise SystemExit(f"Not found: {target_dir}")
    except PermissionError as e:
        raise SystemExit(f"No permission to: {target_dir} ({e})")

    root_dev = root_stat.st_dev
    inodes: Set[Tuple[int, int]] = set()
    inode_stat: Dict[Tuple[int, int], os.stat_result] = {}

    for curdir, dirs, files in os.walk(target_dir, followlinks=False):
        try:
            curdir_dev = os.stat(curdir, follow_symlinks=False).st_dev
        except Exception:
            curdir_dev = root_dev
        if xdev and curdir_dev != root_dev:
            dirs[:] = []
            continue

        for fname in files:
            path = os.path.join(curdir, fname)
            try:
                st = os.stat(path, follow_symlinks=False)
            except FileNotFoundError:
                continue
            except PermissionError:
                logging.warning("No permission to file: %s", path)
                continue
            if not stat.S_ISREG(st.st_mode):
                continue
            key = (st.st_dev, st.st_ino)
            inodes.add(key)
            inode_stat[key] = st
    return inodes, inode_stat


def find_all_paths_for_inodes(
    fs_root: str, inodes: Set[Tuple[int, int]], xdev: bool = True
) -> Dict[Tuple[int, int], List[str]]:
    """
    Walk entire filesystem from fs_root and find all paths to given inodes.
    """
    fs_root = os.path.abspath(fs_root)
    try:
        root_stat = os.stat(fs_root, follow_symlinks=False)
    except Exception as e:
        raise SystemExit(f"Cannot stat() fs_root {fs_root}: {e}")

    root_dev = root_stat.st_dev
    hits: Dict[Tuple[int, int], List[str]] = defaultdict(list)

    for curdir, dirs, files in os.walk(fs_root, followlinks=False):
        try:
            curdir_stat = os.stat(curdir, follow_symlinks=False)
            curdir_dev = curdir_stat.st_dev
        except Exception:
            curdir_dev = root_dev
        if xdev and curdir_dev != root_dev:
            dirs[:] = []
            continue

        try:
            with os.scandir(curdir) as it:
                for entry in it:
                    try:
                        st = entry.stat(follow_symlinks=False)
                    except FileNotFoundError:
                        continue
                    except PermissionError:
                        logging.debug("No permission: %s", entry.path)
                        continue

                    if xdev and st.st_dev != root_dev:
                        continue
                    if not stat.S_ISREG(st.st_mode):
                        continue

                    key = (st.st_dev, st.st_ino)
                    if key in inodes:
                        hits[key].append(entry.path)
        except PermissionError:
            logging.debug("No permission to: %s", curdir)
            continue
        except FileNotFoundError:
            continue

    return hits


def purge_hardlink_groups_globally(
    target_dir: str,
    fs_root: Optional[str] = None,
    yes: bool = False,
    dry_run: bool = True,
    xdev: bool = True,
) -> Tuple[int, int, int]:
    """
    For all files from target_dir, find and delete *all* their paths (hardlinks)
    within the same filesystem (from fs_root). Returns: (inode_count, deleted_path_count, freed_bytes_estimate).
    Freed bytes counted once per inode (complete object deletion).
    """
    inodes, inode_stat = collect_target_inodes(target_dir, xdev=xdev)
    if not inodes:
        logging.info("No files to purge in: %s", target_dir)
        return (0, 0, 0)

    if fs_root is None:
        fs_root = detect_fs_root(target_dir)
    logging.info("FS root: %s", fs_root)

    hits = find_all_paths_for_inodes(fs_root, inodes, xdev=xdev)

    freed_bytes = 0
    total_paths = 0
    for key, paths in hits.items():
        total_paths += len(paths)
        st = inode_stat.get(key)
        if st is not None:
            freed_bytes += file_disk_usage(st)

    if not hits:
        logging.info("No paths found to delete within %s", fs_root)
        return (0, 0, 0)

    logging.info(
        "To delete: %d inodes, %d paths. Est. freed: %.2f MiB",
        len(hits),
        total_paths,
        freed_bytes / 1024 / 1024,
    )

    for key, paths in hits.items():
        for p in paths:
            logging.info("[PURGE] %s", p)

    if dry_run:
        logging.info("DRY-RUN enabled. Nothing was deleted.")
        return (len(hits), total_paths, freed_bytes)

    if not yes:
        ans = input("Delete ALL above paths (purge)? [y/N]: ").strip().lower()
        if ans not in ("y", "yes"):
            logging.info("Cancelled by user.")
            return (0, 0, 0)

    removed_paths = 0
    for key, paths in hits.items():
        for p in paths:
            try:
                os.unlink(p)
                removed_paths += 1
            except FileNotFoundError:
                logging.warning("Already doesn't exist: %s", p)
            except PermissionError:
                logging.error("No permission to delete: %s", p)
            except IsADirectoryError:
                logging.error("This is a directory (expected file): %s", p)
            except OSError as e:
                logging.error("Error deleting %s: %s", p, e)

    logging.info(
        "Deleted paths: %d. Estimated freed size: %.2f MiB",
        removed_paths,
        freed_bytes / 1024 / 1024,
    )
    return (len(hits), removed_paths, freed_bytes)


# -------------- Removing symlinks in directory --------------


def remove_symlinks(
    target_dir: str, yes: bool = False, dry_run: bool = True, xdev: bool = True
) -> Tuple[int, int]:
    target_dir = os.path.abspath(target_dir)
    try:
        root_stat = os.stat(target_dir, follow_symlinks=False)
    except FileNotFoundError:
        raise SystemExit(f"Not found: {target_dir}")
    except PermissionError as e:
        raise SystemExit(f"No permission to: {target_dir} ({e})")

    root_dev = root_stat.st_dev

    symlinks: List[str] = []
    total_size = 0
    for curdir, dirs, files in os.walk(target_dir, followlinks=False):
        try:
            curdir_dev = os.stat(curdir, follow_symlinks=False).st_dev
        except Exception:
            curdir_dev = root_dev
        if xdev and curdir_dev != root_dev:
            dirs[:] = []
            continue

        with os.scandir(curdir) as it:
            for entry in it:
                try:
                    st = entry.stat(follow_symlinks=False)
                except FileNotFoundError:
                    continue
                except PermissionError:
                    logging.warning("No permission: %s", entry.path)
                    continue

                if entry.is_symlink():
                    symlinks.append(entry.path)
                    total_size += st.st_size

    if not symlinks:
        logging.info("No symlinks to delete in: %s", target_dir)
        return (0, 0)

    for p in symlinks:
        logging.info("[SYMLINK] %s", p)

    logging.info("Found %d symlinks. Total link size: %d B", len(symlinks), total_size)

    if dry_run:
        logging.info("DRY-RUN enabled. Nothing was deleted.")
        return (len(symlinks), total_size)

    if not yes:
        ans = input("Delete above symlinks? [y/N]: ").strip().lower()
        if ans not in ("y", "yes"):
            logging.info("Cancelled by user.")
            return (0, 0)

    removed = 0
    for p in symlinks:
        try:
            os.unlink(p)
            removed += 1
        except FileNotFoundError:
            logging.warning("Already doesn't exist: %s", p)
        except PermissionError:
            logging.error("No permission to delete: %s", p)
        except IsADirectoryError:
            logging.error("Symlink is a directory? %s", p)
        except OSError as e:
            logging.error("Error deleting %s: %s", p, e)

    logging.info("Deleted symlinks: %d", removed)
    return (removed, total_size)


# -------------- Saving/loading scan results --------------


def save_scan_results(
    target_dir: str,
    fs_root: str,
    inodes: Set[Tuple[int, int]],
    inode_stat: Dict[Tuple[int, int], os.stat_result],
    hits: Dict[Tuple[int, int], List[str]],
    filename: str,
) -> None:
    """Saves scan results to JSON file."""
    import json

    data = {
        "target_dir": target_dir,
        "fs_root": fs_root,
        "inodes": [list(k) for k in inodes],
        "inode_stat": {
            str(k): {
                "st_size": s.st_size,
                "st_blocks": getattr(s, "st_blocks", 0),
                "st_dev": s.st_dev,
                "st_ino": s.st_ino,
                "st_nlink": s.st_nlink,
            }
            for k, s in inode_stat.items()
        },
        "hits": {str(k): v for k, v in hits.items()},
    }
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    logging.info("Saved scan results to: %s", filename)


def load_scan_results(
    filename: str,
) -> Tuple[
    str,
    str,
    Set[Tuple[int, int]],
    Dict[Tuple[int, int], os.stat_result],
    Dict[Tuple[int, int], List[str]],
]:
    """Loads scan results from JSON file."""
    import json

    with open(filename, "r") as f:
        data = json.load(f)

    # Reconstruct data structures
    inodes = {tuple(k) for k in data["inodes"]}

    # Convert inode_stat - create simple class instead of os.stat_result
    class StatProxy:
        def __init__(self, data_dict):
            self.st_size = data_dict["st_size"]
            self.st_blocks = data_dict["st_blocks"]
            self.st_dev = data_dict["st_dev"]
            self.st_ino = data_dict["st_ino"]
            self.st_nlink = data_dict["st_nlink"]

    inode_stat = {}
    for k_str, v in data["inode_stat"].items():
        k = eval(k_str)  # Convert string "(dev, ino)" back to tuple
        inode_stat[k] = StatProxy(v)

    hits = {eval(k): v for k, v in data["hits"].items()}

    logging.info("Loaded scan results from: %s", filename)
    logging.info("  - %d inodes", len(inodes))
    logging.info("  - %d hardlink groups", len(hits))

    return data["target_dir"], data["fs_root"], inodes, inode_stat, hits


# -------------- Interactive TUI interface --------------


def interactive_purge_mode(
    target_dir: str,
    fs_root: Optional[str] = None,
    xdev: bool = True,
) -> Tuple[
    Set[Tuple[int, int]],
    Dict[Tuple[int, int], os.stat_result],
    Dict[Tuple[int, int], List[str]],
]:
    """
    Interactive file selection mode for purge in ncdu style.
    Navigate through directories, aggregated sizes, mark files.
    Returns: (selected_inodes, inode_stat, filtered_hits)
    """
    target_dir = os.path.abspath(target_dir)

    if fs_root is None:
        fs_root = detect_fs_root(target_dir)

    try:
        root_stat = os.stat(target_dir, follow_symlinks=False)
        root_dev = root_stat.st_dev
    except Exception as e:
        logging.error("Cannot read directory %s: %s", target_dir, e)
        return (set(), {}, {})

    # Function to scan directory and calculate sizes with aggregation
    def scan_directory(
        dirpath: str,
    ) -> List[Tuple[str, bool, int, Optional[Tuple[int, int]]]]:
        """
        Scans directory and returns list of (name, is_dir, size, inode_key).
        For directories size is the sum of contents (without double-counting hardlinks).
        """
        items = []
        seen_inodes = set()

        try:
            entries = list(os.scandir(dirpath))
        except (PermissionError, FileNotFoundError, NotADirectoryError) as e:
            logging.warning("Cannot read directory %s: %s", dirpath, e)
            return []

        for entry in entries:
            try:
                st = entry.stat(follow_symlinks=False)
            except (FileNotFoundError, PermissionError):
                continue

            if xdev and st.st_dev != root_dev:
                continue

            if entry.is_symlink():
                # Symlinks - show their own size
                size = file_disk_usage(st)
                items.append((entry.name, False, size, None))
            elif entry.is_dir(follow_symlinks=False):
                # Directories - calculate recursively aggregated size
                dir_size = calculate_dir_size(entry.path, seen_inodes)
                items.append((entry.name, True, dir_size, None))
            elif stat.S_ISREG(st.st_mode):
                # Regular file
                key = (st.st_dev, st.st_ino)
                size = file_disk_usage(st)
                items.append((entry.name, False, size, key))
            else:
                # Other (devices, etc.)
                size = file_disk_usage(st)
                items.append((entry.name, False, size, None))

        # Sort by size descending
        items.sort(key=lambda x: x[2], reverse=True)
        return items

    def calculate_dir_size(dirpath: str, seen_inodes: Set[Tuple[int, int]]) -> int:
        """
        Recursively calculates directory size without double-counting hardlinks.
        Uses passed seen_inodes set to track already counted files.
        """
        total_size = 0

        try:
            # Size of directory itself
            dir_st = os.stat(dirpath, follow_symlinks=False)
            total_size += file_disk_usage(dir_st)
        except Exception:
            pass

        try:
            with os.scandir(dirpath) as it:
                for entry in it:
                    try:
                        st = entry.stat(follow_symlinks=False)
                    except (FileNotFoundError, PermissionError):
                        continue

                    if xdev and st.st_dev != root_dev:
                        continue

                    if entry.is_symlink():
                        total_size += file_disk_usage(st)
                    elif entry.is_dir(follow_symlinks=False):
                        total_size += calculate_dir_size(entry.path, seen_inodes)
                    elif stat.S_ISREG(st.st_mode):
                        key = (st.st_dev, st.st_ino)
                        if key not in seen_inodes:
                            seen_inodes.add(key)
                            total_size += file_disk_usage(st)
                    else:
                        total_size += file_disk_usage(st)
        except (PermissionError, FileNotFoundError, NotADirectoryError):
            pass

        return total_size

    def collect_files_from_directory(
        dirpath: str, root_dev: int
    ) -> Dict[str, Tuple[int, int]]:
        """
        Recursively collects all files from directory.
        Returns: dict {full_path: inode_key}
        """
        files = {}
        try:
            for curdir, dirs, filenames in os.walk(dirpath, followlinks=False):
                # Check xdev
                try:
                    curdir_dev = os.stat(curdir, follow_symlinks=False).st_dev
                    if xdev and curdir_dev != root_dev:
                        dirs[:] = []  # Don't go deeper
                        continue
                except Exception:
                    continue

                for fname in filenames:
                    fpath = os.path.join(curdir, fname)
                    try:
                        st = os.stat(fpath, follow_symlinks=False)
                        if stat.S_ISREG(st.st_mode):
                            key = (st.st_dev, st.st_ino)
                            files[fpath] = key
                    except (FileNotFoundError, PermissionError):
                        continue
        except (PermissionError, FileNotFoundError):
            pass
        return files

    def tui_main(stdscr):
        curses.curs_set(0)
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Highlight
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Selected
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Header
        curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)  # Directories

        current_dir = target_dir
        current_idx = 0
        scroll_offset = 0
        selected_items = {}  # selected paths (files OR directories) -> 'file' or 'dir'
        selected_file_inodes = {}  # complete list of files to delete: path -> inode_key

        # Cache for directory contents
        dir_cache = {}

        while True:
            # Load current directory contents
            if current_dir not in dir_cache:
                stdscr.clear()
                stdscr.addstr(0, 0, "Scanning directory...", curses.A_DIM)
                stdscr.refresh()
                dir_cache[current_dir] = scan_directory(current_dir)

            items = dir_cache[current_dir]

            # Draw interface
            stdscr.clear()
            height, width = stdscr.getmaxyx()

            # Header with current path
            header = f"ncdu-like: {current_dir}"
            if len(header) > width - 1:
                header = "..." + header[-(width - 4) :]
            stdscr.addstr(
                0, 0, header[: width - 1], curses.color_pair(3) | curses.A_BOLD
            )

            # Help
            help_text = "↑/↓: navigate | Enter/→: enter | Backspace/←: exit | SPACE: mark | d: delete | q: quit"
            if len(help_text) > width - 1:
                help_text = "↑/↓ Enter/→ Back/← SPACE d:delete q:quit"
            stdscr.addstr(1, 0, help_text[: width - 1], curses.A_DIM)

            # Status of selected
            selected_count = len(
                selected_file_inodes
            )  # Number of FILES (not directories)
            selected_size = 0
            for path, inode_key in selected_file_inodes.items():
                try:
                    st = os.stat(path, follow_symlinks=False)
                    selected_size += file_disk_usage(st)
                except Exception:
                    pass

            status = f"Selected: {selected_count} files, {human_bytes(selected_size)}"
            stdscr.addstr(2, 0, status[: width - 1], curses.color_pair(2))
            stdscr.addstr(3, 0, "-" * min(width - 1, 100))

            # List of files and directories
            visible_height = height - 5

            # Automatic scrolling
            if current_idx < scroll_offset:
                scroll_offset = current_idx
            if current_idx >= scroll_offset + visible_height:
                scroll_offset = current_idx - visible_height + 1

            for i in range(visible_height):
                list_idx = scroll_offset + i
                if list_idx >= len(items):
                    break

                name, is_dir, size, inode_key = items[list_idx]
                full_path = os.path.join(current_dir, name)
                is_selected = full_path in selected_items
                is_current = list_idx == current_idx

                # Formatting
                size_str = human_bytes(size)

                if is_dir:
                    prefix = "/"
                    mark = (
                        "[X]" if full_path in selected_items else "[ ]"
                    )  # Directories can also be marked
                else:
                    prefix = " "
                    mark = "[X]" if full_path in selected_items else "[ ]"

                # Shorten name if too long
                max_name_len = width - len(mark) - len(size_str) - 5
                if len(name) > max_name_len:
                    name_display = name[: max_name_len - 3] + "..."
                else:
                    name_display = name

                line = f"{mark} {size_str:>12} {prefix}{name_display}"
                line = line[: width - 1]

                y = 4 + i

                # Choose color and style
                if is_current and is_selected:
                    attrs = curses.color_pair(1) | curses.A_BOLD
                elif is_current:
                    attrs = curses.color_pair(1) | curses.A_BOLD
                elif is_selected:
                    attrs = curses.color_pair(2)
                elif is_dir:
                    attrs = curses.color_pair(4)
                else:
                    attrs = curses.A_NORMAL

                try:
                    stdscr.addstr(y, 0, line, attrs)
                except curses.error:
                    pass  # Ignore errors when drawing off-screen

            stdscr.refresh()

            # Handle keys
            key = stdscr.getch()

            if key == ord("q") or key == ord("Q"):
                return None  # Cancel

            elif key == ord("d") or key == ord("D"):
                if selected_file_inodes:
                    return selected_file_inodes  # Confirm deletion

            elif key == ord(" "):  # SPACE - mark/unmark file OR directory
                if 0 <= current_idx < len(items):
                    name, is_dir, size, inode_key = items[current_idx]
                    full_path = os.path.join(current_dir, name)

                    if full_path in selected_items:
                        # Unmark
                        del selected_items[full_path]
                        # Remove all files from this directory/file from selected_file_inodes
                        if is_dir:
                            # Remove all files belonging to this directory
                            to_remove = [
                                p
                                for p in selected_file_inodes.keys()
                                if p.startswith(full_path + os.sep)
                            ]
                            for p in to_remove:
                                del selected_file_inodes[p]
                        else:
                            if full_path in selected_file_inodes:
                                del selected_file_inodes[full_path]
                    else:
                        # Mark
                        if is_dir:
                            selected_items[full_path] = "dir"
                            # Collect all files from directory
                            dir_files = collect_files_from_directory(
                                full_path, root_dev
                            )
                            selected_file_inodes.update(dir_files)
                        else:
                            selected_items[full_path] = "file"
                            if inode_key:
                                selected_file_inodes[full_path] = inode_key

                    # Move cursor down
                    if current_idx < len(items) - 1:
                        current_idx += 1

            elif key == curses.KEY_UP or key == ord("k"):
                if current_idx > 0:
                    current_idx -= 1

            elif key == curses.KEY_DOWN or key == ord("j"):
                if current_idx < len(items) - 1:
                    current_idx += 1

            elif (
                key == curses.KEY_RIGHT
                or key == ord("\n")
                or key == curses.KEY_ENTER
                or key == 10
                or key == 13
            ):
                # Enter directory
                if 0 <= current_idx < len(items):
                    name, is_dir, size, inode_key = items[current_idx]
                    if is_dir:
                        new_dir = os.path.join(current_dir, name)
                        if os.path.isdir(new_dir):
                            current_dir = new_dir
                            current_idx = 0
                            scroll_offset = 0

            elif (
                key == curses.KEY_LEFT
                or key == curses.KEY_BACKSPACE
                or key == 127
                or key == 8
            ):
                # Exit to parent directory
                parent = os.path.dirname(current_dir)
                if parent != current_dir:  # We're not at root
                    current_dir = parent
                    current_idx = 0
                    scroll_offset = 0

            elif key == curses.KEY_PPAGE:  # Page Up
                current_idx = max(0, current_idx - visible_height)

            elif key == curses.KEY_NPAGE:  # Page Down
                current_idx = min(len(items) - 1, current_idx + visible_height)

            elif key == curses.KEY_HOME or key == ord("g"):
                current_idx = 0

            elif key == curses.KEY_END or key == ord("G"):
                current_idx = len(items) - 1 if items else 0

    # Run curses interface
    try:
        selected_indices = curses.wrapper(tui_main)
    except KeyboardInterrupt:
        logging.info("Interrupted by user")
        return (set(), {}, {})

    if selected_indices is None:
        logging.info("Cancelled by user")
        return (set(), {}, {})

    if not selected_indices:
        logging.info("No files selected")
        return (set(), {}, {})

    # selected_indices is now dict {path: inode_key}
    # Collect unique inodes
    selected_inodes = set(selected_indices.values())

    # Collect statistics
    logging.info("Collecting information about selected files...")
    inode_stat = {}

    for path, inode_key in selected_indices.items():
        try:
            st = os.stat(path, follow_symlinks=False)
            if stat.S_ISREG(st.st_mode):
                if inode_key not in inode_stat:
                    inode_stat[inode_key] = st
        except (FileNotFoundError, PermissionError) as e:
            logging.warning("Cannot read file %s: %s", path, e)

    if not selected_inodes:
        logging.info("No valid files found for deletion")
        return (set(), {}, {})

    # Find all hardlinks of selected files
    logging.info("Scanning filesystem for all hardlinks...")
    filtered_hits = find_all_paths_for_inodes(fs_root, selected_inodes, xdev=xdev)

    return (selected_inodes, inode_stat, filtered_hits)


# -------------- Size formatting --------------


def human_bytes(n: int) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]
    s = float(n) if n is not None else 0.0
    for u in units:
        if s < 1024 or u == units[-1]:
            return f"{s:.2f} {u}"
        s /= 1024.0
    return f"{n} B"


# -------------- CLI --------------


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Script: scan largest directories, cleanup hardlinks (variant A), remove symlinks, global hardlink purge."
    )

    p.add_argument("root", help="Root directory for analysis / operation")
    p.add_argument(
        "--xdev",
        action="store_true",
        help="Don't enter different filesystem (check st_dev)",
    )
    p.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        default=True,
        help="Interactive mode (TUI) for selecting files to purge (default)",
    )
    p.add_argument(
        "--no-interactive",
        action="store_false",
        dest="interactive",
        help="Disable interactive mode",
    )
    p.add_argument(
        "--yes", "-y", action="store_true", help="Don't ask for confirmation"
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Only show what would be done; don't delete anything",
    )
    p.add_argument(
        "--save-scan",
        help="Save scan results to JSON file (enables later loading and analysis)",
    )
    p.add_argument(
        "--load-scan",
        help="Load scan results from JSON file instead of scanning again",
    )
    p.add_argument("--verbose", "-v", action="store_true", help="More logs (DEBUG)")
    p.add_argument("--log", help="Log file (optional)")

    return p.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    setup_logging(args.verbose, args.log)

    root = os.path.abspath(args.root)
    if not os.path.exists(root):
        logging.error("Directory doesn't exist: %s", root)
        return 2
    if not os.path.isdir(root):
        logging.error("This is not a directory: %s", root)
        return 2

    # Global hardlink purge
    fs_root = None

    # Load from file instead of scanning
    if args.load_scan:
        logging.info("Loading scan results from file: %s", args.load_scan)
        try:
            (
                target_dir_loaded,
                fs_root_loaded,
                inodes_loaded,
                inode_stat_loaded,
                hits_loaded,
            ) = load_scan_results(args.load_scan)
            # Use loaded data instead of scanning again
            root = target_dir_loaded
            if fs_root is None:
                fs_root = fs_root_loaded

            # In load mode we don't do interactive scanning
            # just show what was saved
            selected_inodes = inodes_loaded
            inode_stat = inode_stat_loaded
            filtered_hits = hits_loaded

            logging.info("Loaded data for directory: %s", root)
        except Exception as e:
            logging.error("Error loading scan file: %s", e)
            return 2

    # Interactive mode
    elif args.interactive:
        logging.info(
            "Mode: interactive hardlink purge in %s (fs_root=%s)",
            root,
            fs_root or "auto",
        )
        selected_inodes, inode_stat, filtered_hits = interactive_purge_mode(
            root, fs_root=fs_root, xdev=args.xdev
        )

        # Save scan results if option provided
        if args.save_scan and selected_inodes:
            if fs_root is None:
                fs_root = detect_fs_root(root)
            save_scan_results(
                root,
                fs_root,
                selected_inodes,
                inode_stat,
                filtered_hits,
                args.save_scan,
            )

        if not selected_inodes:
            logging.info("No files selected for deletion")
            return 0

        # Calculate statistics
        total_paths = sum(len(v) for v in filtered_hits.values())
        freed_bytes = sum(
            file_disk_usage(inode_stat[k]) for k in selected_inodes if k in inode_stat
        )

        logging.info(
            "Selected: %d inodes, %d paths. Est. freed: %.2f MiB",
            len(selected_inodes),
            total_paths,
            freed_bytes / 1024 / 1024,
        )

        # Display all paths to delete
        for key, paths in filtered_hits.items():
            for p in paths:
                logging.info("[PURGE] %s", p)

        if args.dry_run:
            logging.info("DRY-RUN enabled. Nothing was deleted.")
        else:
            # Confirmation if not --yes
            if not args.yes:
                ans = input("Delete ALL above paths (purge)? [y/N]: ").strip().lower()
                if ans not in ("y", "yes"):
                    logging.info("Cancelled by user.")
                    return 0

            # Delete files
            removed_paths = 0
            for key, paths in filtered_hits.items():
                for p in paths:
                    try:
                        os.unlink(p)
                        removed_paths += 1
                    except FileNotFoundError:
                        logging.warning("Already doesn't exist: %s", p)
                    except PermissionError:
                        logging.error("No permission to delete: %s", p)
                    except IsADirectoryError:
                        logging.error("This is a directory (expected file): %s", p)
                    except OSError as e:
                        logging.error("Error deleting %s: %s", p, e)

            logging.info(
                "Deleted paths: %d. Estimated freed size: %.2f MiB",
                removed_paths,
                freed_bytes / 1024 / 1024,
            )
    else:
        # Non-interactive mode (original)
        logging.info(
            "Mode: global hardlink purge in %s (fs_root=%s)",
            root,
            fs_root or "auto",
        )

        # If --save-scan provided, first collect data without deleting
        if args.save_scan:
            # Collect inodes and find all paths
            inodes, inode_stat = collect_target_inodes(root, xdev=args.xdev)
            if fs_root is None:
                fs_root = detect_fs_root(root)
            hits = find_all_paths_for_inodes(fs_root, inodes, xdev=args.xdev)

            # Save results
            save_scan_results(root, fs_root, inodes, inode_stat, hits, args.save_scan)

            # Continue with deletion if not dry-run
            if args.dry_run:
                total_paths = sum(len(v) for v in hits.values())
                freed_bytes = sum(
                    file_disk_usage(inode_stat[k]) for k in inodes if k in inode_stat
                )
                logging.info(
                    "DRY-RUN: saved scan. Purge summary: inodes=%d, paths=%d, freed~=%s",
                    len(inodes),
                    total_paths,
                    human_bytes(freed_bytes),
                )
            else:
                # Execute purge using standard function
                inodes_count, removed_paths, freed = purge_hardlink_groups_globally(
                    root,
                    fs_root=fs_root,
                    yes=args.yes,
                    dry_run=args.dry_run,
                    xdev=args.xdev,
                )
                logging.info(
                    "Purge summary: inodes=%d, paths=%d, freed~=%s",
                    inodes_count,
                    removed_paths,
                    human_bytes(freed),
                )
        else:
            # Standard purge without saving
            inodes, removed_paths, freed = purge_hardlink_groups_globally(
                root,
                fs_root=fs_root,
                yes=args.yes,
                dry_run=args.dry_run,
                xdev=args.xdev,
            )
            logging.info(
                "Purge summary: inodes=%d, paths=%d, freed~=%s",
                inodes,
                removed_paths,
                human_bytes(freed),
            )

    return 0


def main_entry():
    """Entry point for console script."""
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        print("\nInterrupted by user.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main_entry()
