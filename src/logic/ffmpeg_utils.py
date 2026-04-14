"""FFmpeg utility functions."""

import asyncio
import os


async def get_video_duration(path: str, timeout: float = 30.0) -> float | None:
    """Get video duration using ffprobe."""
    clean_path = path.strip().strip('"').strip("'").strip()

    if not os.path.exists(clean_path):
        return None

    try:
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            clean_path,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return None
        except asyncio.CancelledError:
            proc.kill()
            await proc.wait()
            raise

        if proc.returncode == 0:
            duration_str = stdout.decode().strip()
            if duration_str:
                return float(duration_str)
            return None
        else:
            return None
    except asyncio.CancelledError:
        raise
    except Exception:
        return None


async def run_ffmpeg(
    cmd: list[str], log_callback, idx: int, out_path: str, timeout: float = 3600.0
) -> bool:
    """Run ffmpeg command and log output.
    
    Args:
        cmd: FFmpeg command list
        log_callback: Function to log progress messages
        idx: Task index for logging
        out_path: Output file path
        timeout: Maximum time in seconds (default 1 hour)
    """
    proc = None
    try:
        log_callback(f"[Task #{idx}] ⏳ Processing... {os.path.basename(out_path)}\n")

        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            log_callback(f"[Task #{idx}] ❌ Timeout after {timeout}s\n")
            return False
        except asyncio.CancelledError:
            proc.kill()
            await proc.wait()
            raise

        if proc.returncode != 0:
            log_callback(f"[Task #{idx}] ❌ FFmpeg Error\n")
            err = stderr.decode(errors="ignore")[:500]
            log_callback(f"{err}\n")
            return False
        else:
            # Check file exists before getting size
            if os.path.exists(out_path):
                file_size = os.path.getsize(out_path) / (1024 * 1024)
                log_callback(f"[Task #{idx}] ✅ Completed ({file_size:.1f} MB)\n")
                return True
            else:
                log_callback(f"[Task #{idx}] ❌ Output file not found\n")
                return False
    except asyncio.CancelledError:
        if proc:
            proc.kill()
            await proc.wait()
        raise
    except Exception as exc:
        log_callback(f"[Task #{idx}] ❌ Exception: {exc}\n")
        return False
