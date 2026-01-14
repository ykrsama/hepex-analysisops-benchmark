from __future__ import annotations

from typing import Any, Protocol
from pathlib import Path
import os
import urllib.request
from tqdm import tqdm
import urllib.request
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
DEFAULT_BASE_DIR = os.getenv("HEPEX_DATA_DIR", "./data")

import atlasopenmagic as atom


class DataTaskLike(Protocol):
    release: str
    dataset: str
    skim: str
    protocol: str        # e.g. "https"
    cache: bool          # kept for compatibility, not relied on for download logic
    max_files: int


def _extract_https_url(u: str) -> str:
    """
    atlasopenmagic get_urls may return strings like:
      "simplecache::https://opendata.cern.ch/eos/path/to/file.root"
      "root::https://..."
    We only want the actual URL part.
    """
    return u.split("::", 1)[1] if "::" in u else u

def _default_data_dir(base_dir: str | Path, task: DataTaskLike) -> Path:
    """
    Default folder layout:
      <base_dir>/<release>/<dataset>/<skim>/
    """
    return Path(base_dir).expanduser().resolve() / task.release / task.dataset / task.skim

def _download_with_progress(url: str, target_path: Path, chunk_size: int = 1024 * 1024):
    """
    Download a file with a tqdm progress bar.
    """
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        total_size = response.length  # may be None
        with open(target_path, "wb") as f, tqdm(
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc=target_path.name,
            leave=True,
        ) as pbar:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                pbar.update(len(chunk))

def ensure_data_downloaded(
    task: DataTaskLike,
    base_dir: str | Path | None = None,
) -> dict[str, Any]:
    """
    Ensure data files exist locally under:
      <base_dir>/<release>/<dataset>/<skim>/

    Download missing files via HTTPS and return metadata.

    Returns:
      - data_dir: folder used to store files
      - local_paths: list of local file paths
      - downloaded: newly downloaded paths
      - skipped_existing: already-present paths
    """
    if base_dir is None:
        base_dir = DEFAULT_BASE_DIR

    atom.set_release(task.release)

    data_dir = _default_data_dir(base_dir, task)
    data_dir.mkdir(parents=True, exist_ok=True)

    raw_urls = atom.get_urls(
        task.dataset,
        task.skim,
        protocol=task.protocol,
        cache=False,  # we do download-if-missing ourselves
    )

    urls_sorted = sorted(raw_urls)
    if getattr(task, "max_files", 0) and task.max_files > 0:
        urls_sorted = urls_sorted[: task.max_files]

    remote_urls = [_extract_https_url(u) for u in urls_sorted]

    local_paths: list[str] = []
    downloaded: list[str] = []
    skipped_existing: list[str] = []

    for url in remote_urls:
        filename = os.path.basename(url)
        if not filename:
            raise ValueError(f"Cannot infer filename from URL: {url}")

        target_path = data_dir / filename

        if target_path.exists() and target_path.stat().st_size > 0:
            skipped_existing.append(str(target_path))
            local_paths.append(str(target_path))
            continue

        print(f"Downloading {url}")
        _download_with_progress(url, target_path)

        downloaded.append(str(target_path))
        local_paths.append(str(target_path))

    return {
        "release": task.release,
        "dataset": task.dataset,
        "skim": task.skim,
        "protocol": task.protocol,
        "base_dir": str(Path(base_dir).expanduser().resolve()),
        "data_dir": str(data_dir),
        "n_files": len(local_paths),
        "local_paths": local_paths,
        "downloaded": downloaded,
        "skipped_existing": skipped_existing,
        "raw_urls": urls_sorted,
        "remote_urls": remote_urls,
    }


def test_ensure_data_downloaded():
    class MockTask:
        release = "2025e-13tev-beta"
        dataset = "data"
        skim = "2muons"
        protocol = "https"
        max_files = 1

    task = MockTask()
    info = ensure_data_downloaded(task, base_dir=DEFAULT_BASE_DIR)

    assert info["n_files"] <= task.max_files
    assert Path(info["data_dir"]).exists()
    for p in info["local_paths"]:
        assert Path(p).exists()
        assert Path(p).stat().st_size > 0

    # check layered layout
    expected_dir = Path(DEFAULT_BASE_DIR).resolve() / task.release / task.dataset / task.skim
    assert Path(info["data_dir"]) == expected_dir


if __name__ == "__main__":
    test_ensure_data_downloaded()