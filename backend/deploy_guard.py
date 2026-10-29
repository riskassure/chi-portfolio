"""Deploy guard: website code is published only from a clean, up-to-date main.

Options 14 and 15 call check() before reading anything from the live site, and
option 5 calls it again just before publishing. It refuses unless

- the laptop folder is on the main branch,
- main matches GitHub's main exactly (fetched first; nothing behind or ahead),
- no tracked file has uncommitted changes, and
- every selected file is tracked by git.

Content files that the local admin pages write (saved map places, gallery
display settings, gallery images) are data, not code: they are published first
and committed afterwards, so their uncommitted changes never block, and a
selection made only of them skips the guard. See
docs/administration/deployment/DEPLOY_GUARD.md.
"""
import re
import subprocess

# Files the live site, or a helper option, rewrites as content rather than code.
CONTENT_FILES = re.compile(r'frontend/(?:images/photography/.+|geography/places-data\.js|photography/gallery-settings\.js)')
SHOWN = 10


def git(root, *args):
    try:
        return subprocess.run(['git', '-C', str(root), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              check=False, timeout=120)
    except FileNotFoundError:
        raise ValueError('git was not found. Install Git for Windows (or open a terminal where "git --version" works) and try again.')
    except subprocess.TimeoutExpired:
        raise ValueError('git took more than two minutes (git ' + ' '.join(args) + '). Check the internet connection and try again.')


def output(root, *args):
    result = git(root, *args)
    if result.returncode:
        raise ValueError('git ' + ' '.join(args) + ' failed: ' + result.stderr.decode('utf-8', 'replace').strip())
    return result.stdout.decode('utf-8', 'replace')


def listing(paths):
    shown = ['  ' + path for path in paths[:SHOWN]]
    if len(paths) > SHOWN:
        shown.append(f'  ...and {len(paths) - SHOWN} more')
    return '\n'.join(shown)


def changed_files(root):
    """Tracked paths with uncommitted changes, from git status. Untracked files that
    were not selected are never published, so they do not count."""
    fields = output(root, 'status', '--porcelain=v1', '-z', '-uall').split('\0')
    tracked = []
    i = 0
    while i < len(fields):
        entry = fields[i]
        i += 1
        if not entry:
            continue
        code, path = entry[:2], entry[3:]
        if code not in ('??', '!!'):
            tracked.append(path)
            if 'R' in code or 'C' in code:
                i += 1  # -z puts a rename's original path in the next field
    return tracked


def check(root, paths, fetch=True):
    """Return the main commit the selected files come from, or None for a content-only selection.

    paths are repository-relative (frontend/... for option 14). Raises
    ValueError with the fix when the folder is not a clean, up-to-date main.
    """
    paths = [path.replace('\\', '/').strip('/') for path in paths]
    if all(CONTENT_FILES.fullmatch(path) for path in paths):
        return None
    head = 'Deploy guard: website code is published only from a clean main that matches GitHub.\n'
    if git(root, 'rev-parse', '--is-inside-work-tree').returncode:
        raise ValueError(head + f'{root} is not a git folder, so the guard cannot tell what you would publish.')
    branch = output(root, 'rev-parse', '--abbrev-ref', 'HEAD').strip()
    if branch != 'main':
        raise ValueError(head + f'This folder is on "{branch}", not main. Fix: git switch main, then git pull, then prepare again.')
    if fetch:
        print('Checking that main matches GitHub (git fetch; changes nothing in your files)...', flush=True)
        result = git(root, 'fetch', '--quiet', 'origin', 'main')
        if result.returncode:
            raise ValueError(head + 'Could not reach GitHub to confirm main is up to date: '
                             + result.stderr.decode('utf-8', 'replace').strip() + '\nCheck the internet connection and try again.')
    ahead, behind = (int(count) for count in output(root, 'rev-list', '--left-right', '--count', 'HEAD...origin/main').split())
    if ahead and behind:
        raise ValueError(head + f'Your main and GitHub\'s main have split ({ahead} commit(s) only here, {behind} only on GitHub). '
                         'Do not publish until they are reconciled; ask Claude in the project to sort it out.')
    if behind:
        raise ValueError(head + f'GitHub\'s main has {behind} commit(s) this folder does not have yet. Fix: git pull, then prepare again.')
    if ahead:
        raise ValueError(head + f'This folder has {ahead} commit(s) on main that are not on GitHub. '
                         'Fix: git push (or move them to a pull request and merge it, then git pull), then prepare again.')
    tracked = [path for path in changed_files(root) if not CONTENT_FILES.fullmatch(path)]
    if tracked:
        raise ValueError(head + 'These files have changes that are not committed:\n' + listing(tracked) + '\n'
                         'Fix: get the change into main on GitHub (commit and push, or a pull request), then git pull. '
                         'To throw a local change away instead: git restore <file>. Then prepare again.')
    known = set(output(root, 'ls-files', '-z', '--', *paths).split('\0'))
    missing = [path for path in paths if path not in known and not CONTENT_FILES.fullmatch(path)]
    if missing:
        raise ValueError(head + 'These selected files are not in git, so they are not part of main:\n' + listing(missing) + '\n'
                         'Fix: commit them to main on GitHub first, then git pull, then prepare again.')
    return output(root, 'rev-parse', 'HEAD').strip()
