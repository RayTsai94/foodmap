from django.core.management.base import BaseCommand
from django.db import transaction
from restaurants.models import Restaurant, MenuItem
from food_analysis.models import NutritionInfo, Ingredient, MenuItemIngredient, FoodPreference, MenuItemPreference
import random

class Command(BaseCommand):
    help = '填充食物分析示例數據'

    def handle(self, *args, **options):
        self.stdout.write('開始填充食物分析數據...')
        
        with transaction.atomic():
            # 創建食材
            self.create_ingredients()
            
            # 創建飲食偏好
            self.create_food_preferences()
            
            # 為現有菜單項添加營養信息
            self.add_nutrition_info()
            
            # 添加食材關聯
            self.add_ingredient_relations()
            
            # 添加偏好關聯
            self.add_preference_relations()
        
        self.stdout.write(self.style.SUCCESS('成功填充食物分析數據！'))

    def create_ingredients(self):
        """創建常見食材"""
        ingredients_data = [
            ('雞肉', '優質蛋白質來源，低脂肪'),
            ('豬肉', '含豐富蛋白質和維生素B群'),
            ('牛肉', '高蛋白質，富含鐵質'),
            ('魚肉', '富含Omega-3脂肪酸'),
            ('蝦', '低熱量高蛋白海鮮'),
            ('蛋', '完整蛋白質，含多種維生素'),
            ('豆腐', '植物性蛋白質，適合素食者'),
            ('米飯', '主要碳水化合物來源'),
            ('麵條', '小麥製品，提供能量'),
            ('番茄', '富含茄紅素和維生素C'),
            ('洋蔥', '含抗氧化物質'),
            ('高麗菜', '富含維生素K和纖維'),
            ('紅蘿蔔', '富含β-胡蘿蔔素'),
            ('青椒', '維生素C含量豐富'),
            ('菠菜', '富含鐵質和葉酸'),
            ('生菜', '低熱量，含膳食纖維'),
            ('起司', '鈣質和蛋白質來源'),
            ('牛奶', '優質蛋白質和鈣質'),
            ('奶油', '脂肪含量高，增加風味'),
            ('橄欖油', '健康脂肪，含維生素E'),
        ]
        
        for name, description in ingredients_data:
            ingredient, created = Ingredient.objects.get_or_create(
                name=name,
                defaults={'description': description}
            )
            if created:
                self.stdout.write(f'創建食材: {name}')

    def create_food_preferences(self):
        """創建飲食偏好和過敏原"""
        preferences_data = [
            # 飲食習慣
            ('素食', 'DIET', '不含肉類、魚類和海鮮的飲食'),
            ('全素', 'DIET', '不含任何動物製品的飲食'),
            ('無麩質', 'DIET', '不含麩質的飲食，適合乳糜瀉患者'),
            ('低碳水化合物', 'DIET', '限制碳水化合物攝入的飲食'),
            ('高蛋白', 'DIET', '強調蛋白質攝入的飲食'),
            ('地中海飲食', 'DIET', '以橄欖油、魚類、蔬果為主的飲食'),
            
            # 過敏原
            ('麩質', 'ALLERGY', '小麥、大麥、黑麥中的蛋白質'),
            ('乳製品', 'ALLERGY', '牛奶及其製品'),
            ('堅果', 'ALLERGY', '樹堅果和花生'),
            ('海鮮', 'ALLERGY', '魚類、貝類、甲殼類'),
            ('蛋類', 'ALLERGY', '雞蛋及含蛋製品'),
            ('大豆', 'ALLERGY', '大豆及其製品'),
        ]
        
        for name, pref_type, description in preferences_data:
            preference, created = FoodPreference.objects.get_or_create(
                name=name,
                type=pref_type,
                defaults={'description': description}
            )
            if created:
                self.stdout.write(f'創建偏好: {name} ({pref_type})')

    def add_nutrition_info(self):
        """為菜單項添加營養信息"""
        menu_items = MenuItem.objects.filter(nutrition__isnull=True)[:20]
        
        for item in menu_items:
            # 根據菜單項名稱估算營養值
            calories = random.randint(200, 800)
            protein = random.randint(10, 40)
            carbs = random.randint(20, 80)
            fat = random.randint(5, 30)
            fiber = random.randint(2, 15)
            sugar = random.randint(1, 20)
            sodium = random.randint(300, 1500)
            
            # 根據菜名調整營養值
            if '沙拉' in item.name or '蔬菜' in item.name:
                calories = random.randint(100, 300)
                fat = random.randint(2, 10)
                fiber = random.randint(5, 15)
            elif '炸' in item.name or '酥' in item.name:
                calories = random.randint(400, 900)
                fat = random.randint(15, 40)
            elif '湯' in item.name:
                calories = random.randint(80, 250)
                sodium = random.randint(600, 1200)
            
            nutrition = NutritionInfo.objects.create(
                menu_item=item,
                calories=calories,
                protein=protein,
                carbs=carbs,
                fat=fat,
                fiber=fiber,
                sugar=sugar,
                sodium=sodium
            )
            self.stdout.write(f'添加營養信息: {item.name}')

    def add_ingredient_relations(self):
        """添加菜單項與食材的關聯"""
        menu_items = MenuItem.objects.all()[:15]
        ingredients = list(Ingredient.objects.all())
        
        for item in menu_items:
            # 隨機選擇3-6個食材
            selected_ingredients = random.sample(ingredients, random.randint(3, 6))
            
            for ingredient in selected_ingredients:
                MenuItemIngredient.objects.get_or_create(
                    menu_item=item,
                    ingredient=ingredient,
                    defaults={'amount': f'{random.randint(50, 200)}克'}
                )

    def add_preference_relations(self):
        """添加菜單項與偏好的關聯"""
        menu_items = MenuItem.objects.all()[:15]
        preferences = list(FoodPreference.objects.all())
        
        for item in menu_items:
            # 隨機選擇一些偏好進行關聯
            selected_prefs = random.sample(preferences, random.randint(2, 5))
            
            for pref in selected_prefs:
                # 隨機決定是否兼容
                is_compatible = random.choice([True, False])
                
                # 根據偏好類型調整兼容性邏輯
                if pref.type == 'ALLERGY':
                    # 過敏原通常是不兼容的（即菜單項不含該過敏原）
                    is_compatible = random.choice([True, False])
                elif pref.type == 'DIET':
                    # 飲食偏好通常是兼容的
                    is_compatible = random.choice([True, True, False])
                
                MenuItemPreference.objects.get_or_create(
                    menu_item=item,
                    preference=pref,
                    defaults={'is_compatible': is_compatible}
                ) 