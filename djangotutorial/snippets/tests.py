import pytest

from django.test import TestCase

from django.urls import reverse

from .models import Snippet
from django.contrib.auth.models import User


class SnippetTests(TestCase):
    """ Testing Snippets """
    def test_snippet_list_get(self):
        """ 
        When requesting a list of snippets
        Then the snippets should be returned with serializer
        """

        user = User.objects.create_user(
        username="admin",
        password="secret"
    )

        snippet = Snippet.objects.create(
        owner=user,
        code="print(123)",
       )

        response = self.client.get(
           reverse("snippets:index"),
       )
        
        self.assertEqual(response.status_code, 200)

    def test_snippet_list_post(self):
        """ 
        When making post request for a snippet object
        And the fields are correct
        Then the new snippet should be successfully created
        """

        owner = User.objects.create_user(
        username="admin",
        password="secret"
    )

        self.client.force_login(owner)

        payload_data = {
            "id": 1,
            "title": "",
            "code": "foo = \"bar\"\n",
            "linenos": False,
            "language": "python",
            "style": "friendly"
        }


        response = self.client.post(
           reverse("snippets:index"), data=payload_data
       )
        
        print("status:", response.status_code)
        print("content:", response.content.decode())
        
        self.assertEqual(response.status_code, 201)

    def test_snippet_list_post_errorneously(self):
        """ 
        When making post request for a snippet object
        And not all the fields are correct
        Then an error should be thrown
        """

        payload_data = {
            #"owner": "admin",
            "id": 1,
            "title": "",
            "code": "foo = \"bar\"\n",
            "linenos": "hej",
            "language": "python",
            "style": "friendly"
        }

        response = self.client.post(
           reverse("snippets:index"), data=payload_data,
       )
        
        self.assertEqual(response.status_code, 400)

    def test_snippet_detail_get(self):
        """ 
        When making get request for an existing snippet object
        And the given primary key is valid
        Then a serialized snippet object should be returned
        """


        user = User.objects.create_user(
        username="admin",
        password="secret"
    )

        snippet = Snippet.objects.create(
        owner=user,
        code="print(123)"
    )
        response = self.client.get(
           reverse("snippets:detail", kwargs={"pk": snippet.pk}),
       )
        
        self.assertEqual(response.status_code, 200)

    def test_snippet_detail_get_errorneously(self):
        """ 
        When making get request for a snippet object
        And the given primary key is invalid
        Then an error should be returned
        """

        user = User.objects.create_user(
        username="admin",
        password="secret"
     )

        snippet = Snippet.objects.create(
        owner=user,
        code="print(123)"
    )
        response = self.client.get(
           reverse("snippets:detail", kwargs={"pk": 2}),
       )
        
        self.assertEqual(response.status_code, 404)

    def test_snippet_detail_put(self):
        """ 
        When updating an existing snippet
        Then the snippet should be updated successfully
        """

        user = User.objects.create_user(
        username="admin",
        password="secret"
    )
        

        snippet = Snippet.objects.create(
        owner=user,
        code="print(123)"
    )
        
        payload_data = {
            "owner": "admin",
            "title": "",
            "code": "foo = \"bar\"\n",
            "language": "python",
            "style": "friendly"
        }

        response = self.client.put(
           reverse("snippets:detail", kwargs={"pk": snippet.pk}), data=payload_data, content_type="application/json",)
       
        
        self.assertEqual(response.status_code, 200)

    def test_snippet_detail_put_errorneously(self):
        """
        Given an existing snippet
        When invalid data is submitted in a PUT request
        Then a 400 Bad Request response should be returned
        """

        user = User.objects.create_user(
        username="admin",
        password="secret"
    )


        snippet = Snippet.objects.create(
        owner=user,
        code="print(123)"
    )
        
        payload_data = {
            "title": "",
            "code": "foo = \"bar\"\n",
            "language": "dk",
            "style": "friendly"
        }

        response = self.client.put(
           reverse("snippets:detail", kwargs={"pk": snippet.pk}), data=payload_data, content_type="application/json",)
              
        self.assertEqual(response.status_code, 400)

    def test_snippet_detail_delete(self):
        """
        Given an existing snippet
        When a DELETE request is made
        Then the snippet should be deleted and a 204 response returned
        """

        user = User.objects.create_user(
        username="admin",
        password="secret"
    )

        snippet = Snippet.objects.create(
        owner=user,
        code="print(123)"
    )

        response = self.client.delete(
            reverse("snippets:detail", kwargs={"pk": snippet.pk})
        )

        self.assertEqual(response.status_code, 204)

       
       
