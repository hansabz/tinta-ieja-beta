from django.db import models


class Estilo(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Etiqueta(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Obra(models.Model):
    artista = models.ForeignKey("artists.Empleado", on_delete=models.CASCADE, related_name="obras")
    estilo = models.ForeignKey(Estilo, on_delete=models.PROTECT, related_name="obras")
    etiquetas = models.ManyToManyField(Etiqueta, blank=True, related_name="obras")
    titulo = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to="obras/")
    zona_cuerpo = models.CharField(max_length=60, blank=True)
    fecha = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["estilo"]),
            models.Index(fields=["artista"]),
        ]

    def __str__(self):
        return self.titulo
