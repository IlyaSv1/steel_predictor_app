from django.db import models


class Prediction(models.Model):
    STEEL_TYPES = [
        ('carbon', 'Углеродистая сталь'),
        ('stainless', 'Нержавеющая сталь'),
    ]

    steel_type = models.CharField(max_length=20, choices=STEEL_TYPES)

    # Химический состав
    C = models.FloatField()
    Mn = models.FloatField()
    Si = models.FloatField()
    P = models.FloatField()
    S = models.FloatField()
    Ni = models.FloatField(null=True, blank=True)
    Cr = models.FloatField(null=True, blank=True)
    Mo = models.FloatField(null=True, blank=True)
    Ti = models.FloatField(null=True, blank=True)

    # Предсказанные свойства
    UTS = models.FloatField()
    YS = models.FloatField()
    Elongation = models.FloatField()
    Hardness = models.FloatField()
    Reduction = models.FloatField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_steel_type_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
