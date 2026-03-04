#!/usr/bin/env python3
"""
consistency_checker.py — Check narrative consistency of Soundmaze story paths.

Second stage of the content authoring pipeline:
    story.md → md2soundmaze.py → story.json → consistency_checker.py → report.json

Usage:
    python tools/consistency_checker.py <input.json> [--dry-run]

Dependencies:
    anthropic   — async client (only imported when not in --dry-run mode)
    Standard library: json, asyncio, sys, pathlib, datetime, logging, argparse
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

CONSISTENCY_CHECK_SYSTEM_PROMPT = """\
You are a narrative consistency checker for branching audio stories.

You will be given the complete text of one linear path through a branching story
— the full experience of a single listener who made a specific sequence of choices.

Check this path for narrative inconsistencies. An inconsistency is anything that
would confuse or jar a listener on this specific path, for example:
- A character dying and then speaking or acting
- An object being lost, given away, or destroyed and then used
- A location or physical state changing without explanation
- A fact stated early that is contradicted later
- An emotional or psychological state that shifts without cause

For each inconsistency found, report:
  Location: approximate position in the narrative (quote a short phrase)
  Issue: one sentence describing the inconsistency
  Severity: minor or major

If no inconsistencies are found, respond with exactly: No inconsistencies found.
"""

logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger(__name__)


def enumerate_paths(waypoints):
    """
    Enumerate all valid root-to-leaf paths through the waypoint graph,
    respecting flag_required and gates constraints.

    Returns a list of paths. Each path is a list of step dicts:
        {"waypoint": <wp obj>, "choice_taken": <str or None>, "flag_set": <str or None>}
    """
    wp_by_id = {wp['id']: wp for wp in waypoints}
    start = next((wp for wp in waypoints if wp.get('start')), None)
    if start is None:
        log.error("No start waypoint found")
        return []

    paths = []

    def dfs(wp, path, flags, gates, visited):
        """
        wp:      current waypoint
        path:    list of step dicts built so far (including current wp)
        flags:   set of active flag names (lowercased)
        gates:   None (no constraint) or set of allowed ending labels
        visited: set of waypoint IDs on the current DFS stack
        """
        # Leaf node — check gates then record
        if not wp['options']:
            label = wp.get('label', '')
            if gates is not None and label not in gates:
                return  # ending not allowed by active gates
            paths.append(path)
            return

        for opt in wp['options']:
            # 1. Check flag_required
            flag_req = opt.get('flag_required')
            if flag_req:
                flag_req_lower = flag_req.lower()
                negated = opt.get('flag_required_negated', False)
                flag_is_set = flag_req_lower in flags
                if negated and flag_is_set:
                    continue   # option requires flag NOT set, but it is set
                if not negated and not flag_is_set:
                    continue   # option requires flag set, but it isn't

            dest_id = opt['destinationWaypoint_id']

            # Cycle detection
            if dest_id in visited:
                log.warning(
                    "Cycle detected: waypoint %d already in path, skipping",
                    dest_id)
                continue

            dest = wp_by_id.get(dest_id)
            if dest is None:
                log.warning(
                    "Destination waypoint %d not found, skipping", dest_id)
                continue

            # 2. Update flags
            new_flags = set(flags)
            flag_set_val = opt.get('flag_set')
            if flag_set_val:
                new_flags.add(flag_set_val.lower())

            # 3. Update gates (intersect narrows, never widens)
            new_gates = gates
            opt_gates = opt.get('gates')
            if opt_gates:
                opt_gates_set = set(opt_gates)
                if new_gates is None:
                    new_gates = opt_gates_set
                else:
                    new_gates = new_gates & opt_gates_set

            # Build step for destination waypoint
            next_step = {
                'waypoint': dest,
                'choice_taken': opt.get('linkText'),
                'flag_set': flag_set_val,
            }

            dfs(dest, path + [next_step], new_flags, new_gates,
                visited | {dest_id})

    # Kick off DFS from start
    start_step = {
        'waypoint': start,
        'choice_taken': None,
        'flag_set': None,
    }
    dfs(start, [start_step], set(), None, {start['id']})

    return paths


def build_path_summary(path):
    """Build a human-readable summary like:
    Choice 1 → 'Take the glen path' → Choice 2 → ... → Ending A
    """
    parts = []
    for i, step in enumerate(path):
        wp = step['waypoint']
        label = wp.get('label', 'Waypoint {}'.format(wp['id']))
        if i > 0 and step['choice_taken']:
            parts.append("'{}'".format(step['choice_taken']))
        parts.append(label)
    return ' \u2192 '.join(parts)


def assemble_narrative(path):
    """
    Assemble a linear narrative string from a path for consistency checking.
    """
    parts = []
    for i, step in enumerate(path):
        wp = step['waypoint']

        # Soundscape
        soundscape = wp.get('soundscape')
        if soundscape:
            parts.append('[Soundscape: {}]'.format(soundscape))

        # Content
        content = wp.get('content', {})
        if content.get('type') == 'text':
            data = content.get('data', '')
            if data:
                parts.append(data)
        else:
            ctype = content.get('type', 'unknown')
            parts.append('[Non-text content: {}]'.format(ctype))
            log.warning(
                'Non-text content type "%s" at waypoint %d', ctype, wp['id'])

        # Choice taken (shown after this waypoint's narration, before next)
        if i + 1 < len(path):
            next_choice = path[i + 1].get('choice_taken')
            if next_choice:
                parts.append('[Choice: "{}"]'.format(next_choice))

    return '\n\n'.join(parts)


async def check_path(client, semaphore, path_index, path, narrative):
    """Send a single path's narrative to the API for consistency checking."""
    summary = build_path_summary(path)
    async with semaphore:
        await asyncio.sleep(path_index * 2)  # stagger requests
        try:
            response = await client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                system=CONSISTENCY_CHECK_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": narrative}],
            )
            api_response = response.content[0].text
        except Exception as e:
            return {
                'path_index': path_index,
                'path_summary': summary,
                'narrative': narrative,
                'api_response': None,
                'error': str(e),
            }

    return {
        'path_index': path_index,
        'path_summary': summary,
        'narrative': narrative,
        'api_response': api_response,
        'error': None,
    }


