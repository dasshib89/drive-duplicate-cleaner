import os
import math
import streamlit as st
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive']

st.set_page_config(page_title="Drive Cleaner Pro", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    .hero-banner {
        background: linear-gradient(-45deg, #0f172a, #1e3a8a, #2563eb, #0f172a);
        padding: 25px; border-radius: 16px; color: white; text-align: center; margin-bottom: 20px;
    }
    .hero-title { font-size: 34px !important; font-weight: 800; }
    .folder-path-box {
        font-size: 11px;
        font-weight: 600;
        color: #1e293b;
        background-color: #f1f5f9;
        border-left: 3px solid #2563eb;
        padding: 4px 8px;
        border-radius: 4px;
        margin-top: 6px;
        word-break: break-all;
    }
</style>
""", unsafe_allow_html=True)

def get_drive_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def fetch_all_folders_map(service):
    folders_map = {}
    page_token = None
    while True:
        response = service.files().list(
            q="mimeType = 'application/vnd.google-apps.folder' and trashed = false",
            fields="nextPageToken, files(id, name, parents)",
            pageToken=page_token
        ).execute()
        for f in response.get('files', []):
            parent = f.get('parents', [None])[0]
            folders_map[f['id']] = {'name': f['name'], 'parent': parent}
        page_token = response.get('nextPageToken', None)
        if not page_token:
            break
    return folders_map

def get_full_path(folder_id, folders_map):
    if not folder_id or folder_id not in folders_map:
        return "📁 My Drive"
    
    path_list = []
    curr_id = folder_id
    while curr_id in folders_map:
        path_list.append(folders_map[curr_id]['name'])
        curr_id = folders_map[curr_id]['parent']
    
    path_list.append("My Drive")
    return " / ".join(reversed(path_list))

def delete_multiple_files(file_ids):
    service = get_drive_service()
    success_count = 0
    for fid in file_ids:
        try:
            service.files().update(fileId=fid, body={'trashed': True}).execute()
            success_count += 1
        except Exception:
            pass
    return success_count

def get_file_category(mime_type, file_name):
    mime_type = mime_type.lower() if mime_type else ""
    ext = file_name.split('.')[-1].lower() if '.' in file_name else ""
    if mime_type.startswith('image/') or ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
        return '📷 Photos'
    elif mime_type.startswith('video/') or ext in ['mp4', 'mkv', 'avi', 'mov']:
        return '🎬 Videos'
    elif mime_type.startswith('audio/') or ext in ['mp3', 'wav', 'aac', 'flac']:
        return '🎵 Audio'
    elif mime_type.startswith('application/pdf') or mime_type.startswith('text/') or ext in ['pdf', 'doc', 'docx', 'txt', 'pem']:
        return '📄 Documents'
    elif ext in ['zip', 'rar', '7z']:
        return '📦 Archives'
    else:
        return '📁 Others'

st.markdown("""
<div class="hero-banner">
    <div class="hero-title">⚡ Google Drive Duplicate Cleaner Pro</div>
    <p>Smart Automated MD5 Hash Precision Scanner with Bulk Delete</p>
</div>
""", unsafe_allow_html=True)

if 'duplicates' not in st.session_state:
    st.session_state['duplicates'] = []
if 'selected_files' not in st.session_state:
    st.session_state['selected_files'] = set()

# Scan Screen
if not st.session_state['duplicates']:
    st.markdown("<br>", unsafe_allow_html=True)
    scan_col1, scan_col2, scan_col3 = st.columns([1, 2, 1])
    with scan_col2:
        if st.button("🚀 START SCANNING DRIVE NOW", type="primary", use_container_width=True):
            with st.spinner("Fetching Folders & MD5 Hashes... Please wait..."):
                service = get_drive_service()
                folders_map = fetch_all_folders_map(service)
                
                hashes = {}
                duplicates_list = []
                page_token = None

                while True:
                    response = service.files().list(
                        q="trashed = false and mimeType != 'application/vnd.google-apps.folder'",
                        fields="nextPageToken, files(id, name, mimeType, md5Checksum, size, webViewLink, parents)",
                        pageToken=page_token
                    ).execute()

                    for file in response.get('files', []):
                        md5 = file.get('md5Checksum')
                        if md5:
                            parent_id = file.get('parents', [None])[0]
                            file_path = get_full_path(parent_id, folders_map)

                            if md5 in hashes:
                                orig_file, orig_path = hashes[md5]
                                duplicates_list.append({
                                    'dup': file,
                                    'dup_path': file_path,
                                    'orig': orig_file,
                                    'orig_path': orig_path,
                                    'category': get_file_category(file.get('mimeType', ''), file.get('name', ''))
                                })
                            else:
                                hashes[md5] = (file, file_path)

                    page_token = response.get('nextPageToken', None)
                    if not page_token:
                        break

                st.session_state['duplicates'] = duplicates_list
                st.session_state['selected_files'] = set()
                st.rerun()

# Dashboard Screen
if st.session_state['duplicates']:
    st.markdown("---")
    
    top_col1, top_col2 = st.columns([3, 1])
    with top_col1:
        st.markdown(f"### 🗂️ Duplicates Found: **{len(st.session_state['duplicates'])} files**")
    with top_col2:
        if st.button("🔄 Rescan / Clear Cache", type="secondary"):
            st.session_state['duplicates'] = []
            st.session_state['selected_files'] = set()
            st.rerun()

    tab_names = ["All Files", "📷 Photos", "🎬 Videos", "📄 Documents", "🎵 Audio", "📦 Archives", "📁 Others"]
    tabs = st.tabs(tab_names)

    for i, tab in enumerate(tabs):
        cat_name = tab_names[i]
        with tab:
            if cat_name == "All Files":
                filtered_items = st.session_state['duplicates']
            else:
                filtered_items = [x for x in st.session_state['duplicates'] if x['category'] == cat_name]

            if not filtered_items:
                st.info(f"No duplicate files found under **{cat_name}**!")
            else:
                items_per_page = 100
                total_pages = math.ceil(len(filtered_items) / items_per_page)

                p_col1, p_col2 = st.columns([1, 4])
                tab_prefix = "".join(e for e in cat_name if e.isalnum())
                with p_col1:
                    current_page = st.number_input("Page", min_value=1, max_value=max(1, total_pages), step=1, key=f"p_{tab_prefix}")
                with p_col2:
                    st.caption(f"Showing **{len(filtered_items)}** items | Page **{current_page}** of **{total_pages}**")

                start_idx = (current_page - 1) * items_per_page
                page_items = filtered_items[start_idx:start_idx + items_per_page]

                # Bulk Delete Control Bar
                st.markdown("<br>", unsafe_allow_html=True)
                b_col1, b_col2, b_col3 = st.columns([2, 2, 3])
                
                with b_col1:
                    if st.button(f"☑️ Select All (Current Page)", key=f"sel_all_{tab_prefix}"):
                        for item in page_items:
                            st.session_state['selected_files'].add(item['dup']['id'])
                        st.rerun()

                with b_col2:
                    if st.button(f"🔳 Deselect All", key=f"desel_all_{tab_prefix}"):
                        st.session_state['selected_files'].clear()
                        st.rerun()

                with b_col3:
                    selected_count = len(st.session_state['selected_files'])
                    if st.button(f"🗑️ Bulk Delete Selected ({selected_count})", type="primary", key=f"bulk_del_{tab_prefix}"):
                        if selected_count == 0:
                            st.warning("Please select at least one duplicate file to delete!")
                        else:
                            with st.spinner(f"Deleting {selected_count} files..."):
                                deleted_cnt = delete_multiple_files(st.session_state['selected_files'])
                                # Filter out deleted files from state
                                st.session_state['duplicates'] = [
                                    x for x in st.session_state['duplicates'] if x['dup']['id'] not in st.session_state['selected_files']
                                ]
                                st.session_state['selected_files'].clear()
                                st.toast(f"🎉 Successfully moved {deleted_cnt} files to Trash!", icon="✅")
                                st.rerun()

                st.markdown("<br>", unsafe_allow_html=True)

                # Items Rendering with Checkboxes
                for page_i, item in enumerate(page_items):
                    real_index = start_idx + page_i
                    dup = item['dup']
                    orig = item['orig']
                    size_mb = round(int(dup.get('size', 0)) / (1024 * 1024), 2)
                    dup_id = dup['id']

                    with st.container(border=True):
                        col_chk, col1, col2, col3 = st.columns([0.6, 3.4, 3.4, 2.6])

                        # Checkbox Column
                        with col_chk:
                            st.write("")
                            is_checked = dup_id in st.session_state['selected_files']
                            check_val = st.checkbox("", value=is_checked, key=f"chk_{tab_prefix}_{dup_id}_{real_index}")
                            if check_val:
                                st.session_state['selected_files'].add(dup_id)
                            else:
                                st.session_state['selected_files'].discard(dup_id)

                        # Original File
                        with col1:
                            st.markdown("🟢 **Original File**")
                            st.write(f"📄 `{orig['name']}`")
                            st.markdown(f"<div class='folder-path-box'>📂 Path: {item['orig_path']}</div>", unsafe_allow_html=True)
                            st.markdown(f"[🔗 View Original]({orig.get('webViewLink')})")

                        # Duplicate File
                        with col2:
                            st.markdown("🔴 **Duplicate File**")
                            st.write(f"📄 `{dup['name']}`")
                            st.markdown(f"<div class='folder-path-box'>📂 Path: {item['dup_path']}</div>", unsafe_allow_html=True)
                            st.markdown(f"[🔗 View Duplicate]({dup.get('webViewLink')})")

                        # Info & Single Delete Button
                        with col3:
                            st.markdown("💾 **Size / Category**")
                            st.write(f"**{size_mb} MB** | {item['category']}")
                            
                            btn_key = f"del_single_{tab_prefix}_{dup_id}_{real_index}"
                            if st.button("🗑️ Delete Single File", key=btn_key):
                                with st.spinner("Deleting..."):
                                    if delete_multiple_files([dup_id]):
                                        st.session_state['duplicates'] = [
                                            x for x in st.session_state['duplicates'] if x['dup']['id'] != dup_id
                                        ]
                                        st.session_state['selected_files'].discard(dup_id)
                                        st.toast("✅ Moved to Trash!", icon="🎉")
                                        st.rerun()