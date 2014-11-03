from django.forms import ModelForm
from .models import Assembly


class AssemblyForm(ModelForm):
    class Meta:
        model = Assembly
        fields = ['recipe', 'contigs', 'metagenome']
