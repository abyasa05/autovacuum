from django.shortcuts import render
from .models import VacuumHistory

def history_list(request):
    histories = VacuumHistory.objects.all()
    return render(request, 'history/history.html', {'histories': histories})
