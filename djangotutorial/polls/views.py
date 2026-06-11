import xlsxwriter
from xlwt import Workbook
from io import BytesIO
from django.db.models import F
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.utils import timezone
from django.forms import inlineformset_factory
from django import forms
from django.core.exceptions import ValidationError

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
    
def export_excel(request, question_id):
        
        question = get_object_or_404(Question, pk=question_id)

        response = HttpResponse(
        content_type="application/vnd.ms-excel"
)

        response["Content-Disposition"] = (
        f'attachment; filename="question_{question.id}.xls"'
    )

        output = BytesIO()

        #Create an object of the workbook
        workbook = Workbook()

        #Add sheet in workbook
        sheet = workbook.add_sheet("Question Data")

        sheet.write(0, 0, f"Question: {question.question_text}")

        sheet.write(2, 0, "Choice")
        sheet.write(2, 1, "Votes")

        for row, choice in enumerate(question.choice_set.all(), start=3):
             sheet.write(row, 0, choice.choice_text)
             sheet.write(row, 1, choice.votes)

        workbook.save(output)

        response.write(output.getvalue())


        #Now save the excel
        #save_location = "path/to/your/working/directory/result.xls"
        #excel.save(save_location)

        return response

        # question = get_object_or_404(Question, pk=question_id)

        # #Tells the browser that the data being sent is an Excel (.xlsx) file
        # response = HttpResponse(
        #     content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        # )

        # #Tells the browser to download this file instead of opening it in the browser, and name it this filename
        # response["Content-Disposition"] = (
        #     f'attachment; filename="question_{question.id}.xlsx"'
        # )

        # workbook = xlsxwriter.Workbook(response)
        # worksheet = workbook.add_worksheet()

        # worksheet.write(0, 0, f"Question: {question.question_text}")

        # worksheet.write(2, 0, "Choice")
        # worksheet.write(2, 1, "Votes")

        # for row, choice in enumerate(question.choice_set.all(), start=3):
        #     worksheet.write(row, 0, choice.choice_text)
        #     worksheet.write(row, 1, choice.votes)

        # workbook.close()

        # return response
    

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
    extra=1,  # number of empty choice fields shown
    can_delete=False,
)
class CreateView(generic.CreateView):
    model = Question
    fields = ["question_text"]
    template_name = "polls/create.html"
    success_url = reverse_lazy("polls:index")
    print("HERE")

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
            print("VALID")
            self.object = form.save(commit=False)
            self.object.pub_date = timezone.now()
            self.object.save()

            formset.instance = self.object  # link choices to question
            formset.save()

            return super().form_valid(form)

        else:
            print("INVALID")
            print(formset.errors)
            #print(dir(formset))
            return self.form_invalid(form)
        
    


class SearchForm(forms.Form):
    #In HTML, it becomes <input type="text" name="search">
    search = forms.CharField(
        label="Search",
        max_length=100,
        required=False
    )

    ORDER_CHOICES = [
        ('1', 'Alphabetical order'),
        ('2', 'Reverse alphabetical order'),
        ('3', 'Nothing')
    ]
    
    order = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=ORDER_CHOICES, 
    )

    #field name is search, therefore the method name becomes clean_ followed by that field name
    def clean_search(self):
        data = self.cleaned_data["search"]

        if not data:
            raise ValidationError("Empty string")
        
        if len(data) < 3:
            raise ValidationError("Enter more characters in your search term")

        # Always return a value to use as the new cleaned data, even if
        # this method didn't change it.
        return data

def get_question_list(request):

    if request.method == "POST":
        form = SearchForm(request.POST)

        if form.is_valid():
            search_term = form.cleaned_data["search"]
          

            question_list = Question.objects.filter(
                question_text__icontains=search_term
            )

            
            if form.cleaned_data["order"] == "1":
                sorted_list = question_list.order_by("question_text")
                print("first")
            elif form.cleaned_data["order"] == "2":
                sorted_list = question_list.order_by("question_text").reverse()
                print("second")
            else:
                sorted_list = []

        
            print("anything")

            return render(
                request,
                "polls/search_list.html",
                {"question_list": sorted_list},
            )

    else:
        form = SearchForm()

    return render(
        request,
        "polls/search.html",
        {"form": form},
    )
        
# class SearchView(generic.ListView):
#     model = Question
#     fields = ["question_text"]
#     template_name = "polls/search.html"
#     success_url = reverse_lazy("polls:index")

   
    
        
    # model = Question
    # template_name = "polls/search.html"
    # context_object_name = "latest_question_list"
    # def get_queryset(self):
    #     return Question.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")

        
def piechart_test(request):
    data = [5, 15, 25]
    labels = ['Apples', 'Bananas', 'Oranges']

    return render(request, "polls/piechart_test.html", {
        'data': data,
        'labels': labels
    })

def barchart_test(request):
    data = [5, 15, 25]
    labels = ['Apples', 'Bananas', 'Oranges']

    return render(request, "polls/barchart_test.html", {
        'data': data,
        'labels': labels
    })

