"""Модуль тестирования маршрутов."""
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):
    """Класс для тестирования маршрутов."""

    @classmethod
    def setUpTestData(cls):
        """КлассМетод для подготовки фикстур."""
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Читатель простой')
        cls.notes = Note.objects.create(
            title='Заголовок', text='Текст', slug='aaa', author=cls.author)

    def test_pages_availability(self):
        """Тест: Главная страница доступна анонимным пользователям.
        Страницы регистрации пользователей, входа в учётную запись и
        выхода из неё доступны анонимным пользователям.
        """
        urls = (
            ('notes:home', None),
            ('users:login', None),
            ('users:logout', None),
            ('users:signup', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_note_and_edit_and_delete(self):
        """Тест: Страницы отдельной заметки, удаления и редактирования заметки
        доступны только автору заметки.
        Если на эти страницы попытается зайти другой пользователь —
        вернётся ошибка 404.
        """
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in ('notes:detail', 'notes:edit', 'notes:delete'):
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.notes.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        """Тест: При попытке перейти на страницу списка заметок,
        страницу успешного добавления записи, страницу добавления заметки,
        отдельной заметки, редактирования или удаления заметки
        анонимный пользователь перенаправляется на страницу логина.
        """
        login_url = reverse('users:login')
        urls = (
            ('notes:detail', (self.notes.slug,)),
            ('notes:edit', (self.notes.slug,)),
            ('notes:delete', (self.notes.slug,)),
            ('notes:add', None),
            ('notes:list', None),
            ('notes:success', None)
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)

    def test_availability_for_notes_and_add_and_done(self):
        """Тест: Аутентифицированному пользователю доступна страница
        со списком заметок notes/, страница успешного добавления заметки done/,
        страница добавления новой заметки add/.
        """
        user = self.author
        self.client.force_login(user)
        for name in ('notes:list', 'notes:add', 'notes:success'):
            with self.subTest(user=user, name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
