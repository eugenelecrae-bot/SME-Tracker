import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="SME Directorate Tracker", layout="wide")
st.image("https://via.placeholder.com/800x100.png?text=MINISTRY+OF+TRADE,+AGRIBUSINESS+AND+INDUSTRY", use_container_width=True)
st.title("📂 Correspondence Tracking System")
st.subheader("SME Development Directorate")

# --- GOOGLE SHEETS CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(worksheet="Data", ttl=0) # Read real-time data

menu = ["View Dashboard", "Log New Correspondence", "Update & Search"]
choice = st.sidebar.selectbox("Menu", menu)

# --- 1. DASHBOARD ---
if choice == "View Dashboard":
    st.write("### Directorate Overview")
    col1, col2, col3 = st.columns(3)
    
    pending_count = len(df[df["Status"] != "Completed"])
    avg_tat = df[df["Status"] == "Completed"]["TAT (Days)"].mean()
    
    col1.metric("Total Received", len(df))
    col2.metric("Pending Actions", pending_count)
    col3.metric("Avg Turn Around (Days)", f"{avg_tat:.1f}" if not pd.isna(avg_tat) else "0")

    st.divider()
    st.dataframe(df, use_container_width=True)

# --- 2. LOG NEW CORRESPONDENCE ---
elif choice == "Log New Correspondence":
    with st.form("entry_form"):
        col1, col2 = st.columns(2)
        with col1:
            date_rcvd = st.date_input("Date Received", datetime.now())
            c_type = st.selectbox("Type", ["External", "Internal", "Circular"])
            classif = st.selectbox("Classification", ["SME Development", "Administration"])
        with col2:
            sender = st.text_input("Sender/Origin (SME Name/Staff)")
            subject = st.text_input("Subject/Title")
            assigned = st.text_input("Assigned Officer")
        
        if st.form_submit_button("Submit to Registry"):
            ref_id = f"MOTI-SME-{len(df) + 1001}"
            new_row = pd.DataFrame([{
                "Ref ID": ref_id, "Date Received": str(date_rcvd), "Type": c_type,
                "Classification": classif, "Sender": sender, "Subject": subject,
                "Assigned To": assigned, "Status": "Pending", "Date Completed": "", "TAT (Days)": 0
            }])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(worksheet="Data", data=updated_df)
            st.success(f"Successfully Logged! Reference ID: {ref_id}")

# --- 3. SEARCH & UPDATE ---
elif choice == "Update & Search":
    search = st.text_input("Search by SME Name, Subject or Ref ID")
    if search:
        search_results = df[df.apply(lambda x: search.lower() in str(x).lower(), axis=1)]
        st.write(f"Found {len(search_results)} matching records:")
        st.table(search_results[["Ref ID", "Sender", "Subject", "Status"]])
        
        ref_to_edit = st.selectbox("Select Ref ID to Update", search_results["Ref ID"])
        new_status = st.selectbox("Update Status", ["In-Progress", "Completed"])
        
        if st.button("Confirm Update"):
            idx = df[df["Ref ID"] == ref_to_edit].index[0]
            df.at[idx, "Status"] = new_status
            if new_status == "Completed":
                today = datetime.now().date()
                start = pd.to_datetime(df.at[idx, "Date Received"]).date()
                df.at[idx, "Date Completed"] = str(today)
                df.at[idx, "TAT (Days)"] = (today - start).days
            
            conn.update(worksheet="Data", data=df)
            st.success("Record Updated Online!")
