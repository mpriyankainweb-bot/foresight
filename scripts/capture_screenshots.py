import asyncio
import os

from playwright.async_api import async_playwright

os.makedirs("/app/screenshots", exist_ok=True)
os.makedirs("/home/jules/verification", exist_ok=True)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 1000})
        page = await context.new_page()

        print("1. Capturing Landing Page...")
        await page.goto("http://localhost:3000/", wait_until="domcontentloaded")
        await page.wait_for_timeout(1000)
        await page.screenshot(path="/app/screenshots/01_landing_page.png", full_page=True)

        print("2. Capturing Deploy Check Page...")
        await page.goto("http://localhost:3000/check", wait_until="domcontentloaded")
        await page.wait_for_timeout(1000)
        btn = page.get_by_text("Run Friday 5:40 PM Scenario")
        await btn.click()
        await page.wait_for_timeout(2500)
        await page.screenshot(path="/app/screenshots/02_deploy_check_page.png", full_page=True)
        await page.screenshot(path="/home/jules/verification/verification.png", full_page=True)

        print("3. Capturing Memory Inspector Drawer...")
        inspector_btn = page.get_by_text("Memory Inspector").first
        await inspector_btn.click()
        await page.wait_for_timeout(1500)
        await page.screenshot(path="/app/screenshots/03_memory_inspector_drawer.png", full_page=False)

        await page.keyboard.press("Escape")
        await page.wait_for_timeout(500)

        print("4. Capturing Incident Mode Page...")
        await page.goto("http://localhost:3000/incident", wait_until="domcontentloaded")
        await page.wait_for_timeout(1000)
        inc_btn = page.get_by_text("Search Incident Memory for Fixes").first
        await inc_btn.click()
        await page.wait_for_timeout(2500)
        await page.screenshot(path="/app/screenshots/04_incident_mode_page.png", full_page=True)

        print("5. Capturing Insights / Learning Curve Page...")
        await page.goto("http://localhost:3000/insights", wait_until="domcontentloaded")
        await page.wait_for_timeout(2500)
        await page.screenshot(path="/app/screenshots/05_insights_page.png", full_page=True)

        print("6. Capturing Integrate Page...")
        await page.goto("http://localhost:3000/integrate", wait_until="domcontentloaded")
        await page.wait_for_timeout(1000)
        gen_btn = page.get_by_text("Generate New X-API-Key").first
        await gen_btn.click()
        await page.wait_for_timeout(1000)
        await page.screenshot(path="/app/screenshots/06_integrate_page.png", full_page=True)

        print("7. Capturing Demo Control Page...")
        await page.goto("http://localhost:3000/demo", wait_until="domcontentloaded")
        await page.wait_for_timeout(1000)
        replay_btn = page.get_by_text("Run Demo Replay").first
        await replay_btn.click()
        await page.wait_for_timeout(3500)
        await page.screenshot(path="/app/screenshots/07_demo_control_page.png", full_page=True)

        await browser.close()
        print("All screenshots captured successfully!")

if __name__ == "__main__":
    asyncio.run(main())
