import random
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class WordFlashItem:
    item_id: str
    target: str
    options: list[str]
    prompt: Optional[str] = None
    correct: Optional[str] = None

# ---- Темы ----
# В каждой теме: слова по difficulty
THEMES = {
    1: {
        "name": "Школа",
        "easy": [
            "школа","класс","урок","парта","звонок","мел","доска","стол",
            "книга","ручка","пенал","портфель","окно","коридор","здание",
            "форма","стул","листок","сменка","рюкзак"
        ],
        "normal": [
            "тетрадь","учебник","учитель","задание","перемена",
            "карандаш","линейка","дневник","расписание","кабинет",
            "одноклассник","директор","оценка","экзамен","предмет",
            "библиотека","глобус","карта","плакат","лаборатория"
        ],
        "hard": [
            "объяснение","самостоятельность","подготовка","контрольная",
            "исследование","дисциплина","внимательность","успеваемость",
            "образование","конспектирование","аттестация","концентрация",
            "познавательный","аналитический","проектирование",
            "экспериментальный","организация","академический",
            "интеллектуальный","саморазвитие"
        ],
    },

    2: {
        "name": "Животные",
        "easy": [
            "кот","пёс","ёж","заяц","лиса","волк","слон","тигр",
            "утка","жук","рыба","лось","кит","крот","гусь",
            "краб","аист","сом","лев","бык"
        ],
        "normal": [
            "собака","кошка","кролик","лошадь","медведь",
            "воробей","лягушка","черепаха","попугай",
            "дельфин","белка","барсук","антилопа","кенгуру",
            "ястреб","павлин","кальмар","пингвин","енот","осьминог"
        ],
        "hard": [
            "млекопитающее","земноводное","пресмыкающееся","хищник",
            "травоядное","обитание","выживание","миграция",
            "экосистема","размножение","инстинкт","популяция",
            "территориальный","паразитический","симбиоз",
            "адаптация","биоразнообразие","плотоядный",
            "естественный","средаобитания"
        ],
    },

    3: {
        "name": "Природа",
        "easy": [
            "лес","сад","река","поле","снег","дождь","ветер",
            "солнце","трава","гора","луг","камень","песок","ручей",
            "глина","лед","куст","пень","берег","скала"
        ],
        "normal": [
            "радуга","озеро","берёза","ромашка","тропинка",
            "туман","мороз","облако","водопад","рассвет",
            "закат","гроза","поляна","ущелье","долина",
            "равнина","болото","остров","пещера","источник"
        ],
        "hard": [
            "извержение","наводнение","землетрясение",
            "растительность","окружение","климатический",
            "атмосферный","природоведение","вулканический",
            "осадочный","географический","экологический",
            "формирование","преобразование","ландшафтный",
            "цикличность","испарение","конденсация","эрозия","биосфера"
        ],
    },

    4: {
        "name": "Еда",
        "easy": [
            "сок","сыр","хлеб","мёд","чай","суп","рис",
            "лук","соль","груша","пирог","кефир","арбуз","слива",
            "борщ","батон","булка","кекс","дыня","сырник"
        ],
        "normal": [
            "молоко","печенье","компот","котлета","морковка",
            "картофель","карамель","йогурт","омлет","варенье",
            "салат","макароны","сметана","пельмени","колбаса",
            "шоколад","конфета","бутерброд","запеканка","блинчики"
        ],
        "hard": [
            "питательный","калорийность","ингредиенты","приготовление",
            "сервировка","ароматный","кулинарный","маринование",
            "запекание","ферментация","пастеризация","консервирование",
            "дегустация","гастрономический","рецептура","пряность",
            "вегетарианский","диетический","сбалансированный","изысканный"
        ],
    },

    5: {
        "name": "Транспорт",
        "easy": [
            "поезд","метро","такси","лодка","шина","руль",
            "мост","путь","рейс","трос","парус","гараж",
            "катер","кран","вагон","фара","шлюз","тоннель","трактор","платформа"
        ],
        "normal": [
            "автобус","трамвай","самолёт","вертолёт","машина",
            "велосипед","станция","перрон","платформа","шоссе",
            "двигатель","маршрут","экипаж","прицеп","кабина",
            "рейсовый","пассажир","багажник","тормоз","колонна"
        ],
        "hard": [
            "навигация","маршрутизация","перекрёсток","транспортировка",
            "скоростной","регулирование","безопасность","инфраструктура",
            "магистральный","автоматизированный","маневрирование",
            "логистика","эксплуатация","координация","диспетчеризация",
            "аэродинамический","грузоперевозка","сертификация",
            "проектирование","оптимизация"
        ],
    },

    6: {
        "name": "Космос",
        "easy": [
            "луна","марс","звезда","небо","луч","пуск",
            "спутник","комета","орбита","метеор",
            "космос","шлем","шар","сигнал","станция",
            "план","взлёт","скафандр","флаг","пыль"
        ],
        "normal": [
            "планета","ракета","галактика","астероид",
            "космонавт","телескоп","созвездие","модуль",
            "платформа","траектория","обсерватория","движение",
            "поверхность","излучение","капсула","экспедиция",
            "корабль","центр","аппарат","вселенная"
        ],
        "hard": [
            "гравитация","невесомость","притяжение","сверхновая",
            "космология","астрофизика","космический","межпланетный",
            "исследовательский","бесконечность","радиационный",
            "орбитальный","межзвёздный","спектроскопия",
            "экзопланета","колонизация","галактический",
            "наблюдательный","расширение","сингулярность"
        ],
    },

    7: {
        "name": "Спорт",
        "easy": [
            "мяч","гол","бег","лыжи","старт","финиш",
            "матч","судья","форма","клюшка","щит",
            "тур","сетка","шайба","канат","зал","клуб","трек","круг","прыжок"
        ],
        "normal": [
            "футбол","теннис","хоккей","плавание","команда",
            "турнир","тренер","стадион","чемпион","разминка",
            "эстафета","гимнастика","борьба","атлетика",
            "секунда","тайм","награждение","болельщик","сборная","подача"
        ],
        "hard": [
            "соревнование","выносливость","тренировка",
            "результативность","профессиональный","олимпийский",
            "квалификация","регламент","дисциплина","рекордсмен",
            "подготовительный","интенсивность","тактический",
            "стратегический","спортивный",
            "координация","мобилизация","мотивация","концентрация"
        ],
    },

    8: {
        "name": "Профессии",
        "easy": [
            "врач","повар","шахтёр","пилот","шофёр","дворник",
            "маляр","судья","швея","няня","фермер","кассир",
            "почтальон","рыбак","актёр","пекарь","сторож","слесарь","крановщик","столяр"
        ],
        "normal": [
            "инженер","архитектор","программист","строитель",
            "журналист","дизайнер","менеджер","бухгалтер",
            "переводчик","редактор","воспитатель","фармацевт",
            "электрик","монтажник","следователь","юрист",
            "психолог","ветеринар","аналитик","консультант"
        ],
        "hard": [
            "специализация","квалификация","профессионализм",
            "компетенция","ответственность","сертификация",
            "стажировка","трудоустройство","руководитель",
            "предпринимательство","координация","организационный",
            "должностной","администрирование","производственный",
            "карьерный","перспектива","аттестационный",
            "контрактный","регламентированный"
        ],
    },

    9: {
        "name": "Дом",
        "easy": [
            "дом","крыша","стена","пол","дверь","лампа","ковёр",
            "диван","шкаф","кухня","ванна","чашка",
            "ложка","вилка","кран","печь","замок","окно","рама","подвал","чердак"
        ],
        "normal": [
            "квартира","балкон","прихожая","гостиная",
            "спальня","кладовка","лестница","подъезд","комната","корзина","холодильник",
            "микроволновка","пылесос","телевизор","комод",
            "подушка","одеяло","занавеска","розетка"
        ],
        "hard": [
            "интерьер","планировка","благоустройство",
            "коммунальный","электроснабжение","водопровод",
            "вентиляция","конструкция","отопительный",
            "капитальный","изоляция","реконструкция",
            "архитектурный","фасадный","инженерный",
            "эксплуатационный","проектировочный",
            "строительный","ремонтный","обустройство"
        ],
    },

    10: {
        "name": "Тёма",
        "easy": [
            "скебоб","крипер","амонгус","Стив","Алекс","липтон","наггетсы","картошка фри","майнкрафт"
        ],
    },
}

