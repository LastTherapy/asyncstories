from typing import Optional, List, Dict
import asyncio
import aiohttp
from fastapi import FastAPI, status, BackgroundTasks
import uvicorn
from pydantic import BaseModel, HttpUrl
from uuid import uuid4, UUID
from fastapi.responses import JSONResponse

app = FastAPI()

# Модель задачи
class Task(BaseModel):
    urls: List[HttpUrl]
    status: str
    id: UUID
    result: Optional[Dict[HttpUrl, int]] = None  # Заменили на None по умолчанию

# Хранилище задач
tasks: Dict[UUID, Task] = {}

# Эндпоинт для создания задачи
@app.post('/api/v1/tasks/', status_code=status.HTTP_201_CREATED)
def get_urls(urls: List[HttpUrl], background_tasks: BackgroundTasks):
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

# Асинхронная функция для выполнения GET-запроса
async def fetch_url(session: aiohttp.ClientSession, url: HttpUrl):
    async with session.get(str(url)) as response:
        return response.status

# Асинхронная функция для обработки результата
async def make_result(task: Task):
    async with aiohttp.ClientSession() as session:
        result = await asyncio.gather(*[fetch_url(session, url) for url in task.urls])
        task.result = dict(zip(task.urls, result))  # Связываем URL с результатом
        task.status = "ready"

# Запуск сервера
if __name__ == "__main__":
    uvicorn.run("server:app", host='127.0.0.1', port=8888)
