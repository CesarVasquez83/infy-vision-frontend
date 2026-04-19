import os
import json
import time
import glob
import requests

API_URL = "http://localhost:8000/vision-analysis"
IMAGES_DIR = "./test_images"  # carpeta con tus imágenes
MAX_IMAGES = 10               # cuántas imágenes probar

def list_images(directory):
    patterns = ("*.png", "*.jpg", "*.jpeg", "*.webp")
    files = []
    for pattern in patterns:
        files.extend(glob.glob(os.path.join(directory, pattern)))
    return sorted(files)

def test_image(path):
    filename = os.path.basename(path)
    with open(path, "rb") as f:
        files = {"file": (filename, f, "image/jpeg")}  # el tipo MIME no es crítico aquí
        try:
            start = time.time()
            resp = requests.post(API_URL, files=files, timeout=60)
            elapsed = time.time() - start
        except Exception as e:
            return {
                "filename": filename,
                "status_code": None,
                "error": f"ERROR_REQUEST: {e}",
                "elapsed_sec": None,
            }

    result = {
        "filename": filename,
        "status_code": resp.status_code,
        "elapsed_sec": round(elapsed, 3),
    }

    try:
        data = resp.json()
    except Exception:
        result["error"] = "ERROR_PARSE_JSON"
        result["raw_text"] = resp.text[:500]
        return result

    # Caso 422: no es dashboard
    if resp.status_code == 422:
        # FastAPI suele devolver {"detail": "..."} o similar
        result["type"] = "NO_DASHBOARD"
        result["detail"] = data.get("detail", data)
        return result

    # Caso 200: dashboard válido
    if resp.status_code == 200:
        result["type"] = "OK"
        result["id"] = data.get("id")
        result["returned_filename"] = data.get("filename")
        result["descripcion"] = data.get("descripcion")
        analisis_pm = data.get("analisis_pm", {})

        # opcional: sacar algunos campos clave del AnalisisPM
        proyecto = analisis_pm.get("proyecto", {})
        resumen = analisis_pm.get("resumen_ejecutivo", {})
        result["proyecto_nombre"] = proyecto.get("nombre")
        result["estado_proyecto"] = resumen.get("estado_proyecto")
        result["version_modelo"] = analisis_pm.get("version_modelo")

        return result

    # Cualquier otro código: tratar como error
    result["type"] = "ERROR"
    result["detail"] = data
    return result


def main():
    images = list_images(IMAGES_DIR)
    if not images:
        print(f"No se encontraron imágenes en: {IMAGES_DIR}")
        return

    if MAX_IMAGES:
        images = images[:MAX_IMAGES]

    print(f"Probando {len(images)} imágenes contra {API_URL}")

    results = []
    for path in images:
        print(f"-> Enviando: {path}")
        res = test_image(path)
        results.append(res)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        print("-" * 60)

    # Resumen final
    ok = sum(1 for r in results if r.get("type") == "OK")
    no_dash = sum(1 for r in results if r.get("type") == "NO_DASHBOARD")
    errors = sum(1 for r in results if r.get("type") == "ERROR" or r.get("error"))

    print("===== RESUMEN =====")
    print(f"Total imágenes: {len(results)}")
    print(f"Dashboards OK: {ok}")
    print(f"No-dashboard (422): {no_dash}")
    print(f"Errores: {errors}")


if __name__ == "__main__":
    main()