DEFAULT_THEME_ID = 1

VOCAB_CATEGORIES = {
101: {
    "name": "1 класс — словарные слова",
    "easy": [
        {"word": "молоко", "missing_index": 1, "options": ["о", "а"]},
        {"word": "корова", "missing_index": 1, "options": ["о", "а"]},
        {"word": "собака", "missing_index": 1, "options": ["о", "а"]},
        {"word": "ворона", "missing_index": 1, "options": ["о", "а"]},
        {"word": "пенал", "missing_index": 1, "options": ["е", "и"]},
        {"word": "ребята", "missing_index": 1, "options": ["е", "и"]},
        {"word": "берёза", "missing_index": 3, "options": ["ё", "е"]},
        {"word": "тетрадь", "missing_index": 1, "options": ["е", "и"]},
    ],
    "normal": [
        {"word": "лопата", "missing_index": 1, "options": ["о", "а"]},
        {"word": "посуда", "missing_index": 1, "options": ["о", "а"]},
        {"word": "воробей", "missing_index": 1, "options": ["о", "а"]},
        {"word": "девочка", "missing_index": 1, "options": ["е", "и"]},
        {"word": "машина", "missing_index": 1, "options": ["а", "о"]},
        {"word": "пальто", "missing_index": 1, "options": ["а", "о"]},
        {"word": "карман", "missing_index": 1, "options": ["а", "о"]},
        {"word": "народ", "missing_index": 1, "options": ["а", "о"]},
    ],
    "hard": [
        {"word": "ученик", "missing_index": 2, "options": ["е", "и"]},
        {"word": "учитель", "missing_index": 2, "options": ["и", "е"]},
        {"word": "дежурный", "missing_index": 3, "options": ["у", "ю"]},
        {"word": "комната", "missing_index": 1, "options": ["о", "а"]},
        {"word": "картина", "missing_index": 1, "options": ["а", "о"]},
        {"word": "лестница", "missing_index": 1, "options": ["е", "и"]},
        {"word": "карандаш", "missing_index": 1, "options": ["а", "о"]},
        {"word": "директор", "missing_index": 1, "options": ["и", "е"]},
    ],
},

102: {
    "name": "2 класс — словарные слова",
    "easy": [
        {"word": "капуста", "missing_index": 1, "options": ["а", "о"]},
        {"word": "коньки", "missing_index": 1, "options": ["о", "а"]},
        {"word": "магазин", "missing_index": 1, "options": ["а", "о"]},
        {"word": "малина", "missing_index": 1, "options": ["а", "о"]},
        {"word": "мебель", "missing_index": 1, "options": ["е", "и"]},
        {"word": "медведь", "missing_index": 1, "options": ["е", "и"]},
        {"word": "месяц", "missing_index": 1, "options": ["е", "и"]},
        {"word": "погода", "missing_index": 1, "options": ["о", "а"]},
    ],
    "normal": [
        {"word": "помидор", "missing_index": 1, "options": ["о", "а"]},
        {"word": "работа", "missing_index": 1, "options": ["а", "о"]},
        {"word": "рисунок", "missing_index": 1, "options": ["и", "е"]},
        {"word": "родина", "missing_index": 1, "options": ["о", "а"]},
        {"word": "сапоги", "missing_index": 1, "options": ["а", "о"]},
        {"word": "сорока", "missing_index": 1, "options": ["о", "а"]},
        {"word": "тарелка", "missing_index": 1, "options": ["а", "о"]},
        {"word": "товарищ", "missing_index": 1, "options": ["о", "а"]},
    ],
    "hard": [
        {"word": "хорошо", "missing_index": 1, "options": ["о", "а"]},
        {"word": "ягода", "missing_index": 2, "options": ["о", "а"]},
        {"word": "завод", "missing_index": 1, "options": ["а", "о"]},
        {"word": "морковь", "missing_index": 1, "options": ["о", "а"]},
        {"word": "календарь", "missing_index": 1, "options": ["а", "о"]},
        {"word": "ботинки", "missing_index": 1, "options": ["о", "а"]},
        {"word": "каникулы", "missing_index": 1, "options": ["а", "о"]},
        {"word": "квартира", "missing_index": 2, "options": ["а", "о"]},
    ],
},

103: {
    "name": "3 класс — словарные слова",
    "easy": [
        {"word": "беседа", "missing_index": 1, "options": ["е", "и"]},
        {"word": "библиотека", "missing_index": 1, "options": ["и", "е"]},
        {"word": "болото", "missing_index": 1, "options": ["о", "а"]},
        {"word": "газета", "missing_index": 1, "options": ["а", "о"]},
        {"word": "герой", "missing_index": 1, "options": ["е", "и"]},
        {"word": "горизонт", "missing_index": 1, "options": ["о", "а"]},
        {"word": "железо", "missing_index": 1, "options": ["е", "и"]},
        {"word": "километр", "missing_index": 1, "options": ["и", "е"]},
    ],
    "normal": [
        {"word": "коллекция", "missing_index": 1, "options": ["о", "а"]},
        {"word": "командир", "missing_index": 1, "options": ["о", "а"]},
        {"word": "космонавт", "missing_index": 1, "options": ["о", "а"]},
        {"word": "математика", "missing_index": 1, "options": ["а", "о"]},
        {"word": "победа", "missing_index": 1, "options": ["о", "а"]},
        {"word": "секунда", "missing_index": 1, "options": ["е", "и"]},
        {"word": "солдат", "missing_index": 1, "options": ["о", "а"]},
        {"word": "телефон", "missing_index": 1, "options": ["е", "и"]},
    ],
    "hard": [
        {"word": "тепловоз", "missing_index": 1, "options": ["е", "и"]},
        {"word": "трактор", "missing_index": 2, "options": ["а", "о"]},
        {"word": "столица", "missing_index": 2, "options": ["о", "а"]},
        {"word": "путешествие", "missing_index": 1, "options": ["у", "ю"]},
        {"word": "инженер", "missing_index": 0, "options": ["и", "е"]},
        {"word": "интерес", "missing_index": 0, "options": ["и", "е"]},
        {"word": "расстояние", "missing_index": 1, "options": ["а", "о"]},
        {"word": "велосипед", "missing_index": 3, "options": ["о", "а"]},
    ],
},

104: {
    "name": "4 класс — словарные слова",
    "easy": [
        {"word": "агроном", "missing_index": 0, "options": ["а", "о"]},
        {"word": "адрес", "missing_index": 0, "options": ["а", "о"]},
        {"word": "аккуратно", "missing_index": 3, "options": ["у", "о"]},
        {"word": "аппетит", "missing_index": 3, "options": ["е", "и"]},
        {"word": "корабль", "missing_index": 1, "options": ["о", "а"]},
        {"word": "костюм", "missing_index": 1, "options": ["о", "а"]},
        {"word": "пассажир", "missing_index": 1, "options": ["а", "о"]},
        {"word": "портрет", "missing_index": 1, "options": ["о", "а"]},
    ],
    "normal": [
        {"word": "салют", "missing_index": 1, "options": ["а", "о"]},
        {"word": "хоккей", "missing_index": 1, "options": ["о", "а"]},
        {"word": "биография", "missing_index": 1, "options": ["и", "е"]},
        {"word": "диалог", "missing_index": 1, "options": ["и", "е"]},
        {"word": "интонация", "missing_index": 0, "options": ["и", "е"]},
        {"word": "каллиграфия", "missing_index": 1, "options": ["а", "о"]},
        {"word": "литература", "missing_index": 1, "options": ["и", "е"]},
        {"word": "территория", "missing_index": 1, "options": ["е", "и"]},
    ],
    "hard": [
        {"word": "дисциплина", "missing_index": 1, "options": ["и", "е"]},
        {"word": "искусство", "missing_index": 3, "options": ["у", "ю"]},
        {"word": "количество", "missing_index": 1, "options": ["о", "а"]},
        {"word": "микроскоп", "missing_index": 1, "options": ["и", "е"]},
        {"word": "температура", "missing_index": 1, "options": ["е", "и"]},
        {"word": "экскаватор", "missing_index": 4, "options": ["а", "о"]},
        {"word": "эксперимент", "missing_index": 4, "options": ["е", "и"]},
        {"word": "путешественник", "missing_index": 1, "options": ["у", "ю"]},
    ],
    },

    201: {
        "name": "ЖИ-ШИ",
        "easy": [
            {"word": "ежи", "missing_index": 2, "options": ["и", "ы"]},
            {"word": "ужи", "missing_index": 2, "options": ["и", "ы"]},
            {"word": "ножи", "missing_index": 3, "options": ["и", "ы"]},
            {"word": "лыжи", "missing_index": 3, "options": ["и", "ы"]},
            {"word": "шило", "missing_index": 1, "options": ["и", "ы"]},
            {"word": "шина", "missing_index": 1, "options": ["и", "ы"]},
            {"word": "машина", "missing_index": 3, "options": ["и", "ы"]},
            {"word": "шишка", "missing_index": 1, "options": ["и", "ы"]},
            {"word": "пиши", "missing_index": 3, "options": ["и", "ы"]},
            {"word": "живи", "missing_index": 1, "options": ["и", "ы"]},
        ],
        "normal": [
            {"word": "жираф", "missing_index": 1, "options": ["и", "ы"]},
            {"word": "жизнь", "missing_index": 1, "options": ["и", "ы"]},
            {"word": "пружина", "missing_index": 5, "options": ["и", "ы"]},
            {"word": "тишина", "missing_index": 1, "options": ["и", "ы"]},
            {"word": "лужи", "missing_index": 3, "options": ["и", "ы"]},
            {"word": "решить", "missing_index": 3, "options": ["и", "ы"]},
            {"word": "живой", "missing_index": 1, "options": ["и", "ы"]},
            {"word": "шипы", "missing_index": 1, "options": ["и", "ы"]},
            {"word": "ошибка", "missing_index": 1, "options": ["и", "ы"]},
            {"word": "чижик", "missing_index": 2, "options": ["и", "ы"]},
        ],
        "hard": [
            {"word": "живопись", "missing_index": 1, "options": ["и", "ы"]},
            {"word": "ширина", "missing_index": 1, "options": ["и", "ы"]},
            {"word": "служить", "missing_index": 4, "options": ["и", "ы"]},
            {"word": "пружинка", "missing_index": 5, "options": ["и", "ы"]},
            {"word": "животное", "missing_index": 1, "options": ["и", "ы"]},
            {"word": "решительный", "missing_index": 3, "options": ["и", "ы"]},
            {"word": "поспешить", "missing_index": 6, "options": ["и", "ы"]},
            {"word": "зашипеть", "missing_index": 3, "options": ["и", "ы"]},
            {"word": "дружить", "missing_index": 4, "options": ["и", "ы"]},
            {"word": "напиши", "missing_index": 5, "options": ["и", "ы"]},
        ],
    },

    202: {
        "name": "ЧА-ЩА",
        "easy": [
            {"word": "чашка", "missing_index": 1, "options": ["а", "я"]},
            {"word": "чаща", "missing_index": 1, "options": ["а", "я"]},
            {"word": "чайка", "missing_index": 1, "options": ["а", "я"]},
            {"word": "роща", "missing_index": 3, "options": ["а", "я"]},
            {"word": "свеча", "missing_index": 4, "options": ["а", "я"]},
            {"word": "туча", "missing_index": 3, "options": ["а", "я"]},
            {"word": "дача", "missing_index": 3, "options": ["а", "я"]},
            {"word": "качать", "missing_index": 2, "options": ["а", "я"]},
            {"word": "чай", "missing_index": 1, "options": ["а", "я"]},
            {"word": "пища", "missing_index": 3, "options": ["а", "я"]},
        ],
        "normal": [
            {"word": "начало", "missing_index": 1, "options": ["а", "я"]},
            {"word": "печать", "missing_index": 3, "options": ["а", "я"]},
            {"word": "прощай", "missing_index": 4, "options": ["а", "я"]},
            {"word": "обещание", "missing_index": 4, "options": ["а", "я"]},
            {"word": "площадка", "missing_index": 4, "options": ["а", "я"]},
            {"word": "часто", "missing_index": 1, "options": ["а", "я"]},
            {"word": "участок", "missing_index": 1, "options": ["а", "я"]},
            {"word": "чайник", "missing_index": 1, "options": ["а", "я"]},
            {"word": "частица", "missing_index": 1, "options": ["а", "я"]},
            {"word": "обращаться", "missing_index": 4, "options": ["а", "я"]},
        ],
        "hard": [
            {"word": "прощание", "missing_index": 4, "options": ["а", "я"]},
            {"word": "смущаться", "missing_index": 4, "options": ["а", "я"]},
            {"word": "ощущать", "missing_index": 4, "options": ["а", "я"]},
            {"word": "возвращаться", "missing_index": 6, "options": ["а", "я"]},
            {"word": "замечательный", "missing_index": 3, "options": ["а", "я"]},
            {"word": "обучающий", "missing_index": 3, "options": ["а", "я"]},
            {"word": "чаепитие", "missing_index": 1, "options": ["а", "я"]},
            {"word": "разочарование", "missing_index": 4, "options": ["а", "я"]},
            {"word": "нечаянно", "missing_index": 1, "options": ["а", "я"]},
            {"word": "участвовать", "missing_index": 1, "options": ["а", "я"]},
        ],
    },

    203: {
        "name": "ЧУ-ЩУ",
        "easy": [
            {"word": "чудо", "missing_index": 1, "options": ["у", "ю"]},
            {"word": "щука", "missing_index": 1, "options": ["у", "ю"]},
            {"word": "чулок", "missing_index": 1, "options": ["у", "ю"]},
            {"word": "чугун", "missing_index": 1, "options": ["у", "ю"]},
            {"word": "щуп", "missing_index": 1, "options": ["у", "ю"]},
            {"word": "ищу", "missing_index": 2, "options": ["у", "ю"]},
            {"word": "тащу", "missing_index": 3, "options": ["у", "ю"]},
            {"word": "молчу", "missing_index": 4, "options": ["у", "ю"]},
            {"word": "хочу", "missing_index": 2, "options": ["у", "ю"]},
            {"word": "чуть", "missing_index": 1, "options": ["у", "ю"]},
        ],
        "normal": [
            {"word": "чужой", "missing_index": 1, "options": ["у", "ю"]},
            {"word": "щуплый", "missing_index": 1, "options": ["у", "ю"]},
            {"word": "чудесный", "missing_index": 1, "options": ["у", "ю"]},
            {"word": "прощу", "missing_index": 4, "options": ["у", "ю"]},
            {"word": "чудак", "missing_index": 1, "options": ["у", "ю"]},
            {"word": "щуриться", "missing_index": 1, "options": ["у", "ю"]},
            {"word": "учу", "missing_index": 1, "options": ["у", "ю"]},
            {"word": "чудовище", "missing_index": 1, "options": ["у", "ю"]},
            {"word": "щукач", "missing_index": 1, "options": ["у", "ю"]},
            {"word": "чугунный", "missing_index": 1, "options": ["у", "ю"]},
        ],
        "hard": [
            {"word": "чувство", "missing_index": 1, "options": ["у", "ю"]},
            {"word": "щурёнок", "missing_index": 1, "options": ["у", "ю"]},
            {"word": "щупальце", "missing_index": 1, "options": ["у", "ю"]},
            {"word": "предчувствие", "missing_index": 5, "options": ["у", "ю"]},
            {"word": "почудилось", "missing_index": 2, "options": ["у", "ю"]},
            {"word": "прищуриться", "missing_index": 4, "options": ["у", "ю"]},
            {"word": "чудаковатый", "missing_index": 1, "options": ["у", "ю"]},
            {"word": "разыщу", "missing_index": 4, "options": ["у", "ю"]},
            {"word": "отыщу", "missing_index": 4, "options": ["у", "ю"]},
            {"word": "почуять", "missing_index": 2, "options": ["у", "ю"]},
        ],
    },
}

