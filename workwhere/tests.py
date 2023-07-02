import datetime

from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError

from workwhere.models import Workplace, Employee, Location, Reservation, Floor
from workwhere.forms import ReservationForm


def create_office_environment():
    """Fill a test database with some basic information for testing"""

    location_office = Location.objects.create(name='location_office', isoffice=True)
    floor1 = Floor.objects.create(name='floor1', location=location_office)
    floor2 = Floor.objects.create(name='floor2', location=location_office)

    Workplace.objects.create(name='w1_1', floor=floor1)
    Workplace.objects.create(name='w2_1', floor=floor2)

    location_no_office = Location.objects.create(name='location_no_office', isoffice=False)
    floor_other = Floor.objects.create(name='floor_other', location=location_no_office)

    Workplace.objects.create(name='home_office', floor=floor_other)
    Workplace.objects.create(name='business_trip', floor=floor_other)
    Workplace.objects.create(name='not_working', floor=floor_other)

    Employee.objects.create(first_name='Dave', last_name='Miller', id='dav_mi')
    Employee.objects.create(first_name='Clare', last_name='Smith', id='cla_sm')
    Employee.objects.create(first_name='Sarah', last_name='Brown', id='sar_br', isactive=False)
    Employee.objects.create(first_name='James', last_name='Davis', id='jam_da', isstudent=True)


class ReservationModelTest(TestCase):
    def test_same_desk_different_employee_error(self):
        create_office_environment()
        workplace1=Workplace.objects.get(name='w1_1')
        dave = Employee.objects.get(pk='dav_mi')
        clare = Employee.objects.get(pk='cla_sm')
        day = "2023-04-22"

        Reservation.objects.create(day=day, employee=dave, workplace=workplace1)
        with self.assertRaises(ValidationError):
            Reservation.objects.create(day=day, employee=clare, workplace=workplace1)

    def test_two_reservations_of_employee_on_one_day_error(self):
        create_office_environment()
        workplace1 = Workplace.objects.get(name='w1_1')
        workplace2 = Workplace.objects.get(name='w2_1')
        dave = Employee.objects.get(pk='dav_mi')
        day = "2023-04-22"
        
        # First reservation
        Reservation(day=day, employee=dave, workplace=workplace1).save()
        with self.assertRaises(ValidationError):
            # Second reservation on same day
            Reservation(day=day, employee=dave, workplace=workplace2).save()

    def test_two_nooffice_reservations_on_same_day(self):
        """There should be no error when creating two reservations for
        workplaces whose location is labeled as 'isoffice=False', like
        e.g. 'home_office'.
        """
        create_office_environment()
        home_office = Workplace.objects.get(name='home_office')
        dave = Employee.objects.get(pk='dav_mi')
        clare = Employee.objects.get(pk='cla_sm')
        day = "2023-04-22"

        Reservation(day=day, employee=dave, workplace=home_office).save()
        Reservation(day=day, employee=clare, workplace=home_office).save()

class ReservationFormTests(TestCase):
    def test_date_in_past(self):
        """Reservation can't be done for date in past"""
        input_data = {'employee': 1, 'day': "2023-04-21", 'workplace': 1}
        form = ReservationForm(input_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['day'], ['Invalid date - date in past'])

    def test_date_non_working_day(self):
        """Reservation can't be done for next sunday"""
        today = datetime.date.today()
        current_weekday = today.isoweekday()
        next_sunday = today + datetime.timedelta(days=7-current_weekday)

        input_data = {'employee': 1, 'day': str(next_sunday), 'workplace': 1}
        form = ReservationForm(input_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['day'], ['Invalid date - not a working day'])

    def test_date_too_far_in_future(self):
        """Reservation can't be done more than 4 weeks into the future"""
        far_future_day = datetime.date.today() + datetime.timedelta(weeks=5)
        input_data = {'employee': 1, 'day': str(far_future_day), 'workplace': 1}
        form = ReservationForm(input_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['day'], \
                         ['Invalid date - date more than 4 weeks into the future'])       

    def test_correct_employee_queryset(self):
        """Only active employees should appear in employee list"""
        create_office_environment()
        actual = ReservationForm().fields['employee'].queryset
        expected = Employee.objects.exclude(pk='sar_br')
        self.assertQuerysetEqual(actual, expected)

    def test_correct_workplace_queryset(self):
        """
        Reserved office workplaces should not appear in the workplace 
        list.
        Reserved non-office workplaces should still appear.
        This should be independent of reservations on other days.
        """
        create_office_environment()
        workplace1 = Workplace.objects.get(name='w1_1')
        workplace2 = Workplace.objects.get(name='w2_1')
        home_office = Workplace.objects.get(name='home_office')
        dave = Employee.objects.get(pk='dav_mi')
        clare = Employee.objects.get(pk='cla_sm')
        james = Employee.objects.get(pk='jam_da')

        today = datetime.date(2023, 4, 21)
        tomorrow = today + datetime.timedelta(days=1)
        after_tomorrow = today + datetime.timedelta(days=2)


        # One office reservation today:
        Reservation(day=today, employee=dave, workplace=workplace1).save()

        form = ReservationForm({'employee': clare, 'day': today})
        expected = Workplace.objects.exclude(pk=workplace1.pk).order_by('-floor__location')

        # 1. Only the today occupied workplace should be missing in the 
        # list.
        actual = form.fields['workplace'].queryset
        self.assertQuerysetEqual(actual, expected, None, None, "test1")

        # 2. Additionally one non-office reservation today. List should 
        # not change:
        Reservation(day=today, employee=james, workplace=home_office).save()
        actual = form.fields['workplace'].queryset
        self.assertQuerysetEqual(actual, expected, None, None, "test2")
        
        # 3. Additionally other reservations the next days. List should
        # still not change.
        Reservation(day=tomorrow, employee=dave, workplace=workplace1).save()
        Reservation(day=tomorrow, employee=clare, workplace=workplace2).save()
        Reservation(day=after_tomorrow, employee=dave, workplace=home_office).save()
        Reservation(day=after_tomorrow, employee=clare, workplace=home_office).save()
        actual = form.fields['workplace'].queryset
        self.assertQuerysetEqual(actual, expected, None, None, "test3")


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
