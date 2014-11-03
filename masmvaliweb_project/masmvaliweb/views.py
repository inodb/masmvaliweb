from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from masmvaliweb.forms import AssemblyForm
from masmvaliweb.models import Metagenome


# Create your views here.
def add_assembly(request):
    if request.method == 'POST':
        form = AssemblyForm(request.POST, request.FILES)
        if form.is_valid():
            # file is saved
            form.save()
            return HttpResponseRedirect(reverse('masmvaliweb.views.add_assembly_success'))
    else:
        form = AssemblyForm()
    return render(request, 'masmvaliweb/upload.html', {'form': form})


def add_assembly_success(request):
    return render(request, 'masmvaliweb/add_assembly_success.html')


def browse(request):
    return render(request, 'masmvaliweb/browse.html')


def index(request):
    return render(request, 'masmvaliweb/index.html')


def metagenome(request, id):
    mg = Metagenome.objects.get(pk=id)
    return render(request, 'masmvaliweb/metagenome.html', {"metagenome": mg})
