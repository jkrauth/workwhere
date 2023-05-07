import datetime
import calendar

from django.utils import timezone
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.http import Http404
from django.contrib.auth.decorators import login_required

from .models import Reservation, Workplace, Floor, Location
from .forms import ReservationForm


def index(request):
    # The reservation page
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        print(request.POST)
        if form.is_valid():
            selected_employee = form.cleaned_data['employee']
            selected_day = form.cleaned_data['day']
            selected_workplace = form.cleaned_data['workplace']

            reservation, created = Reservation.objects.update_or_create(
                day=selected_day, 
                employee=selected_employee,
                defaults={'workplace': selected_workplace})         
            alert = "success"
            message = f"Reserved: {selected_employee.first_name}, {selected_day: %d.%m.}, {selected_workplace}"
            #return HttpResponseRedirect(reverse('workwhere:today')) # Redirect somewhere else in case of success
        else:
            alert = "error"
            message = "Reservation failed"
    else:
        form = ReservationForm(initial={'day': timezone.now().date()})
        alert = None
        message = None

    context = {
        'form': form,
        'alert': alert,
        'message': message
    }

    return render(request, 'workwhere/index.html', context)


def load_workplaces(request):
    day = request.GET.get('day')
    employee = request.GET.get('employee')
    reserved_pk = None
    if day and employee:
        other_desk_reservations_today = Reservation.objects.filter(day=day, workplace__location__isoffice=True).exclude(employee=employee)
        choice_workplaces = Workplace.objects.exclude(reservation__in=other_desk_reservations_today).order_by('location__isoffice', 'name')

        already_reserved_workplace = Workplace.objects.filter(reservation__employee=employee, reservation__day=day)
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
    """
    template_name = 'workwhere/today.html'

    def get(self, request):
        reservations_today = Reservation.objects.filter(day=timezone.now().date())
        
        locationDict = dict()
        for location in Location.objects.filter(isoffice=True):
            workplaces = Workplace.objects.filter(location=location, location__isoffice=True).order_by('name')
            workplace_status = dict()
            for workplace in workplaces:
                try:
                    workplace_status[workplace.name] = reservations_today.get(workplace=workplace).employee
                except Reservation.DoesNotExist: 
                    workplace_status[workplace.name] = "free"

            locationDict[location.name] = workplace_status
        context = {
            'desks_today': locationDict,
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
    for workplace in Workplace.objects.filter(location__isoffice=True).order_by('name'):
        row = [workplace]
        for day in weekdays:
            try:
                reserved = Reservation.objects.get(day=day, workplace=workplace)
            except Reservation.DoesNotExist:
                reserved = False
            row.append('free' if not reserved else reserved.employee)  
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

class Floorplans(generic.ListView):
    model = Floor
    template_name = 'workwhere/floorplans.html'


from workalendar.europe import Spain

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

    workdays_count = Spain().get_working_days_delta(first, last)
    
    report = dict()
    for reservation in Reservation.objects.filter(day__year=year, day__month=month):
        if reservation.employee.id in report:
            report[reservation.employee.id]['reservation_count'] += 1
            if reservation.workplace.location.isoffice:
                report[reservation.employee.id]['office_count'] += 1
        else:
            report[reservation.employee.id] = {
                'name': str(reservation.employee),
                'reservation_count': 1,
                'office_count': 1 if reservation.workplace.location.isoffice else 0,
                'office_rate': None,
                'reservation_rate': None,
            }
    
    for employee in report:
        report[employee]['office_rate'] = 100*report[employee]['office_count'] / workdays_count
        report[employee]['reservation_rate'] = 100*report[employee]['reservation_count'] / workdays_count

    context = {
        'data': report,
        'workdays_count': workdays_count,
        'title': f'Summary',
        'date': first,
        'prev': (first - datetime.timedelta(days=1)).replace(day=1),
        'next': (first + datetime.timedelta(days=31)).replace(day=1),        
    }

    return render(request, 'workwhere/summary.html', context)

class SummaryRedirect(generic.RedirectView):
    def get_redirect_url(self):
        first_of_this_month = timezone.now().replace(day=1)
        year_of_last_month = (first_of_this_month - datetime.timedelta(days=1)).year
        last_month = (first_of_this_month - datetime.timedelta(days=1)).month
        return reverse('workwhere:summary', args=(year_of_last_month, last_month))
