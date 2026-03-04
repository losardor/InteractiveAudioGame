#!/usr/bin/env python3
"""
md2soundmaze.py — Parse a Soundmaze story Markdown file into Soundmaze JSON format.

First stage of the content authoring pipeline:
    story.md → md2soundmaze.py → story.json → consistency_checker.py

Usage:
    python tools/md2soundmaze.py <input.md> [output.json]

If output.json is omitted, writes to the same directory as input with .json extension.

Dependencies: standard library only (re, json, sys, pathlib).
"""

import json
import re
import sys
from pathlib import Path


def strip_comments(text):
    """Remove HTML comments (single- and multi-line)."""
    return re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)


def parse_meta(lines):
    """Parse the ## Meta section into a dict of key-value pairs."""
    meta = {}
    key_map = {
        'Setting': 'setting',
        'Listener role': 'listener_role',
        'Central question': 'central_question',
        'Echo': 'echo',
    }
    for line in lines:
        m = re.match(r'\*\*(.+?):\*\*\s*(.*)', line)
        if m:
            key = m.group(1).strip()
            value = m.group(2).strip()
            json_key = key_map.get(key)
            if json_key:
                meta[json_key] = value
    return meta


def split_subsections(lines):
    """Split body lines by ### headers into {header: [lines]} ordered dict."""
    sections = {}
    order = []
    current = None
    for line in lines:
        m = re.match(r'^###\s+(.+)', line)
        if m:
            current = m.group(1).strip()
            sections[current] = []
            order.append(current)
        elif current is not None:
            sections[current].append(line)
    return sections, order


def collect_text(lines):
    """Join non-empty stripped lines with double newlines (paragraph breaks)."""
    parts = [line.strip() for line in lines if line.strip()]
    return '\n\n'.join(parts)


def parse_option(lines):
    """Parse an ### Option block's lines into a dict of fields."""
    opt = {}
    narration_parts = []
    in_narration = False

    for line in lines:
        m = re.match(r'\*\*(.+?):\*\*\s*(.*)', line)
        if m:
            key = m.group(1).strip()
            val = m.group(2).strip()
            if key == 'Label':
                in_narration = False
                opt['label'] = val
            elif key == 'Flag set':
                in_narration = False
                opt['flag_set'] = val
            elif key == 'Flag required':
                in_narration = False
                stripped = val.strip()
                if stripped.upper().startswith('NOT '):
                    opt['flag_required'] = stripped[4:].strip()
                    opt['flag_required_negated'] = True
                else:
                    opt['flag_required'] = stripped
                    opt['flag_required_negated'] = False
            elif key == 'Gates':
                in_narration = False
                opt['gates'] = [g.strip() for g in val.split(',')]
            elif key == 'Narration':
                in_narration = True
                if val:
                    narration_parts.append(val)
            elif key == 'Leads to':
                in_narration = False
                opt['leads_to'] = val
        elif in_narration and line.strip():
            narration_parts.append(line.strip())

    opt['narration'] = '\n\n'.join(narration_parts)
    return opt


