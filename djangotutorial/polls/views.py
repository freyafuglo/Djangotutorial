from django.db.models import F
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.utils import timezone
from django.forms import inlineformset_factory

from .models import Choice, Question


class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        """
         Return the last five published questions (not including those set to be
         published in the future).
        """
        return Question.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")[:5]


class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"
    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())


class ResultsView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"
   

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        question = self.object
        choices = question.choice_set.all()

        labels = [choice.choice_text for choice in choices]
        data = [choice.votes for choice in choices]

        context["labels"] = labels
        context["data"] = data

        return context
    

def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "You didn't select a choice.",
            },
        )
    else:
        selected_choice.votes = F("votes") + 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))
    
ChoiceFormSet = inlineformset_factory(
    Question,
    Choice,
    fields=("choice_text",),
    extra=3,  # number of empty choice fields shown
)
class CreateView(generic.CreateView):
    model = Question
    fields = ["question_text"]
    template_name = "polls/create.html"
    success_url = reverse_lazy("polls:index")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context["formset"] = ChoiceFormSet(self.request.POST)
        else:
            context["formset"] = ChoiceFormSet()

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["formset"]

        if formset.is_valid():
            self.object = form.save(commit=False)
            self.object.pub_date = timezone.now()
            self.object.save()

            formset.instance = self.object  # link choices to question
            formset.save()

            return super().form_valid(form)

        else:
            return self.form_invalid(form)
        
def piechart_test(request):
    data = [5, 15, 25]
    labels = ['Apples', 'Bananas', 'Oranges']

    return render(request, "polls/piechart_test.html", {
        'data': data,
        'labels': labels
    })

