from __future__ import annotations

import os
import time
from typing import Iterable, List, Tuple

import requests
from flask import current_app


class BlobClient:
    """
    极简版 Vercel Blob 客户端，使用 REST API：
    - 上传：POST https://api.vercel.com/v2/blob/upload
    - 删除：DELETE https://api.vercel.com/v2/blob/<blob_id>

    需要环境变量：BLOB_READ_WRITE_TOKEN
    """

    UPLOAD_URL = "https://api.vercel.com/v2/blob/upload"
    DELETE_URL = "https://api.vercel.com/v2/blob/{blob_id}"

    def __init__(self, token: str | None = None) -> None:
        self.token = token or os.getenv("BLOB_READ_WRITE_TOKEN", "")
        if not self.token:
            raise RuntimeError("缺少 BLOB_READ_WRITE_TOKEN，无法进行图片上传/删除")

    def upload_files(self, files: Iterable[Tuple[str, bytes]]) -> List[str]:
        """
        上传多张图片，返回 blob URL 列表。
        files: [(filename, content_bytes), ...]
        """
        urls: List[str] = []
        for filename, content in files:
            key = f"notes/{int(time.time()*1000)}_{filename}"
            res = requests.post(
                self.UPLOAD_URL,
                headers={"Authorization": f"Bearer {self.token}"},
                files={"file": (key, content)},
            )
            if res.status_code >= 300:
                current_app.logger.error("Blob upload failed: %s", res.text)
                raise RuntimeError("图片上传失败")
            data = res.json()
            # Vercel 返回 { url, downloadUrl, pathname, ... }
            url = data.get("url") or data.get("downloadUrl")
            if not url:
                raise RuntimeError("图片上传失败，未返回 URL")
            urls.append(url)
        return urls

    def delete_urls(self, urls: Iterable[str]) -> None:
        """
        根据 blob URL 删除文件。URL 形如 https://...vercel-storage.com/<blob_id>
        这里简单从 URL 取末段作为 blob_id。
        """
        for url in urls:
            blob_id = url.rstrip("/").split("/")[-1]
            res = requests.delete(
                self.DELETE_URL.format(blob_id=blob_id),
                headers={"Authorization": f"Bearer {self.token}"},
            )
            if res.status_code >= 300:
                current_app.logger.warning("Blob delete failed for %s: %s", url, res.text)


