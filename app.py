import streamlit as st
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import plotly.graph_objects as go
import sqlite3
from datetime import datetime

data = {
    "Gender": ["Male","Female","Male","Male","Female","Male","Female","Male","Male","Female"],
    "Married": ["Yes","No","Yes","Yes","No","Yes","No","Yes","No","Yes"],
    "Dependents": [0,1,2,0,1,3,0,2,1,0],
    "Education": ["Graduate","Not Graduate","Graduate","Graduate","Graduate","Not Graduate","Graduate","Graduate","Not Graduate","Graduate"],
    "Self_Employed": ["No","No","Yes","No","No","Yes","No","No","No","Yes"],
    "ApplicantIncome": [5000,3000,7000,4000,6000,2500,8000,4500,3500,9000],
    "CoapplicantIncome": [2000,0,1500,1800,0,2200,0,1200,0,3000],
    "LoanAmount": [150,100,200,120,180,80,250,130,90,300],
    "Loan_Amount_Term": [360,120,360,240,360,180,360,360,120,360],
    "Credit_History": [1,1,1,0,1,0,1,1,0,1],
    "Property_Area": ["Urban","Rural","Semiurban","Urban","Rural","Urban","Semiurban","Rural","Urban","Semiurban"],
    "Loan_Status": [1,1,1,0,1,0,1,1,0,1]
}

df = pd.DataFrame(data)
le = LabelEncoder()
for col in ["Gender","Married","Education","Self_Employed","Property_Area"]:
    df[col] = le.fit_transform(df[col])

X = df.drop("Loan_Status", axis=1)
y = df["Loan_Status"]
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

