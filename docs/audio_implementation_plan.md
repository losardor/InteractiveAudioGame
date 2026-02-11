# Soundmaze — Audio Playback Implementation Plan

## Pre-requisite: Merge Branch

Before starting, merge `modernize/flask-cli` into `master`:

```bash
cd /Users/losardo/Documents/Soundmaze/InteractiveAudioGame
git checkout master
git merge modernize/flask-cli
git push
git checkout -b feature/audio-playback
```

---

## Task Breakdown

### Task 1: Extend Data Model + Audio File Infrastructure
**Module:** books-core, infra  
**Goal:** Add audio fields to the content model, create the upload directory structure, and add a config setting for audio storage path.

**Changes:**
- Add `audio_url` (String, nullable) and `audio_duration` (Float, nullable) to `TextContent`
- Add `AUDIO_UPLOAD_DIR` to config (defaults to `app/static/audio/`)
- Create `app/static/audio/` directory with a `.gitkeep`
- Run `recreate-db` (no migrations infrastructure yet — acceptable for PoC)

**Verification:** App boots, existing book loading still works, new columns exist in DB.

---

### Task 2: Update JSON Loader to Support Audio References
**Module:** books-core  
**Goal:** Extend the JSON book format and loader to accept optional audio file references per waypoint.

---

### Task 3: Audio File Upload for Waypoints (Admin)
**Module:** books-core  
**Goal:** Allow uploading mp3 files per waypoint through the web UI.

---

### Task 4: Audio Player Page
**Module:** frontend, books-core  
**Goal:** Build a playback page where users hear the story and see choices when audio ends.

---

### Task 5: Browser TTS Fallback
**Module:** frontend  
**Goal:** If a waypoint has no audio file, use the browser's Web Speech API to read the text aloud.

---

See the full plan with Claude Code prompts in the downloadable file.
