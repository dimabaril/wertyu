import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings

from ..models import Comment, Group, Post, User
from .utils import checking_post_content, get_reverse_url

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostcreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='Writer')
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
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        small_2_gif = (
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
        cls.uploaded_2 = SimpleUploadedFile(
            name='small_2.gif',
            content=small_2_gif,
            content_type='image/gif'
        )

        # name _template arg
        cls.profile = ('posts:profile', 'posts/profile.html',
                       [cls.user_author.username])
        cls.detail = ('posts:post_detail', 'posts/post_detail.html',
                      [cls.post.id])
        cls.edit = ('posts:post_edit', 'posts/post_create.html',
                    [cls.post.id])
        cls.create = ('posts:post_create', 'posts/post_create.html', None)
        cls.comment = ('posts:add_comment', None, [cls.post.id])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_author)

    def test_authorized_create_post(self):
        """Авторизованным создаём новую запись и проверяем редирект"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый авторизованным пост',
            'group': self.group.id,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            get_reverse_url(self.create),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, get_reverse_url(self.profile))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.latest('id')
        checking_post_content(
            self, post,
            form_data['text'], self.user_author.username, form_data['group'],
            'posts/' + form_data['image'].name
        )

    def test_authorized_edit_post(self):
        """Авторизованным правим запись и проверяем редирект"""
        posts_count = Post.objects.count()
        self.assertFalse(Post.objects.filter(
            text='Правленный авторизованным пост',
            group=self.group.id).exists()
        )
        form_data = {
            'text': 'Правленный авторизованным пост',
            'group': self.group.id,
            'image': self.uploaded_2,
        }
        response = self.authorized_client.post(
            get_reverse_url(self.edit),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, get_reverse_url(self.detail))
        self.assertEqual(Post.objects.count(), posts_count)
        post = Post.objects.get(id=self.post.id)
        checking_post_content(
            self, post,
            form_data['text'], self.user_author.username, form_data['group'],
            'posts/' + form_data['image'].name
        )

    def test_guest_create_post(self):
        """Гость не может создать новую запись и проверяем редирект"""
        posts_count = Post.objects.count()
        form_data = {'text': 'Гостевой тестовый пост'}
        response = self.guest_client.post(
            get_reverse_url(self.create),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(Post.objects.filter(
            text='Гостевой тестовый пост').exists()
        )

    def test_guest_edit_post(self):
        """Гость не может править запись и проверяем редирект"""
        posts_count = Post.objects.count()
        form_data = {'text': 'Правленный гостем пост'}
        response = self.guest_client.post(
            get_reverse_url(self.edit),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/edit/')
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(Post.objects.filter(
            text='Правленный гостем пост').exists()
        )

    def test_authorized_create_comment(self):
        """Авторизованным создаём комментарий и проверяем редирект"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый авторизованным коммент',
            'post': self.post,
        }
        response = self.authorized_client.post(
            get_reverse_url(self.comment),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, get_reverse_url(self.detail))
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(Comment.objects.latest('id').text, form_data['text'])

    def test_guest_create_comment(self):
        """Гость не может создать коммент и проверяем редирект"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый гостем коммент',
            'post': self.post,
        }
        response = self.guest_client.post(
            get_reverse_url(self.comment),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/comment/')
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertFalse(Comment.objects.filter(
            text='Тестовый гостем коммент').exists()
        )
