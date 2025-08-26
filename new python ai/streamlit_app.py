"""
Streamlit Web Interface cho AI PowerPoint Generator
Giao diện web đơn giản để người dùng tạo presentation với API keys được ẩn hoàn toàn
"""
try:
    import streamlit as st
    import os
    import sys
    from typing import Dict
    import tempfile
    import base64
    from modules.bert_refiner import BertContentRefiner 
except ImportError as e:
    st.error(f"❌ Lỗi import modules: {e}")
    st.stop()

# Thêm modules vào Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_dir = os.path.join(current_dir, 'modules')
sys.path.insert(0, current_dir)
sys.path.insert(0, modules_dir)

# Import các modules
try:
    from content_processor import SlideContentProcessor
    from image_searcher import ImageSearcher, FallbackImageProvider
    from powerpoint_generator import PowerPointGenerator
    from enhanced_powerpoint_generator import EnhancedPowerPointGenerator
    from quickchart_mermaid import QuickChartMermaidGenerator
    
    # BERT import with memory error handling
    try:
        from modules.bert_refiner import BertContentRefiner
        BERT_AVAILABLE = True
    except (ImportError, OSError, MemoryError) as e:
        print(f"⚠️ BERT module not available: {e}")
        BERT_AVAILABLE = False
        
        # Lightweight fallback class
        class BertContentRefiner:
            def __init__(self, force_lightweight=True):
                self.available = False
                self.refinement_stats = {
                    "total_slides": 0,
                    "improved_content": 0, 
                    "improved_bullets": 0,
                    "improved_speaking": 0,
                    "average_quality": 0.8,
                    "method_used": "rule-based"
                }
            
            def refine_content(self, data):
                # Basic text cleaning without ML models
                slides = data.get("slides", [])
                for slide in slides:
                    slide["quality_score"] = 0.8
                    slide["bert_refined"] = False
                
                self.refinement_stats["total_slides"] = len(slides)
                data["bert_refinement_stats"] = self.refinement_stats
                return data

except ImportError as e:
    st.error(f"❌ Lỗi import modules: {e}")
    st.stop()

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    st.warning("⚠️ python-dotenv không có sẵn")

class WebAIPowerPointApp:
    def __init__(self, gemini_key, pexels_key=None):
        """Khởi tạo app cho web interface"""
        self.gemini_api_key = gemini_key
        self.pexels_api_key = pexels_key
        
        # Khởi tạo components
        self.content_processor = SlideContentProcessor(self.gemini_api_key)
        
        # Khởi tạo QuickChart & Mermaid generator
        try:
            self.quickchart_generator = QuickChartMermaidGenerator()
            self.quickchart_available = True
            print("✅ QuickChart & Mermaid generator loaded")
        except:
            self.quickchart_generator = None
            self.quickchart_available = False
            print("⚠️ QuickChart & Mermaid not available")
        
        # Khởi tạo BERT Content Refiner với memory optimization
        try:
            # Try normal BERT first
            self.bert_refiner = BertContentRefiner()
            self.bert_available = self.bert_refiner.available
            
            if self.bert_available:
                print("✅ BERT Content Refiner loaded")
            else:
                print("⚠️ BERT models not available, using rule-based refinement")
                
        except Exception as e:
            print(f"⚠️ BERT initialization failed: {e}")
            # Fallback to lightweight mode
            try:
                print("🔄 Trying lightweight mode...")
                self.bert_refiner = BertContentRefiner(force_lightweight=True)
                self.bert_available = False
                print("✅ Lightweight text refiner loaded")
            except:
                self.bert_refiner = None
                self.bert_available = False
                print("❌ Text refinement not available")
        
        if self.pexels_api_key:
            self.image_searcher = ImageSearcher(self.pexels_api_key)
            self.use_images = True
        else:
            self.image_searcher = None
            self.use_images = False
            
        # Try enhanced generator first, fallback to basic
        try:
            self.powerpoint_generator = EnhancedPowerPointGenerator()
            self.enhanced_available = True
            print("✅ Enhanced PowerPoint Generator loaded")
        except:
            self.powerpoint_generator = PowerPointGenerator()
            self.enhanced_available = False
            print("⚠️ Using basic PowerPoint Generator")
    
    def _enhance_slides_with_advanced_features(self, slides_data: dict, use_charts: bool, use_diagrams: bool, use_animations: bool, use_quickchart: bool = False, use_bert: bool = False) -> dict:
        """Enhance slides với advanced features bao gồm QuickChart và BERT"""
        try:
            # Chỉ enhance nếu có enhanced generator
            if not hasattr(self, 'enhanced_available') or not self.enhanced_available:
                return slides_data
            
            # BERT Content Refinement trước tiên
            if use_bert and self.bert_available:
                try:
                    slides_data = self.bert_refiner.refine_content(slides_data)
                    print("✅ BERT content refinement completed")
                except Exception as e:
                    print(f"Warning: BERT refinement failed: {e}")
            
            # Process slides với advanced features
            slides = slides_data.get("slides", [])
            
            for slide in slides:
                slide_content = slide.get("content", "")
                
                # QuickChart.io & Mermaid.js processing
                if use_quickchart and self.quickchart_available:
                    try:
                        quickchart_result = self.quickchart_generator.process_slide_content(
                            slide_content, 
                            slide.get("slide_title", "")
                        )
                        
                        # Thêm chart URLs nếu có
                        if quickchart_result["chart_urls"]:
                            slide["quickchart_urls"] = quickchart_result["chart_urls"]
                            slide["chart_data"] = quickchart_result["charts"]
                            slide["has_quickchart"] = True
                        
                        # Thêm diagram URLs nếu có
                        if quickchart_result["diagram_urls"]:
                            slide["mermaid_urls"] = quickchart_result["diagram_urls"]
                            slide["mermaid_data"] = quickchart_result["diagrams"]
                            slide["has_mermaid"] = True
                            
                    except Exception as e:
                        print(f"Warning: QuickChart processing failed for slide: {e}")
                
                # Thêm charts nếu có số liệu (fallback method)
                if use_charts and "content" in slide:
                    content = slide.get("content", "")
                    # Kiểm tra có số liệu không
                    if any(char.isdigit() for char in content):
                        slide["has_chart"] = True
                        slide["chart_type"] = "auto"
                
                # Thêm diagrams cho process flows (fallback method)
                if use_diagrams and "content" in slide:
                    content = slide.get("content", "").lower()
                    if any(keyword in content for keyword in ["bước", "step", "giai đoạn", "quy trình"]):
                        slide["has_diagram"] = True
                        slide["diagram_type"] = "process_flow"
                
                # Thêm animations
                if use_animations:
                    slide["animations"] = True
            
            return slides_data
            
        except Exception as e:
            print(f"Warning: Advanced features enhancement failed: {e}")
            return slides_data

    def process_text_to_presentation(self, input_text: str, slide_count: int = 5, use_charts: bool = False, use_diagrams: bool = False, use_animations: bool = False, advanced_mode: bool = False, use_quickchart: bool = False, use_bert: bool = False, progress_callback=None) -> tuple:
        """Xử lý văn bản thành presentation với advanced features, QuickChart và BERT"""
        try:
            def update_progress(step, total, message=""):
                if progress_callback:
                    progress_callback(step, total, message)
            
            # Bước 1: Phân tích nội dung với Gemini
            update_progress(1, 10, "🧠 Đang phân tích nội dung với Gemini AI...")
            slides_data = self.content_processor.process_text_to_slides(input_text, slide_count)
            
            if not slides_data:
                return None

            update_progress(2, 10, "✅ Đã tạo cấu trúc slides")
            
            # Advanced processing if enabled
            if advanced_mode or use_charts or use_diagrams or use_animations or use_quickchart or use_bert:
                update_progress(3, 10, "⚡ Đang xử lý advanced features...")
                slides_data = self._enhance_slides_with_advanced_features(
                    slides_data, use_charts, use_diagrams, use_animations, use_quickchart, use_bert
                )
                update_progress(4, 10, "✅ Advanced features đã hoàn tất")
            
            # Bước 2: Tìm ảnh
            update_progress(5, 10, "🖼️ Đang tìm và tải ảnh minh họa...")
            image_paths = {}
            if self.use_images and self.image_searcher:
                image_paths = self.image_searcher.get_images_for_all_slides(slides_data)
            else:
                # Tạo placeholder images nhanh hơn
                fallback_provider = FallbackImageProvider()
                slides = slides_data.get("slides", [])
                for i, slide in enumerate(slides):
                    slide_number = slide.get("slide_number", 1)
                    keywords = slide.get("image_keywords", "presentation")
                    placeholder_path = fallback_provider.create_placeholder_image(keywords)
                    if placeholder_path:
                        image_paths[slide_number] = placeholder_path
                    
                    # Mini progress cho từng ảnh
                    if progress_callback and len(slides) > 1:
                        sub_progress = 5 + (i + 1) / len(slides) * 1  # From 5 to 6
                        progress_callback(sub_progress, 10, f"🖼️ Đang xử lý ảnh {i+1}/{len(slides)}")
            
            update_progress(6, 10, f"✅ Đã tải {len(image_paths)} ảnh")
            
            # Bước 3: Download QuickChart images nếu có
            quickchart_paths = {}
            if use_quickchart and self.quickchart_available:
                update_progress(7, 10, "📊 Đang tạo charts và diagrams...")
                slides = slides_data.get("slides", [])
                chart_count = 0
                for slide in slides:
                    slide_number = slide.get("slide_number", 1)
                    
                    # Download chart images
                    if slide.get("quickchart_urls"):
                        for i, url in enumerate(slide["quickchart_urls"]):
                            filename = f"chart_{slide_number}_{i}.png"
                            downloaded_path = self.quickchart_generator.download_image(url, filename)
                            if downloaded_path:
                                key = f"chart_{slide_number}_{i}"
                                quickchart_paths[key] = downloaded_path
                                chart_count += 1
                    
                    # Download mermaid images
                    if slide.get("mermaid_urls"):
                        for i, url in enumerate(slide["mermaid_urls"]):
                            filename = f"mermaid_{slide_number}_{i}.png"
                            downloaded_path = self.quickchart_generator.download_image(url, filename)
                            if downloaded_path:
                                key = f"mermaid_{slide_number}_{i}"
                                quickchart_paths[key] = downloaded_path
                                chart_count += 1
                
                update_progress(8, 10, f"✅ Đã tạo {chart_count} charts/diagrams")
            else:
                update_progress(8, 10, "⏭️ Bỏ qua charts (không được chọn)")
            
            # Bước 4: Tạo PowerPoint với enhanced features
            update_progress(9, 10, "📝 Đang tạo file PowerPoint...")
            presentation_title = slides_data.get("presentation_title", "AI Generated Presentation")
            
            # Tạo filename unique
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ai_presentation_{timestamp}.pptx"
            
            # Sử dụng enhanced generator nếu có advanced features
            if (advanced_mode or use_charts or use_diagrams or use_quickchart) and hasattr(self, 'enhanced_available') and self.enhanced_available:
                update_progress(9.5, 10, "🚀 Sử dụng Enhanced PowerPoint Generator...")
                # Enhanced generator luôn sử dụng filepath parameter
                result_path = self.powerpoint_generator.save_presentation(
                    filepath=filename,
                    slides_data=slides_data, 
                    image_paths=image_paths,
                    quickchart_paths=quickchart_paths
                )
            else:
                # Fallback - kiểm tra loại generator
                update_progress(9.5, 10, "📝 Đang lưu presentation...")
                self.powerpoint_generator.add_metadata(
                    title=presentation_title,
                    author="AI PowerPoint Generator"
                )
                
                # Nếu là Enhanced generator thì dùng filepath, không thì dùng filename
                if self.powerpoint_generator.__class__.__name__ == 'EnhancedPowerPointGenerator':
                    result_path = self.powerpoint_generator.save_presentation(
                        filepath=filename,
                        slides_data=slides_data, 
                        image_paths=image_paths
                    )
                else:
                    # Basic PowerPointGenerator
                    result_path = self.powerpoint_generator.save_presentation(
                        slides_data=slides_data, 
                        image_paths=image_paths,
                        filename=filename
                    )
            
            update_progress(10, 10, "✅ Hoàn thành!")
            return result_path, slides_data, image_paths, quickchart_paths
            
        except Exception as e:
            if progress_callback:
                progress_callback(0, 10, f"❌ Lỗi: {e}")
            st.error(f"❌ Lỗi xử lý: {e}")
            return None

