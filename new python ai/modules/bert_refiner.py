# file: modules/bert_refiner.py

import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer
import time

class BertContentRefiner:
    """
    Module tinh chỉnh nội dung slide sử dụng model T5 với hiệu suất cao.
    - Sử dụng batch processing để tăng tốc độ.
    - Phân tích văn bản trước để quyết định hành động tinh chỉnh.
    - Cung cấp các đề xuất cải thiện cụ thể.
    """
    def __init__(self, model_name='t5-small'):
        self.available = False
        self.model = None
        self.tokenizer = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.refinement_stats = {}

        try:
            print(f"🔄 Đang tải model T5 ({model_name}) lên thiết bị {self.device}...")
            start_time = time.time()
            
            # Tải tokenizer và model
            self.tokenizer = T5Tokenizer.from_pretrained(model_name)
            self.model = T5ForConditionalGeneration.from_pretrained(model_name).to(self.device)
            
            self.available = True
            load_time = time.time() - start_time
            print(f"✅ Model T5 đã tải thành công sau {load_time:.2f} giây.")
        except Exception as e:
            print(f"❌ Lỗi khi tải model T5: {e}")
            print("⚠️ Module tinh chỉnh nội dung sẽ không hoạt động.")

    def _analyze_text_quality(self, text: str) -> dict:
        """
        Phân tích chất lượng văn bản bằng các heuristic nhẹ nhàng.
        Trả về một từ điển chứa điểm chất lượng và đề xuất hành động.
        """
        analysis = {'score': 1.0, 'action': 'none', 'reason': ''}
        
        # 1. Phân tích độ dài
        words = text.split()
        if len(words) > 40:
            analysis['score'] -= 0.3
            analysis['action'] = 'summarize'
            analysis['reason'] = 'Văn bản quá dài cho một slide, cần rút gọn.'
            return analysis
            
        # 2. Phân tích sự rõ ràng (ví dụ đơn giản)
        long_words = [w for w in words if len(w) > 12]
        if len(long_words) / len(words + [1e-5]) > 0.15: # Hơn 15% là từ dài
            analysis['score'] -= 0.2
            analysis['action'] = 'clarify'
            analysis['reason'] = 'Sử dụng nhiều từ phức tạp, cần làm rõ ràng hơn.'
            return analysis

        # (Có thể thêm các bước kiểm tra ngữ pháp nhẹ ở đây)

        return analysis

    def refine_content_batch(self, texts: list, actions: list) -> list:
        """
        Tinh chỉnh một loạt văn bản sử dụng T5 model.
        """
        if not self.available or not texts:
            return texts

        # Tạo các tiền tố (prefix) cho từng hành động
        prefixes = {
            'summarize': 'summarize: ',
            'clarify': 'make it clear: ',
            'grammar': 'fix grammar: ',
            'none': ''
        }
        
        # Chuẩn bị input cho model
        inputs = [prefixes[action] + text for text, action in zip(texts, actions) if action != 'none']
        if not inputs:
            return texts
            
        # Tokenize và đưa qua model
        tokenized_inputs = self.tokenizer(inputs, return_tensors="pt", padding=True, truncation=True).to(self.device)
        
        outputs = self.model.generate(
            tokenized_inputs.input_ids, 
            max_length=150, 
            num_beams=4, 
            early_stopping=True
        )
        
        # Giải mã kết quả
        refined_texts = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
        
        # Ánh xạ kết quả trở lại danh sách ban đầu
        final_results = []
        refined_idx = 0
        for i, action in enumerate(actions):
            if action != 'none':
                final_results.append(refined_texts[refined_idx])
                refined_idx += 1
            else:
                final_results.append(texts[i])
        
        return final_results

    def refine_content(self, data: dict) -> dict:
        """
        Hàm chính để tinh chỉnh toàn bộ nội dung của slides_data.
        """
        if not self.available:
            return data

        slides = data.get("slides", [])
        if not slides:
            return data

        # --- Bước 1: Thu thập tất cả văn bản cần xử lý ---
        texts_to_process = []
        actions = []
        original_map = [] # Để ánh xạ kết quả trở lại

        for i, slide in enumerate(slides):
            # Tinh chỉnh nội dung chi tiết
            content = slide.get("content", "")
            if content:
                analysis = self._analyze_text_quality(content)
                texts_to_process.append(content)
                actions.append(analysis['action'])
                original_map.append({'slide_index': i, 'field': 'content', 'analysis': analysis})
            
            # Tinh chỉnh các gạch đầu dòng (bullet points)
            bullets = slide.get("bullet_points", [])
            for j, bullet in enumerate(bullets):
                analysis = self._analyze_text_quality(bullet)
                texts_to_process.append(bullet)
                actions.append(analysis['action'])
                original_map.append({'slide_index': i, 'field': 'bullet_points', 'bullet_index': j, 'analysis': analysis})

        # --- Bước 2: Xử lý hàng loạt (Batch Processing) ---
        print(f"🧠 Bắt đầu tinh chỉnh {len(texts_to_process)} đoạn văn bản bằng T5...")
        start_time = time.time()
        refined_texts = self.refine_content_batch(texts_to_process, actions)
        process_time = time.time() - start_time
        print(f"✅ Hoàn thành tinh chỉnh hàng loạt sau {process_time:.2f} giây.")

        # --- Bước 3: Cập nhật lại dữ liệu và thu thập số liệu thống kê ---
        stats = {
            "total_slides": len(slides), "improved_content": 0, "improved_bullets": 0,
            "total_quality_score": 0, "method_used": f"t5-small ({self.device})"
        }
        
        # Sử dụng set để tránh đếm trùng lặp slide đã cải thiện
        improved_content_slides = set()
        improved_bullets_slides = set()

        for i, original_info in enumerate(original_map):
            original_text = texts_to_process[i]
            refined_text = refined_texts[i]
            slide_idx = original_info['slide_index']
            field = original_info['field']
            analysis = original_info['analysis']
            
            slides[slide_idx]['bert_refined'] = slides[slide_idx].get('bert_refined', False)
            slides[slide_idx]['quality_score'] = slides[slide_idx].get('quality_score', 1.0)
            slides[slide_idx]['bert_suggestions'] = slides[slide_idx].get('bert_suggestions', [])

            # Nếu có sự thay đổi
            if original_text.strip() != refined_text.strip() and analysis['action'] != 'none':
                slides[slide_idx]['bert_refined'] = True
                slides[slide_idx]['bert_suggestions'].append(analysis['reason'])
                
                if field == 'content':
                    slides[slide_idx]['original_content'] = original_text
                    slides[slide_idx]['content'] = refined_text
                    improved_content_slides.add(slide_idx)
                
                elif field == 'bullet_points':
                    bullet_idx = original_info['bullet_index']
                    if 'original_bullet_points' not in slides[slide_idx]:
                        slides[slide_idx]['original_bullet_points'] = list(slides[slide_idx]['bullet_points'])
                    slides[slide_idx]['bullet_points'][bullet_idx] = refined_text
                    improved_bullets_slides.add(slide_idx)
            
            # Cập nhật điểm chất lượng dựa trên phân tích
            slides[slide_idx]['quality_score'] -= (1.0 - analysis['score'])

        # Tổng hợp điểm chất lượng cuối cùng và số liệu
        for slide in slides:
            # Chuẩn hóa điểm không thấp hơn 0.1
            slide['quality_score'] = max(0.1, slide.get('quality_score', 1.0))
            stats['total_quality_score'] += slide['quality_score']

        stats['improved_content'] = len(improved_content_slides)
        stats['improved_bullets'] = len(improved_bullets_slides)
        stats['average_quality'] = stats['total_quality_score'] / len(slides) if slides else 0
        
        data['bert_refinement_stats'] = stats
        return data