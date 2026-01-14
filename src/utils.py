import os
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Optional
from .tasks.task_spec import TaskSpec
import atlasopenmagic as atom


@dataclass
class DownloadResult:
    url: str
    local_path: str
    ok: bool
    skipped: bool
    expected_size: Optional[int]
    local_size: int
    error: Optional[str] = None


# ----------------------------- # Helper: atlasopenmagic download # ----------------------------- 
def _get_local_paths_from_atlasopenmagic_urls(urls: list[str]) -> list[str]: 
    """ atlasopenmagic get_urls sometimes returns strings like: 
    "https::/path/to/local/file.root" (based on your earlier snippet using split('::')[1]) 
    This helper extracts the local path part robustly. """ 
    local_paths: list[str] = [] 
    for u in urls: 
        if "::" in u: 
            local_paths.append(u.split("::", 1)[1]) 
        else: 
            # Fallback: keep as-is (could already be local) 
            local_paths.append(u) 
    return local_paths

# -----------------------------
# Low-level HTTP helpers (urllib)
# -----------------------------
def _head_content_length(url: str, timeout: int = 30) -> Optional[int]:
    """
    Return Content-Length from HEAD if available, else None.
    """
    req = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        cl = resp.headers.get("Content-Length")
        if cl is None:
            return None
        try:
            return int(cl)
        except ValueError:
            return None


def _download_to_file(url: str, dst_path: str, timeout: int = 60, chunk_size: int = 1024 * 1024) -> int:
    """
    Download url to dst_path (overwrite). Returns bytes written.
    Uses streaming read to avoid urlretrieve pitfalls.
    """
    req = urllib.request.Request(url, method="GET")
    written = 0
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        with open(dst_path, "wb") as f:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                written += len(chunk)
    return written


def _ensure_one_file(
    url: str,
    output_dir: str,
    timeout_head: int = 30,
    timeout_get: int = 120,
    max_retries: int = 2,
    verbose: bool = True,
) -> DownloadResult:
    """
    Ensure a single file is present and complete (by Content-Length if available).
    """
    filename = os.path.basename(url)
    local_path = os.path.join(output_dir, filename)
    part_path = local_path + ".part"

    # Local size (if any)
    local_size = os.path.getsize(local_path) if os.path.exists(local_path) else 0

    # Expected size from HEAD (best effort)
    expected_size: Optional[int] = None
    try:
        expected_size = _head_content_length(url, timeout=timeout_head)
    except Exception:
        expected_size = None  # server may not support HEAD / transient issues

    # If we can validate size and it matches -> skip
    if expected_size is not None and os.path.exists(local_path) and local_size == expected_size:
        return DownloadResult(
            url=url,
            local_path=local_path,
            ok=True,
            skipped=True,
            expected_size=expected_size,
            local_size=local_size,
        )

    # If expected_size unknown, but file exists and nonzero, you can choose to trust it.
    # For safety in benchmark context, we *do not* trust it; we re-download unless you want otherwise.
    # You can change this policy if desired.
    # if expected_size is None and os.path.exists(local_path) and local_size > 0:
    #     return DownloadResult(... skipped=True ...)

    # Download with retries
    last_err: Optional[str] = None
    for attempt in range(max_retries + 1):
        try:
            # clean stale part
            if os.path.exists(part_path):
                try:
                    os.remove(part_path)
                except OSError:
                    pass

            if verbose:
                msg = f"[download] {filename}"
                if expected_size is not None:
                    msg += f" (expected {expected_size} bytes)"
                if os.path.exists(local_path):
                    msg += f" [local {local_size} bytes -> redownload]"
                print(msg)

            written = _download_to_file(url, part_path, timeout=timeout_get)

            # Verify if we know expected_size
            if expected_size is not None and written != expected_size:
                raise RuntimeError(f"size mismatch: wrote {written}, expected {expected_size}")

            # Atomic move into place
            os.replace(part_path, local_path)

            final_size = os.path.getsize(local_path)
            return DownloadResult(
                url=url,
                local_path=local_path,
                ok=True,
                skipped=False,
                expected_size=expected_size,
                local_size=final_size,
            )

        except Exception as e:
            last_err = str(e)
            # backoff
            if attempt < max_retries:
                time.sleep(0.5 * (attempt + 1))
            continue

    # Failed
    final_size = os.path.getsize(local_path) if os.path.exists(local_path) else 0
    return DownloadResult(
        url=url,
        local_path=local_path,
        ok=False,
        skipped=False,
        expected_size=expected_size,
        local_size=final_size,
        error=last_err,
    )


