from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import os
import json
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

        print("📦 Extrayendo datos del DOM...")
        razon_social = driver.find_element(By.ID, "vistaConsultaEstadoRUT:formConsultaEstadoRUT:razonSocial").text.strip()
        estado = driver.find_element(By.ID, "vistaConsultaEstadoRUT:formConsultaEstadoRUT:estado").text.strip()

        # 🟡 Extracción robusta de la fecha con JavaScript
        fecha = driver.execute_script("""
            return [...document.querySelectorAll("td.fondoTituloLeftAjustado")]
                .find(td => td.textContent.trim() === "Fecha Actual")
                ?.nextElementSibling?.textContent.trim();
        """)

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        data = {
            "NIT": nit,
            "razon_social": razon_social.replace("S.A.S.", "SAS"),
            "fecha": fecha.replace(" ", "").replace(":", "") if fecha else "No encontrada",
            "estado": estado,
            "timestamp": timestamp
        }

        with open("resultado_dian.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print("✅ Extracción completada")

    except Exception as e:
        print(f"❌ Error durante navegación o extracción: {e}")
        if driver:
            try:
                driver.save_screenshot("error_screenshot.png")
            except:
                pass
        with open("resultado_dian.json", "w", encoding="utf-8") as f:
            json.dump({
                "NIT": nit,
                "razon_social": "Error",
                "fecha": "Error",
                "estado": "Error",
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }, f, ensure_ascii=False, indent=2)
        raise e

    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main("901192159")
