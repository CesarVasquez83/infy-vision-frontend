"""
probar_vision.py — Cliente INFY VISION API v5.0

Uso:
    python probar_vision.py                           # STANDARD con tablero.png
    python probar_vision.py --elite                   # ELITE agnóstico
    python probar_vision.py --imagen mi_radar.png --elite
"""

import requests
import argparse
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

parser = argparse.ArgumentParser(description="INFY VISION API v5.0 — cliente de prueba")
parser.add_argument("--imagen",  default="tablero.png", help="Ruta a la imagen (default: tablero.png)")
parser.add_argument("--elite",   action="store_true",   help="Usar endpoint ELITE agnóstico")
args = parser.parse_args()

try:
    imagen_file = open(args.imagen, "rb")
except FileNotFoundError:
    print(f"❌ No se encontró la imagen: {args.imagen}")
    sys.exit(1)

print(f"\n{'='*60}")
print(f"  INFY VISION API v5.0")
print(f"  Imagen : {args.imagen}")
print(f"  Modo   : {'ELITE' if args.elite else 'STANDARD'}")
print(f"{'='*60}\n")

with imagen_file:
    files    = {"file": (args.imagen, imagen_file, "image/png")}
    endpoint = f"{BASE_URL}/vision-analysis/elite" if args.elite else f"{BASE_URL}/vision-analysis"
    r        = requests.post(endpoint, files=files)

print(f"Status : {r.status_code}")
print(f"URL    : {endpoint}\n")

if r.status_code == 200:
    resp = r.json()
    mode = resp.get("mode", "STANDARD")
    print(f"📡 Modo retornado : {mode}")

    print("\n" + "─"*60)
    print("📊 BLOQUE STANDARD")
    print("─"*60)
    standard = resp.get("standard") or resp
    print(json.dumps(standard, indent=2, ensure_ascii=False))

    if mode == "ELITE" and resp.get("elite"):
        elite = resp["elite"]
        print("\n" + "─"*60)
        print("🏆 BLOQUE ELITE")
        print("─"*60)
        print(f"\n  approach_infy      : {elite.get('approach_infy')}")
        print(f"  framework_detectado: {elite.get('framework_detectado')}")
        print(f"  confianza_lectura  : {elite.get('confianza_lectura')}")

        print(f"\n  📐 Suitability Indexes leídos:")
        for k, v in (elite.get("suitability_indexes") or {}).items():
            print(f"    {k:15}: {v}")

        print(f"\n  🎯 VEREDICTO:")
        print(f"  {elite.get('veredicto')}")

        print(f"\n  Flags:")
        print(f"    more_pred : {elite.get('suitability_more_pred')}")
        print(f"    less_pred : {elite.get('suitability_less_pred')}")
        print(f"    mismatch  : {elite.get('suitability_mismatch')}")

        if elite.get("kpis_detectados"):
            print(f"\n  🔍 KPIs detectados en la imagen:")
            print(json.dumps(elite.get("kpis_detectados"), indent=4, ensure_ascii=False))

        if elite.get("notas_lectura"):
            print(f"\n  📝 Notas: {elite.get('notas_lectura')}")
else:
    print("❌ ERROR:")
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))