async def main():
    parser = argparse.ArgumentParser(
        description='Check narrative consistency of Soundmaze story paths')
    parser.add_argument('input_json', help='Path to Soundmaze JSON file')
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Enumerate paths and print narratives without API calls')
    args = parser.parse_args()

    input_path = Path(args.input_json)
    data = json.loads(input_path.read_text(encoding='utf-8'))
    waypoints = data['waypoints']
    story_name = data.get('name', 'Unknown')

    # Enumerate paths
    paths = enumerate_paths(waypoints)
    print('Found {} paths:'.format(len(paths)))
    for i, path in enumerate(paths):
        print('  Path {}: {}'.format(i, build_path_summary(path)))

    # Dry run — print narratives and exit
    if args.dry_run:
        for i, path in enumerate(paths):
            narrative = assemble_narrative(path)
            print('\n--- Path {}: {} ---'.format(
                i, build_path_summary(path)))
            print(narrative)
        return

    # Import anthropic only when making API calls
    from anthropic import AsyncAnthropic
    client = AsyncAnthropic()

    # Run checks with concurrency limit to avoid rate limits
    semaphore = asyncio.Semaphore(2)
    narratives = [assemble_narrative(path) for path in paths]
    tasks = [
        check_path(client, semaphore, i, path, narrative)
        for i, (path, narrative) in enumerate(zip(paths, narratives))
    ]
    results = await asyncio.gather(*tasks)
    results = sorted(results, key=lambda r: r['path_index'])

    # Write report
    report = {
        'story': story_name,
        'checked_at': datetime.now(timezone.utc).isoformat(),
        'total_paths': len(paths),
        'results': results,
    }
    output_path = input_path.parent / (input_path.stem + '_consistency_report.json')
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + '\n',
        encoding='utf-8')
    print('\nReport written to: {}'.format(output_path))

    # Print human-readable summary
    print()
    for r in results:
        print('Path {}: {}'.format(r['path_index'], r['path_summary']))
        if r['error']:
            print('  \u2717 Error: {}'.format(r['error']))
        elif r['api_response'] and 'No inconsistencies found' in r['api_response']:
            print('  \u2713 No inconsistencies found.')
        else:
            # Print the raw API response indented
            for line in (r['api_response'] or '').split('\n'):
                print('  {}'.format(line))
        print()


if __name__ == '__main__':
    asyncio.run(main())
