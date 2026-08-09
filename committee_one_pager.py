"""
BLACKDARK — Committee One-Pager Auto (U6).

Printable / downloadable one-pager for funds & M&A committees from live evidence.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_minimal_pdf(lines: list[str], *, title: str = "BLACKDARK Committee One-Pager") -> bytes:
    """Tiny single-page PDF (Helvetica) — no external deps."""
    y = 800
    content_lines = [f"BT /F1 14 Tf 50 {y} Td ({_pdf_escape(title)}) Tj"]
    y_offset = -28
    content_lines.append(f"/F1 10 Tf 0 {y_offset} Td ({_pdf_escape(lines[0] if lines else '')}) Tj")
    for line in lines[1:40]:
        content_lines.append(f"0 -14 Td ({_pdf_escape(line[:110])}) Tj")
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", errors="replace")

    objs: list[bytes] = []
    objs.append(b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n")
    objs.append(b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n")
    objs.append(
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>endobj\n"
    )
    objs.append(f"4 0 obj<< /Length {len(stream)} >>stream\n".encode() + stream + b"\nendstream\nendobj\n")
    objs.append(b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n")

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objs:
        offsets.append(len(out))
        out.extend(obj)
    xref_pos = len(out)
    out.extend(f"xref\n0 {len(offsets)}\n".encode())
    out.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode())
    out.extend(
        f"trailer<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode()
    )
    return bytes(out)


async def build_committee_one_pager() -> dict[str, Any]:
    from acquirer_evidence_pack import build_acquirer_evidence_pack
    from kill_rate_board import build_kill_rate_board

    pack = await build_acquirer_evidence_pack()
    kills = build_kill_rate_board()
    acc = pack.get("sections", {}).get("public_accuracy") or {}
    truth = pack.get("sections", {}).get("net_edge_truth") or {}
    registry = pack.get("sections", {}).get("signal_registry") or {}
    audit = pack.get("sections", {}).get("audit_chain") or {}

    hit = acc.get("hit_rate_percent") or acc.get("direction_hit_rate_percent") or acc.get("hit_rate")
    samples = acc.get("sample_size") or acc.get("resolved_count") or acc.get("n") or 0

    bullets = [
        f"Generated: {datetime.now(UTC).isoformat()}",
        f"Thesis: {pack.get('product_thesis')}",
        f"Public accuracy hit-rate: {hit} | samples: {samples}",
        f"Net-Edge reject rate: {truth.get('reject_rate')} | evaluated: {truth.get('evaluated')}",
        f"Public kill-rate: {kills['metrics']['kill_rate_percent']}% | kills: {kills['metrics']['total_kills']}",
        f"Signal registry: {registry}",
        f"Audit chain: {audit.get('summary') or audit}",
        "Differentiators: D1 Proof · D2 Veto · D3 Net-Edge · D4 Half-Life · D6 Evidence · D8 Registry",
        "Access: Desk/Institutional Evidence Pack + this one-pager",
        "Disclaimer: Not financial advice. Proof ≠ guaranteed returns.",
    ]

    checklist = list(pack.get("committee_checklist") or [])
    html = _render_html(bullets, checklist, kills)

    return {
        "surface": "committee_one_pager",
        "generated_at": datetime.now(UTC).isoformat(),
        "title": "BLACKDARK — Committee One-Pager",
        "bullets": bullets,
        "checklist": checklist,
        "kill_rate": kills["metrics"],
        "html": html,
        "pdf_available": True,
        "endpoints": {
            "json": "/api/due-diligence/committee-one-pager",
            "html": "/b2b/committee-one-pager",
            "pdf": "/api/due-diligence/committee-one-pager.pdf",
        },
        "access": "whale_or_admin",
        "disclaimer": "Committee packet — analytical evidence only. Not financial advice.",
    }


def _render_html(bullets: list[str], checklist: list[Any], kills: dict[str, Any]) -> str:
    lis = "".join(f"<li>{b}</li>" for b in bullets)
    checks = "".join(f"<li>{c}</li>" for c in checklist[:20]) or "<li>See Evidence Pack checklist</li>"
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>BLACKDARK Committee One-Pager</title>
<style>
@page {{ margin: 16mm; }}
body {{ font-family: Georgia, 'Times New Roman', serif; color:#111; max-width:720px; margin:24px auto; }}
h1 {{ font-size:22px; letter-spacing:.04em; }}
.kicker {{ color:#444; font-size:13px; margin-bottom:18px; }}
.metric {{ font-size:28px; font-weight:700; margin:12px 0; }}
ul {{ line-height:1.55; }}
.foot {{ margin-top:28px; font-size:11px; color:#666; }}
@media print {{ .noprint {{ display:none; }} }}
</style></head><body>
<p class="kicker">BLACKDARK Trust OS · Acquirer / Fund Committee</p>
<h1>Committee One-Pager</h1>
<p class="metric">Kill-Rate {kills['metrics']['kill_rate_percent']}%</p>
<p>We publish refusals. Fewer signals. Higher executable honesty.</p>
<ul>{lis}</ul>
<h2>Checklist</h2>
<ul>{checks}</ul>
<p class="foot">Not financial advice. Print or Save as PDF. Source: /api/due-diligence/evidence-pack</p>
<p class="noprint"><button onclick="window.print()">Print / Save PDF</button>
<a href="/api/due-diligence/committee-one-pager.pdf">Download PDF</a></p>
</body></html>"""


def render_committee_pdf(one_pager: dict[str, Any]) -> bytes:
    lines = [str(x) for x in one_pager.get("bullets") or []]
    return build_minimal_pdf(lines, title=str(one_pager.get("title") or "BLACKDARK Committee"))
