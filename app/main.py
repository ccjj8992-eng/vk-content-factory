import os
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .database import (
    init_db,
    add_post,
    get_pending_posts,
    get_all_posts
)

from .scheduler import (
    start_scheduler,
    process_posts
)

from .vk import (
    get_group_info,
    VKError
)


app = FastAPI(
    title="VK Content Factory",
    version="1.0.0"
)


class PostCreate(BaseModel):

    text: str = Field(
        min_length=1,
        max_length=10000
    )

    scheduled_at: str


@app.on_event("startup")
def startup():

    init_db()

    start_scheduler()

    print(
        "VK Content Factory v1.0 started"
    )


@app.get("/")
def root():

    return {
        "app": "VK Content Factory",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
def health():

    return {
        "status": "ok"
    }


@app.get("/config")
def config():

    return {
        "vk_group_id": os.getenv(
            "VK_GROUP_ID"
        ),
        "timezone": os.getenv(
            "TIMEZONE",
            "Europe/Moscow"
        ),
        "vk_api_version": os.getenv(
            "VK_API_VERSION",
            "5.199"
        )
    }


@app.post("/posts")
def create_post(post: PostCreate):

    try:

        datetime.fromisoformat(
            post.scheduled_at
        )

    except ValueError:

        raise HTTPException(
            status_code=400,
            detail=(
                "scheduled_at должен быть "
                "в формате "
                "YYYY-MM-DDTHH:MM:SS"
            )
        )

    post_id = add_post(
        post.text,
        post.scheduled_at
    )

    return {
        "success": True,
        "post_id": post_id
    }


@app.get("/posts")
def posts():

    return {
        "posts": get_all_posts()
    }


@app.get("/posts/pending")
def pending_posts():

    return {
        "posts": get_pending_posts()
    }


@app.post("/scheduler/run")
def run_scheduler():

    process_posts()

    return {
        "success": True,
        "message": "Проверка очереди выполнена"
    }


@app.get("/vk/test")
def vk_test():

    try:

        result = get_group_info()

        return {
            "success": True,
            "response": result
        }

    except VKError as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
