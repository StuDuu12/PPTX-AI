"""
Module 1: AI Content Processing với Gemini API
Nhiệm vụ: Phân tích văn bản và tạo cấu trúc slide có định dạng JSON với tính năng Advanced
"""

import google.generativeai as genai
import json
import os
from typing import List, Dict, Optional
import re

class SlideContentProcessor:
    def __init__(self, api_key: str):
        """
        Khởi tạo processor với Gemini API key
        """
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def create_advanced_prompt(self, text: str, slide_count: int = 5) -> str:
        """
        Tạo prompt chi tiết để Gemini hiểu rõ yêu cầu với Advanced Features
        """
        prompt = f"""
Bạn là một chuyên gia tạo bài thuyết trình chuyên nghiệp với hơn 10 năm kinh nghiệm.

NHIỆM VỤ: Phân tích văn bản sau và tạo cấu trúc slide với NỘI DUNG CHI TIẾT và VISUALIZATION THÔNG MINH.

VĂN BẢN CẦN PHÂN TÍCH:
"{text}"

YÊU CẦU CỤTHỂ:
1. Tạo {slide_count} slide (bao gồm slide mở đầu và kết luận)
2. Tạo nội dung chi tiết, phong phú cho mỗi slide
3. Phân tích nội dung để đề xuất CHARTS và DIAGRAMS thay vì bullet points đơn thuần
4. Nhận diện số liệu → Tạo charts (bar, line, pie)
5. Nhận diện quy trình → Tạo process diagrams  
6. Nhận diện cấu trúc → Tạo hierarchy diagrams
7. Đề xuất animations phù hợp cho từng slide

ĐỊNH DẠNG JSON YÊU CẦU:
{{
  "presentation_title": "Tiêu đề tổng thể của bài thuyết trình",
  "total_slides": {slide_count},
  "slides": [
    {{
      "slide_number": 1,
      "slide_type": "title|content|chart|process|hierarchy",
      "slide_title": "Tiêu đề slide",
      "slide_content": ["Câu đầy đủ mô tả chi tiết ý tưởng 1", "Câu đầy đủ giải thích chi tiết ý tưởng 2", "Câu đầy đủ phân tích sâu ý tưởng 3"],
      "detailed_content": "Đoạn văn chi tiết 3-5 câu mở rộng nội dung slide, giải thích sâu sắc và cung cấp context đầy đủ cho người xem.",
      "visualization": {{
        "type": "chart|diagram|bullet_list",
        "chart_type": "bar|line|pie|none",
        "data_points": ["data1", "data2", "data3"],
        "labels": ["label1", "label2", "label3"],
        "diagram_style": "process_flow|hierarchy|comparison|none"
      }},
      "animation": {{
        "entrance": "fade_in|fly_in_left|grow",
        "emphasis": "pulse|grow|none",
        "transition": "fade|push|slide"
      }},
      "image_keywords": "từ khóa tìm ảnh",
      "notes": "Ghi chú chi tiết cho người thuyết trình với hướng dẫn cụ thể",
      "speaking_points": ["Điểm nói chính 1 với giải thích đầy đủ", "Điểm nói chính 2 với ví dụ cụ thể", "Điểm nói chính 3 với kết luận rõ ràng"]
    }}
  ]
}}

QUY TẮC QUAN TRỌNG:
- Slide đầu tiên: type = "title" (giới thiệu chủ đề)
- Slide cuối: type = "conclusion" (tóm tắt và kết luận)
- Slides giữa: type = "content" (nội dung chính)
- Mỗi bullet point trong slide_content phải là câu đầy đủ, có ý nghĩa (15-25 từ)
- detailed_content phải là đoạn văn 3-5 câu giải thích sâu nội dung slide
- speaking_points cung cấp gợi ý chi tiết cho người thuyết trình
- Image_keywords mô tả chính xác nội dung để tìm ảnh phù hợp
- Khai thác tối đa thông tin từ văn bản gốc, không bỏ sót chi tiết quan trọng

CHỈ TRẢ VỀ JSON, KHÔNG CÓ GIẢI THÍCH THÊM.
"""
        return prompt
    
    def process_text_to_slides(self, text: str, slide_count: int = 5) -> Optional[Dict]:
        """
        Gửi text đến Gemini và nhận về cấu trúc slide JSON
        """
        try:
            prompt = self.create_advanced_prompt(text, slide_count)
            
            print("🤖 Đang gọi Gemini AI...")
            response = self.model.generate_content(prompt)
            
            # Làm sạch response
            json_text = response.text.strip()
            
            # Xử lý trường hợp Gemini trả về trong code block
            if "```json" in json_text:
                start = json_text.find("```json") + 7
                end = json_text.find("```", start)
                json_text = json_text[start:end].strip()
            elif "```" in json_text:
                start = json_text.find("```") + 3
                end = json_text.rfind("```")
                json_text = json_text[start:end].strip()
            
            print(f"📝 Raw JSON từ Gemini: {json_text[:200]}...")
            
            # Parse JSON
            slides_data = json.loads(json_text)
            
            # Validate cấu trúc JSON
            if not self.validate_slides_structure(slides_data):
                raise ValueError("Cấu trúc JSON không hợp lệ")
            
            print(f"✅ Đã tạo thành công {len(slides_data.get('slides', []))} slides")
            return slides_data
            
        except json.JSONDecodeError as e:
            print(f"❌ Lỗi parse JSON: {e}")
            print(f"Response từ Gemini: {response.text}")
            return None
        except Exception as e:
            print(f"❌ Lỗi khi xử lý với Gemini: {e}")
            return None
    
    def validate_slides_structure(self, data: Dict) -> bool:
        """
        Kiểm tra cấu trúc JSON có đúng format không
        """
        required_fields = ["presentation_title", "slides"]
        
        # Check top level fields
        for field in required_fields:
            if field not in data:
                print(f"❌ Thiếu trường: {field}")
                return False
        
        # Check slides array
        slides = data.get("slides", [])
        if not isinstance(slides, list) or len(slides) == 0:
            print("❌ Slides phải là array và không được rỗng")
            return False
        
        # Check each slide structure
        for i, slide in enumerate(slides):
            # Required fields
            required_slide_fields = ["slide_title", "image_keywords"]
            for field in required_slide_fields:
                if field not in slide:
                    print(f"❌ Slide {i+1} thiếu trường: {field}")
                    return False
            
            # Check có ít nhất một trong các content fields
            content_fields = ["slide_content", "detailed_content", "speaking_points"]
            has_content = any(field in slide and slide[field] for field in content_fields)
            
            if not has_content:
                print(f"❌ Slide {i+1} không có nội dung (slide_content, detailed_content, hoặc speaking_points)")
                return False
        
        return True
    
    def enhance_content_with_context(self, slides_data: Dict, context: str = "") -> Dict:
        """
        Cải thiện nội dung slides dựa trên ngữ cảnh bổ sung
        """
        if not context:
            return slides_data
        
        try:
            enhance_prompt = f"""
Cải thiện nội dung slides sau dựa trên ngữ cảnh bổ sung:

SLIDES HIỆN TẠI:
{json.dumps(slides_data, ensure_ascii=False, indent=2)}

NGỮ CẢNH BỔ SUNG:
{context}

Hãy:
1. Cập nhật image_keywords cho phù hợp hơn
2. Thêm notes chi tiết cho người thuyết trình
3. Cải thiện bullet points cho rõ ràng hơn

Trả về JSON với cấu trúc tương tự nhưng đã được cải thiện.
"""
            
            response = self.model.generate_content(enhance_prompt)
            enhanced_data = json.loads(response.text.replace("```json", "").replace("```", "").strip())
            
            return enhanced_data
        except Exception as e:
            print(f"⚠️ Không thể cải thiện nội dung: {e}")
            return slides_data

# Test function
def test_content_processor():
    """
    Hàm test module
    """
    # Sử dụng API key demo - thay bằng key thật
    api_key = "your_api_key_here"
    
    processor = SlideContentProcessor(api_key)
    
    sample_text = """
    Trí tuệ nhân tạo (AI) đang thay đổi thế giới. Từ xe tự lái đến chẩn đoán y tế, 
    AI giúp con người giải quyết những vấn đề phức tạp. Tuy nhiên, AI cũng đặt ra 
    những thách thức về đạo đức và việc làm. Chúng ta cần chuẩn bị cho tương lai 
    có AI.
    """
    
    result = processor.process_text_to_slides(sample_text, 4)
    if result:
        print("🎉 Test thành công!")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("❌ Test thất bại!")

if __name__ == "__main__":
    test_content_processor()
