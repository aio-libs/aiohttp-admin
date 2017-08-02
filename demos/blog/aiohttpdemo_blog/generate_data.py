import asyncio
import pathlib

import psycopg2
from faker import Factory
from sqlalchemy.schema import CreateTable, DropTable

import db
from utils import init_postgres


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


async def delete_tables(pg, tables):
    async with pg.acquire() as conn:
        for table in reversed(tables):
            drop_expr = DropTable(table)
            try:
                await conn.execute(drop_expr)
            except psycopg2.ProgrammingError:
                pass


async def prepare_tables(pg):
    tables = [db.post, db.tag, db.comment]
    await delete_tables(pg, tables)
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


async def generate_tags(pg, rows, fake):
    values = []
    for i in range(rows):
        values.append({
            'name': fake.word()[:10],
            'published': bool(i % 2),
        })
    ids = await insert_data(pg, db.tag, values)
    return ids


async def generate_posts(pg, rows, fake, tag_ids):
    values = []
    for i in range(rows):
        values.append({
            'title': fake.sentence(nb_words=7)[:200],
            'teaser': fake.paragraph(nb_sentences=4)[:500],
            'body': fake.text(max_nb_chars=2000),
            'views': i % 1000,
            'average_note': i % 0.1,
            'pictures': {'first': {'name': fake.word(),
                                   'url': fake.image_url()}},
            'published_at': fake.iso8601(),
            'tags': [tag_ids[(i + j) % len(tag_ids)] for j in range(7)],
            'category': fake.word()[:50],
            'subcategory': fake.word()[:50],
            'backlinks': {'date': fake.iso8601(),
                          'url': fake.uri()},
        })

    ids = await insert_data(pg, db.post, values)
    return ids


async def generate_comments(pg, rows, fake, post_ids):
    values = []
    for post_id in post_ids:
        for i in range(rows):
            values.append({
                'post_id': post_id,
                'body': fake.text(max_nb_chars=500),
                'created_at': fake.iso8601(),
                'author': {'name': fake.name(),
                           'email': fake.email()},
            })

    await insert_data(pg, db.comment, values)


async def init(loop):
    print("Generating Fake Data")
    pg = await init_postgres(conf['postgres'], loop)
    fake = Factory.create()
    fake.seed(1234)
    await prepare_tables(pg)

    rows = 1000

    tag_ids = await generate_tags(pg, 500, fake)
    post_ids = await generate_posts(pg, rows, fake, tag_ids)
    await generate_comments(pg, 25, fake, post_ids)


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init(loop))


if __name__ == "__main__":
    main()
