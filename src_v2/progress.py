#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
progress - Progress management and state tracking
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class VolumeStatus(Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ChapterStatus(Enum):
    PLANNED = "planned"
    OUTLINING = "outlining"
    WRITING = "writing"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    ARCHIVED = "archived"


def load_yaml(path: Path) -> Optional[Dict[str, Any]]:
    """Load YAML file, with JSON fallback"""
    import json
    try:
        import yaml
        use_yaml = True
    except ImportError:
        use_yaml = False

    if not path.exists():
        return None

    with open(path, 'r', encoding='utf-8') as f:
        if use_yaml:
            try:
                return yaml.safe_load(f) or {}
            except:
                pass
        # Try JSON fallback
        try:
            f.seek(0)
            return json.load(f)
        except:
            return None


def save_yaml(path: Path, data: Dict[str, Any]) -> None:
    """Save YAML file, with JSON fallback"""
    import json
    try:
        import yaml
        use_yaml = True
    except ImportError:
        use_yaml = False

    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', encoding='utf-8') as f:
        if use_yaml:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)
        else:
            json.dump(data, f, ensure_ascii=False, indent=2)


def get_progress_path(process_dir: Path) -> Path:
    """Get progress file path"""
    return process_dir / 'progress.yaml'


def init_progress() -> Dict[str, Any]:
    """Initialize empty progress structure"""
    return {
        'volumes': {},
        'chapters': {},
        'updated_at': datetime.now().isoformat(),
    }


def load_progress(process_dir: Path) -> Dict[str, Any]:
    """Load progress, create if doesn't exist"""
    path = get_progress_path(process_dir)
    if path.exists():
        return load_yaml(path) or init_progress()
    return init_progress()


def save_progress(process_dir: Path, progress: Dict[str, Any]) -> None:
    """Save progress"""
    progress['updated_at'] = datetime.now().isoformat()
    save_yaml(get_progress_path(process_dir), progress)


def set_volume_status(
    progress: Dict[str, Any],
    volume_num: int,
    status: VolumeStatus,
    chapters_total: Optional[int] = None,
) -> Dict[str, Any]:
    """Set volume status"""
    vol_key = str(volume_num)
    if 'volumes' not in progress:
        progress['volumes'] = {}
    if vol_key not in progress['volumes']:
        progress['volumes'][vol_key] = {}

    progress['volumes'][vol_key]['status'] = status.value
    if chapters_total:
        progress['volumes'][vol_key]['chapters_total'] = chapters_total

    return progress


def set_chapter_status(
    progress: Dict[str, Any],
    chapter_num: int,
    status: ChapterStatus,
    volume_num: Optional[int] = None,
    progress_pct: Optional[int] = None,
    last_scene: Optional[int] = None,
    last_position: Optional[str] = None,
) -> Dict[str, Any]:
    """Set chapter status"""
    ch_key = str(chapter_num)
    if 'chapters' not in progress:
        progress['chapters'] = {}
    if ch_key not in progress['chapters']:
        progress['chapters'][ch_key] = {}

    progress['chapters'][ch_key]['status'] = status.value
    progress['chapters'][ch_key]['updated_at'] = datetime.now().isoformat()

    if volume_num:
        progress['chapters'][ch_key]['volume'] = volume_num
    if progress_pct is not None:
        progress['chapters'][ch_key]['progress'] = progress_pct
    if last_scene:
        progress['chapters'][ch_key]['last_scene'] = last_scene
    if last_position:
        progress['chapters'][ch_key]['last_position'] = last_position

    if status == ChapterStatus.COMPLETED:
        progress['chapters'][ch_key]['completed_at'] = datetime.now().isoformat()

    return progress


def get_volume_status(progress: Dict[str, Any], volume_num: int) -> Optional[VolumeStatus]:
    """Get volume status"""
    vol_key = str(volume_num)
    vol_data = progress.get('volumes', {}).get(vol_key, {})
    status_str = vol_data.get('status')
    if status_str:
        return VolumeStatus(status_str)
    return None


def get_chapter_status(progress: Dict[str, Any], chapter_num: int) -> Optional[ChapterStatus]:
    """Get chapter status"""
    ch_key = str(chapter_num)
    ch_data = progress.get('chapters', {}).get(ch_key, {})
    status_str = ch_data.get('status')
    if status_str:
        return ChapterStatus(status_str)
    return None


def get_completed_chapters(progress: Dict[str, Any]) -> List[int]:
    """Get list of completed chapter numbers"""
    completed = []
    for ch_key, ch_data in progress.get('chapters', {}).items():
        status = ch_data.get('status')
        if status in (ChapterStatus.COMPLETED.value, ChapterStatus.ARCHIVED.value):
            try:
                completed.append(int(ch_key))
            except ValueError:
                pass
    return sorted(completed)


def get_current_chapter(progress: Dict[str, Any]) -> int:
    """Get current chapter number"""
    # Find first non-completed chapter
    completed = get_completed_chapters(progress)
    if not completed:
        return 1
    return max(completed) + 1


def get_current_volume(progress: Dict[str, Any], structure: Dict[str, Any]) -> int:
    """Get current volume number using per-volume chapter config"""
    from .paths import get_volume_and_chapter
    current_ch = get_current_chapter(progress)
    vol_num, _ = get_volume_and_chapter(current_ch, structure)
    return vol_num


if __name__ == '__main__':
    # Test progress tracking
    prog = init_progress()
    prog = set_volume_status(prog, 1, VolumeStatus.IN_PROGRESS, 30)
    prog = set_chapter_status(prog, 1, ChapterStatus.WRITING, 1, progress_pct=50)
    print("Progress initialized")
