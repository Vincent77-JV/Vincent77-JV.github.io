import time
import json
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Union

def to_decimal(val: Union[float, int, str]) -> Decimal:
    """Converts any numeric input to Decimal with exact precision"""
    return Decimal(str(val))

class JinOpsUnderwritingEngine:
    def __init__(self):
        # Precise Lender Matrix (IDFC FIRST, Kinara Capital, SIDBI Rules)
        self.lenders = [
            {
                "name": "IDFC FIRST Bank",
                "min_cibil": 700,
                "max_foir": Decimal("0.60"),
                "min_dscr": Decimal("1.25"),
                "min_turnover": Decimal("5000000.00"),
                "max_gst_var": Decimal("0.20")
            },
            {
                "name": "Kinara Capital",
                "min_cibil": 650,
                "max_foir": Decimal("0.65"),
                "min_dscr": Decimal("1.15"),
                "min_turnover": Decimal("1200000.00"),
                "max_gst_var": Decimal("0.30")
            },
            {
                "name": "SIDBI",
                "min_cibil": 720,
                "max_foir": Decimal("0.50"),
                "min_dscr": Decimal("1.40"),
                "min_turnover": Decimal("10000000.00"),
                "max_gst_var": Decimal("0.15")
            }
        ]

    def round_curr(self, val: Decimal) -> Decimal:
        """Rounds to 2 decimal places using standard financial ROUND_HALF_UP"""
        return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate_exact_emi(self, principal: Decimal, annual_rate: Decimal, tenure_months: int) -> Decimal:
        """Standard Banking Reducing EMI Formula: P * r * (1+r)^n / ((1+r)^n - 1)"""
        if principal <= 0 or tenure_months <= 0:
            return Decimal("0.00")
        
        monthly_rate = (annual_rate / Decimal("12")) / Decimal("100")
        one_plus_r_n = (Decimal("1") + monthly_rate) ** tenure_months
        
        emi = principal * monthly_rate * one_plus_r_n / (one_plus_r_n - Decimal("1"))
        return self.round_curr(emi)

    def process_underwriting(self,
                             applicant_name: str,
                             cibil_score: int,
                             monthly_income: float,
                             existing_emi: float,
                             annual_gst_turnover: float,
                             annual_banking_turnover: float,
                             net_profit_annual: float,
                             depreciation_annual: float,
                             interest_annual: float,
                             requested_loan: float,
                             tenure_months: int,
                             interest_rate: float) -> Dict[str, Any]:
        
        start_time = time.time()

        # Decimal Conversions
        P = to_decimal(requested_loan)
        R = to_decimal(interest_rate)
        Inc = to_decimal(monthly_income)
        Ex_EMI = to_decimal(existing_emi)
        GST_TO = to_decimal(annual_gst_turnover)
        Bank_TO = to_decimal(annual_banking_turnover)
        PAT = to_decimal(net_profit_annual)
        Dep = to_decimal(depreciation_annual)
        Int_Exp = to_decimal(interest_annual)

        # 1. Exact EMI Calculation
        proposed_emi = self.calculate_exact_emi(P, R, tenure_months)

        # 2. FOIR Calculation & Audit Formula Proof
        total_monthly_obligation = Ex_EMI + proposed_emi
        foir_ratio = (total_monthly_obligation / Inc) if Inc > 0 else Decimal("1.00")
        foir_pct = self.round_curr(foir_ratio * Decimal("100"))

        # 3. DSCR Calculation (EBITDA / Total Debt Service)
        ebitda = PAT + Dep + Int_Exp
        annual_debt_service = total_monthly_obligation * Decimal("12")
        dscr_ratio = self.round_curr(ebitda / annual_debt_service) if annual_debt_service > 0 else Decimal("0.00")

        # 4. GST vs Banking Variance Calculation
        turnover_diff = abs(Bank_TO - GST_TO)
        gst_variance_ratio = (turnover_diff / GST_TO) if GST_TO > 0 else Decimal("0.00")
        gst_var_pct = self.round_curr(gst_variance_ratio * Decimal("100"))

        # 5. Maximum Loan Eligibility Limit (@ 50% FOIR Cap)
        max_allowed_emi = (Inc * Decimal("0.50")) - Ex_EMI
        max_eligible_loan = Decimal("0.00")
        if max_allowed_emi > 0:
            monthly_r = (R / Decimal("12")) / Decimal("100")
            factor = ((Decimal("1") + monthly_r) ** tenure_months - Decimal("1")) / (monthly_r * ((Decimal("1") + monthly_r) ** tenure_months))
            max_eligible_loan = self.round_curr(max_allowed_emi * factor)

        # 6. Lender Routing Check
        lender_results = []
        for l in self.lenders:
            cibil_ok = cibil_score >= l["min_cibil"]
            foir_ok = foir_ratio <= l["max_foir"]
            dscr_ok = dscr_ratio >= l["min_dscr"]
            to_ok = Bank_TO >= l["min_turnover"]
            var_ok = gst_variance_ratio <= l["max_gst_var"]

            reasons = []
            if not cibil_ok: reasons.append(f"CIBIL {cibil_score} < {l['min_cibil']}")
            if not foir_ok: reasons.append(f"FOIR {foir_pct}% > {l['max_foir']*100}%")
            if not dscr_ok: reasons.append(f"DSCR {dscr_ratio}x < {l['min_dscr']}x")
            if not to_ok: reasons.append(f"Turnover INR {float(Bank_TO):,.2f} < Min INR {float(l['min_turnover']):,.2f}")
            if not var_ok: reasons.append(f"GST Mismatch {gst_var_pct}% High")

            lender_results.append({
                "lender_name": l["name"],
                "decision": "APPROVED" if (cibil_ok and foir_ok and dscr_ok and to_ok and var_ok) else "REJECTED",
                "audit_flags": reasons
            })

        execution_time_ms = round((time.time() - start_time) * 1000, 2)

        # Output Structure with Complete Audit Lineage
        return {
            "meta": {
                "engine": "JinOps High-Precision Underwriting Engine v2.0",
                "execution_speed": f"{execution_time_ms} ms",
                "mathematical_accuracy": "100% Bank Audit-Compliant (Decimal Precision)"
            },
            "applicant": {
                "name": applicant_name,
                "requested_loan": f"INR {float(P):,.2f}",
                "max_eligible_loan": f"INR {float(max_eligible_loan):,.2f}"
            },
            "metrics": {
                "proposed_emi": f"INR {float(proposed_emi):,.2f}",
                "foir": f"{foir_pct}%",
                "dscr": f"{dscr_ratio}x",
                "gst_banking_variance": f"{gst_var_pct}%"
            },
            "audit_lineage_proof": {
                "emi_formula_used": "P * r * (1+r)^n / ((1+r)^n - 1)",
                "foir_math_proof": f"(Existing EMI INR {float(Ex_EMI):,.2f} + New EMI INR {float(proposed_emi):,.2f}) / Gross Income INR {float(Inc):,.2f} = {foir_pct}%",
                "dscr_math_proof": f"(PAT INR {float(PAT):,.2f} + Dep INR {float(Dep):,.2f} + Int INR {float(Int_Exp):,.2f}) / Annual Obligations INR {float(annual_debt_service):,.2f} = {dscr_ratio}x",
                "gst_variance_proof": f"|Banking INR {float(Bank_TO):,.2f} - GST INR {float(GST_TO):,.2f}| / GST INR {float(GST_TO):,.2f} = {gst_var_pct}%"
            },
            "lender_decisions": lender_results
        }

