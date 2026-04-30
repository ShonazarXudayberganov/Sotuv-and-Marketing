"""Generate a PDF invoice with reportlab — no external HTML→PDF dependency."""

from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models.billing import Invoice, Subscription
from app.models.tenant import Tenant


def render_invoice_pdf(*, invoice: Invoice, sub: Subscription, tenant: Tenant) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>NEXUS AI</b> — Hisob faktura", styles["Title"]))
    elements.append(Spacer(1, 6 * mm))

    meta = [
        ["Invoice raqami:", invoice.invoice_number],
        ["Sana:", invoice.created_at.strftime("%Y-%m-%d") if invoice.created_at else "-"],
        ["To'lov muddati:", invoice.due_at.strftime("%Y-%m-%d") if invoice.due_at else "-"],
        ["Holat:", invoice.status.upper()],
        ["Mijoz:", tenant.name],
        ["Tenant ID:", str(tenant.id)],
    ]
    meta_tbl = Table(meta, colWidths=[40 * mm, 100 * mm])
    meta_tbl.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#6b6b6b")),
            ]
        )
    )
    elements.append(meta_tbl)
    elements.append(Spacer(1, 6 * mm))

    package_label = (sub.package or "custom").title()
    description = f"{package_label} — {sub.tier} ({len(sub.selected_modules)} modul)"
    rows = [["Tavsif", "Davr (oy)", "Chegirma %", "Miqdor (so'm)"]]
    rows.append(
        [
            description,
            str(sub.billing_cycle_months),
            f"{sub.discount_percent}%",
            f"{invoice.amount:,}".replace(",", " "),
        ]
    )
    rows.append(["", "", "JAMI:", f"{invoice.amount:,} so'm".replace(",", " ")])

    items_tbl = Table(rows, colWidths=[80 * mm, 25 * mm, 25 * mm, 40 * mm])
    items_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A1A1A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#F8F4ED")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#E6DCC4")),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("ALIGN", (-1, 1), (-1, -1), "RIGHT"),
                ("ALIGN", (1, 1), (2, -1), "CENTER"),
            ]
        )
    )
    elements.append(items_tbl)
    elements.append(Spacer(1, 10 * mm))

    elements.append(
        Paragraph(
            "<b>To'lov ko'rsatmasi:</b> Bank o'tkazmasi orqali to'lang. To'lov tasdiqlangach, "
            "akkauntingizdagi modullar avtomatik faollashtiriladi.",
            styles["Normal"],
        )
    )
    elements.append(Spacer(1, 4 * mm))
    elements.append(Paragraph("Savol bo'lsa: <b>support@nexusai.uz</b>", styles["Normal"]))

    doc.build(elements)
    return buf.getvalue()
