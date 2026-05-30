import uuid
import time
import re
import asyncio
import os
import random
import datetime
import logging
from typing import Any, Awaitable, Callable, Literal, Optional, Union
from playwright.async_api import Playwright, Page, Locator, FrameLocator, ElementHandle, Frame


class PlaywrightFacade:
    """
    Una clase Facade para simplificar y reutilizar las interacciones con Playwright,
    encapsulando esperas, comportamiento humano simulado y manejo de errores.
    """

    def __init__(self, page: Page, screenshot_path: str, download_path: str, screenshot_on_action: bool = False):
        self.page = page
        self.screenshot_path = screenshot_path
        self.download_path = download_path
        self.screenshot_on_action = screenshot_on_action

    @classmethod
    async def initialize(cls, playwright: Playwright, screenshot_path: str, download_path: str,
                         headless: bool = False, slow_mo: int = 50,
                         user_agent: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                         viewport: dict = {'width': 1920, 'height': 1080},
                         locale: str = 'es-PE', timezone_id: str = 'America/Lima',
                         screenshot_on_action: bool = False, proxy: Optional[dict] = None,
                         is_camoufox: bool = False, camoufox_params: Optional[dict] = {}):
        """Inicializa el navegador, el contexto y la página, y devuelve una instancia del Facade."""
        logging.info('Inicializando el navegador...')
        if is_camoufox:
            from camoufox.async_api import AsyncCamoufox
            from browserforge.fingerprints import Screen
            constrains = Screen(max_width=1920, max_height=1080)
            browser = await AsyncCamoufox(
                os=('windows', 'macos', 'linux'),
                screen=constrains,
                humanize=camoufox_params.get('humanize', True),
                window=(1920, 1080),
                locale=locale,
                geoip=True,
                proxy=proxy
            ).__aenter__()
            context = await browser.new_context(viewport=viewport)
            page = await context.new_page()
        else:
            launch_options = {
                'executable_path': os.environ.get('BROWSER_EXECUTABLE'),
                'headless': headless,
                'slow_mo': slow_mo
            }
            browser = await playwright.chromium.launch(**launch_options)
            context = await browser.new_context(
                user_agent=user_agent,
                viewport=viewport,
                locale=locale,
                timezone_id=timezone_id,
                accept_downloads=True,
                proxy=proxy,
                permissions=['clipboard-read', 'clipboard-write']
            )
            page = await context.new_page()
            await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return cls(page, screenshot_path, download_path, screenshot_on_action)

    def _get_locator(self, selector: str,
                     parent: Optional[Union[Page, FrameLocator, Locator, ElementHandle]] = None) -> Locator:
        """Método centralizado para obtener un localizador,
ya sea desde la página o un elemento padre."""
        scope = parent if parent else self.page
        return scope.locator(selector)

    async def go_to(self, url: str, **kwargs: Any):
        """
Navega a una URL específica. Acepta argumentos de palabra clave para page.goto().
Por ejemplo: timeout, wait_until.
"""
        logging.info(f'Navegando a: {url} con argumentos {kwargs}')
        await self.page.goto(url, **kwargs)

    async def _click_core(self, locator: Locator, timeout: int = 20000, human_delay: bool = True,
                          force: bool = False,
                          state: Literal['attached', 'detached', 'visible', 'hidden'] = 'visible',
                          hover_delay_range: tuple[float, float] = (0.2, 0.7),
                          click_delay_range: tuple[float, float] = (0.4, 1.1)):
        """Lógica central de clic sobre un Locator ya resuelto."""
        if not force:
            await locator.wait_for(state=state, timeout=timeout)
        if human_delay and not force:
            await locator.hover()
            await asyncio.sleep(random.uniform(*hover_delay_range))
        await locator.click(force=force)
        if human_delay and not force:
            await asyncio.sleep(random.uniform(*click_delay_range))

    async def _click_by_index(self, selector: str, index: int,
                              parent: Optional[Union[Page, FrameLocator, Locator, ElementHandle]] = None,
                              **kwargs):
        """Resuelve el Locator en la posición indicada y lo pasa a _click_core."""
        if index <= 0:
            raise ValueError('La posición debe ser un número positivo (basado en 1).')
        locator = self._get_locator(selector, parent).nth(index - 1)
        await self._click_core(locator, **kwargs)

    async def _click_by_text(self, selector: str, text_to_find: str,
                             parent: Optional[Union[Page, FrameLocator, Locator, ElementHandle, Frame]] = None,
                             timeout: int = 10000, **kwargs):
        """Busca un elemento por texto y lo pasa a _click_core."""
        elements = self._get_locator(selector, parent)
        count = await elements.count()
        for i in range(count):
            text = await elements.nth(i).inner_text()
            if text.strip() == text_to_find:
                locator = elements.nth(i)
                await self._click_core(locator, timeout=timeout, **kwargs)
                logging.info(f"Click realizado en el elemento con texto '{text_to_find}'")
                return
        raise Exception(f"No se encontró un elemento con texto '{text_to_find}'")

    async def click(self, selector: str, index: Optional[int] = None, text_to_find: Optional[str] = None,
                    parent: Optional[Union[Page, FrameLocator, Locator, ElementHandle, Frame]] = None,
                    delay_before: float = 0, delay_after: float = 0, **kwargs):
        """
Método público:
- Si pasas index → clic en esa posición.
- Si pasas text_to_find → busca el elemento con ese texto y hace clic.
- Si no pasas nada → clic en el primer elemento.
- delay_before: Pausa en segundos antes de la acción.
- delay_after: Pausa en segundos después de la acción.
Maneja errores, screenshot y logging.
"""
        try:
            if delay_before > 0:
                await asyncio.sleep(delay_before)
            if text_to_find is not None:
                await self._click_by_text(selector, text_to_find, parent, **kwargs)
            elif index is not None:
                await self._click_by_index(selector, index, parent, **kwargs)
            else:
                locator = self._get_locator(selector, parent).first
                await self._click_core(locator, **kwargs)
            logging.info(f"Click realizado en '{selector}' (index={index}, text={text_to_find})")
            if delay_after > 0:
                await asyncio.sleep(delay_after)
            if self.screenshot_on_action:
                await self.take_screenshot(f'click_{selector}', prefix='action')
        except Exception as e:
            filename = 'click_' + '_'.join(filter(None, [
                selector,
                f'idx{index}' if index else None,
                f'text{text_to_find}' if text_to_find else None
            ]))
            await self.take_screenshot(filename, prefix='error')
            logging.error(f'Error al hacer clic: {e}')
            raise

    async def send_text(self, selector: str, text: str,
                        parent: Optional[Union[Page, FrameLocator, Locator, ElementHandle]] = None,
                        timeout: int = 10000, delay_before: float = 0, delay_after: float = 0,
                        delay_random_a: int = 10, delay_random_b: int = 100,
                        index: Optional[int] = None):
        """
Localiza un campo de entrada, hace clic en él y escribe texto de forma secuencial
para simular la escritura humana.
:param index: Posición 1-based si el selector coincide con varios elementos (como en click).
:param delay_before: Pausa en segundos antes de la acción.
:param delay_after: Pausa en segundos después de la acción.
"""
        try:
            if delay_before > 0:
                await asyncio.sleep(delay_before)
            logging.info(f'Escribiendo en: {selector}')
            locator = self._get_locator(selector, parent)
            if index is not None:
                if index <= 0:
                    raise ValueError('La posición debe ser un número positivo (basado en 1).')
                target = locator.nth(index - 1)
            else:
                target = locator.first
            await target.wait_for(state='visible', timeout=timeout)
            await target.click()
            await target.press_sequentially(text, delay=random.randint(delay_random_a, delay_random_b))
            if delay_after > 0:
                await asyncio.sleep(delay_after)
            if self.screenshot_on_action:
                await self.take_screenshot(f'send_text_{selector}', prefix='action')
        except Exception as e:
            logging.error(f"Error al escribir en '{selector}': {e}", exc_info=True)
            await self.take_screenshot(f'send_text_{selector}', prefix='error')
            raise

    async def clear_input(self, selector: str,
                          parent: Optional[Union[Page, FrameLocator, Locator, ElementHandle]] = None,
                          timeout: int = 10000, index: Optional[int] = None):
        """
Limpia un campo de entrada editable.
:param selector: El selector del campo de entrada.
:param parent: El elemento padre opcional donde buscar.
:param timeout: Tiempo de espera para que el elemento sea visible.
:param index: Posición 1-based si el selector coincide con varios elementos.
"""
        try:
            logging.info(f'Limpiando el campo: {selector}')
            locator = self._get_locator(selector, parent)
            if index is not None:
                if index <= 0:
                    raise ValueError('La posición debe ser un número positivo (basado en 1).')
                target = locator.nth(index - 1)
            else:
                target = locator.first
            await target.wait_for(state='visible', timeout=timeout)
            await target.clear()
            if self.screenshot_on_action:
                await self.take_screenshot(f'clear_input_{selector}', prefix='action')
        except Exception as e:
            logging.error(f"Error al limpiar el campo '{selector}': {e}", exc_info=True)
            await self.take_screenshot(f'clear_input_{selector}', prefix='error')
            raise

    async def keypress(self, key: str, delay_before: float = 0, delay_after: float = 0):
        """
Simula la presión de una tecla del teclado.
:param key: La tecla a presionar (ej: "Enter", "End", "Tab").
:param delay_after: Tiempo de espera en segundos después de la acción.
"""
        try:
            if delay_before > 0:
                await asyncio.sleep(delay_before)
            logging.info(f'Presionando tecla: {key}')
            await self.page.keyboard.press(key)
            if delay_after > 0:
                await asyncio.sleep(delay_after)
            if self.screenshot_on_action:
                await self.take_screenshot(f'keypress_{key}', prefix='action')
        except Exception as e:
            logging.error(f"Error al presionar la tecla '{key}': {e}", exc_info=True)
            await self.take_screenshot(f'keypress_{key}', prefix='error')
            raise

    async def inner_text(self, selector: str,
                         parent: Optional[Union[Page, FrameLocator, Locator, ElementHandle]] = None,
                         *, list_selector: Optional[str] = None, position: Optional[int] = None,
                         shadow_selector: Optional[str] = None, timeout: int = 10000) -> str:
        """
Devuelve el texto de un elemento. Si se especifican `list_selector`, `position`
y `shadow_selector`, obtiene el texto dentro del shadow DOM.
"""
        try:
            logging.info(f"Obteniendo texto de: selector='{selector}', list='{list_selector}', position={position}, shadow='{shadow_selector}'")
            target = None
            if list_selector and position and shadow_selector:
                target = await self._get_shadow_locator(list_selector, position, shadow_selector, parent)
            else:
                target = self._get_locator(selector, parent)
            await target.wait_for(state='visible', timeout=timeout)
            text = await target.inner_text()
            return text.strip()
        except Exception as e:
            logging.error(f'Error al obtener texto: {e}', exc_info=True)
            await self.take_screenshot(f"get_text_{selector or list_selector.replace('/', '_').replace('=', '')}")
            raise

    async def inner_html(self, selector: str,
                         parent: Optional[Union[Page, FrameLocator, Locator, ElementHandle]] = None,
                         *, list_selector: Optional[str] = None, position: Optional[int] = None,
                         shadow_selector: Optional[str] = None, timeout: int = 10000) -> str:
        """
Devuelve el HTML interno de un elemento. Si se especifican `list_selector`, `position`
y `shadow_selector`, obtiene el HTML dentro del shadow DOM.
"""
        try:
            logging.info(f"Obteniendo HTML de: selector='{selector}', list='{list_selector}', position={position}, shadow='{shadow_selector}'")
            target = None
            if list_selector and position and shadow_selector:
                target = await self._get_shadow_locator(list_selector, position, shadow_selector, parent)
            else:
                target = self._get_locator(selector, parent)
            await target.wait_for(state='visible', timeout=timeout)
            return await target.inner_html()
        except Exception as e:
            logging.error(f'Error al obtener HTML: {e}', exc_info=True)
            await self.take_screenshot(f"get_html_{selector or list_selector.replace('/', '_').replace('=', '')}", prefix='error')
            raise

    async def get_attribute(self, selector: str, attribute_name: str,
                            parent: Optional[Union[Page, FrameLocator, Locator, ElementHandle]] = None,
                            timeout: int = 10000) -> Optional[str]:
        """
Obtiene el valor de un atributo de un elemento.
"""
        try:
            logging.info(f"Obteniendo atributo '{attribute_name}' de: {selector}")
            target = self._get_locator(selector, parent)
            await target.first.wait_for(state='attached', timeout=timeout)
            return await target.first.get_attribute(attribute_name)
        except Exception as e:
            logging.error(f"Error al obtener atributo '{attribute_name}' de '{selector}': {e}", exc_info=True)
            await self.take_screenshot(f"get_attr_{attribute_name}_{selector.replace('/', '_').replace('=', '')}", prefix='error')
            raise

    async def _get_shadow_locator(self, list_selector: str, position: int, shadow_selector: str,
                                  parent: Optional[Union[Page, FrameLocator]] = None):
        """
Retorna un Locator apuntando al elemento dentro del shadow DOM.
"""
        if position <= 0:
            raise ValueError('La posición debe ser un número positivo (basado en 1).')
        elements = self._get_locator(list_selector, parent)
        target_element = elements.nth(position - 1)
        return target_element.locator(shadow_selector)

    async def get_frame_locator(self, selector: str,
                                parent: Optional[Union[Page, FrameLocator, Locator, ElementHandle]] = None,
                                timeout: int = 20000) -> FrameLocator:
        """
Espera a que un iframe (dentro de la página o de un frame padre) esté adjunto
al DOM y devuelve su localizador.
"""
        try:
            logging.info(f'Esperando y localizando iframe: {selector}')
            scope = parent if parent else self.page
            await scope.locator(selector).wait_for(state='attached', timeout=timeout)
            return scope.frame_locator(selector)
        except Exception as e:
            logging.error(f"Error al localizar el iframe '{selector}': {e}", exc_info=True)
            await self.take_screenshot(f'get_frame_{selector}', prefix='error')
            raise

    async def wait_for_element(self, selector: str,
                               parent: Optional[Union[Page, FrameLocator, Locator, ElementHandle]] = None,
                               state: Literal['attached', 'detached', 'visible', 'hidden'] = 'visible',
                               timeout: int = 20000):
        """
Espera a que un elemento cumpla con un estado específico (ej. 'visible').
"""
        try:
            logging.info(f'Esperando por el elemento: {selector}')
            target = self._get_locator(selector, parent)
            await target.first.wait_for(state=state, timeout=timeout)
            logging.info(f"Elemento '{selector}' encontrado.")
        except Exception as e:
            logging.error(f"Error esperando por el elemento '{selector}': {e}", exc_info=True)
            await self.take_screenshot(f'wait_for_{selector}', prefix='error')
            raise

    async def download_file(self, trigger_action: Callable[[], Awaitable[Any]]) -> str:
        """
Maneja la descarga de un archivo.
:param trigger_action: Una función async que, al ser llamada, inicia la descarga.
"""
        logging.info('Iniciando proceso de descarga...')
        try:
            async with self.page.expect_download() as download_info:
                await trigger_action()
            download = await download_info.value
            original_name = download.suggested_filename
            _, ext = os.path.splitext(original_name)
            timestamp = int(time.time())
            unique_id = uuid.uuid4().hex[:6]
            final_name = f'file_{timestamp}_{unique_id}{ext}'
            final_download_path = os.path.join(self.download_path, final_name)
            await download.save_as(final_download_path)
            logging.info(f'Descarga completada. Archivo guardado en: {final_download_path}')
            return final_download_path
        except Exception as e:
            logging.error(f'Error durante el proceso de descarga: {e}', exc_info=True)
            await self.take_screenshot('descarga', prefix='error')
            raise

    async def get_xhr_response(self, url_filter: str, trigger_action: Callable[[], Awaitable[Any]],
                               is_json: bool = True, timeout: float = 30000) -> dict:
        """
Intercepta una respuesta XHR/Fetch específica y devuelve:
- payload enviado
- respuesta (json o texto)
"""
        logging.info(f'Esperando respuesta XHR que contenga: {url_filter}')
        try:
            async with self.page.expect_response(lambda response: url_filter in response.url, timeout=timeout) as response_info:
                await trigger_action()
            response = await response_info.value
            request = response.request
            logging.info(f'XHR capturado exitosamente: {response.url}')
            payload = None
            try:
                payload = request.post_data_json
            except Exception:
                payload = request.post_data
            if is_json:
                response_data = await response.json()
            else:
                response_data = await response.text()
            return {
                'url': response.url,
                'method': request.method,
                'payload': payload,
                'response': response_data,
                'headers': request.headers
            }
        except Exception as e:
            logging.error(f'Error al interceptar XHR: {e}', exc_info=True)
            await self.take_screenshot('xhr_capture', prefix='error')
            raise

    async def expect_popup(self, trigger_action: Callable[[], Awaitable[Any]]) -> 'PlaywrightFacade':
        """
Intercepta la apertura de una nueva pestaña tras ejecutar trigger_action
y devuelve una nueva instancia de PlaywrightFacade asociada a esa pestaña.
"""
        logging.info('Esperando apertura de nueva pestaña...')
        try:
            async with self.page.context.expect_page() as page_info:
                await trigger_action()
            new_page = await page_info.value
            await new_page.wait_for_load_state()
            logging.info(f'Nueva pestaña capturada: {new_page.url}')
            return PlaywrightFacade(new_page, self.screenshot_path, self.download_path, self.screenshot_on_action)
        except Exception as e:
            logging.error(f'Error al capturar popup: {e}', exc_info=True)
            await self.take_screenshot('popup_capture', prefix='error')
            raise

    async def take_screenshot(self, name: str, prefix: Optional[str] = None) -> str:
        """
Toma una captura de pantalla con un nombre descriptivo.
:param name: Nombre base para el archivo.
:param prefix: Prefijo opcional (ej. 'error', 'success').
:return: La ruta completa del archivo guardado.
"""
        safe_name = re.sub('[^A-Za-z0-9_-]', '_', name)
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        filename_parts = [timestamp, prefix, safe_name]
        filename = '_'.join(filter(None, filename_parts)) + '.png'
        path = os.path.join(self.screenshot_path, filename)
        await self.page.screenshot(path=path, timeout=10000)
        logging.info(f'Captura de pantalla guardada en: {path}')
        return path

    async def close_page(self):
        """Cierra la página (pestaña) actual sin cerrar el navegador completo."""
        logging.info('Cerrando pestaña actual...')
        await self.page.close()

    async def close(self):
        """Cierra el contexto y el navegador."""
        logging.info('Cerrando el navegador.')
        await self.page.context.close()
        await self.page.context.browser.close()

    async def get_frame_by_position(self, selector: str, position: int,
                                    parent: Optional[Union[Page, FrameLocator, Locator]] = None,
                                    shadow_host_selector: Optional[str] = None,
                                    timeout: int = 20000) -> Frame:
        """
Localiza todos los iframes que coinciden con el selector y devuelve el localizador
del iframe en la posición especificada (basado en 1).
Si el iframe está dentro de un Shadow DOM, se puede proporcionar un `shadow_host_selector`.

:param selector: El selector CSS o XPath para localizar los iframes.
:param position: La posición del iframe en la lista (1 para el primero, 2 para el segundo)
:param parent: El elemento padre opcional donde buscar.
:param shadow_host_selector: Selector para elemento host del Shadow DOM que contiene iframe.
:param timeout: Tiempo de espera para encontrar el iframe.
"""
        try:
            log_msg = f'Esperando y localizando iframe en posición {position}, selector: {selector}'
            if shadow_host_selector:
                log_msg += f' dentro del shadow host: {shadow_host_selector}'
            logging.info(log_msg)
            if position <= 0:
                raise ValueError('La posición debe ser un número positivo (basado en 1).')
            scope = parent if parent else self.page
            if shadow_host_selector:
                iframe_locator = scope.locator(shadow_host_selector).locator(selector)
            else:
                iframe_locator = scope.locator(selector)
            iframe_handle = await iframe_locator.nth(position - 1).element_handle(timeout=timeout)
            if not iframe_handle:
                raise Exception('No se pudo obtener el element_handle del iframe.')
            frame = await iframe_handle.content_frame()
            if not frame:
                raise Exception('No se pudo obtener el content_frame del iframe.')
            return frame
        except Exception as e:
            logging.error(f"Error al localizar el iframe en posición {position} de '{selector}': {e}", exc_info=True)
            await self.take_screenshot(f"get_frame_pos_{position}_{selector.replace('#', '')}", prefix='error')
            raise

    async def select_dropdown_option(self, selector: str, option_text: Optional[str] = None,
                                     option_value: Optional[str] = None,
                                     parent: Optional[Union[Page, FrameLocator, Locator, ElementHandle]] = None,
                                     timeout: int = 10000):
        """
Selecciona una opción de un <select> ya sea por texto visible (label) o por value.
"""
        try:
            logging.info(f'Seleccionando opción en {selector}')
            target = self._get_locator(selector, parent)
            await target.wait_for(state='visible', timeout=timeout)
            if option_text:
                await target.select_option(label=option_text)
            elif option_value:
                await target.select_option(value=option_value)
            else:
                raise ValueError('Debes pasar option_text o option_value.')
            if self.screenshot_on_action:
                await self.take_screenshot(f'select_option_{selector}', prefix='action')
        except Exception as e:
            logging.error(f"Error al seleccionar opción en '{selector}': {e}", exc_info=True)
            await self.take_screenshot(f'select_option_{selector}', prefix='error')
            raise

    async def hover(self, selector: str,
                    parent: Optional[Union[Page, FrameLocator, Locator, ElementHandle]] = None,
                    timeout: int = 20000, delay_before: float = 0, delay_after: float = 0):
        """
Realiza hover sobre un elemento.
Útil para desplegar menús, tooltips o subopciones.
"""
        try:
            if delay_before > 0:
                await asyncio.sleep(delay_before)
            logging.info(f'Haciendo hover sobre {selector}')
            target = self._get_locator(selector, parent)
            await target.wait_for(state='visible', timeout=timeout)
            await target.hover()
            if delay_after > 0:
                await asyncio.sleep(delay_before)
            if self.screenshot_on_action:
                await self.take_screenshot(f'hover_{selector}', prefix='action')
        except Exception as e:
            logging.error(f"Error al hacer hover en '{selector}': {e}", exc_info=True)
            await self.take_screenshot(f'hover_{selector}', prefix='error')
            raise
