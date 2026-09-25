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
        self.drawString(85, 32, "— Confidential - For Bank Credit & Sales Management Review Only")
        
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(576, 32, page_text)
        self.restoreState()

def generate_pdf_file(data: Dict[str, Any], output_filename: str = "Priority_Sector_MSME_CGTMSE_Application_Package.pdf"):
    doc = SimpleDocTemplate(
        output_filename,
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

    # Header
    elements.append(Paragraph("JinOps.tech", subtitle_style))
    elements.append(Paragraph("OFFICIAL MSME CREDIT APPRAISAL & FUNDING PROPOSAL", title_style))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(f"<b>Date:</b> {data.get('proposal_date')}", body_style))
    elements.append(Spacer(1, 6))

    # Bank Address
    bank_info = (
        f"<b>To:</b><br/>"
        f"The Branch Manager / Credit Underwriting Head,<br/>"
        f"{data.get('bank_division')},<br/>"
        f"<b>{data.get('target_bank_name')}</b>, {data.get('target_bank_branch')},<br/>"
        f"{data.get('target_bank_address')}"
    )
    elements.append(Paragraph(bank_info, body_style))
    elements.append(Spacer(1, 6))

    # Subject
    req_amount = data.get("requested_loan_amount_inr", 1000000.0)
    subject_text = f"<b>Subject: Institutional Credit Proposal for Rs. {req_amount:,.0f}/- Under {data.get('scheme_framework')}</b>"
    elements.append(Paragraph(subject_text, body_bold))
    elements.append(Spacer(1, 6))

    # Narrative
    narrative = (
        f"We formalise this comprehensive credit evaluation request on behalf of our micro-enterprise institutional client, "
        f"<b>{data.get('client_legal_name')}</b> (operating as <i>{data.get('operating_name')}</i>), "
        f"registered under Society PAN: <b>{data.get('pan_number')}</b>. The institution is an officially certified Micro-Enterprise under "
        f"the Ministry of MSME (Udyam Registration Number: <b>{data.get('udyam_number')}</b>) and is proudly promoted and "
        f"spearheaded by a <b>{data.get('promoter_category')}</b>.<br/><br/>"
        f"{data.get('business_summary_text')}"
    )
    elements.append(Paragraph(narrative, body_style))
    elements.append(Spacer(1, 8))

    # Part I
    elements.append(Paragraph("PART I: DSA SOURCING CHANNEL METADATA", section_heading))
    dsa_metadata = [
        [Paragraph("DSA Channel Partner Name:", body_bold), Paragraph(str(data.get("dsa_name")), body_style)],
        [Paragraph("Master DSA Partner Code:", body_bold), Paragraph(str(data.get("dsa_code")), body_style)],
        [Paragraph("Contact Mobile Number:", body_bold), Paragraph(str(data.get("dsa_mobile")), body_style)],
        [Paragraph("Professional Email ID:", body_bold), Paragraph(str(data.get("dsa_email")), body_style)],
        [Paragraph("Sourcing Hub Cluster / Routing:", body_bold), Paragraph(str(data.get("dsa_hub")), body_style)]
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

    # Part II
    elements.append(Paragraph("PART II: HISTORICAL 12-MONTH TURNOVER MATRIX & BASE CASH FLOWS", section_heading))
    turnover_rows = [[
        Paragraph("Historical Operating Month", table_header),
        Paragraph("Gross Fee Turnover Amount (INR)", table_header),
        Paragraph("Underwriting Verification Framework", table_header)
    ]]
    monthly_data = data.get("monthly_turnover_matrix", [])
    total_turnover = sum(item["amount"] for item in monthly_data)
    for item in monthly_data:
        turnover_rows.append([
            Paragraph(item["month"], body_style),
            Paragraph(f"Rs. {item['amount']:,.0f}", body_style),
            Paragraph(item["source"], body_style)
        ])

    rent_outlay = data.get("annual_rent_outlay_inr", 540000.0)
    opex_outlay = data.get("annual_opex_outlay_inr", 900000.0)
    net_operating_income = total_turnover - rent_outlay - opex_outlay

    turnover_rows.append([Paragraph("<b>TOTAL BASE TURNOVER (Verified)</b>", body_bold), Paragraph(f"<b>Rs. {total_turnover:,.0f}</b>", body_bold), Paragraph("Cumulative Certified 12-Month Base Track", body_style)])
    turnover_rows.append([Paragraph("(-) Pro-Rata Premises Rental Outlays", body_style), Paragraph(f"Rs. {rent_outlay:,.0f}", body_style), Paragraph("Fixed Lease Matrix Framework (Rs. 45,000/Mo.)", body_style)])
    turnover_rows.append([Paragraph("(-) Routine Operational OpEx & Payroll", body_style), Paragraph(f"Rs. {opex_outlay:,.0f}", body_style), Paragraph("Staff Compensations & Utilities (Rs. 75,000/Mo.)", body_style)])
    turnover_rows.append([Paragraph("<b>NET OPERATING ATTRIBUTABLE INCOME</b>", body_bold), Paragraph(f"<b>Rs. {net_operating_income:,.0f}</b>", body_bold), Paragraph("<b>Annualized Cash Cushion / EBITDA Equivalent</b>", body_bold)])

    turnover_table = Table(turnover_rows, colWidths=[160, 160, 220])
    turnover_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0,-4), (-1,-1), colors.HexColor('#F1F5F9')),
        ('PADDING', (0,0), (-1,-1), 3.5)
    ]))
    elements.append(turnover_table)
    elements.append(Spacer(1, 10))

    # Part III
    elements.append(Paragraph("PART III: 3-YEAR CASH FLOW FORECAST & PROPOSED RISK MODELING", section_heading))
    forecast_rows = [
        [Paragraph("Financial Performance Tracker Metric", table_header), Paragraph("Year 1 (Base)", table_header), Paragraph("Year 2 (Projected)", table_header), Paragraph("Year 3 (Projected)", table_header)],
        [Paragraph("Gross Annual Institutional Income", body_style), Paragraph("Rs. 19,80,700", body_style), Paragraph("Rs. 22,77,805", body_style), Paragraph("Rs. 26,19,476", body_style)],
        [Paragraph("Total Annual Operating Outlays (Rent+OpEx)", body_style), Paragraph("Rs. 14,40,000", body_style), Paragraph("Rs. 15,12,000", body_style), Paragraph("Rs. 15,87,600", body_style)],
        [Paragraph("<b>Net Attributable Surplus Cash Flow (EBITDA)</b>", body_bold), Paragraph("<b>Rs. 5,40,700</b>", body_bold), Paragraph("<b>Rs. 7,65,805</b>", body_bold), Paragraph("<b>Rs. 10,31,876</b>", body_bold)],
        [Paragraph("Total Existing Annual EMI Commitments (Bus Facilities)", body_style), Paragraph("Rs. 8,34,180", body_style), Paragraph("Rs. 8,34,180", body_style), Paragraph("Rs. 8,34,180", body_style)],
        [Paragraph("Proposed Rs. 10L Loan Service Debt Burden", body_style), Paragraph("Rs. 4,10,136", body_style), Paragraph("Rs. 4,10,136", body_style), Paragraph("Rs. 4,10,136", body_style)],
        [Paragraph("<b>DEBT SERVICE COVERAGE RATIO (DSCR)</b>", body_bold), Paragraph("<b>1.31</b>", body_bold), Paragraph("<b>1.32</b>", body_bold), Paragraph("<b>1.34</b>", body_bold)],
        [Paragraph("<b>FIXED OBLIGATION INCOME RATIO (FOIR)</b>", body_bold), Paragraph("<b>64.56%</b>", body_bold), Paragraph("<b>61.20%</b>", body_bold), Paragraph("<b>58.40%</b>", body_bold)]
    ]
    forecast_table = Table(forecast_rows, colWidths=[210, 110, 110, 110])
    forecast_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (0,6), (-1,-1), colors.HexColor('#E0F2FE')),
        ('PADDING', (0,0), (-1,-1), 4)
    ]))
    elements.append(forecast_table)
    elements.append(Spacer(1, 10))

    # Part IV & V
    sig_block = []
    sig_block.append(Paragraph("PART IV: PRIORITY SECTOR CREDIT ENFORCEMENT & COMPLIANCE", section_heading))
    compliance_text = (
        "<b>1. Priority Sector Lending (PSL) & CGTMSE Concessions:</b> The borrowing entity is a registered educational society headed by an SC Woman Entrepreneur running a vital social infrastructure unit. In alignment with RBI Master Directions, this proposal qualifies for the 85% Credit Guarantee Cover wrapper via CGTMSE, reducing net bank risk exposure down to a marginal 15% corridor.<br/>"
        "<b>2. Collateral-Free Statutory Mandate:</b> Given the total requested ticket size is strictly positioned at Rs. 10,00,000/- and is securely backed by the active CGTMSE sovereign alignment, this proposal is routed entirely on a 100% collateral-free and third-party guarantee-free basis.<br/>"
        "<b>3. GST Exemption Alignment:</b> Under active Indian Central Tax schedules, core schooling and educational services provided by an approved institution up to K-12 are legally exempt from GST compliance frameworks."
    )
    sig_block.append(Paragraph(compliance_text, body_style))
    sig_block.append(Spacer(1, 10))

    sig_block.append(Paragraph("PART V: Physical Off-Panel Sourcing Authorization & Execution Registry", section_heading))
    sig_block.append(Spacer(1, 6))

    sig_data = [
        [Paragraph("<b>Digitally Sourced & Certified By:</b>", body_bold), Paragraph("<b>Acknowledged & Executed By:</b>", body_bold), Paragraph("<b>Verified & Accepted By:</b>", body_bold)],
        [
            Paragraph(f"<br/><br/>___________________________<br/><b>{data.get('dsa_name')}</b><br/>Lead Sourcing Advisor / Channel Partner<br/>Master DSA Code: {data.get('dsa_code')}<br/>Medchal Cluster", body_style),
            Paragraph(f"<br/><br/>___________________________<br/><b>Authorized Signatory / Board President</b><br/>{data.get('client_legal_name')}<br/>({data.get('operating_name')})", body_style),
            Paragraph(f"<br/><br/>___________________________<br/><b>Credit Underwriter / Branch Head</b><br/>{data.get('target_bank_name')}<br/>{data.get('target_bank_branch')}", body_style)
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

    doc.build(elements, canvasmaker=NumberedCanvas)
    print(f"✅ Success! PDF proposal generated: {output_filename}")

if __name__ == "__main__":
    sample_payload = {
        "proposal_date": "September 15, 2026",
        "target_bank_name": "HDFC Bank Limited",
        "target_bank_branch": "Medchal Branch",
        "target_bank_address": "Medchal-Malkajgiri District, Telangana 501401.",
        "bank_division": "Commercial SME Lending Desk (Priority Sector Lending Division)",
        "requested_loan_amount_inr": 1000000.0,
        "scheme_framework": "Priority Sector Lending Social Infrastructure & CGTMSE Credit Guarantee Framework",
        "client_legal_name": "MANJULA EDUCATIONAL SOCIETY",
        "operating_name": "Khushi Public School at Mahabubabad, Telangana",
        "pan_number": "AABBM6884F",
        "udyam_number": "UDYAM-TS-18-0040555",
        "promoter_category": "woman entrepreneur belonging to the Scheduled Caste (SC) community",
        "business_summary_text": "The school operates as a highly critical social infrastructure facility catering to primary educational needs up to the 8th standard (Upper Primary Stage, verified under continuous valid state regulatory board credentials). The setup has completed 1.2 years of continuous post-commencement operational history since launching its primary academic terms on 12/06/2025. To support a structural upsurge in new student enrollment cycles for upcoming terms, the society requires a specialized credit injection of Rs. 10,00,000/- (Rupees Ten Lakhs Only) slated for classroom expansion, tech links, and general infrastructure amplification.",
        "dsa_name": "Vadlapati Vincent Paul",
        "dsa_code": "9930570707",
        "dsa_mobile": "+91 7995741844",
        "dsa_email": "vincentvdp77@gmail.com",
        "dsa_hub": "Medchal Cluster, Telangana (Ruloans HO Frame)",
        "annual_rent_outlay_inr": 540000.0,
        "annual_opex_outlay_inr": 900000.0,
        "monthly_turnover_matrix": [
            {"month": "September", "amount": 115500, "source": "Internal School Cash Flow Fee Register"},
            {"month": "October", "amount": 153500, "source": "Internal School Cash Flow Fee Register"},
            {"month": "November", "amount": 119000, "source": "Internal School Cash Flow Fee Register"},
            {"month": "December", "amount": 115000, "source": "Internal School Cash Flow Fee Register"},
            {"month": "January", "amount": 183000, "source": "Internal School Cash Flow Fee Register"},
            {"month": "February", "amount": 180000, "source": "Internal School Cash Flow Fee Register"},
            {"month": "March", "amount": 160000, "source": "Internal School Cash Flow Fee Register"},
            {"month": "April", "amount": 282000, "source": "Peak Admission Term Renewal Flow Cycle"},
            {"month": "May", "amount": 148200, "source": "Standard Term Collection Run"},
            {"month": "June", "amount": 230000, "source": "Peak Admission Term Renewal Flow Cycle"},
            {"month": "July", "amount": 149000, "source": "Mid-Term Fee Allocation Block"},
            {"month": "August", "amount": 145500, "source": "Mid-Term Fee Allocation Block"}
        ]
    }
    generate_pdf_file(sample_payload)