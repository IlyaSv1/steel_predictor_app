from django.shortcuts import render
from django.http import Http404
from .utils import predict_properties, validate_composition
from .models import Prediction


STEEL_NAMES = {
    'carbon': 'углеродистой стали',
    'stainless': 'нержавеющей стали'
}


def index(request):
    return render(request, 'steel_predictor/index.html')


def predict_view(request, steel_type):
    if steel_type not in STEEL_NAMES:
        raise Http404("Неизвестный тип стали")

    steel_name = STEEL_NAMES[steel_type]

    if request.method == 'POST':
        data = request.POST

        # 🔍 ВАЛИДАЦИЯ СОСТАВА
        errors = validate_composition(steel_type, data)

        if errors:
            return render(
                request,
                'steel_predictor/predict.html',
                {
                    'steel_name': steel_name,
                    'steel_type': steel_type,
                    'errors': errors,
                    'data': data,
                }
            )

        # === ML предсказание ===
        result = predict_properties(steel_type, data)

        # === Сохранение в БД ===
        Prediction.objects.create(
            steel_type=steel_type,

            # химический состав
            C=float(data.get('C') or 0),
            Mn=float(data.get('Mn') or 0),
            Si=float(data.get('Si') or 0),
            P=float(data.get('P') or 0),
            S=float(data.get('S') or 0),
            Ni=float(data.get('Ni') or 0),
            Cr=float(data.get('Cr') or 0),
            Mo=float(data.get('Mo') or 0),
            Ti=float(data.get('Ti') or 0),

            # результаты ML (КЛЮЧИ СОВПАДАЮТ С UTILS)
            UTS=result['uts'],
            YS=result['ys'],
            Elongation=result['elong'],
            Hardness=result['hardness'],
        )

        return render(
            request,
            'steel_predictor/result.html',
            {
                'result': result,
                'data': data,
                'steel_name': steel_name,
                'steel_type': steel_type,
            }
        )

    return render(
        request,
        'steel_predictor/predict.html',
        {
            'steel_name': steel_name,
            'steel_type': steel_type,
        }
    )


def history_view(request, steel_type):
    if steel_type not in STEEL_NAMES:
        raise Http404("Неизвестный тип стали")

    predictions = Prediction.objects.filter(
        steel_type=steel_type
    ).order_by('-created_at')

    return render(
        request,
        'steel_predictor/history.html',
        {
            'predictions': predictions,
            'steel_name': STEEL_NAMES[steel_type],
            'steel_type': steel_type,
        }
    )