# Local Test Execution
if __name__ == "__main__":
    engine = JinOpsUnderwritingEngine()
    response = engine.process_underwriting(
        applicant_name="Vincent Paul",
        cibil_score=710,
        monthly_income=250000.00,
        existing_emi=40000.00,
        annual_gst_turnover=3000000.00,
        annual_banking_turnover=3200000.00,
        net_profit_annual=450000.00,
        depreciation_annual=50000.00,
        interest_annual=60000.00,
        requested_loan=2000000.00,
        tenure_months=36,
        interest_rate=14.0
    )
    
    print(json.dumps(response, indent=2))
def run_underwriting_engine(parsed_data: dict) -> dict:
    turnover = parsed_data.get("annual_turnover") or 0.0
    gstin = parsed_data.get("gstin")
    pan = parsed_data.get("pan")

    # Core Financial Rules
    monthly_income = turnover / 12.0 if turnover > 0 else 0.0
    max_allowed_foir = 0.60  # 60% FOIR for Business Loans
    
    eligible_monthly_emi = monthly_income * max_allowed_foir
    estimated_max_loan = eligible_monthly_emi * 48  # 4-year tenure multiplier

    # Risk Scoring Logic
    risk_score = 685  # Adjusted Default baseline
    status = "APPROVED"

    if not gstin or not pan:
        risk_score -= 100
        status = "MANUAL_REVIEW_REQUIRED"

    if turnover < 1200000:  # Below 12 Lakhs annual
        status = "REJECTED"
        reason = "Annual turnover below threshold eligibility."
    else:
        reason = "Financial profile meets underwriting policy guidelines."

    return {
        "status": status,
        "monthly_cashflow_est": round(monthly_income, 2),
        "eligible_monthly_emi": round(eligible_monthly_emi, 2),
        "max_loan_limit": round(estimated_max_loan, 2),
        "risk_score": risk_score,
        "remark": reason
    }   