def init_db():
    conn = sqlite3.connect("loan_history.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, gender TEXT, married TEXT, dependents INTEGER,
        education TEXT, income INTEGER, loan_amount INTEGER,
        loan_term INTEGER, credit_history INTEGER, property_area TEXT,
        result TEXT, approval_prob INTEGER, risk_score INTEGER,
        risk_label TEXT, date TEXT
    )''')
    conn.commit()
    conn.close()

def save_to_db(data):
    conn = sqlite3.connect("loan_history.db")
    c = conn.cursor()
    c.execute('''INSERT INTO history (name, gender, married, dependents, education, income,
        loan_amount, loan_term, credit_history, property_area, result, approval_prob,
        risk_score, risk_label, date) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (data["name"], data["gender"], data["married"], data["dependents"], data["education"],
         data["applicant_income"], data["loan_amount"], data["loan_term"], data["credit_history"],
         data["property_area"], "APPROVED" if data["prediction"] == 1 else "REJECTED",
         data["approval_prob"], data["risk_score"], data["risk_label"],
         datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect("loan_history.db")
    df = pd.read_sql_query("SELECT * FROM history ORDER BY id DESC", conn)
    conn.close()
    return df

def calculate_risk_score(credit_history, applicant_income, coapplicant_income, loan_amount, dependents, education):
    score = 100
    if credit_history == 0:
        score -= 40
    total_income = applicant_income + coapplicant_income
    if total_income < 3000:
        score -= 20
    elif total_income < 5000:
        score -= 10
    ratio = (loan_amount * 1000) / total_income if total_income > 0 else 999
    if ratio > 10:
        score -= 20
    elif ratio > 5:
        score -= 10
    if dependents >= 3:
        score -= 10
    elif dependents >= 2:
        score -= 5
    if education == "Not Graduate":
        score -= 5
    return max(0, min(100, score))

def loan_safety_message(prob):
    if prob >= 80:
        return "Very Safe to give loan"
    elif prob >= 60:
        return "Safe to give loan"
    elif prob >= 40:
        return "Moderate risk, proceed with caution"
    else:
        return "High risk, not recommended to give loan"

def generate_repayment_schedule(principal, annual_rate, months):
    monthly_rate = annual_rate / 12 / 100
    if monthly_rate == 0:
        emi = principal / months
    else:
        emi = principal * monthly_rate * (1 + monthly_rate)**months / ((1 + monthly_rate)**months - 1)
    schedule = []
    balance = principal
    for month in range(1, months + 1):
        interest = balance * monthly_rate
        principal_paid = emi - interest
        balance -= principal_paid
        if balance < 0:
            balance = 0
        schedule.append({
            "Month": month,
            "EMI (Rs)": round(emi),
            "Principal Paid (Rs)": round(principal_paid),
            "Interest Paid (Rs)": round(interest),
            "Balance Remaining (Rs)": round(balance)
        })
    return pd.DataFrame(schedule)

def generate_pdf(data):
    from fpdf import FPDF
    import tempfile
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "LOAN ASSESSMENT REPORT", ln=True, align="C")
    pdf.ln(3)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Applicant Details", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Name: {data['name']}", ln=True)
    pdf.cell(0, 8, f"Gender: {data['gender']}  Married: {data['married']}  Dependents: {data['dependents']}", ln=True)
    pdf.cell(0, 8, f"Education: {data['education']}  Self Employed: {data['self_employed']}", ln=True)
    pdf.cell(0, 8, f"Property Area: {data['property_area']}", ln=True)
    pdf.ln(3)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Financial Details", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Applicant Income: Rs {data['applicant_income']:,}", ln=True)
    pdf.cell(0, 8, f"Co-applicant Income: Rs {data['coapplicant_income']:,}", ln=True)
    pdf.cell(0, 8, f"Loan Amount: Rs {data['loan_amount'] * 1000:,}", ln=True)
    pdf.cell(0, 8, f"Loan Term: {data['loan_term']} months", ln=True)
    pdf.cell(0, 8, f"Credit History: {'Good' if data['credit_history'] == 1 else 'Bad'}", ln=True)
    pdf.ln(3)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Assessment Results", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Loan Decision: {'APPROVED' if data['prediction'] == 1 else 'REJECTED'}", ln=True)
    pdf.cell(0, 8, f"Approval Probability: {data['approval_prob']}%", ln=True)
    pdf.cell(0, 8, f"Safety Assessment: {str(data['approval_prob'])}% - See app for details", ln=True)
    pdf.cell(0, 8, f"Risk Score: {data['risk_score']}/100 ({data['risk_label']} Risk)", ln=True)
    pdf.cell(0, 8, f"Maximum Suggested Loan: Rs {data['suggested_loan']:,.0f}", ln=True)
    pdf.cell(0, 8, f"Estimated Monthly EMI: Rs {data['monthly_emi']:,.0f}", ln=True)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)
    return tmp.name

init_db()

st.set_page_config(page_title="Loan Eligibility Predictor", page_icon="🏦")
st.title("🏦 Loan Eligibility Predictor")
st.write("Fill in the details below to check loan eligibility.")

st.markdown("### Applicant 1 Details")
applicant_name = st.text_input("Applicant Name", value="")
gender = st.selectbox("Gender", ["Male", "Female", "Other"])
married = st.selectbox("Married", ["Yes", "No"])
dependents = st.selectbox("Number of Dependents", [0, 1, 2, 3])
education = st.selectbox("Education", ["Graduate", "Not Graduate"])
self_employed = st.selectbox("Self Employed", ["No", "Yes"])
applicant_income = st.number_input("Applicant Income (Rs)", min_value=0, value=5000)
coapplicant_income = st.number_input("Co-applicant Income (Rs)", min_value=0, value=0)
loan_amount = st.number_input("Loan Amount (in thousands Rs)", min_value=0, value=150)
loan_term = st.selectbox("Loan Amount Term (months)", [120, 180, 240, 360])
credit_history = st.selectbox("Credit History", [1, 0], format_func=lambda x: "Good (1)" if x == 1 else "Bad (0)")
property_area = st.selectbox("Property Area", ["Urban", "Semiurban", "Rural"])
annual_interest_rate = st.slider("Annual Interest Rate (%)", min_value=1.0, max_value=20.0, value=8.5, step=0.5)

st.markdown("---")
st.markdown("### Compare Two Applicants?")
compare = st.checkbox("Enable Applicant Comparison")

