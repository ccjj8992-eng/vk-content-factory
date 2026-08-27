import os
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from .database import (
    get_due_posts,
    mark_error,
    mark_published
)

from .vk import publish_text_post


scheduler = BackgroundScheduler(
    timezone=os.getenv(
        "TIMEZONE",
        "Europe/Moscow"
    )
)


def process_posts():
    now = datetime.now(
        timezone.utc
    ).replace(
        tzinfo=None
    ).isoformat()

    posts = get_due_posts(now)

    for post in posts:

        try:
            vk_post_id = publish_text_post(
                post["text"]
            )

            mark_published(
                post["id"],
                vk_post_id
            )

            print(
                f"[OK] Post #{post['id']} "
                f"published to VK. "
                f"VK ID: {vk_post_id}"
            )

        except Exception as error:

            mark_error(
                post["id"],
                str(error)
            )

            print(
                f"[ERROR] Post #{post['id']}: "
                f"{error}"
            )


def start_scheduler():

    scheduler.add_job(
        process_posts,
        "interval",
        minutes=1,
        id="vk_publisher",
        replace_existing=True
    )

    scheduler.start()

    print(
        "VK Content Factory scheduler started"
    )
