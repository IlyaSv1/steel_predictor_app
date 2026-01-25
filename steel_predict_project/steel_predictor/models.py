from django.db import models


class Prediction(models.Model):
    STEEL_TYPES = [
        ('carbon', 'Углеродистая сталь'),
        ('stainless', 'Нержавеющая сталь'),
        ('alloy', 'Легированная сталь'),
    ]

    steel_type = models.CharField(max_length=20, choices=STEEL_TYPES)

    # ГОСТ / марка
    gost = models.CharField(max_length=20, null=True, blank=True)
    grade = models.CharField(max_length=50, null=True, blank=True)

    # Химический состав
    C = models.FloatField(default=0)
    Mn = models.FloatField(default=0)
    Si = models.FloatField(default=0)
    P = models.FloatField(default=0)
    S = models.FloatField(default=0)
    Ni = models.FloatField(default=0)
    Cr = models.FloatField(default=0)
    Mo = models.FloatField(default=0)
    Ti = models.FloatField(default=0)

    # Предсказанные свойства
    UTS = models.FloatField()
    YS = models.FloatField()
    Elongation = models.FloatField()
    Hardness = models.FloatField()
    Reduction = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        label = self.get_steel_type_display()
        if self.gost and self.grade:
            label += f" | ГОСТ {self.gost} – {self.grade}"
        return f"{label} ({self.created_at:%Y-%m-%d %H:%M})"
