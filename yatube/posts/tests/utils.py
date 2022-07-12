from django.urls import reverse


def checking_post_content(self, post, text, author, group, image):
    """Проверяем контент поста."""
    self.assertEqual(post.text, text)
    self.assertEqual(post.author.username, author)
    self.assertEqual(post.group.id, group)
    self.assertEqual(post.image, image)


def get_reverse_url(url_tuple):
    """Возвращает url из name, arg"""
    return reverse(url_tuple[0], args=url_tuple[2])
