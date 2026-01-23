import threading

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.postgres.search import TrigramSimilarity
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from . import models
from .forms import CreateReplyForm, CreateReportForm, CreateThreadForm

PER_PAGE = 10


@login_required
def home(request, category_slug=None):
    threads = models.Thread.objects.filter(is_deleted=False)
    if category_slug:
        threads = threads.filter(category__slug=category_slug)

    sort = request.GET.get("sort", "latest")
    order = request.GET.get("order", "desc")

    if sort == "latest":
        order_field = "created_timestamp"
    elif sort == "popular":
        threads = threads.annotate(upvote_count=Count("upvotethread"))
        order_field = "upvote_count"

    if order == "desc":
        threads = threads.order_by(f"-{order_field}")
    else:
        threads = threads.order_by(order_field)

    search_query = request.GET.get("search")
    if search_query:
        # NOTE: The database should be PostgreSQL
        threads = (
            threads.annotate(similarity=TrigramSimilarity("title", search_query))
            .filter(similarity__gt=0.3)
            .order_by("-similarity")
        )

    paginator = Paginator(threads, PER_PAGE)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        "forum/home.html",
        context={"page_obj": page_obj, "sort": sort, "order": order},
    )


@login_required
def thread_view(request, category_slug, pk):
    thread = get_object_or_404(models.Thread, pk=pk, category__slug=category_slug)
    if thread.is_deleted:
        return HttpResponseForbidden()
    replies = models.Reply.objects.filter(thread__id=pk, is_deleted=False)

    sort = request.GET.get("sort", "latest")
    order = request.GET.get("order", "desc")

    if sort == "latest":
        order_field = "created_timestamp"
    elif sort == "popular":
        replies = replies.annotate(upvote_count=Count("upvotereply"))
        order_field = "upvote_count"

    if order == "desc":
        replies = replies.order_by(f"-{order_field}")
    else:
        replies = replies.order_by(order_field)

    paginator = Paginator(replies, PER_PAGE)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    reply_page_map = {}
    for index, reply in enumerate(replies):
        reply_page_map[reply.id] = (index // PER_PAGE) + 1

    reply_form = CreateReplyForm()
    return render(
        request,
        "forum/thread_view.html",
        context={
            "thread": thread,
            "page_obj": page_obj,
            "reply_form": reply_form,
            "reply_page_map": reply_page_map,
            "sort": sort,
            "order": order,
        },
    )


@login_required
def create_thread(request):
    if request.method == "POST":
        form = CreateThreadForm(request.POST)
        if form.is_valid():
            thread = form.save(commit=False)
            if thread.resource and thread.course != thread.resource.course:
                messages.warning(request, "The resource should be of the same course!")
            else:
                thread.author = request.user
                thread.save()
                form.save_m2m()
                messages.success(request, "Your thread has been created!")
                return redirect(
                    "thread-view", category_slug=thread.category.slug, pk=thread.id
                )
    else:
        form = CreateThreadForm()
    return render(request, "forum/create_thread.html", {"form": form})


def send_email_async(subject, message, to_email):
    def task():
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [to_email],
            fail_silently=True,
        )

    threading.Thread(target=task).start()


@login_required
def create_reply(request, category_slug, pk, parent_id=None):
    thread = get_object_or_404(models.Thread, pk=pk, category__slug=category_slug)
    parent = None

    if parent_id is not None:
        parent = get_object_or_404(models.Reply, id=parent_id, thread=thread)

    if request.method == "POST":
        form = CreateReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.thread = thread
            reply.parent = parent
            reply.author = request.user
            reply.save()
            if parent and parent.author != reply.author:
                subject = f"New reply on the thread: {thread.title}"
                thread_url = request.build_absolute_uri(
                    reverse("thread-view", args=[thread.category.slug, thread.id])
                )
                message = f"You: \n{reply.parent.content}\n\n{reply.author.username} replied: \n{reply.content}\n{thread_url}"
                send_email_async(subject, message, thread.author.email)
            elif not parent and thread.author != reply.author:
                subject = f"New reply on your thread: {thread.title}"
                thread_url = request.build_absolute_uri(
                    reverse("thread-view", args=[thread.category.slug, thread.id])
                )
                message = (
                    f"{reply.author.username} replied: \n{reply.content}\n{thread_url}"
                )
                send_email_async(subject, message, thread.author.email)
            messages.success(request, "Your reply has been created!")
            return redirect(
                "thread-view", category_slug=thread.category.slug, pk=thread.pk
            )
    return redirect("thread-view", category_slug=thread.category.slug, pk=thread.pk)


@login_required
def delete_thread(request, pk):
    if request.method == "POST":
        thread = get_object_or_404(models.Thread, pk=pk)
        if thread.author != request.user and not request.user.has_perm(
            "forum.delete_any_thread"
        ):
            return HttpResponseForbidden()
        thread.is_deleted = True
        thread.save()
        messages.success(request, "Thread has been deleted!")
        return redirect("home")
    return HttpResponseForbidden()