def list_all_categories():
    base = list_themes()
    vocab = [{"id": tid, "name": f"📘 {t['name']}"} for tid, t in sorted(VOCAB_CATEGORIES.items())]
    return base + vocab

def list_themes():
    return [{"id": tid, "name": t["name"]} for tid, t in sorted(THEMES.items())]

def _pool_for(theme_id, difficulty):
    theme = THEMES[theme_id]

    words = (
        theme.get(difficulty)
        or theme.get("normal")
        or theme.get("easy")
        or theme.get("hard")
        or []
    )

    return list(words)

def make_word_flash_items(n: int, difficulty: str, theme_id: int, options_k: int = 4) -> list[WordFlashItem]:
    words = _pool_for(theme_id, difficulty)
    pool = words[:]
    random.shuffle(pool)

    # без повторов в рамках сессии, если слов хватает
    if len(pool) >= n:
        pool = pool[:n]

    items: list[WordFlashItem] = []
    for i in range(n):
        target = pool[i % len(pool)]
        distractors = [w for w in words if w != target]
        random.shuffle(distractors)
        options = [target] + distractors[: max(0, options_k - 1)]
        random.shuffle(options)
        items.append(WordFlashItem(item_id=f"wf_t{theme_id}_{difficulty}_{i}", target=target, options=options))
    return items
