"""Recover the plotted acetate-MFC series from Fig. S2 of L096's DOCX.

The figure's numeric chart cache preserves plotted values. It is not a raw
instrument export. No points from the MEC or hydrolysate arms are processed.
"""
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
import argparse
import json
import xml.etree.ElementTree as ET

DATA = Path(__file__).resolve().parents[1] / "research" / "conventional-arms"
MEMBER = "word/charts/chart1.xml"
CHART_NS = {
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
}


def points(series, dimension):
    container = series.find(f"c:{dimension}/c:numRef/c:numCache", CHART_NS)
    count = int(container.find("c:ptCount", CHART_NS).attrib["val"])
    entries = container.findall("c:pt", CHART_NS)
    rows = {
        int(point.attrib["idx"]): Decimal(point.findtext("c:v", namespaces=CHART_NS))
        for point in entries
    }
    if not rows or len(rows) != len(entries) or any(
        index < 0 or index >= count or not value.is_finite() for index, value in rows.items()
    ):
        raise ValueError("Invalid plotted value or index")
    return rows


def extract(document):
    with ZipFile(document) as archive:
        root = ET.fromstring(archive.read(MEMBER))
    if [node.text for node in root.findall(".//a:t", CHART_NS)] != ["Time (Days)", "Voltage (mV)", "Current (mA)"]:
        raise ValueError("Unexpected axes in supplementary figure")
    voltage, current = root.findall(".//c:ser", CHART_NS)
    days = points(voltage, "xVal")
    u = points(voltage, "yVal")
    i = points(current, "yVal")
    ordered_days = [days[index] for index in sorted(days)]
    if days != points(current, "xVal") or days.keys() != u.keys() or days.keys() != i.keys():
        raise ValueError("Unaligned time coordinates")
    if ordered_days != sorted(set(ordered_days)) or any(day % 1 for day in ordered_days):
        raise ValueError("Invalid day coordinates")
    return [
        {"chart_index": index, "day": int(days[index]), "voltage_mv": str(u[index]), "current_ma": str(i[index])}
        for index in sorted(days)
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    digest = sha256(args.document.read_bytes()).hexdigest()
    attachments = json.loads((DATA / "attachments.json").read_text())
    identity = next(row for row in attachments if row["source"] == "L096")
    if digest != identity["sha256"]:
        raise ValueError("Supplement SHA-256 differs from the reviewed document")
    series = {
        "arm_id": "L096-acetate", "document_sha256": digest, "locator": f"Fig. S2, {MEMBER}",
        "method": "Read aligned numeric cache entries for voltage and current from the published DOCX.",
        "status": "quarantined_for_modeling",
        "limitations": [
            "Values are plotted source values with original units. Measurement log not recovered.",
            "Reported resistance and experimental duration conflict with the plotted series.",
            "Missing days are left absent. No point was digitized or interpolated.",
        ],
        "points": extract(args.document),
    }
    output = DATA / "series-L096.json"
    encoded = json.dumps(series, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if output.read_text(encoding="utf-8") != encoded:
            raise ValueError("Committed series differs from the source chart")
    else:
        temporary = output.with_suffix(".json.part")
        temporary.write_text(encoded, encoding="utf-8")
        temporary.replace(output)
    print(f"{series['arm_id']}: {len(series['points'])} published pairs, quarantined for modeling")


if __name__ == "__main__":
    main()
