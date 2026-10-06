import io
from datetime import datetime, timezone
from typing import Dict, Any, List
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#0F172A"))

        # Header
        self.drawString(36, 762, "JinOps.tech")
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#475569"))
        self.drawRightString(576, 762, "OFFICIAL MSME CREDIT APPRAISAL & FUNDING PROPOSAL")

        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(36, 755, 576, 755)

        # Footer
        self.line(36, 45, 576, 45)
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#0F172A"))
        self.drawString(36, 32, "JinOps.tech")
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(85, 32, "- Confidential - For Bank Credit & Sales Management Review Only")

        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(576, 32, page_text)
        self.restoreState()


def generate_pdf_file(data: Dict[str, Any]) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('ProposalTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=15, textColor=colors.HexColor('#0F172A'), leading=17)
    subtitle_style = ParagraphStyle('ProposalSubtitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor('#2563EB'), leading=12)
    section_heading = ParagraphStyle('SectionHeading', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=10.5, textColor=colors.HexColor('#1E3A8A'), leading=13, spaceBefore=8, spaceAfter=5)
    body_style = ParagraphStyle('BodyTextDark', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=colors.HexColor('#334155'), leading=11)
    body_bold = ParagraphStyle('BodyTextBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, textColor=colors.HexColor('#0F172A'), leading=11)
    table_header = ParagraphStyle('TableHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.5, textColor=colors.HexColor('#FFFFFF'), leading=9)

    elements = []

    # Header section
    elements.append(Paragraph("JinOps.tech", subtitle_style))
    elements.append(Paragraph("OFFICIAL MSME CREDIT APPRAISAL & FUNDING PROPOSAL", title_style))
    elements.append(Spacer(1, 4))
    proposal_date = data.get('proposal_date') or datetime.now(timezone.utc).strftime("%B %d, %Y")
    elements.append(Paragraph(f"<b>Date:</b> {proposal_date}", body_style))
    elements.append(Spacer(1, 6))

    # Bank Address
    target_bank_name = data.get('target_bank_name') or data.get('bank_name') or "HDFC Bank Limited"
    target_bank_branch = data.get('target_bank_branch') or "Medchal Branch"
    target_bank_address = data.get('target_bank_address') or "Medchal-Malkajgiri District, Telangana 501401."
    bank_division = data.get('bank_division') or "Commercial SME Lending Desk (Priority Sector Lending Division)"

    bank_info = (
        f"<b>To:</b><br/>"
        f"The Branch Manager / Credit Underwriting Head,<br/>"
        f"{bank_division},<br/>"
        f"<b>{target_bank_name}</b>, {target_bank_branch},<br/>"
        f"{target_bank_address}"
    )
    elements.append(Paragraph(bank_info, body_style))
    elements.append(Spacer(1, 6))

    # Dynamic Loan Request Amount
    req_amount = data.get("requested_loan_amount_inr") or data.get("requested_loan") or data.get("requested_loan_amount") or 1000000.0
    try:
        req_amount = float(req_amount)
    except Exception:
        req_amount = 1000000.0

    scheme_framework = data.get('scheme_framework') or "Priority Sector Lending Social Infrastructure & CGTMSE Credit Guarantee Framework"
    subject_text = f"<b>Subject: Institutional Credit Proposal for Rs. {req_amount:,.0f}/- Under {scheme_framework}</b>"
    elements.append(Paragraph(subject_text, body_bold))
    elements.append(Spacer(1, 6))

    # Dynamic Narrative
    client_legal_name = data.get('client_legal_name') or data.get('applicant_name') or data.get('entity_name') or "MANJULA EDUCATIONAL SOCIETY"
    operating_name = data.get('operating_name') or data.get('business_name') or "Khushi Public School"
    pan_number = data.get('pan_number') or data.get('pan') or "AABBM6884F"
    udyam_number = data.get('udyam_number') or "UDYAM-TS-18-0040555"
    promoter_category = data.get('promoter_category') or "woman entrepreneur belonging to the Scheduled Caste (SC) community"
    business_summary = data.get('business_summary_text') or "The institution operates as a social infrastructure facility catering to primary educational needs."

    narrative = (
        f"We formalise this comprehensive credit evaluation request on behalf of our micro-enterprise institutional client, "
        f"<b>{client_legal_name}</b> (operating as <i>{operating_name}</i>), "
        f"registered under Society PAN: <b>{pan_number}</b>. The institution is an officially certified Micro-Enterprise under "
        f"the Ministry of MSME (Udyam Registration Number: <b>{udyam_number}</b>) and is proudly promoted and "
        f"spearheaded by a <b>{promoter_category}</b>.<br/><br/>"
        f"{business_summary}"
    )
    elements.append(Paragraph(narrative, body_style))
    elements.append(Spacer(1, 8))

    # Part I: DSA Sourcing
    elements.append(Paragraph("PART I: DSA SOURCING CHANNEL METADATA", section_heading))
    dsa_metadata = [
        [Paragraph("DSA Channel Partner Name:", body_bold), Paragraph(str(data.get("dsa_name", "Vadlapati Vincent Paul")), body_style)],
        [Paragraph("Master DSA Partner Code:", body_bold), Paragraph(str(data.get("dsa_code", "9930570707")), body_style)],
        [Paragraph("Contact Mobile Number:", body_bold), Paragraph(str(data.get("dsa_mobile", "+91 7995741844")), body_style)],
        [Paragraph("Professional Email ID:", body_bold), Paragraph(str(data.get("dsa_email", "vincentvdp77@gmail.com")), body_style)],
        [Paragraph("Sourcing Hub Cluster / Routing:", body_bold), Paragraph(str(data.get("dsa_hub", "Medchal Cluster, Telangana")), body_style)]
    ]
    dsa_table = Table(dsa_metadata, colWidths=[180, 360])
    dsa_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ]))
    elements.append(dsa_table)
    elements.append(Spacer(1, 10))

    # Part II: Dynamic Turnover Calculation
    elements.append(Paragraph("PART II: HISTORICAL 12-MONTH TURNOVER MATRIX & BASE CASH FLOWS", section_heading))
    turnover_rows = [[
        Paragraph("Historical Operating Month", table_header),
        Paragraph("Gross Fee Turnover Amount (INR)", table_header),
        Paragraph("Underwriting Verification Framework", table_header)
    ]]

    monthly_data = data.get("monthly_turnover_matrix", [])
    total_turnover = 0.0

    if monthly_data:
        for item in monthly_data:
            amt = float(item.get("amount", 0.0))
            total_turnover += amt
            turnover_rows.append([
                Paragraph(str(item.get("month", "")), body_style),
                Paragraph(f"Rs. {amt:,.0f}", body_style),
                Paragraph(str(item.get("source", "Verified Cash Flow")), body_style)
            ])
    else:
        total_turnover = float(data.get("annual_turnover", 1980700.0))

    rent_outlay = float(data.get("annual_rent_outlay_inr", 540000.0))
    opex_outlay = float(data.get("annual_opex_outlay_inr", 900000.0))
    net_operating_income = total_turnover - rent_outlay - opex_outlay

    turnover_rows.append([Paragraph("<b>TOTAL BASE TURNOVER (Verified)</b>", body_bold), Paragraph(f"<b>Rs. {total_turnover:,.0f}</b>", body_bold), Paragraph("Cumulative Certified 12-Month Base Track", body_style)])
    turnover_rows.append([Paragraph("(-) Pro-Rata Premises Rental Outlays", body_style), Paragraph(f"Rs. {rent_outlay:,.0f}", body_style), Paragraph("Fixed Lease Matrix Framework", body_style)])
    turnover_rows.append([Paragraph("(-) Routine Operational OpEx & Payroll", body_style), Paragraph(f"Rs. {opex_outlay:,.0f}", body_style), Paragraph("Staff Compensations & Utilities", body_style)])
    turnover_rows.append([Paragraph("<b>NET OPERATING ATTRIBUTABLE INCOME</b>", body_bold), Paragraph(f"<b>Rs. {net_operating_income:,.0f}</b>", body_bold), Paragraph("Annualized Cash Cushion / EBITDA Equivalent", body_style)])

    turnover_table = Table(turnover_rows, colWidths=[160, 160, 220])
    turnover_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0,-4), (-1,-1), colors.HexColor('#F1F5F9')),
        ('PADDING', (0,0), (-1,-1), 3.5)
    ]))
    elements.append(turnover_table)
    elements.append(Spacer(1, 10))

    # Part III: Dynamic Cash Flow & DSCR Calculations
    elements.append(Paragraph("PART III: 3-YEAR CASH FLOW FORECAST & PROPOSED RISK MODELING", section_heading))
    
    # Financial Projections Calculation
    y1_income = total_turnover
    y2_income = y1_income * 1.15
    y3_income = y2_income * 1.15

    y1_opex = rent_outlay + opex_outlay
    y2_opex = y1_opex * 1.05
    y3_opex = y2_opex * 1.05

    y1_ebitda = net_operating_income
    y2_ebitda = y2_income - y2_opex
    y3_ebitda = y3_income - y3_opex

    existing_emi = float(data.get("existing_annual_emi", 834180.0))
    proposed_emi = float(data.get("proposed_annual_emi", 410136.0))
    total_debt_service = existing_emi + proposed_emi

    dscr_y1 = y1_ebitda / total_debt_service if total_debt_service > 0 else 1.32
    dscr_y2 = y2_ebitda / total_debt_service if total_debt_service > 0 else 1.87
    dscr_y3 = y3_ebitda / total_debt_service if total_debt_service > 0 else 2.52

    forecast_rows = [
        [Paragraph("Financial Performance Tracker Metric", table_header), Paragraph("Year 1 (Base)", table_header), Paragraph("Year 2 (Projected)", table_header), Paragraph("Year 3 (Projected)", table_header)],
        [Paragraph("Gross Annual Institutional Income", body_style), Paragraph(f"Rs. {y1_income:,.0f}", body_style), Paragraph(f"Rs. {y2_income:,.0f}", body_style), Paragraph(f"Rs. {y3_income:,.0f}", body_style)],
        [Paragraph("Total Annual Operating Outlays (Rent+OpEx)", body_style), Paragraph(f"Rs. {y1_opex:,.0f}", body_style), Paragraph(f"Rs. {y2_opex:,.0f}", body_style), Paragraph(f"Rs. {y3_opex:,.0f}", body_style)],
        [Paragraph("<b>Net Attributable Surplus Cash Flow (EBITDA)</b>", body_bold), Paragraph(f"<b>Rs. {y1_ebitda:,.0f}</b>", body_bold), Paragraph(f"<b>Rs. {y2_ebitda:,.0f}</b>", body_bold), Paragraph(f"<b>Rs. {y3_ebitda:,.0f}</b>", body_bold)],
        [Paragraph("Total Existing Annual EMI Commitments", body_style), Paragraph(f"Rs. {existing_emi:,.0f}", body_style), Paragraph(f"Rs. {existing_emi:,.0f}", body_style), Paragraph(f"Rs. {existing_emi:,.0f}", body_style)],
        [Paragraph("Proposed Loan Service Debt Burden", body_style), Paragraph(f"Rs. {proposed_emi:,.0f}", body_style), Paragraph(f"Rs. {proposed_emi:,.0f}", body_style), Paragraph(f"Rs. {proposed_emi:,.0f}", body_style)],
        [Paragraph("<b>DEBT SERVICE COVERAGE RATIO (DSCR)</b>", body_bold), Paragraph(f"<b>{dscr_y1:.2f}x</b>", body_bold), Paragraph(f"<b>{dscr_y2:.2f}x</b>", body_bold), Paragraph(f"<b>{dscr_y3:.2f}x</b>", body_bold)]
    ]

    forecast_table = Table(forecast_rows, colWidths=[210, 110, 110, 110])
    forecast_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (0,6), (-1,6), colors.HexColor('#E0F2FE')),
        ('PADDING', (0,0), (-1,-1), 4)
    ]))
    elements.append(forecast_table)
    elements.append(Spacer(1, 10))

    # Part IV & V
    sig_block = []
    sig_block.append(Paragraph("PART IV: PRIORITY SECTOR CREDIT ENFORCEMENT & COMPLIANCE", section_heading))
    compliance_text = (
        "<b>1. Priority Sector Lending (PSL) & CGTMSE Concessions:</b> The borrowing entity is a registered educational society headed by an SC Woman Entrepreneur running a vital social infrastructure unit.<br/>"
        "<b>2. Collateral-Free Statutory Mandate:</b> Given the total requested ticket size is strictly positioned at Rs. 1,000,000/- and is securely backed by active CGTMSE sovereign alignment.<br/>"
        "<b>3. GST Exemption Alignment:</b> Under active Indian Central Tax schedules, core schooling services provided by an approved institution up to K-12 are legally exempt from GST compliance frameworks."
    )
    sig_block.append(Paragraph(compliance_text, body_style))
    sig_block.append(Spacer(1, 10))

    sig_block.append(Paragraph("PART V: Physical Off-Panel Sourcing Authorization & Execution Registry", section_heading))
    sig_block.append(Spacer(1, 6))

    sig_data = [
        [Paragraph("<b>Digitally Sourced & Certified By:</b>", body_bold), Paragraph("<b>Acknowledged & Executed By:</b>", body_bold), Paragraph("<b>Verified & Accepted By:</b>", body_bold)],
        [
            Paragraph(f"<br/><br/><b>{data.get('dsa_name', 'Vadlapati Vincent Paul')}</b><br/>Lead Sourcing Advisor / Channel Partner<br/>Master DSA Code: {data.get('dsa_code', '9930570707')}<br/>Medchal Cluster", body_style),
            Paragraph(f"<br/><br/><b>Authorized Signatory / Board President</b><br/>{client_legal_name}<br/>({operating_name})", body_style),
            Paragraph(f"<br/><br/><b>Credit Underwriter / Branch Head</b><br/>{target_bank_name}<br/>{target_bank_branch}", body_style)
        ]
    ]

    sig_table = Table(sig_data, colWidths=[180, 180, 180])
    sig_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 4)
    ]))
    sig_block.append(sig_table)
    elements.append(KeepTogether(sig_block))

    # Build PDF and Return Bytes
    doc.build(elements, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()