# -----------------------------
# High-level: get URL list via atlasopenmagic + multithread ensure
# -----------------------------
def ensure_atlas_open_data_downloaded(
    skim: str = "2muons",
    release: str = "2025e-13tev-beta",
    dataset: str = "data",
    protocol: str = "https",
    output_dir: str = "./atlas_data",
    max_files: int = 0,
    workers: int = 6,
    verbose: bool = True,
) -> dict[str, Any]:
    """
    Ensure ATLAS Open Data files are present locally & complete. Multi-threaded.

    Returns metadata including local_paths and per-file results.
    """
    atom.set_release(release)
    os.makedirs(output_dir, exist_ok=True)

    # Get URL list (no atlasopenmagic cache here)
    files_list = atom.get_urls(dataset, skim, protocol=protocol, cache=False)
    urls = []
    for entry in sorted(files_list):
        # atlasopenmagic returns "root::https://.../file.root"
        if "::" in entry:
            urls.append(entry.split("::", 1)[1])
        else:
            urls.append(entry)

    if max_files and max_files > 0:
        urls = urls[:max_files]

    results: list[DownloadResult] = []
    ok_paths: list[str] = []

    if verbose:
        print(f"[ensure] release={release} dataset={dataset} skim={skim} files={len(urls)} workers={workers}")
        print(f"[ensure] output_dir={os.path.abspath(output_dir)}")

    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        futs = [ex.submit(_ensure_one_file, url, output_dir, verbose=verbose) for url in urls]
        for fut in as_completed(futs):
            r = fut.result()
            results.append(r)
            if r.ok:
                ok_paths.append(r.local_path)
            if verbose:
                if r.ok and r.skipped:
                    print(f"[ok][skip] {os.path.basename(r.local_path)} ({r.local_size} bytes)")
                elif r.ok:
                    print(f"[ok]      {os.path.basename(r.local_path)} ({r.local_size} bytes)")
                else:
                    print(f"[fail]    {os.path.basename(r.local_path)} err={r.error}")

    # Keep stable order: same as urls
    url_to_path = {r.url: r.local_path for r in results if r.ok}
    local_paths_ordered = [url_to_path[u] for u in urls if u in url_to_path]

    n_ok = sum(1 for r in results if r.ok)
    n_fail = sum(1 for r in results if not r.ok)

    return {
        "release": release,
        "dataset": dataset,
        "skim": skim,
        "protocol": protocol,
        "output_dir": os.path.abspath(output_dir),
        "n_requested": len(urls),
        "n_ok": n_ok,
        "n_fail": n_fail,
        "local_paths": local_paths_ordered,
        "results": [r.__dict__ for r in results],  # JSON-friendly
        "raw_urls": urls,
    }

def ensure_data_cahce_downloaded(task: TaskSpec) -> dict[str, Any]:
    """
    Download (cache) files using atlasopenmagic, return metadata for later steps.
    """
    import atlasopenmagic as atom  # installed per user

    atom.set_release(task.release)

    # cache=True makes files copied locally rather than streamed.
    urls = atom.get_urls(task.dataset, task.skim, protocol=task.protocol, cache=task.cache)

    urls_sorted = sorted(urls)
    if task.max_files and task.max_files > 0:
        urls_sorted = urls_sorted[: task.max_files]

    local_paths = _get_local_paths_from_atlasopenmagic_urls(urls_sorted)

    return {
        "release": task.release,
        "dataset": task.dataset,
        "skim": task.skim,
        "protocol": task.protocol,
        "cache": task.cache,
        "n_files": len(local_paths),
        "local_paths": local_paths,
        # keep raw urls too in case you want to debug
        "raw_urls": urls_sorted,
    }


def download_atlas_open_data(task: TaskSpec) -> dict[str, Any]:
    return ensure_atlas_open_data_downloaded(
        skim=task.skim,
        release=task.release,
        dataset=task.dataset,
        protocol=task.protocol,
        output_dir=getattr(task, "output_dir", "./atlas_data"),
        max_files=task.max_files or 0,
        workers=getattr(task, "workers", 6),
        verbose=True,
    )