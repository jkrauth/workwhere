import datetime

from workalendar.europe import Spain
from django.core.exceptions import ValidationError
from django import forms
from django.db.models import Q

from .models import Reservation, Workplace, Employee


class SearchSelect(forms.Select):
    template_name = 'workwhere/search_select.html'

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['employee', 'day', 'workplace']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        #self.fields['employee'].widget.attrs.update({'class': 'form-select selectpicker'})
        self.fields['employee'].widget = SearchSelect(attrs={
            'class': 'form-control', 
            'placeholder': 'Type to search...',
            })
        self.fields['employee'].queryset = Employee.objects.filter(isactive=True)

        self.fields['day'].widget = forms.DateInput(attrs={
            'class': 'form-control', 
            'type': 'date',  # <--- IF I REMOVE THIS LINE, THE INITIAL VALUE IS DISPLAYED
            'min': str(datetime.date.today()),
            'max': str(datetime.date.today()+datetime.timedelta(weeks=4)),
            })

        #self.fields['workplace'].widget = SearchSelect(attrs={'class': 'form-control', 'placeholder': 'Type to search...'})
        self.fields['workplace'].widget.attrs.update({'class': 'form-select selectpicker'})
        self.fields['workplace'].queryset = Workplace.objects.none()

        self.label_suffix = "" # Remove default ":"

        if 'day' in self.data and 'employee' in self.data:
            try:
                day = self.data['day']
                employee = self.data['employee']

                other_desk_reservations_today = Reservation.objects.filter(day=day, workplace__location__isoffice=True).exclude(employee=employee)
                available_workplaces = Workplace.objects.exclude(reservation__in=other_desk_reservations_today)
                self.fields['workplace'].queryset = available_workplaces.order_by('location__isoffice')
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty workplace queryset

        #elif self.instance.pk:
        #    self.fields['workplace'].queryset = Workplace.objects.all()

    def clean_day(self):
        data = self.cleaned_data['day']

        if data < datetime.date.today():
            raise ValidationError('Invalid date - date in past')

        if data > datetime.date.today() + datetime.timedelta(weeks=4):
            raise ValidationError('Invalid date - date more than 4 weeks into the future')

        if not Spain().is_working_day(data):
            raise ValidationError('Invalid date - not a working day')

        return data 
