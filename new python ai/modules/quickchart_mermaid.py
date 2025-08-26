"""
QuickChart.io & Mermaid.js Integration
Tích hợp API QuickChart.io để tạo charts và Mermaid diagrams
"""

import requests
import urllib.parse
import json
import re
from typing import Dict, List, Optional, Tuple
import tempfile
import os

class QuickChartMermaidGenerator:
    """Class để tạo charts và Mermaid diagrams với QuickChart.io API"""
    
    def __init__(self):
        self.quickchart_base_url = "https://quickchart.io/chart"
        self.mermaid_base_url = "https://quickchart.io/mermaid"
        
    def create_chart_from_data(self, data: Dict, chart_type: str = "bar") -> Optional[str]:
        """Tạo chart từ dữ liệu với QuickChart.io"""
        try:
            # Cấu hình chart config
            chart_config = {
                "type": chart_type,
                "data": data,
                "options": {
                    "responsive": True,
                    "plugins": {
                        "title": {
                            "display": True,
                            "text": data.get("title", "Chart")
                        },
                        "legend": {
                            "display": True
                        }
                    },
                    "scales": {
                        "y": {
                            "beginAtZero": True
                        }
                    } if chart_type in ["bar", "line"] else {}
                }
            }
            
            # Tạo URL với config
            config_json = json.dumps(chart_config)
            encoded_config = urllib.parse.quote(config_json)
            chart_url = f"{self.quickchart_base_url}?c={encoded_config}&format=png&width=600&height=400"
            
            return chart_url
            
        except Exception as e:
            print(f"❌ Lỗi tạo chart: {e}")
            return None
    
    def extract_chart_data_from_text(self, text: str) -> List[Dict]:
        """Trích xuất dữ liệu chart từ văn bản"""
        charts = []
        
        # Pattern 1: Doanh thu theo quý (Q1: 100tr, Q2: 150tr...)
        quarter_pattern = r'(Q[1-4]|quý\s*[1-4]|quarter\s*[1-4]):\s*(\d+(?:[\.,]\d+)?)\s*(tr|triệu|million|tỷ|billion|k|thousand)?'
        quarter_matches = re.findall(quarter_pattern, text, re.IGNORECASE)
        
        if quarter_matches:
            labels = []
            values = []
            for match in quarter_matches:
                quarter = match[0].upper()
                value = float(match[1].replace(',', '.'))
                unit = match[2].lower()
                
                # Normalize units
                if unit in ['tr', 'triệu', 'million']:
                    value *= 1000000
                elif unit in ['tỷ', 'billion']:
                    value *= 1000000000
                elif unit in ['k', 'thousand']:
                    value *= 1000
                
                labels.append(quarter)
                values.append(value)
            
            if labels and values:
                chart_data = {
                    "title": "Doanh thu theo Quý",
                    "labels": labels,
                    "datasets": [{
                        "label": "Doanh thu",
                        "data": values,
                        "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0"]
                    }]
                }
                charts.append({"type": "bar", "data": chart_data})
        
        # Pattern 2: Tỷ lệ phần trăm (iOS 60%, Android 35%...)
        percentage_pattern = r'([a-zA-ZÀ-ỹ\s]+):\s*(\d+(?:[\.,]\d+)?)\s*%'
        percentage_matches = re.findall(percentage_pattern, text, re.IGNORECASE)
        
        if percentage_matches:
            labels = []
            values = []
            for match in percentage_matches:
                label = match[0].strip()
                value = float(match[1].replace(',', '.'))
                labels.append(label)
                values.append(value)
            
            if labels and values:
                chart_data = {
                    "title": "Phân bố Tỷ lệ",
                    "labels": labels,
                    "datasets": [{
                        "label": "Tỷ lệ (%)",
                        "data": values,
                        "backgroundColor": [
                            "#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", 
                            "#9966FF", "#FF9F40", "#FF6384", "#C9CBCF"
                        ]
                    }]
                }
                charts.append({"type": "pie", "data": chart_data})
        
        # Pattern 3: Dữ liệu theo năm (2020: 100, 2021: 120...)
        year_pattern = r'(20\d{2}):\s*(\d+(?:[\.,]\d+)?)\s*(tr|triệu|million|tỷ|billion|k|thousand)?'
        year_matches = re.findall(year_pattern, text, re.IGNORECASE)
        
        if year_matches:
            labels = []
            values = []
            for match in year_matches:
                year = match[0]
                value = float(match[1].replace(',', '.'))
                unit = match[2].lower()
                
                # Normalize units
                if unit in ['tr', 'triệu', 'million']:
                    value *= 1000000
                elif unit in ['tỷ', 'billion']:
                    value *= 1000000000
                elif unit in ['k', 'thousand']:
                    value *= 1000
                
                labels.append(year)
                values.append(value)
            
            if labels and values:
                chart_data = {
                    "title": "Xu hướng theo Năm",
                    "labels": labels,
                    "datasets": [{
                        "label": "Giá trị",
                        "data": values,
                        "borderColor": "#36A2EB",
                        "backgroundColor": "rgba(54, 162, 235, 0.2)",
                        "fill": True
                    }]
                }
                charts.append({"type": "line", "data": chart_data})
        
        return charts
    
    def create_mermaid_diagram(self, diagram_code: str, theme: str = "default") -> Optional[str]:
        """Tạo Mermaid diagram với QuickChart.io"""
        try:
            # Encode Mermaid code
            encoded_code = urllib.parse.quote(diagram_code)
            
            # Tạo URL với theme
            mermaid_url = f"{self.mermaid_base_url}?chart={encoded_code}&theme={theme}&format=png&width=800&height=600"
            
            return mermaid_url
            
        except Exception as e:
            print(f"❌ Lỗi tạo Mermaid diagram: {e}")
            return None
    
    def extract_process_flow_from_text(self, text: str) -> Optional[str]:
        """Trích xuất process flow từ văn bản và tạo Mermaid diagram"""
        try:
            # Tìm các bước trong process
            step_patterns = [
                r'bước\s*(\d+):\s*([^\n\r]+)',
                r'step\s*(\d+):\s*([^\n\r]+)',
                r'giai\s*đoạn\s*(\d+):\s*([^\n\r]+)',
                r'phase\s*(\d+):\s*([^\n\r]+)'
            ]
            
            steps = []
            for pattern in step_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    for match in matches:
                        step_num = int(match[0])
                        step_desc = match[1].strip()
                        steps.append((step_num, step_desc))
                    break
            
            if not steps:
                return None
            
            # Sắp xếp steps theo số thứ tự
            steps.sort(key=lambda x: x[0])
            
            # Tạo Mermaid flowchart code
            mermaid_code = "flowchart TD\n"
            
            for i, (step_num, step_desc) in enumerate(steps):
                node_id = f"step{step_num}"
                # Làm sạch description
                clean_desc = step_desc[:30] + "..." if len(step_desc) > 30 else step_desc
                clean_desc = clean_desc.replace('"', "'")
                
                mermaid_code += f'    {node_id}["{clean_desc}"]\n'
                
                # Thêm arrows giữa các bước
                if i < len(steps) - 1:
                    next_step = f"step{steps[i+1][0]}"
                    mermaid_code += f"    {node_id} --> {next_step}\n"
            
            # Thêm styling
            mermaid_code += """
    classDef stepClass fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000
    classDef firstStep fill:#c8e6c9,stroke:#2e7d32,stroke-width:3px,color:#000
    classDef lastStep fill:#ffcdd2,stroke:#c62828,stroke-width:3px,color:#000
    """
            
            if steps:
                mermaid_code += f"    class step{steps[0][0]} firstStep\n"
                mermaid_code += f"    class step{steps[-1][0]} lastStep\n"
                
                for step_num, _ in steps[1:-1]:
                    mermaid_code += f"    class step{step_num} stepClass\n"
            
            return mermaid_code
            
        except Exception as e:
            print(f"❌ Lỗi extract process flow: {e}")
            return None
    
    def create_organizational_chart(self, text: str) -> Optional[str]:
        """Tạo organizational chart từ văn bản"""
        try:
            # Pattern cho hierarchy
            hierarchy_patterns = [
                r'(ceo|giám\s*đốc|director):\s*([^\n\r]+)',
                r'(phó|deputy|vice):\s*([^\n\r]+)',
                r'(trưởng\s*phòng|manager|head):\s*([^\n\r]+)',
                r'(nhân\s*viên|staff|employee):\s*([^\n\r]+)'
            ]
            
            hierarchy = {}
            for pattern in hierarchy_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    role = match[0].strip()
                    name = match[1].strip()
                    hierarchy[role] = name
            
            if not hierarchy:
                return None
            
            # Tạo Mermaid org chart
            mermaid_code = "flowchart TD\n"
            
            levels = ['ceo', 'phó', 'trưởng phòng', 'nhân viên']
            node_ids = {}
            
            for i, level in enumerate(levels):
                for role, name in hierarchy.items():
                    if level.lower() in role.lower():
                        node_id = f"node{i}{len(node_ids)}"
                        node_ids[role] = node_id
                        clean_name = name[:20] + "..." if len(name) > 20 else name
                        mermaid_code += f'    {node_id}["{role}\\n{clean_name}"]\n'
            
            # Thêm connections
            node_list = list(node_ids.values())
            for i in range(len(node_list) - 1):
                mermaid_code += f"    {node_list[i]} --> {node_list[i+1]}\n"
            
            # Styling
            mermaid_code += """
    classDef ceoClass fill:#ffeb3b,stroke:#f57c00,stroke-width:3px,color:#000
    classDef managerClass fill:#4caf50,stroke:#2e7d32,stroke-width:2px,color:#fff
    classDef staffClass fill:#2196f3,stroke:#1565c0,stroke-width:2px,color:#fff
    """
            
            return mermaid_code
            
        except Exception as e:
            print(f"❌ Lỗi tạo org chart: {e}")
            return None
    
    def analyze_text_for_diagrams(self, text: str) -> List[Dict]:
        """Phân tích văn bản để tạo các loại diagrams phù hợp"""
        diagrams = []
        
        # 1. Process Flow Diagrams
        process_code = self.extract_process_flow_from_text(text)
        if process_code:
            diagrams.append({
                "type": "mermaid_flowchart",
                "title": "Process Flow",
                "code": process_code
            })
        
        # 2. Organizational Charts
        org_code = self.create_organizational_chart(text)
        if org_code:
            diagrams.append({
                "type": "mermaid_org",
                "title": "Organizational Structure", 
                "code": org_code
            })
        
        # 3. Timeline diagrams (nếu có dates)
        timeline_code = self.create_timeline_diagram(text)
        if timeline_code:
            diagrams.append({
                "type": "mermaid_timeline",
                "title": "Timeline",
                "code": timeline_code
            })
        
        return diagrams
    
    def create_timeline_diagram(self, text: str) -> Optional[str]:
        """Tạo timeline diagram từ dates trong text"""
        try:
            # Pattern cho dates và events
            date_patterns = [
                r'(\d{4}):\s*([^\n\r]+)',
                r'tháng\s*(\d{1,2})/(\d{4}):\s*([^\n\r]+)',
                r'(\d{1,2})/(\d{4}):\s*([^\n\r]+)'
            ]
            
            events = []
            for pattern in date_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    for match in matches:
                        if len(match) == 2:  # Year format
                            year = match[0]
                            event = match[1].strip()
                            events.append((year, event))
                        elif len(match) == 3:  # Month/Year format
                            month = match[0]
                            year = match[1]
                            event = match[2].strip()
                            events.append((f"{month}/{year}", event))
                    break
            
            if len(events) < 2:
                return None
            
            # Sắp xếp events theo thời gian
            events.sort(key=lambda x: x[0])
            
            # Tạo Mermaid timeline
            mermaid_code = "timeline\n"
            mermaid_code += "    title Timeline of Events\n"
            
            for date, event in events:
                clean_event = event[:40] + "..." if len(event) > 40 else event
                mermaid_code += f"    {date} : {clean_event}\n"
            
            return mermaid_code
            
        except Exception as e:
            print(f"❌ Lỗi tạo timeline: {e}")
            return None
    
    def download_image(self, url: str, filename: str) -> Optional[str]:
        """Download image từ URL và lưu local"""
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                # Tạo temp file
                temp_dir = tempfile.gettempdir()
                filepath = os.path.join(temp_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                return filepath
            else:
                print(f"❌ HTTP Error {response.status_code} khi download {url}")
                return None
                
        except Exception as e:
            print(f"❌ Lỗi download image: {e}")
            return None
    
    def process_slide_content(self, slide_content: str, slide_title: str = "") -> Dict:
        """Xử lý nội dung slide để tạo charts và diagrams"""
        result = {
            "charts": [],
            "diagrams": [],
            "chart_urls": [],
            "diagram_urls": []
        }
        
        try:
            # 1. Extract và tạo charts
            charts = self.extract_chart_data_from_text(slide_content)
            for chart in charts:
                chart_url = self.create_chart_from_data(chart["data"], chart["type"])
                if chart_url:
                    result["charts"].append(chart)
                    result["chart_urls"].append(chart_url)
            
            # 2. Extract và tạo diagrams
            diagrams = self.analyze_text_for_diagrams(slide_content)
            for diagram in diagrams:
                if diagram["type"].startswith("mermaid"):
                    diagram_url = self.create_mermaid_diagram(diagram["code"])
                    if diagram_url:
                        result["diagrams"].append(diagram)
                        result["diagram_urls"].append(diagram_url)
            
            return result
            
        except Exception as e:
            print(f"❌ Lỗi process slide content: {e}")
            return result
