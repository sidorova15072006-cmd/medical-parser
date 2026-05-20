import re

def extract_data(text):
    result = {
        "demographics": {},
        "chief_complaint": "",
        "symptoms": [],
        "medications": [],
        "negated_symptoms": [],
        "follow_up_questions": []
    }

    text_low = text.lower()

    # ========== ИМЯ ==========
    name_match = re.search(r'меня зовут ([А-Яа-я]+(?:\s+[А-Яа-я]+)?)', text)
    if name_match:
        result["demographics"]["name"] = name_match.group(1)

    # ========== ВОЗРАСТ ==========
    age = re.search(r'(\d+)\s*(лет|года|год)', text_low)
    if age:
        result["demographics"]["age"] = int(age.group(1))

    # ========== ПОЛ ==========
    if "name" in result["demographics"]:
        name = result["demographics"]["name"].lower()
        if name.endswith(('а', 'я', 'ия')):
            result["demographics"]["gender"] = "female"
        else:
            result["demographics"]["gender"] = "male"

    # ========== ГЛАВНАЯ ЖАЛОБА И СИМПТОМЫ ==========
    # Проверяем наличие жалоб
    if 'температур' in text_low:
        result["chief_complaint"] = "Повышенная температура"
        result["symptoms"].append({
            "type": "температура",
            "body_site": ["общее состояние"],
            "severity": "высокая" if 'высок' in text_low else "",
            "duration_value": None,
            "duration_unit": "",
            "character": ""
        })
    
    if 'болит' in text_low or 'боль' in text_low:
        symptom = {
            "type": "боль",
            "body_site": [],
            "severity": "сильная" if 'сильн' in text_low or 'очень' in text_low else "",
            "duration_value": None,
            "duration_unit": "",
            "character": "иррадиирующая" if 'отдает' in text_low else ""
        }
        
        # Локализация боли
        if 'поясниц' in text_low or 'спин' in text_low:
            symptom["body_site"].append("поясница")
        if 'ног' in text_low or 'нога' in text_low:
            if 'лева' in text_low:
                symptom["body_site"].append("левая нога")
            elif 'права' in text_low:
                symptom["body_site"].append("правая нога")
            else:
                symptom["body_site"].append("нога")
        if 'голов' in text_low:
            symptom["body_site"].append("голова")
        if 'живот' in text_low:
            symptom["body_site"].append("живот")
        if 'груд' in text_low:
            symptom["body_site"].append("грудь")
        
        # Длительность
        duration = re.search(r'(\d+)\s*(недел|день|дней|месяц)', text_low)
        if duration:
            symptom["duration_value"] = int(duration.group(1))
            if 'недел' in duration.group(2):
                symptom["duration_unit"] = "неделя"
            elif 'день' in duration.group(2):
                symptom["duration_unit"] = "день"
            elif 'месяц' in duration.group(2):
                symptom["duration_unit"] = "месяц"
        
        if symptom["body_site"]:
            result["symptoms"].append(symptom)
            if not result["chief_complaint"]:
                result["chief_complaint"] = f"Боль в {symptom['body_site'][0]}"
    
    # Если нет конкретных жалоб, но есть общее недомогание
    if not result["symptoms"] and not result["chief_complaint"]:
        if 'болею' in text_low or 'болен' in text_low or 'плохо' in text_low:
            result["chief_complaint"] = "Общее недомогание"

    # ========== ЛЕКАРСТВА ==========
    if 'обезбол' in text_low or 'обезболивающ' in text_low:
        result["medications"].append({
            "name": "обезболивающие",
            "effect": "почти не помогают" if 'не помога' in text_low else "упоминаются пациентом"
        })
    elif 'лекарств' in text_low or 'таблетк' in text_low:
        result["medications"].append({
            "name": "лекарства (не уточнены)",
            "effect": "упоминаются пациентом"
        })

    # ========== ОТРИЦАЕМЫЕ СИМПТОМЫ ==========
    if 'температур' in text_low and ('нет' in text_low or 'вроде нет' in text_low):
        result["negated_symptoms"].append({
            "type": "температура",
            "stated_as": "нет" if 'нет' in text_low else "вроде нет"
        })
    
    if 'кашля' in text_low and 'нет' in text_low:
        result["negated_symptoms"].append({
            "type": "кашель",
            "stated_as": "нет"
        })

    # ========== УТОЧНЯЮЩИЕ ВОПРОСЫ ==========
    questions = []
    
    if "age" not in result["demographics"]:
        questions.append("Сколько вам лет?")
    
    if "name" not in result["demographics"]:
        questions.append("Как вас зовут?")
    
    if not result["symptoms"]:
        questions.append("Что именно вас беспокоит?")
    
    if 'поясниц' in text_low or 'спин' in text_low:
        questions.append("Когда началась боль в спине?")
        questions.append("Есть ли онемение в ногах?")
    
    if 'температур' not in text_low:
        questions.append("Измеряли ли вы температуру?")
    
    if not result["medications"]:
        questions.append("Какие лекарства вы принимали до визита?")
    
    result["follow_up_questions"] = questions[:6]

    return result