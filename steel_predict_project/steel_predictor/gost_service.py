import json
from pathlib import Path


class GOSTService:
    def __init__(self, data_dir=None):
        # Если путь не указан, берём папку data в приложении
        self.data_dir = Path(data_dir or Path(__file__).parent / "data")
        self.gosts = {}  # словарь всех ГОСТов
        self.load_gosts()

    def load_gosts(self):
        """Загружает все JSON-файлы из папки data"""
        for file in self.data_dir.glob("*.json"):
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                gost_number = data.get("gost")
                if gost_number:
                    self.gosts[gost_number] = data

    def list_gosts(self):
        """Возвращает список ГОСТов"""
        return list(self.gosts.keys())

    def list_grades(self, gost_number):
        """Возвращает список марок для выбранного ГОСТа"""
        gost = self.gosts.get(gost_number)
        if gost:
            return list(gost.get("grades", {}).keys())
        return []

    def get_gost_grades(self, gost_number):
        """Возвращает словарь всех марок с их составом для ГОСТа"""
        gost = self.gosts.get(gost_number)
        if gost:
            return gost.get("grades", {})
        return {}

    def get_grade_composition(self, gost_number, grade):
        """Возвращает диапазоны состава для выбранной марки"""
        gost = self.gosts.get(gost_number)
        if gost:
            return gost.get("grades", {}).get(grade)
        return None

    def get_gost_type(self, gost_number):
        """Возвращает тип стали по ГОСТу (carbon/alloy/stainless)"""
        gost = self.gosts.get(gost_number)
        if gost:
            return gost.get("type")
        return None


# создаём один глобальный экземпляр
gost_service = GOSTService()
