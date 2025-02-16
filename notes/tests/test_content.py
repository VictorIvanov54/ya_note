"""Модуль тестирования контента."""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()


class TestContent(TestCase):
    """Класс для тестирования контента."""

    @classmethod
    def setUpTestData(cls):
        """КлассМетод для подготовки фикстур."""
        cls.author = User.objects.create(username='Автор')
        cls.not_author = User.objects.create(username='Не Автор')
        cls.note = Note.objects.create(
            title='Заголовок', text='Текст.', slug='aaa', author=cls.author
        )

    def test_authorized_author_has_form(self):
        """Тест: На страницы создания и редактирования заметки
        передаются формы.
        """
        urls = (
            ('notes:edit', (self.note.slug,)),
            ('notes:add', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                self.client.force_login(self.author)
                response = self.client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)

    def test_note_in_list_for_author(self):
        """Тест: Отдельная заметка передаётся на страницу со списком заметок
        в списке object_list в словаре context.
        """
        url = reverse('notes:list')
        self.client.force_login(self.author)
        response = self.client.get(url)
        self.assertIn(self.note, response.context['object_list'])

    def test_note_not_in_list_for_not_author(self):
        """Тест: В список заметок одного пользователя не попадают
        заметки другого пользователя.
        """
        url = reverse('notes:list')
        self.client.force_login(self.not_author)
        response = self.client.get(url)
        self.assertNotIn(self.note, response.context['object_list'])
