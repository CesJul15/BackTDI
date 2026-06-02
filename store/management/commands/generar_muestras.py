from django.core.management.base import BaseCommand
from store.models import Instrumento
from django.core.files.base import ContentFile
import os
import requests
import time


class Command(BaseCommand):
    help = "Genera muestras de audio para todos los instrumentos usando Hugging Face MusicGen"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Sobrescribir muestras existentes")
        parser.add_argument("--model", type=str, help="Modelo HF a usar (p. ej. facebook/musicgen-small)")

    def handle(self, *args, **options):
        token = os.environ.get("HF_TOKEN")
        if not token:
            self.stderr.write("HF_TOKEN no configurado en el entorno")
            return

        model = options.get("model") or os.environ.get("HF_MODEL", "facebook/musicgen-small")
        force = options.get("force")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        instrumentos = Instrumento.objects.all()
        total = instrumentos.count()
        self.stdout.write(f"Procesando {total} instrumentos con modelo {model}")

        for idx, inst in enumerate(instrumentos, start=1):
            if inst.audio_sample and not force:
                self.stdout.write(f"[{idx}/{total}] Saltando {inst.name} (ya tiene muestra)")
                continue

            prompt = f"Genera un breve audio de muestra (5-12s) del siguiente instrumento: {inst.name}. Sonido realista, timbre de instrumento, sin voz."
            self.stdout.write(f"[{idx}/{total}] Generando muestra para: {inst.name}")

            try:
                resp = requests.post(f"https://api-inference.huggingface.co/models/{model}", json={"inputs": prompt}, headers=headers, timeout=120)
                resp.raise_for_status()
                audio_bytes = resp.content
                if not audio_bytes:
                    self.stderr.write(f"No se recibió audio para {inst.name}")
                    continue
                filename = f"instrument_{inst.id}_sample.wav"
                inst.audio_sample.save(filename, ContentFile(audio_bytes), save=True)
                self.stdout.write(f"Guardado: {filename}")
            except Exception as e:
                self.stderr.write(f"Error generando {inst.name}: {e}")

            # pequeña espera para evitar ráfagas
            time.sleep(1)

        self.stdout.write("Generación completada")
