from polls.models import Person, Question

from celery import shared_task

@shared_task
def add(x, y):
    return x + y

@shared_task
def mul(x, y):
    return x * y

@shared_task
def xsum(numbers):
    return sum(numbers)

@shared_task
def create_person(person_name, age):
    person = Person.objects.create(
        person_name=person_name,
        age=age
    )

    return person.id

@shared_task
def count_persons():
    return Person.objects.count()

@shared_task
def rename_person(person_id, new_name):
    person = Person.objects.get(id=person_id)
    person.person_name = new_name
    person.save()

@shared_task
def print_questions():
    questions = Question.objects.all()

    #for every question print each question

    for question in questions:
        print("Question id " + str(question.id) + " - " + question.question_text)

        choices = question.choice_set.all()

        for choice in choices:
            print("    Option " + str(choice.id) + ": " + choice.choice_text + " - voted for " + str(choice.votes) + "times")
  

    
    
