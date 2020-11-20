import math
import aerospike

from aerospike import predicates as p
from aerospike import exception as ex

from flask import current_app

aerospike_host = current_app.config['AEROSPIKE_HOST']
aerospike_port = current_app.config['AEROSPIKE_PORT']

namespace = current_app.config['AEROSPIKE_NAMESPACE']
set_name = current_app.config['AEROSPIKE_SET_NAME']

n_replicas = 1

config = {
    'hosts': [
        (aerospike_host, aerospike_port)
    ],
    'policies': {
        'timeout': 1000  # milliseconds
    }
}

client = aerospike.client(config).connect()

# cannot limit the number of rows, only percent
# there is no start offset option
# https://discuss.aerospike.com/t/can-you-limit-the-number-of-returned-records/1330/2
# https://discuss.aerospike.com/t/official-as-approach-to-pagination/2532
# https://stackoverflow.com/questions/25927736/limit-number-of-records-in-aerospike-select-query


def init_app(app):
    pass


# if there is no more record, return -1 as next
def list(limit=10, cursor=None):
    if cursor:
        start = int(cursor)
    else:
        start = 0

    end = start + limit
    records = []

    for i in range(start, end):
        rec = read(str(i))

        if rec:
            records.append(rec)

    if end >= __get_objs_cnt__():
        next_key = -1
    else:
        next_key = len(records)

    return records, next_key

# cannot limit the number of rows, only percent
# there is no start offset option
# https://discuss.aerospike.com/t/can-you-limit-the-number-of-returned-records/1330/2
# https://discuss.aerospike.com/t/official-as-approach-to-pagination/2532
# https://stackoverflow.com/questions/25927736/limit-number-of-records-in-aerospike-select-query


# if there is no more record, return -1 as next
def list_by_user(user_id, limit=10, cursor=None):
    if cursor:
        start = cursor
    else:
        start = 0

    query = client.query(namespace, set_name)
    query.where(p.equals('createdById', user_id))

    records = []
    results = query.results()

    if cursor:
        start = cursor
    else:
        start = 0

    cnt = 0

    records = []

    for i, result in enumerate(results):
        if cnt >= limit:
            break

        if i < start:
            continue
        else:
            rec = result[2]
            records.append(rec)
            cnt += 1

    if cnt == limit:
        next_key = cnt
    else:
        next_key = -1

    return records, next_key


def __get_objs_cnt__():
    info = client.info("sets" + "/" + namespace + "/" + set_name)

    for value in info.values():
        info_str = value[1]

    try:
        start_idx = info_str.index("=") + 1
        end_idx = info_str.index(":")

        n_str = info_str[start_idx:end_idx]

        return math.ceil(int(n_str) / n_replicas)
    except ValueError:
        return 0


def create(data, id=None):
    if id:
        key = str(id)
    else:
        key = str(__get_objs_cnt__())
        data['id'] = key

    client.put((namespace, set_name, key), data)

    return read(key)


def read(id):
    try:
        (key, metadata) = client.exists((namespace, set_name, id))
        (key, metadata, record) = client.get((namespace, set_name, id))
        return record
    except ex.RecordNotFound:
        print("Record not found:", id)
        return None
    except ex.AerospikeError as e:
        print("Error: {0} [{1}]".format(e.msg, e.code))
        return None


def update(data, id):
    if client.exists((namespace, set_name, id)):
        delete(id)

    return create(data, id)


def delete(id):
    client.remove((namespace, set_name, id))
