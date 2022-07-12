import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings

from yatube.settings import POSTS_PER_PAGE

from ..models import Comment, Follow, Group, Post, User
from .utils import checking_post_content, get_reverse_url

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class AllTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='Writer')
        cls.user_follower = User.objects.create_user(
            username='Follower')
        cls.user_not_follower = User.objects.create_user(
            username='NotFollower')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.group_1 = Group.objects.create(
            title='Тестовая группа 1',
            slug='test_slug_1',
            description='Тестовое описание 1',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug_2',
            description='Тестовое описание 2',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовый длинююююющий пост',
            group=cls.group,
            image=cls.uploaded
        )
        cls.comment_1 = Comment.objects.create(
            post=cls.post,
            author=cls.user_author,
            text='Тестовый коммент 1',
        )
        cls.comment_2 = Comment.objects.create(
            post=cls.post,
            author=cls.user_author,
            text='Тестовый коммент 2',
        )

        # name template arg
        cls.index = ('posts:index', 'posts/index.html', None)
        cls.group_list = ('posts:group_list',
                          'posts/group_list.html', [cls.group.slug])
        cls.group_list_1 = ('posts:group_list', 'posts/group_list.html',
                            ['test_slug_1'])
        cls.group_list_2 = ('posts:group_list', 'posts/group_list.html',
                            ['test_slug_2'])
        cls.profile = ('posts:profile', 'posts/profile.html',
                       [cls.user_author.username])
        cls.detail = ('posts:post_detail', 'posts/post_detail.html',
                      [cls.post.id])
        cls.edit = ('posts:post_edit', 'posts/post_create.html',
                    [cls.post.id])
        cls.create = ('posts:post_create', 'posts/post_create.html', None)
        cls.follow_index = ('posts:follow_index', 'posts/follow.html', None)
        cls.follow = ('posts:profile_follow', None,
                      [cls.user_author])
        cls.unfollow = ('posts:profile_unfollow', None,
                        [cls.user_author])

    @ classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_author = Client()
        self.authorized_author.force_login(self.user_author)
        self.authorized_follower = Client()
        self.authorized_follower.force_login(
            self.user_follower)
        self.authorized_not_follower = Client()
        self.authorized_not_follower.force_login(
            self.user_not_follower)

    def test_pages_uses_correct_template(self):
        """View использует соответствующий шаблон."""
        page_names_templates_args = (
            self.index, self.group_list, self.profile,
            self.detail, self.edit, self.create)
        for url_tuple in page_names_templates_args:
            reversed_name = get_reverse_url(url_tuple)
            with self.subTest(reversed_name=reversed_name):
                response = self.authorized_author.get(reversed_name)
                self.assertTemplateUsed(response, url_tuple[1])

    def test_page_show_correct_context(self):
        """Шаблон сформирован с правильным контекстом."""
        page_names_templates_args = (
            self.index, self.group_list, self.profile
        )
        for url_tuple in page_names_templates_args:
            reversed_name = get_reverse_url(url_tuple)
            with self.subTest(reversed_name=reversed_name):
                response = self.authorized_author.get(reversed_name)
                post = response.context['page_obj'][-1]
                checking_post_content(
                    self, post,
                    self.post.text, self.user_author.username,
                    self.post.group.id, self.post.image
                )

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_author.get(get_reverse_url(self.detail))
        post = response.context['post']
        posts_count = response.context['posts_count']
        post_comments = response.context['comments']
        checking_post_content(
            self, post,
            self.post.text, self.user_author.username,
            self.post.group.id, self.post.image
        )
        self.assertEqual(list(post_comments),
                         list(Comment.objects.filter(post_id=self.post.id)))
        self.assertEqual(posts_count, Post.objects.count())

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_author.get(get_reverse_url(self.create))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_author.get(get_reverse_url(self.edit))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_exists_in_right_pages(self):
        """Проверяем заход поста в index, в profile,
        в правильную group_list"""
        page_names_templates_args = (
            self.index, self.profile, self.group_list_2,
        )
        for url_tuple in page_names_templates_args:
            reversed_name = get_reverse_url(url_tuple)
            with self.subTest(reversed_name=reversed_name):
                response = self.authorized_author.get(reversed_name)
                post_count_befor_post = len(response.context['page_obj'])
                Post.objects.create(
                    author=self.user_author,
                    text='Тестовый длинююююющий пост',
                    group=self.group_2
                )
                cache.clear()
                response = self.authorized_author.get(reversed_name)
                self.assertEqual(
                    len(response.context['page_obj']),
                    post_count_befor_post + 1
                )

    def test_post_in_right_group(self):
        """Проверяем отсутствие поста в иной group_list"""
        page_names_templates_args = (
            self.group_list_1,
        )
        for url_tuple in page_names_templates_args:
            reversed_name = get_reverse_url(url_tuple)
            with self.subTest(reversed_name=reversed_name):
                response = self.authorized_author.get(reversed_name)
                post_count_befor_post = len(response.context['page_obj'])
                Post.objects.create(
                    author=self.user_author,
                    text='Тестовый длинююююющий пост',
                    group=self.group_2
                )
                cache.clear()
                response = self.authorized_author.get(reversed_name)
                self.assertEqual(
                    len(response.context['page_obj']),
                    post_count_befor_post
                )

    def test_cashe(self):
        """Проверяем кэш"""
        test_post = Post.objects.create(
            author=self.user_author,
            text='Пост для теста кэша',
        )
        content_before_del = self.authorized_author.get(
            get_reverse_url(self.index)).content
        test_post.delete()
        content_after_del = self.authorized_author.get(
            get_reverse_url(self.index)).content
        self.assertEqual(content_before_del, content_after_del)
        cache.clear()
        content_after_del_clear_cache = self.authorized_author.get(
            get_reverse_url(self.index)).content
        self.assertNotEqual(content_before_del, content_after_del_clear_cache)

    def test_following(self):
        """Проверяем подписку"""
        self.assertFalse(Follow.objects.filter(
            user=self.user_follower, author=self.user_author).exists())
        self.authorized_follower.get(get_reverse_url(self.follow))
        self.assertTrue(Follow.objects.filter(
            user=self.user_follower, author=self.user_author).exists())

    def test_unfollowing(self):
        """Проверяем отписку"""
        Follow.objects.create(
            user=self.user_follower, author=self.user_author)
        self.assertTrue(Follow.objects.filter(
            user=self.user_follower, author=self.user_author).exists())
        self.authorized_follower.get(get_reverse_url(self.unfollow))
        self.assertFalse(Follow.objects.filter(
            user=self.user_follower, author=self.user_author).exists())

    def test_follow(self):
        """У фоловера пост есть, у не фоловера нет"""
        Follow.objects.create(user=self.user_follower, author=self.user_author)
        response = self.authorized_follower.get(
            get_reverse_url(self.follow_index))
        follower_posts_count_befor_post = len(response.context['page_obj'])
        response = self.authorized_not_follower.get(
            get_reverse_url(self.follow_index))
        not_follower_posts_count_befor_post = len(response.context['page_obj'])
        Post.objects.create(
            author=self.user_author,
            text='Тестовый пост от автора для фоловера',
        )
        response = self.authorized_follower.get(
            get_reverse_url(self.follow_index))
        self.assertEqual(len(response.context['page_obj']),
                         follower_posts_count_befor_post + 1)
        response = self.authorized_not_follower.get(
            get_reverse_url(self.follow_index))
        self.assertEqual(len(response.context['page_obj']),
                         not_follower_posts_count_befor_post)


