import datetime
import calendar

from django.utils import timezone
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q

from .models import Reservation, Workplace, Floor, TextInfo
from .forms import ReservationForm


def index(request):
    """
    The reservation main page.
    """
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        print(request.POST)
        if form.is_valid():
            selected_employee = form.cleaned_data['employee']
            selected_day = form.cleaned_data['day']
            selected_workplace = form.cleaned_data['workplace']

            _, _ = Reservation.objects.update_or_create(
                day=selected_day, 
                employee=selected_employee,
                defaults={'workplace': selected_workplace})         
            alert = "success"
            message = f"Reserved: {selected_employee.first_name}, {selected_day: %d.%m.}, {selected_workplace}"
        else:
            alert = "error"
            message = "Reservation failed"
    else:
        form = ReservationForm(initial={'day': timezone.now().date()})
        alert = None
        message = None

    maps = Floor.objects.all()

    context = {
        'form': form,
        'alert': alert,
        'message': message,
        'maps': maps
    }

    return render(request, 'workwhere/index.html', context)


def load_workplaces(request):
    """
    Load the free workplace options available for an employee on a
    specific day. Needed in the reservatino form on the index page.
    """
    
    day = request.GET.get('day')
    employee = request.GET.get('employee')
    reserved_pk = None
    if day and employee:
        other_desk_reservations_today = Reservation.objects \
            .filter(day=day, workplace__floor__location__isoffice=True) \
            .exclude(employee=employee)
        choice_workplaces = Workplace.objects \
            .exclude(reservation__in=other_desk_reservations_today) \
            .order_by('floor__location__isoffice', 'name')

        already_reserved_workplace = Workplace.objects \
            .filter(reservation__employee=employee, reservation__day=day)
        if already_reserved_workplace.exists():
            reserved_pk = already_reserved_workplace.first().pk
    else:
        choice_workplaces = Workplace.objects.none()

    context = {
        'workplaces': choice_workplaces, 
        'reserved_pk': reserved_pk,
        }
        
    return render(request, 'workwhere/workplace_dropdown_list_options.html', context)


class Today(generic.View):
    """
    Gets reservation data on office workplaces for current day.
    Helps to find free places and who sits where.
    """
    template_name = 'workwhere/today.html'

    def get(self, request):
        reservations_today = Reservation.objects \
            .filter(day=timezone.now().date()) \
            .select_related('employee')
        
        status = {}
        for floor in Floor.objects.filter(location__isoffice=True):
            if floor not in status:
                status[floor] = {}

            workplaces = Workplace.objects.filter(floor=floor, floor__location__isoffice=True).order_by('name')
            for workplace in workplaces:
                try:
                    status[floor][workplace.name] = reservations_today.get(workplace=workplace).employee
                except Reservation.DoesNotExist: 
                    status[floor][workplace.name] = ""

        context = {
            'desks_today': status,
            'title': f"Reservations on {timezone.now():%A, %B %d (%Y)}"
        }

        return render(request, self.template_name, context)

def week(request, year, week):
    """
    Gets reservation data for office workplaces in a given week.
    """
    try:
        monday = datetime.date.fromisocalendar(year, week, 1)
        friday = datetime.date.fromisocalendar(year, week, 5)
    except ValueError:
        raise Http404('Year or week not valid.')

    weekdays = [monday + datetime.timedelta(days=i) for i in range(5)]
    weekday_names = [day.strftime("%A") for day in weekdays]
    data = [['', *weekday_names]]
    for workplace in Workplace.objects.filter(floor__location__isoffice=True).order_by('name'):
        row = [workplace]
        for day in weekdays:
            try:
                reserved = Reservation.objects.get(day=day, workplace=workplace)
            except Reservation.DoesNotExist:
                reserved = False
            row.append('-' if not reserved else reserved.employee)  
        data.append(row)

    context = {
        'data': data,
        'title': 'Workplace availability',
        'date': monday.isocalendar(),
        'prev': (monday - datetime.timedelta(weeks=1)).isocalendar(),
        'next': (monday + datetime.timedelta(weeks=1)).isocalendar(),
        'day_range': f"{monday:%d.%m.} to {friday:%d.%m.}",
    }

    return render(request, 'workwhere/week.html', context)

