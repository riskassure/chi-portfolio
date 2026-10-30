"""Record a finished option 20 batch in git (helper option 23).

After a batch is published, verified and brought home with option 8, this
writes its migration (math_entry_record.write_migration), proves it rebuilds
the batch exactly as your baseline holds it, and after you type COMMIT makes
one focused commit on its own branch, entries/<date>-<topic>, then pushes it so
you can open a pull request.

The git work happens in a separate checkout (a git worktree) under the batch's
folder, so your own folder, its branch and anything you have staged there are
never touched. Only the migration and its diagram SVGs are committed. The
topic and branch are saved in the batch manifest, so choosing 23 again after an
interruption reuses them, skips a commit already made and retries the push.
"""
import json
from pathlib import Path
import re
import sys

import batch_publish as bp
from deploy_guard import git, output
import website_workflow as w

sys.path.insert(0, str(Path(__file__).resolve().parent / 'src' / 'database' / 'math' / 'migrations'))
import math_entry_record as record  # noqa: E402

MIGRATIONS = 'backend/src/database/math/migrations'
TOPIC_RE = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')


def names(manifest, topic):
    """Return (branch, migration file name) for the batch and topic."""
    date = record.published_on(manifest)
    return (f'entries/{date.isoformat()}-{topic}',
            f'add_{topic.replace("-", "_")}_entries_{date.strftime("%Y%m%d")}.py')


def finished_batches():
    """Manifests of batches whose entries are all live, oldest first."""
    found = []
    for path in sorted(bp.BATCHES.glob('*/manifest.json')):
        manifest = json.loads(path.read_text(encoding='utf-8'))
        if manifest.get('publication') == 'complete':
            found.append(manifest)
    return found


def readiness(manifest, state):
    """Reasons the batch cannot be recorded yet (empty when it can)."""
    reasons = []
    if (manifest.get('verification') or {}).get('status') != 'verified':
        reasons.append('its live pages have not been recorded as checked (choose 20 and type VERIFIED)')
    if (manifest.get('synchronization') or {}).get('status') != 'complete':
        reasons.append('option 8 has not brought the batch home yet (choose 20 to run it)')
    if manifest.get('username') != state.get('username'):
        reasons.append('it belongs to a different PythonAnywhere account')
    return reasons


def pull_request_link(root, branch):
    url = output(root, 'remote', 'get-url', 'origin').strip()
    match = re.search(r'github\.com[:/]([^/]+)/(.+?)(?:\.git)?/?$', url)
    if not match:
        return None
    return f'https://github.com/{match.group(1)}/{match.group(2)}/compare/main...{branch}?expand=1'


def has(root, ref):
    return git(root, 'rev-parse', '--verify', '--quiet', ref).returncode == 0


def checkout(root, folder, branch):
    """Return a worktree at folder on branch, creating either as needed."""
    if folder.exists():
        if git(folder, 'rev-parse', '--is-inside-work-tree').returncode == 0 and \
                output(folder, 'rev-parse', '--abbrev-ref', 'HEAD').strip() == branch:
            return folder
        raise ValueError(f'{folder} exists but is not a checkout of {branch}. Delete that folder and choose 23 again.')
    output(root, 'worktree', 'prune')
    if has(root, 'refs/heads/' + branch):
        result = git(root, 'worktree', 'add', str(folder), branch)
    elif has(root, 'refs/remotes/origin/' + branch):
        result = git(root, 'worktree', 'add', '-b', branch, str(folder), 'origin/' + branch)
    else:
        result = git(root, 'worktree', 'add', '-b', branch, str(folder), 'origin/main')
    if result.returncode:
        raise ValueError(f'Could not make a separate checkout of {branch}: ' +
                         result.stderr.decode('utf-8', 'replace').strip() +
                         ('\nIf your own folder is on that branch, switch it back to main (git switch main) and choose 23 again.'
                          if 'already' in result.stderr.decode('utf-8', 'replace') else ''))
    return folder


def committed(folder, path):
    """The commit on the checkout's branch that added path, or None."""
    if git(folder, 'cat-file', '-e', 'HEAD:' + path).returncode:
        return None
    return output(folder, 'log', '-1', '--format=%H', '--', path).strip()


def run(state, ask=input):
    batches = finished_batches()
    if not batches:
        print('No finished batches. Publish one with option 20 first.')
        return
    print('Published batches:')
    for index, manifest in enumerate(batches, 1):
        saved = manifest.get('record') or {}
        status = {'pushed': 'recorded on ' + saved.get('branch', ''), 'committed': 'committed, not pushed yet'}.get(
            saved.get('state'), 'not recorded yet')
        print(f"{index}. \"{manifest['name']}\" ({manifest['batch_id']}), {len(manifest['order'])} entries: {status}")
    choice = ask('Batch number (blank cancels): ').strip()
    if not choice:
        return
    if not choice.isdigit() or not 1 <= int(choice) <= len(batches):
        raise ValueError('Invalid batch number.')
    manifest = batches[int(choice) - 1]
    with bp.locked(manifest):
        record_batch(bp.reload(manifest), state, ask)


