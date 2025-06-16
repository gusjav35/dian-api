from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import os
import json
import time
import pyautogui

def intentar_consulta(nit: str):
    driver = None
    try:
        print(f"Iniciando consulta para NIT: {nit}")

        driver = Driver(
            uc=True,
            headless=False,
            #user_data_dir="/home/gustavo/.config/google-chrome/Default"
            user_data_dir="/home/ubuntu/.config/chrome-temp-persistente"
            #user_data_dir=None
        )

        driver.uc_open_with_reconnect("https://muisca.dian.gov.co/WebRutMuisca/DefConsultaEstadoRUT.faces", 4)

        print("🧠 Calculando posición del checkbox en base al botón 'Buscar'...")
        boton = driver.find_element(By.ID, "vistaConsultaEstadoRUT:formConsultaEstadoRUT:btnBuscar")
        location = boton.location

        #x = location["x"] + 100
        #y = location["y"] + 120
        x = location["x"] + 40
        y = location["y"] + 80

        time.sleep(1)
        pyautogui.moveTo(x, y, duration=0.5)  # ⬅️ Movimiento rápido
        pyautogui.click()
        print(f"✅ Clic en checkbox estimado en x={x}, y={y}")

        time.sleep(1)

        campo_nit = driver.find_element(By.ID, "vistaConsultaEstadoRUT:formConsultaEstadoRUT:numNit")
        campo_nit.clear()
        campo_nit.send_keys(nit)
        campo_nit.send_keys(Keys.RETURN)
        print("✅ NIT enviado")

        try:
            driver.wait_for_element("#vistaConsultaEstadoRUT\\:formConsultaEstadoRUT\\:razonSocial", timeout=18)
            print("✅ Se cargó la página con respuesta")

        except Exception:
            # Buscar si se muestra el mensaje "No está inscrito en el RUT"
            if "No está inscrito en el RUT" in driver.get_page_source():
                print("ℹ️ El NIT no está inscrito en el RUT")
                guardar_resultado({
                    "NIT": nit,
                    "razon_social": "No inscrito",
                    "fecha": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "estado": "No está inscrito en el RUT"
                })
                return
            else:
                raise TimeoutError("⏰ Resultado no cargado")

        # Si llegó aquí, se cargaron los datos correctamente
        resultado_img = "resultado_dian.png"
        driver.save_screenshot(resultado_img)

        print("📦 Extrayendo datos del DOM...")
        razon_social = driver.find_element(By.ID, "vistaConsultaEstadoRUT:formConsultaEstadoRUT:razonSocial").text.strip()
        estado = driver.find_element(By.ID, "vistaConsultaEstadoRUT:formConsultaEstadoRUT:estado").text.strip()

        fecha = time.strftime("%Y-%m-%d %H:%M:%S")

        guardar_resultado({
            "NIT": nit,
            "razon_social": razon_social.replace("S.A.S.", "SAS"),
            "fecha": fecha,
            "estado": estado
        })

        print("✅ Extracción completada")

    except Exception as e:
        print(f"❌ Error durante navegación o extracción: {e}")
        if driver:
            try:
                driver.save_screenshot("error_screenshot.png")
            except:
                pass
        raise e

    finally:
        if driver:
            driver.quit()


def guardar_resultado(data: dict):
    with open("resultado_dian.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main(nit: str):
    MAX_INTENTOS = 3
    for intento in range(1, MAX_INTENTOS + 1):
        try:
            print(f"\n🔁 Intento {intento} de {MAX_INTENTOS}")
            intentar_consulta(nit)
            break
        except TimeoutError as e:
            print(f"⏳ Timeout (intento #{intento}): {e}")
            if intento == MAX_INTENTOS:
                guardar_resultado({
                    "NIT": nit,
                    "razon_social": "Error",
                    "fecha": time.strftime("%Y-%m-%d %H:%M:%S").replace(" ", "").replace(":", ""),
                    "estado": "Se intentó 3 veces sin éxito. Captcha no resuelto"
                })
        except Exception as e:
            print(f"🚨 Error inesperado en intento #{intento}: {e}")
            if intento == MAX_INTENTOS:
                guardar_resultado({
                    "NIT": nit,
                    "razon_social": "Error",
                    "fecha": time.strftime("%Y-%m-%d %H:%M:%S").replace(" ", "").replace(":", ""),
                    "estado": "Se intentó 3 veces sin éxito. Captcha no resuelto"
                })


if __name__ == "__main__":
    main("901192159")
