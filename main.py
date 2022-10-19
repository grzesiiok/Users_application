from fastapi import FastAPI, Query, HTTPException, Response, Request, BackgroundTasks
from pydantic import BaseModel, Field
from pydantic import Field as field
import uvicorn
from sqlmodel import SQLModel, create_engine, Field, Session,select
from typing import Optional
from fastapi_redis_cache import FastApiRedisCache, cache
from fastapi.encoders import jsonable_encoder
import aio_pika
import asyncio
import json
import redis

con_str = "postgresql://postgres:password@postgres:5432/postgres"
REDIS_CONNECTION_STRING = "redis://redis:6379"
# con_str = "postgresql://postgres:password@localhost:5432/postgres"
# REDIS_CONNECTION_STRING = "redis://localhost:6379"
engine = create_engine(con_str, echo=True)

async def publish(message):
    connection = await aio_pika.connect('amqp://guest:guest@rabbit')
    # connection = await aio_pika.connect('amqp://guest:guest@localhost')
    async with connection:
        queue_name = "status_queue"
        channel = await connection.channel()
        await channel.declare_queue(queue_name, auto_delete=True)

        msg = aio_pika.Message(body=json.dumps(message.dict()).encode())
        await channel.default_exchange.publish(msg, routing_key=queue_name)

async def consume(queue_name="status_queue"):
    connection = await aio_pika.connect('amqp://guest:guest@rabbit')
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=5)
        queue = await channel.declare_queue(queue_name, auto_delete=True)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    print(message.body)

def cache_invalidation():
    r = redis.Redis(host='redis', port=6379)
    # r = redis.Redis(host='localhost', port=6379)
    for key in r.scan_iter("users_cache:*"):
        r.delete(key)

class UserEvent(BaseModel):
    action: str
    user: dict

def create_tables():
    SQLModel.metadata.create_all(engine)

app = FastAPI(
    title="Users Service",
    description="""Users Service is an application to manage users identities :)
               It allows to create, get, filter, update and delete users accounts.
               \nSome useful links""",
    contact={
        "name": "The Users Service repository",
        "url": "https://training-git.lohika.com/cap-python-internship/python-internship-poland/users-service",
    },
)

@app.on_event('startup')
def on_startup():
    create_tables()
    redis_cache= FastApiRedisCache().init(host_url=REDIS_CONNECTION_STRING,prefix='users_cache',
                                          response_header="X-Users-Cache",ignore_arg_types=[Response, Request,Session])

responses = {
    400: {"description": "invalid parameter received"},
    404: {"description": "item not found"},
    405: {"description": "method not allowed"},
    500: {"description": "internal server error"},
    503: {"description": "service unavailable"},
}

responses4post = {
    400: {"description": "invalid parameter received"},
    404: {"description": "item not found"},
    405: {"description": "method not allowed"},
    500: {"description": "internal server error"},
    503: {"description": "service unavailable"},
}


class User(SQLModel, table=True):
    __tablename__ = 'Users'
    __table_args__ = {'extend_existing': True}
    id: int = Field(primary_key=True, default=None)
    countryCode: Optional[str]
    dateOfBirth: Optional[str]
    firstName: Optional[str]
    lastName: Optional[str]
    nickname: Optional[str]
    gender: Optional[str]
    email: Optional[str]

class UserWithoutId(BaseModel):
    countryCode: str | None = field(example="UA")
    dateOfBirth: str | None = field(
        example="24-08-1991"
    )  # Could be Optional[date] = None
    firstName: str | None = field(example="James")
    lastName: str | None = field(example="Morrison")
    nickname: str | None = field(example="b_psychedelic")
    gender: str | None = field(example="male")
    email: str | None = field(example="will.be.psychedelic@gmail.com")



@app.get("/v1/users", response_model=list[User])
@cache(expire=60)
async def Search_and_filter_user(
    ids: int = Query(default=None, description="user id", example="1"),
    nickname: str
    | None = Query(default=None, description="user nickname", example="b_psychodelic"),
    email: str
    | None = Query(default=None, description="user email", example="lol@gmail.com"),
):
    nones = sum(x is None for x in [ids, nickname, email])
    print(nones)

    if nones >= 2:
        with Session(engine) as session:
            if ids:
                users = session.exec(select(User).where(ids == User.id)).all()
            elif nickname:
                users = session.exec(select(User).where(nickname == User.nickname)).all()
            elif email:
                users = session.exec(select(User).where(email == User.email)).all()
            elif nones == 3:
                users = session.exec(select(User)).all()
            if not users:
                raise HTTPException(status_code=404, detail=f"Cannot find user")
            else:
                return jsonable_encoder(users)
    else:
        raise HTTPException(status_code=405, detail=f"method not allowed")



@app.post('/v1/users')
async def create_user(user: User, background_tsk: BackgroundTasks):
    with Session(engine) as session:
        if session.exec(select(User).where(user.id == User.id)).all() == [] and session.exec(select(User).where(user.email == User.email)).all() == [] and session.exec(select(User).where(user.nickname == User.nickname)).all() == []:
            session.add(user)
            session.commit()
            session.refresh(user)
            useraction = UserEvent(action="created", user=user.dict())
            background_tsk.add_task(publish, useraction)
            cache_invalidation()
        else:
            useraction = UserEvent(action="not created", user=user.dict())
            await publish(useraction)
            raise HTTPException(status_code=422, detail=f"User exists")
    return user



@app.get("/v1/users/{id}", responses=responses)
@cache(expire=60)
def get_user_info(id: int | None = Query(default="1")):
    with Session(engine) as session:
        users = session.exec(select(User).where(id == User.id)).all()
    if not users:
        raise HTTPException(status_code=404, detail=f"Cannot find user")
    else:
        cache_invalidation()
        return jsonable_encoder(users)

@app.put("/v1/users/{id}", responses=responses)
async def update_user_info(usr: UserWithoutId, id: int, background_tsk:BackgroundTasks):
    with Session(engine) as session:
        statement = select(User).where(id == User.id)
        results = session.exec(statement).all()
    if results:
        results = session.exec(statement).one()
        usr = usr.dict(exclude_unset=True)
        for key, value in usr.items():
            setattr(results, key, value)
        session.add(results)
        session.commit()
        session.refresh(results)
        useraction = UserEvent(action="updated", user={"id":id})
        background_tsk.add_task(publish, useraction)
        cache_invalidation()
        return results
    else:
        useraction = UserEvent(action="User not found", user={"id":id})
        await publish(useraction)
        raise HTTPException(status_code=404, detail=f'User not found')


@app.delete("/v1/users/{id}", responses=responses)
async def delete_user(id: int, background_tsk:BackgroundTasks):
    with Session(engine) as session:
        if session.exec(select(User).where(id == User.id)).all():
            statement = select(User).where(id == User.id)
            results = session.exec(statement).one()
            session.delete(results)
            session.commit()

            statement = select(User).where(User.id == id)
            results = session.exec(statement).first()
            if results is None:
                useraction = UserEvent(action="deleted", user={"id": id})
                background_tsk.add_task(publish, useraction)
                cache_invalidation()
                return {"message": f"user {id} has been deleted"}
        else:
            useraction = UserEvent(action="User not found", user={"id": id})
            await publish(useraction)
            raise HTTPException(status_code=404, detail=f"Cannot find user")



if __name__ == "__main__":
    """It's for debugging only."""
    uvicorn.run("main:app", host="127.0.0.1", port=9000)

