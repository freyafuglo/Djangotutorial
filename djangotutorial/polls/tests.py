import datetime
import pytest
import xlrd
import os

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .models import Question, Choice, Person
from .views import barchart_test, SearchForm
from mysite.celery import debug_task

 

def create_question(question_text, days):
    """
    Create a question with the given `question_text` and published the
    given number of `days` offset to now (negative for questions published
    in the past, positive for questions that have yet to be published).
    """
    time = timezone.now() + datetime.timedelta(days=days)
    return Question.objects.create(question_text=question_text, pub_date=time)
       
        

class QuestionModelTests(TestCase):
    """ Question Model Tests """
    def test_was_published_recently_with_future_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is in the future.
        """
        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=time)
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is older than 1 day.
        """
        time = timezone.now() - datetime.timedelta(days=1, seconds=0) # or 1 sec
        old_question = Question(pub_date=time)
        self.assertIs(old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        """
        was_published_recently() returns True for questions whose pub_date
        is within the last day.
        """
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(pub_date=time)
        self.assertIs(recent_question.was_published_recently(), True)
    
class QuestionIndexViewTests(TestCase):
    """ Testing Question Index View """
    def test_no_questions(self):
        """
        If no questions exist, an appropriate message is displayed.
        """
        response = self.client.get(reverse("polls:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerySetEqual(response.context["latest_question_list"], [])

    def test_past_question(self):
        """
        Questions with a pub_date in the past are displayed on the
        index page.
        """
        question = create_question(question_text="Past question.", days=-30)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(response.context["latest_question_list"], [question],
                                 )
        
    def test_future_question(self):
        """
        Questions with a pub_date in the future aren't displayed on
        the index page.
        """
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse("polls:index"))
        self.assertContains(response, "No polls are available.")
        self.assertQuerySetEqual(response.context["latest_question_list"], [])

    def test_future_question_and_past_question(self):
        """
        Even if both past and future questions exist, only past questions
        are displayed.
        """
        question = create_question(question_text="Past question.",days=-30)
        create_question(question_text="Future question", days=30)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(response.context["latest_question_list"],
            [question],
        )

    def test_two_past_questions(self):
        """
        The questions index page may display multiple questions.
        """
        question1 = create_question(question_text="Past question 1.", days=-30)
        question2 = create_question(question_text="Past question 2.", days=-5)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(
            response.context["latest_question_list"],
            [question2, question1],
        )

class QuestionDetailViewTests(TestCase):
    def test_future_question(self):
        """
        The detail view of a question with a pub_date in the future
        returns a 404 not found.
        """
        future_question = create_question(question_text="Future question", days=5)
        url = reverse("polls:detail", args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question(self):
        """
        The detail view of a question with a pub_date in the past
        displays the question's text.
        """
        past_question = create_question(question_text="Past Question.", days=-5)
        url = reverse("polls:detail", args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)


class CreateViewTests(TestCase):
    """ Testing Creating New Questions """

    def test_create_question_with_choice(self):
        """ 
        When the correct data for a question is forwared
        Then a new question object should be created 
        """

        payload_data = {
            "question_text": "hej",

            "choice_set-TOTAL_FORMS": 1,
            "choice_set-INITIAL_FORMS": 0,
            #"choice_set-MIN_NUM_FORMS": 0,
            #"choice_set-MAX_NUM_FORMS": 1000,
            "choice_set-0-choice_text": "hi",
            #"choice_set-0-id": "",
            #"choice_set-0-question": "",
            #"choice_set-__prefix__-choice_text": "",
            #"choice_set-__prefix__-id": "",
            #"choice_set-__prefix__-question": "",          
        }
       
        response = self.client.post(reverse("polls:create"), data=payload_data,)

        self.assertEqual(response.status_code, 302)

        self.assertEqual(Question.objects.count(), 1)
        self.assertEqual(Choice.objects.count(), 1)
    

    def test_invalid_formset(self):
        """ 
        When attempting to create a new question with incorrect data
        Then there shouldn't be a new question object created
        """

        payload_data = {
            "question_text": "hi",

            "choice_set-TOTAL_FORMS": "hej",
            "choice_set-INITIAL_FORMS": 0,
            
            "choice_set-0-choice_text": "hi",
                   
        }

        response = self.client.post(reverse("polls:create"), data=payload_data,)

        self.assertEqual(Question.objects.count(), 0)
        self.assertEqual(Choice.objects.count(), 0)

    def test_non_post_request(self):
        """ 
        When getting the create page
        Then it should respond with status code 200
        """
        response = self.client.get(reverse("polls:create"))
        self.assertEqual(response.status_code, 200)

class VoteTests(TestCase):
    """ Testing Voting on a Question """

    def test_vote_increments_votes(self):
        """ 
        When voting on a choice
        And that choice is connected to a question
        Then the 'votes' field for that choice for that question should be 1
        """

        question = Question.objects.create(
           question_text="Test question",
           pub_date=timezone.now(),
       )

        choice = Choice.objects.create(
           question=question,
           choice_text="Choice 1",
           votes=0,
       )

        payload_data = {
            "choice": choice.id,
                   
        }

        response = self.client.post(
           reverse("polls:vote", args=(question.id,)),
           data=payload_data

       )

        choice.refresh_from_db()

        self.assertEqual(choice.votes, 1)
        
        self.assertRedirects(
                response,
                reverse("polls:results", args=(question.id,))
            )

    def test_vote_without_choice(self):
        """ 
        When attempting to vote
        But no choice is selected
        Then a message should be displayed
        """

        question = Question.objects.create(
            question_text="Test question",
            pub_date=timezone.now(),
        )

        response = self.client.post(
            reverse("polls:vote", args=(question.id,)),
            data={},
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "select a choice.",
        )

class BarPieTests(TestCase):
    """ Testing Bar Pie """
    def test_piechart(self):
        """ 
        When on the Pie Chart page
        Then the status code should be 200
        """
        response = self.client.get(reverse("polls:piechart_test"))
        self.assertEqual(response.status_code, 200)

class BarChartTests(TestCase):
    """ Testing Bar Chart """
    def test_barchart(self):
        """ 
        When on the Bar Chart page
        Then the status code should be 200
        """
        response = self.client.get(reverse("polls:barchart_test"))
        self.assertEqual(response.status_code, 200)
        #self.assertEqual(response)


#request database access
#decorator to the whole test class: pytest.mark.django_db
@pytest.mark.django_db
class ModelsTests(TestCase):
    """ Testing Models """
    def test_str_question(self):
        """ 
        When calling the question string method
        Then no errors should occur
        """
        question = Question.objects.create(
            question_text="Test question",
                pub_date=timezone.now(),)
        question.__str__()

    def test_str_choice(self):
        """ 
        When calling the choice string method
        Then no errors should occur
        """
        question = Question.objects.create(
            question_text="Test question",
                pub_date=timezone.now(),)
        choice = Choice.objects.create(
            question=question,
                choice_text="Choice 1",
                    votes=0,
        )
        choice.__str__()

    def test_str_person(self):
        """ 
        When calling the person string method
        Then no errors should occur
        """
        person = Person.objects.create(
            person_name="Freya",
            age=25,
        )
        print(person)


class CeleryTests(TestCase):
    """ Testing Celery """
    def test_debug_task(self):
        """ 
        When calling debug_task method
        Then it should run without errors
        """
        debug_task()

class ExportExcelTests(TestCase):
     """ Testing Export of Excel File """
     def test_export_excel_returns_correct_data(self):
        """ 
        When triggering export_excel method
        Then the data (the content) within the excel file should match the actual data
        """
        
        question = Question.objects.create(
            question_text="Test question",
            pub_date=timezone.now(),
        )

        choice1 = Choice.objects.create(
            question=question,
            choice_text="A",
            votes=3,
        )

        choice2 = Choice.objects.create(
            question=question,
            choice_text="B",
            votes=7,
        )

        response = self.client.get(
            reverse("polls:export_excel", args=(question.id,))
        )

        book = xlrd.open_workbook(file_contents=response.content)
        sheet = book.sheet_by_index(0)

        # Check question title
        self.assertEqual(sheet.cell_value(0, 0), "Question: Test question")

        # Check headers
        self.assertEqual(sheet.cell_value(2, 0), "Choice")
        self.assertEqual(sheet.cell_value(2, 1), "Votes")

        # Check data rows
        self.assertEqual(sheet.cell_value(3, 0), "A")
        self.assertEqual(sheet.cell_value(3, 1), 3)

        self.assertEqual(sheet.cell_value(4, 0), "B")
        self.assertEqual(sheet.cell_value(4, 1), 7)


        # def save_xl(response):
        #     with open(f'question_{question.id}.xls', 'wb') as file:
        #         file.write(response.content)
        #         filename = f'question_{question.id}.xls'
        #         print(filename)
        #         book = xlrd.open_workbook(filename)
        #         return file 

        
        # excel_file = save_xl(response)

        #self.assertEqual(response, excel_file)
    

        #load excel file with python
        
        #book = xlrd.open_workbook("question_{question.id}.xls")
        
        #print(os.getcwd()+"\\"+excel_file)

        




    #  def test_export_excel_returns_file(self):
    #     """ 
    #     When triggering export_excel method
    #     Then it should return the correct response type
    #     And the content type should be an Excel file
    #     And have the correct download header
    #     """

    #     question = Question.objects.create(
    #         question_text="Test question",
    #         pub_date=timezone.now(),
    #     )

    #     choice1 = Choice.objects.create(
    #         question=question,
    #         choice_text="A",
    #         votes=3,
    #     )

    #     choice2 = Choice.objects.create(
    #         question=question,
    #         choice_text="B",
    #         votes=7,
    #     )

    #     response = self.client.get(
    #         reverse("polls:export_excel", args=(question.id,))
    #     )

    #     # 1. correct response type
    #     self.assertEqual(response.status_code, 200)

    #     # 2. correct content type (Excel file)
    #     self.assertEqual(
    #         response["Content-Type"],
    #         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    #     )

    #     # 3. correct download header
    #     self.assertIn(
    #         f"question_{question.id}.xlsx",
    #         response["Content-Disposition"],
    #     )
         

class SearchTests(TestCase):
    """ Testing Searching for Questions """
    def test_search_question_list(self):
        """ 
        When searching for a question by 3 or more characters
        Then it should return a list of questions, containing that sequence of characters
        """

        #need new question objects for the test
        question = Question.objects.create(
           question_text="Test question",
           pub_date=timezone.now(),
       )
        
        payload_data = {
            "search": "que",
            "order": "1"
        }

        response = self.client.post(
           reverse("polls:search"),
           data=payload_data
       )
        
        self.assertQuerySetEqual(response.context["question_list"], [question]),
    
    def test_search_question_list_reverse_order(self):
        """ 
        When searching for a question by 3 or more characters
        And 'reverse order' is selected
        Then it should return the question list in reverse alphabetical order
        """
        #need new question objects for the test
        question = Question.objects.create(
           question_text="Test question",
           pub_date=timezone.now(),
       )
        
        question2 = Question.objects.create(
           question_text="ATest question",
           pub_date=timezone.now(),
       )
        
        question3 = Question.objects.create(
           question_text="BTest question",
           pub_date=timezone.now(),
       )
        
        question_list = Question.objects.all()
           
        
        reversed_question_list = question_list.order_by("question_text").reverse()
        
        payload_data = {
            "search": "que",
            "order": "2"
        }

        response = self.client.post(
           reverse("polls:search"),
           data=payload_data
       )
        
        print(list(response.context["question_list"]))
        print(list(reversed_question_list))
        
        self.assertQuerySetEqual(response.context["question_list"], reversed_question_list)

    
    def test_search_question_list_random_order(self):
        """ 
        When searching for a question by 3 or more characters
        And 'random order' is selected
        Then it should return the question list in random alphabetical order
        """
        #need new question objects for the test
        question = Question.objects.create(
           question_text="Test question",
           pub_date=timezone.now(),
       )
        
        question2 = Question.objects.create(
           question_text="BTest question",
           pub_date=timezone.now(),
       )
        
        question3 = Question.objects.create(
           question_text="ATest question",
           pub_date=timezone.now(),
       )
        
        #question_list = Question.objects.all()
        
        payload_data = {
            "search": "que",
            "order": "3"
        }

        response = self.client.post(
           reverse("polls:search"),
           data=payload_data
       )
        
        result = set(response.context["question_list"])

        expected = {question, question2, question3}

        self.assertEqual(result, expected)
        

    def test_search_question_list_with_another_option(self):
        """ 
        When searching for a question by 3 or more characters
        And a value for 'order' with no logic attached to it is selected
        It should run without errors
        """
        #need new question objects for the test
        question = Question.objects.create(
           question_text="Test question",
           pub_date=timezone.now(),
       )
        
        payload_data = {
            "search": "que",
            "order": "4"
        }

        response = self.client.post(
           reverse("polls:search"),
           data=payload_data
       )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "No polls"),

    
    def test_before_searching(self):
        """ 
        When entering the search page
        Then the SearchForm() should be present
        """

        form = SearchForm()

        response = self.client.get(
           reverse("polls:search"),
       )        
        
        self.assertContains(
            response,
            "Search"),

    def test_search_question_list_empty_string(self):
        """ 
        When searching for a question with an empty string
        Then a validation error should be thrown
        """
        payload_data = {
            "search": "",       
        }

        response = self.client.post(
           reverse("polls:search"),
           data=payload_data
       )
        
        self.assertContains(
            response,
            "Empty string"),

    def test_search_question_list_two_characters(self):
        """ 
        When searching for a question less than three characters
        Then a validation error should be thrown
        """

        payload_data = {
            "search": "qu",       
        }

        response = self.client.post(
           reverse("polls:search"),
           data=payload_data
       )
        
        self.assertContains(
            response,
            "Enter more characters in your search term"),
