from urllib.parse import quote, urljoin

from django.conf import settings
from storages.backends.s3 import S3Storage


class PublicMediaURLS3Storage(S3Storage):
    """Build media URLs from the configured public R2 URL."""

    def url(self, name, parameters=None, expire=None, http_method=None):
        cleaned_name = str(name).replace("\\", "/").lstrip("/")
        base_url = (getattr(settings, "R2_PUBLIC_MEDIA_URL", "") or "").strip()

        if base_url:
            safe_key = quote(cleaned_name, safe="/")
            return urljoin(base_url.rstrip("/") + "/", safe_key)

        return super().url(
            name,
            parameters=parameters,
            expire=expire,
            http_method=http_method,
        )
