import asyncio
import pathlib
import psycopg2
from faker import Factory

import aiohttpdemo_polls.db as db
from aiohttpdemo_polls.utils import init_postgres
from sqlalchemy.schema import CreateTable, DropTable, DropConstraint


PROJ_ROOT = pathlib.Path(__file__).parent.parent

conf = {"host": "127.0.0.1",
        "port": 8080,
        "postgres": {
            "database": "aiohttp_admin_polls",
            "user": "aiohttp_admin",
            "password": "mysecretpassword",
            "host": "192.168.99.100",
            "port": 5432,
            "minsize": 1,
            "maxsize": 5}
        }


async def preapre_tables(pg):
    tables = [db.choice, db.question]
    async with pg.acquire() as conn:
        for table in tables:
            drop_expr = DropTable(table)
            create_expr = CreateTable(table)
            for c in table.constraints:
                dc = DropConstraint(c)
                try:
                    await conn.execute(dc)
                except psycopg2.ProgrammingError:
                    pass
            try:
                await conn.execute(drop_expr)
            except psycopg2.ProgrammingError:
                pass
            await conn.execute(create_expr)


async def init(loop):
    print("Generating Fake Data")
    pg = await init_postgres(conf['postgres'], loop)
    fake = Factory.create()
    fake.seed(1234)
    await preapre_tables(pg)

    values = []
    rows = 100000
    for i in range(rows):
        values.append({
            'question_text': fake.sentence(nb_words=10)[:200],
            'pub_date': fake.iso8601(),
        })

    query = db.question.insert().values(values)
    async with pg.acquire() as conn:
        await conn.execute(query)

    async with pg.acquire() as conn:
        query = db.question.select()
        resp = await conn.execute(query)
        values = []
        for q in list(resp):
            for i in range(5):
                values.append({
                    'question_id': q['id'],
                    'choice_text': fake.sentence(nb_words=10)[:200],
                    'votes': i})

        await conn.execute(db.choice.insert().values(values))

    pg.close()
    await pg.wait_closed()


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init(loop))

if __name__ == "__main__":
    main()