def make_odd_one_out_items(n: int, difficulty: str, theme_id: int, options_k: int = 4) -> list[WordFlashItem]:
    """Generate 'odd one out' tasks.

    options: list[str] of length options_k (usually 4)
    target: the odd word (must be selected by the player)

    - pick (options_k-1) words from the chosen theme
    - pick 1 word from a different theme
    """
    if options_k < 3:
        options_k = 3

    base_words = _pool_for(theme_id, difficulty)
    base_pool = base_words[:]
    random.shuffle(base_pool)

    other_theme_ids = [tid for tid in THEMES.keys() if tid != theme_id]
    if not other_theme_ids:
        other_theme_ids = [DEFAULT_THEME_ID]

    items: list[WordFlashItem] = []
    for i in range(n):
        group_k = max(2, options_k - 1)
        group = []
        while len(group) < group_k:
            w = base_pool[(i + len(group)) % len(base_pool)]
            if w not in group:
                group.append(w)

        odd_theme_id = random.choice(other_theme_ids)
        odd_words = _pool_for(odd_theme_id, difficulty)
        odd = random.choice([w for w in odd_words if w not in group] or odd_words)

        options = group + [odd]
        options = list(dict.fromkeys(options))
        while len(options) < options_k:
            cand = random.choice([w for w in base_words if w not in options] or base_words)
            options.append(cand)

        options = options[:options_k]
        random.shuffle(options)
        items.append(
            WordFlashItem(
                item_id=f"ooo_t{theme_id}_{difficulty}_{i}",
                target="",  # важно: НЕ показываем ответ на этапе "показа"
                options=options,
                prompt="Выбери лишнее слово",
                correct=odd,
            )
        )
    return items
