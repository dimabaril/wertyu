from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post, User
from .utils import get_reverse_url


class PostUrlTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='Writer')
        cls.user_not_author = User.objects.create_user(username='Not_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовый длинююююющий пост',
            group=cls.group
        )

        # name template arg
        cls.index = ('posts:index', 'posts/index.html', None)
        cls.group_list = ('posts:group_list',
                          'posts/group_list.html', [cls.group.slug])
        cls.profile = ('posts:profile', 'posts/profile.html',
                       [cls.user_author.username])
        cls.detail = ('posts:post_detail', 'posts/post_detail.html',
                      [cls.post.id])
        cls.edit = ('posts:post_edit', 'posts/post_create.html',
                    [cls.post.id])
        cls.create = ('posts:post_create', 'posts/post_create.html', None)
        cls.unexisting = ('/unexisting_page/', 'core/404.html', None)
        cls.login = ('users:login', 'users/login.html', None)
        cls.comment = ('posts:add_comment', None, [cls.post.id])

        # Проверка отклика не авторизованным юзером.
        cls.unauth_client_address_http_ok = (
            cls.index, cls.group_list, cls.profile, cls.detail
        )

        # Проверка отклика не авторизованным юзером с редиректом.
        cls.unauth_client_address_http_found = (
            cls.edit, cls.create,
        )

        # Проверка отклика авторизованным юзером.
        cls.auth_client_address_http_ok = (
            *cls.unauth_client_address_http_ok,
            *cls.unauth_client_address_http_found)

        # Проверка соответствия шаблонов авторизованным юзером.
        cls.auth_url_templates = (
            cls.index, cls.group_list, cls.profile, cls.detail, cls.edit,
            cls.create
        )

        # Проверка соответствия шаблонов не авторизованным юзером.
        cls.unauth_url_templates = (
            cls.index, cls.group_list, cls.profile, cls.detail
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_author = Client()
        self.authorized_author.force_login(self.user_author)
        self.authorized_not_author = Client()
        self.authorized_not_author.force_login(self.user_not_author)

    def test_auth_client_address_http_ok(self):
        """Проверка отклика авторизованным юзером."""
        for url_tuple in self.auth_client_address_http_ok:
            reversed_name = get_reverse_url(url_tuple)
            with self.subTest(reversed_name=reversed_name):
                response = self.authorized_author.get(reversed_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unauth_client_address_http_ok(self):
        """Проверка отклика не авторизованным юзером."""
        for url_tuple in self.unauth_client_address_http_ok:
            reversed_name = get_reverse_url(url_tuple)
            with self.subTest(reversed_name=reversed_name):
                response = self.guest_client.get(reversed_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unauth_client_address_http_found(self):
        """Проверка отклика не авторизованным юзером с редиректом."""
        for url_tuple in self.unauth_client_address_http_found:
            reversed_name = get_reverse_url(url_tuple)
            with self.subTest(reversed_name=reversed_name):
                response = self.guest_client.get(reversed_name)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_auth_adress_templates(self):
        """Проверка соответствия шаблонов авторизованным юзером."""
        for url_tuple in self.auth_url_templates:
            reversed_name = get_reverse_url(url_tuple)
            with self.subTest(reversed_name=reversed_name):
                response = self.authorized_author.get(reversed_name)
                self.assertTemplateUsed(response, url_tuple[1])

    def test_unauth_adress_templates(self):
        """Проверка соответствия шаблонов не авторизованным юзером."""
        for url_tuple in self.unauth_url_templates:
            reversed_name = get_reverse_url(url_tuple)
            with self.subTest(reversed_name=reversed_name):
                response = self.guest_client.get(reversed_name)
                self.assertTemplateUsed(response, url_tuple[1])

    def test_unauthorized_redirect_edit_create(self):
        """Проверка редиректа правки/создания поста
        не авторизиванного юзера."""
        url_tuples = (self.edit, self.create)
        for url_tuple in url_tuples:
            reversed_name = get_reverse_url(url_tuple)
            with self.subTest(reversed_name=reversed_name):
                response = self.guest_client.get(reversed_name, follow=True)
                self.assertRedirects(
                    response,
                    get_reverse_url(self.login) + '?next=' + reversed_name)

    def test_not_author_redirect_edit(self):
        """Проверка редиректа правки поста авторизованного,
        но не автора пост."""
        reversed_name = get_reverse_url(self.edit)
        response = self.authorized_not_author.get(reversed_name, follow=True)
        self.assertRedirects(response, get_reverse_url(self.detail))

    def test_unexisting_page_status_code_templates(self):
        """Проверка несуществующей страницы."""
        url = self.unexisting[0]
        response = self.authorized_author.get(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, self.unexisting[1])

    def test_auth_client_comment_http_ok(self):
        """Проверка страницы коммента."""
        response = self.authorized_author.get(get_reverse_url(self.comment))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        response = self.guest_client.get(get_reverse_url(self.comment))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
