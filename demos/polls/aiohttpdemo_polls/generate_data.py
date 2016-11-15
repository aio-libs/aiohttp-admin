import asyncio
import pathlib

import aiohttpdemo_polls.db as db
import psycopg2
from faker import Factory

from aiohttpdemo_polls.utils import init_postgres
from sqlalchemy.schema import CreateTable, DropTable


PROJ_ROOT = pathlib.Path(__file__).parent.parent

conf = {"host": "127.0.0.1",
        "port": 8080,
        "postgres": {
            "database": "aiohttp_admin",
            "user": "aiohttp_admin_user",
            "password": "mysecretpassword",
            "host": "127.0.0.1",
            "port": 5432,
            "minsize": 1,
            "maxsize": 5}
        }


async def preapre_tables(pg):
    tables = [db.question, db.choice]
    async with pg.acquire() as conn:
        for table in reversed(tables):
            drop_expr = DropTable(table)
            try:
                await conn.execute(drop_expr)
            except psycopg2.ProgrammingError:
                pass

    async with pg.acquire() as conn:
        for table in tables:
            create_expr = CreateTable(table)
            await conn.execute(create_expr)


async def insert_data(pg, table, values):
    async with pg.acquire() as conn:
        query = table.insert().values(values).returning(table.c.id)
        cursor = await conn.execute(query)
        resp = await cursor.fetchall()
    return [r[0] for r in resp]


async def generate_questions(pg, rows, fake):
    values = []
    for i in range(rows):
        values.append({
            'question_text': fake.sentence(nb_words=10)[:200],
            'pub_date': fake.iso8601(),
        })
    ids = await insert_data(pg, db.question, values)
    return ids


async def generate_choices(pg, rows, fake, question_ids):
    values = []
    for q_id in question_ids:
        for i in range(rows):
            values.append({
                'question_id': q_id,
                'choice_text': fake.sentence(nb_words=10)[:200],
                'votes': i})
    ids = await insert_data(pg, db.choice, values)
    return ids


async def init(loop):
    print("Generating Fake Data")
    pg = await init_postgres(conf['postgres'], loop)
    fake = Factory.create()
    fake.seed(1234)
    await preapre_tables(pg)

    quiestion_num = 1000
    choices_num = 5
    question_ids = await generate_questions(pg, quiestion_num, fake)
    await generate_choices(pg, choices_num, fake, question_ids)

    pg.close()
    await pg.wait_closed()


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init(loop))


if __name__ == "__main__":
    main()
