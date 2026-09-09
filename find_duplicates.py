import streamlit as st
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive']

def get_drive_service():
    if "google_credentials" in st.secrets:
        creds_dict = dict(st.secrets["google_credentials"])
        if "installed" not in creds_dict and "web" not in creds_dict:
            creds_dict = {"installed": creds_dict}
        flow = InstalledAppFlow.from_client_config(creds_dict, SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    
    creds = flow.run_local_server(port=0)
    return build('drive', 'v3', credentials=creds)

st.set_page_config(page_title="Drive Cleaner Pro", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    .hero-banner {
        background: linear-gradient(-45deg, #0f172a, #1e3a8a, #2563eb, #0f172a);
        padding: 25px; border-radius: 16px; color: white; text-align: center; margin-bottom: 20px;
    }
    .hero-title { font-size: 34px !important; font-weight: 800; }
</style>
<div class="hero-banner">
    <div class="hero-title">⚡ Google Drive Duplicate Cleaner Pro</div>
    <div>Smart Automated MD5 Hash Precision Scanner with Bulk Delete</div>
</div>
""", unsafe_allow_html=True)

if st.button("🚀 START SCANNING DRIVE NOW", use_container_width=True):
    with st.spinner("Connecting to Google Drive..."):
        try:
            service = get_drive_service()
            st.success("Successfully connected to Google Drive!")
        except Exception as e:
            st.error(f"Error connecting to Drive: {e}")
