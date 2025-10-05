import hashlib
import aiofiles


async def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    async with aiofiles.open(path, "rb") as f:
        while True:
            chunk = await f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()
