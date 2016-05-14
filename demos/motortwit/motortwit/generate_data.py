import asyncio
import random

from bson import ObjectId
from faker import Factory

from motortwit.main import init_mongo
from motortwit.security import generate_password_hash


conf = {"host": "127.0.0.1",
        "port": 8080,
        "mongo": {
            "host": "127.0.0.1",
            "port": 27017,
            "database": "motortwit",
            "max_pool_size": 1}
        }


# TODO: validate using trafarets before insert

async def insert_data(collection, values):
    await collection.insert(values)
    return values

async def generate_users(mongo, rows, fake):
    values = []
    pw_hash = generate_password_hash(b'123456')
    for i in range(rows):
        values.append({
            '_id': ObjectId(),
            'username': fake.word()[:50].lower(),
            'email': fake.email(),
            'pw_hash': pw_hash,
        })
    users = await insert_data(mongo, values)
    return users


async def generate_messages(mongo, rows, fake, users):
    values = []
    for user in users:
        for i in range(rows):
            values.append({
                '_id': ObjectId(),
                'author_id': user['_id'],
                'email': user['email'],
                'username': user['username'],
                'text': fake.text(max_nb_chars=140),
                'pub_date': fake.iso8601(),
            })

    ids = await insert_data(mongo, values)
    return ids


async def generate_followers(mongo, rows, fake, user_ids):
    values = []
    for user_id in user_ids:
        values = []
        for i in range(rows):
            values.append({
                '_id': ObjectId(),
                'who': random.choice(user_ids),
                'whom': user_id,
            })

    await insert_data(mongo, values)


async def prepare_coolections(*collections):
    for coll in collections:
        await coll.drop()


async def init(loop):
    print("Generating Fake Data")
    mongo = await init_mongo(conf['mongo'], loop)
    fake = Factory.create()
    fake.seed(1234)

    await prepare_coolections(mongo.user, mongo.message, mongo.follwer)

    users = await generate_users(mongo.user, 100, fake)
    await generate_messages(mongo.message, 50, fake, users)
    user_ids = [v['_id'] for v in users]
    await generate_followers(mongo.follwer, 5, fake, user_ids)


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init(loop))


if __name__ == "__main__":
    main()
