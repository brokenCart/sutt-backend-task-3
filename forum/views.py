from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from . import models
from .forms import CreateThreadForm, CreateReplyForm, CreateReportForm

PER_PAGE = 10

@login_required
def home(request, category_slug=None):
    threads = models.Thread.objects.order_by('-created_timestamp').filter(is_deleted=False)
    if category_slug:
        threads = threads.filter(category__slug=category_slug)
    paginator = Paginator(threads, PER_PAGE)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    return render(request, 'forum/home.html', context={'page_obj': page_obj})

@login_required
def thread_view(request, category_slug, pk):
    thread = get_object_or_404(models.Thread, pk=pk, category__slug=category_slug)
    if thread.is_deleted:
        return HttpResponseForbidden()
    replies = models.Reply.objects.filter(thread__id=pk, is_deleted=False)
    paginator = Paginator(replies, PER_PAGE)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    reply_page_map = {}
    for index, reply in enumerate(replies):
        reply_page_map[reply.id] = (index // PER_PAGE) + 1

    reply_form = CreateReplyForm()
    return render(request, 'forum/thread_view.html', context={'thread': thread, 'page_obj': page_obj, 'reply_form': reply_form, 'reply_page_map': reply_page_map})

@login_required
def create_thread(request):
    if request.method == 'POST':
        form = CreateThreadForm(request.POST)
        if form.is_valid():
            thread = form.save(commit=False)
            if thread.resource and thread.course != thread.resource.course:
                messages.warning(request, 'The resource should be of the same course!')
            else:
                thread.author = request.user
                thread.save()
                form.save_m2m()
                messages.success(request, 'Your thread has been created!')
                return redirect('thread-view', category_slug=thread.category.slug, pk=thread.id)
    else:
        form = CreateThreadForm()
    return render(request, 'forum/create_thread.html', {'form': form})

@login_required
def create_reply(request, category_slug, pk, parent_id=None):
    thread = get_object_or_404(models.Thread, pk=pk, category__slug=category_slug)
    parent = None
    
    if parent_id is not None:
        parent = get_object_or_404(models.Reply, id=parent_id, thread=thread)
    
    if request.method == 'POST':
        form = CreateReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.thread = thread
            reply.parent = parent
            reply.author = request.user
            reply.save()
            messages.success(request, f'Your reply has been created!')
            return redirect('thread-view', category_slug=thread.category.slug, pk=thread.pk)
    return redirect('thread-view', category_slug=thread.category.slug, pk=thread.pk)

@login_required
def delete_thread(request, pk):
    if request.method == 'POST':
        thread = get_object_or_404(models.Thread, pk=pk)
        if thread.author != request.user and not request.user.has_perm('forum.delete_any_thread'):
            return HttpResponseForbidden()
        thread.is_deleted = True
        thread.save()
        messages.success(request, 'Thread has been deleted!')
        return redirect('home')
    return HttpResponseForbidden()

@login_required
def delete_reply(request, pk):
    if request.method == 'POST':
        reply = get_object_or_404(models.Reply, pk=pk)
        if reply.author != request.user and not request.user.has_perm('forum.delete_any_reply'):
            return HttpResponseForbidden()
        reply.is_deleted = True
        reply.save()
        messages.success(request, 'Reply has been deleted!')
        return redirect('thread-view', category_slug=reply.thread.category.slug, pk=reply.thread.pk)
    return HttpResponseForbidden()

@login_required
def category_list(request):
    return render(request, 'forum/category_list.html', context={'categories': models.Category.objects.all()})

@login_required
@permission_required('forum.lock_thread', raise_exception=True)
def toggle_thread_lock(request, pk):
    if request.method == 'POST':
        thread = get_object_or_404(models.Thread, pk=pk)
        thread.is_locked = not thread.is_locked
        thread.save()
        return redirect('thread-view', category_slug=thread.category.slug, pk=thread.pk)
    return HttpResponseForbidden()

@login_required
def report_thread(request, pk):
    form = CreateReportForm()
    thread = get_object_or_404(models.Thread, pk=pk)
    if request.method == 'POST':
        form = CreateReportForm(request.POST)
        report = models.Report.objects.filter(thread=thread, author=request.user).first()
        if report:
            messages.warning(request, 'You have already reported this thread!')
            return redirect('thread-view', category_slug=thread.category.slug, pk=thread.pk)
        if form.is_valid():
            report = form.save(commit=False)
            report.thread = thread
            report.author = request.user
            report.save()
            messages.success(request, 'Thread has been reported!')
            return redirect('thread-view', category_slug=thread.category.slug, pk=thread.pk)
    return render(request, 'forum/create_report.html', {'form': form, 'object': thread, 'object_type': 'thread'})

@login_required
def report_reply(request, pk):
    reply = get_object_or_404(models.Reply, pk=pk)
    form = CreateReportForm()
    if request.method == 'POST':
        form = CreateReportForm(request.POST)
        report = models.Report.objects.filter(reply=reply, author=request.user).first()
        if report:
            messages.warning(request, 'You have already reported this reply!')
            return redirect('thread-view', category_slug=reply.thread.category.slug, pk=reply.thread.pk)
        if form.is_valid():
            report = form.save(commit=False)
            report.thread = reply.thread
            report.reply = reply
            report.author = request.user
            report.save()
            messages.success(request, 'Reply has been reported!')
            return redirect('thread-view', category_slug=reply.thread.category.slug, pk=reply.thread.pk)
    return render(request, 'forum/create_report.html', {'form': form, 'object': reply, 'object_type': 'reply'})

@login_required
@permission_required('forum.view_report_page', raise_exception=True)
def reports_view(request):
    reports = models.Report.objects.filter(resolved=False).order_by('-created_timestamp')
    reply_reports = reports.filter(reply__isnull=False)
    reply_page_map = {}
    for report in reply_reports:
        reply = report.reply
        index = models.Reply.objects.filter(thread=reply.thread, is_deleted=False, created_timestamp__lt=reply.created_timestamp).count()
        page = (index // PER_PAGE) + 1
        reply_page_map[reply.id] = page
    return render(request, 'forum/reports_view.html', {'reports': reports, 'reply_page_map': reply_page_map})

@login_required
@permission_required('forum.view_report_page', raise_exception=True)
def resolve_report(request, pk):
    if request.method == 'POST':
        report = get_object_or_404(models.Report, pk=pk)
        report.resolved = True
        report.save()
        return redirect('reports-list')
    return HttpResponseForbidden()
