from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import VacuumHistory

@login_required
def history_list(request):
    histories = VacuumHistory.objects.all()
    return render(request, 'history/history.html', {'histories': histories})
