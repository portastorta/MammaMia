import re
from fastapi import HTTPException
from fastapi.responses import Response
from curl_cffi.requests import AsyncSession
import Src.Utilities.config as config
import logging
from Src.Utilities.config import setup_logging

level = config.LEVEL
logger = setup_logging(level)
SC_DOMAIN = config.SC_DOMAIN
User_Agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"


async def fetch_and_filter_playlist(url, quality, proxies):
    headers = {
        'User-Agent': User_Agent,
        'Referer': f"{SC_DOMAIN}/",
        'Origin': SC_DOMAIN
    }

    try:
        async with AsyncSession(proxies=proxies) as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch playlist")

            content = response.text

            filtered_lines = []
            if not content.startswith("#EXTM3U"):
                filtered_lines.append("#EXTM3U")

            iter_lines = iter(content.splitlines())
            for line in iter_lines:
                if line.startswith("#EXTM3U"):
                    filtered_lines.append(line)
                    continue
                if line.startswith("#EXT-X-MEDIA"):
                    filtered_lines.append(line)
                    continue
                if line.startswith("#EXT-X-STREAM-INF"):
                    if f"RESOLUTION={quality}" in line:
                        filtered_lines.append(line)
                        try:
                            next_line = next(iter_lines)
                            filtered_lines.append(next_line)
                        except StopIteration:
                            break
                    else:
                        try:
                            next(iter_lines)
                        except StopIteration:
                            break
                    continue
                if line.startswith("#") and not line.startswith("#EXT"):
                    filtered_lines.append(line)

            new_playlist = "\n".join(filtered_lines)
            return Response(content=new_playlist, media_type="application/vnd.apple.mpegurl")

    except Exception as e:
        logger.error(f"Proxy invalid: {e}")
        raise HTTPException(status_code=500, detail=str(e))
