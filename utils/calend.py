import calendar
from datetime import datetime, timedelta


def previous_month():
    current_date = datetime.now()
    previous_month_date = current_date - timedelta(days=current_date.day)
    previous_month_name = calendar.month_name[previous_month_date.month]
    month = f"{months_dict[previous_month_name]} {current_date.year}"
    return month


def next_month():
    current_date = datetime.now()
    next_month_date = current_date.replace(day=1) + timedelta(days=32)
    next_month_name = calendar.month_name[next_month_date.month]
    month = f"{months_dict[next_month_name]} {next_month_date.year}"
    return month


months_dict = {
    "January": "Январь",
    "February": "Февраль",
    "March": "Март",
    "April": "Апрель",
    "May": "Май",
    "June": "Июнь",
    "July": "Июль",
    "August": "Август",
    "September": "Сентябрь",
    "October": "Октябрь",
    "November": "Ноябрь",
    "December": "Декабрь"
}


def current_month():
    current_date = datetime.now()
    month_eng = current_date.strftime("%B")
    now = f"{months_dict[month_eng]} {current_date.year}"
    return now


def current_day():
    t = datetime.now()
    today = t.strftime('%d.%m')
    tom = t + timedelta(days=1)
    tomorrow = tom.strftime('%d.%m')
    return today, tomorrow