def make_letter_builder_items(n: int, difficulty: str, theme_id: int) -> list[WordFlashItem]:
    """
    letter_builder:
    - target НЕ показываем (ставим пустую строку)
    - correct = правильное слово (для проверки на фронте)
    - options = перемешанные буквы слова
    """
    words = _pool_for(theme_id, difficulty)
    pool = words[:]
    random.shuffle(pool)

    if len(pool) >= n:
        pool = pool[:n]

    items: list[WordFlashItem] = []
    for i in range(n):
        w = pool[i % len(pool)]
        letters = list(w)
        random.shuffle(letters)

        items.append(
            WordFlashItem(
                item_id=f"lb_t{theme_id}_{difficulty}_{i}",
                target="",               # важно: не показываем слово
                options=letters,          # буквы-кнопки
                prompt=None,              # никаких подсказок
                correct=w,                # правильный ответ
            )
        )
    return items

def _vocab_pool_for(theme_id: int, difficulty: str) -> list[dict]:
    theme = VOCAB_CATEGORIES.get(theme_id)
    if not theme:
        return []
    return theme.get(difficulty) or theme.get("normal") or []

def make_vocab_spell_items(n: int, difficulty: str, theme_id: int) -> list[WordFlashItem]:
    """
    vocab_spell:
    - prompt = слово с пропущенной буквой, например: вел_сипед
    - options = варианты буквы
    - target = НЕ показываем
    - correct = правильная буква
    """
    rows = _vocab_pool_for(theme_id, difficulty)
    if not rows:
        return make_word_flash_items(n, difficulty, DEFAULT_THEME_ID, options_k=4)

    pool = rows[:]
    random.shuffle(pool)

    if len(pool) >= n:
        pool = pool[:n]

    items: list[WordFlashItem] = []
    for i in range(n):
        row = pool[i % len(pool)]
        word = row["word"]
        miss_idx = row["missing_index"]
        correct = word[miss_idx]
        options = list(dict.fromkeys([correct] + row["options"]))
        random.shuffle(options)

        masked = word[:miss_idx] + "_" + word[miss_idx + 1:]

        items.append(
            WordFlashItem(
                item_id=f"vs_t{theme_id}_{difficulty}_{i}",
                target="",           # слово заранее не показываем
                options=options,     # варианты букв
                prompt=masked,       # показываем слово с пропуском
                correct=correct,     # правильная буква
            )
        )
    return items

