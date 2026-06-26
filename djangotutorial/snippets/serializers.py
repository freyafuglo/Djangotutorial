from rest_framework import serializers
from snippets.models import Snippet, LANGUAGE_CHOICES, STYLE_CHOICES


from rest_framework import serializers
from snippets.models import Snippet
from django.contrib.auth.models import User


class SnippetSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="snippets:snippet-detail"
    )

    owner = serializers.ReadOnlyField(source="owner.username")

    highlight = serializers.HyperlinkedIdentityField(
        view_name="snippets:snippet-highlight",
        format="html",
    )

    class Meta:
        model = Snippet
        fields = [
            "url",
            "id",
            "highlight",
            "owner",
            "title",
            "code",
            "linenos",
            "language",
            "style",
        ]
        

class UserSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="snippets:user-detail"
    )

    snippets = serializers.HyperlinkedRelatedField(
        many=True,
        view_name="snippets:snippet-detail",
        read_only=True,
    )

    class Meta:
        model = User
        fields = ["url", "id", "username", "snippets"]