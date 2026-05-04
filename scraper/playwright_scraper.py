import asyncio
import logging
from typing import List, Dict
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeout
from config import TARGET_URL, HEADLESS, SLOW_MO

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TribunalScraper:
    def __init__(self, headless: bool = HEADLESS, slow_mo: int = SLOW_MO):
        self.headless = headless
        self.slow_mo = slow_mo
        self.browser = None
        self.context = None
        self.playwright = None

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        logger.info("Browser iniciado (headless=%s, slow_mo=%dms)", self.headless, self.slow_mo)

    async def stop(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser encerrado.")

    async def _setup_page(self) -> Page:
        """Cria uma nova página com bloqueio de recursos desnecessários para performance."""
        page = await self.context.new_page()
        
        # Sênior: Bloqueio de Imagens, CSS, Fontes e Media para máxima velocidade
        await page.route("**/*", lambda route: route.abort() 
                         if route.request.resource_type in ["image", "stylesheet", "font", "media"] 
                         else route.continue_())
        
        return page

    async def consultar_processo(self, page: Page, numero: str) -> List[Dict]:
        """Consulta um único processo de forma otimizada."""
        try:
            # Ir direto para a página e esperar apenas o necessário
            await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=30000)
            
            input_selector = '#numeroProcesso'
            await page.wait_for_selector(input_selector, state="visible", timeout=10000)
            await page.fill(input_selector, numero)
            
            btn_selector = '#btnPesquisar'
            await page.click(btn_selector)
            
            # Aguarda a tabela ou a mensagem de erro
            try:
                await page.wait_for_selector('#tbodyResultados tr', state="attached", timeout=5000)
            except PlaywrightTimeout:
                # Checa se é mensagem de 'não encontrado'
                no_results = await page.query_selector('#noResults')
                if no_results and await no_results.is_visible():
                    logger.warning("Nenhum resultado encontrado: %s", numero)
                    return []
                return []

            rows = await page.query_selector_all('#tbodyResultados tr')
            resultados = []
            for row in rows:
                cells = await row.query_selector_all('td')
                if len(cells) >= 6:
                    data = {
                        "numero_processo": (await cells[0].inner_text()).strip(),
                        "classe": (await cells[1].inner_text()).strip(),
                        "assunto": (await cells[2].inner_text()).strip(),
                        "vara": (await cells[3].inner_text()).strip(),
                        "juiz": (await cells[4].inner_text()).strip(),
                        "ultima_movimentacao": (await cells[5].inner_text()).strip(),
                    }
                    resultados.append(data)
            return resultados
        except Exception as e:
            logger.error("Falha ao consultar %s: %s", numero, str(e))
            return []

    async def worker(self, queue: asyncio.Queue, results_callback):
        """Worker assíncrono que processa itens da fila continuamente."""
        page = await self._setup_page()
        try:
            while True:
                numero = await queue.get()
                if numero is None: # Sinal de parada
                    queue.task_done()
                    break
                
                logger.info("Worker processando: %s", numero)
                dados = await self.consultar_processo(page, numero)
                if dados:
                    await results_callback(dados)
                
                queue.task_done()
                # Pequeno respiro para o servidor alvo não bloquear
                await asyncio.sleep(0.1)
        finally:
            await page.close()
