from django import forms

from .models import Task


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'notes', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'What needs to get done?'}),
            'notes': forms.Textarea(attrs={'rows': 4, 'placeholder': 'A few helpful details…'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }
        help_texts = {
            'notes': 'Optional · up to 2,000 characters.',
            'due_date': 'Optional · choose a day to aim for.',
        }