def create_download_link(file_path: str, filename: str) -> str:
    """Tạo link download cho file PowerPoint"""
    try:
        with open(file_path, "rb") as f:
            bytes_data = f.read()
        
        b64 = base64.b64encode(bytes_data).decode()
        
        return f'''
        <a href="data:application/vnd.openxmlformats-officedocument.presentationml.presentation;base64,{b64}" 
           download="{filename}" 
           style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
           📥 Tải xuống PowerPoint
        </a>
        '''
    except Exception as e:
        return f"❌ Lỗi tạo link download: {e}"

def show_enhanced_loading(stage: str, progress: int, details: str = "", performance_info: dict = None):
    """Hiển thị loading animation với enhanced visual effects - ẩn performance metrics"""
    
    # Performance metrics đã được ẩn hoàn toàn
    perf_html = ""
    
    loading_html = f"""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin: 1rem 0; box-shadow: 0 10px 30px rgba(0,0,0,0.3); color: white; text-align: center;">
        <div style="width: 60px; height: 60px; border: 4px solid #f3f3f3; border-top: 4px solid #4CAF50; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 1rem;"></div>
        <div style="font-size: 1.2rem; font-weight: bold; margin-bottom: 1rem;">{stage}</div>
        <div style="width: 100%; max-width: 400px; background: rgba(255,255,255,0.2); border-radius: 10px; overflow: hidden; margin-bottom: 1rem; height: 8px;">
            <div style="height: 100%; background: linear-gradient(90deg, #4CAF50, #45a049); border-radius: 10px; transition: width 0.3s ease; box-shadow: 0 2px 10px rgba(76, 175, 80, 0.3); width: {progress}%;"></div>
        </div>
        <div style="color: rgba(255,255,255,0.9); font-size: 0.9rem; margin-top: 0.5rem;">{details}</div>
        <div style="background: rgba(255,255,255,0.1); padding: 0.5rem 1rem; border-radius: 8px; color: rgba(255,255,255,0.8); font-size: 0.8rem; margin-top: 0.5rem;">
            🚀 Processing with enhanced AI algorithms • ⚡ Fast mode enabled
        </div>
    </div>
    <style>
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
    """
    return loading_html

def show_success_notification(title: str, details: str = ""):
    """Hiển thị success notification với animation - đã ẩn performance info"""
    
    # Không hiển thị performance info nữa
    success_html = f"""
    <div style="background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); color: white; padding: 1.5rem; border-radius: 15px; text-align: center; margin: 1rem 0; animation: successPulse 0.6s ease-out; box-shadow: 0 5px 20px rgba(76, 175, 80, 0.4);">
        <div style="font-size: 3rem; margin-bottom: 0.5rem; animation: checkmark 0.6s ease-in-out;">✅</div>
        <div style="font-size: 1.3rem; font-weight: bold; margin-bottom: 0.5rem;">{title}</div>
        <div style="font-size: 0.9rem; opacity: 0.9;">{details}</div>
    </div>
    <style>
        @keyframes successPulse {{
            0% {{ transform: scale(0.8); opacity: 0; }}
            50% {{ transform: scale(1.05); }}
            100% {{ transform: scale(1); opacity: 1; }}
        }}
        @keyframes checkmark {{
            0% {{ transform: scale(0); }}
            50% {{ transform: scale(1.2); }}
            100% {{ transform: scale(1); }}
        }}
    </style>
    """
    return success_html

