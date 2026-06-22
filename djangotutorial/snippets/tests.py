import pytest

from django.test import TestCase

from django.urls import reverse

from .models import Snippet


class SnippetTests(TestCase):
    """ Testing Snippets """
    def test_snippet_list_get(self):
        """ 
        When requesting a list of snippets
        Then the snippets should be returned with serializer
        """

        snippet = Snippet.objects.create(
           code="print(123)",
       )

        response = self.client.get(
           reverse("snippets:index"),
       )
        
        self.assertEqual(response.status_code, 200)

    def test_snippet_list_post(self):
        """ 
        When requesting a list of snippets
        Then the snippets should be returned with serializer
        """

        payload_data = {
            "id": 1,
            "title": "",
            "code": "foo = \"bar\"\n",
            "linenos": False,
            "language": "python",
            "style": "friendly"
        }


        response = self.client.post(
           reverse("snippets:index"), data=payload_data,
       )
        
        self.assertEqual(response.status_code, 201)

       
       