def parse_file(path):
    """Parse the Markdown file and return (json_dict, stats_dict)."""
    text = Path(path).read_text(encoding='utf-8')
    text = strip_comments(text)

    # Extract title from # header
    title_match = re.search(r'^#\s+(.+)', text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else 'Untitled'

    # Split into ## sections
    meta = {}
    choices = []
    endings = []

    for section_text in re.split(r'^(?=##\s)', text, flags=re.MULTILINE):
        header_match = re.match(r'^##\s+(.+)', section_text)
        if not header_match:
            continue
        header = header_match.group(1).strip()
        body = section_text.split('\n')[1:]

        if header == 'Meta':
            meta = parse_meta(body)

        elif header.startswith('Choice '):
            subs, order = split_subsections(body)
            options = []
            for key in order:
                if key.startswith('Option '):
                    options.append(parse_option(subs[key]))
            choices.append({
                'label': header,
                'soundscape': collect_text(subs.get('Soundscape', [])),
                'narration': collect_text(subs.get('Narration', [])),
                'options': options,
            })

        elif header.startswith('Ending '):
            # Reached by appears before first ### subsection
            reached_by = None
            for line in body:
                if re.match(r'^###\s+', line):
                    break
                m = re.match(r'\*\*Reached by:\*\*\s*(.*)', line)
                if m:
                    reached_by = m.group(1).strip()
            subs, _ = split_subsections(body)
            endings.append({
                'label': header,
                'reached_by': reached_by,
                'soundscape': collect_text(subs.get('Soundscape', [])),
                'narration': collect_text(subs.get('Narration', [])),
                'final_sound': collect_text(subs.get('Final sound', [])),
            })

    # --- Assign IDs: choices 1..N, then endings N+1..N+M ---
    label_to_id = {}
    next_id = 1
    for c in choices:
        c['id'] = next_id
        label_to_id[c['label']] = next_id
        next_id += 1
    for e in endings:
        e['id'] = next_id
        label_to_id[e['label']] = next_id
        next_id += 1

    # --- Build waypoints ---
    errors = []
    flags_set = set()
    flags_required = set()
    waypoints = []

    for choice in choices:
        wp_options = []
        for opt in choice['options']:
            leads_to = opt.get('leads_to', '')
            dest_id = label_to_id.get(leads_to)
            if dest_id is None:
                errors.append(
                    f"Unresolved 'Leads to: {leads_to}' in option "
                    f"'{opt.get('label', '?')}' of {choice['label']}")
                dest_id = -1

            o = {
                'destinationWaypoint_id': dest_id,
                'linkText': opt.get('label', ''),
            }
            if opt.get('narration'):
                o['transition_text'] = opt['narration']
            if 'flag_set' in opt:
                o['flag_set'] = opt['flag_set']
                flags_set.add(opt['flag_set'].lower())
            if 'flag_required' in opt:
                o['flag_required'] = opt['flag_required']
                o['flag_required_negated'] = opt.get('flag_required_negated', False)
                if opt.get('flag_required_negated'):
                    flags_required.add('not ' + opt['flag_required'].lower())
                else:
                    flags_required.add(opt['flag_required'].lower())
            if 'gates' in opt:
                for gate in opt['gates']:
                    if gate not in label_to_id:
                        errors.append(
                            f"Gates reference '{gate}' not found in option "
                            f"'{opt.get('label', '?')}' of {choice['label']}")
                o['gates'] = opt['gates']
            wp_options.append(o)

        waypoints.append({
            'id': choice['id'],
            'start': choice['label'] == 'Choice 1',
            'label': choice['label'],
            'soundscape': choice['soundscape'],
            'content': {'type': 'text', 'data': choice['narration']},
            'options': wp_options,
        })

    for ending in endings:
        wp = {
            'id': ending['id'],
            'start': False,
            'label': ending['label'],
            'soundscape': ending['soundscape'],
            'content': {'type': 'text', 'data': ending['narration']},
            'options': [],
        }
        if ending['final_sound']:
            wp['final_sound'] = ending['final_sound']
        if ending['reached_by']:
            wp['reached_by'] = ending['reached_by']
        waypoints.append(wp)

    # --- Validation ---
    # 1. Unresolved leads_to — already collected above

    # 2. Flag required without corresponding flag set (warning only)
    #    Negated flags (e.g. "not echo") check that the base flag exists in flags_set
    for flag in sorted(flags_required):
        base_flag = flag[4:] if flag.startswith('not ') else flag
        if base_flag not in flags_set:
            print(f"Warning: Flag required '{flag}' references base flag "
                  f"'{base_flag}' which is never set by any Flag set")

    # 3. Gates targets exist — already collected above

    # 4. At least one start waypoint
    if not any(wp['start'] for wp in waypoints):
        errors.append("No waypoint has start=true")

    # 5. Every Choice has at least one option
    for choice in choices:
        if not choice['options']:
            errors.append(f"{choice['label']} has no options")

    # 6. Every Ending has no options (guaranteed by construction, but verify)
    for wp in waypoints:
        if wp['label'].startswith('Ending ') and wp['options']:
            errors.append(f"{wp['label']} has options but should be a leaf")

    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        sys.exit(1)

    # --- Assemble output ---
    result = {
        'name': title,
        'description': meta.get('central_question', ''),
        'meta': meta,
        'waypoints': waypoints,
    }

    all_flags = sorted(flags_set | flags_required)
    total_options = sum(len(c['options']) for c in choices)
    stats = {
        'title': title,
        'choices': len(choices),
        'endings': len(endings),
        'options': total_options,
        'flags': all_flags,
    }
    return result, stats


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/md2soundmaze.py <input.md> [output.json]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        output_path = input_path.with_suffix('.json')

    result, stats = parse_file(input_path)

    output_path.write_text(
        json.dumps(result, indent=4, ensure_ascii=False) + '\n',
        encoding='utf-8')

    print(f"Parsed: {stats['title']}")
    print(f"Choices:  {stats['choices']}")
    print(f"Endings:  {stats['endings']}")
    print(f"Options:  {stats['options']}")
    if stats['flags']:
        print(f"Flags:    {', '.join(stats['flags'])}")
    print(f"Output: {output_path}")


if __name__ == '__main__':
    main()
