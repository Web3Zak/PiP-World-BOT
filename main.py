import json
import asyncio
from playwright.async_api import async_playwright

from ads import ADSClient
from logger import setup_logger, ProfileLoggerAdapter
from mm_pip import run_mm_pip


async def main():
    # load config 
    with open("config.json", encoding="utf-8") as f:
        accounts = json.load(f)

    if not isinstance(accounts, list):
        raise ValueError("config.json must be a list of accounts")

    logger = setup_logger()
    ads = ADSClient()

    async with async_playwright() as p:
        for account in accounts:
            browser = None
            context = None
            page = None

            account_id = account["id"]
            account_name = account.get("name", account_id)

            log = ProfileLoggerAdapter(logger, {"profile": account_name})
            log.info("Starting profile")

            try:
                # start ADS profile
                ws = await ads.start_profile(account_id)

                browser = await p.chromium.connect_over_cdp(ws)
                context = browser.contexts[0]
                page = await context.new_page()

                # run project
                stats = await run_mm_pip(page, log)

                log.info(
                    "Stats:\n"
                    f"Streak: {stats.get('current_streak')}\n"
                    f"XP Rank: {stats.get('xp')}\n"
                    f"Badges: {stats.get('badges')}"
                )

            except Exception as e:
                log.error(f"ERROR: {e}")

            finally:
                # browser shutdown
                try:
                    if page:
                        await page.close()
                except Exception:
                    pass

                try:
                    if context:
                        await context.close()
                except Exception:
                    pass

                try:
                    if browser:
                        await browser.close()
                except Exception:
                    pass

                # stop ADS profile
                try:
                    await ads.stop_profile(account_id)
                except Exception:
                    pass

                log.info("Profile finished")

    # close ADS client
    await ads.close()


if __name__ == "__main__":
    asyncio.run(main())
