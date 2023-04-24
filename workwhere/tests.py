import datetime

from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError

from workwhere.models import Workplace, Employee, Location, Reservation
from workwhere.forms import ReservationForm


def create_workplace(name: str, location):
    return Workplace.objects.create(name=name, location=location)


class ReservationModelTest(TestCase):
    def test_same_desk_different_employee_error(self):
        l = Location.objects.create(name='location1', isoffice=True)
        w = Workplace.objects.create(name='A1', location=l)
        e1 = Employee.objects.create(first_name='Dave', last_name='Miller', user_id='dav_mi')
        e2 = Employee.objects.create(first_name='Clare', last_name='Smith', user_id='cla_sm')
        day = "2023-04-22"
        
        Reservation.objects.create(day=day, employee=e1, workplace=w)
        with self.assertRaises(ValidationError):
            Reservation.objects.create(day=day, employee=e2, workplace=w)

    # TBD: Test that two people can reserve same isoffice=False workplace on same day.

    def test_two_reservations_of_employee_on_one_day(self):
        l = Location.objects.create(name='location1', isoffice=True)
        w1 = Workplace.objects.create(name='W1', location=l)
        w2 = Workplace.objects.create(name='W2', location=l)
        e = Employee.objects.create(first_name='Dave', last_name='Miller', user_id='dav_mi')
        day = "2023-04-22"
        
        # First reservation
        Reservation(day=day, employee=e, workplace=w1).save()
        with self.assertRaises(ValidationError):
            # Second reservation on same day
            Reservation(day=day, employee=e, workplace=w2).save()


class ReservationFormTests(TestCase):
    def test_date_in_past(self):
        input_data = {'employee': 1, 'day': "2023-04-21", 'workplace': 1}
        form = ReservationForm(input_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['day'], ['Invalid date - date in past'])

    # also add tests for non-working days and days too far in the future.

    def test_correct_employee_queryset(self):
        Employee(first_name='Dave', last_name='Miller', user_id='dav_mi').save()
        Employee(first_name='Clare', last_name='Smith', user_id='cla_sm', isactive=False).save()
        actual = ReservationForm().fields['employee'].queryset
        expected = Employee.objects.filter(first_name='Dave')
        self.assertQuerysetEqual(actual, expected)

    def test_correct_workplace_queryset(self):
        l = Location.objects.create(name='location1', isoffice=True)
        w1 = Workplace.objects.create(name='W1', location=l)
        w2 = Workplace.objects.create(name='W2', location=l)
        e1 = Employee.objects.create(first_name='Dave', last_name='Miller', user_id='dav_mi')
        e2 = Employee.objects.create(first_name='Clare', last_name='Smith', user_id='cla_sm')

        today = datetime.date(2023, 4, 21)
        tomorrow = today + datetime.timedelta(days=1)

        # One reservation today:
        Reservation(day=today, employee=e1, workplace=w1).save()
        # Everything booked tomorrow:
        Reservation(day=tomorrow, employee=e1, workplace=w1).save()
        Reservation(day=tomorrow, employee=e2, workplace=w2).save()

        # Employee only has a reservation on a different day, and there 
        # should be one workplace still left today
        form = ReservationForm({'employee': e2, 'day': today})
        actual = form.fields['workplace'].queryset
        expected = Workplace.objects.filter(name="W2")
        self.assertQuerysetEqual(actual, expected)

class TodayViewTests(TestCase):
    def test_no_workplaces(self):
        response = self.client.get(reverse('workwhere:today'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No office desks are available.")
        self.assertQuerysetEqual(response.context['desks_today'], [])

class WeekViewTests(TestCase):
    def test_week_redirect(self):
        response = self.client.get(reverse('workwhere:week_redirect'))
        self.assertEqual(response.status_code, 302)

    def test_no_workplaces(self):
        response = self.client.get( \
            reverse('workwhere:week', kwargs={'year':2023, 'week': 15}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Monday")
        self.assertQuerysetEqual(response.context['data'], \
            [['', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']])
