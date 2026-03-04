# Soundmaze Story Schema — v2

**Version:** 2.0  
**Status:** Canonical  
**Replaces:** v1 (inline content objects inside waypoint array)

---

## Overview

A Soundmaze story file is a JSON document describing a branching audio narrative. The schema separates **content** (what is narrated and heard) from **structure** (how the story tree is traversed), enabling multiple tree nodes to share the same scene.

---

## Design Principles

### Content ≠ Structure
Content blocks and waypoints are separate collections. A waypoint references a content block by ID; it does not embed the content. This allows two different waypoints to point at the same scene — the "convergent path" pattern.

### Fully Unfolded Tree
The `waypoints` array always describes a **pure tree** — every node has exactly one parent (except the root). There are no back-edges, no runtime conditions, and no flags evaluated during playback. If two narrative paths converge on the same scene, the story author creates **two distinct waypoint objects** that share a single `content_id`. Conditions (locked doors, sacrifices, echo flags) are resolved at **story generation time** by an extraction/compilation script, not at runtime by the player app.

### Schema Version
The top-level `schema_version` field lets the loader detect and handle format evolution.

---

## Top-Level Structure

```json
{
  "schema_version": "2.0",
  "name": "...",
  "description": "...",
  "start_waypoint_id": 1,
  "content": [ ... ],
  "waypoints": [ ... ]
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `schema_version` | string | yes | Format version. Currently `"2.0"`. |
| `name` | string | yes | Display title of the story. |
| `description` | string | yes | Short synopsis shown in the library. |
| `start_waypoint_id` | int or string | yes | ID of the root waypoint (entry point). |
| `content` | array | yes | Content blocks. Order is irrelevant. |
| `waypoints` | array | yes | Tree nodes. Order is irrelevant. |

---

## Content Block

```json
{
  "id": "c1",
  "narration": "You stand at the entrance of an ancient forest...",
  "sound_note": "wp1-forest-entrance.mp3"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | yes | Unique identifier. Convention: `"c1"`, `"c2"`, … or a readable slug. |
| `narration` | string | yes | The text that is narrated (TTS source or script for voice actor). |
| `sound_note` | string | no | Filename or free-text description of ambient audio to play alongside narration. May be a `.mp3` reference, a cue label, or empty. |

**Future fields (reserved, not yet used):**
- `voice_id` — narrator voice override
- `narration_audio` — direct audio file URL for pre-recorded narration
- `tags` — array of strings for content categorisation

---

## Waypoint

```json
{
  "id": 1,
  "content_id": "c1",
  "options": [
    { "destination_id": 2, "link_text": "Take the dark path into the ancient oaks" },
    { "destination_id": 3, "link_text": "Follow the sunlit path toward the meadow" }
  ]
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | int or string | yes | Unique identifier within the waypoints array. |
| `content_id` | string | yes | References a content block by its `id`. Multiple waypoints may share the same `content_id`. |
| `options` | array | yes | Available choices after this waypoint. Empty array `[]` for leaf nodes (endings). |

### Option Object

| Field | Type | Required | Description |
|---|---|---|---|
| `destination_id` | int or string | yes | `id` of the target waypoint. Must exist in the waypoints array. |
| `link_text` | string | yes | Short label for the choice (shown/read to the player). |

---

## Convergent Paths — Pattern Example

When two narrative paths reach the same scene, create two waypoint objects sharing a `content_id`:

```json
"waypoints": [
  { "id": 5, "content_id": "c5", "options": [ ... ] },
  { "id": 6, "content_id": "c5", "options": [ ... ] }
]
```

Both `w5` and `w6` will play the same narration (from `c5`), but they occupy different positions in the tree and may have different children if the paths diverge again afterward. If they converge again at a descendant scene, that scene is also split into two waypoint objects sharing a `content_id`.

---

## Validation Rules

A valid v2 story file must satisfy:

1. Every `content_id` in `waypoints` refers to an `id` that exists in `content`.
2. Every `destination_id` in `options` refers to an `id` that exists in `waypoints`.
3. `start_waypoint_id` refers to an `id` that exists in `waypoints`.
4. The waypoints array forms a valid tree rooted at `start_waypoint_id` (no cycles, every non-root node reachable from root).
5. All `id` values within `content` are unique. All `id` values within `waypoints` are unique.

---

## Migration from v1

In v1, each waypoint embedded its content inline:

```json
{
  "id": 1,
  "start": true,
  "content": { "type": "text", "data": "...", "audio": "..." },
  "options": [ { "destinationWaypoint_id": 2, "linkText": "..." } ]
}
```

Migration steps:

1. Extract all `content` objects into the top-level `content` array, assigning each a unique `id`.
2. Replace inline `content` with `content_id` on each waypoint.
3. Detect convergence points (waypoints reachable from more than one parent). For each convergence point, duplicate the subtree rooted there, assigning new waypoint IDs. Shared subtree nodes reference the same `content_id` values.
4. Rename option field `destinationWaypoint_id` → `destination_id` and `linkText` → `link_text`.
5. Remove the `start: bool` field from waypoints; use top-level `start_waypoint_id` instead.
6. Add `"schema_version": "2.0"` at the top level.
7. Map `content.data` → `narration` and `content.audio` → `sound_note`.

---

## Changelog

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2019 | Initial schema. Inline content, `start: bool` on waypoints, `destinationWaypoint_id`/`linkText`. |
| 2.0 | 2025-03 | Decoupled content blocks. Added `start_waypoint_id`. Fully unfolded tree. Renamed option fields. Added `schema_version`. |
