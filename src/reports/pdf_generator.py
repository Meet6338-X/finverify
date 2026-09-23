import io
from typing import Optional, List, Dict
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

class CertificatePDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = self.styles['Heading1']
        self.title_style.alignment = 1 # Center
        self.normal_style = self.styles['Normal']
        self.subtitle_style = self.styles['Heading2']
        
    def _get_status_color(self, status: str):
        s = str(status).upper()
        if s == "PASS":
            return colors.green
        elif s in ("PASS_WITH_WARNING", "WARNING"):
            return colors.orange
        elif s == "FAIL":
            return colors.red
        else:
            return colors.gray

    def generate_claim_certificate(self, certificate: dict, qr_code_path: Optional[str] = None) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        # Header
        elements.append(Paragraph("FinVerify Verification Certificate", self.title_style))
        elements.append(Spacer(1, 12))
        
        # Status Badge
        status = certificate.get("status", "UNVERIFIABLE")
        status_color = self._get_status_color(status)
        status_style = ParagraphStyle(
            'Status', parent=self.normal_style,
            textColor=status_color, fontSize=14, fontName='Helvetica-Bold', alignment=1
        )
        elements.append(Paragraph(f"Status: {status}", status_style))
        elements.append(Spacer(1, 20))
        
        # Claim Details Table
        details_data = [
            ["Claim ID", str(certificate.get("claim_id", ""))],
            ["Expected Value", str(certificate.get("expected_value", ""))],
            ["Computed Value", str(certificate.get("computed_value", ""))],
            ["Relative Error", str(certificate.get("relative_error", ""))]
        ]
        
        details_table = Table(details_data, colWidths=[150, 300])
        details_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(Paragraph("Claim Details", self.subtitle_style))
        elements.append(Spacer(1, 6))
        elements.append(details_table)
        elements.append(Spacer(1, 20))
        
        # Discrepancy Trace
        trace = certificate.get("discrepancy_trace", [])
        if trace:
            elements.append(Paragraph("Computation Trace", self.subtitle_style))
            elements.append(Spacer(1, 6))
            
            trace_data = [["Step", "Formula", "Computed", "Source"]]
            for step in trace:
                trace_data.append([
                    str(step.get("step_name", "")),
                    str(step.get("formula", "")),
                    str(step.get("computed_value", "")),
                    str(step.get("source_reference", ""))
                ])
                
            trace_table = Table(trace_data, colWidths=[100, 150, 100, 100])
            trace_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(trace_table)
            elements.append(Spacer(1, 20))
            
        # Source References
        refs = certificate.get("source_refs", [])
        if refs:
            elements.append(Paragraph("Source References", self.subtitle_style))
            elements.append(Spacer(1, 6))
            for ref in refs:
                elements.append(Paragraph(f"- {ref}", self.normal_style))
            elements.append(Spacer(1, 20))
            
        # Timestamp and Signature
        timestamp = certificate.get("timestamp", "")
        signature = certificate.get("signature", "")
        sig_trunc = signature[:16] + "..." if signature else "N/A"
        
        elements.append(Paragraph(f"Timestamp: {timestamp}", self.normal_style))
        elements.append(Paragraph(f"Signature: {sig_trunc}", self.normal_style))
        elements.append(Spacer(1, 20))
        
        # QR Code
        if qr_code_path:
            try:
                img = Image(qr_code_path, width=100, height=100)
                elements.append(img)
                elements.append(Spacer(1, 20))
            except Exception:
                pass
                
        # Footer
        footer_style = ParagraphStyle(
            'Footer', parent=self.normal_style,
            textColor=colors.grey, fontSize=8, alignment=1
        )
        elements.append(Paragraph("Generated by FinVerify - Tamper-Evident Verification System", footer_style))
        
        doc.build(elements)
        return buffer.getvalue()

    def generate_report_summary(self, report: dict, certificates: List[dict]) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        # Title
        title = report.get("title", "Report Summary")
        elements.append(Paragraph(title, self.title_style))
        elements.append(Spacer(1, 12))
        
        # Aggregate stats
        total = len(certificates)
        passed = sum(1 for c in certificates if str(c.get("status", "")).upper() == "PASS")
        warnings = sum(1 for c in certificates if str(c.get("status", "")).upper() in ("PASS_WITH_WARNING", "WARNING"))
        failed = sum(1 for c in certificates if str(c.get("status", "")).upper() == "FAIL")
        unverifiable = sum(1 for c in certificates if str(c.get("status", "")).upper() == "UNVERIFIABLE")
        
        stats_data = [
            ["Metric", "Count"],
            ["Total Claims", str(total)],
            ["Pass", str(passed)],
            ["Pass with Warning", str(warnings)],
            ["Fail", str(failed)],
            ["Unverifiable", str(unverifiable)]
        ]
        
        stats_table = Table(stats_data, colWidths=[200, 100])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(Paragraph("Aggregate Statistics", self.subtitle_style))
        elements.append(Spacer(1, 6))
        elements.append(stats_table)
        elements.append(Spacer(1, 20))
        
        # Per-claim summary
        elements.append(Paragraph("Claims Summary", self.subtitle_style))
        elements.append(Spacer(1, 6))
        
        claims_data = [["Claim ID", "Status", "Expected", "Computed"]]
        for cert in certificates:
            claims_data.append([
                str(cert.get("claim_id", "")),
                str(cert.get("status", "")),
                str(cert.get("expected_value", "")),
                str(cert.get("computed_value", ""))
            ])
            
        claims_table = Table(claims_data, colWidths=[100, 120, 100, 100])
        claims_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(claims_table)
        
        doc.build(elements)
        return buffer.getvalue()
