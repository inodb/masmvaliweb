from django.db import models


# Create your models here.
class Metagenome(models.Model):
    """Keep track of metagenomes"""
    name = models.TextField(max_length=50, unique=True)
    references = models.URLField()
    reads = models.URLField()
    description = models.TextField()

    def __unicode__(self):
        return unicode(self.name)


class Recipe(models.Model):
    """Assembly recipes"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField()

    def __unicode__(self):
        return unicode(self.name)


class Assembly(models.Model):
    """Keep track of assemblies"""
    recipe = models.ForeignKey(Recipe)
    contigs = models.FileField(upload_to="{}")
    metagenome = models.ForeignKey(Metagenome)

    def __unicode__(self):
        return unicode("{metagenome}/{recipe}".format(
            recipe=self.recipe,
            metagenome=self.metagenome))

    class Meta:
        verbose_name_plural = "Assemblies"