class PostPagesPagenatorTest(TestCase):
    @ classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='Writer')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )

        # name _template arg
        cls.index = ('posts:index', 'posts/index.html', None)
        cls.group_list = ('posts:group_list',
                          'posts/group_list.html', [cls.group.slug])
        cls.profile = ('posts:profile', 'posts/profile.html',
                       [cls.user_author.username])

        for i in range(13):
            Post.objects.create(
                author=cls.user_author,
                text=f'{i+1}й тестовый длинююююющий пост',
                group=cls.group
            )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_author = Client()
        self.authorized_author.force_login(self.user_author)

    def test_page_contains_records(self):
        """Проверяем паджинатор."""
        posts_on_last_page = Post.objects.count() % POSTS_PER_PAGE
        if posts_on_last_page == 0:
            posts_on_last_page = 10
            pages_count = Post.objects.count() // POSTS_PER_PAGE
        else:
            pages_count = Post.objects.count() // POSTS_PER_PAGE + 1
        page_names_templates_args = (
            self.index, self.group_list, self.profile
        )
        for url_tuple in page_names_templates_args:
            reversed_name = get_reverse_url(url_tuple)
            with self.subTest(reversed_name=reversed_name):
                response = self.guest_client.get(reversed_name)
                self.assertEqual(len(response.context['page_obj']),
                                 POSTS_PER_PAGE)
                response = self.guest_client.get(
                    reversed_name + f'?page={pages_count}')
                self.assertEqual(
                    len(response.context['page_obj']),
                    posts_on_last_page)
