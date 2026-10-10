from django.contrib import messages
from django.db.models import BooleanField, Case, Count, Q, Value, When
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import TaskForm
from .models import Task


@require_GET
def task_list(request):
    status = request.GET.get('status', 'all')
    if status not in {'all', 'active', 'completed'}:
        status = 'all'
    tasks = Task.objects.all()
    counts = tasks.aggregate(total=Count('pk'), completed=Count('pk', filter=Q(completed=True)))
    counts['active'] = counts['total'] - counts['completed']
    if status != 'all':
        tasks = tasks.filter(completed=(status == 'completed'))
    return render(request, 'todo_list/task_list.html', {
        'tasks': tasks,
        'status': status,
        'counts': counts,
    })


@require_http_methods(['GET', 'POST'])
def task_create(request):
    form = TaskForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Task added. One step closer!')
        return redirect('todo_list:list')
    return render(request, 'todo_list/task_form.html', {'form': form, 'editing': False})


@require_http_methods(['GET', 'POST'])
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk)
    form = TaskForm(request.POST if request.method == 'POST' else None, instance=task)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Task updated.')
        return redirect('todo_list:list')
    return render(request, 'todo_list/task_form.html', {'form': form, 'editing': True})


@require_POST
def task_toggle(request, pk):
    task = get_object_or_404(Task, pk=pk)
    # Flip in the database so concurrent requests cannot overwrite each other.
    Task.objects.filter(pk=task.pk).update(completed=Case(
        When(completed=True, then=Value(False)),
        default=Value(True),
        output_field=BooleanField(),
    ))
    messages.success(request, 'Task status updated.')
    status = request.POST.get('status', 'all')
    if status not in {'all', 'active', 'completed'}:
        status = 'all'
    return redirect(f"{reverse('todo_list:list')}?status={status}")


@require_http_methods(['GET', 'POST'])
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted.')
        return redirect('todo_list:list')
    return render(request, 'todo_list/task_confirm_delete.html', {'task': task})
