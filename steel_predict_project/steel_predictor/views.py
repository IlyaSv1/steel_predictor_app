import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404
from .utils import predict_properties, validate_composition
from .models import Prediction
from .gost_service import gost_service
from django.views.decorators.http import require_POST


STEEL_NAMES = {
    'carbon': 'углеродистой стали',
    'stainless': 'нержавеющей стали',
}


def index(request):
    return render(request, 'steel_predictor/index.html')


# ===== predict_view =====
def predict_view(request, steel_type):
    if steel_type not in STEEL_NAMES:
        raise Http404("Неизвестный тип стали")

    steel_name = STEEL_NAMES[steel_type]

    # ГОСТы нужного типа
    gosts = [
        g for g in gost_service.list_gosts()
        if gost_service.get_gost_type(g) == steel_type
    ]

    gost_data = {g: gost_service.get_gost_grades(g) for g in gosts}

    data = {}
    selected_gost = ''
    selected_grade = ''
    errors = {}

    restore_id = request.GET.get('restore_id')
    if restore_id:
        prediction = get_object_or_404(Prediction, id=restore_id)
        data = {
            'C': prediction.C,
            'Mn': prediction.Mn,
            'Si': prediction.Si,
            'P': prediction.P,
            'S': prediction.S,
            'Ni': prediction.Ni,
            'Cr': prediction.Cr,
            'Mo': prediction.Mo,
            'Ti': prediction.Ti,
        }
        selected_gost = prediction.gost
        selected_grade = prediction.grade

    if request.method == 'POST':
        data = request.POST
        selected_gost = data.get('gost', '')
        selected_grade = data.get('grade', '')

        # Валидация по ГОСТ
        if selected_gost and selected_grade:
            ranges = gost_service.get_grade_composition(
                selected_gost,
                selected_grade
            )

            if not ranges:
                errors['grade'] = 'Марка не найдена в выбранном ГОСТе'
            else:
                for el, (min_v, max_v) in ranges.items():
                    val = float(data.get(el, 0) or 0)
                    if not (min_v <= val <= max_v):
                        errors[el] = f'{val} вне диапазона [{min_v}–{max_v}]'
        else:
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
                    'gosts': gosts,
                    'gost_data': json.dumps(gost_data, ensure_ascii=False),
                    'selected_gost': selected_gost,
                    'selected_grade': selected_grade,
                }
            )

        # ===== Используем словарь, а не numpy =====
        # predict_properties теперь принимает словарь
        result = predict_properties(steel_type, {
            "C": float(data.get('C') or 0),
            "Mn": float(data.get('Mn') or 0),
            "Si": float(data.get('Si') or 0),
            "P": float(data.get('P') or 0),
            "S": float(data.get('S') or 0),
            "Ni": float(data.get('Ni') or 0),
            "Cr": float(data.get('Cr') or 0),
            "Mo": float(data.get('Mo') or 0),
            "Ti": float(data.get('Ti') or 0),
        })

        # Сохранение в БД
        Prediction.objects.create(
            steel_type=steel_type,
            gost=selected_gost,
            grade=selected_grade,
            C=float(data.get('C') or 0),
            Mn=float(data.get('Mn') or 0),
            Si=float(data.get('Si') or 0),
            P=float(data.get('P') or 0),
            S=float(data.get('S') or 0),
            Ni=float(data.get('Ni') or 0),
            Cr=float(data.get('Cr') or 0),
            Mo=float(data.get('Mo') or 0),
            Ti=float(data.get('Ti') or 0),
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

    # GET-запрос
    return render(
        request,
        'steel_predictor/predict.html',
        {
            'steel_name': steel_name,
            'steel_type': steel_type,
            'gosts': gosts,
            'gost_data': json.dumps(gost_data, ensure_ascii=False),
            'data': data,
            'selected_gost': selected_gost,
            'selected_grade': selected_grade,
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


@require_POST
def delete_prediction(request, steel_type, pk):
    prediction = get_object_or_404(
        Prediction,
        id=pk,
        steel_type=steel_type
    )
    prediction.delete()
    return redirect('history', steel_type=steel_type)