if compare:
    st.markdown("#### Applicant 2 Details")
    name2 = st.text_input("Applicant 2 Name", value="")
    gender2 = st.selectbox("Gender (A2)", ["Male", "Female", "Other"])
    married2 = st.selectbox("Married (A2)", ["Yes", "No"])
    dependents2 = st.selectbox("Dependents (A2)", [0, 1, 2, 3])
    education2 = st.selectbox("Education (A2)", ["Graduate", "Not Graduate"])
    income2 = st.number_input("Applicant 2 Income (Rs)", min_value=0, value=4000)
    coincome2 = st.number_input("Co-applicant 2 Income (Rs)", min_value=0, value=0)
    loan2 = st.number_input("Loan Amount 2 (thousands Rs)", min_value=0, value=120)
    term2 = st.selectbox("Loan Term (A2)", [120, 180, 240, 360])
    credit2 = st.selectbox("Credit History (A2)", [1, 0], format_func=lambda x: "Good (1)" if x == 1 else "Bad (0)")
    area2 = st.selectbox("Property Area (A2)", ["Urban", "Semiurban", "Rural"])

st.markdown("---")
if st.button("Check Eligibility"):
    gender_val = 1 if gender == "Male" else 0
    married_val = 1 if married == "Yes" else 0
    education_val = 0 if education == "Graduate" else 1
    self_emp_val = 1 if self_employed == "Yes" else 0
    area_val = 2 if property_area == "Urban" else (1 if property_area == "Semiurban" else 0)

    input_data = [[gender_val, married_val, dependents, education_val, self_emp_val,
                   applicant_income, coapplicant_income, loan_amount, loan_term,
                   credit_history, area_val]]

    prediction = model.predict(input_data)[0]
    proba = model.predict_proba(input_data)[0]
    approval_prob = round(proba[1] * 100)

    total_income = applicant_income + coapplicant_income
    if credit_history == 1:
        multiplier = 5 if education == "Graduate" else 4
    else:
        multiplier = 2
    if dependents >= 2:
        multiplier -= 0.5
    suggested_loan = total_income * multiplier
    monthly_emi = suggested_loan / loan_term if loan_term > 0 else 0
    risk_score = calculate_risk_score(credit_history, applicant_income, coapplicant_income, loan_amount, dependents, education)
    risk_label = "Low" if risk_score >= 70 else ("Medium" if risk_score >= 40 else "High")

    result = {
        "name": applicant_name or "N/A",
        "gender": gender, "married": married, "dependents": dependents,
        "education": education, "self_employed": self_employed,
        "property_area": property_area, "applicant_income": applicant_income,
        "coapplicant_income": coapplicant_income, "loan_amount": loan_amount,
        "loan_term": loan_term, "credit_history": credit_history,
        "prediction": prediction, "approval_prob": approval_prob,
        "suggested_loan": suggested_loan, "monthly_emi": monthly_emi,
        "risk_score": risk_score, "risk_label": risk_label,
        "annual_interest_rate": annual_interest_rate
    }

    save_to_db(result)
    st.session_state["result"] = result

    if compare:
        g2 = 1 if gender2 == "Male" else 0
        m2 = 1 if married2 == "Yes" else 0
        e2 = 0 if education2 == "Graduate" else 1
        a2 = 2 if area2 == "Urban" else (1 if area2 == "Semiurban" else 0)
        input2 = [[g2, m2, dependents2, e2, 0, income2, coincome2, loan2, term2, credit2, a2]]
        pred2 = model.predict(input2)[0]
        proba2 = model.predict_proba(input2)[0]
        prob2 = round(proba2[1] * 100)
        risk2 = calculate_risk_score(credit2, income2, coincome2, loan2, dependents2, education2)
        st.session_state["result2"] = {"name": name2 or "Applicant 2", "pred": pred2, "risk": risk2, "prob": prob2}
    else:
        st.session_state["result2"] = None

