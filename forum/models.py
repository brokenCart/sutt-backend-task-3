from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class Course(models.Model):
    code = models.CharField(max_length=20)
    title = models.CharField(max_length=200)
    department = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.code}: {self.title}"

class Resource(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    type = models.CharField(max_length=10, choices=[
        ('pdf', 'PDF'),
        ('video', 'Video'),
        ('link', 'Link'),
    ])
    link = models.URLField()

    def __str__(self):
        return f"{self.course} -> {self.title}"

class Tag(models.Model):
    name = models.CharField(max_length=30, unique=True)
    slug = models.SlugField(max_length=40, unique=True)

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=30, unique=True)
    slug = models.SlugField(max_length=40, unique=True)

    def __str__(self):
        return self.name

class Thread(models.Model):
    title = models.CharField(max_length=200)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    resource = models.ForeignKey(Resource, on_delete=models.SET_NULL, null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField()
    created_timestamp = models.DateTimeField(default=timezone.now)
    is_locked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    tags = models.ManyToManyField(Tag, blank=True)

    class Meta:
        permissions = [
            ('lock_thread', 'Can lock threads'),
            ('delete_any_thread', 'Can delete any thread')
        ]
    
    def __str__(self):
        return f'{self.author}: {self.title}'

class Reply(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField()
    created_timestamp = models.DateTimeField(default=timezone.now)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        permissions = [
            ('delete_any_reply', 'Can delete any reply'),
        ]
    
    def __str__(self):
        return f'{self.author}: {self.content[:100]}'

class UpvoteThread(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['thread', 'user'],
                name='unique_thread_upvote',
            )
        ]

class UpvoteReply(models.Model):
    reply = models.ForeignKey(Reply, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['reply', 'user'],
                name='unique_reply_upvote',
            )
        ]

class Report(models.Model):
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    reply = models.ForeignKey(Reply, on_delete=models.CASCADE, null=True, blank=True)
    reason = models.TextField()
    created_timestamp = models.DateTimeField(default=timezone.now)
    resolved = models.BooleanField(default=False)

    class Meta:
        permissions = [
            ('view_report_page', 'Can view a page with all the reports'),
        ]

    def __str__(self):
        return f'{self.author}: {self.reason}'
