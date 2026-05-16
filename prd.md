# PRD: Video-Slice-TUI Optimizations & Optional GUI

## Problem Statement
The Video-Slice-TUI project requires hardening of its existing TUI implementation and the addition of a mirrored GUI for users who prefer a graphical interface over the terminal. Both interfaces must share the same core video-processing logic.

## Scope and Non-goals
### In Scope
- **TUI Optimizations**: Fix `arranque.sh`, preference validation, and path resolution bugs.
- **Optional GUI**: Implement a desktop GUI that replicates Clipper, Splitter, and Merger functionality.
- **Unified Logic**: Ensure both TUI and GUI consume `src/logic/`.
- **CLI Mode Toggle**: Add a `--gui` flag to switch between interfaces.

### Non-goals
- Adding new FFmpeg features not currently present in the TUI.
- Web or cloud-based implementations.
- Refactoring `src/logic/` unless required for GUI compatibility.

## Acceptance Criteria
- [ ] `arranque.sh`: Uses `exec` to run Python and is guaranteed executable.
- [ ] `preferences.py`: `set_last_media_dir` validates that the path is a valid directory.
- [ ] `HubScreen`: Resolves file dialog paths using absolute directory names.
- [ ] `main.py`: Supports `--gui` flag to launch the GUI.
- [ ] GUI:
    - Built using `CustomTkinter` for a modern aesthetic.
    - Mirrors the Tabbed interface of the TUI.
    - Implements Hub, Clipper, Splitter, and Merger screens.
    - Correctly invokes `src/logic/` functions for FFmpeg operations.
- [ ] Requirements: `requirements.txt` updated with GUI dependencies.

## Constraints and Dependencies
- **OS**: Linux (primary), should be cross-platform compatible.
- **Dependencies**: FFmpeg (external), Textual (TUI), CustomTkinter (GUI).
- **Python**: 3.10+.

## Handoff Checklist
- [ ] PRD reviewed and approved.
- [ ] Taskboard initialized with identified tasks.
- [ ] Baseline codebase verified for integration.

---

# Initial Task List for Planner

## Phase 1: Optimizations
1. **Fix `arranque.sh`**: Add `exec` and ensure permissions.
2. **Harden `preferences.py`**: Add `os.path.isdir` check to `set_last_media_dir`.
3. **Fix `HubScreen` path resolution**: Ensure `abspath` is used in file dialog handlers.

## Phase 2: GUI Foundation
4. **Update `requirements.txt`**: Add `customtkinter`.
5. **CLI Toggle**: Update `src/main.py` to support `--gui` flag and route to `VideoSliceGUIApp`.
6. **GUI App Skeleton**: Create `src/ui/gui/app.py` with tabbed navigation.

## Phase 3: GUI Screens Implementation
7. **Hub Screen**: Implement shared video/export path selection.
8. **Clipper Screen**: Mirror TUI Clipper (Time inputs, Export).
9. **Splitter Screen**: Mirror TUI Splitter (Segments/Parts).
10. **Merger Screen**: Mirror TUI Merger (Video list management).

## Phase 4: Verification
11. **E2E Testing**: Verify both TUI and GUI perform FFmpeg operations correctly.
12. **UI Polishing**: Ensure GUI theme matches TUI "Sleek" aesthetic.
