"""
BERT Features Extracted from streamlit_app.py
===============================================
This file contains all BERT-related code from the main streamlit application.

Extracted sections:
1. BERT Imports and Fallback Class
2. BERT Initialization in WebAIPowerPointApp
3. BERT Enhancement Function
4. BERT Parameter in main processing
5. BERT UI Elements
6. BERT Statistics Display
7. BERT Refinement Details UI
8. BERT Sidebar Information

Author: Extracted from streamlit_app.py
Date: 2025-08-21
"""

import streamlit as st
import os

# 1. BERT IMPORTS AND FALLBACK CLASS (Lines 27-57)

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

# 2. BERT INITIALIZATION IN WebAIPowerPointApp (Lines 89-109)

class WebAIPowerPointApp:
    def __init__(self, gemini_key, pexels_key=None):
        """Khởi tạo app cho web interface - BERT section only"""
        # ... other initialization code ...
        
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

# 3. BERT ENHANCEMENT FUNCTION (Lines 130-143)

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
            
            # ... other enhancement code ...
            
        except Exception as e:
            print(f"Warning: Advanced features enhancement failed: {e}")
            return slides_data

# 4. BERT PARAMETER IN MAIN PROCESSING (Lines 199-219)

    def process_text_to_presentation(self, input_text: str, slide_count: int = 5, use_charts: bool = False, use_diagrams: bool = False, use_animations: bool = False, advanced_mode: bool = False, use_quickchart: bool = False, use_bert: bool = False, progress_callback=None) -> tuple:
        """Xử lý văn bản thành presentation với advanced features, QuickChart và BERT"""
        try:
            # ... processing code ...
            
            # Advanced processing if enabled
            if advanced_mode or use_charts or use_diagrams or use_animations or use_quickchart or use_bert:
                update_progress(3, 10, "⚡ Đang xử lý advanced features...")
                slides_data = self._enhance_slides_with_advanced_features(
                    slides_data, use_charts, use_diagrams, use_animations, use_quickchart, use_bert
                )
                update_progress(4, 10, "✅ Advanced features đã hoàn tất")
            
            # ... rest of processing ...

# 5. BERT UI ELEMENTS (Lines 1143-1146)

def bert_ui_checkbox():
    """BERT UI checkbox element"""
    use_bert = st.sidebar.checkbox("🧠 Tinh chỉnh BERT", value=True, help="Sử dụng AI để cải thiện văn bản")
    
    # Quality indicator calculation
    # features_count = sum([use_images, use_quickchart, use_mermaid, use_bert])
    return use_bert

# 6. BERT STATISTICS DISPLAY (Lines 1641-1672)

def display_bert_statistics(slides_data, use_bert):
    """Display BERT refinement statistics"""
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

# 7. BERT QUALITY INDICATORS IN SLIDE LIST (Lines 1718-1741)

def display_slide_with_bert_indicators(slides):
    """Display slide list with BERT quality indicators"""
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

# 8. BERT REFINEMENT DETAILS UI (Lines 1744-1794)

def display_bert_refinement_details(slides, use_bert):
    """Display detailed BERT refinement comparison"""
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

# 9. BERT FEATURES IN SIDEBAR CONDITIONS (Lines 1375-1388)

def calculate_features_with_bert(use_bert, use_quickchart, use_mermaid, use_animations, advanced_mode):
    """Calculate feature text and timing with BERT"""
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
    
    return features_str, estimated_time

# 10. BERT PROCESSING CONDITIONS (Lines 1505-1540)

def check_bert_processing_conditions(use_bert, use_quickchart, use_mermaid, advanced_mode):
    """Check if BERT processing should be enabled"""
    # Step 3: Enhanced processing - Parallel processing
    if use_bert or use_quickchart or use_mermaid or advanced_mode:
        # Enhanced processing with BERT
        return True
    return False

def call_bert_processing(app, slides_data, use_bert, use_quickchart, use_mermaid, use_charts, use_diagrams, use_animations, advanced_mode):
    """Call the processing function with BERT parameters"""
    result = app.process_text_to_presentation(
        # ... other parameters ...
        use_bert=use_bert,
        # ... other parameters ...
    )
    return result