@login_required
def delete_reply(request, pk):
    if request.method == "POST":
        reply = get_object_or_404(models.Reply, pk=pk)
        if reply.author != request.user and not request.user.has_perm(
            "forum.delete_any_reply"
        ):
            return HttpResponseForbidden()
        reply.is_deleted = True
        reply.save()
        messages.success(request, "Reply has been deleted!")
        return redirect(
            "thread-view", category_slug=reply.thread.category.slug, pk=reply.thread.pk
        )
    return HttpResponseForbidden()


@login_required
def category_list(request):
    return render(
        request,
        "forum/category_list.html",
        context={"categories": models.Category.objects.all()},
    )


@login_required
@permission_required("forum.lock_thread", raise_exception=True)
def toggle_thread_lock(request, pk):
    if request.method == "POST":
        thread = get_object_or_404(models.Thread, pk=pk)
        thread.is_locked = not thread.is_locked
        thread.save()
        return redirect("thread-view", category_slug=thread.category.slug, pk=thread.pk)
    return HttpResponseForbidden()


@login_required
def report_thread(request, pk):
    form = CreateReportForm()
    thread = get_object_or_404(models.Thread, pk=pk)
    if request.method == "POST":
        form = CreateReportForm(request.POST)
        report = models.Report.objects.filter(
            thread=thread, author=request.user
        ).first()
        if report:
            messages.warning(request, "You have already reported this thread!")
            return redirect(
                "thread-view", category_slug=thread.category.slug, pk=thread.pk
            )
        if form.is_valid():
            report = form.save(commit=False)
            report.thread = thread
            report.author = request.user
            report.save()
            messages.success(request, "Thread has been reported!")
            return redirect(
                "thread-view", category_slug=thread.category.slug, pk=thread.pk
            )
    return render(
        request,
        "forum/create_report.html",
        {"form": form, "object": thread, "object_type": "thread"},
    )


@login_required
def report_reply(request, pk):
    reply = get_object_or_404(models.Reply, pk=pk)
    form = CreateReportForm()
    if request.method == "POST":
        form = CreateReportForm(request.POST)
        report = models.Report.objects.filter(reply=reply, author=request.user).first()
        if report:
            messages.warning(request, "You have already reported this reply!")
            return redirect(
                "thread-view",
                category_slug=reply.thread.category.slug,
                pk=reply.thread.pk,
            )
        if form.is_valid():
            report = form.save(commit=False)
            report.thread = reply.thread
            report.reply = reply
            report.author = request.user
            report.save()
            messages.success(request, "Reply has been reported!")
            return redirect(
                "thread-view",
                category_slug=reply.thread.category.slug,
                pk=reply.thread.pk,
            )
    return render(
        request,
        "forum/create_report.html",
        {"form": form, "object": reply, "object_type": "reply"},
    )


@login_required
@permission_required("forum.view_report_page", raise_exception=True)
def reports_view(request):
    reports = models.Report.objects.filter(resolved=False).order_by(
        "-created_timestamp"
    )
    reply_reports = reports.filter(reply__isnull=False)
    reply_page_map = {}
    for report in reply_reports:
        reply = report.reply
        index = models.Reply.objects.filter(
            thread=reply.thread,
            is_deleted=False,
            created_timestamp__lt=reply.created_timestamp,
        ).count()
        page = (index // PER_PAGE) + 1
        reply_page_map[reply.id] = page
    return render(
        request,
        "forum/reports_view.html",
        {"reports": reports, "reply_page_map": reply_page_map},
    )


@login_required
@permission_required("forum.view_report_page", raise_exception=True)
def resolve_report(request, pk):
    if request.method == "POST":
        report = get_object_or_404(models.Report, pk=pk)
        report.resolved = True
        report.save()
        return redirect("reports-list")
    return HttpResponseForbidden()


@login_required
def load_resources_for_course(request):
    course_id = request.GET.get("course_id")
    resources = models.Resource.objects.filter(course_id=course_id)
    return JsonResponse([{"id": r.id, "title": r.title} for r in resources], safe=False)


@login_required
def toggle_thread_like(request, pk):
    thread = get_object_or_404(models.Thread, pk=pk)
    if request.method == "POST":
        upvote = models.UpvoteThread.objects.filter(
            thread=thread, user=request.user
        ).first()
        if upvote:
            upvote.delete()
        else:
            upvote = models.UpvoteThread(thread=thread, user=request.user)
            upvote.save()
    liked = models.UpvoteThread.objects.filter(
        thread=thread, user=request.user
    ).exists()
    upvote_count = models.UpvoteThread.objects.filter(thread=thread).count()
    return JsonResponse({"upvote_count": upvote_count, "liked": liked})


@login_required
def toggle_reply_like(request, pk):
    reply = get_object_or_404(models.Reply, pk=pk)
    if request.method == "POST":
        upvote = models.UpvoteReply.objects.filter(
            reply=reply, user=request.user
        ).first()
        if upvote:
            upvote.delete()
        else:
            upvote = models.UpvoteReply(reply=reply, user=request.user)
            upvote.save()
    liked = models.UpvoteReply.objects.filter(reply=reply, user=request.user).exists()
    upvote_count = models.UpvoteReply.objects.filter(reply=reply).count()
    return JsonResponse({"upvote_count": upvote_count, "liked": liked})
