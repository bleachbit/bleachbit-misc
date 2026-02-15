#!/usr/bin/env python3
# vim: ts=4:sw=4:expandtab

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2025 to 2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""Summarize translation changes over a git commit range."""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from typing import Dict, List, Optional


WEBLATE_URL_TEMPLATE = 'https://hosted.weblate.org/projects/bleachbit/main/%s/'
MSGSTR_PATTERN = re.compile(r'\+msgstr\s+"(.*)"\s*$')
MULTILINE_MSGSTR_PATTERN = re.compile(r'\+"(.+)"')
MAX_LOOKAHEAD_LINES = 20


class BleachbitLanguageManager:
    """Manages bleachbit.Language module import with lazy initialization."""

    def __init__(self, repo_path: str):
        """Initialize the manager.

        Args:
            repo_path: Path to the bleachbit repository
        """
        self.repo_path = repo_path
        self._language_module = None

    def get_language_module(self):
        """Get bleachbit.Language module, importing only once.

        Returns:
            bleachbit.Language module
        """
        if self._language_module is None:
            sys.path.insert(0, self.repo_path)
            import bleachbit.Language
            self._language_module = bleachbit.Language
        return self._language_module

    def get_locale_name(self, locale_code: str) -> str:
        """Convert locale code to human-readable name with Weblate link.

        Args:
            locale_code: The locale code (e.g., 'de', 'fr')

        Returns:
            HTML string with name and Weblate link
        """
        name = self.get_language_module().native_locale_names.get(locale_code, locale_code)
        url = WEBLATE_URL_TEMPLATE % locale_code
        return f'<a href="{url}">{name}</a>'


def get_po_files_in_range(repo_path: str, commit_range: str) -> List[str]:
    """Get list of .po files that were modified in the commit range.

    Args:
        repo_path: Path to the git repository
        commit_range: Git commit range (e.g., 'v5.0.0...v5.0.2')

    Returns:
        List of modified .po file paths

    Raises:
        SystemExit: If git command fails
    """
    try:
        result = subprocess.run(
            ['git', 'diff', '--name-only', commit_range, '--', 'po/*.po'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        files = [f for f in result.stdout.strip().split('\n') if f]
        return files
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Error getting changed files: {e}\n")
        sys.exit(1)


def get_locale_from_filename(filename: str) -> Optional[str]:
    """Extract locale code from .po filename.

    Args:
        filename: Path to .po file

    Returns:
        Locale code or None if not a .po file

    Example:
        >>> get_locale_from_filename('po/de.po')
        'de'
    """
    basename = os.path.basename(filename)
    if basename.endswith('.po'):
        return basename[:-3]
    return None


def is_new_language(repo_path: str, commit_range: str, po_file: str) -> bool:
    """Check if this is a new language added in this range.

    Args:
        repo_path: Path to the git repository
        commit_range: Git commit range
        po_file: Path to the .po file

    Returns:
        True if the language is new in this range, False otherwise
    """
    try:
        # Check if file exists in the first commit of the range
        start_commit = commit_range.split('...')[0]
        result = subprocess.run(
            ['git', 'cat-file', '-e', f'{start_commit}:{po_file}'],
            cwd=repo_path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False  # Don't raise exception on non-zero exit code
        )
        # If exit code is 0, file existed; if non-zero, it didn't exist
        return result.returncode != 0
    except Exception as e:
        print(f"Error checking if {po_file} is new: {e}", file=sys.stderr)
        return False


def count_msgstr_changes(repo_path: str, commit_range: str, po_file: str) -> int:
    """Count non-empty msgstr changes in a .po file.

    Args:
        repo_path: Path to the git repository
        commit_range: Git commit range
        po_file: Path to the .po file

    Returns:
        Number of non-empty msgstr changes
    """
    try:
        result = subprocess.run(
            ['git', 'diff', commit_range, '--', po_file],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        diff_output = result.stdout
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Error getting diff for {po_file}: {e}\n")
        return 0

    return _parse_msgstr_changes(diff_output)


def _parse_msgstr_changes(diff_output: str) -> int:
    """Parse git diff output to count msgstr changes.

    Args:
        diff_output: Git diff output text

    Returns:
        Number of non-empty msgstr changes
    """
    lines = diff_output.split('\n')
    count = 0
    i = 0

    while i < len(lines):
        line = lines[i]

        if line.startswith('+msgstr "') and not line.startswith('+++'):
            count += _handle_single_line_msgstr(line)
        elif line == '+msgstr ""':
            count += _handle_multiline_msgstr(lines, i)

        i += 1

    return count


def _handle_single_line_msgstr(line: str) -> int:
    """Handle single-line msgstr changes.

    Args:
        line: The diff line containing msgstr

    Returns:
        1 if msgstr has content, 0 otherwise
    """
    match = MSGSTR_PATTERN.match(line)
    if match and match.group(1):
        return 1
    return 0


def _handle_multiline_msgstr(lines: List[str], start_idx: int) -> int:
    """Handle multi-line msgstr changes.

    Args:
        lines: All diff lines
        start_idx: Starting index of the multiline msgstr

    Returns:
        1 if multiline msgstr has content, 0 otherwise
    """
    # Look ahead for continuation lines
    end_idx = min(start_idx + MAX_LOOKAHEAD_LINES, len(lines))

    for j in range(start_idx + 1, end_idx):
        if not lines[j].startswith('+'):
            break

        if lines[j] != '+""':
            content_match = MULTILINE_MSGSTR_PATTERN.match(lines[j])
            if content_match and content_match.group(1):
                return 1

    return 0

def display_summary(language_changes: Dict[str, int], new_languages: List[str], lang_manager: BleachbitLanguageManager) -> None:
    """Display summary of translation changes.

    Args:
        language_changes: Dictionary mapping locale codes to change counts
        new_languages: List of newly added locale codes
    """
    total_languages = len(language_changes)
    total_changes = sum(language_changes.values())

    if total_changes == 0 and not new_languages:
        print("No translation changes found in this range.")
        return

    summary_parts = []

    if total_changes > 0:
        summary_parts.append(_format_changes_summary(total_languages, total_changes))
        summary_parts.append(_format_top_languages(language_changes, lang_manager))

    if new_languages:
        summary_parts.append(_format_new_languages(new_languages, lang_manager))

    print(" ".join(summary_parts))


def _format_changes_summary(total_languages: int, total_changes: int) -> str:
    """Format the main changes summary.

    Args:
        total_languages: Number of languages with changes
        total_changes: Total number of changes

    Returns:
        Formatted summary string
    """
    lang_text = f"{total_languages} language{'s' if total_languages != 1 else ''}"
    verb_text = f"{'were' if total_languages != 1 else 'was'}"
    change_text = f"{total_changes} change{'s' if total_changes != 1 else ''}"

    return f"{lang_text} {verb_text} updated with {change_text}.\n"


def _format_top_languages(language_changes: Dict[str, int], lang_manager: BleachbitLanguageManager) -> str:
    """Format the top languages summary.

    Args:
        language_changes: Dictionary mapping locale codes to change counts

    Returns:
        Formatted top languages string or empty string if no changes
    """
    if not language_changes:
        return ""

    sorted_languages = sorted(
        language_changes.items(),
        key=lambda x: x[1],
        reverse=True
    )

    top_count = min(3, len(sorted_languages))
    top_langs = []

    for i in range(top_count):
        locale, count = sorted_languages[i]
        name = lang_manager.get_locale_name(locale)
        top_langs.append(f"{name} ({count})")

    if len(top_langs) == 1:
        return f"The most active was {top_langs[0]}\n"
    else:
        return f"The most active were {', '.join(top_langs[:-1])} and {top_langs[-1]}\n"


def _format_new_languages(new_languages: List[str], lang_manager: BleachbitLanguageManager) -> str:
    """Format the new languages summary.

    Args:
        new_languages: List of newly added locale codes

    Returns:
        Formatted new languages string
    """
    lang_plural = "s" if len(new_languages) > 1 else ""
    sorted_langs = sorted(new_languages)
    lang_names = [lang_manager.get_locale_name(lang) for lang in sorted_langs]

    return f"New language{lang_plural} added: {', '.join(lang_names)}\n"


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Summarize translation changes over a git commit range'
    )
    parser.add_argument(
        'commit_range',
        help='Git commit range (e.g., v5.0.0...v5.0.2)'
    )
    parser.add_argument(
        '--repo-path',
        required=True,
        help='Path to bleachbit repository'
    )

    args = parser.parse_args()

    repo_path = os.path.abspath(os.path.expanduser(args.repo_path))
    if not os.path.isdir(repo_path):
        sys.stderr.write(f"Repository path does not exist: {repo_path}\n")
        sys.exit(1)

    # Initialize language manager
    lang_manager = BleachbitLanguageManager(repo_path)

    # Get list of modified .po files
    po_files = get_po_files_in_range(repo_path, args.commit_range)

    if not po_files:
        print("No translation files were modified in this range.")
        return

    # Count changes per language and track new languages
    language_changes: Dict[str, int] = {}
    new_languages: List[str] = []

    for po_file in po_files:
        locale = get_locale_from_filename(po_file)
        if not locale:
            continue

        # Check if new language (regardless of whether it has changes)
        if is_new_language(repo_path, args.commit_range, po_file):
            new_languages.append(locale)

        # Count changes
        changes = count_msgstr_changes(repo_path, args.commit_range, po_file)
        if changes > 0:
            language_changes[locale] = changes

    display_summary(language_changes, new_languages, lang_manager)


class TestSummarizeTranslationChanges(unittest.TestCase):
    """Test summarize_translation_changes functionality."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up a temporary git repository for testing."""
        cls.test_dir = tempfile.mkdtemp(prefix='bleachbit-test-')
        os.chdir(cls.test_dir)

        # Initialize git repo
        subprocess.run(['git', 'init'], check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], check=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], check=True)
        subprocess.run(['git', 'config', 'commit.gpgsign', 'false'], check=True)  # Disable GPG signing

        # Create initial commit
        os.makedirs('po', exist_ok=True)
        with open('po/.gitkeep', 'w', encoding='utf-8'):
            pass
        subprocess.run(['git', 'add', 'po/.gitkeep'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], check=True)

        # Create test files in a feature branch
        subprocess.run(['git', 'checkout', '-b', 'test-branch'], check=True)

        # Add some .po files
        po_files = {
            'po/en_GB.po': 'msgid "test"\nmsgstr "test"',
            'po/el.po': 'msgid "test"\nmsgstr "δοκιμή"',
            'po/de.po': 'msgid "test"\nmsgstr "Test"',
            'po/si.po': 'msgid "test"\nmsgstr "පරීක්ෂාව"'  # Sinhala
        }

        for filename, content in po_files.items():
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            subprocess.run(['git', 'add', filename], check=True)

        # First commit with multiple files
        subprocess.run(['git', 'commit', '-m', 'Add initial translations'], check=True)

        # Make some changes for second commit
        with open('po/el.po', 'a', encoding='utf-8') as f:
            f.write('\nmsgid "new"\nmsgstr "νέο"')
        with open('po/de.po', 'a', encoding='utf-8') as f:
            f.write('\nmsgid "new"\nmsgstr "neu"')

        # Create a third commit with more changes
        for i in range(18):  # 18 changes as per test case
            with open('po/de.po', 'a') as f:
                f.write(f'\nmsgid "new_{i}"\nmsgstr "neu_{i}"')

        subprocess.run(['git', 'add', 'po/de.po', 'po/el.po'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Update translations'], check=True)

        # Get the commit hashes for testing
        result = subprocess.run(
            ['git', 'log', '--pretty=format:%H'],
            capture_output=True, text=True, check=True
        )
        commits = result.stdout.strip().split('\n')
        cls.commit1 = commits[1]  # First commit with initial files
        cls.commit2 = commits[0]  # Most recent commit with changes

        # Create a tag for version testing
        subprocess.run(['git', 'tag', 'v5.0.0', cls.commit1], check=True)
        subprocess.run(['git', 'tag', 'v5.0.1', cls.commit2], check=True)

        # Create a new .po file that doesn't exist in the first commit
        # but is added in the second commit for testing is_new_language
        cls.new_po_file = 'po/fr.po'
        with open(cls.new_po_file, 'w', encoding='utf-8') as f:
            f.write('msgid "test"\nmsgstr "test"')
        subprocess.run(['git', 'add', cls.new_po_file], check=True)
        subprocess.run(['git', 'commit', '-m', 'Add French translation'], check=True)
        cls.commit3 = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True, text=True, check=True
        ).stdout.strip()

    def test_get_po_files_in_range(self) -> None:
        """Test getting PO files in a commit range."""
        files = get_po_files_in_range(
            self.test_dir,
            f'{self.commit1}...{self.commit2}'
        )
        self.assertEqual(
            sorted(files),
            ['po/de.po', 'po/el.po']
        )

    def test_is_new_language(self) -> None:
        """Test detecting new languages in a version range."""
        # si.po was added in the initial commit, so it should NOT be detected as new
        # (it exists in the starting commit of the range)
        self.assertFalse(
            is_new_language(
                self.test_dir,
                'v5.0.0...v5.0.1',
                'po/si.po'
            )
        )

        # Test with the new file created in setUpClass
        self.assertTrue(
            is_new_language(
                self.test_dir,
                f'{self.commit2}...{self.commit3}',
                self.new_po_file
            )
        )

    def test_count_msgstr_changes(self) -> None:
        """Test counting msgstr changes in a commit."""
        # Count changes in de.po (should be 20: 1 from the first update + 18 from the loop + 1 from the initial add)
        count = count_msgstr_changes(
            self.test_dir,
            f'{self.commit1}...{self.commit2}',
            'po/de.po'
        )
        self.assertEqual(count, 20)

        # el.po should have 2 changes (1 from the initial add, 1 from the update)
        count = count_msgstr_changes(
            self.test_dir,
            f'{self.commit1}...{self.commit2}',
            'po/el.po'
        )
        self.assertEqual(count, 2)

    @classmethod
    def tearDownClass(cls) -> None:
        """Clean up the temporary directory."""
        shutil.rmtree(cls.test_dir, ignore_errors=True)


if __name__ == '__main__':
    main()
