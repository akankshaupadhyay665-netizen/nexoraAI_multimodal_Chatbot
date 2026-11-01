"""
NEXORA AI - Web Media, YouTube & Website Intelligence Service
Provides SSRF-protected URL inspection, YouTube metadata & transcripts,
direct video stream detection (MP4/WebM/HLS), and Open Graph web extraction.
"""
import re
import ipaddress
import socket
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, List, Optional
import httpx
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi

class WebMediaService:
    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36 NexoraBot/2.5"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        }
        self.timeout = httpx.Timeout(10.0, connect=5.0)

    # =========================================================================
    # SSRF Protection & URL Validation
    # =========================================================================
    @staticmethod
    def is_safe_url(url: str) -> bool:
        """
        Validates URL to protect against SSRF (Server-Side Request Forgery).
        Blocks private IP ranges, loopback addresses, local link-local, and cloud metadata IPs.
        """
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return False

            hostname = parsed.hostname
            if not hostname:
                return False

            # Block localhost and typical local domains
            lower_host = hostname.lower()
            if lower_host in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
                return False
            if lower_host.endswith(".local") or lower_host.endswith(".internal"):
                return False

            # Resolve IP and check against private / reserved ranges
            try:
                ip_str = socket.gethostbyname(hostname)
                ip = ipaddress.ip_address(ip_str)
                if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                    return False
                # Block AWS/GCP/Azure link-local metadata IP (169.254.169.254)
                if str(ip) == "169.254.169.254":
                    return False
            except Exception:
                # If DNS resolution fails, reject for safety
                return False

            return True
        except Exception:
            return False

    # =========================================================================
    # URL Categorization
    # =========================================================================
    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """Extracts valid HTTP/HTTPS URLs from plain text messages"""
        url_pattern = r'https?://[^\s<>"\)\]\}]+'
        matches = re.findall(url_pattern, text)
        clean_urls = []
        for u in matches:
            # Strip trailing punctuation often captured
            clean = u.rstrip(".,;:!?")
            if clean and clean not in clean_urls:
                clean_urls.append(clean)
        return clean_urls

    @staticmethod
    def is_youtube_url(url: str) -> bool:
        """Checks if a URL belongs to YouTube"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        return any(d in domain for d in ["youtube.com", "youtu.be", "m.youtube.com"])

    @staticmethod
    def extract_youtube_id(url: str) -> Optional[str]:
        """Extracts the 11-character video ID from YouTube watch, embed, shorts, or shortlinks"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        if "youtu.be" in domain:
            # https://youtu.be/VIDEO_ID
            path = parsed.path.strip("/")
            return path.split("?")[0].split("/")[0] if path else None

        if "youtube.com" in domain or "m.youtube.com" in domain:
            # https://www.youtube.com/watch?v=VIDEO_ID
            if "/watch" in parsed.path:
                qs = parse_qs(parsed.query)
                v_list = qs.get("v")
                if v_list:
                    return v_list[0]
            # https://www.youtube.com/shorts/VIDEO_ID
            if "/shorts/" in parsed.path:
                parts = parsed.path.split("/shorts/")
                if len(parts) > 1:
                    return parts[1].split("/")[0].split("?")[0]
            # https://www.youtube.com/embed/VIDEO_ID
            if "/embed/" in parsed.path:
                parts = parsed.path.split("/embed/")
                if len(parts) > 1:
                    return parts[1].split("/")[0].split("?")[0]

        return None

    @staticmethod
    def is_direct_video_url(url: str) -> bool:
        """Checks if URL directly points to an MP4, WebM, or HLS stream"""
        path = urlparse(url).path.lower()
        return any(path.endswith(ext) for ext in [".mp4", ".webm", ".m3u8", ".ogv"])

    @staticmethod
    def is_direct_image_url(url: str) -> bool:
        """Checks if URL directly points to an image"""
        path = urlparse(url).path.lower()
        return any(path.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg", ".bmp"])

    @staticmethod
    def is_vimeo_url(url: str) -> bool:
        """Checks if URL is a Vimeo video"""
        domain = urlparse(url).netloc.lower()
        return "vimeo.com" in domain

    # =========================================================================
    # YouTube Metadata & Transcript Extraction
    # =========================================================================
    async def get_youtube_info(self, url: str) -> Dict[str, Any]:
        """
        Retrieves official YouTube oEmbed metadata, thumbnail, embed URL,
        and legal transcript if available.
        """
        video_id = self.extract_youtube_id(url)
        if not video_id:
            return {"success": False, "error": "Invalid YouTube video ID"}

        data = {
            "type": "youtube",
            "video_id": video_id,
            "url": url,
            "embed_url": f"https://www.youtube-nocookie.com/embed/{video_id}?enablejsapi=1&rel=0",
            "title": f"YouTube Video ({video_id})",
            "author": "YouTube Creator",
            "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
            "fallback_thumbnail": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
            "has_transcript": False,
            "transcript_text": "",
            "transcript_segments": [],
            "duration": None
        }

        # 1. Fetch official oEmbed metadata
        try:
            oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                res = await client.get(oembed_url)
                if res.status_code == 200:
                    info = res.json()
                    data["title"] = info.get("title", data["title"])
                    data["author"] = info.get("author_name", data["author"])
                    if info.get("thumbnail_url"):
                        data["thumbnail_url"] = info["thumbnail_url"]
        except Exception as e:
            # Fallback to standard YouTube thumbnail
            pass

        # 2. Fetch transcript if legally available
        try:
            # Supports English, auto-generated, and common international languages
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US', 'en-GB', 'auto', 'es', 'fr', 'de'])
            if transcript_list:
                data["has_transcript"] = True
                segments = []
                formatted_lines = []
                
                for item in transcript_list[:150]:  # Limit to ~150 key segments
                    start_sec = int(item.get("start", 0))
                    mins = start_sec // 60
                    secs = start_sec % 60
                    time_str = f"{mins:02d}:{secs:02d}"
                    text = item.get("text", "").strip()
                    if text:
                        segments.append({"time": time_str, "seconds": start_sec, "text": text})
                        formatted_lines.append(f"[{time_str}] {text}")

                data["transcript_segments"] = segments
                data["transcript_text"] = "\n".join(formatted_lines)
        except Exception:
            # Transcripts might be disabled or unavailable for this video
            data["has_transcript"] = False

        data["success"] = True
        return data

    # =========================================================================
    # Direct Video & Vimeo Information
    # =========================================================================
    async def get_direct_video_info(self, url: str) -> Dict[str, Any]:
        """Inspects direct video stream (MP4, WebM, HLS)"""
        parsed = urlparse(url)
        path = parsed.path.lower()
        is_hls = path.endswith(".m3u8")
        ext = "m3u8" if is_hls else (path.split(".")[-1] if "." in path else "mp4")

        # Extract filename from path
        filename = parsed.path.split("/")[-1] or "video"

        return {
            "success": True,
            "type": "direct_video",
            "url": url,
            "filename": filename,
            "format": ext,
            "is_hls": is_hls,
            "title": f"Video: {filename}",
            "description": f"Direct stream format: {ext.upper()}"
        }

    async def get_vimeo_info(self, url: str) -> Dict[str, Any]:
        """Fetches Vimeo video metadata using official oEmbed"""
        data = {
            "success": True,
            "type": "vimeo",
            "url": url,
            "title": "Vimeo Video",
            "thumbnail_url": "",
            "embed_url": ""
        }
        try:
            oembed_url = f"https://vimeo.com/api/oembed.json?url={url}"
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                res = await client.get(oembed_url)
                if res.status_code == 200:
                    info = res.json()
                    data["title"] = info.get("title", "Vimeo Video")
                    data["thumbnail_url"] = info.get("thumbnail_url", "")
                    data["author"] = info.get("author_name", "")
                    video_id = info.get("video_id")
                    if video_id:
                        data["embed_url"] = f"https://player.vimeo.com/video/{video_id}"
        except Exception:
            pass
        return data

    # =========================================================================
    # General Webpage & Open Graph Metadata Extraction
    # =========================================================================
    async def get_webpage_info(self, url: str) -> Dict[str, Any]:
        """
        Extracts Open Graph metadata, title, description, favicon, and readable article text.
        Guarantees SSRF protection and safe character truncation.
        """
        if not self.is_safe_url(url):
            return {
                "success": False,
                "error": "URL failed security validation (private/internal IP blocked)"
            }

        domain = urlparse(url).netloc

        data = {
            "success": True,
            "type": "webpage",
            "url": url,
            "domain": domain,
            "title": domain,
            "description": "",
            "image": "",
            "favicon": f"https://www.google.com/s2/favicons?domain={domain}&sz=64",
            "readable_text": ""
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                res = await client.get(url)
                if res.status_code != 200:
                    data["description"] = f"Webpage returned HTTP status {res.status_code}"
                    return data

                html = res.text
                soup = BeautifulSoup(html, "html.parser")

                # 1. Title
                title_tag = soup.find("meta", property="og:title") or soup.find("title")
                if title_tag:
                    data["title"] = (title_tag.get("content") or title_tag.get_text() or domain).strip()

                # 2. Description
                desc_tag = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
                if desc_tag and desc_tag.get("content"):
                    data["description"] = desc_tag["content"].strip()

                # 3. Open Graph Image
                img_tag = soup.find("meta", property="og:image")
                if img_tag and img_tag.get("content"):
                    og_img = img_tag["content"].strip()
                    if og_img.startswith("//"):
                        og_img = "https:" + og_img
                    elif og_img.startswith("/"):
                        og_img = f"https://{domain}{og_img}"
                    data["image"] = og_img

                # 4. Extract readable text for AI analysis (strip script, style, nav, footer)
                for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "svg"]):
                    tag.decompose()

                raw_text = soup.get_text(separator=" ", strip=True)
                # Normalize whitespace
                clean_text = re.sub(r'\s+', ' ', raw_text)
                # Truncate to reasonable context window (~3,000 characters)
                data["readable_text"] = clean_text[:3000].strip()

        except Exception as e:
            data["description"] = f"Unable to fetch preview: {str(e)[:80]}"

        return data

    # =========================================================================
    # Universal URL Inspector
    # =========================================================================
    async def inspect_url(self, url: str) -> Dict[str, Any]:
        """Inspects any URL and delegates to specialized extractor"""
        if not self.is_safe_url(url):
            return {"success": False, "error": "Restricted address"}

        if self.is_youtube_url(url):
            return await self.get_youtube_info(url)
        elif self.is_direct_video_url(url):
            return await self.get_direct_video_info(url)
        elif self.is_vimeo_url(url):
            return await self.get_vimeo_info(url)
        elif self.is_direct_image_url(url):
            return {
                "success": True,
                "type": "image",
                "url": url,
                "title": url.split("/")[-1].split("?")[0] or "Web Image",
                "image_url": url
            }
        else:
            return await self.get_webpage_info(url)

    async def fetch_image_bytes(self, url: str) -> Optional[bytes]:
        """Fetches remote image safely for Gemini Vision analysis"""
        if not self.is_safe_url(url):
            return None
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                res = await client.get(url)
                if res.status_code == 200 and "image" in res.headers.get("content-type", ""):
                    # Enforce max 15MB limit
                    if len(res.content) <= 15 * 1024 * 1024:
                        return res.content
        except Exception:
            return None
        return None

web_media_service = WebMediaService()

