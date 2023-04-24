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

    context = {
        'num_users': Employee.objects.count(),
        'num_workplaces': Workplace.objects.count(),
    }

    return render(request, 'workwhere/index.html', context=context)


def reserve(request):
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            selected_employee = form.cleaned_data['employee']
            selected_day = form.cleaned_data['day']
            selected_workplace_id = form.cleaned_data['workplace']

            reservation, created = Reservation.objects.update_or_create(
                day=selected_day, 
                employee=selected_employee,
                defaults={'workplace': selected_workplace_id})         

            return HttpResponseRedirect(reverse('workwhere:today'))
    else:
        form = ReservationForm()

    context = {
        'form': form,
    }

    return render(request, 'workwhere/reserve.html', context)


def load_workplaces(request):
    day = request.GET.get('day')
    employee = request.GET.get('employee')
    reserved_pk = None
    if day and employee:
        already_reserved_workplace = Workplace.objects.filter(reservation__employee=employee, reservation__day=day)
        free_workplaces = Workplace.objects.exclude(reservation__day=day)
        choice_workplaces = (free_workplaces | already_reserved_workplace).order_by('location__isoffice')

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
        
        workplaces = sorted(Workplace.objects.filter(location__isoffice=True), key=lambda x: x.name)
        res = dict()
        for workplace in workplaces:
            try:
                res[workplace.name] = reservations_today.get(workplace=workplace).employee
            except Reservation.DoesNotExist: 
                res[workplace.name] = "free"

        context = {
            'desks_today': res,
            'date': timezone.now(),
        }

        return render(request, self.template_name, context)

def week(request, year, week):
    """
    Gets reservation data for office workplaces in a given week.
    """
    try:
        monday = datetime.date.fromisocalendar(year, week, 1)
    except ValueError:
        raise Http404('Year or week not valid.')

    weekdays = [monday + datetime.timedelta(days=i) for i in range(5)]
    weekday_names = [day.strftime("%A") for day in weekdays]
    data = [['', *weekday_names]]
    for workplace in Workplace.objects.exclude(location__isoffice=False):
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
        'title': f'Workplace availability in week {week}',
        'year': year,
        'prev_week': week-1,
        'next_week': week+1,
    }

    return render(request, 'workwhere/week.html', context)

class WeekRedirect(generic.RedirectView):
    def get_redirect_url(self):
        return reverse('workwhere:week', args=(timezone.now().year, timezone.now().isocalendar()[1]))

class Floorplans(generic.ListView):
    model = Floor
    template_name = 'workwhere/floorplans.html'
