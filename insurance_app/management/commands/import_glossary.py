from django.core.management.base import BaseCommand
from django.db import transaction
from pathlib import Path
import json

from insurance_app.models import GlossaryTerm

class Command(BaseCommand):
    help = "Load/Update glossary terms from insurance_app/data/glossary.json into DB"

    def handle(self, *args, **options):
        data_path = Path(__file__).resolve().parents[2] / "data" / "glossary.json"
        if not data_path.exists():
            self.stderr.write(f"[ERR] Not found: {data_path}")
            return

        try:
            data = json.loads(data_path.read_text(encoding="utf-8"))
        except Exception as e:
            self.stderr.write(f"[ERR] JSON read error: {e}")
            return

        if not isinstance(data, list):
            self.stderr.write("[ERR] JSON must be a list")
            return

        created = updated = 0
        with transaction.atomic():
            for it in data:
                slug = it.get("slug") or ""
                defaults = {
                    "term": it.get("term") or "",
                    "short_def": it.get("short_def") or "",
                    "long_def": it.get("long_def") or "",
                    "category": it.get("category") or "",
                    "aliases": it.get("aliases") or [],
                    "related": it.get("related") or [],
                    "meta": it.get("meta") or {},
                }
                obj, is_created = GlossaryTerm.objects.update_or_create(
                    slug=slug,
                    defaults=defaults
                )
                if is_created: created += 1
                else: updated += 1

        self.stdout.write(self.style.SUCCESS(f"Glossary imported. created={created}, updated={updated}"))
