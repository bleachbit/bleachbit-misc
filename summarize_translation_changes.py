#!/usr/bin/env python3
# vim: ts=4:sw=4:expandtab

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2025 to 2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

# Summarize translation changes over a git commit range

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


WEBLATE_TPL = 'https://hosted.weblate.org/projects/bleachbit/main/%s/'

dir_bb_root = os.path.abspath(os.path.expanduser('../bleachbit'))
sys.path.insert(0, dir_bb_root)

import bleachbit.Language


def get_locale_name(locale_code):
    """Convert locale code to human-readable name with Weblate link"""
    name = bleachbit.Language.native_locale_names.get(locale_code, locale_code)
    url = WEBLATE_TPL % locale_code
    return f'<a href="{url}">{name}</a>'


def get_po_files_in_range(repo_path, commit_range):
    """Get list of .po files that were modified in the commit range"""
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


def get_locale_from_filename(filename):
    """Extract locale code from .po filename

    Example: po/de.po -> de
    """
    basename = os.path.basename(filename)
    if basename.endswith('.po'):
        return basename[:-3]
    return None


def is_new_language(repo_path, commit_range, po_file):
    """Check if this is a new language added in this range"""
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


def count_msgstr_changes(repo_path, commit_range, po_file):
    """Count non-empty msgstr changes in a .po file"""
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

    count = 0
    lines = diff_output.split('\n')

    # Look for added/modified msgstr lines that are not empty
    # Pattern: +msgstr "something" where something is not empty
    for i, line in enumerate(lines):
        if line.startswith('+msgstr "') and not line.startswith('+++'):
            # Extract the string content
            match = re.match(r'\+msgstr\s+"(.*)"\s*$', line)
            if match:
                content = match.group(1)
                # Only count if content is non-empty
                if content:
                    count += 1
            else:
                # Handle multi-line msgstr
                # Check if it's msgstr "" followed by actual content
                if line == '+msgstr ""' or line.startswith('+msgstr ""\n'):
                    # Look ahead for continuation lines
                    has_content = False
                    for j in range(i + 1, min(i + 20, len(lines))):
                        if lines[j].startswith('+"') and lines[j] != '+""\n':
                            # Check if there's actual content
                            content_match = re.match(r'\+"(.+)"', lines[j])
                            if content_match and content_match.group(1):
                                has_content = True
                                break
                        elif not lines[j].startswith('+'):
                            break
                    if has_content:
                        count += 1
                else:
                    # It's a msgstr with content on the same line
                    count += 1

    return count

def display_summmary(language_changes, new_languages):
    """Display summary of translation changes"""
    total_languages = len(language_changes)
    total_changes = sum(language_changes.values())

    if total_changes == 0 and not new_languages:
        print("No translation changes found in this range.")
        return

    # Sort by change count
    sorted_languages = sorted(
        language_changes.items(),
        key=lambda x: x[1],
        reverse=True
    )

    summary_parts = []

    if total_changes > 0:
        summary = f"{total_languages} language{'s' if total_languages != 1 else ''} "
        summary += f"{'were' if total_languages != 1 else 'was'} updated with "
        summary += f"{total_changes} change{'s' if total_changes != 1 else ''}.\n"
        summary_parts.append(summary)

        if sorted_languages:
            # Show top languages
            top_count = min(3, len(sorted_languages))
            top_summary = "The most active were "
            top_langs = []
            for i in range(top_count):
                locale, count = sorted_languages[i]
                name = get_locale_name(locale)
                top_langs.append(f"{name} ({count})")
            top_summary += " and ".join(
                [', '.join(top_langs[:-1]), top_langs[-1]] if len(top_langs) > 1 else top_langs
            )
            top_summary += "\n"
            summary_parts.append(top_summary)

    if new_languages:
        new_lang_summary = "New language" + ("s" if len(new_languages) > 1 else "") + " added: "
        new_lang_summary += ", ".join([get_locale_name(lang) for lang in sorted(new_languages)])
        new_lang_summary += "\n"
        summary_parts.append(new_lang_summary)

    print(" ".join(summary_parts))


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Summarize translation changes over a git commit range'
    )
    parser.add_argument(
        'commit_range',
        help='Git commit range (e.g., v5.0.0...v5.0.2)'
    )
    parser.add_argument(
        '--repo-path',
        default=dir_bb_root,
        help=f'Path to bleachbit repository (default: {dir_bb_root})'
    )

    args = parser.parse_args()

    repo_path = os.path.abspath(os.path.expanduser(args.repo_path))
    if not os.path.isdir(repo_path):
        sys.stderr.write(f"Repository path does not exist: {repo_path}\n")
        sys.exit(1)

    # Get list of modified .po files
    po_files = get_po_files_in_range(repo_path, args.commit_range)

    if not po_files:
        print("No translation files were modified in this range.")
        return

    # Count changes per language and track new languages
    language_changes = {}
    new_languages = []

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

    display_summmary(language_changes, new_languages)


class TestSummarizeTranslationChanges(unittest.TestCase):
    """Test summarize_translation_changes"""

    @classmethod
    def setUpClass(cls):
        """Set up a temporary git repository for testing"""
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

    def test_get_po_files_in_range(self):
        """Test getting PO files in a commit range"""
        files = get_po_files_in_range(
            self.test_dir,
            f'{self.commit1}...{self.commit2}'
        )
        self.assertEqual(
            sorted(files),
            ['po/de.po', 'po/el.po']
        )

    def test_is_new_language(self):
        """Test detecting new languages in a version range"""
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

    def test_count_msgstr_changes(self):
        """Test counting msgstr changes in a commit"""
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
    def tearDownClass(cls):
        """Clean up the temporary directory"""
        shutil.rmtree(cls.test_dir, ignore_errors=True)


if __name__ == '__main__':
    main()
