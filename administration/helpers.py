from datetime import datetime, timedelta
from django.utils.translation import gettext_lazy as _, pgettext

def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'    

def divide_zero_set(n, d):
    return n / d if d else 0

def number_color(n):
    if n > 0:
        return "text-bright-blue"
    elif n < 0:
        return "text-bright-pink"
    else:
        return ""

def number_sign(n):
    if n > 0:
        return "+"
    else:
        return ""

def get_current_week_day_date_dictionary(date):
    """
    *** no params ***
    :return: Dictionary {}
        This method returns a dictionary containing `days` as keys and `month + date` as values.
        i.e {'Monday': 'Sep 2','Tuesday': 'Sep 3', 'Wednesday': 'Sep 4', 'Thursday': 'Sep 5', 'Friday': 'Sep 6', 'Saturday': 'Sep 7', 'Sunday': 'Sep 8'}
        Note: Date is system dependent.
        
        Note: This function returns both a translated day_date_dict (for UI display) and an English day_date_dict_english (for use comparing against database entries)
    """

    today = date
    day_date_dict = {}
    day_date_dict_english = {}
    year_dict = {}
    week_date_list = []
    week_day_list = [_('Sunday'), _('Monday'), _('Tuesday'), _('Wednesday'), _('Thursday'), _('Friday'), _('Saturday')]
    week_start_date = today.add(days=1).start_of('week').date().subtract(days=1).day
    week_end_date = today.add(days=1).end_of('week').date().subtract(days=1).day
    month_end_date = today.add(days=1).start_of('week').date().subtract(days=1).end_of('month').day
    week_start_date_month_name = today.add(days=1).start_of('week').date().subtract(days=1).format('MMM')
    week_end_date_month_name = today.add(days=1).end_of('week').date().subtract(days=1).format('MMM')

    day_char = str(pgettext("character after date"," "))

    if week_start_date < week_end_date:
        week_date_list = [_(week_start_date_month_name) + " " + str(date)+day_char for date in range(week_start_date, week_end_date+1)]
        week_date_list_english = [week_start_date_month_name + " " + str(date) for date in range(week_start_date, week_end_date+1)]
        year_list = [today.year for date in range(week_start_date, week_end_date+1)]
    else:
        week_date_list = [_(week_start_date_month_name) + " " + str(date)+day_char for date in range(week_start_date, month_end_date+1)]
        week_date_list_english = [week_start_date_month_name + " " + str(date) for date in range(week_start_date, month_end_date+1)]
        year_list = [today.year for date in range(week_start_date, month_end_date+1)]

        if week_end_date_month_name == "Jan":
            next_year = today.year + 1
        else:
            next_year = today.year

        for date in range(1, week_end_date+1):
            week_date_list.append(_(week_end_date_month_name) + " " + str(date)+day_char)
            week_date_list_english.append(week_end_date_month_name + " " + str(date))
            year_list.append(next_year)

    for index in range(0, len(week_date_list)):
        day_date_dict[week_day_list[index]] = week_date_list[index]
        day_date_dict_english[week_day_list[index]] = week_date_list_english[index]
        year_dict[week_day_list[index]] = year_list[index]

    return day_date_dict, day_date_dict_english, day_char, year_dict

def get_week_date_and_month_list(date):
    today = date

    week_start_date = today.start_of('week').date().subtract(days=1).day
    week_end_date = today.end_of('week').date().subtract(days=1).day

    month_number = today.date().month
    week_start_date_month = today.start_of('week').date().subtract(days=1).month
    week_end_date_month = today.end_of('week').date().subtract(days=1).month
    week_date_list = []

    if week_start_date < week_end_date:
        week_date_list = [(month_number, date) for date in range(week_start_date, week_end_date + 1)]
    else:
        month_end_date = today.start_of('week').date().subtract(days=1).end_of('month').day
        week_date_list = [(week_start_date_month, date) for date in range(week_start_date, month_end_date + 1)]
        for date in range(1, week_end_date + 1):
            week_date_list.append((week_end_date_month, date))

    return week_date_list

def get_timings_range():
    #Note: This function returns both a translated time_list (for UI display) and a translated-English time_list_tuples (for use comparing against database entries)

    ante_meridiem_start = 9  # 9 am
    post_meridiem_end = 9  # 9 pm

    time_list = [(item, _(" AM")) for item in range(ante_meridiem_start, 12)]
    time_list_english = [(item, " AM") for item in range(ante_meridiem_start, 12)]
    time_list.append((12, _(" PM")))
    time_list_english.append((12, " PM"))
    for item in range(1, post_meridiem_end + 1):
        time_list.append((item, _(" PM")))
        time_list_english.append((item, " PM"))

    return time_list, zip(time_list, time_list_english)

def blank_function_to_define_translations():
    #This function only exists to define strings for translation

    possible_lc_times = [
        _("12am"),
        _("1am"),
        _("2am"),
        _("3am"),
        _("4am"),
        _("5am"),
        _("6am"),
        _("7am"),
        _("8am"),
        _("9am"),
        _("10am"),
        _("11am"),
        _("12pm"),
        _("1pm"),
        _("2pm"),
        _("3pm"),
        _("4pm"),
        _("5pm"),
        _("6pm"),
        _("7pm"),
        _("8pm"),
        _("9pm"),
        _("10pm"),
        _("11pm")
    ]

    possible_month_abvs = [
        _("Jan"),
        _("Feb"),
        _("Mar"),
        _("Apr"),
        _("May"),
        _("Jun"),
        _("Jul"),
        _("Aug"),
        _("Sep"),
        _("Oct"),
        _("Nov"),
        _("Dec")
    ]

    return