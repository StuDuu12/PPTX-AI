import streamlit as st
import os
from modules.bert_refiner import BertContentRefiner
from streamlit_app import WebAIPowerPointApp  # reuse class
import base64

def main():
    st.set_page_config(page_title="AI PowerPoint Generator", page_icon="📊", layout="wide")

    # Session state init
    if 'api_keys_configured' not in st.session_state:
        st.session_state.api_keys_configured = False
        st.session_state.gemini_key = os.getenv('GEMINI_API_KEY', '')
        st.session_state.pexels_key = os.getenv('PEXELS_API_KEY', '')
        if st.session_state.gemini_key:
            st.session_state.api_keys_configured = True

    st.title("AI PowerPoint Generator")

    tab_input, tab_setup, tab_output = st.tabs(["📝 Nhập nội dung", "⚙️ Cấu hình", "📦 Kết quả"])

    input_text = ""

    with tab_input:
        st.subheader("Chọn cách nhập")
        method = st.radio("Input method", ["Direct", "Upload", "Demo"], horizontal=True)
        if method == "Direct":
            input_text = st.text_area("Nội dung", height=300, placeholder="Dán nội dung ở đây...")
        elif method == "Upload":
            up = st.file_uploader("Tải tệp .txt/.md", type=["txt","md"])
            if up:
                input_text = up.read().decode("utf-8", errors="ignore")
                st.code(input_text[:300])
        else:
            demos = {
                "AI & Giáo dục": "AI đang thay đổi cách dạy và học...",
                "Báo cáo kinh doanh": "Q1: 120k, Q2: 145k, Q3: 180k, Q4: 220k...",
                "Phát triển bền vững": "Biến đổi khí hậu và các giải pháp..."
            }
            chosen = st.selectbox("Demo", list(demos.keys()))
            input_text = demos[chosen]
            st.code(input_text[:400])

    with tab_setup:
        st.subheader("Cài đặt trình bày")
        colA, colB = st.columns(2)
        with colA:
            slide_count = st.slider("📑 Số slide", 3, 15, 5)
            template_option = st.selectbox("🎨 Phong cách", ["Academic", "Professional", "Modern"])
        with colB:
            use_images = st.checkbox("🖼️ Hình ảnh minh họa", value=True)
            use_quickchart = st.checkbox("📊 Charts", value=True)
            use_mermaid = st.checkbox("🔄 Diagrams", value=True)
            use_bert = st.checkbox("🧠 BERT refine", value=True)

    with tab_output:
        st.subheader("Tạo & Tải xuống")
        disabled = not (st.session_state.get("api_keys_configured") and st.session_state.get("gemini_key") and input_text.strip())
        go = st.button("🚀 Generate", type="primary", disabled=disabled, use_container_width=True)
        if disabled:
            st.info("Nhập API key & nội dung ở tab trước để bật Generate")

        if 'last_result' not in st.session_state:
            st.session_state.last_result = None

        if go:
            prog = st.progress(0, text="Đang khởi tạo…")
            msg = st.status("Đang tạo bài trình bày", state="running")

            def progress_callback(step, total, message):
                pct = int((step / total) * 100)
                prog.progress(min(pct, 100), text=message)

            try:
                app = WebAIPowerPointApp(gemini_key=st.session_state.gemini_key, pexels_key=st.session_state.pexels_key)
                result = app.process_text_to_presentation(
                    input_text, slide_count,
                    use_charts=False, use_diagrams=False, use_animations=False,
                    advanced_mode=False,
                    use_quickchart=(use_quickchart or use_mermaid),
                    use_bert=use_bert,
                    progress_callback=progress_callback
                )
                prog.progress(100, text="Hoàn tất")
                msg.update(label="Tạo xong ✅", state="complete")
                st.session_state.last_result = result
            except Exception as e:
                msg.update(label="Có lỗi xảy ra", state="error")
                st.error(str(e))

        if st.session_state.last_result:
            res = st.session_state.last_result
            if len(res) == 4:
                result_path, slides_data, image_paths, quickchart_paths = res
            else:
                result_path, slides_data, image_paths = res
                quickchart_paths = {}

            if result_path and os.path.exists(result_path):
                filename = os.path.basename(result_path)
                size_kb = os.path.getsize(result_path) / 1024
                st.success(f"Đã tạo **{filename}** ({size_kb:.1f} KB)")
                with open(result_path, "rb") as f:
                    st.download_button("📥 Tải PowerPoint", f, file_name=filename, mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")
                with st.expander("📋 Tóm tắt"):
                    st.write(f"**Tiêu đề:** {slides_data.get('presentation_title','Untitled')}")
                    st.write(f"**Số slide:** {len(slides_data.get('slides', []))}")
                    if quickchart_paths:
                        st.write(f"**Charts/Diagrams:** {len(quickchart_paths)}")
                    if use_bert and slides_data.get("bert_refinement_stats"):
                        s = slides_data["bert_refinement_stats"]
                        st.write(f"**BERT Improved Content:** {s.get('improved_content',0)}/{s.get('total_slides',0)}  •  Avg Quality {s.get('average_quality',0):.2f}")

if __name__ == "__main__":
    main()