def record_batch(manifest, state, ask=input, root=None):
    root = Path(root or w.ROOT)
    reasons = readiness(manifest, state)
    if reasons:
        raise ValueError('This batch cannot be recorded yet: ' + '; '.join(reasons) + '.')
    saved = manifest.get('record')
    if saved:
        print(f"Reusing this batch's record: topic {saved['topic']}, branch {saved['branch']}.")
    else:
        topic = ask('Topic for the branch and file name, lowercase words joined by hyphens '
                    f"(for example {manifest['name'].lower().replace(' ', '-')}): ").strip()
        if not TOPIC_RE.fullmatch(topic) or len(topic) > 40:
            raise ValueError('Use lowercase letters and digits, words joined by hyphens, at most 40 characters.')
        branch, migration = names(manifest, topic)
        saved = manifest['record'] = dict(topic=topic, branch=branch, migration=migration, state='planned')
        bp.save_manifest(manifest)
    branch, migration = saved['branch'], saved['migration']
    if saved['state'] == 'pushed':
        link = pull_request_link(root, branch)
        print(f'Already recorded and pushed on {branch}. If its pull request is not merged yet:' + (f'\n  {link}' if link else ''))
        return
    path = MIGRATIONS + '/' + migration
    assets = MIGRATIONS + '/' + record.ASSETS + '/' + Path(migration).stem
    print('Fetching main from GitHub (changes nothing in your folder)...', flush=True)
    result = git(root, 'fetch', '--quiet', 'origin', 'main')
    if result.returncode:
        raise ValueError('Could not reach GitHub: ' + result.stderr.decode('utf-8', 'replace').strip())
    git(root, 'fetch', '--quiet', 'origin', f'refs/heads/{branch}:refs/remotes/origin/{branch}')  # May not exist yet.
    if git(root, 'cat-file', '-e', 'origin/main:' + path).returncode == 0:
        raise ValueError(f'main already has {path}. Choose a different topic: delete the "record" '
                         f"section of {Path(manifest['folder']) / 'manifest.json'}, or ask Claude in the project.")
    folder = checkout(root, Path(manifest['folder']) / 'git', branch)
    commit = committed(folder, path)
    if commit:
        print(f'Already committed on {branch} ({commit[:10]}); skipping to the push.')
    else:
        target = folder / path
        for stale in [target, *sorted((folder / assets).glob('*'))]:
            stale.unlink(missing_ok=True)  # Left by an interrupted run; written again from the frozen packages.
        record.write_migration(target, manifest)
        print('Wrote', target)
        print(f"Checking it against your baseline ({state['base']}) on scratch copies...", flush=True)
        for line in record.check_record(record.load_entries(target), folder / assets, state['base']):
            print(line)
        print(f'Review {target} if you like. COMMIT makes one commit with only that file'
              + (' and its diagram SVGs' if (folder / assets).is_dir() else '') + f' on branch {branch}, then pushes it.')
        if ask('Type COMMIT to commit and push (anything else stops; nothing is committed): ').strip() != 'COMMIT':
            print('Stopped. Nothing was committed. Choose 23 again when ready.')
            return
        to_add = [path] + ([assets] if (folder / assets).is_dir() else [])
        output(folder, 'add', '--', *to_add)
        message = (f"Record the \"{manifest['name']}\" batch of math entries\n\n"
                   f"{len(manifest['order'])} entries published with helper option 20 on "
                   f"{record.published_on(manifest).isoformat()} (batch {manifest['batch_id']}).\n"
                   'Written and checked by helper option 23.')
        result = git(folder, 'commit', '--quiet', '-m', message, '--', *to_add)
        if result.returncode:
            raise ValueError('git commit failed: ' + result.stderr.decode('utf-8', 'replace').strip() +
                             '\nNothing was pushed. Fix the problem (for example set your name and email with '
                             'git config --global user.name / user.email) and choose 23 again.')
        commit = output(folder, 'rev-parse', 'HEAD').strip()
        print(f'Committed {commit[:10]} on {branch}.')
    manifest['record'].update(state='committed', commit=commit)
    bp.save_manifest(manifest)
    print('Pushing the branch to GitHub...', flush=True)
    result = git(folder, 'push', '--quiet', '-u', 'origin', branch)
    if result.returncode:
        raise ValueError('git push failed: ' + result.stderr.decode('utf-8', 'replace').strip() +
                         f'\nThe commit is saved on {branch}. Choose 23 again to retry the push.')
    manifest['record'].update(state='pushed')
    bp.save_manifest(manifest)
    git(root, 'worktree', 'remove', str(folder))
    link = pull_request_link(root, branch)
    print(f'Pushed {branch}.')
    print('Open a pull request, wait for the checks, and merge it, then git pull:' + (f'\n  {link}' if link else ''))
