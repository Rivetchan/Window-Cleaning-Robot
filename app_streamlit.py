"""
Robot Pembersih Kaca - Streamlit Dashboard
Full Monitoring & Control with Tracking Graph
Ukuran: 70 cm × 90 cm (prototype)
"""

import streamlit as st
import requests
import time
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from collections import deque
import os

# ============================================
# KONFIGURASI
# ============================================

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:7080")
API_BASE = f"{BACKEND_URL}/api"

MONITORING_URL = f"{API_BASE}/monitoring"
CONTROL_URL = f"{API_BASE}/control"
MQTT_URL = f"{API_BASE}/mqtt"

# ============================================
# UKURAN GEDUNG PROTOTYPE
# ============================================
MAX_COL = 70
MAX_ROW = 90
TOTAL_CELLS = MAX_COL * MAX_ROW

st.set_page_config(
    page_title="Robot Pembersih Kaca",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# SESSION STATE
# ============================================

if 'position_history' not in st.session_state:
    st.session_state.position_history = deque(maxlen=200)
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = True
if 'battery_history' not in st.session_state:
    st.session_state.battery_history = deque(maxlen=30)

# ============================================
# FUNGSI API
# ============================================

def fetch_status():
    try:
        resp = requests.get(f"{MONITORING_URL}/status", timeout=3)
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return None

def fetch_logs():
    try:
        resp = requests.get(f"{MONITORING_URL}/logs?limit=30", timeout=3)
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return []

def send_command(endpoint, data=None):
    url = f"{CONTROL_URL}/{endpoint}"
    try:
        if data:
            resp = requests.post(url, json=data, timeout=5)
        else:
            resp = requests.post(url, timeout=5)
        if resp.status_code == 200:
            st.success("✅ Command berhasil!")
            st.cache_data.clear()
            return resp.json()
    except Exception as e:
        st.error(f"❌ Gagal mengirim command: {str(e)}")
    return None

def send_katrol_command(command, params=None):
    data = {"command": command}
    if params:
        data["params"] = params
    return send_command("katrol/command", data)

# ============================================
# CSS
# ============================================

st.markdown("""
<style>
    .metric-card {
        background: #1a1a2e;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #2d3643;
        text-align: center;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #3b7dd8;
    }
    .metric-label {
        color: #7d8590;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 13px;
    }
    .status-badge.idle { background: #2ea043; color: white; }
    .status-badge.moving { background: #3b7dd8; color: white; }
    .status-badge.cleaning { background: #d29922; color: white; }
    .status-badge.error { background: #da3633; color: white; }
    .status-badge.emergency { background: #da3633; color: white; animation: blink 1s infinite; }
    .status-badge.auto { background: #8b5cf6; color: white; animation: pulse-purple 2s infinite; }
    @keyframes blink { 50% { opacity: 0.5; } }
    @keyframes pulse-purple {
        0% { box-shadow: 0 0 0 0 rgba(139, 92, 246, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(139, 92, 246, 0); }
        100% { box-shadow: 0 0 0 0 rgba(139, 92, 246, 0); }
    }
    .stButton button { width: 100%; border-radius: 8px; font-weight: 600; }
    .tracking-card {
        background: #1a1a2e;
        border-radius: 12px;
        padding: 15px;
        border: 1px solid #2d3643;
        text-align: center;
    }
    .direction-indicator {
        font-size: 48px;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# SIDEBAR
# ============================================

with st.sidebar:
    st.title("🧹 Robot")
    st.caption("Pembersih Kaca v2.0")
    st.divider()
    
    status = fetch_status()
    if status:
        status_text = status.get('status', 'idle')
        is_auto = status.get('mode') == "auto" and status.get('auto_active', False)
        badge_class = "auto" if is_auto else status_text
        
        st.markdown(f"""
        <div style="background: #1a1a2e; border-radius: 12px; padding: 15px; border: 1px solid #2d3643;">
            <div style="display: flex; justify-content: space-between;">
                <span style="color: #7d8590;">Status</span>
                <span class="status-badge {badge_class}">{status_text.upper()}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 8px;">
                <span style="color: #7d8590;">Mode</span>
                <span style="color: white; font-weight: 600;">{status.get('mode', 'manual').upper()}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 8px;">
                <span style="color: #7d8590;">📍 Kolom</span>
                <span style="color: white; font-weight: 600;">{status.get('kolom', MAX_COL)}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🔋 Baterai", f"{status.get('battery', 0):.1f}%")
        with col2:
            st.metric("🧹 Progress", f"{status.get('clean_progress', 0):.1f}%")
        
        pos = status.get('position', {})
        st.metric("📍 Posisi", f"({pos.get('col', MAX_COL)}, {pos.get('row', 1)})")
        st.metric("⏱️ Uptime", status.get('uptime', '00:00:00'))
        st.caption(f"🔄 {datetime.now().strftime('%H:%M:%S')}")
    else:
        st.error("❌ Koneksi gagal!")
    
    st.divider()
    
    st.subheader("⚡ Quick Actions")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🛑 Stop", use_container_width=True, key="stop_sidebar"):
            send_command("stop")
            send_katrol_command("STOP_ALL")
    with col2:
        if st.button("🔄 Reset", use_container_width=True, key="reset_sidebar"):
            send_command("reset")
    
    st.divider()
    
    st.subheader("🔄 Auto Refresh")
    auto_refresh = st.checkbox("Auto Refresh", value=st.session_state.auto_refresh)
    st.session_state.auto_refresh = auto_refresh
    
    if st.button("🔄 Refresh Now", use_container_width=True, key="refresh_sidebar"):
        st.cache_data.clear()
        st.rerun()

# ============================================
# MAIN CONTENT
# ============================================

st.title("🧹 Robot Pembersih Kaca")
st.caption(f"📐 Ukuran: 70 cm × 90 cm | Grid: {MAX_COL}×{MAX_ROW} = {TOTAL_CELLS} sel (1 cm²/sel)")

# ============================================
# TABS
# ============================================

tab1, tab2, tab3, tab4 = st.tabs([
    "🎮 Control",
    "📊 Monitoring",
    "📈 Tracking",
    "📋 Logs"
])

# ============================================
# TAB 1: CONTROL
# ============================================

with tab1:
    st.subheader("🎮 Kontrol Robot")
    
    status = fetch_status()
    current_mode = status.get('mode', 'manual') if status else 'manual'
    
    st.markdown("### 🤖 Mode Kontrol")
    col_mode1, col_mode2 = st.columns(2)
    with col_mode1:
        if st.button("🔧 MANUAL", use_container_width=True, 
                     key="mode_manual",
                     type="primary" if current_mode == "manual" else "secondary"):
            send_command("mode/manual")
            send_katrol_command("AUTO_STOP")
            st.success("✅ Mode Manual Aktif")
            st.rerun()
    
    with col_mode2:
        if st.button("🤖 OTOMATIS (ZIG-ZAG)", use_container_width=True, 
                     key="mode_auto",
                     type="primary" if current_mode == "auto" else "secondary"):
            send_command("mode/auto")
            send_katrol_command("AUTO_START")
            st.success("✅ Mode Auto Aktif")
            st.rerun()
    
    if current_mode == "auto":
        st.info(f"🤖 **Mode Auto Aktif** - Robot berjalan otomatis zig-zag dari kolom {MAX_COL} ke 1")
        if status and status.get('auto_complete'):
            st.success("✅ **Zig-Zag Selesai!**")
        elif status:
            st.info(f"📍 **Kolom Saat Ini:** {status.get('kolom', MAX_COL)}")
    else:
        st.info("🔧 **Mode Manual** - Gunakan tombol di bawah")
    
    st.divider()
    
    if current_mode == "manual":
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            st.subheader("⚡ Kecepatan")
            speed = st.select_slider(
                "Speed (%)",
                options=[25, 50, 75, 100],
                value=50,
                key="speed_slider"
            )
            if st.button("Apply Speed", use_container_width=True, key="apply_speed"):
                send_command("speed", {"speed": speed / 100})
        
        with col2:
            st.subheader("🔄 Katrol (Naik/Turun)")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                if st.button("⬆ NAIK", use_container_width=True, key="katrol_naik"):
                    send_katrol_command("KATROL", {"direction": "NAIK", "speed": speed})
            with col_b:
                if st.button("⏹ STOP", use_container_width=True, key="stop_katrol"):
                    send_katrol_command("STOP_ALL")
            with col_c:
                if st.button("⬇ TURUN", use_container_width=True, key="katrol_turun"):
                    send_katrol_command("KATROL", {"direction": "TURUN", "speed": speed})
        
        with col3:
            st.subheader("🚗 Roda (Maju/Mundur)")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                if st.button("⬆ MAJU", use_container_width=True, key="roda_maju"):
                    send_katrol_command("RODA", {"direction": "MAJU", "speed": speed})
            with col_b:
                if st.button("⏹ STOP", use_container_width=True, key="stop_roda"):
                    send_katrol_command("STOP_ALL")
            with col_c:
                if st.button("⬇ MUNDUR", use_container_width=True, key="roda_mundur"):
                    send_katrol_command("RODA", {"direction": "MUNDUR", "speed": speed})
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📊 Status Auto Mode")
            if status:
                st.metric("Kolom Saat Ini", status.get('kolom', MAX_COL))
                st.metric("Step", status.get('auto_step', 0))
                st.metric("Auto Complete", "✅ Selesai" if status.get('auto_complete') else "⏳ Berjalan")
            else:
                st.info("Menunggu data...")
        
        with col2:
            st.subheader("🎮 Kontrol Auto")
            if st.button("🛑 STOP AUTO", use_container_width=True, key="stop_auto"):
                send_katrol_command("AUTO_STOP")
                send_command("mode/manual")
                st.success("✅ Auto Mode Dihentikan")
                st.rerun()
    
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("🖌️ Brush")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🟢 ON", use_container_width=True, key="brush_on"):
                send_command("brush", {"action": "on"})
        with col_b:
            if st.button("🔴 OFF", use_container_width=True, key="brush_off"):
                send_command("brush", {"action": "off"})
        
        brush_speed = st.slider("Brush Speed", 0, 100, 50, 5, key="brush_speed")
        if st.button("Set Speed", use_container_width=True, key="brush_apply"):
            send_command("brush", {"action": "on", "speed": brush_speed})
    
    with col2:
        st.subheader("⚠️ Emergency")
        col_c, col_d = st.columns(2)
        with col_c:
            if st.button("🛑 EMERGENCY STOP", use_container_width=True, key="emergency_stop"):
                send_command("emergency/stop")
                send_katrol_command("EMERGENCY_STOP")
        with col_d:
            if st.button("🔄 EMERGENCY RESET", use_container_width=True, key="emergency_reset"):
                send_command("emergency/reset")
                send_katrol_command("EMERGENCY_RESET")
    
    with col3:
        st.subheader("🔧 System")
        if st.button("🔄 Reset Posisi", use_container_width=True, key="reset_position"):
            send_command("reset")
            send_katrol_command("STOP_ALL")
        if st.button("🔄 Katrol System ON", use_container_width=True, key="katrol_system_on"):
            send_katrol_command("KATROL_SYSTEM_ON")
        if st.button("🔴 Katrol System OFF", use_container_width=True, key="katrol_system_off"):
            send_katrol_command("KATROL_SYSTEM_OFF")

# ============================================
# TAB 2: MONITORING
# ============================================

with tab2:
    status = fetch_status()
    if status:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">🔋 Baterai</div>
                <div class="metric-value">{status.get('battery', 0):.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">🧹 Progress</div>
                <div class="metric-value">{status.get('clean_progress', 0):.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">💧 Air</div>
                <div class="metric-value">{status.get('water_tank', 0):.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">⏱️ Uptime</div>
                <div class="metric-value" style="font-size:20px;">{status.get('uptime', '00:00:00')}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📍 Posisi & Status")
            pos = status.get('position', {})
            st.progress(pos.get('col', MAX_COL) / MAX_COL, text=f"Kolom: {pos.get('col', MAX_COL)} / {MAX_COL}")
            st.progress(pos.get('row', 1) / MAX_ROW, text=f"Baris: {pos.get('row', 1)} / {MAX_ROW}")
            st.write(f"**Mode:** {status.get('mode', 'manual').upper()}")
            st.write(f"**Moving:** {'✅ Yes' if status.get('moving') else '❌ No'}")
            st.write(f"**Katrol Direction:** {status.get('katrol_direction', '-')}")
            st.write(f"**Roda Direction:** {status.get('roda_direction', '-')}")
            st.write(f"**Auto Active:** {'✅ Yes' if status.get('auto_active') else '❌ No'}")
            st.write(f"**Auto Complete:** {'✅ Yes' if status.get('auto_complete') else '❌ No'}")
            st.write(f"**Kolom:** {status.get('kolom', MAX_COL)}")
        
        with col2:
            st.subheader("📡 System Status")
            st.write(f"**Brush:** {'🟢 ON' if status.get('brush_running') else '⚪ OFF'}")
            st.write(f"**Brush Speed:** {status.get('brush_speed', 50)}%")
            st.write(f"**Brush System:** {'ON' if status.get('brush_system') else 'OFF'}")
            st.write(f"**Katrol System:** {'ON' if status.get('katrol_system') else 'OFF'}")
            st.write(f"**ESP Katrol:** {'🟢 Online' if status.get('esp_katrol') else '🔴 Offline'}")
            
            if status.get('emergency_stop'):
                st.error("⚠️ EMERGENCY STOP ACTIVE!")
            else:
                st.success("✅ Emergency: Normal")
        
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.subheader("🧹 Progress Cleaning")
            progress = status.get('clean_progress', 0)
            st.progress(progress / 100)
            st.write(f"{progress:.1f}% selesai ({status.get('cleaned_cells', 0)} / {TOTAL_CELLS} sel)")
        with col2:
            st.subheader("🔋 Battery")
            battery = status.get('battery', 0)
            st.progress(battery / 100)
            st.write(f"{battery:.1f}%")
        with col3:
            st.subheader("💧 Water")
            water = status.get('water_tank', 0)
            st.progress(water / 100)
            st.write(f"{water:.1f}%")
        
        st.markdown("---")
        st.markdown("#### 🧭 Arah Gerak")
        
        col_dir1, col_dir2 = st.columns(2)
        with col_dir1:
            katrol_dir = status.get('katrol_direction', '-')
            dir_emoji = "⬆" if katrol_dir == "NAIK" else "⬇" if katrol_dir == "TURUN" else "⏹"
            dir_text = "Naik" if katrol_dir == "NAIK" else "Turun" if katrol_dir == "TURUN" else "Diam"
            st.markdown(f"""
            <div class="tracking-card">
                <div class="direction-indicator">{dir_emoji}</div>
                <div style="font-size: 20px; font-weight: bold;">Katrol: {dir_text}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_dir2:
            roda_dir = status.get('roda_direction', '-')
            dir_emoji = "➡" if roda_dir == "MAJU" else "⬅" if roda_dir == "MUNDUR" else "⏹"
            dir_text = "Maju" if roda_dir == "MAJU" else "Mundur" if roda_dir == "MUNDUR" else "Diam"
            st.markdown(f"""
            <div class="tracking-card">
                <div class="direction-indicator">{dir_emoji}</div>
                <div style="font-size: 20px; font-weight: bold;">Roda: {dir_text}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.error("❌ Gagal fetch data")

# ============================================
# TAB 3: TRACKING
# ============================================

with tab3:
    st.subheader("🗺️ Tracking Pergerakan Robot")
    st.caption(f"📐 Ukuran: 70 cm × 90 cm | Grid: {MAX_COL}×{MAX_ROW} sel | Garis setiap 10 cm")
    
    status = fetch_status()
    if status:
        pos = status.get('position', {})
        col = pos.get('col', MAX_COL)
        row = pos.get('row', 1)
        kolom = status.get('kolom', MAX_COL)
        auto_active = status.get('auto_active', False)
        auto_complete = status.get('auto_complete', False)
        
        st.session_state.position_history.append((col, row))
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("#### 📍 Robot Path Tracking")
            
            fig = go.Figure()
            
            # Grid background
            grid_data = [[0]*MAX_ROW for _ in range(MAX_COL)]
            cleaned_cells = status.get('cleaned_cells', 0)
            if cleaned_cells > 0:
                for i in range(min(MAX_COL, cleaned_cells // MAX_ROW + 2)):
                    for j in range(min(MAX_ROW, cleaned_cells % TOTAL_CELLS // 10 + 2)):
                        if (i-1) * MAX_ROW + (j-1) < cleaned_cells:
                            grid_data[i-1][j-1] = 0.5
            
            fig.add_trace(go.Heatmap(
                z=grid_data,
                colorscale=[[0, 'rgba(0,0,0,0)'], [0.5, 'rgba(46,160,67,0.3)'], [1, 'rgba(46,160,67,0.6)']],
                showscale=False,
                hovertemplate='Kolom: %{y}<br>Baris: %{x}<extra></extra>'
            ))
            
            # Garis setiap 10 cm
            for i in range(0, MAX_ROW + 1, 10):
                fig.add_shape(
                    type="line",
                    x0=i, y0=0,
                    x1=i, y1=MAX_COL,
                    line=dict(color="rgba(255,255,255,0.2)", width=1, dash="dash"),
                    xref="x", yref="y"
                )
            
            for i in range(0, MAX_COL + 1, 10):
                fig.add_shape(
                    type="line",
                    x0=0, y0=i,
                    x1=MAX_ROW, y1=i,
                    line=dict(color="rgba(255,255,255,0.2)", width=1, dash="dash"),
                    xref="x", yref="y"
                )
            
            # Path
            if len(st.session_state.position_history) > 1:
                history = list(st.session_state.position_history)
                cols_path = [p[0] for p in history]
                rows_path = [p[1] for p in history]
                
                fig.add_trace(go.Scatter(
                    x=rows_path,
                    y=cols_path,
                    mode='lines+markers',
                    name='Jalur Robot',
                    line=dict(color='#3b7dd8', width=2),
                    marker=dict(size=4, color='#5a9cff', symbol='circle'),
                    hovertemplate='Kolom: %{y}<br>Baris: %{x}<extra></extra>'
                ))
                
                if len(history) > 0:
                    fig.add_trace(go.Scatter(
                        x=[history[0][1]],
                        y=[history[0][0]],
                        mode='markers',
                        name='🏁 Start',
                        marker=dict(size=14, color='#2ea043', symbol='circle', line=dict(color='white', width=2))
                    ))
                
                fig.add_trace(go.Scatter(
                    x=[row],
                    y=[col],
                    mode='markers',
                    name='📍 Current',
                    marker=dict(size=18, color='#ff4444', symbol='star', line=dict(color='white', width=2))
                ))
            
            fig.update_layout(
                title='Tracking Pergerakan Robot (70 cm × 90 cm)',
                xaxis_title='Baris (cm)',
                yaxis_title='Kolom (cm)',
                xaxis=dict(range=[0, MAX_ROW + 1], tickmode='linear', dtick=10, gridcolor='rgba(255,255,255,0.05)'),
                yaxis=dict(range=[0, MAX_COL + 1], tickmode='linear', dtick=10, gridcolor='rgba(255,255,255,0.05)', autorange='reversed'),
                height=600,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                hovermode='closest',
                margin=dict(l=60, r=40, t=60, b=60)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### 📊 Informasi Posisi")
            
            if auto_active:
                st.success("🤖 Auto Mode ACTIVE")
            else:
                st.info("🔧 Manual Mode")
            
            if auto_complete:
                st.success("✅ Auto Mode COMPLETE")
            
            st.divider()
            
            st.metric("📍 Kolom (cm)", f"{kolom} / {MAX_COL}")
            st.metric("📍 Baris (cm)", f"{row} / {MAX_ROW}")
            st.metric("🧹 Cleaned", f"{status.get('cleaned_cells', 0)} / {TOTAL_CELLS} cm²")
            st.metric("📈 Progress", f"{status.get('clean_progress', 0):.1f}%")
            st.metric("📏 Track Points", f"{len(st.session_state.position_history)}")
            
            katrol_dir = status.get('katrol_direction', '-')
            roda_dir = status.get('roda_direction', '-')
            
            if katrol_dir == "NAIK":
                dir_text = "⬆ Naik"
            elif katrol_dir == "TURUN":
                dir_text = "⬇ Turun"
            elif roda_dir == "MAJU":
                dir_text = "➡ Maju"
            elif roda_dir == "MUNDUR":
                dir_text = "⬅ Mundur"
            else:
                dir_text = "⏹ Diam"
            
            st.metric("🧭 Arah", dir_text)
        
        st.markdown("---")
        st.markdown("#### 📈 Posisi Over Time")
        
        if len(st.session_state.position_history) > 1:
            history_list = list(st.session_state.position_history)
            times = list(range(len(history_list)))
            cols_data = [p[0] for p in history_list]
            rows_data = [p[1] for p in history_list]
            
            fig2 = go.Figure()
            
            fig2.add_trace(go.Scatter(
                x=times,
                y=cols_data,
                mode='lines+markers',
                name='Kolom (cm)',
                line=dict(color='#3b7dd8', width=2),
                marker=dict(size=6, color='#5a9cff'),
                hovertemplate='Time: %{x}<br>Kolom: %{y} cm<extra></extra>'
            ))
            
            fig2.add_trace(go.Scatter(
                x=times,
                y=rows_data,
                mode='lines+markers',
                name='Baris (cm)',
                line=dict(color='#d29922', width=2),
                marker=dict(size=6, color='#e3b341'),
                hovertemplate='Time: %{x}<br>Baris: %{y} cm<extra></extra>'
            ))
            
            fig2.update_layout(
                title='Pergerakan Kolom & Baris (cm)',
                height=300,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                xaxis=dict(title='Time (step)', gridcolor='rgba(255,255,255,0.05)'),
                yaxis=dict(title='Kolom (cm)', range=[0, MAX_COL + 1], tickmode='linear', dtick=10, gridcolor='rgba(255,255,255,0.05)'),
                yaxis2=dict(title='Baris (cm)', range=[0, MAX_ROW + 1], tickmode='linear', dtick=10, gridcolor='rgba(255,255,255,0.05)', overlaying='y', side='right'),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                margin=dict(l=60, r=60, t=40, b=40)
            )
            
            st.plotly_chart(fig2, use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🗑️ Clear Tracking", use_container_width=True, key="clear_tracking"):
                st.session_state.position_history.clear()
                st.rerun()
        
        with col2:
            if st.button("📥 Export Data", use_container_width=True, key="export_tracking"):
                if len(st.session_state.position_history) > 0:
                    history_list = list(st.session_state.position_history)
                    df = pd.DataFrame(history_list, columns=['Kolom (cm)', 'Baris (cm)'])
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"robot_tracking_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        key="download_tracking"
                    )
    else:
        st.info("⏳ Menunggu data posisi...")

# ============================================
# TAB 4: LOGS
# ============================================

with tab4:
    st.subheader("📋 Event Logs")
    
    logs = fetch_logs()
    if logs:
        df = pd.DataFrame(logs)
        df.columns = ['Time', 'Level', 'Message']
        
        level_filter = st.selectbox("Filter Level", ["All", "INFO", "WARN", "ERROR", "SUCCESS"])
        if level_filter != "All":
            df = df[df['Level'] == level_filter]
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        if st.button("📥 Export CSV", use_container_width=True, key="export_csv"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"robot_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_csv"
            )
    else:
        st.info("📭 No logs")

# ============================================
# AUTO REFRESH
# ============================================

if st.session_state.auto_refresh:
    time.sleep(3)
    st.rerun()
