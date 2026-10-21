"""Собирает offers.json для трекера из предложений сайта (../../bank-offers/data.py)
и условий RKO Group, которые владелец прислал скриншотами 22.10.2026.

Запуск из корня репозитория: python3 tools/offers_from_site.py
Трекер добавляет офферы из offers.json один раз и дальше их не трогает: правки делаются в самом трекере.
"""
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = runpy.run_path(str(ROOT.parent.parent / 'bank-offers' / 'data.py'))
# На izum-partners.ru пока нет SSL, поэтому ссылки на сайт через http.
SITE_URL = 'http://izum-partners.ru'
CAT = {'cards': 'debit', 'credit': 'credit', 'business': 'rko'}

# Условия из кабинета RKO Group. Чего нет на скриншотах, не заполняем.
RKO = {
    'vtb-mir': {
        'name': 'ВТБ — дебетовая карта «Мир» с розыгрышем',
        'payout': 2000, 'hold': '30 дней',
        'action': 'Выдача + активация: покупка новым клиентом от 500 ₽ по карте с 08.10.2026 по 31.12.2026',
        'terms': ['Не учитываются: СБП, переводы, снятие, ЖКХ, мобильная связь, консультационные платежи (Авито, Юла)'],
        'notes': 'RKO: ставка по дате конверсии, обработка до 60 дней, cookie 30 дней.',
    },
    't-debit': {
        'name': 'Т-Банк — дебетовая карта Black «Мир»',
        'payout': 1400, 'hold': '30 дней',
        'action': 'Выдача + транзакция: покупка от 100 ₽',
        'terms': ['Нет активной кредитной карты Т-Банка не менее 365 дней (так в условиях RKO)'],
        'notes': 'RKO: ставка по дате клика, обработка до 30 дней, cookie 30 дней.',
    },
    'halva-premium': {
        'name': 'Совкомбанк — X-CARD Премиум',
        'cat': 'debit',  # в RKO это дебетовая карта, на сайте предложение лежит в кредитных
        'payout': 5000, 'hold': '30 дней',
        'action': 'Выдача карты по заявке, переданной в банк, в течение 30 дней с даты заявки',
        'terms': ['Кросс-селлы (выдачи по нецелевым заявкам) не оплачиваются'],
        'notes': 'RKO: ставка по дате конверсии, обработка до 30 дней, cookie 30 дней. '
                 'В RKO это «X-CARD Премиум дебетовая», а на сайте «Карта Xalva Premium»: проверьте, что ссылка ведёт на нужный оффер.',
    },
    't-bank-ip': {
        'name': 'Т-Банк — регистрация ИП',
        'payout': 3500, 'hold': '30 дней',
        'action': 'Открытие ИП',
        'terms': ['Оффер доступен по согласованию: нужно запросить доступ в RKO Group'],
        'notes': 'RKO: ставка по дате ЦД, обработка до 60 дней, cookie 30 дней. Партнёрской ссылки пока нет.',
    },
    't-credit': {'name': 'Т-Банк — кредитная карта'},
    'vtb-card': {'name': 'ВТБ — дебетовая карта «Мир» без розыгрыша'},
}
UNKNOWN = 'Выплату, холд и целевое действие уточните в RKO Group.'

offers = []
for o in SITE['OFFERS']:
    r = RKO.get(o['id'], {})
    notes = [r.get('notes') or UNKNOWN]
    if o.get('hidden'):
        notes.append('Страница скрыта: открывается только по прямой ссылке.')
    offers.append({
        'id': 'izum-' + o['id'],
        'name': r.get('name') or f"{o['bank']} — {o['title']}",
        'cat': r.get('cat') or CAT.get(o['cat'], 'rko'),
        'status': 'active',
        'payout': r.get('payout', 0),
        'days': '',
        'hold': r.get('hold', ''),
        'action': r.get('action', ''),
        'terms': '\n'.join([*o.get('requirements', []), *r.get('terms', [])]),
        'site': f"{SITE_URL}/predlozheniya/{o['slug']}/",
        'url': o.get('url') or '',
        'network': 'RKO Group',
        'notes': ' '.join(notes),
    })

(ROOT / 'offers.json').write_text(json.dumps({'offers': offers}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print(f'offers.json: {len(offers)} офферов')
