from django.http import HttpResponseRedirect
from django.utils import timezone
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.http import Http404


import datetime

from .models import Reservation, Workplace, Employee, Floor
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
        
        workplaces = Workplace.objects.filter(location__isoffice=True).order_by('name')
        res = dict()
        for workplace in workplaces:
            try:
                res[workplace.name] = reservations_today.get(workplace=workplace).employee
            except Reservation.DoesNotExist: 
                res[workplace.name] = "free"

        context = {
            'desks_today': res,
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
        'year': year,
        'week': week,
        'prev_week': week-1,
        'next_week': week+1,
        'day_range': f"{monday:%d.%m.} to {friday:%d.%m.}"
    }

    return render(request, 'workwhere/week.html', context)

class WeekRedirect(generic.RedirectView):
    def get_redirect_url(self):
        return reverse('workwhere:week', args=(timezone.now().year, timezone.now().isocalendar()[1]))

class Floorplans(generic.ListView):
    model = Floor
    template_name = 'workwhere/floorplans.html'
