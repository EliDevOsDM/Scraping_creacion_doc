import os
import win32com.client
from app.playwright_facade import PlaywrightFacade


class AutomationService:
    """
    Encapsulates the automation logic for the SGDEA website.
    """

    def __init__(self, bot: PlaywrightFacade):
        self.bot = bot

    async def login(self, user: str, password: str):
        """
        Realiza únicamente el login en el portal SGDEA.
        """
        url = ("https://sgdea.mineducacion.gov.co/TMS.Solution.MENGESDOC/"
               "(SwgUB8M7)/CR/es//Home/Corporativo")
        await self.bot.go_to(url)

        await self.bot.send_text("//form[@id='formlogin']//input[@placeholder='Usuario']", user)
        await self.bot.send_text("//form[@id='formlogin']//input[@placeholder='Clave']", password)
        await self.bot.click(
            "//form[@id='formlogin']//button[text()='INICIAR SESIÓN']",
            delay_after=5,
            timeout=20000
        )

    async def create_communication_correos(self, data: dict, excel_path: str, word_path: str, base_dir: str):
        """
        Crea una comunicación de salida para cada registro de correos.
        """
        
        print(f"------------ Iniciando creación Comunicación: {data.get('Nombre entidad', '')} ------------")

        # 1. Ir al menú crear
        await self.bot.click(
            "//div[@id='main-menu']//ul/li/a[@title='Crear']",
            delay_after=2,
            timeout=20000
        )

        # 2. Ir al submenú Comunicación de salida
        await self.bot.click(
            "//div[@id='main-menu']//ul/li/a[@title='Crear']/../ul/li/"
            "a[@title='Comunicación de salida']",
            delay_after=10,
            timeout=20000
        )

        # 3. Entrar al iframe
        frame_selector = "//iframe[@id='frameVerDocumentos']"
        frame = await self.bot.get_frame_locator(frame_selector)

        # 4. Click en destinatario
        print("Destinatario...")
        await self.bot.click(
            "//div[@id='TmsmenuForm']/a[@id='DestinatarioExterno']",
            parent=frame,
            delay_after=2,
            timeout=20000
        )

        # 5. Click en nuevo destinatario
        await self.bot.click(
            "//div[@id='TMSDialogModalContentDialog']/form//button[contains(normalize-space(), "
            "'Nuevo destinatario')]",
            parent=frame,
            delay_before=5,
            timeout=20000
        )

        # 6. Click en tipo destinatario
        tipo_dest = str(data.get('Tipo Destinatario', 'Persona Natural'))
        await self.bot.select_dropdown_option(
            "//div[@id='DestinatariosContainer']//select[contains(@class, "
            "'input-tipodestinatario')]",
            option_text=tipo_dest,
            parent=frame,
        )

        # 7. Click en profesion
        profesion_input = (
            "//div[@id='DestinatariosContainer']//label[text()='Título/Profesión']"
            "/..//input[@placeholder='Diligencie por favor...']"
        )
        await self.bot.send_text(profesion_input, str(data.get('Titulo/Profesion', '')), parent=frame)

        await self.bot.click(
            f"(//div[@id='DestinatariosContainer']//div[@class='ms-res-ctn dropdown-menu']"
            f"/div[contains(normalize-space(), '{str(data.get('Titulo/Profesion', ''))}')])[1]",
            parent=frame,
            delay_after=1,
            timeout=20000
        )

        # 8. Escribir nombre (primer destinatario; la página puede tener varias filas)
        await self.bot.send_text(
            "//div[@id='DestinatariosContainer']"
            "//input[@name='ListaDestinatarios[0].NomUsuarioDestino']",
            str(data.get('Destinatario', '')),
            parent=frame,
            index=1,
        )

        # 8.1. Cargo
        await self.bot.send_text(
            "//div[@id='DestinatariosContainer']"
            "//input[@name='ListaDestinatarios[0].NomCargo']",
            data.get('Cargo', ''),
            parent=frame,
            index=1,
        )

        # 8.2. Empresa / entidad
        await self.bot.send_text(
            "//div[@id='DestinatariosContainer']"
            "//input[@name='ListaDestinatarios[0].NomEmpresaDestino']",
            data.get('Nombre entidad', ''),
            parent=frame,
            index=1,
        )

        # 9. Click en Medio de envío
        await self.bot.click(
            f"//div[@id='DestinatariosContainer']//label[text()='Medio de envío']"
            f"/../div/div[contains(normalize-space(), '{str(data.get('Medio de envio', ''))}')]",
            parent=frame,
            delay_after=1,
            timeout=20000
        )

        # 10. Escribir email
        correo_key = next((k for k in data.keys() if 'Correo electr' in k), 'Correo electrónico')
        await self.bot.send_text(
            "//div[@id='DestinatariosContainer']"
            "//input[@name='ListaDestinatarios[0].CorreoElectronico']",
            str(data.get(correo_key, '')),
            parent=frame,
            index=1,
        )

        # 11. Click en guardar
        await self.bot.click(
            "//div[@id='TMSDialogModalDialog']"
            "//div[@class='modal-footer']/button[text()='Guardar']",
            parent=frame,
            delay_after=5,
            timeout=20000
        )

        # 12. Click en asunto
        print("Asunto...")
        await self.bot.click(
            "//div[@id='TmsmenuForm']/a[@id='Asunto']",
            parent=frame,
            delay_after=1,
            timeout=20000
        )
        await self.bot.send_text(
            "//div[@id='TMSDialogModalContentDialog']//form[@id='FormAsunto']"
            "//textarea[@id='asunto']",
            str(data.get('Asunto', '')),
            parent=frame,
            delay_random_a=0,
            delay_random_b=0,
        )
        await self.bot.click(
            "//div[@id='TMSDialogModalDialog']"
            "//div[@class='modal-footer']/button[text()='Guardar']",
            parent=frame,
            delay_after=5,
            timeout=20000
        )

        # 13. Firmante
        print("Firmante...")
        await self.bot.click(
            "//div[@id='TmsmenuForm']/a[@id='Remitente']",
            parent=frame,
            delay_after=2,
            timeout=20000
        )

        await self.bot.click(
            "//div[@id='TMSDialogModalContentDialog']//div[@id='AutocompleteUsuario']",
            parent=frame
        )
        await self.bot.keypress("End")
        await self.bot.keypress("Backspace")
        await self.bot.page.keyboard.type(str(data.get('Firmante', '')), delay=100)

        # Buscar Cargo.1 (si está duplicado)
        cargo_firmante_key = 'Cargo.1' if 'Cargo.1' in data else 'Cargo'
        cargo_firmante = str(data.get(cargo_firmante_key, ''))

        if cargo_firmante:
            try:
                cargo_selector = (
                    f"(//div[@id='TMSDialogModalContentDialog']//div[@id='AutocompleteUsuario']"
                    f"/div[@class='ms-res-ctn dropdown-menu']"
                    f"/div[contains(@data-json, 'NomCargo\":\"{cargo_firmante}')])[1]"
                )
                await self.bot.click(cargo_selector, parent=frame, delay_after=1, timeout=10000)
            except Exception:
                try:
                    cargo_selector = (
                        f"(//div[@id='TMSDialogModalContentDialog']//div[@id='AutocompleteUsuario']"
                        f"/div[@class='ms-res-ctn dropdown-menu']/div)[1]"
                    )
                    await self.bot.click(cargo_selector, parent=frame, delay_after=1, timeout=5000)
                except Exception:
                    pass
        else:
            try:
                cargo_selector = (
                    f"(//div[@id='TMSDialogModalContentDialog']//div[@id='AutocompleteUsuario']"
                    f"/div[@class='ms-res-ctn dropdown-menu']/div)[1]"
                )
                await self.bot.click(cargo_selector, parent=frame, delay_after=1, timeout=5000)
            except Exception:
                pass


        await self.bot.click(
            "//div[@id='TMSDialogModalDialog']//div[@class='modal-footer']/button[text()='Guardar']",
            parent=frame,
            delay_after=20,
            timeout=20000
        )

        # 14. Click en saludo y copiar plantilla word generada
        print("Insertar en documento (Word Generado)...")
        await self.bot.click(
            "//div[@id='EditorRich_View']//div[@class='dxreRow']/span[text()='Saludo,']",
            parent=frame,
            delay_after=1,
            timeout=20000
        )
        await self.bot.keypress("Home")
        for _ in range(8):
            await self.bot.keypress("Delete")

        try:
            # 1. Usar Dispatch en lugar de DispatchEx
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            word.DisplayAlerts = False

            # 2. Abrir el documento
            doc = word.Documents.Open(os.path.abspath(word_path))
            
            # Pausa breve para asegurar que el documento cargue en Office 365
            await self.bot.page.wait_for_timeout(500) 
            
            # 3. Copiar el contenido
            doc.Content.Copy()
            
            # Pausa para que el portapapeles de Windows registre el contenido enriquecido
            await self.bot.page.wait_for_timeout(500)

            # 4. PEGAR MIENTRAS WORD SIGUE ABIERTO
            await self.bot.page.keyboard.press("Control+V")
            await self.bot.page.wait_for_timeout(5000)

            # 5. AHORA SÍ, CERRAR WORD
            doc.Close(False)
            word.Quit()

        except Exception as e:
            print(f"Error al leer/pegar plantilla word generada: {e}")
            await self.bot.page.keyboard.type(str(data.get('Saludo', 'Hola')))

        # 15. Click en revisor
        print("Revisor...")
        await self.bot.click(
            "//div[@id='TmsmenuForm']/a[@id='AprobadoresCicloAdhoc']",
            parent=frame,
            delay_after=1,
            timeout=20000
        )
        await self.bot.send_text(
            "//div[@id='TMSDialogModalContentDialog']//form[@id='FormDestinatario']"
            "//input[@id='FiltroUsuario']",
            data['Revisores ciclo adHoc'],
            parent=frame
        )
        await self.bot.click(
            f"(//div[@id='TMSDialogModalContentDialog']//form[@id='FormDestinatario']"
            f"//div[@id='TBodyResultado']//div[contains(normalize-space(.),'{data['Revisores ciclo adHoc']}')]"
            f"/parent::div/div[contains(normalize-space(.),'{data['Cargo Revisor']}')])[1]",
            parent=frame,
            delay_after=1,
            timeout=20000
        )
        await self.bot.click(
            "//div[@id='TMSDialogModalDialog']"
            "//div[@class='modal-footer']/button[text()='Guardar']",
            parent=frame,
            delay_after=5,
            timeout=20000
        )

        # 15. Click en anexos (solo subir anexo generado excel)
        print("Anexos...")
        await self.bot.click(
            "//div[@id='TmsmenuForm']/a[@id='Anexo']",
            parent=frame,
            delay_after=1,
            timeout=20000
        )

        anexo_input = "//div[@id='TMSDialogModalContentDialog']//form//input[@id='anexo']"
        await self.bot.clear_input(anexo_input, parent=frame)
        await self.bot.send_text(anexo_input, "1", parent=frame, timeout=20000)
        await self.bot.click(
            "//div[@id='TMSDialogModalDialog']"
            "//div[@class='modal-footer']/button[text()='Guardar']",
            parent=frame,
            delay_after=5,
            timeout=20000
        )

        # 16. Salir del iframe y subir archivo
        print("Subiendo excel generado...")
        upload_selector = "//div[@id='divAnexosRespuesta']//input[@id='anexosRespuesta']"
        await self.bot.page.locator(upload_selector).set_input_files([os.path.abspath(excel_path)])

        await self.bot.click(
            "//div[@id='divAnexosRespuesta']//a[@title='Subir archivos seleccionados']",
            delay_after=10,
            timeout=20000
        )

        # 17. Entrar al iframe para iniciar ciclo
        frame = await self.bot.get_frame_locator(frame_selector)

        await self.bot.click(
            "//a[contains(normalize-space(), 'Inicio proceso aprobación')]",
            parent=frame,
            delay_before=5,
            delay_after=5,
            timeout=20000
        )
        
        # Opcional: Escribir comentario si existe el textarea
        await self.bot.send_text(
            "//div[@id='TMSDialogModalContentDialog']//textarea",
            "Para revisión y firma",
            parent=frame,
            timeout=10000
        )

        # 18. Confirmar inicio de ciclo
        async def trigger_inicio_ciclo():
            await self.bot.click(
                "//div[@id='TMSDialogModalDialog' and contains(@class,'show')]"
                "//div[@class='modal-footer']/button[text()='Inicio de Ciclo']",  # Cerrar
                parent=frame,
                delay_after=5,
                timeout=20000
            )

        xhr_response = await self.bot.get_xhr_response(
            url_filter="GestionarCicloAprobacion",
            trigger_action=trigger_inicio_ciclo
        )

        resp_data = xhr_response.get("response", {})
        id_documento = resp_data.get("IdDocumento")
        pagina = resp_data.get("Pagina")

        solicitud_id = f"CS-26-{id_documento}.{pagina}" if id_documento and pagina else "(No generó id_documento)"
        print(f"Solicitud generada: {solicitud_id}")

        print("------------ Fin creación de Comunicación de Salida (Correos) ------------")
        return solicitud_id
