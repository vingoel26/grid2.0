"""Service to generate PDF challans."""
from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

from ..models import Violation
from .owner_lookup import OwnerInfo
from ..main import EVIDENCE_DIR

log = logging.getLogger("backend.challan_generator")


class ChallanGenerator:
    """Generates official-looking PDF challans using ReportLab."""

    def __init__(self, output_dir: str | Path = EVIDENCE_DIR / "challans"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self.title_style = self.styles['Heading1']
        self.title_style.alignment = 1  # Center
        self.normal_style = self.styles['Normal']

    def generate(self, challan_number: str, violation: Violation, owner: OwnerInfo, due_date: datetime) -> str:
        """
        Generates a PDF challan and returns the relative path.
        """
        pdf_filename = f"{challan_number}.pdf"
        pdf_path = self.output_dir / pdf_filename
        
        doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
        elements = []

        # 1. Header
        elements.append(Paragraph("<b>TRAFFIC POLICE E-CHALLAN</b>", self.title_style))
        elements.append(Spacer(1, 12))
        
        # 2. General Info Table
        info_data = [
            ["Challan No:", challan_number, "Date:", datetime.now().strftime("%Y-%m-%d %H:%M")],
            ["Vehicle Plate:", violation.plate_number or "UNKNOWN", "Vehicle Type:", violation.vehicle_type or "UNKNOWN"],
            ["Owner Name:", owner.name, "Owner Phone:", owner.phone],
            ["Owner Address:", Paragraph(owner.address, self.normal_style), "", ""]
        ]
        info_table = Table(info_data, colWidths=[100, 150, 100, 150])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 20))

        # 3. Violation Details
        elements.append(Paragraph("<b>VIOLATION DETAILS</b>", self.styles['Heading3']))
        viol_data = [
            ["Violation Type:", violation.violation_type],
            ["Section (MVA):", violation.violation_code],
            ["Location:", violation.location_name or violation.camera_name or violation.camera_id],
            ["Date & Time:", violation.occurred_at.strftime("%Y-%m-%d %H:%M:%S") if violation.occurred_at else "UNKNOWN"],
        ]
        viol_table = Table(viol_data, colWidths=[120, 380])
        viol_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        elements.append(viol_table)
        elements.append(Spacer(1, 20))

        # 4. Evidence Image
        if violation.evidence_image_path or violation.evidence_thumbnail_path:
            img_path_rel = violation.evidence_image_path or violation.evidence_thumbnail_path
            # Handle absolute or relative paths
            if img_path_rel.startswith("/evidence"):
                img_path = Path("/evidence") / img_path_rel.replace("/evidence/", "")
                # In local dev where /evidence might not be at root but in EVIDENCE_DIR
                if not img_path.exists() and EVIDENCE_DIR.name == "evidence":
                    img_path = EVIDENCE_DIR / img_path_rel.replace("/evidence/", "")
            else:
                img_path = EVIDENCE_DIR / img_path_rel
                
            if img_path.exists():
                elements.append(Paragraph("<b>EVIDENCE</b>", self.styles['Heading3']))
                try:
                    # Maintain aspect ratio, max width 400
                    img = Image(str(img_path))
                    img.drawWidth = 400
                    img.drawHeight = img.drawWidth * (img.imageHeight / img.imageWidth)
                    elements.append(img)
                except Exception as e:
                    log.error(f"Failed to embed evidence image {img_path}: {e}")
                    elements.append(Paragraph(f"[Image not available: {e}]", self.normal_style))
                elements.append(Spacer(1, 20))
            else:
                elements.append(Paragraph(f"[Evidence image not found at path: {img_path}]", self.normal_style))
                elements.append(Spacer(1, 20))

        # 5. Fine & Payment
        elements.append(Paragraph("<b>FINE & PAYMENT DETAILS</b>", self.styles['Heading3']))
        payment_data = [
            ["Fine Amount:", f"Rs. {violation.fine_inr}/-"],
            ["Due Date:", due_date.strftime("%Y-%m-%d")],
            ["Status:", "UNPAID"]
        ]
        payment_table = Table(payment_data, colWidths=[120, 380])
        payment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(payment_table)
        elements.append(Spacer(1, 20))

        # 6. Footer / Hash
        if violation.evidence_hash:
            elements.append(Paragraph(f"<font size='8' color='grey'>Evidence Hash: {violation.evidence_hash}</font>", self.normal_style))
        
        elements.append(Paragraph("<font size='8' color='grey'>This is an electronically generated document. No signature is required.</font>", self.normal_style))

        # Build PDF
        try:
            doc.build(elements)
            log.info(f"Generated PDF challan at {pdf_path}")
            return f"/evidence/challans/{pdf_filename}"
        except Exception as e:
            log.error(f"Failed to build PDF challan: {e}")
            raise


generator = ChallanGenerator()


def generate_pdf(challan_number: str, violation: Violation, owner: OwnerInfo, due_date: datetime) -> str:
    return generator.generate(challan_number, violation, owner, due_date)
