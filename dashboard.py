"""
================================================================================
🚀 AutoScaling NASA Log - Dashboard UI
================================================================================
Run: streamlit run dashboard.py
================================================================================
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import requests
import os

# =============================================================================
# CONFIG
# =============================================================================
API_URL = "http://localhost:8000"
st.set_page_config(
    page_title="🚀 AutoScaling NASA Log",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CUSTOM CSS
# =============================================================================
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0e1117 0%, #1a1a2e 100%);
    }
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #2d3748;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    .save-card {
        background: linear-gradient(135deg, #143322 0%, #1a4a2e 100%);
        border: 2px solid #2ecc71;
        border-radius: 15px;
        padding: 25px;
        text-align: center;
    }
    .cost-card {
        background: linear-gradient(135deg, #331414 0%, #4a1a1a 100%);
        border: 2px solid #e74c3c;
        border-radius: 15px;
        padding: 25px;
        text-align: center;
    }
    .scale-up { background: linear-gradient(135deg, rgba(231, 76, 60, 0.2) 0%, rgba(192, 57, 43, 0.3) 100%); border: 2px solid #e74c3c; border-radius: 15px; padding: 20px; text-align: center; }
    .scale-down { background: linear-gradient(135deg, rgba(46, 204, 113, 0.2) 0%, rgba(39, 174, 96, 0.3) 100%); border: 2px solid #2ecc71; border-radius: 15px; padding: 20px; text-align: center; }
    .maintain { background: linear-gradient(135deg, rgba(149, 165, 166, 0.2) 0%, rgba(127, 140, 141, 0.3) 100%); border: 2px solid #95a5a6; border-radius: 15px; padding: 20px; text-align: center; }
    h1 { background: linear-gradient(90deg, #1f77b4, #2ecc71); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# API HELPER FUNCTIONS
# =============================================================================
def check_api_health():
    """Check if backend API is running."""
    try:
        r = requests.get(f"{API_URL}/health", timeout=2)
        return r.status_code == 200
    except:
        return False

def get_forecast(steps=4):
    """Get traffic forecast."""
    try:
        r = requests.get(f"{API_URL}/forecast", params={"timestamp": "now", "steps": steps}, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def get_scaling_recommendation(predicted_requests, current_servers):
    """Get scaling recommendation."""
    try:
        r = requests.get(f"{API_URL}/recommend-scaling", 
                        params={"predicted_requests": predicted_requests, "current_servers": current_servers}, 
                        timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def get_cost_report(hours=24):
    """Get cost comparison report."""
    try:
        r = requests.get(f"{API_URL}/cost-report", params={"simulation_hours": hours}, timeout=30)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def get_metrics():
    """Get current system metrics."""
    try:
        r = requests.get(f"{API_URL}/metrics", timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None

# =============================================================================
# HEADER
# =============================================================================
col1, col2 = st.columns([4, 1])
with col1:
    st.markdown("# 🚀 AutoScaling Command Center")
    st.markdown("*Hệ thống dự báo lưu lượng và tự động điều chỉnh server - NASA Log Data*")
with col2:
    if check_api_health():
        st.markdown("""
            <div style="text-align: right; padding: 15px;">
                <span style="color: #2ecc71; font-size: 24px;">●</span>
                <span style="color: #2ecc71; font-weight: 600;"> API ONLINE</span>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style="text-align: right; padding: 15px;">
                <span style="color: #e74c3c; font-size: 24px;">●</span>
                <span style="color: #e74c3c; font-weight: 600;"> API OFFLINE</span>
            </div>
        """, unsafe_allow_html=True)
        st.error("⚠️ Backend chưa chạy! Hãy chạy: `uvicorn app:app --reload --port 8000`")

st.divider()

# =============================================================================
# SIDEBAR - CONTROL PANEL
# =============================================================================
with st.sidebar:
    st.markdown("## ⚙️ Control Panel")
    st.divider()
    
    st.markdown("### 📊 Forecast Settings")
    forecast_steps = st.slider("Số khoảng 15 phút dự báo", 1, 24, 8)
    
    st.divider()
    
    st.markdown("### 🖥️ Server Settings")
    current_servers = st.number_input("Số server hiện tại", 1, 20, 2)
    
    st.divider()
    
    st.markdown("### 💰 Cost Simulation")
    sim_hours = st.selectbox("Thời gian mô phỏng", [6, 12, 24, 48, 72, 168], index=2, 
                             format_func=lambda x: f"{x} giờ ({x//24} ngày)" if x >= 24 else f"{x} giờ")
    
    st.divider()
    
    st.markdown("### 📖 API Documentation")
    st.markdown("[📚 Swagger UI](http://localhost:8000/docs)")

# =============================================================================
# MAIN CONTENT - TAB LAYOUT
# =============================================================================
tab1, tab2, tab3 = st.tabs(["📈 Dự Báo & Scaling", "💰 Phân Tích Chi Phí", "📊 System Metrics"])

# -----------------------------------------------------------------------------
# TAB 1: FORECAST & SCALING
# -----------------------------------------------------------------------------
with tab1:
    st.markdown("## 🔮 Dự Báo Lưu Lượng")
    
    if st.button("🚀 Chạy Dự Báo", use_container_width=True, type="primary"):
        with st.spinner("Đang dự báo với XGBoost model..."):
            forecast_data = get_forecast(forecast_steps)
        
        if forecast_data and forecast_data.get('status') == 'success':
            predictions = forecast_data['predictions']
            df = pd.DataFrame(predictions)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Metrics row
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🤖 Model", forecast_data['model'])
            with col2:
                st.metric("📊 RMSE", forecast_data['metrics']['model_rmse'])
            with col3:
                st.metric("📉 MAPE", forecast_data['metrics']['model_mape'])
            with col4:
                st.metric("🔮 Predictions", len(predictions))
            
            # Chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['timestamp'], 
                y=df['predicted_requests'],
                mode='lines+markers',
                name='Predicted Requests',
                line=dict(color='#1f77b4', width=3),
                fill='tozeroy',
                fillcolor='rgba(31, 119, 180, 0.2)'
            ))
            
            # Add threshold lines
            capacity = current_servers * 1000
            fig.add_hline(y=capacity * 0.85, line_dash="dash", line_color="#e74c3c", 
                         annotation_text=f"Scale Up Threshold (85%)")
            fig.add_hline(y=capacity * 0.30, line_dash="dash", line_color="#2ecc71",
                         annotation_text=f"Scale Down Threshold (30%)")
            
            fig.update_layout(
                title=f"Dự báo lưu lượng {forecast_steps * 15} phút tới",
                xaxis_title="Thời gian",
                yaxis_title="Số requests",
                template="plotly_dark",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Scaling Recommendation
            st.markdown("### ⚡ Khuyến Nghị Scaling")
            max_predicted = df['predicted_requests'].max()
            
            scaling = get_scaling_recommendation(max_predicted, current_servers)
            
            if scaling:
                action = scaling['action']
                style_class = "scale-up" if "UP" in action else "scale-down" if "DOWN" in action else "maintain"
                icon = "⬆️" if "UP" in action else "⬇️" if "DOWN" in action else "➡️"
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"""
                        <div class="{style_class}">
                            <h1 style="margin:0">{icon}</h1>
                            <h2 style="margin:10px 0">{action}</h2>
                            <p style="color:#aaa">{scaling['reason']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.metric("🖥️ Target Servers", scaling['target_servers'])
                    st.metric("💵 Chi phí/giờ", scaling['cost_estimate']['hourly'])
                    st.metric("📅 Chi phí/tháng", scaling['cost_estimate']['monthly'])
            
            # Data table
            with st.expander("📋 Xem chi tiết dự báo"):
                st.dataframe(df, use_container_width=True)
        else:
            st.error("❌ Không thể lấy dữ liệu dự báo. Kiểm tra Backend API.")

# -----------------------------------------------------------------------------
# TAB 2: COST ANALYSIS
# -----------------------------------------------------------------------------
with tab2:
    st.markdown("## 💰 Phân Tích Chi Phí - ĐIỂM CỘNG")
    st.markdown("So sánh **Static Deployment** (10 servers cố định) vs **AutoScaling** (động)")
    
    if st.button("📊 Tạo Báo Cáo Chi Phí", use_container_width=True, type="primary"):
        with st.spinner(f"Đang mô phỏng {sim_hours} giờ dữ liệu NASA..."):
            cost_data = get_cost_report(sim_hours)
        
        if cost_data:
            # Main metrics
            static = cost_data['cost_comparison']['static_deployment']
            auto = cost_data['cost_comparison']['auto_scaling']
            savings = cost_data['savings']
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                    <div class="cost-card">
                        <h4 style="color:#e74c3c; margin:0">❌ Static Deployment</h4>
                        <h1 style="color:#ff6b6b; margin:15px 0">{static['total_cost']}</h1>
                        <p style="color:#999; margin:0">{static['servers']} servers cố định</p>
                        <p style="color:#666; font-size:12px">{static['cost_per_hour']}/hour</p>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                    <div class="save-card">
                        <h4 style="color:#2ecc71; margin:0">✅ AutoScaling</h4>
                        <h1 style="color:#6bff9a; margin:15px 0">{auto['total_cost']}</h1>
                        <p style="color:#999; margin:0">Trung bình {auto['avg_servers']} servers</p>
                        <p style="color:#666; font-size:12px">Tự động điều chỉnh</p>
                    </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #142233 0%, #1a3352 100%); 
                                border: 2px solid #3498db; border-radius: 15px; padding: 25px; text-align: center;">
                        <h4 style="color:#3498db; margin:0">💵 TIẾT KIỆM</h4>
                        <h1 style="color:#5dade2; margin:15px 0">{savings['amount']}</h1>
                        <p style="color:#2ecc71; font-weight:bold; margin:5px 0">{savings['percentage']}</p>
                        <p style="color:#f39c12; font-size:14px">📅 {savings['monthly_projection']}/tháng</p>
                    </div>
                """, unsafe_allow_html=True)
            
            # Conclusion
            st.markdown(f"""
                <div style="background: linear-gradient(90deg, #1a1a2e 0%, #16213e 100%);
                            padding: 20px; border-radius: 10px; border-left: 4px solid #f39c12; margin: 20px 0;">
                    <h4 style="color: #f39c12; margin: 0 0 10px 0;">📋 Kết Luận cho Giám Khảo</h4>
                    <p style="color: #ddd; margin: 0; font-size: 16px;">{cost_data['conclusion']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Scaling events chart
            st.markdown("### 📈 Scaling Events Timeline")
            
            if cost_data.get('scaling_history'):
                events_df = pd.DataFrame(cost_data['scaling_history'])
                
                fig = go.Figure()
                
                # Scale up events
                scale_up = events_df[events_df['action'] == 'scale_up']
                fig.add_trace(go.Scatter(
                    x=scale_up['timestamp'], y=scale_up['to_servers'],
                    mode='markers', name='Scale Up',
                    marker=dict(color='#e74c3c', size=15, symbol='triangle-up')
                ))
                
                # Scale down events
                scale_down = events_df[events_df['action'] == 'scale_down']
                fig.add_trace(go.Scatter(
                    x=scale_down['timestamp'], y=scale_down['to_servers'],
                    mode='markers', name='Scale Down',
                    marker=dict(color='#2ecc71', size=15, symbol='triangle-down')
                ))
                
                fig.update_layout(
                    title=f"Các sự kiện Scaling ({cost_data['scaling_events']} lần)",
                    xaxis_title="Thời gian",
                    yaxis_title="Số servers",
                    template="plotly_dark",
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
                
                with st.expander(f"📋 Chi tiết {len(events_df)} scaling events"):
                    st.dataframe(events_df, use_container_width=True)
            
            # Summary stats
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"📊 **Data points analyzed:** {cost_data['data_points_used']}")
            with col2:
                st.info(f"🔄 **Total scaling events:** {cost_data['scaling_events']}")
        else:
            st.error("❌ Không thể tạo báo cáo. Kiểm tra Backend API.")

# -----------------------------------------------------------------------------
# TAB 3: SYSTEM METRICS
# -----------------------------------------------------------------------------
with tab3:
    st.markdown("## 📊 System Metrics")
    
    metrics = get_metrics()
    
    if metrics:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            load = metrics.get('current_load', 0)
            status = "🟢" if load < 1000 else "🟡" if load < 2000 else "🔴"
            st.metric(f"{status} Current Load", f"{load:,.0f} req/min")
        
        with col2:
            st.metric("🖥️ Running Servers", metrics.get('running_servers', 'N/A'))
        
        with col3:
            st.metric("💵 24h Cost", f"${metrics.get('cost_24h', 0):.2f}")
        
        with col4:
            acc = metrics.get('model_accuracy', {})
            st.metric("🎯 Model RMSE", f"{acc.get('rmse', 'N/A')}")
        
        st.divider()
        
        # Model accuracy details
        st.markdown("### 🤖 Model Performance")
        acc = metrics.get('model_accuracy', {})
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("RMSE", f"{acc.get('rmse', 'N/A')}")
        with col2:
            st.metric("MAE", f"{acc.get('mae', 'N/A')}")
        with col3:
            mape = acc.get('mape', 0)
            st.metric("MAPE", f"{mape*100:.1f}%" if mape else "N/A")
    else:
        st.warning("⚠️ Không thể kết nối tới API để lấy metrics.")

# =============================================================================
# FOOTER
# =============================================================================
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <p>🚀 <strong>AutoScaling NASA Log System</strong> - AI-Powered Server Scaling</p>
    <p style="font-size: 12px;">Built with FastAPI + Streamlit + XGBoost | Data: NASA HTTP Logs 1995</p>
</div>
""", unsafe_allow_html=True)
