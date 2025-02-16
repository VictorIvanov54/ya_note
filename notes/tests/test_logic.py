"""Модуль тестирования логики."""
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):
    """Класс для тестирования создания заметок."""

    NOTE_TEXT = 'Текст заметки'

    @classmethod
    def setUpTestData(cls):
        """КлассМетод для подготовки фикстур."""
        cls.user = User.objects.create(username='Кто-то')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.url = reverse('notes:add')
        cls.url_success = reverse('notes:success')
        cls.form_data = {
            'title':  'Заголовок',
            'text': cls.NOTE_TEXT,
            'slug': 'bbb'
            }

    def test_anonymous_user_cant_create_note(self):
        """Тест: Анонимный пользователь не может создать заметку."""
        self.client.post(self.url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_can_create_note(self):
        """Тест: Залогиненный пользователь может создать заметку."""
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, self.url_success)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        note = Note.objects.get()
        # Проверяем, что все атрибуты заметки совпадают с ожидаемыми.
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.slug, self.form_data['slug'])
        self.assertEqual(note.author, self.user)

    def test_not_unique_slug(self):
        """Тест: Невозможно создать две заметки с одинаковым slug."""
        note = Note.objects.create(
                title='Заголовок',
                text=self.NOTE_TEXT,
                slug='aaa',
                author=self.user
            )
        self.form_data['slug'] = note.slug
        response = self.auth_client.post(self.url, data=self.form_data)
        # Проверяем, что в ответе содержится ошибка формы для поля slug:
        self.assertFormError(
            response, 'form', 'slug', errors=(note.slug + WARNING)
        )
        # Убеждаемся, что количество заметок в базе осталось равным 1:
        assert Note.objects.count() == 1

    def test_empty_slug(self):
        """Тест: Если при создании заметки не заполнен slug,
        то он формируется автоматически.
        """
        self.form_data.pop('slug')
        response = self.auth_client.post(self.url, data=self.form_data)
        # Проверяем, что даже без slug заметка была создана:
        self.assertRedirects(response, self.url_success)
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.get()
        expected_slug = slugify(self.form_data['title'])
        # Проверяем, что slug заметки соответствует ожидаемому:
        self.assertEqual(new_note.slug, expected_slug)


class TestNoteEditDelete(TestCase):
    """Класс для тестирования редактирования и удаления заметок."""

    NOTE_TEXT = 'Текст заметки'
    NEW_NOTE_TEXT = 'Обновлённая заметка'

    @classmethod
    def setUpTestData(cls):
        """КлассМетод для подготовки фикстур."""
        cls.author = User.objects.create(username='Автор заметки')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.note = Note.objects.create(
            title='Заголовок',
            text=cls.NOTE_TEXT,
            slug='aaa',
            author=cls.author
        )
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.url_success = reverse('notes:success')
        cls.form_data = {
            'title':  'Заголовок новый',
            'text': cls.NEW_NOTE_TEXT,
            }

    def test_author_can_delete_note(self):
        """Тест: Авторизованный пользователь может удалять свои заметки."""
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.url_success)
        self.assertEqual(Note.objects.count(), 0)

    def test_user_cant_delete_note_of_another_user(self):
        """Тест: Авторизованный пользователь не может удалять чужие заметки."""
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)

    def test_author_can_edit_note(self):
        """Тест: Авторизованный пользователь может
        редактировать свои заметки.
        """
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.url_success)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)

    def test_user_cant_edit_note_of_another_user(self):
        """Тест: Авторизованный пользователь не может
        редактировать чужие заметки.
        """
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NOTE_TEXT)
