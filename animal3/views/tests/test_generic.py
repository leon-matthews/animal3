
import datetime
import json

from django.http import HttpResponse
from django.test import TestCase
from django.utils import timezone

from animal3.utils.testing import GET
from animal3.tests.models import TestModel

from ..generic import TotalsDailyView


class TotalsDailyViewValidateDatesTest(TestCase):
    """
    Test date validation `TotalsDailyView` base class.
    """
    class View(TotalsDailyView):
        model = TestModel

    def assert400(self, response: HttpResponse, message: str) -> None:
        """
        Response a bad request with the given error message.
        """
        self.assertEqual(response.status_code, 400)
        returned = json.loads(response.content)
        expected = {'error': message}
        self.assertEqual(returned, expected)

    def test_error_no_start(self) -> None:
        response = GET(self.View)
        self.assert400(response, "Missing required 'start' parameter")

    def test_error_end_before_start(self) -> None:
        data = {
            'start': '2021-12-19',
            'end': '2021-06-28',
        }
        response = GET(self.View, data=data)
        self.assert400(response, "Start must come before end")

    def test_error_invalid_start(self) -> None:
        data = {
            'start': 'banana',
        }
        response = GET(self.View, data=data)
        self.assert400(response, "start: time data 'banana' does not match format '%Y-%m-%d'")

    def test_error_invalid_end(self) -> None:
        data = {
            'start': '2021-12-19',
            'end': 'carrot',
        }
        response = GET(self.View, data=data)
        self.assert400(response, "end: time data 'carrot' does not match format '%Y-%m-%d'")

    def test_error_invalid_start_and_end(self) -> None:
        data = {
            'start': 'banana',
            'end': 'carrot',
        }
        response = GET(self.View, data=data)
        self.assert400(response, "start: time data 'banana' does not match format '%Y-%m-%d'")

    def test_valid(self) -> None:
        """
        Start and end given as inclusive range.
        """
        data = {
            'start': '2021-12-29',
            'end': '2021-12-31',
        }
        response = GET(self.View, data=data)
        self.assertEqual(response.status_code, 200)
        returned = json.loads(response.content)
        expected = [
            {'count': 0, 'date': '2021-12-29'},
            {'count': 0, 'date': '2021-12-30'},
            {'count': 0, 'date': '2021-12-31'},
        ]
        self.assertEqual(returned, expected)

    def test_valid_no_end(self) -> None:
        """
        Today's date should be used if no end date is given.
        """
        last_week = timezone.localtime() - datetime.timedelta(days=7)
        data = {
            'start': last_week.strftime('%Y-%m-%d'),
        }
        response = GET(self.View, data=data)
        self.assertEqual(response.status_code, 200)
        returned = json.loads(response.content)
        self.assertEqual(len(returned), 8)
