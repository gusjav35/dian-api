from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from PIL import Image
import pytesseract
import os
import json
import re
import time
import pyautogui

def main(nit: str):
    driver = None
    try:
        print(f"Iniciando consulta para NIT: {nit}")

        driver = Driver(
            uc=True,
            headless=False,
            user_data_dir="/home/gustavo/.config/google-chrome/Default"
        )

        driver.uc_open_with_reconnect("https://muisca.dian.gov.co/WebRutMuisca/DefConsultaEstadoRUT.faces", 4)

        print("🧠 Calculando posición del checkbox en base al botón 'Buscar'...")
        boton = driver.find_element(By.ID, "vistaConsultaEstadoRUT:formConsultaEstadoRUT:btnBuscar")
        location = boton.location
        size = boton.size

        # Coordenadas estimadas del checkbox relativo al botón Buscar
        x = location["x"] + 100
        y = location["y"] + 120

        
        time.sleep(1)
        pyautogui.moveTo(x, y, duration=1)
        pyautogui.click()
        print(f"✅ Clic en checkbox estimado en x={x}, y={y}")

        time.sleep(4)

        campo_nit = driver.find_element(By.ID, "vistaConsultaEstadoRUT:formConsultaEstadoRUT:numNit")
        campo_nit.clear()
        campo_nit.send_keys(nit)
        campo_nit.send_keys(Keys.RETURN)
        print("✅ NIT enviado")

        driver.wait_for_element("#vistaConsultaEstadoRUT\\:formConsultaEstadoRUT\\:razonSocial", timeout=15)
        print("✅ Datos cargados correctamente")

        resultado_img = "resultado_dian.png"
        driver.save_screenshot(resultado_img)

    except Exception as e:
        print(f"❌ Error durante navegación: {e}")
        if driver:
            try:
                driver.save_screenshot("error_screenshot.png")
            except:
                pass
        raise e

    finally:
        if driver:
            driver.quit()

    try:
        print("Procesando OCR...")
        if os.path.exists('/usr/bin/tesseract'):
            pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

        img = Image.open("resultado_dian.png").convert("L")
        texto = pytesseract.image_to_string(img, lang="spa")

        with open("debug_ocr.txt", "w", encoding="utf-8") as f:
            f.write(texto)

        razon = re.search(r"Raz[oó]n Social\s*([A-Z0-9\s\.\-&áéíóúüñÁÉÍÓÚÜÑ]+)", texto, re.IGNORECASE)
        fecha = re.search(r"Fecha Actual\s*([0-9\-: ]+)", texto, re.IGNORECASE)
        estado = re.search(r"Estado\s*([A-ZÁÉÍÓÚáéíóúüñÑ ]+)", texto, re.IGNORECASE)

        data = {
            "NIT": nit,
            "razon_social": razon.group(1).strip() if razon else "No encontrado",
            "fecha": fecha.group(1).strip() if fecha else "No encontrada",
            "estado": estado.group(1).strip() if estado else "No encontrado",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        with open("resultado_dian.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        os.remove("resultado_dian.png")

        print("✅ OCR y extracción completada")

    except Exception as e:
        print(f"❌ Error en OCR: {e}")
        with open("resultado_dian.json", "w", encoding="utf-8") as f:
            json.dump({
                "NIT": nit,
                "razon_social": "Error en OCR",
                "fecha": "Error en OCR",
                "estado": "Error en OCR",
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }, f, ensure_ascii=False, indent=2)
        raise e

if __name__ == "__main__":
    main("901192159")
