import datetime
from workalendar.europe import Spain
from django.core.exceptions import ValidationError
from django import forms
from django.db.models import Q

import datetime
from .models import Reservation, Workplace, Employee

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['employee', 'day', 'workplace']
        widgets = {
            'employee': forms.Select(
                attrs={
                    'class': 'form-select selectpicker', 
                    }),
            'day': forms.DateInput(
                #format=(r'%m/%d/%y'),
                attrs={'class': 'form-control', 
                       #'placeholder': 'Select a date',
                       'type': 'date',  # <--- IF I REMOVE THIS LINE, THE INITIAL VALUE IS DISPLAYED
                       'min': str(datetime.date.today()),
                       'max': str(datetime.date.today()+datetime.timedelta(weeks=4)),

                      }),
            'workplace': forms.Select(
                attrs={
                    'class': 'form-control',
                    }),            
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(isactive=True)
        self.fields['workplace'].queryset = Workplace.objects.none()
        self.label_suffix = "" # Remove default ":"

        if 'day' in self.data and 'employee' in self.data:
            try:
                day = self.data['day']
                employee = self.data['employee']
                
                free_workplaces = Workplace.objects.exclude(reservation__day=day)
                already_reserved_workplace = Workplace.objects.filter(reservation__day=day, reservation__employee=employee)
                available_workplaces =  free_workplaces | already_reserved_workplace
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

        es_calendar = Spain()
        if not es_calendar.is_working_day(data):
            raise ValidationError('Invalid date - not a working day')

        return data 
