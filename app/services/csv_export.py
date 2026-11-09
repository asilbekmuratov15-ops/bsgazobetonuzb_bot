import csv
import io
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from app.services.validation import problems


def export_csv(documents, profile_path=Path(__file__).resolve().parents[2] / "csv_profile.json"):
    profile = json.loads(Path(profile_path).read_text(encoding="utf-8"))
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, delimiter=profile["delimiter"])
    writer.writerow(profile["columns"].values())

    def safe(value):
        if isinstance(value, Decimal):
            return format(value, "f").replace(".", profile["decimal_separator"])
        if isinstance(value, date):
            return value.strftime("%d.%m.%Y")
        value = str(value or "")
        return "'" + value if value.startswith(("=", "+", "-", "@", "\t", "\r", "\n")) else value

    for doc_id, inv in documents:
        if problems(inv):
            raise ValueError("Tasdiqlanmagan yoki xatoli hujjat")
        for n, item in enumerate(inv.items, 1):
            row = {
                **inv.model_dump(),
                **item.model_dump(),
                "document_id": doc_id,
                "line": n,
                "document_total": inv.total,
                "currency_total": inv.total,
            }
            writer.writerow((safe(row.get(k)) for k in profile["columns"]))
    return stream.getvalue().encode(profile["encoding"])
