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

    async def consultar_processo(self, page: Page, numero: str) -> List[Dict]:
        logger.info("Consultando processo: %s", numero)
        await page.goto(TARGET_URL, wait_until="networkidle")
        logger.info("Página carregada: %s", TARGET_URL)
        input_selector = '#numeroProcesso'
        await page.wait_for_selector(input_selector, state="visible", timeout=10000)
        await page.fill(input_selector, '')
        await page.fill(input_selector, numero)
        logger.info("Campo preenchido com: %s", numero)
        btn_selector = '#btnPesquisar'
        await page.click(btn_selector)
        logger.info("Clique em 'Pesquisar' realizado.")
        try:
            await page.wait_for_selector('#tabelaResultados[style*="display: table"]', state="attached", timeout=15000)
            logger.info("Tabela de resultados visível.")
        except PlaywrightTimeout:
            no_results = await page.query_selector('#noResults[style*="display: block"]')
            if no_results:
                logger.warning("Nenhum resultado encontrado para: %s", numero)
                return []
            raise RuntimeError("Timeout aguardando resultado da consulta.")
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
                logger.info("Processo extraído: %s", data['numero_processo'])
        return resultados

    async def buscar_varios(self, numeros: List[str]) -> List[Dict]:
        page = await self.context.new_page()
        todos_resultados = []
        try:
            for numero in numeros:
                resultados = await self.consultar_processo(page, numero)
                todos_resultados.extend(resultados)
                await asyncio.sleep(0.5)
        finally:
            await page.close()
        return todos_resultados
