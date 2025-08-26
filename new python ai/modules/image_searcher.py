"""
Module 2: Image Search và Download với Pexels API
Nhiệm vụ: Tìm kiếm và tải ảnh phù hợp cho mỗi slide
"""

import requests
import os
from typing import Optional, List, Dict
from urllib.parse import urlparse
import io
from PIL import Image

class ImageSearcher:
    def __init__(self, pexels_api_key: str):
        """
        Khởi tạo với Pexels API key
        """
        self.api_key = pexels_api_key
        self.base_url = "https://api.pexels.com/v1/search"
        self.headers = {
            "Authorization": self.api_key
        }
        self.cache_dir = "image_cache"
        self._create_cache_dir()
    
    def _create_cache_dir(self):
        """
        Tạo thư mục cache cho ảnh
        """
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def search_images(self, query: str, per_page: int = 5) -> Optional[List[Dict]]:
        """
        Tìm kiếm ảnh trên Pexels theo từ khóa
        """
        try:
            params = {
                "query": query,
                "per_page": per_page,
                "orientation": "landscape",  # Phù hợp cho slide
                "size": "medium"
            }
            
            print(f"🔍 Đang tìm ảnh cho: '{query}'...")
            response = requests.get(self.base_url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            photos = data.get("photos", [])
            
            if not photos:
                print(f"⚠️ Không tìm thấy ảnh cho '{query}'")
                return None
            
            print(f"✅ Tìm thấy {len(photos)} ảnh cho '{query}'")
            return photos
            
        except requests.RequestException as e:
            print(f"❌ Lỗi khi tìm ảnh: {e}")
            return None
        except Exception as e:
            print(f"❌ Lỗi không xác định: {e}")
            return None
    
    def download_image(self, image_url: str, filename: str) -> Optional[str]:
        """
        Tải ảnh từ URL và lưu vào cache
        """
        try:
            print(f"⬇️ Đang tải ảnh: {filename}...")
            
            response = requests.get(image_url, stream=True)
            response.raise_for_status()
            
            # Tạo đường dẫn file đầy đủ
            file_path = os.path.join(self.cache_dir, filename)
            
            # Lưu ảnh
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Kiểm tra và resize ảnh nếu cần
            self._optimize_image(file_path)
            
            print(f"✅ Đã tải ảnh: {file_path}")
            return file_path
            
        except Exception as e:
            print(f"❌ Lỗi khi tải ảnh {filename}: {e}")
            return None
    
    def _optimize_image(self, file_path: str, max_width: int = 1024, max_height: int = 768):
        """
        Tối ưu ảnh cho slide (resize và compress)
        """
        try:
            with Image.open(file_path) as img:
                # Chuyển về RGB nếu cần
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize nếu ảnh quá lớn
                width, height = img.size
                if width > max_width or height > max_height:
                    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                    img.save(file_path, 'JPEG', quality=85, optimize=True)
                    print(f"🔧 Đã tối ưu ảnh: {file_path}")
                
        except Exception as e:
            print(f"⚠️ Không thể tối ưu ảnh {file_path}: {e}")
    
    def get_best_image_for_slide(self, keywords: str, slide_number: int) -> Optional[str]:
        """
        Lấy ảnh tốt nhất cho slide dựa trên keywords
        """
        # Tìm ảnh
        photos = self.search_images(keywords, per_page=3)
        
        if not photos:
            # Fallback keywords
            fallback_keywords = ["presentation", "business", "technology", "abstract"]
            for fallback in fallback_keywords:
                photos = self.search_images(fallback, per_page=3)
                if photos:
                    print(f"🔄 Dùng ảnh fallback với từ khóa: {fallback}")
                    break
        
        if not photos:
            return None
        
        # Chọn ảnh tốt nhất (ảnh đầu tiên)
        best_photo = photos[0]
        image_url = best_photo['src']['medium']
        
        # Tạo tên file
        filename = f"slide_{slide_number}_{keywords.replace(' ', '_')[:20]}.jpg"
        
        # Tải ảnh
        return self.download_image(image_url, filename)
    
    def get_images_for_all_slides(self, slides_data: Dict) -> Dict:
        """
        Tải ảnh cho tất cả slides trong presentation
        """
        slides = slides_data.get("slides", [])
        image_paths = {}
        
        print(f"🖼️ Bắt đầu tải ảnh cho {len(slides)} slides...")
        
        for i, slide in enumerate(slides):
            slide_number = slide.get("slide_number", i + 1)
            keywords = slide.get("image_keywords", "presentation")
            
            image_path = self.get_best_image_for_slide(keywords, slide_number)
            
            if image_path:
                image_paths[slide_number] = image_path
            else:
                print(f"⚠️ Không thể tải ảnh cho slide {slide_number}")
        
        print(f"✅ Đã tải thành công {len(image_paths)} ảnh")
        return image_paths
    
    def cleanup_cache(self):
        """
        Dọn dẹp thư mục cache
        """
        try:
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                os.remove(file_path)
            print("🧹 Đã dọn dẹp cache ảnh")
        except Exception as e:
            print(f"⚠️ Lỗi khi dọn dẹp cache: {e}")

class FallbackImageProvider:
    """
    Provider ảnh dự phòng khi không có Pexels API
    """
    
    @staticmethod
    def create_placeholder_image(text: str, size: tuple = (1024, 768)) -> str:
        """
        Tạo ảnh placeholder với text
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Tạo ảnh nền
            img = Image.new('RGB', size, color='#f0f0f0')
            draw = ImageDraw.Draw(img)
            
            # Thử load font, fallback về font mặc định
            try:
                font = ImageFont.truetype("arial.ttf", 48)
            except:
                font = ImageFont.load_default()
            
            # Vẽ text vào giữa
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (size[0] - text_width) // 2
            y = (size[1] - text_height) // 2
            
            draw.text((x, y), text, fill='#333333', font=font)
            
            # Lưu ảnh
            filename = f"placeholder_{text.replace(' ', '_')[:15]}.png"
            file_path = os.path.join("image_cache", filename)
            
            # Tạo thư mục nếu chưa có
            os.makedirs("image_cache", exist_ok=True)
            
            img.save(file_path)
            return file_path
            
        except Exception as e:
            print(f"❌ Không thể tạo placeholder image: {e}")
            return None

# Test function
def test_image_searcher():
    """
    Hàm test module
    """
    # Sử dụng API key demo - thay bằng key thật
    api_key = "your_pexels_api_key_here"
    
    searcher = ImageSearcher(api_key)
    
    # Test search
    photos = searcher.search_images("artificial intelligence", 2)
    if photos:
        print("🎉 Search test thành công!")
        
        # Test download
        image_url = photos[0]['src']['medium']
        file_path = searcher.download_image(image_url, "test_image.jpg")
        
        if file_path:
            print("🎉 Download test thành công!")
        else:
            print("❌ Download test thất bại!")
    else:
        print("❌ Search test thất bại!")
    
    # Test fallback
    fallback = FallbackImageProvider()
    placeholder = fallback.create_placeholder_image("AI Technology")
    if placeholder:
        print("🎉 Placeholder test thành công!")

if __name__ == "__main__":
    test_image_searcher()
