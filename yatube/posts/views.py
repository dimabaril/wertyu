from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import paginate


@cache_page(1, key_prefix='index_page')
def index(request):
    """Отображаем главную страничку со всеми постами."""
    posts_list = Post.objects.select_related('group', 'author')
    page_obj = paginate(posts_list, request)
    context = {'page_obj': page_obj}
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Отображаем посты фильтруя по группе."""
    group = get_object_or_404(Group, slug=slug)
    posts_list = group.posts.select_related('author')
    page_obj = paginate(posts_list, request)
    context = {'group': group, 'page_obj': page_obj}
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Отображаем посты фильтруя по юзеру."""
    author = get_object_or_404(User, username=username)
    posts_list = author.posts.select_related('group', 'author')
    posts_count = posts_list.count()
    page_obj = paginate(posts_list, request)
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=author).exists()
    context = {
        'author': author,
        'page_obj': page_obj,
        'posts_count': posts_count,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Отображаем пост фильтруя по id и прочую инфу."""
    post = get_object_or_404(
        Post.objects.select_related('author'), id=post_id)
    posts_count = post.author.posts.count()
    comments = post.comments.all()
    context = {
        'post': post,
        'posts_count': posts_count,
        'form': CommentForm(),
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Создаём пост."""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == "POST" and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=post.author)
    return render(request, 'posts/post_create.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """Редактируем пост."""
    post = get_object_or_404(Post.objects.select_related('author'), id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    is_edit = True
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if request.method == "POST" and form.is_valid():
        post = form.save()
        return redirect('posts:post_detail', post_id=post_id)
    return render(request, 'posts/post_create.html',
                  {'form': form, 'is_edit': is_edit})


@login_required
def add_comment(request, post_id):
    """Добавляем коммент."""
    post = get_object_or_404(Post.objects.all(), id=post_id)
    form = CommentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Отображаем страничку с постами по подписке."""
    user = request.user
    posts_list = Post.objects.filter(
        author__following__user=user
    ).select_related('group', 'author')
    page_obj = paginate(posts_list, request)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписываемся."""
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(author=author, user=request.user)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    """Отписываемся."""
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(author=author, user=request.user).delete()
    return redirect('posts:profile', username)