def main():
    """Main Streamlit app với bảo mật API keys và optimized loading"""
    
    # Page config với performance optimizations
    st.set_page_config(
        page_title="HNUE AI Generator",
        page_icon="pic/Logo.png",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state trước tiên
    if 'api_keys_configured' not in st.session_state:
        st.session_state.api_keys_configured = False
        st.session_state.gemini_key = ""
        st.session_state.pexels_key = ""
        st.session_state.app_preloaded = False

        # Tự động load từ environment nếu có
        env_gemini = os.getenv('GEMINI_API_KEY', '')
        env_pexels = os.getenv('PEXELS_API_KEY', '')
        
        if env_gemini:
            st.session_state.gemini_key = env_gemini
            st.session_state.pexels_key = env_pexels
            st.session_state.api_keys_configured = True

    
    # Initialize preloaded flag if not exists
    if 'app_preloaded' not in st.session_state:
        st.session_state.app_preloaded = False
    

    # Page config
    st.set_page_config(
        page_title="AI PowerPoint Generator - HNUE",
        page_icon="pic/Logo.png",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS cho giao diện thế hệ mới - Ultra Modern Design
    st.markdown("""
    <style>
        /* Import Google Fonts - Academic Style */
        @import url('https://fonts.googleapis.com/css2?family=Times+New+Roman&family=Crimson+Text:wght@400;600;700&family=Source+Sans+Pro:wght@300;400;600;700&display=swap');
        
        /* Global Styles - Soft Blue & Comfortable Theme */
        .stApp {
            background: linear-gradient(135deg, #F0F8FF 0%, #E6F3FF 50%, #E0F2F1 100%);
            font-family: 'Crimson Text', serif;
        }
        
        /* Main container - Clean & Comfortable */
        .main .block-container {
            padding-top: 2rem;
            padding-left: 2rem;
            padding-right: 2rem;
            max-width: 1200px;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
            margin: 2rem auto;
            border: 1px solid rgba(0, 0, 0, 0.05);
        }
        
        /* Header styling - Modern Blue (Easier to read) */
        h1 {
            color: #2C3E50 !important;
            text-shadow: 0 1px 3px rgba(44, 62, 80, 0.2);
            font-family: 'Crimson Text', serif;
            font-weight: 700;
            font-size: 3.5rem !important;
            text-align: center;
            margin-bottom: 0.5rem;
        }
        
        @keyframes academicGlow {
            0% { filter: drop-shadow(0 0 5px rgba(44, 62, 80, 0.2)); }
            100% { filter: drop-shadow(0 0 10px rgba(44, 62, 80, 0.3)); }
        }
        
        /* Subtitle styling - Modern Gray (Darker, easier to read) */
        h3 {
            color: #34495E;
            text-align: center;
            font-weight: 600;
            opacity: 0.9;
            margin-bottom: 2rem;
            font-family: 'Source Sans Pro', sans-serif;
        }
        
        /* Modern Card Design (Blue-Gray theme) */
        .glass-container {
            background: rgba(255, 255, 255, 0.98);
            border: 2px solid #5DADE2;
            border-radius: 15px;
            padding: 2rem;
            margin: 1rem 0;
            box-shadow: 0 8px 32px rgba(93, 173, 226, 0.15);
        }
        
        /* Modern Badge System (Blue-White-Gray colors) */
        .security-badge {
            background: linear-gradient(135deg, #2C3E50, #34495E);
            color: white;
            padding: 0.8rem 1.5rem;
            border-radius: 25px;
            font-weight: 600;
            text-align: center;
            margin: 1rem 0;
            box-shadow: 0 4px 15px rgba(44, 62, 80, 0.2);
        }
        
        .warning-badge {
            background: linear-gradient(135deg, #5DADE2, #3498DB);
            color: white;
            padding: 0.8rem 1.5rem;
            border-radius: 25px;
            font-weight: 600;
            text-align: center;
            box-shadow: 0 4px 15px rgba(93, 173, 226, 20);
        }
        
        /* Modern Input Styling (Blue theme) */
        .stTextInput > div > div > input {
            background: rgba(255, 255, 255, 0.95) !important;
            border: 2px solid #5DADE2 !important;
            border-radius: 8px !important;
            color: #2C3E50 !important;
            transition: all 0.3s ease !important;
            font-family: 'Source Sans Pro', sans-serif !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #3498DB !important;
            box-shadow: 0 0 8px rgba(52, 152, 219, 15) !important;
        }
        
        .stTextInput > div > div > input[type="password"] {
            background: rgba(248, 249, 250, 0.95) !important;
            border: 2px solid #AED6F1 !important;
        }
        
        /* Enhanced Academic Sidebar - HNUE Style (Softer, easier colors) */
        .css-1d391kg {
            background: linear-gradient(180deg, #4A5568 0%, #2D3748 50%, #1A202C 100%);
            color: white;
            border-right: 3px solid #E2E8F0;
            box-shadow: 3px 0 15px rgba(74, 85, 104, 0.5);
        }
        
        /* University Logo Area (softer gold) */
        .css-1d391kg::before {
            content: "🎓";
            display: block;
            text-align: center;
            font-size: 2.5rem;
            padding: 1rem;
            background: rgba(237, 242, 247, 0.1);
            margin-bottom: 1rem;
            border-bottom: 2px solid #E2E8F0;
        }
        
        /* Sidebar headers - University Style (Clean, readable) */
        .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3 {
            color: #E2E8F0 !important;
            font-weight: 700 !important;
            font-family: 'Crimson Text', serif !important;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.2) !important;
            border-bottom: 1px solid rgba(226, 232, 240, 0.3) !important;
            padding-bottom: 0.5rem !important;
            margin-bottom: 1rem !important;
        }
        
        /* Sidebar expander styling (Clean design) */
        .css-1d391kg .streamlit-expanderHeader {
            background: rgba(226, 232, 240, 0.1) !important;
            border: 1px solid rgba(226, 232, 240, 0.2) !important;
            border-radius: 8px !important;
            color: #E2E8F0 !important;
            font-weight: 600 !important;
            margin: 0.5rem 0 !important;
        }
        
        .css-1d391kg .streamlit-expanderHeader:hover {
            background: rgba(226, 232, 240, 0.2) !important;
            border-color: #E2E8F0 !important;
        }
        
        /* Sidebar text styling */
        .css-1d391kg .stMarkdown {
            color: rgba(255, 255, 255, 0.9) !important;
        }
        
        /* Sidebar input fields (Clean, professional) */
        .css-1d391kg .stTextInput > div > div > input {
            background: rgba(255, 255, 255, 0.95) !important;
            border: 2px solid #CBD5E0 !important;
            border-radius: 6px !important;
            color: #2D3748 !important;
            font-weight: 500 !important;
        }
        
        .css-1d391kg .stTextInput > div > div > input:focus {
            border-color: #4299E1 !important;
            box-shadow: 0 0 8px rgba(66, 153, 225, 0.3) !important;
        }
        
        /* Sidebar slider styling (Clean blue theme) */
        .css-1d391kg .stSlider {
            padding: 1rem 0 !important;
        }
        
        .css-1d391kg .stSlider > div > div > div > div {
            background: linear-gradient(90deg, #4299E1, #3182CE) !important;
        }
        
        /* Sidebar selectbox styling */
        .css-1d391kg .stSelectbox > div > div {
            background: rgba(255, 255, 255, 0.95) !important;
            border: 2px solid #CBD5E0 !important;
            border-radius: 6px !important;
            color: #2D3748 !important;
        }
        
        /* Sidebar checkbox styling (Clean design) */
        .css-1d391kg .stCheckbox {
            background: rgba(226, 232, 240, 0.1) !important;
            padding: 0.5rem !important;
            border-radius: 6px !important;
            border: 1px solid rgba(226, 232, 240, 0.2) !important;
            margin: 0.3rem 0 !important;
        }
        
        .css-1d391kg .stCheckbox > label {
            color: white !important;
            font-weight: 500 !important;
        }
        
        /* Sidebar button styling (Professional blue theme) */
        .css-1d391kg .stButton > button {
            background: linear-gradient(135deg, #4299E1, #3182CE) !important;
            color: white !important;
            border: 2px solid #E2E8F0 !important;
            border-radius: 8px !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
            box-shadow: 0 4px 12px rgba(66, 153, 225, 0.3) !important;
        }
        
        .css-1d391kg .stButton > button:hover {
            background: linear-gradient(135deg, #2B6CB0, #2C5282) !important;
            color: white !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(66, 153, 225, 0.4) !important;
        }
        
        /* Modern Button Design (Blue-Gray theme) */
        .stButton > button {
            background: linear-gradient(135deg, #2C3E50, #34495E) !important;
            color: white !important;
            border: 2px solid #5DADE2 !important;
            border-radius: 8px !important;
            padding: 0.75rem 2rem !important;
            font-weight: 600 !important;
            font-size: 1.1rem !important;
            font-family: 'Source Sans Pro', sans-serif !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 15px rgba(44, 62, 80, 0.2) !important;
        }
        
        .stButton > button:hover {
            background: linear-gradient(135deg, #3498DB, #5DADE2) !important;
            color: white !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 25px rgba(52, 152, 219, 0.4) !important;
        }
        
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #3498DB, #5DADE2) !important;
            color: white !important;
            border: 2px solid #2C3E50 !important;
        }
        
        @keyframes modernButtonGlow {
            0% { box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3); }
            100% { box-shadow: 0 6px 25px rgba(44, 62, 80, 0.5); }
        }
        
        /* Modern Controls (Blue theme) */
        .stSlider > div > div > div > div {
            background: linear-gradient(90deg, #3498DB, #5DADE2) !important;
        }
        
        /* Modern checkboxes */
        .stCheckbox > label > div[data-testid="stCheckbox"] > div {
            background: rgba(255, 255, 255, 0.9) !important;
            border: 2px solid #3498DB !important;
            border-radius: 4px !important;
        }
        
        /* Modern selectbox */
        .stSelectbox > div > div {
            background: rgba(255, 255, 255, 0.9) !important;
            border: 2px solid #3498DB !important;
            border-radius: 8px !important;
            color: #2C3E50 !important;
        }
        
        /* Modern text areas */
        .stTextArea > div > div > textarea {
            background: rgba(255, 255, 255, 0.95) !important;
            border: 2px solid #3498DB !important;
            border-radius: 8px !important;
            color: #2C3E50 !important;
            font-family: 'Source Sans Pro', sans-serif !important;
        }
        
        .stTextArea textarea {
            color: #2C3E50 !important;
            background-color: rgba(255, 255, 255, 0.95) !important;
        }
        
        /* Enhanced radio buttons */
        .stRadio > div {
            background: rgba(255, 255, 255, 0.05);
            padding: 1rem;
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Enhanced expanders */
        .streamlit-expanderHeader {
            background: rgba(255, 255, 255, 0.1) !important;
            border-radius: 15px !important;
            backdrop-filter: blur(10px) !important;
        }
        
        /* Enhanced loading animations */
        .loading-container {
            background: linear-gradient(135deg, rgba(255,255,255,0.15), rgba(255,255,255,0.05));
            backdrop-filter: blur(25px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 25px;
            padding: 3rem;
            margin: 2rem 0;
            box-shadow: 0 12px 40px rgba(0,0,0,0.2);
            animation: containerFloat 4s ease-in-out infinite;
        }
        
        @keyframes containerFloat {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-5px); }
        }
        
        .loading-spinner {
            width: 80px;
            height: 80px;
            border: 5px solid rgba(255,255,255,0.3);
            border-top: 5px solid #00f260;
            border-radius: 50%;
            animation: advancedSpin 1.5s linear infinite;
            margin-bottom: 2rem;
        }
        
        @keyframes advancedSpin {
            0% { transform: rotate(0deg) scale(1); }
            50% { transform: rotate(180deg) scale(1.1); }
            100% { transform: rotate(360deg) scale(1); }
        }
        
        .loading-text {
            color: white;
            font-size: 1.4rem;
            font-weight: 700;
            text-align: center;
            margin-bottom: 1.5rem;
            text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }
        
        .progress-container {
            width: 100%;
            max-width: 500px;
            background: rgba(255,255,255,0.2);
            border-radius: 25px;
            overflow: hidden;
            margin-bottom: 2rem;
            height: 12px;
            box-shadow: inset 0 2px 10px rgba(0,0,0,0.2);
        }
        
        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #00f260, #0575e6, #667eea);
            border-radius: 25px;
            transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        
        .progress-bar::after {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
            animation: progressShine 2s infinite;
        }
        
        @keyframes progressShine {
            0% { left: -100%; }
            100% { left: 100%; }
        }
        
        .stage-indicator {
            color: rgba(255,255,255,0.95);
            font-size: 1rem;
            text-align: center;
            margin-top: 1rem;
            font-weight: 500;
        }
        
        .performance-metrics {
            background: rgba(255,255,255,0.15);
            padding: 1.5rem 2rem;
            border-radius: 20px;
            color: rgba(255,255,255,0.9);
            font-size: 0.95rem;
            margin-top: 1.5rem;
            border: 1px solid rgba(255,255,255,0.2);
            backdrop-filter: blur(15px);
        }
        
        /* Success animations with modern design */
        .success-container {
            background: linear-gradient(135deg, #00f260, #0575e6, #667eea);
            color: white;
            padding: 2.5rem;
            border-radius: 25px;
            text-align: center;
            margin: 2rem 0;
            animation: successAppear 0.8s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 15px 50px rgba(0, 242, 96, 0.3);
            position: relative;
            overflow: hidden;
        }
        
        .success-container::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
            animation: successSweep 3s infinite;
        }
        
        @keyframes successSweep {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        @keyframes successAppear {
            0% { transform: scale(0.8) translateY(20px); opacity: 0; }
            100% { transform: scale(1) translateY(0); opacity: 1; }
        }
        
        .success-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
            animation: successBounce 0.8s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            z-index: 1;
        }
        
        @keyframes successBounce {
            0%, 20%, 40%, 60%, 80% { transform: translateY(0) scale(1); }
            10%, 30%, 50%, 70%, 90% { transform: translateY(-15px) scale(1.1); }
        }
        
        .success-text {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            position: relative;
            z-index: 1;
        }
        
        .success-details {
            font-size: 1rem;
            opacity: 0.95;
            position: relative;
            z-index: 1;
        }
        
        /* Enhanced feature indicators */
        .speed-indicator {
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1);
            color: white;
            padding: 0.5rem 1.2rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 700;
            display: inline-block;
            margin: 0.3rem;
            animation: featurePulse 2s ease-in-out infinite;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        
        @keyframes featurePulse {
            0%, 100% { transform: scale(1); box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
            50% { transform: scale(1.05); box-shadow: 0 6px 20px rgba(0,0,0,0.3); }
        }
        
        /* Enhanced metrics display */
        .metric-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 20px;
            padding: 1.5rem;
            margin: 1rem 0;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: 800;
            color: #00f260;
            margin-bottom: 0.5rem;
            text-shadow: 0 2px 10px rgba(0, 242, 96, 0.3);
        }
        
        .metric-label {
            font-size: 1rem;
            color: rgba(255, 255, 255, 0.8);
            font-weight: 500;
        }
        
        /* Enhanced download section */
        .download-container {
            background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 25px;
            padding: 2rem;
            margin: 2rem 0;
            box-shadow: 0 10px 40px rgba(0,0,0,0.15);
            animation: downloadFloat 3s ease-in-out infinite;
        }
        
        @keyframes downloadFloat {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-3px); }
        }
        
        /* Enhanced footer */
        .footer {
            background: rgba(0,0,0,0.3);
            backdrop-filter: blur(10px);
            padding: 2rem;
            border-radius: 20px;
            margin-top: 3rem;
            text-align: center;
            color: rgba(255,255,255,0.8);
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            h1 { font-size: 2.5rem !important; }
            .glass-container { padding: 1.5rem; }
            .loading-container { padding: 2rem; }
            .success-container { padding: 2rem; }
        }
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, #764ba2, #667eea);
        }
        
        /* Additional modern animations */
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.8; }
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes readyPulse {
            0%, 100% { box-shadow: 0 8px 32px rgba(0, 242, 96, 0.3); }
            50% { box-shadow: 0 12px 40px rgba(0, 242, 96, 0.5); }
        }
        
        @keyframes securitySweep {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .fade-in {
            animation: fadeIn 0.6s ease-out;
        }
        
        /* Enhanced file upload */
        .stFileUploader > div > div {
            background: rgba(255, 255, 255, 0.1) !important;
            border: 2px dashed rgba(255, 255, 255, 0.3) !important;
            border-radius: 20px !important;
            backdrop-filter: blur(10px) !important;
        }
        
        /* Enhanced tabs */
        .stTabs [data-baseweb="tab-list"] {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 0.5rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            background: transparent;
            border-radius: 10px;
            transition: all 0.3s ease;
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #667eea, #764ba2) !important;
            color: white !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Academic Header với University Branding - All in one container
    st.markdown("""
    <div class="fade-in">
        <div style="text-align: center; margin: 2rem 0;">
            <div style="background: rgba(255,255,255,0.98); 
                        border: 3px solid #2C3E50; 
                        border-radius: 15px; 
                        padding: 3rem; 
                        margin: 2rem auto; 
                        max-width: 900px;
                        box-shadow: 0 15px 50px rgba(44,62,80,0.2);">
                <h1 style="margin: 0; line-height: 1.2; color: #2C3E50;">AI PowerPoint Generator</h1>
                <div style="font-size: 1.8rem; color: #34495E; margin: 1rem 0; font-weight: 600; font-family: 'Crimson Text', serif;">
                    Education Technology Platform
                </div>
                <div style="font-size: 1.1rem; color: #34495E; max-width: 700px; margin: 0 auto; line-height: 1.6; font-family: 'Source Sans Pro', sans-serif;">
                    Công cụ tạo bài giảng thông minh dành cho giảng viên và sinh viên - Ứng dụng AI tiên tiến trong giáo dục
                </div>
                <div style="margin-top: 2rem;">
                    <span style="background: #2C3E50; color: white; padding: 0.5rem 1rem; margin: 0.2rem; border-radius: 15px; font-size: 0.9rem;">🤖 Gemini AI</span>
                    <span style="background: #3498DB; color: white; padding: 0.5rem 1rem; margin: 0.2rem; border-radius: 15px; font-size: 0.9rem;">📊 Biểu đồ</span>
                    <span style="background: #5DADE2; color: white; padding: 0.5rem 1rem; margin: 0.2rem; border-radius: 15px; font-size: 0.9rem;">🧠 AI Nâng cao</span>
                    <span style="background: #34495E; color: white; padding: 0.5rem 1rem; margin: 0.2rem; border-radius: 15px; font-size: 0.9rem;">🎨 Thiết kế</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Removed old header
    # st.title("AI PowerPoint Generator - Future Power")
    # st.markdown("### Tự động tạo bài thuyết trình bằng AI")
    # st.markdown("##### Đưa ý tưởng của bạn vào cuộc sống với AI")
    
    # Academic Sidebar - HNUE Educational Theme
    st.sidebar.markdown("""      
    <div style="text-align: center; padding: 1rem; background: rgba(226,232,240,0.15); 
                border-radius: 10px; margin-bottom: 1rem; border: 1px solid rgba(226,232,240,0.3);">
        <div style="font-size: 1.2rem; color: #0e2d80; font-weight: 700; margin-bottom: 0.5rem; text-shadow: 1px 1px 2px rgba(0,0,0,0.2);">
            🏛️ Trường Đại học Sư phạm Hà Nội
        </div>
        <div style="font-size: 0.9rem; color: #000;">
            Khoa Công nghệ Thông tin
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("### 🎓 Hệ thống Tạo Bài giảng")
    
    # University API Keys section
    with st.sidebar.expander("🔐 Cấu hình API", expanded=not st.session_state.api_keys_configured):
        st.markdown("**Khóa truy cập AI Services:**")
        if not st.session_state.api_keys_configured:
            gemini_key = st.text_input("🧠 Google Gemini API", type="password", placeholder="AIzaSy...", help="Khóa API cho xử lý ngôn ngữ tự nhiên")
            pexels_key = st.text_input("� Pexels API (Tùy chọn)", type="password", placeholder="Không bắt buộc", help="Khóa API cho tìm kiếm hình ảnh")
            
            if st.button("💾 Lưu cấu hình", type="primary"):
                if gemini_key and gemini_key.startswith('AIzaSy'):
                    st.session_state.gemini_key = gemini_key
                    st.session_state.pexels_key = pexels_key
                    st.session_state.api_keys_configured = True
                    st.success("✅ Cấu hình đã được lưu!")
                    st.rerun()
                else:
                    st.error("❌ Khóa Gemini không hợp lệ")
        else:
            st.success("✅ Hệ thống đã được cấu hình")
            if st.button("🔄 Cấu hình lại"):
                st.session_state.api_keys_configured = False
                st.session_state.gemini_key = ""
                st.session_state.pexels_key = ""
                st.rerun()
    
    # Academic Settings với style riêng
    st.sidebar.markdown("### 📚 Thiết lập Bài giảng")
    
    slide_count = st.sidebar.slider("📑 Số slide", 3, 15, 5, help="Số lượng slide trong bài thuyết trình")
    template_option = st.sidebar.selectbox("🎨 Phong cách thiết kế", ["Academic", "Professional", "Modern"], help="Chọn template phù hợp với môi trường giảng dạy")
    
    st.sidebar.markdown("### 🤖 Tính năng AI")
    
    # Educational AI Features với description
    use_images = st.sidebar.checkbox("🖼️ Hình ảnh minh họa", value=True, help="Tự động thêm hình ảnh phù hợp với nội dung")
    use_quickchart = st.sidebar.checkbox("📊 Charts", value=True, help="Tạo biểu đồ từ dữ liệu số")
    use_mermaid = st.sidebar.checkbox("🔄 Diagrams", value=True, help="Tạo sơ đồ quy trình và mối quan hệ")
    use_bert = st.sidebar.checkbox("🧠 Tinh chỉnh BERT", value=True, help="Sử dụng AI để cải thiện văn bản")
    
    # Quality indicator
    features_count = sum([use_images, use_quickchart, use_mermaid, use_bert])
    quality_level = "Cơ bản" if features_count <= 1 else "Nâng cao" if features_count <= 3 else "Chuyên nghiệp"
    
    st.sidebar.markdown(f"""
    <div style="background: rgba(226,232,240,0.15); padding: 0.8rem; border-radius: 8px; 
                border: 1px solid rgba(226,232,240,0.3); margin: 1rem 0;">
        <div style="color: #0e2d80; font-weight: 600; text-align: center; text-shadow: 1px 1px 2px rgba(0,0,0,0.2);">
            📈 Chất lượng: {quality_level}
        </div>
        <div style="color: #000; font-size: 0.8rem; text-align: center;">
            {features_count}/4 tính năng được kích hoạt
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Set deprecated features for backward compatibility
    use_charts = False
    use_diagrams = False
    use_animations = False
    advanced_mode = False
    image_layout = "AI Smart"
    content_balance = "Perfect Balance"
    content_detail = "Rich Detail"
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
         # Enhanced Input Methods với Modern Tabs - màu nhẹ nhàng dễ nhìn
        st.markdown("""
        <div style="background: linear-gradient(135deg, #E8F6F3, #D5F3F0); 
                    border: 2px solid #A3E4D7; 
                    border-radius: 15px; 
                    padding: 1.5rem; 
                    margin: 1rem 0; 
                    box-shadow: 0 4px 20px rgba(163, 228, 215, 0.2);">
            <div style="color: #2C5530; font-weight: 600; font-size: 1.1rem; margin-bottom: 0.5rem; text-align: center;">
                📥 Choose Your Input Method
            </div>
        """, unsafe_allow_html=True)
        
        # Hiển thị radio ngay trong thẻ xanh
        
        input_method = st.radio(
            "Choose Input Method",
            ["💬 Direct Input", "📄 Upload File", "🎯 Demo Examples"],
            horizontal=True,
            label_visibility="collapsed"
        )


        # Tiếp tục nội dung trong thẻ trắng
        st.markdown("""
        <div style="margin-top: 1rem;">
        """, unsafe_allow_html=True)
        
        input_text = ""
        
        if input_method == "💬 Direct Input":
            st.markdown("""
            <div style="color: rgba(255,255,255,0.9); background: rgb(247, 196, 203); border-radius: 12px; font-size: 0.95rem; margin: 1rem 0; text-align: center;">
                ✨ Paste your content below and watch AI transform it into a stunning presentation
            </div>
            """, unsafe_allow_html=True)
            
            # CSS for black text in textarea
            st.markdown("""
            <style>
            .stTextArea textarea {
                color: #000000 !important;
                background-color: #ffffff !important;
                border: 2px solid #dddddd !important;
                border-radius: 8px !important;
            }
            .stTextArea textarea::placeholder {
                color: #666666 !important;
            }
            .stTextArea > div > div > textarea {
                color: #000000 !important;
                background-color: #ffffff !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            input_text = st.text_area(
                "Content Input",
                height=300,
                placeholder="✨ Enter your content here...\n\nTip: The more detailed your content, the better your presentation will be!\n\nExample:\n- Main topic overview\n- Key points with explanations\n- Supporting details and examples\n- Conclusions and takeaways",
                label_visibility="collapsed"
            )
        
        elif input_method == "📄 Upload File":
            st.markdown("""
            <div style="color: rgba(255,255,255,0.9); font-size: 0.95rem; margin: 1rem 0; text-align: center;">
                📤 Upload your text file and let AI work its magic
            </div>
            """, unsafe_allow_html=True)
            
            uploaded_file = st.file_uploader(
                "Upload File",
                type=['txt', 'md'],
                label_visibility="collapsed"
            )
            if uploaded_file:
                input_text = str(uploaded_file.read(), "utf-8")
                st.markdown("""
                <div style="background: rgba(0, 242, 96, 0.1); 
                           border: 1px solid rgba(0, 242, 96, 0.3); 
                           border-radius: 15px; 
                           padding: 1rem; 
                           margin: 1rem 0;">
                    <div style="color: #00f260; font-weight: 600; text-align: center;">✅ File Loaded Successfully</div>
                    <div style="color: rgba(255,255,255,0.8); font-size: 0.9rem; text-align: center; margin-top: 0.5rem;">
                  Direct       Ready for AI processing
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.text_area("📖 File Preview:", value=input_text[:500] + "..." if len(input_text) > 500 else input_text, height=200, disabled=True)
        
        elif input_method == "🎯 Demo Examples":
            st.markdown("""
            <div style="color: rgba(255,255,255,0.9); font-size: 0.95rem; margin: 1rem 0; text-align: center;">
                🎭 Try our curated examples to see AI in action
            </div>
            """, unsafe_allow_html=True)
            demo_topics = {
                "🤖 Artificial Intelligence Revolution": """
                Artificial Intelligence is transforming our world at an unprecedented pace. From automating simple tasks 
                to solving humanity's most complex challenges, AI has become an indispensable tool in modern society.
                
                AI applications span across diverse domains: autonomous vehicles reducing traffic accidents, medical diagnosis 
                systems enabling early disease detection, intelligent chatbots enhancing customer service, and robotic automation 
                revolutionizing manufacturing processes.
                
                However, AI also presents significant challenges regarding ethics, privacy, and employment displacement. 
                We must develop AI responsibly to ensure benefits for all humanity while addressing potential risks and societal impacts.
                """,
                "🌍 Climate Change & Sustainability": """
                Climate change represents one of the most pressing challenges of the 21st century. Rising global temperatures 
                due to human activities, primarily fossil fuel combustion and deforestation, threaten our planet's future.
                
                The consequences are far-reaching: melting ice caps, rising sea levels, extreme weather events, and agricultural 
                disruption. These changes disproportionately affect vulnerable populations and ecosystems worldwide.
                
                Solutions require immediate action: transitioning to renewable energy sources, implementing sustainable practices, 
                protecting forests, and fostering international cooperation. Every individual and organization must contribute 
                to building a sustainable future for coming generations.
                """,
                "🚀 Tech Startup Ecosystem": """
                The technology startup ecosystem represents innovation and entrepreneurship in the digital age. Startups leverage 
                cutting-edge technology to solve real-world problems while creating value for society and stakeholders.
                
                Success factors include innovative ideas, strong team dynamics, market fit, and effective fundraising capabilities. 
                The startup journey involves identifying problems, developing solutions, validating markets, and scaling operations.
                
                Challenges are significant: intense competition, high failure rates, funding difficulties, and pressure for rapid growth. 
                However, successful startups can revolutionize industries and create lasting positive impact on global society.
                """,
                "📊 Advanced Business Analytics Demo": """
                Q4 2024 Business Performance Report - Exceeding All Expectations
                
                Quarterly Revenue Performance Throughout 2024:
                Q1: $120,000 in revenue with 15% growth
                Q2: $145,000 in revenue with 21% growth  
                Q3: $180,000 in revenue with 24% growth
                Q4: $220,000 in revenue with 22% growth
                
                Current Market Share Distribution Analysis:
                Our Company: 40% market leadership position
                Competitor A: 30% strong secondary position
                Competitor B: 20% emerging challenger
                Other Players: 10% fragmented remaining market
                
                Strategic Process Improvements Implemented This Year:
                Phase 1: Comprehensive customer data analysis and insights
                Phase 2: Product optimization based on user feedback
                Phase 3: E-commerce platform enhancement and automation
                Phase 4: Geographic market expansion into new regions
                Phase 5: Digital marketing strategy implementation and optimization
                
                Five-Year Revenue Growth Trajectory Analysis:
                2020: $80,000 baseline establishment
                2021: $95,000 steady growth phase
                2022: $120,000 acceleration period
                2023: $150,000 expansion success
                2024: $195,000 breakthrough performance
                
                Results demonstrate strategic alignment and establish strong foundation for 2025 ambitious growth targets.
                """,
                "🎓 Modern Education Technology": """
                Educational technology is revolutionizing how we learn and teach in the 21st century. Digital platforms, 
                AI-powered personalization, and immersive technologies are creating unprecedented learning opportunities.
                
                Key innovations include adaptive learning systems that adjust to individual student needs, virtual reality 
                classrooms providing immersive experiences, collaborative online platforms enabling global connections, 
                and AI tutoring systems offering personalized support.
                
                Benefits encompass increased accessibility, personalized learning paths, real-time assessment, and global 
                knowledge sharing. However, challenges include digital divide issues, screen time concerns, and maintaining 
                human connection in digital environments.
                """
            }
            
            selected_topic = st.selectbox(
                "Select Demo Topic",
                list(demo_topics.keys()),
                label_visibility="collapsed"
            )
            
            # Display topic with enhanced preview
            input_text = demo_topics[selected_topic]
            
            st.markdown(f"""
            <div style="background: rgba(102, 126, 234, 0.1); 
                       border: 1px solid rgba(102, 126, 234, 0.3); 
                       border-radius: 20px; 
                       padding: 1.5rem; 
                       margin: 1rem 0;">
                <div style="color: #667eea; font-weight: 600; font-size: 1rem; text-align: center; margin-bottom: 1rem;">
                    📖 Preview: {selected_topic}
                </div>
                <div style="color: rgba(255,255,255,0); font-size: 0.9rem; line-height: 1.6; max-height: 200px; overflow-y: auto;">
                    {input_text[:400]}{"..." if len(input_text) > 400 else ""}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        # AI Generator trong thẻ trắng
        # Enhanced Settings Display với Performance Metrics
        features_text = []
        if use_animations: features_text.append("🎬 Motion")
        if use_quickchart: features_text.append("🎯 Charts")
        if use_mermaid: features_text.append("🌊 Diagrams")
        if use_bert: features_text.append("🧠 AI Brain")
        if advanced_mode: features_text.append("⚡ Master")
        
        features_str = " • ".join(features_text) if features_text else "Standard Mode"
        
        # Enhanced performance estimation
        estimated_time = 12  # Base time optimized
        if use_bert: estimated_time += 4
        if use_quickchart or use_mermaid: estimated_time += 6
        if slide_count > 6: estimated_time += (slide_count - 6) * 1.5
        
        speed_class = "🚀 Lightning" if estimated_time <= 15 else "⚡ Fast" if estimated_time <= 25 else "🎯 Detailed"
        quality_score = "Premium" if len(features_text) >= 3 else "Professional" if len(features_text) >= 2 else "Standard"
        
        st.markdown(f"""
        <div style='background: rgb(243, 181, 189); 
                    backdrop-filter: blur(25px); 
                    border: 1px solid rgba(255,255,255,0.2); 
                    border-radius: 25px; 
                    padding: 2rem; 
                    margin: 2rem 0;
                    box-shadow: 0 12px 40px rgba(0,0,0,0.15);'>
            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; align-items: center;'>
                <div style='color: white;'>
                    <div style='font-weight: 700; font-size: 1.1rem; margin-bottom: 1rem; color: #667eea;'>📊 Configuration Summary</div>
                    <div style='line-height: 1.8; font-size: 0.95rem;'>
                        <div><strong>📑 Slides:</strong> {slide_count} slides</div>
                        <div><strong>� Style:</strong> {template_option}</div>
                        <div><strong>📐 Layout:</strong> {image_layout}</div>
                        <div><strong>📝 Detail:</strong> {content_detail}</div>
                        <div><strong>🎯 Features:</strong> {features_str}</div>
                    </div>
                </div>
                <div style='text-align: center;'>
                    <div style='background: rgba(255,255,255,0.1); border-radius: 20px; padding: 1.5rem; margin-bottom: 1rem;'>
                        <div class="speed-indicator" style="font-size: 1rem; margin: 0;">{speed_class}</div>
                        <div style='color: rgba(255,255,255,0.8); font-size: 0.9rem; margin-top: 0.5rem;'>Est. {estimated_time}s</div>
                    </div>
                    <div style='background: rgba(102, 126, 234, 0.2); border-radius: 15px; padding: 1rem;'>
                        <div style='color: #667eea; font-weight: 600; font-size: 0.9rem;'>Quality: {quality_score}</div>
                        <div style='color: rgba(255,255,255,0.7); font-size: 0.8rem;'>AI Enhanced</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        

        # Simple Validation
        if not st.session_state.api_keys_configured or not st.session_state.gemini_key:
            st.error("🔐 Please configure your Gemini API key in the sidebar")
            st.info("Get your free API key at: https://makersuite.google.com/app/apikey")
        elif not input_text.strip():
            st.warning("📝 Please enter your content or select a demo example")
        else:
            st.success("✅ Ready to generate your presentation!")
            
            # Simple Generate Button
            if st.button("🎨 Generate PowerPoint", type="primary", use_container_width=True):
                # Enhanced progress tracking với modern animation
                progress_container = st.container()
                loading_placeholder = st.empty()
                
                # Cache app initialization để tăng tốc
                @st.cache_resource
                def get_cached_app(gemini_key, pexels_key):
                    return WebAIPowerPointApp(
                        gemini_key=gemini_key,
                        pexels_key=pexels_key
                    )
                
                # Cache content processing để tránh xử lý lại
                @st.cache_data(ttl=300)  # Cache 5 phút
                def process_content_cached(text_content, slide_count_param):
                    return text_content, slide_count_param
                
                # Cache image search để tránh tải lại
                @st.cache_data(ttl=600)  # Cache 10 phút
                def cache_image_search(query):
                    # Placeholder for image caching
                    return query
                
                # Cache Gemini response để tránh API call lặp lại
                @st.cache_data(ttl=300)
                def cache_gemini_response(content_hash):
                    return None  # Will be filled by actual response
                
                # Tối ưu threading cho tốc độ
                import concurrent.futures
                
                try:
                    import time
                    start_time = time.time()
                    
                    # Pre-optimization: Kiểm tra cache trước
                    content_hash = hash(input_text + str(slide_count))
                    
                    # Step 1: Initialize app với enhanced loading - Super Optimized
                    loading_placeholder.markdown(
                        show_enhanced_loading(
                            "🚀 Turbo Mode Active", 
                            20,  # Bắt đầu với 20%
                            "High-speed processing..."
                        ), 
                        unsafe_allow_html=True
                    )
                    # Giảm sleep time để tăng tốc
                    time.sleep(0.1)  # Giảm từ 0.2 xuống 0.1
                    
                    app = get_cached_app(
                        gemini_key=st.session_state.gemini_key,
                        pexels_key=st.session_state.pexels_key
                    )
                    
                    # Step 2: Content analysis - Optimized
                    loading_placeholder.markdown(
                        show_enhanced_loading(
                            "⚡ Phân tích Nội dung (Fast)", 
                            35,  # Tăng progress nhanh hơn
                            "AI processing optimized..."
                        ), 
                        unsafe_allow_html=True
                    )
                    time.sleep(0.1)  # Giảm thời gian chờ
                    
                    # Step 3: Enhanced processing - Parallel processing
                    if use_bert or use_quickchart or use_mermaid or advanced_mode:
                        loading_placeholder.markdown(
                            show_enhanced_loading(
                                "🚀 Xử lý Parallel Features", 
                                50,  # Tăng progress
                                "Parallel processing active..."
                            ), 
                            unsafe_allow_html=True
                        )
                        time.sleep(0.1)  # Giảm thời gian chờ
                    
                    # Step 4: Process presentation với enhanced callback - Optimized
                    def progress_callback(step, total, message):
                        progress_value = 60 + (step / total) * 25  # From 60% to 85% - Faster progress
                        
                        loading_placeholder.markdown(
                            show_enhanced_loading(
                                "🚀 Tạo Slides ", 
                                int(progress_value), 
                                f"Optimized: {message}"
                            ), 
                            unsafe_allow_html=True
                        )
                    
                    # Sử dụng cached content processing
                    cached_content, cached_slide_count = process_content_cached(input_text, slide_count)
                    
                    result = app.process_text_to_presentation(
                        cached_content, 
                        cached_slide_count,
                        use_charts=use_charts,
                        use_diagrams=use_diagrams,  
                        use_animations=use_animations,
                        advanced_mode=advanced_mode,
                        use_quickchart=(use_quickchart or use_mermaid),
                        use_bert=use_bert,
                        progress_callback=progress_callback
                    )
                    
                    # Step 5: Finalizing - Optimized
                    loading_placeholder.markdown(
                        show_enhanced_loading(
                            "⚡ Finalizing (Optimized)", 
                            90,  # Tăng progress nhanh hơn
                            "Fast file generation..."
                        ), 
                        unsafe_allow_html=True
                    )
                    time.sleep(0.05)  # Giảm thời gian chờ đáng kể
                    
                    # Step 6: Complete với success notification - Faster
                    elapsed_time = time.time() - start_time
                    
                    loading_placeholder.markdown(
                        show_enhanced_loading(
                            "✅ Hoàn thành!", 
                            100, 
                            f"Completed in {elapsed_time:.1f}s"
                        ), 
                        unsafe_allow_html=True
                    )
                    time.sleep(0.3)  # Giảm từ 1s xuống 0.3s
                    loading_placeholder.empty()  # Clear loading area
                    
                    if result and len(result) >= 3:
                        if len(result) == 4:
                            result_path, slides_data, image_paths, quickchart_paths = result
                        else:
                            result_path, slides_data, image_paths = result
                            quickchart_paths = {}
                        
                        # Kiểm tra result_path có hợp lệ không
                        if result_path and os.path.exists(result_path):
                            # Success animation và message
                            st.markdown("""
                            <div class="success-animation" style="text-align: center; padding: 1rem; background: linear-gradient(45deg, #4CAF50, #45a049); color: white; border-radius: 10px; margin: 1rem 0;">
                                <h3>🎉 PowerPoint đã được tạo thành công!</h3>
                                <p>⚡ Tạo trong {:.1f} giây với AI tiên tiến</p>
                            </div>
                            """.format(elapsed_time), unsafe_allow_html=True)
                            
                            # Download section với enhanced UI - layout ngang
                            st.markdown("### 📥 Tải xuống")
                            
                            # Container ngang với fit-content
                            filename = os.path.basename(result_path)
                            file_size = os.path.getsize(result_path) / 1024  # KB
                            download_link = create_download_link(result_path, filename)
                            
                            # Download button above the file container
                            st.markdown(f"""
                            <div style="margin: 1rem 0; margin-right: 1rem; text-align: center;">
                                <a href="data:application/vnd.openxmlformats-officedocument.presentationml.presentation;base64,{create_download_link(result_path, filename).split('base64,')[1].split('"')[0]}" 
                                   download="{filename}" 
                                   style="display: inline-flex; align-items: center; gap: 0.5rem; background: linear-gradient(135deg, #4CAF50, #45a049); color: white; padding: 15px 25px; text-decoration: none; border-radius: 10px; font-weight: bold; transition: all 0.3s ease; box-shadow: 0 3px 10px rgba(76, 175, 80, 0.4); font-size: 1.1rem;">
                                    <span style="font-size: 1.3rem;">📥</span>
                                    <span>Tải xuống PowerPoint</span>
                                </a>
                            </div>
                            
                            <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; margin: 1rem 0; width: 100%; max-width: 600px; box-sizing: border-box; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                                <div style="display: flex; align-items: center; gap: 1rem;">
                                    <div style="font-size: 3rem;">📊</div>
                                    <div>
                                        <div style="font-weight: bold; font-size: 0.8rem; margin-bottom: 0.3rem; color: #2c3e50;">{filename}</div>
                                        <div style="color: #6c757d; font-size: 0.8rem; margin-bottom: 0.3rem;">{file_size:.2f} KB</div>
                                        <div style="color: #28a745; font-weight: bold; font-size: 0.8rem;">✅ Ready</div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Display QuickChart preview nếu có
                            if quickchart_paths:
                                with st.expander("🎯 QuickChart & Mermaid Preview", expanded=False):
                                    for key, path in quickchart_paths.items():
                                        if os.path.exists(path):
                                            st.image(path, caption=f"Generated: {key}", use_column_width=True)
                            
                            # Đóng container trung tâm trước summary
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Display summary - Left aligned like footer
                        with st.expander("📋 Tóm tắt Presentation", expanded=True):
                            title = slides_data.get("presentation_title", "Untitled")
                            slides = slides_data.get("slides", [])
                            st.write(f"**🏷️ Tiêu đề:** {title}")
                            st.write(f"**📄 Số slides:** {len(slides)}")
                            st.write(f"**🖼️ Số ảnh:** {len(image_paths)}")
                            
                            if quickchart_paths:
                                chart_count = len([k for k in quickchart_paths.keys() if k.startswith('chart_')])
                                mermaid_count = len([k for k in quickchart_paths.keys() if k.startswith('mermaid_')])
                                st.write(f"**📊 QuickChart graphs:** {chart_count}")
                                st.write(f"**🌊 Mermaid diagrams:** {mermaid_count}")
                            
                            # Display BERT refinement stats
                            bert_stats = slides_data.get("bert_refinement_stats")
                            if bert_stats and use_bert:
                                st.markdown("### 🧠 BERT Content Refinement Stats")
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.metric(
                                        label="📝 Improved Content",
                                        value=f"{bert_stats['improved_content']}/{bert_stats['total_slides']}",
                                        delta=f"{bert_stats['improved_content']} slides enhanced"
                                    )
                                    st.metric(
                                        label="📋 Improved Bullets", 
                                        value=f"{bert_stats['improved_bullets']}/{bert_stats['total_slides']}",
                                        delta=f"{bert_stats['improved_bullets']} slides optimized"
                                    )
                                
                                with col2:
                                    st.metric(
                                        label="🎤 Improved Speaking",
                                        value=f"{bert_stats['improved_speaking']}/{bert_stats['total_slides']}",
                                        delta=f"{bert_stats['improved_speaking']} slides enhanced"
                                    )
                                    st.metric(
                                        label="⭐ Average Quality",
                                        value=f"{bert_stats['average_quality']:.2f}",
                                        delta="Quality Score (0-1)"
                                    )
                                
                                # Quality breakdown
                                quality_color = "🟢" if bert_stats['average_quality'] > 0.8 else "🟡" if bert_stats['average_quality'] > 0.6 else "🔴"
                                st.write(f"**Overall Quality: {quality_color} {bert_stats['average_quality']:.2f}/1.0**")
                            
                            # Display Responsive Font Information  
                            if (advanced_mode or use_charts or use_diagrams or use_quickchart):
                                try:
                                    # Get font info from app's enhanced generator if available
                                    if hasattr(app, 'powerpoint_generator') and hasattr(app.powerpoint_generator, 'enhanced_generator'):
                                        font_info = app.powerpoint_generator.enhanced_generator.get_font_info()
                                        
                                        if font_info:
                                            st.markdown("### 🔤 Responsive Font System")
                                            col1, col2 = st.columns(2)
                                            
                                            with col1:
                                                st.metric(
                                                    label="📏 Scale Factor",
                                                    value=f"{font_info['scale_factor']:.2f}",
                                                    delta="Based on slide dimensions"
                                                )
                                                st.write(f"**📐 Dimensions:** {font_info['slide_dimensions']}")
                                            
                                            with col2:
                                                st.markdown("**🎯 Font Range:**")
                                                st.write(f"• Title: {font_info['font_sizes']['slide_title']}pt")
                                                st.write(f"• Content: {font_info['font_sizes']['content_normal']}pt")
                                                st.write(f"• Bullets: {font_info['font_sizes']['bullet_main']}pt")
                                            
                                            # Show responsive features
                                            with st.expander("🚀 Responsive Features", expanded=False):
                                                for feature in font_info['responsive_features']:
                                                    st.write(f"• {feature}")
                                except Exception as e:
                                    print(f"⚠️ Could not display font info: {e}")
                            
                            st.write("**📑 Danh sách slides:**")
                            for i, slide in enumerate(slides):
                                slide_title = slide.get("slide_title", "Untitled")
                                slide_type = slide.get("slide_type", "content")
                                
                                # Icons cho different slide types
                                icon = "🏆" if slide_type == "title" else "🎯" if slide_type == "conclusion" else "📝"
                                
                                # Thêm indicators cho special features
                                indicators = []
                                if slide.get("has_quickchart"):
                                    indicators.append("📊")
                                if slide.get("has_mermaid"):
                                    indicators.append("🌊")
                                if slide.get("has_chart"):
                                    indicators.append("📈")
                                if slide.get("has_diagram"):
                                    indicators.append("🔄")
                                
                                # BERT quality indicator
                                if slide.get("bert_refined") and slide.get("quality_score"):
                                    quality = slide["quality_score"]
                                    if quality > 0.8:
                                        indicators.append("✨")  # High quality
                                    elif quality > 0.6:
                                        indicators.append("⭐")  # Good quality
                                    else:
                                        indicators.append("💡")  # Needs improvement
                                
                                indicator_str = " ".join(indicators)
                                
                                # Show quality score if BERT was used
                                quality_display = ""
                                if slide.get("bert_refined") and slide.get("quality_score"):
                                    quality_display = f" (Q:{slide['quality_score']:.2f})"
                                
                                st.write(f"  {icon} {slide_title}{quality_display} {indicator_str}")
                        
                        # BERT Refinement Details (if used) - Center aligned and wide
                        if use_bert and any(slide.get("bert_refined") for slide in slides):
                            # Container trung tâm cho BERT details
                            st.markdown("""
                            <div style="display: flex; justify-content: center; margin: 2rem 0;">
                                <div style="width: 100%; max-width: 1200px;">
                            """, unsafe_allow_html=True)
                            
                            with st.expander("🧠 BERT Content Refinement Details", expanded=False):
                                st.markdown("### 📊 Before vs After Comparison")
                                
                                for i, slide in enumerate(slides):
                                    if not slide.get("bert_refined"):
                                        continue
                                    
                                    st.markdown(f"#### Slide {i+1}: {slide.get('slide_title', 'Untitled')}")
                                    
                                    # Content comparison
                                    if slide.get("original_detailed_content") and slide.get("detailed_content"):
                                        original = slide["original_detailed_content"]
                                        refined = slide["detailed_content"]
                                        
                                        if original != refined:
                                            col1, col2 = st.columns(2)
                                            with col1:
                                                st.markdown("**📝 Original Content:**")
                                                st.text_area("Original Content", original[:200] + "..." if len(original) > 200 else original, 
                                                           key=f"orig_content_{i}", height=100, disabled=True, label_visibility="hidden")
                                            with col2:
                                                st.markdown("**✨ BERT Refined:**")
                                                st.text_area("BERT Refined Content", refined[:200] + "..." if len(refined) > 200 else refined,
                                                           key=f"refined_content_{i}", height=100, disabled=True, label_visibility="hidden")
                                    
                                    # Bullet points comparison
                                    if slide.get("original_slide_content") and slide.get("slide_content"):
                                        original_bullets = slide["original_slide_content"]
                                        refined_bullets = slide["slide_content"]
                                        
                                        if original_bullets != refined_bullets:
                                            col1, col2 = st.columns(2)
                                            with col1:
                                                st.markdown("**📋 Original Bullets:**")
                                                for bullet in original_bullets[:3]:  # Show first 3
                                                    st.write(f"• {bullet}")
                                            with col2:
                                                st.markdown("**✨ BERT Refined:**")
                                                for bullet in refined_bullets[:3]:  # Show first 3
                                                    st.write(f"• {bullet}")
                                    
                                    # Quality score and suggestions
                                    if slide.get("quality_score") or slide.get("bert_suggestions"):
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            if slide.get("quality_score"):
                                                score = slide["quality_score"]
                                                score_color = "🟢" if score > 0.8 else "🟡" if score > 0.6 else "🔴"
                                                st.markdown(f"**Quality Score: {score_color} {score:.2f}**")
                                        
                                        with col2:
                                            if slide.get("bert_suggestions"):
                                                st.markdown("**💡 BERT Suggestions:**")
                                                for suggestion in slide["bert_suggestions"][:2]:  # Show first 2
                                                    st.write(f"• {suggestion}")
                                    
                                    st.markdown("---")
                        else:
                            # result_path is None or file doesn't exist
                            st.error("❌ Không thể tạo presentation. Lỗi trong quá trình lưu file.")
                            st.warning("💡 Vui lòng kiểm tra:")
                            st.write("• Quyền ghi file trong thư mục")
                            st.write("• Dung lượng ổ đĩa còn trống")
                            st.write("• Định dạng nội dung hợp lệ")
                            if result_path:
                                st.write(f"• Đường dẫn: {result_path}")
                        
                    else:
                        st.error("❌ Không thể tạo presentation. Vui lòng thử lại.")
                        
                except Exception as e:
                    st.markdown("""
                    <div style="background: linear-gradient(45deg, #ff6b6b, #ee5a52); color: white; padding: 1rem; border-radius: 10px; text-align: center;">
                        <h4>❌ Oops! Có lỗi xảy ra</h4>
                        <p>Đừng lo lắng, hãy thử lại với:</p>
                        <ul style="text-align: left; display: inline-block;">
                            <li>🔄 Refresh trang và thử lại</li>
                            <li>📝 Rút gọn nội dung text</li>
                            <li>⚙️ Tắt một số tính năng nâng cao</li>
                            <li>🔑 Kiểm tra API keys</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.expander("🔧 Chi tiết lỗi (cho developer)", expanded=False):
                        st.error(f"❌ Lỗi: {e}")
                        st.code(f"Error details: {str(e)}")
                    
                    # Clear loading area on error
                    loading_placeholder.empty()
    
   # Academic Footer
    st.markdown("""
    <div style="margin-top: 4rem; padding: 2rem; background: linear-gradient(135deg, #c8102e, #8B0000); 
                border-radius: 15px; text-align: center; color: white; margin-bottom: 2rem;">
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 2rem; margin-bottom: 2rem;">
            <div>
                <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">🎓</div>
                <div style="font-weight: 600; color: #FFD700;">Đại học Sư phạm Hà Nội</div>
                <div style="font-size: 0.9rem">Khoa Công nghệ Thông tin</div>
            </div>
            <div>
                <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">🤖</div>
                <div style="font-weight: 600; color: #FFD700;">Công nghệ AI</div>
                <div style="font-size: 0.9rem;">Gemini • QuickChart • BERT</div>
            </div>
            <div>
                <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">👥</div>
                <div style="font-weight: 600; color: #FFD700;">Phát triển bởi</div>
                <div style="font-size: 0.9rem;">Ms.Hoa & Chu Duy</div>
            </div>
        </div>
        <div style="text-align: center; padding-top: 1rem; border-top: 1px solid rgba(255,215,0,0.3);">
            <div style="color: rgba(255,255,255,0.8); font-size: 0.9rem;">
                🌟 Nền tảng Giáo dục Thông minh - Ứng dụng AI trong Giảng dạy
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Đóng thẻ trắng container chính
    st.markdown("</div>", unsafe_allow_html=True)
    
if __name__ == "__main__":
    main()
