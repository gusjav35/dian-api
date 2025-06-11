from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from PIL import Image
import pytesseract
import pyautogui
import os
import json
import re
import time

async def main(nit: str):
    driver = None
    try:
        print(f"Iniciando consulta para NIT: {nit}")
        driver = Driver(uc=True, headless=False)
        url = "https://muisca.dian.gov.co/WebRutMuisca/DefConsultaEstadoRUT.faces"
        driver.uc_open_with_reconnect(url, 3)
        print("Página cargada")

        print("Esperando captcha...")
        time.sleep(5)  # Esperar a que cargue bien todo

        # ✅ Clic manual en el checkbox de Cloudflare
        print("Haciendo clic en coordenadas fijas...")
        x = 322  # <- reemplazá con tu coordenada real del checkbox
        y = 620  # <- reemplazá con tu coordenada real del checkbox

        pyautogui.moveTo(x, y, duration=1)
        pyautogui.mouseDown()
        time.sleep(0.3)
        pyautogui.mouseUp()
        print("✅ Clic simulado manualmente sobre el checkbox")
        time.sleep(4)  # dar tiempo a que se valide el captcha


        original_window = driver.current_window_handle
        for window in driver.window_handles:
            if window != original_window:
                driver.switch_to.window(window)
                break

        wait = WebDriverWait(driver, 15)
        wait.until(EC.element_to_be_clickable((By.ID, "vistaConsultaEstadoRUT:formConsultaEstadoRUT:numNit")))
        print("Campo NIT encontrado")

        campo_nit = driver.find_element(By.ID, "vistaConsultaEstadoRUT:formConsultaEstadoRUT:numNit")
        campo_nit.clear()
        campo_nit.send_keys(nit)
        campo_nit.send_keys(Keys.RETURN)

        wait.until(EC.presence_of_element_located((By.ID, "vistaConsultaEstadoRUT:formConsultaEstadoRUT:razonSocial")))
        print("Datos cargados correctamente")

        resultado_img = "resultado_dian.png"
        driver.save_screenshot(resultado_img)

    except Exception as e:
        print(f"❌ Error durante navegación: {e}")
        if driver:
            driver.save_screenshot("error_screenshot.png")
        raise e

    finally:
        if driver:
            driver.quit()

    # OCR y extracción
    try:
        print("Procesando OCR...")
        if os.path.exists('/usr/bin/tesseract'):
            pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

        img = Image.open(resultado_img).convert("L")
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

        if os.path.exists(resultado_img):
            os.remove(resultado_img)

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
