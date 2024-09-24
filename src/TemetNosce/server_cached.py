from contextlib import asynccontextmanager
from typing import Optional, List, Dict
import asyncio
import aiohttp
from fastapi import FastAPI, status, BackgroundTasks
import uvicorn
from pydantic import BaseModel, HttpUrl
from uuid import uuid4, UUID
from fastapi.responses import JSONResponse
from urllib.parse import urlparse
import redis.asyncio as redis
from redis.asyncio.client import Redis
import logging

CACHE_CLEANUP_INTERVAL = 180
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_):
    clean_task = asyncio.create_task(cleanup_cache())
    logger.info("Запущен сборщик кэша.")
    yield
    clean_task.cancel()
    logger.info("Остановлен сборщик кэша.")


app = FastAPI(lifespan=lifespan)



async def get_redis() -> Redis:
    return redis.from_url("redis://localhost")


class Task(BaseModel):
    urls: List[HttpUrl]
    status: str
    id: UUID
    result: Optional[Dict[HttpUrl, int]] = None  # Заменили на None по умолчанию


tasks: Dict[UUID, Task] = {}


@app.post('/api/v1/tasks/', status_code=status.HTTP_201_CREATED)
def get_urls(urls: List[HttpUrl], background_tasks: BackgroundTasks):
    print(f"Got request: {urls}", flush=True)
    id = uuid4()
    t = Task(urls=urls, status="running", id=id)
    tasks[id] = t
    # Добавляем асинхронную задачу в фоновый процесс
    background_tasks.add_task(make_result, t)
    return t


@app.get('/api/v1/tasks/{task_id}')
def get_task(task_id: UUID):

    task = tasks.get(task_id)
    if not task:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Task not found"})
    return task

@app.get('/api/v1/stats/{domain}')
def get_metrics(domain: str):
    cache: Redis = get_redis()



async def fetch_url(session: aiohttp.ClientSession, url: HttpUrl):
    str_url = str(url)
    base: str = urlparse(str_url).netloc
    cache: Redis = await get_redis()

    await cache.incr(f"req:{base}")
    num_requests = await cache.get(f"req:{base}")
    if num_requests:
        num_requests = int(num_requests.decode("utf-8"))
    logger.info(f"Запрос к {str_url}.")
    logger.info(f"Всего {num_requests} запросов к {base}.")
    if await cache.exists(str_url):
        return int(await cache.get(str_url))
    else:
        async with session.get(str(url)) as response:
            await cache.set(str_url, response.status, ex=600)
            return response.status


async def make_result(task: Task):
    async with aiohttp.ClientSession() as session:
        result = await asyncio.gather(*[fetch_url(session, url) for url in task.urls])
        task.result = dict(zip(task.urls, result))  # Связываем URL с результатом
        task.status = "ready"


async def cleanup_cache():
    redis_client = await get_redis()
    logger.info(f"Запущена корутина для очистки кэша каждые {CACHE_CLEANUP_INTERVAL} секунд.")
    try:
        while True:
            # все записи, только потому что это демонстративный проект
            keys = await redis_client.keys("*")
            if keys:
                logger.info(f"Найдено {len(keys)} кэшированных записей для очистки.")
                await redis_client.delete(*keys)
                logger.info(f"Удалены {len(keys)} кэшированные записи.")
            else:
                logger.info("Нет кэшированных записей для очистки. Идем спать.")
            await asyncio.sleep(CACHE_CLEANUP_INTERVAL)
    except Exception as e:
        pass
        logger.error(f"Ошибка при очистке кэша: {e}")
    finally:
        await redis_client.close()


if __name__ == "__main__":
    print("Server started listening on port: 8888")
    uvicorn.run("server_cached:app", host='127.0.0.1', port=8888, log_level=logging.INFO)