class WeekRedirect(generic.RedirectView):
    def get_redirect_url(self):
        # Use +2 days in the future, so on Saturday it already
        # switches to the coming week.
        now = timezone.now() + datetime.timedelta(days=2)

        return reverse('workwhere:week', args=(now.year, now.isocalendar()[1]))


class Info(generic.ListView):
    model = TextInfo
    template_name = 'workwhere/info.html'
    ordering = ['order']


from workalendar.registry import registry

@login_required
def summary(request, year, month):
    """
    Gets reservation summary data for employees in a given month.
    """
    try:
        first = datetime.date(year, month, 1)
        last = datetime.date(year, month, calendar.monthrange(year, month)[1])
    except ValueError:
        raise Http404('Year or month not valid.')

    # Using ISO 3166-1 and ISO 3166-2 countries or regions like e.g. "ES-AN"
    # to select holidays. See also 
    # https://workalendar.github.io/workalendar/iso-registry.html
    holidays_calendar = registry.get("ES-AN")
    workdays_count = holidays_calendar().get_working_days_delta(first, last)
    
    report_per_person = _get_per_person_summary(year, month, workdays_count)

    report_per_day = _get_per_day_summary(year, month, workdays_count)

    context = {
        'data_per_person': report_per_person,
        'workdays_count': workdays_count,
        'data_per_day': report_per_day,
        'date': first,
        'prev': (first - datetime.timedelta(days=1)).replace(day=1),
        'next': (first + datetime.timedelta(days=31)).replace(day=1),        
    }

    return render(request, 'workwhere/summary.html', context)

def _get_per_day_summary(year, month, workdays_count):
    reservations = Reservation.objects \
        .filter(day__year=year, day__month=month, workplace__floor__location__isoffice=True) \
        .select_related('workplace__floor__location')

    reservation_counts = reservations.values('day', 'workplace__floor__location__name', 'employee__isstudent') \
        .annotate(count_all=Count('id'), count_nonstudent=Count('id', filter=Q(employee__isstudent=False)))

    result = {}

    for count in reservation_counts:
        day = count['day']
        location_name = count['workplace__floor__location__name']
        reservation_count = count['count_all']
        nonstudent_count = count['count_nonstudent']

        if location_name not in result:
            result[location_name] = {}
            result[location_name]['per_day'] = {}
            result[location_name]['total'] = 0
            result[location_name]['total_nonstudent'] = 0


        result[location_name]['per_day'][day] = reservation_count
        result[location_name]['total'] += 1
        if not count['employee__isstudent']:
            result[location_name]['total_nonstudent'] += 1

    for location in result.keys():
        total_workplaces_this_month = workdays_count * Workplace.objects.filter(floor__location__name=location).count()
        result[location]['total_rate'] = 100*result[location]['total']/total_workplaces_this_month
        result[location]['total_nonstudent_rate'] = 100*result[location]['total_nonstudent']/total_workplaces_this_month

    return result

def _get_per_person_summary(year, month, workdays_count):
    reservations = Reservation.objects \
        .filter(day__year=year, day__month=month) \
        .select_related('employee')

    reservation_counts = reservations.values('employee__id', 'employee__first_name', 'employee__last_name') \
        .annotate(total_count=Count('id'), office_count=Count('id', filter=Q(workplace__floor__location__isoffice=True)))

    result = {}

    for count in reservation_counts:
        full_name = f"{count['employee__first_name']} {count['employee__last_name']}"
        result[count['employee__id']] = {
            'name': full_name,
            'total_count': count['total_count'],
            'total_rate': count['total_count']/workdays_count*100,
            'office_count': count['office_count'],
            'office_rate': count['office_count']/workdays_count*100,
        }

    return result

class SummaryRedirect(generic.RedirectView):
    def get_redirect_url(self):
        first_of_this_month = timezone.now().replace(day=1)
        year_of_last_month = (first_of_this_month - datetime.timedelta(days=1)).year
        last_month = (first_of_this_month - datetime.timedelta(days=1)).month
        return reverse('workwhere:summary', args=(year_of_last_month, last_month))