if "result" in st.session_state and st.session_state["result"]:
    r = st.session_state["result"]
    st.markdown("---")
    st.markdown("## Results")

    if st.session_state["result2"]:
        r2 = st.session_state["result2"]
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"### {r['name']}")
            st.success("APPROVED") if r["prediction"] == 1 else st.error("REJECTED")
            fig1 = go.Figure(go.Pie(
                labels=["Approval", "Rejection"],
                values=[r["approval_prob"], 100 - r["approval_prob"]],
                hole=0.4, marker_colors=["#22c55e", "#ef4444"]
            ))
            fig1.update_layout(margin=dict(t=0,b=0,l=0,r=0), height=200, showlegend=False)
            st.plotly_chart(fig1, use_container_width=True)
            st.write(loan_safety_message(r["approval_prob"]))
            st.write(f"Risk Score: {r['risk_score']}/100")
            st.progress(r["risk_score"] / 100)
        with col2:
            st.markdown(f"### {r2['name']}")
            st.success("APPROVED") if r2["pred"] == 1 else st.error("REJECTED")
            fig2 = go.Figure(go.Pie(
                labels=["Approval", "Rejection"],
                values=[r2["prob"], 100 - r2["prob"]],
                hole=0.4, marker_colors=["#22c55e", "#ef4444"]
            ))
            fig2.update_layout(margin=dict(t=0,b=0,l=0,r=0), height=200, showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
            st.write(loan_safety_message(r2["prob"]))
            st.write(f"Risk Score: {r2['risk']}/100")
            st.progress(r2["risk"] / 100)
    else:
        if r["prediction"] == 1:
            st.success("Congratulations! Loan is APPROVED!")
        else:
            st.error("Sorry, Loan is REJECTED.")

        st.markdown("### Approval Probability")
        fig = go.Figure(go.Pie(
            labels=["Approval Chance", "Rejection Chance"],
            values=[r["approval_prob"], 100 - r["approval_prob"]],
            hole=0.4, marker_colors=["#22c55e", "#ef4444"]
        ))
        fig.update_layout(margin=dict(t=20,b=0,l=0,r=0), height=300)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(f"### {loan_safety_message(r['approval_prob'])}")

        st.markdown("### Risk Assessment")
        st.markdown(f"**Risk Score: {r['risk_score']}/100**")
        st.progress(r["risk_score"] / 100)
        st.markdown(f"Risk Level: **{r['risk_label']} Risk**")

    st.markdown("### Loan Amount Suggestion")
    st.info(f"Maximum suggested loan: Rs {r['suggested_loan']:,.0f}")
    st.info(f"Estimated Monthly EMI: Rs {r['monthly_emi']:,.0f} over {r['loan_term']} months")
    if r["loan_amount"] * 1000 > r["suggested_loan"]:
        st.warning("Requested loan exceeds suggested limit. Consider reducing it.")
    else:
        st.success("Requested loan amount is within the safe limit!")

    st.markdown("---")
    st.markdown("### Loan Repayment Schedule")
    principal = r["loan_amount"] * 1000
    schedule_df = generate_repayment_schedule(principal, r["annual_interest_rate"], r["loan_term"])
    st.write(f"Interest Rate: {r['annual_interest_rate']}% per annum | Total Months: {r['loan_term']}")
    st.dataframe(schedule_df, use_container_width=True)
    total_interest = schedule_df["Interest Paid (Rs)"].sum()
    st.info(f"Total Interest Payable: Rs {total_interest:,.0f} | Total Amount Payable: Rs {principal + total_interest:,.0f}")

    st.markdown("---")
    st.markdown("### Download PDF Report")
    pdf_path = generate_pdf(r)
    with open(pdf_path, "rb") as f:
        st.download_button("Download Report", f, file_name="loan_report.pdf", mime="application/pdf")

st.markdown("---")
st.markdown("## Applicant History")
history_df = get_history()
if not history_df.empty:
    st.dataframe(history_df[["name","gender","education","income","loan_amount","result","approval_prob","risk_score","risk_label","date"]], use_container_width=True)
    if st.button("Clear History"):
        conn = sqlite3.connect("loan_history.db")
        conn.execute("DELETE FROM history")
        conn.commit()
        conn.close()
        st.rerun()
else:
    st.info("No history yet. Check some applicants to see history here!")