# 11. BERT SIDEBAR INFORMATION (Lines 1908-1949)

def display_bert_sidebar_info(use_bert, use_quickchart, use_mermaid, use_animations, advanced_mode):
    """Display BERT information in sidebar"""
    
    # Status check
    if advanced_mode:
        st.success("🚀 **Advanced Mode ON** - Sử dụng tất cả tính năng AI!")
    elif any([use_animations, use_quickchart, use_mermaid, use_bert]):
        st.info("⭐ **Smart Features ON** - Slides sẽ được tối ưu!")
    else:
        st.warning("📝 **Basic Mode** - Chỉ text và hình ảnh cơ bản")
    
    # QuickChart & Mermaid info
    if use_quickchart or use_mermaid or use_bert:
        st.markdown("### 🎯 AI Features Active")
        
        features_info = []
        if use_quickchart:
            features_info.append("**📊 QuickChart.io**: Tự động tạo Bar, Line, Pie charts")
        if use_mermaid:
            features_info.append("**🌊 Mermaid.js**: Process flows, org charts, timelines")
        if use_bert:
            features_info.append("**🧠 BERT**: AI refine content, improve text quality")
        
        for info in features_info:
            st.markdown(f"- {info}")
        
        st.markdown("""
        - **🎨 Professional**: High-quality vector graphics
        - **📥 Download**: All enhancements embedded in PowerPoint
        """)
        
        # BERT specific info
        if use_bert:
            st.markdown("### 🧠 BERT Capabilities")
            st.markdown("""
            **Content Intelligence:**
            - 📝 **Smart Text Refinement**: Cải thiện cấu trúc câu và từ ngữ
            - 🎯 **Context Enhancement**: Thêm độ sâu và context phù hợp 
            - 📊 **Quality Assessment**: Đánh giá và tối ưu chất lượng nội dung
            - 💡 **Content Suggestions**: Gợi ý cải thiện tự động
            - 🔄 **Before/After**: So sánh nội dung gốc vs đã refine
            
            **Processing Features:**
            - 🎤 **Speaking Notes**: Tối ưu cho thuyết trình
            - 📋 **Bullet Points**: Cân bằng độ dài và rõ ràng
            - 🏗️ **Structure**: Phân tích và cải thiện cấu trúc
            - 🌍 **Vietnamese**: Tối ưu đặc biệt cho tiếng Việt
            """)
            
            # Show BERT availability status
            # Note: This would need to check processor.bert_available if available
            st.info("✅ BERT được kích hoạt - Nội dung sẽ được AI tinh chỉnh!")

# 12. BERT IN RESPONSIVE FONT SYSTEM CONDITIONS (Lines 1950-1964)

def check_bert_responsive_font_conditions(use_quickchart, use_mermaid, use_bert, advanced_mode):
    """Check if responsive font system should be displayed with BERT"""
    # Responsive Font System info
    if any([use_quickchart, use_mermaid, use_bert, advanced_mode]):
        return True
    return False

# USAGE EXAMPLE

def example_usage():
    """Example of how to use the extracted BERT features"""
    
    # Initialize BERT
    app = WebAIPowerPointApp(gemini_key="your_key", pexels_key="your_pexels_key")
    
    # UI Elements
    use_bert = bert_ui_checkbox()
    use_quickchart = True  # example
    use_mermaid = True     # example
    
    # Feature calculation
    features_str, estimated_time = calculate_features_with_bert(
        use_bert, use_quickchart, use_mermaid, False, False
    )
    
    # Processing with BERT
    if check_bert_processing_conditions(use_bert, use_quickchart, use_mermaid, False):
        print("BERT processing enabled")
    
    # Display functions (would be called in main UI)
    # display_bert_statistics(slides_data, use_bert)
    # display_bert_refinement_details(slides, use_bert)
    # display_bert_sidebar_info(use_bert, use_quickchart, use_mermaid, False, False)

if __name__ == "__main__":
    print("BERT Features Extracted Successfully!")
    print("This file contains all BERT-related functionality from streamlit_app.py")
    print("Use the functions above to integrate BERT features into your application.")
