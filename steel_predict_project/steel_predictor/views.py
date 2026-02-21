import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404
from .utils import predict_properties, validate_composition
from .models import Prediction
from .gost_service import gost_service
from django.views.decorators.http import require_POST
import logging
from logging.handlers import RotatingFileHandler

# Настройка логирования с ротацией
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Ротация: 5 файлов по 2 МБ
handler = RotatingFileHandler(
    'steel_predictor.log', maxBytes=2*1024*1024, backupCount=5, encoding='utf-8'
)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

STEEL_NAMES = {
    'carbon': 'углеродистой стали',
    'stainless': 'нержавеющей стали',
}


def index(request):
    return render(request, 'steel_predictor/index.html')


def predict_view(request, steel_type):
    if steel_type not in STEEL_NAMES:
        logger.warning(
            f"Попытка доступа к неизвестному типу стали: {steel_type}")
        raise Http404("Неизвестный тип стали")

    steel_name = STEEL_NAMES[steel_type]

    gosts = [
        g for g in gost_service.list_gosts()
        if gost_service.get_gost_type(g) == steel_type
    ]
    gost_data = {g: gost_service.get_gost_grades(g) for g in gosts}

    data = {}
    selected_gost = ''
    selected_grade = ''
    errors = {}

    element_rows = [
        ['C', 'Mn', 'Si'],
        ['P', 'S', 'Ni'],
        ['Cr', 'Mo', 'Ti']
    ]

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
        logger.info(f"Восстановление данных предсказания ID={restore_id}")

    if request.method == 'POST':
        data = request.POST
        selected_gost = data.get('gost', '')
        selected_grade = data.get('grade', '')

        if selected_gost and selected_grade:
            ranges = gost_service.get_grade_composition(
                selected_gost,
                selected_grade
            )
            if not ranges:
                errors['grade'] = 'Марка не найдена в выбранном ГОСТе'
                logger.warning(
                    f"Марка {selected_grade} не найдена в ГОСТ {selected_gost}")
            else:
                for el, (min_v, max_v) in ranges.items():
                    val = float(data.get(el, 0) or 0)
                    if not (min_v <= val <= max_v):
                        errors[el] = f'{val} вне диапазона [{min_v}–{max_v}]'
                        logger.warning(
                            f"{el}={val} вне диапазона для {selected_gost}-{selected_grade}")
        else:
            errors = validate_composition(steel_type, data)
            if errors:
                logger.warning(f"Ошибки валидации состава стали: {errors}")

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
                    'element_rows': element_rows,
                }
            )

        # Предсказание свойств
        composition = {el: float(data.get(el) or 0)
                       for row in element_rows for el in row}
        result = predict_properties(steel_type, composition)
        logger.info(
            f"Предсказание для {steel_type} с составом {composition}: {result}")

        # Сохранение в БД
        Prediction.objects.create(
            steel_type=steel_type,
            gost=selected_gost,
            grade=selected_grade,
            **composition,
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
            'element_rows': element_rows,
        }
    )


def history_view(request, steel_type):
    if steel_type not in STEEL_NAMES:
        logger.warning(
            f"Попытка просмотра истории неизвестного типа стали: {steel_type}")
        raise Http404("Неизвестный тип стали")

    predictions = Prediction.objects.filter(
        steel_type=steel_type
    ).order_by('-created_at')

    logger.info(
        f"Просмотр истории предсказаний для {steel_type}, всего записей: {predictions.count()}")

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
    logger.info(f"Удалено предсказание ID={pk} для {steel_type}")
    return redirect('steel_predictor:history', steel_type=steel_type)
