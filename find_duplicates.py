import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive']

def get_drive_service():
    if "google_credentials" in st.secrets:
        creds_dict = dict(st.secrets["google_credentials"])
        
        # Ensure private key formatting handles newlines properly
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace('\\n', '\n')
            
        creds = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=SCOPES
        )
        return build('drive', 'v3', credentials=creds)
    else:
        st.error("Secrets-এ google_credentials পাওয়া যায়নি!")
        return None

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
            if service:
                # Test connection by listing 1 file
                results = service.files().list(pageSize=1, fields="files(id, name)").execute()
                st.success("Successfully connected to Google Drive API!")
        except Exception as e:
            st.error(f"Error connecting to Drive: {e}")
