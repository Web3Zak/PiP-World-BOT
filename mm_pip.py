import re
import time
from typing import Optional
from playwright.async_api import Page

URL = "https://mm.pip.world/?lang=en"

# MENU
X_MENU_OPEN = "/html/body/div[1]/div[1]/div[1]/div[3]"
X_MENU_CLOSE = "/html/body/div[1]/div[1]/div[1]/div[3]/div[1]"

# TASKS
TASK_CHECK_IN_DESC = "Log in daily and claim your XP reward."
TASK_SHARE_DESC = "Share your daily Mavericks Trio card on X."

# LEADERBOARD
X_LEADERBOARD_MENU = "/html/body/div[1]/div[1]/div[2]/div[1]/ul/li[4]"
X_LEADERBOARD_TAB = "/html/body/div[1]/div[1]/div[3]/div/div[1]/button[2]"
X_LEADERBOARD_XP = "/html/body/div[1]/div[1]/div[3]/div/div[2]/table/tbody/tr[101]/td[1]"

# PROFILE
X_PROFILE_MENU = "/html/body/div[1]/div[1]/div[2]/div[1]/ul/li[5]"
X_BADGES = "/html/body/div[1]/div[1]/div[3]/div/div[1]/div/div[2]/div[2]/div/div/div[1]"

# STATS

def parse_int(text: Optional[str]) -> int:
    if not text:
        return 0
    digits = re.findall(r"\d+", text)
    if not digits:
        return 0
    return int("".join(digits))

# UTILS

async def wait_text_change(page: Page, xpath: str, old_text: str, timeout=60000):
    await page.wait_for_function(
        """(xpath, oldText) => {
            const el = document.evaluate(
                xpath,
                document,
                null,
                XPathResult.FIRST_ORDERED_NODE_TYPE,
                null
            ).singleNodeValue;
            return el && el.innerText.trim() !== oldText;
        }""",
        xpath,
        old_text,
        timeout=timeout
    )

# helpers

async def find_task_card(page: Page, task_desc: str, timeout: int = 30000) -> dict:
    await page.wait_for_function(
        f"""
        () => Array.from(document.querySelectorAll("span.task-desc"))
            .some(s => s.innerText.trim() === "{task_desc}")
        """,
        timeout=timeout
    )

    return await page.evaluate(
        f"""
        () => {{
            const span = Array.from(document.querySelectorAll("span.task-desc"))
                .find(s => s.innerText.trim() === "{task_desc}");
            if (!span) return {{ found: false }};

            const card = span.closest(".task-card");
            if (!card) return {{ found: false }};

            const btn = card.querySelector("button");
            const streakEl = card.querySelector("span.task-streak");

            return {{
                found: true,
                button_text: btn ? btn.innerText.trim() : null,
                button_disabled: btn ? btn.disabled : null,
                has_streak: Boolean(streakEl && streakEl.innerText.trim()),
                streak_text: streakEl ? streakEl.innerText.trim() : null
            }};
        }}
        """
    )


async def click_task_button(page: Page, task_desc: str) -> bool:
    return await page.evaluate(
        f"""
        () => {{
            const span = Array.from(document.querySelectorAll("span.task-desc"))
                .find(s => s.innerText.trim() === "{task_desc}");
            if (!span) return false;

            const card = span.closest(".task-card");
            if (!card) return false;

            const btn = card.querySelector("button");
            if (!btn || btn.disabled) return false;

            btn.click();
            return true;
        }}
        """
    )


# tasks

async def handle_check_in(page: Page):
    info = await find_task_card(page, TASK_CHECK_IN_DESC)
    if info["found"] and not info["button_disabled"]:
        await click_task_button(page, TASK_CHECK_IN_DESC)


async def wait_and_click_claim(page: Page, timeout: int = 120000) -> bool:
    try:
        await page.wait_for_function(
            f"""
            () => {{
                const span = Array.from(document.querySelectorAll("span.task-desc"))
                    .find(s => s.innerText.trim() === "{TASK_SHARE_DESC}");
                if (!span) return false;

                const card = span.closest(".task-card");
                if (!card) return false;

                const btn = card.querySelector("button");
                return btn && !btn.disabled && btn.innerText.trim() === "CLAIM";
            }}
            """,
            timeout=timeout
        )
    except Exception:
        return False

    return await click_task_button(page, TASK_SHARE_DESC)


# stats

async def get_current_streak(page: Page) -> int | None:
    info = await find_task_card(page, TASK_CHECK_IN_DESC)
    if not info["found"] or not info["has_streak"]:
        return None
    return parse_int(info["streak_text"])


async def wait_for_valid_streak(page: Page, min_value=1, timeout_sec=20) -> int | None:
    deadline = time.monotonic() + timeout_sec
    last_value = None

    while time.monotonic() < deadline:
        value = await get_current_streak(page)
        last_value = value

        if value is not None and value >= min_value:
            return value

        await page.wait_for_timeout(1000)

    return last_value


async def get_xp_from_leaderboard(page: Page) -> int:
    await page.click(f"xpath={X_LEADERBOARD_MENU}")
    await page.wait_for_load_state("domcontentloaded")
    await page.click(f"xpath={X_LEADERBOARD_TAB}")

    xp_text = await (
        await page.wait_for_selector(f"xpath={X_LEADERBOARD_XP}", timeout=15000)
    ).inner_text()

    return parse_int(xp_text)


async def get_badges(page: Page) -> int:
    await page.click(f"xpath={X_PROFILE_MENU}")
    await page.wait_for_load_state("domcontentloaded")
    await page.wait_for_timeout(1000)

    badges_text = await (
        await page.wait_for_selector(f"xpath={X_BADGES}", timeout=15000)
    ).inner_text()

    return parse_int(badges_text)


# MAIN ENTRY

async def run_mm_pip(page: Page, log):
    await page.goto(URL, wait_until="domcontentloaded")

    try:
        await page.click(f"xpath={X_MENU_OPEN}")
    except Exception:
        pass

    await handle_check_in(page)

    share_info = await find_task_card(page, TASK_SHARE_DESC)
    claim_performed = False

    if share_info["found"] and not share_info["button_disabled"]:
        await click_task_button(page, TASK_SHARE_DESC)
        await page.wait_for_timeout(1000)
        await page.click(f"xpath={X_MENU_OPEN}")
        claim_performed = await wait_and_click_claim(page)

    streak = await wait_for_valid_streak(page)

    try:
        await page.click(f"xpath={X_MENU_CLOSE}")
    except Exception:
        pass

    xp = await get_xp_from_leaderboard(page)
    badges = await get_badges(page)

    return {
        "current_streak": streak,
        "xp": xp,
        "badges": badges,
    }
