code = '''import streamlit as st
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

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
from sklearn.ensemble import RandomForestClassifier
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

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

st.set_page_config(page_title="Loan Eligibility Predictor", page_icon="🏦")
st.title("🏦 Loan Eligibility Predictor")
st.write("Fill in the details below to check loan eligibility.")

applicant_name = st.text_input("Applicant Name", value="")
gender = st.selectbox("Gender", ["Male", "Female"])
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
    if risk_score >= 70:
        risk_label = "Low"
        risk_color = "green"
    elif risk_score >= 40:
        risk_label = "Medium"
        risk_color = "orange"
    else:
        risk_label = "High"
        risk_color = "red"

    st.markdown("---")
    if prediction == 1:
        st.success("Congratulations! Loan is APPROVED!")
    else:
        st.error("Sorry, Loan is REJECTED.")

    st.markdown("### Risk Assessment")
    st.markdown(f"**Risk Score: {risk_score}/100**")
    st.progress(risk_score / 100)
    st.markdown(f"Risk Level: **{risk_label} Risk**")

    st.markdown("### Loan Amount Suggestion")
    st.info(f"Maximum suggested loan: Rs {suggested_loan:,.0f}")
    st.info(f"Estimated Monthly EMI: Rs {monthly_emi:,.0f} over {loan_term} months")
    if loan_amount * 1000 > suggested_loan:
        st.warning("Requested loan exceeds suggested limit. Consider reducing it.")
    else:
        st.success("Requested loan amount is within the safe limit!")
'''

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Done!")