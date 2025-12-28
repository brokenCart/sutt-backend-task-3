from django import forms
from .models import Thread, Reply, Report

class CreateThreadForm(forms.ModelForm):
    class Meta:
        model = Thread
        fields = ['title', 'course', 'resource', 'category', 'tags', 'content']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter a clear, concise title',
            }),
            'course': forms.Select(attrs={
                'class': 'form-select',
            }),
            'resource': forms.Select(attrs={
                'class': 'form-select',
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Explain your question or topic in detail...',
            }),
            'tags': forms.CheckboxSelectMultiple(),
        }

class CreateReplyForm(forms.ModelForm):
    class Meta:
        model = Reply
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write your reply...',
            })
        }

class CreateReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['reason']
        widgets = {
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write the reason for report...',
            })
        }
