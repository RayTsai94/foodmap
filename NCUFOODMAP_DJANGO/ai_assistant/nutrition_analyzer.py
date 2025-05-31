"""
AI營養分析器模組
提供食物營養成分分析和營養建議功能
"""

import requests
import json
import re
from django.conf import settings

class NutritionAnalyzer:
    """AI營養分析器類別"""
    
    def __init__(self):
        self.api_key = settings.TOGETHER_API_KEY
        self.api_url = "https://api.together.xyz/v1/chat/completions"
        self.model = "mistralai/Mixtral-8x7B-Instruct-v0.1"
    
    def analyze_food(self, food_description):
        """
        分析食物營養成分
        
        Args:
            food_description (str): 食物描述
            
        Returns:
            dict: 包含營養分析結果的字典
        """
        try:
            # 構建分析提示詞
            prompt = self._build_analysis_prompt(food_description)
            
            # 調用AI API
            response = self._call_ai_api(prompt)
            
            # 解析回應
            nutrition_data = self._parse_nutrition_response(response)
            
            return {
                'success': True,
                'data': nutrition_data,
                'food_description': food_description
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"營養分析失敗：{str(e)}",
                'food_description': food_description
            }
    
    def _build_analysis_prompt(self, food_description):
        """構建營養分析提示詞"""
        return f"""請分析以下食物的營養成分，並以JSON格式回應：

食物：{food_description}

請提供以下營養資訊（每100克）：
- calories（熱量，kcal）
- protein（蛋白質，g）
- carbs（碳水化合物，g）
- fat（脂肪，g）
- fiber（膳食纖維，g）
- sugar（糖分，g）
- sodium（鈉，mg）
- vitamin_c（維生素C，mg）
- calcium（鈣，mg）
- iron（鐵，mg）

回應格式：
{{
    "nutrition": {{
        "calories": 數值,
        "protein": 數值,
        "carbs": 數值,
        "fat": 數值,
        "fiber": 數值,
        "sugar": 數值,
        "sodium": 數值,
        "vitamin_c": 數值,
        "calcium": 數值,
        "iron": 數值
    }},
    "health_rating": "優良/良好/普通/需改善",
    "benefits": ["健康效益1", "健康效益2"],
    "concerns": ["注意事項1", "注意事項2"],
    "recommendations": ["建議1", "建議2"]
}}

請只回應JSON格式，不要包含其他文字。"""
    
    def _call_ai_api(self, prompt):
        """調用Together AI API"""
        if not self.api_key:
            raise Exception("API金鑰未設定")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是專業的營養師，請準確分析食物營養成分並以JSON格式回應。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.3,
            "top_p": 0.9,
            "stream": False
        }
        
        response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"API請求失敗，狀態碼：{response.status_code}")
        
        response_data = response.json()
        
        if 'choices' not in response_data or not response_data['choices']:
            raise Exception("API回應格式錯誤")
        
        return response_data['choices'][0]['message']['content']
    
    def _parse_nutrition_response(self, response):
        """解析AI回應的營養數據"""
        try:
            # 清理回應文字，只保留JSON部分
            cleaned_response = self._clean_json_response(response)
            
            # 解析JSON
            nutrition_data = json.loads(cleaned_response)
            
            # 驗證必要欄位
            required_fields = ['nutrition', 'health_rating']
            for field in required_fields:
                if field not in nutrition_data:
                    raise Exception(f"缺少必要欄位：{field}")
            
            # 設定預設值
            nutrition_data.setdefault('benefits', [])
            nutrition_data.setdefault('concerns', [])
            nutrition_data.setdefault('recommendations', [])
            
            return nutrition_data
            
        except json.JSONDecodeError as e:
            raise Exception(f"JSON解析失敗：{str(e)}")
    
    def _clean_json_response(self, response):
        """清理AI回應，提取JSON部分"""
        # 移除可能的前後說明文字
        response = response.strip()
        
        # 找到JSON的開始和結束位置
        start_idx = response.find('{')
        end_idx = response.rfind('}')
        
        if start_idx == -1 or end_idx == -1:
            raise Exception("回應中未找到有效的JSON格式")
        
        json_str = response[start_idx:end_idx + 1]
        
        # 移除可能的註解
        json_str = re.sub(r'//.*?\n', '', json_str)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        
        return json_str
    
    def get_nutrition_advice(self, user_profile, nutrition_data):
        """
        根據用戶資料和營養數據提供個人化建議
        
        Args:
            user_profile (dict): 用戶資料（年齡、性別、體重、活動量等）
            nutrition_data (dict): 營養分析數據
            
        Returns:
            dict: 個人化營養建議
        """
        try:
            prompt = f"""根據以下用戶資料和食物營養數據，提供個人化營養建議：

用戶資料：
- 年齡：{user_profile.get('age', '未提供')}
- 性別：{user_profile.get('gender', '未提供')}
- 體重：{user_profile.get('weight', '未提供')}kg
- 身高：{user_profile.get('height', '未提供')}cm
- 活動量：{user_profile.get('activity_level', '未提供')}
- 健康目標：{user_profile.get('health_goal', '未提供')}

食物營養數據：
{json.dumps(nutrition_data, ensure_ascii=False, indent=2)}

請提供：
1. 這個食物是否適合該用戶
2. 建議的食用份量
3. 搭配建議
4. 注意事項

請以繁體中文回應，語氣親切專業。"""

            response = self._call_ai_api(prompt)
            
            return {
                'success': True,
                'advice': response
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"建議生成失敗：{str(e)}"
            }

# 便利函數
def analyze_food_nutrition(food_description):
    """便利函數：分析食物營養"""
    analyzer = NutritionAnalyzer()
    return analyzer.analyze_food(food_description)

def get_personalized_advice(user_profile, nutrition_data):
    """便利函數：獲取個人化建議"""
    analyzer = NutritionAnalyzer()
    return analyzer.get_nutrition_advice(user_profile, nutrition_data) 