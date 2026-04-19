#!/usr/bin/env python
"""Sync product images referenced in db.sqlite3 to Cloudflare R2."""

from __future__ import annotations

import argparse
import mimetypes
import os
import sys
from difflib import get_close_matches
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "arivas.settings")

import django  # noqa: E402

django.setup()

from app.models import Product  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload product images from local disk to Cloudflare R2")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be uploaded/fixed without uploading or saving DB changes.",
    )
    parser.add_argument(
        "--fix-missing",
        action="store_true",
        help="Fix DB image names when file is missing but a close filename exists in products folder.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip upload when object already exists in R2.",
    )
    return parser.parse_args()


def env_required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def build_r2_client() -> tuple[object, str]:
    access_key = env_required("R2_ACCESS_KEY_ID")
    secret_key = env_required("R2_SECRET_ACCESS_KEY")
    bucket = env_required("R2_BUCKET_NAME")

    endpoint = os.getenv("R2_ENDPOINT_URL", "").strip()
    if not endpoint:
        account_id = env_required("R2_ACCOUNT_ID")
        endpoint = f"https://{account_id}.r2.cloudflarestorage.com"

    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=os.getenv("R2_REGION", "auto"),
    )
    return client, bucket


def resolve_file(image_name: str, products_dir: Path, media_dir: Path) -> Path | None:
    rel_path = Path(image_name)
    candidates = [
        BASE_DIR / rel_path,
        products_dir / rel_path.name,
        media_dir / rel_path,
        media_dir / "products" / rel_path.name,
    ]
    for path in candidates:
        if path.exists() and path.is_file():
            return path
    return None


def object_exists(s3_client: object, bucket: str, key: str) -> bool:
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as exc:
        status_code = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if status_code == 404:
            return False
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code in {"404", "NoSuchKey", "NotFound"}:
            return False
        raise


def normalize_key(image_name: str) -> str:
    key = image_name.replace("\\", "/").lstrip("/")
    if not key.startswith("products/"):
        key = f"products/{Path(key).name}"
    return key


def main() -> None:
    args = parse_args()

    products_dir = BASE_DIR / "products"
    media_dir = BASE_DIR / "media"
    local_product_files = sorted([p.name for p in products_dir.glob("*") if p.is_file()])

    s3_client = None
    bucket_name = ""
    if not args.dry_run:
        s3_client, bucket_name = build_r2_client()

    uploaded = 0
    skipped = 0
    fixed = 0
    missing = []
    total = 0

    queryset = Product.objects.exclude(image="").exclude(image__isnull=True).order_by("id")

    for product in queryset:
        total += 1
        original_image_name = product.image.name
        image_name = original_image_name

        local_path = resolve_file(image_name, products_dir, media_dir)

        if not local_path and args.fix_missing:
            matches = get_close_matches(Path(image_name).name, local_product_files, n=1, cutoff=0.75)
            if matches:
                corrected_name = f"products/{matches[0]}"
                if corrected_name != image_name:
                    print(f"[FIX] Product #{product.id}: {image_name} -> {corrected_name}")
                    fixed += 1
                    image_name = corrected_name
                    local_path = products_dir / matches[0]
                    if not args.dry_run:
                        product.image.name = corrected_name
                        product.save(update_fields=["image", "updated_at"])

        if not local_path:
            missing.append((product.id, product.name, original_image_name))
            continue

        key = normalize_key(image_name)

        if args.dry_run:
            print(f"[DRY-RUN] Product #{product.id} -> {key} ({local_path})")
            continue

        if args.skip_existing and object_exists(s3_client, bucket_name, key):
            skipped += 1
            print(f"[SKIP] Already exists in bucket: {key}")
            continue

        extra_args = {"CacheControl": "public, max-age=31536000, immutable"}
        content_type, _ = mimetypes.guess_type(str(local_path))
        if content_type:
            extra_args["ContentType"] = content_type

        s3_client.upload_file(str(local_path), bucket_name, key, ExtraArgs=extra_args)
        uploaded += 1
        print(f"[UPLOADED] Product #{product.id} -> {key}")

    print("\n--- Summary ---")
    print(f"Total product image records checked: {total}")
    print(f"Uploaded to R2: {uploaded}")
    print(f"Skipped (already exists): {skipped}")
    print(f"DB image paths fixed: {fixed}")
    print(f"Missing local files: {len(missing)}")

    if missing:
        print("\nMissing records:")
        for item in missing:
            print(item)


if __name__ == "__main__":
    main()
