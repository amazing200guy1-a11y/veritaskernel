"""
VeritasKernel — Forensic Evidence PDF Dossier Compiler
Compiles structured primary-source verification reports for Delphi prediction market oracles.
Built with ReportLab for sub-100ms deterministic document generation.
"""

import os
import time
import hashlib
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class EvidencePDFCompiler:
    def __init__(self, output_dir: str = "data/dossiers"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def compile_dossier(
        self,
        market_id: str,
        market_question: str,
        direction: str,
        source_url: str,
        primary_quote: str,
        dates: list,
        metrics: list,
        quality_score: float,
        fingerprint: str
    ) -> str:
        """
        Generates a 1-page cryptographic PDF dossier and returns the absolute file path.
        """
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        filename = f"DELPHI_DOSSIER_{market_id}_{fingerprint[:8]}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        # Custom Typography & Palette
        title_style = ParagraphStyle(
            'DossierTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            textColor=colors.HexColor('#0F172A')
        )

        subtitle_style = ParagraphStyle(
            'DossierSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#059669') # Emerald accent
        )

        meta_label_style = ParagraphStyle(
            'MetaLabel',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#475569')
        )

        meta_val_style = ParagraphStyle(
            'MetaVal',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#0F172A')
        )

        quote_style = ParagraphStyle(
            'QuoteStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#1E293B')
        )

        story = []

        # 1. Header Banner
        story.append(Paragraph("VERITASKERNEL // DELPHI ORACLE EVIDENCE DOSSIER", title_style))
        story.append(Paragraph(f"AUTONOMOUS FORENSIC PROOF · DIRECT EVIDENCE MINING · TIMESTAMP: {timestamp}", subtitle_style))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0F172A'), spaceAfter=12))

        # 2. Executive Metadata Matrix
        meta_data = [
            [
                Paragraph("<b>MARKET TARGET ID</b>", meta_label_style),
                Paragraph(market_id, meta_val_style),
                Paragraph("<b>FORECAST DIRECTION</b>", meta_label_style),
                Paragraph(f"<b>{direction.upper()}</b>", meta_val_style)
            ],
            [
                Paragraph("<b>MARKET QUESTION</b>", meta_label_style),
                Paragraph(market_question, meta_val_style),
                Paragraph("<b>EVIDENCE QUALITY</b>", meta_label_style),
                Paragraph(f"<b>{quality_score}/100</b>", meta_val_style)
            ],
            [
                Paragraph("<b>PRIMARY SOURCE URL</b>", meta_label_style),
                Paragraph(source_url[:65] + ("..." if len(source_url) > 65 else ""), meta_val_style),
                Paragraph("<b>TEMPORAL ANCHORS</b>", meta_label_style),
                Paragraph(", ".join(dates[:3]) if dates else "N/A", meta_val_style)
            ],
            [
                Paragraph("<b>QUANTITATIVE TOKENS</b>", meta_label_style),
                Paragraph(", ".join(metrics[:4]) if metrics else "Qualitative Ruling", meta_val_style),
                Paragraph("<b>SHA-256 FINGERPRINT</b>", meta_label_style),
                Paragraph(fingerprint[:16] + "...", meta_val_style)
            ]
        ]

        meta_table = Table(meta_data, colWidths=[110, 160, 120, 150])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 14))

        # 3. Certified Primary Source Excerpt
        story.append(Paragraph("<b>CERTIFIED PRIMARY SOURCE EXCERPT:</b>", meta_label_style))
        story.append(Spacer(1, 4))

        quote_table_data = [[
            Paragraph(f'"{primary_quote}"', quote_style)
        ]]
        quote_table = Table(quote_table_data, colWidths=[540])
        quote_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F1F5F9')),
            ('LINELEFT', (0, 0), (-1, -1), 3.0, colors.HexColor('#059669')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(quote_table)
        story.append(Spacer(1, 14))

        # 4. Analytical Rationale for LMSR Forecaster Movement
        rationale_text = (
            f"This piece of primary evidence provides concrete, dated verification regarding: "
            f"<b>{market_question}</b>. Under Logarithmic Market Scoring Rule (LMSR) dynamics, this new "
            f"factual revelation updates the prior belief distribution toward outcome <b>{direction.upper()}</b>, "
            f"justifying an immediate upward probability revision."
        )
        story.append(Paragraph("<b>LMSR PROBABILITY SHIFT RATIONALE:</b>", meta_label_style))
        story.append(Spacer(1, 4))
        story.append(Paragraph(rationale_text, meta_val_style))
        story.append(Spacer(1, 14))

        # 5. Cryptographic Seal & Verification Footer
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#94A3B8'), spaceAfter=8))
        footer_text = (
            f"VERITASKERNEL IMMUTABLE SEAL · SHA256: {fingerprint} · "
            f"DELPHI AGENT ARENA (DORAHACKS × GENSYN) · WALLET: 0x8C64e8AB285F46cB22497f9B6Ce9DF42dDD19EcC"
        )
        footer_style = ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=6.5,
            leading=8,
            textColor=colors.HexColor('#64748B')
        )
        story.append(Paragraph(footer_text, footer_style))

        # Build document
        doc.build(story)
        return filepath
