from django.contrib import admin
from .models import Metagenome, Recipe, Assembly


class MetagenomeAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'name',
        'references',
        'reads',
    ]
admin.site.register(Metagenome, MetagenomeAdmin)


class RecipeAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'name',
    ]
admin.site.register(Recipe, RecipeAdmin)


class AssemblyAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'recipe',
        'contigs',
        'metagenome',
    ]
admin.site.register(Assembly, AssemblyAdmin)