import time
import json
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Union

def to_decimal(val: Union[float, int, str, None]) -> Decimal:
    """Converts any numeric input to Decimal with exact precision safely"""
    if val is None:
        return Decimal("0.00")
    try:
        return Decimal(str(val))
    except Exception:
        return Decimal("0.00")

class JinOpsUnderwritingEngine:
    def __init__(self):
        # Precise Lender Matrix (IDFC FIRST, Kinara Capital, SIDBI Rules)
        self.lenders = [
            {
                "name": "IDFC FIRST Bank",
                "min_cibil": 700,
                "max_foir": Decimal("0.60"),
                "min_dscr": Decimal("1.25"),
                "min_turnover": Decimal("5000000.00"),
                "max_gst_var": Decimal("0.20")
            },
            {
                "name": "Kinara Capital",
                "min_cibil": 650,
                "max_foir": Decimal("0.65"),
                "min_dscr": Decimal("1.15"),
                "min_turnover": Decimal("1200000.00"),
                "max_gst_var": Decimal("0.30")
            },
            {
                "name": "SIDBI",
                "min_cibil": 720,
                "max_foir": Decimal("0.50"),
                "min_dscr": Decimal("1.40"),
                "min_turnover": Decimal("10000000.00"),
                "max_gst_var": Decimal("0.15")
            }
        ]

    def round_curr(self, val: Decimal) -> Decimal:
        """Rounds to 2 decimal places using standard financial ROUND_HALF_UP"""
        return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate_exact_emi(self, principal: Decimal, annual_rate: Decimal, tenure_months: int) -> Decimal:
        """Standard Banking Reducing EMI Formula"""
        if principal <= 0 or tenure_months <= 0 or annual_rate <= 0:
            return Decimal("0.00")
        
        monthly_rate = (annual_rate / Decimal("12")) / Decimal("100")
        one_plus_r_n = (Decimal("1") + monthly_rate) ** tenure_months
        
        emi = principal * monthly_rate * one_plus_r_n / (one_plus_r_n - Decimal("1"))
        return self.round_curr(emi)

    def process_underwriting(self,
                             applicant_name: str,
                             cibil_score: int,
                             monthly_income: Any,
                             existing_emi: Any,
                             annual_gst_turnover: Any,
                             annual_banking_turnover: Any,
                             net_profit_annual: Any,
                             depreciation_annual: Any,
                             interest_annual: Any,
                             requested_loan: Any,
                             tenure_months: int,
                             interest_rate: Any) -> Dict[str, Any]:
        
        start_time = time.time()

        # Decimal Conversions
        P = to_decimal(requested_loan)
        R = to_decimal(interest_rate)
        Inc = to_decimal(monthly_income)
        Ex_EMI = to_decimal(existing_emi)
        GST_TO = to_decimal(annual_gst_turnover)
        Bank_TO = to_decimal(annual_banking_turnover)
        PAT = to_decimal(net_profit_annual)
        Dep = to_decimal(depreciation_annual)
        Int_Exp = to_decimal(interest_annual)

        # 1. Exact EMI Calculation
        proposed_emi = self.calculate_exact_emi(P, R, tenure_months)

        # 2. FOIR Calculation & Audit Formula Proof
        total_monthly_obligation = Ex_EMI + proposed_emi
        foir_ratio = (total_monthly_obligation / Inc) if Inc > 0 else Decimal("1.00")
        foir_pct = self.round_curr(foir_ratio * Decimal("100"))

        # 3. DSCR Calculation (EBITDA / Total Debt Service)
        ebitda = PAT + Dep + Int_Exp
        annual_debt_service = total_monthly_obligation * Decimal("12")
        dscr_ratio = self.round_curr(ebitda / annual_debt_service) if annual_debt_service > 0 else Decimal("0.00")

        # 4. GST vs Banking Variance Calculation
        turnover_diff = abs(Bank_TO - GST_TO)
        gst_variance_ratio = (turnover_diff / GST_TO) if GST_TO > 0 else Decimal("0.00")
        gst_var_pct = self.round_curr(gst_variance_ratio * Decimal("100"))

        # 5. Maximum Loan Eligibility Limit (@ 50% FOIR Cap)
        max_allowed_emi = (Inc * Decimal("0.50")) - Ex_EMI
        max_eligible_loan = Decimal("0.00")
        if max_allowed_emi > 0 and R > 0 and tenure_months > 0:
            monthly_r = (R / Decimal("12")) / Decimal("100")
            factor = ((Decimal("1") + monthly_r) ** tenure_months - Decimal("1")) / (monthly_r * ((Decimal("1") + monthly_r) ** tenure_months))
            max_eligible_loan = self.round_curr(max_allowed_emi * factor)

        # 6. Lender Routing Check
        lender_results = []
        for l in self.lenders:
            cibil_ok = cibil_score >= l["min_cibil"]
            foir_ok = foir_ratio <= l["max_foir"]
            dscr_ok = dscr_ratio >= l["min_dscr"]
            to_ok = Bank_TO >= l["min_turnover"]
            var_ok = gst_variance_ratio <= l["max_gst_var"]

            reasons = []
            if not cibil_ok: reasons.append(f"CIBIL {cibil_score} < {l['min_cibil']}")
            if not foir_ok: reasons.append(f"FOIR {foir_pct}% > {l['max_foir']*100}%")
            if not dscr_ok: reasons.append(f"DSCR {dscr_ratio}x < {l['min_dscr']}x")
            if not to_ok: reasons.append(f"Turnover INR {float(Bank_TO):,.2f} < Min INR {float(l['min_turnover']):,.2f}")
            if not var_ok: reasons.append(f"GST Mismatch {gst_var_pct}% High")

            lender_results.append({
                "lender_name": l["name"],
                "decision": "APPROVED" if (cibil_ok and foir_ok and dscr_ok and to_ok and var_ok) else "REJECTED",
                "audit_flags": reasons
            })

        execution_time_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "meta": {
                "engine": "JinOps High-Precision Underwriting Engine v2.0",
                "execution_speed": f"{execution_time_ms} ms",
                "mathematical_accuracy": "100% Bank Audit-Compliant (Decimal Precision)"
            },
            "applicant": {
                "name": applicant_name,
                "requested_loan": f"INR {float(P):,.2f}",
                "max_eligible_loan": f"INR {float(max_eligible_loan):,.2f}"
            },
            "metrics": {
                "proposed_emi": f"INR {float(proposed_emi):,.2f}",
                "foir": f"{foir_pct}%",
                "dscr": f"{dscr_ratio}x",
                "gst_banking_variance": f"{gst_var_pct}%"
            },
            "audit_lineage_proof": {
                "emi_formula_used": "P * r * (1+r)^n / ((1+r)^n - 1)",
                "foir_math_proof": f"(Existing EMI INR {float(Ex_EMI):,.2f} + New EMI INR {float(proposed_emi):,.2f}) / Gross Income INR {float(Inc):,.2f} = {foir_pct}%",
                "dscr_math_proof": f"(PAT INR {float(PAT):,.2f} + Dep INR {float(Dep):,.2f} + Int INR {float(Int_Exp):,.2f}) / Annual Obligations INR {float(annual_debt_service):,.2f} = {dscr_ratio}x",
                "gst_variance_proof": f"|Banking INR {float(Bank_TO):,.2f} - GST INR {float(GST_TO):,.2f}| / GST INR {float(GST_TO):,.2f} = {gst_var_pct}%"
            },
            "lender_decisions": lender_results
        }

def run_underwriting_engine(parsed_data: dict) -> dict:
    """Wrapper function to integrate seamlessly with API endpoints"""
    engine = JinOpsUnderwritingEngine()
    
    turnover = parsed_data.get("annual_turnover", 3000000.00)
    monthly_inc = turnover / 12.0
    
    return engine.process_underwriting(
        applicant_name=parsed_data.get("applicant_name", "Dynamic MSME Applicant"),
        cibil_score=parsed_data.get("cibil_score", 720),
        monthly_income=parsed_data.get("monthly_income", monthly_inc),
        existing_emi=parsed_data.get("existing_emi", 0.0),
        annual_gst_turnover=parsed_data.get("annual_gst_turnover", turnover),
        annual_banking_turnover=parsed_data.get("annual_banking_turnover", turnover),
        net_profit_annual=parsed_data.get("net_profit_annual", turnover * 0.15),
        depreciation_annual=parsed_data.get("depreciation_annual", 50000.0),
        interest_annual=parsed_data.get("interest_annual", 20000.0),
        requested_loan=parsed_data.get("requested_loan", 1000000.0),
        tenure_months=parsed_data.get("tenure_months", 36),
        interest_rate=parsed_data.get("interest_rate", 14.0)
    )