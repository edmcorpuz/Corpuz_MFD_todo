from datetime import timedelta

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import TaskForm
from .models import Task


class TaskTests(TestCase):
    def setUp(self):
        self.task = Task.objects.create(title='Finish the Django exercise', notes='Push to GitHub')

    def url(self, action):
        return reverse(f'todo_list:{action}', args=[self.task.pk])

    def test_list_and_counts(self):
        Task.objects.create(title='Already done', completed=True)
        response = self.client.get(reverse('todo_list:list'))
        self.assertContains(response, self.task.title)
        self.assertEqual(response.context['counts'], {'total': 2, 'active': 1, 'completed': 1})

    def test_empty_state(self):
        Task.objects.all().delete()
        self.assertContains(self.client.get('/'), 'A fresh start.')

    def test_filters(self):
        done = Task.objects.create(title='Already done', completed=True)
        for status, expected in [('active', [self.task]), ('completed', [done])]:
            with self.subTest(status=status):
                response = self.client.get('/', {'status': status})
                self.assertEqual(list(response.context['tasks']), expected)

    def test_invalid_filter_defaults_to_all(self):
        response = self.client.get('/', {'status': 'invalid'})
        self.assertEqual(response.context['status'], 'all')

    def test_create(self):
        response = self.client.post(reverse('todo_list:create'), {
            'title': '  New task  ', 'notes': 'Details', 'due_date': '2027-01-15',
        })
        self.assertRedirects(response, '/')
        task = Task.objects.get(title='New task')
        self.assertEqual(str(task.due_date), '2027-01-15')
        self.assertFalse(task.completed)

    def test_blank_title_rejected(self):
        for title in ['', '   ']:
            with self.subTest(title=title):
                response = self.client.post(reverse('todo_list:create'), {'title': title})
                self.assertFormError(response.context['form'], 'title', 'This field is required.')
        self.assertEqual(Task.objects.count(), 1)

    def test_invalid_dates_and_field_lengths_rejected(self):
        for data in [
            {'title': 'x' * 201},
            {'title': 'Task', 'notes': 'x' * 2001},
            {'title': 'Task', 'due_date': 'not-a-date'},
        ]:
            with self.subTest(field=list(data)[-1]):
                self.assertFalse(TaskForm(data).is_valid())

    def test_optional_fields(self):
        form = TaskForm({'title': 'Just a title'})
        self.assertTrue(form.is_valid())
        self.assertIsNone(form.save().due_date)

    def test_edit(self):
        response = self.client.post(self.url('edit'), {'title': 'Updated', 'notes': 'Changed'})
        self.assertRedirects(response, '/')
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Updated')
        self.assertEqual(self.task.notes, 'Changed')

    def test_invalid_edit_preserves_task(self):
        self.client.post(self.url('edit'), {'title': ''})
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Finish the Django exercise')

    def test_toggle_and_reopen(self):
        for expected in [True, False]:
            response = self.client.post(self.url('toggle'), {'status': 'active'})
            self.assertRedirects(response, '/?status=active')
            self.task.refresh_from_db()
            self.assertEqual(self.task.completed, expected)

    def test_toggle_get_disallowed(self):
        self.assertEqual(self.client.get(self.url('toggle')).status_code, 405)
        self.task.refresh_from_db()
        self.assertFalse(self.task.completed)

    def test_toggle_redirect_is_local(self):
        response = self.client.post(self.url('toggle'), {'status': 'https://example.com'})
        self.assertRedirects(response, '/?status=all')

    def test_delete_requires_confirmation_and_post(self):
        response = self.client.get(self.url('delete'))
        self.assertContains(response, 'Keep task')
        self.assertTrue(Task.objects.filter(pk=self.task.pk).exists())
        self.assertRedirects(self.client.post(self.url('delete')), '/')
        self.assertFalse(Task.objects.filter(pk=self.task.pk).exists())

    def test_missing_tasks_return_404(self):
        for action in ['edit', 'delete', 'toggle']:
            with self.subTest(action=action):
                self.assertEqual(self.client.post(reverse(f'todo_list:{action}', args=[9999])).status_code, 404)

    def test_csrf_required_for_mutations(self):
        client = Client(enforce_csrf_checks=True)
        for url in [reverse('todo_list:create'), self.url('edit'), self.url('toggle'), self.url('delete')]:
            with self.subTest(url=url):
                self.assertEqual(client.post(url, {'title': 'Blocked'}).status_code, 403)
        self.assertEqual(Task.objects.count(), 1)
        self.task.refresh_from_db()
        self.assertFalse(self.task.completed)

    def test_form_pages_and_date_prefill(self):
        self.task.due_date = timezone.localdate()
        self.task.save()
        self.assertContains(self.client.get(reverse('todo_list:create')), 'Create task')
        self.assertContains(self.client.get(self.url('edit')), self.task.due_date.isoformat())

    def test_user_content_is_escaped(self):
        self.task.title = '<script>alert(1)</script>'
        self.task.notes = '<img src=x onerror=alert(1)>'
        self.task.save()
        response = self.client.get('/')
        self.assertContains(response, '&lt;script&gt;')
        self.assertNotContains(response, '<script>')
        self.assertNotContains(response, '<img src=x')

    def test_overdue_only_for_unfinished_past_tasks(self):
        for days, completed, expected in [(-1, False, True), (0, False, False), (1, False, False), (-1, True, False)]:
            with self.subTest(days=days, completed=completed):
                self.task.due_date = timezone.localdate() + timedelta(days=days)
                self.task.completed = completed
                self.assertEqual(self.task.is_overdue, expected)

    def test_string_representation(self):
        self.assertEqual(str(self.task), self.task.title)
