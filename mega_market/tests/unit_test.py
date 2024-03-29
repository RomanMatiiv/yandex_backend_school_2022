# encoding=utf8

import json
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

import pytest

API_BASEURL = "http://localhost:80"
# API_BASEURL = "http://external-2018.usr.yandex-academy.ru:80"
# API_BASEURL = "https://external-2018.usr.yandex-academy.ru:80"

ROOT_ID = "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1"
ROOT_ID_FOR_MY_UNIT = "4b0bc882-6c39-4d5b-b3e1-b8964ff4ec07"

IMPORT_BATCHES = [
    {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Товары",
                "id": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
                "parentId": None
            }
        ],
        "updateDate": "2022-02-01T12:00:00.000Z"
    },
    {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Смартфоны",
                "id": "d515e43f-f3f6-4471-bb77-6b455017a2d2",
                "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1"
            },
            {
                "type": "OFFER",
                "name": "jPhone 13",
                "id": "863e1a7a-1304-42ae-943b-179184c077e3",
                "parentId": "d515e43f-f3f6-4471-bb77-6b455017a2d2",
                "price": 79999
            },
            {
                "type": "OFFER",
                "name": "Xomiа Readme 10",
                "id": "b1d8fd7d-2ae3-47d5-b2f9-0f094af800d4",
                "parentId": "d515e43f-f3f6-4471-bb77-6b455017a2d2",
                "price": 59999
            }
        ],
        "updateDate": "2022-02-02T12:00:00.000Z"
    },
    {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Телевизоры",
                "id": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1"
            },
            {
                "type": "OFFER",
                "name": "Samson 70\" LED UHD Smart",
                "id": "98883e8f-0507-482f-bce2-2fb306cf6483",
                "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                "price": 32999
            },
            {
                "type": "OFFER",
                "name": "Phyllis 50\" LED UHD Smarter",
                "id": "74b81fda-9cdc-4b63-8927-c978afed5cf4",
                "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                "price": 49999
            }
        ],
        "updateDate": "2022-02-03T12:00:00.000Z"
    },
    {
        "items": [
            {
                "type": "OFFER",
                "name": "Goldstar 65\" LED UHD LOL Very Smart",
                "id": "73bc3b36-02d1-4245-ab35-3106c9ee1c65",
                "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                "price": 69999
            }
        ],
        "updateDate": "2022-02-03T15:00:00.000Z"
    }
]

EXPECTED_TREE = {
    "type": "CATEGORY",
    "name": "Товары",
    "id": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
    "price": 58599,
    "parentId": None,
    "date": "2022-02-03T15:00:00.000Z",
    "children": [
        {
            "type": "CATEGORY",
            "name": "Телевизоры",
            "id": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
            "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
            "price": 50999,
            "date": "2022-02-03T15:00:00.000Z",
            "children": [
                {
                    "type": "OFFER",
                    "name": "Samson 70\" LED UHD Smart",
                    "id": "98883e8f-0507-482f-bce2-2fb306cf6483",
                    "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                    "price": 32999,
                    "date": "2022-02-03T12:00:00.000Z",
                    "children": None,
                },
                {
                    "type": "OFFER",
                    "name": "Phyllis 50\" LED UHD Smarter",
                    "id": "74b81fda-9cdc-4b63-8927-c978afed5cf4",
                    "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                    "price": 49999,
                    "date": "2022-02-03T12:00:00.000Z",
                    "children": None
                },
                {
                    "type": "OFFER",
                    "name": "Goldstar 65\" LED UHD LOL Very Smart",
                    "id": "73bc3b36-02d1-4245-ab35-3106c9ee1c65",
                    "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                    "price": 69999,
                    "date": "2022-02-03T15:00:00.000Z",
                    "children": None
                }
            ]
        },
        {
            "type": "CATEGORY",
            "name": "Смартфоны",
            "id": "d515e43f-f3f6-4471-bb77-6b455017a2d2",
            "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
            "price": 69999,
            "date": "2022-02-02T12:00:00.000Z",
            "children": [
                {
                    "type": "OFFER",
                    "name": "jPhone 13",
                    "id": "863e1a7a-1304-42ae-943b-179184c077e3",
                    "parentId": "d515e43f-f3f6-4471-bb77-6b455017a2d2",
                    "price": 79999,
                    "date": "2022-02-02T12:00:00.000Z",
                    "children": None
                },
                {
                    "type": "OFFER",
                    "name": "Xomiа Readme 10",
                    "id": "b1d8fd7d-2ae3-47d5-b2f9-0f094af800d4",
                    "parentId": "d515e43f-f3f6-4471-bb77-6b455017a2d2",
                    "price": 59999,
                    "date": "2022-02-02T12:00:00.000Z",
                    "children": None
                }
            ]
        },
    ]
}


def request(path, method="GET", data=None, json_response=False):
    try:
        params = {
            "url": f"{API_BASEURL}{path}",
            "method": method,
            "headers": {},
        }

        if data:
            params["data"] = json.dumps(
                data, ensure_ascii=False).encode("utf-8")
            params["headers"]["Content-Length"] = len(params["data"])
            params["headers"]["Content-Type"] = "application/json"

        req = urllib.request.Request(**params)

        with urllib.request.urlopen(req) as res:
            res_data = res.read().decode("utf-8")
            if json_response:
                res_data = json.loads(res_data)
            return (res.getcode(), res_data)
    except urllib.error.HTTPError as e:
        return (e.getcode(), None)


def deep_sort_children(node):
    if node.get("children"):
        node["children"].sort(key=lambda x: x["id"])

        for child in node["children"]:
            deep_sort_children(child)


def print_diff(expected, response):
    with open("expected.json", "w") as f:
        json.dump(expected, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")

    with open("response.json", "w") as f:
        json.dump(response, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")

    subprocess.run(["git", "--no-pager", "diff", "--no-index",
                    "expected.json", "response.json"])


def test_import():
    for index, batch in enumerate(IMPORT_BATCHES):
        print(f"Importing batch {index}")
        status, _ = request("/imports", method="POST", data=batch)

        assert status == 200, f"Expected HTTP status code 200, got {status}"

    print("Test import passed.")


def test_create_my_root_unit():
    root_unit = {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Объекты",
                "id": ROOT_ID_FOR_MY_UNIT
            },
        ],
        "updateDate": "2022-03-01T11:00:00.000Z"
    }

    status, _ = request("/imports", method="POST", data=root_unit)
    assert status == 200, f"Expected HTTP status code 200, got {status}"


def test_incorrect_parent():
    """
    Родителем товара или категории может быть только категория
    """
    import_batch = {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Товары",
                "id": "3a112ec7-ab99-4918-8284-2f11a00a9519",
                "parentId": "eeb75ccc-c543-443b-b15f-0949a00d9c33"
            },
            {
                "type": "OFFER",
                "name": "Nokia 3310",
                "id": "eeb75ccc-c543-443b-b15f-0949a00d9c33",
                "parentId": ROOT_ID_FOR_MY_UNIT,
                "price": 20000
            },
        ],
        "updateDate": "2022-02-01T12:00:00.000Z"
    }

    status, _ = request("/imports", method="POST", data=import_batch)
    assert status == 400, f"Expected HTTP status code 400, got {status}"


def test_name_equal_null():
    """
    Название элемента не может быть null
    """
    offer = {
        "items": [
            {
                "type": "OFFER",
                "name": None,
                "id": "dab1ef99-b831-4801-98ed-79df40729fa1",
                "parentId": ROOT_ID_FOR_MY_UNIT,
                "price": 20000
            },
        ],
        "updateDate": "2022-03-01T11:00:00.000Z"
    }

    category = {
        "items": [
            {
                "type": "CATEGORY",
                "name": None,
                "id": "61028d01-2e20-4ce2-b5ff-a5901a97af59",
                "parentId": ROOT_ID_FOR_MY_UNIT,
            },
        ],
        "updateDate": "2022-03-01T11:00:00.000Z"
    }

    status, _ = request("/imports", method="POST", data=offer)
    assert status == 400, f"Expected HTTP status code 400, got {status}"

    status, _ = request("/imports", method="POST", data=category)
    assert status == 400, f"Expected HTTP status code 400, got {status}"


def test_price_equal_not_null_for_category():
    """
    У категорий поле price должно содержать null
    """
    category = {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Плееры",
                "id": "33161b54-bdef-4d85-8d6d-fa19f1f645f5",
                "parentId": ROOT_ID_FOR_MY_UNIT,
                "price": 999,
            },
        ],
        "updateDate": "2022-03-01T11:00:00.000Z"
    }

    status, _ = request("/imports", method="POST", data=category)
    assert status == 400, f"Expected HTTP status code 400, got {status}"


def test_offer_price_equal_null():
    """
    Цена товара не может быть null
    """
    import_offer = {
        "items": [
            {
                "type": "OFFER",
                "name": "Starlink",
                "id": "ec06f1d1-8bc0-4df3-aac7-4ee98360ae9a",
                "parentId": ROOT_ID_FOR_MY_UNIT,
                "price": None,
            }
        ],
        "updateDate": "2022-03-01T11:00:00.000Z"
    }

    status, _ = request("/imports", method="POST", data=import_offer)
    assert status == 400, f"Expected HTTP status code 400, got {status}"


def test_offer_price_equal_minus_one():
    """
    Цена товара должна быть больше либо равна нулю.
    """
    import_offer = {
        "items": [
            {
                "type": "OFFER",
                "name": "Starlink",
                "id": "ec06f1d1-8bc0-4df3-aac7-4ee98360ae9a",
                "parentId": ROOT_ID_FOR_MY_UNIT,
                "price": -1,
            }
        ],
        "updateDate": "2022-03-01T11:00:00.000Z"
    }

    status, _ = request("/imports", method="POST", data=import_offer)
    assert status == 400, f"Expected HTTP status code 400, got {status}"


def test_two_element_with_same_uuid():
    """
    В одном запросе не может быть двух элементов с одинаковым id
    """
    batch_children_before_parent = {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Смартфоны 1",
                "id": "bb54bb58-b308-46fb-88e1-8f7b7cdf56da",
                "parentId": ROOT_ID_FOR_MY_UNIT
            },
            {
                "type": "CATEGORY",
                "name": "Смартфоны 2",
                "id": "bb54bb58-b308-46fb-88e1-8f7b7cdf56da",
                "parentId": ROOT_ID_FOR_MY_UNIT
            },
        ],
        "updateDate": "2022-03-01T12:00:00.000Z"
    }

    status, _ = request("/imports", method="POST", data=batch_children_before_parent)

    assert status == 400, f"Expected HTTP status code 400, got {status}"


def test_incorrect_date_format():
    """
    Дата должна обрабатываться согласно ISO 8601.
    Если дата не удовлетворяет данному формату, необходимо отвечать 400.
    """
    import_offer = {
        "items": [
            {
                "type": "OFFER",
                "name": "Starlink",
                "id": "ec06f1d1-8bc0-4df3-aac7-4ee98360ae9a",
                "parentId": ROOT_ID_FOR_MY_UNIT,
            }
        ],
        "updateDate": "01-03-2022"
    }

    status, _ = request("/imports", method="POST", data=import_offer)
    assert status == 400, f"Expected HTTP status code 400, got {status}"


def test_import_children_before_parent():
    """
    тестирование кейса, когда дочерний элемент импортируется раньше родительского

    Тк в задании сказано, что порядок элементов является произвольным
    """
    batch_children_before_parent = {
        "items": [
            {
                "type": "OFFER",
                "name": "Keychron k3",
                "id": "9ce9ad31-aa6c-457c-9247-59d3fec38fa4",
                "parentId": "4337063b-2532-4bcf-a1dd-1288d2c2745d",
                "price": 79999
            },
            {
                "type": "CATEGORY",
                "name": "Клавиатуры",
                "id": "4337063b-2532-4bcf-a1dd-1288d2c2745d",
                "parentId": ROOT_ID_FOR_MY_UNIT
            },
        ],
        "updateDate": "2022-03-01T12:00:00.000Z"
    }

    status, _ = request("/imports", method="POST", data=batch_children_before_parent)

    assert status == 200, f"Expected HTTP status code 200, got {status}"


def test_change_type():
    """
    Тестирование изменения типа объекта с offer на category
    """
    import_batch = {
        "items": [
            {
                "type": "OFFER",
                "name": "Nokia 3310",
                "id": "3a112ec7-ab99-4918-8284-2f11a00a9519",
                "price": 20000,
                "parentId":ROOT_ID_FOR_MY_UNIT
            },
        ],
        "updateDate": "2022-02-01T12:00:00.000Z"
    }
    change_type_batch = {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Nokia 3310",
                "id": "3a112ec7-ab99-4918-8284-2f11a00a9519",
                "parentId": ROOT_ID_FOR_MY_UNIT
            }
        ],
        "updateDate": "2022-04-01T12:00:00.000Z"
    }

    status, _ = request("/imports", method="POST", data=import_batch)
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    status, _ = request("/imports", method="POST", data=change_type_batch)
    assert status == 400, f"Expected HTTP status code 400, got {status}"


def test_import_incorrect_uuid():
    import_category = {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Спутники",
                "id": "1234",
                "parentId": ROOT_ID_FOR_MY_UNIT,
            }
        ],
        "updateDate": "2022-02-01T11:00:00.000Z"
    }

    status, _ = request("/imports", method="POST", data=import_category)
    assert status == 400, f"Expected HTTP status code 400, got {status}"


def test_nodes():
    status, response = request(f"/nodes/{ROOT_ID}", json_response=True)
    # print(json.dumps(response, indent=2, ensure_ascii=False))

    assert status == 200, f"Expected HTTP status code 200, got {status}"

    deep_sort_children(response)
    deep_sort_children(EXPECTED_TREE)
    if response != EXPECTED_TREE:
        print_diff(EXPECTED_TREE, response)
        print("Response tree doesn't match expected tree.")
        sys.exit(1)

    print("Test nodes passed.")


def test_sales():
    params = urllib.parse.urlencode({
        "date": "2022-02-04T00:00:00.000Z"
    })
    status, response = request(f"/sales?{params}", json_response=True)
    assert status == 200, f"Expected HTTP status code 200, got {status}"
    print("Test sales passed.")


def test_stats():
    params = urllib.parse.urlencode({
        "dateStart": "2022-02-01T00:00:00.000Z",
        "dateEnd": "2022-02-03T00:00:00.000Z"
    })
    status, response = request(
        f"/node/{ROOT_ID}/statistic?{params}", json_response=True)

    assert status == 200, f"Expected HTTP status code 200, got {status}"
    print("Test stats passed.")


def test_delete_offer():
    id = "786eb0a7-902e-4e93-a798-6aad6de9ac68"
    create = {
        "items": [
            {
                "type": "OFFER",
                "name": "Logitech MX mouse",
                "id": id,
                "price": 10000,
                "parentId": ROOT_ID_FOR_MY_UNIT
            }
        ],
        "updateDate": "2022-02-02T11:00:00.000Z"
    }

    status, _ = request("/imports", method="POST", data=create)
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    status, _ = request(f"/delete/{id}", method="DELETE")
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    status, _ = request(f"/nodes/{id}", json_response=True)
    assert status == 404, f"Expected HTTP status code 404, got {status}"


def test_delete_category():
    id = "0ba80f69-095d-4dd1-9203-4d0d6b4d25fa"
    create = {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Mouse",
                "id": id,
                "parentId":ROOT_ID_FOR_MY_UNIT
            }
        ],
        "updateDate": "2022-02-02T11:00:00.000Z"
    }

    status, _ = request("/imports", method="POST", data=create)
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    status, _ = request(f"/delete/{id}", method="DELETE")
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    status, _ = request(f"/nodes/{id}", json_response=True)
    assert status == 404, f"Expected HTTP status code 404, got {status}"


def test_delete_offer_wit_category():
    offer_id = '8a844c4f-a4d8-4af7-9cb3-8f8fa741b791'
    category_id = 'd9b031f6-14c1-4268-8f3e-a0eec9726a2d'
    create = {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Лампы",
                "id": category_id,
                "parentId": ROOT_ID_FOR_MY_UNIT
            },
            {
                "type": "OFFER",
                "name": "Xiaomi Yeelight",
                "id": offer_id,
                "parentId": category_id,
                "price": 6000
            }
        ],
        "updateDate": "2022-03-01T12:00:00.000Z"
    }
    status, _ = request("/imports", method="POST", data=create)
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    status, _ = request(f"/delete/{category_id}", method="DELETE")
    assert status == 200, f"Expected HTTP status code 404, got {status}"

    status, _ = request(f"/nodes/{offer_id}", json_response=True)
    assert status == 404, f"Expected HTTP status code 404, got {status}"

    status, _ = request(f"/nodes/{category_id}", json_response=True)
    assert status == 404, f"Expected HTTP status code 404, got {status}"


def test_delete_category_with_subcategory():
    category_id = '7ef817a6-fe02-4a98-a27a-f5cc4d5bc09b'
    sub_category_id = '0fbaa683-63a1-4883-9833-dbf542c56e6e'
    create = {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Кабеля",
                "id": category_id,
                "parentId": ROOT_ID_FOR_MY_UNIT
            },
            {
                "type": "CATEGORY",
                "name": "Кабеля Type C",
                "id": sub_category_id,
                "parentId": category_id,
            }
        ],
        "updateDate": "2022-01-03T12:00:00.000Z"
    }
    status, _ = request("/imports", method="POST", data=create)
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    status, _ = request(f"/delete/{category_id}", method="DELETE")
    assert status == 200, f"Expected HTTP status code 404, got {status}"

    status, _ = request(f"/nodes/{category_id}", json_response=True)
    assert status == 404, f"Expected HTTP status code 404, got {status}"

    status, _ = request(f"/nodes/{sub_category_id}", json_response=True)
    assert status == 404, f"Expected HTTP status code 404, got {status}"


def test_delete_invalid_uuid():
    id = '1234'
    status, _ = request(f"/delete/{id}", method="DELETE")
    assert status == 400, f"Expected HTTP status code 400, got {status}"


def test_delete():
    status, _ = request(f"/delete/{ROOT_ID}", method="DELETE")
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    status, _ = request(f"/nodes/{ROOT_ID}", json_response=True)
    assert status == 404, f"Expected HTTP status code 404, got {status}"

    print("Test delete passed.")


def test_delete_my_root_unit():
    status, _ = request(f"/delete/{ROOT_ID_FOR_MY_UNIT}", method="DELETE")
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    status, _ = request(f"/nodes/{ROOT_ID_FOR_MY_UNIT}", json_response=True)
    assert status == 404, f"Expected HTTP status code 404, got {status}"



def test_all():
    test_import()
    test_nodes()
    test_sales()
    test_stats()
    test_delete()


def main():
    global API_BASEURL
    test_name = None

    for arg in sys.argv[1:]:
        if re.match(r"^https?://", arg):
            API_BASEURL = arg
        elif test_name is None:
            test_name = arg

    if API_BASEURL.endswith('/'):
        API_BASEURL = API_BASEURL[:-1]

    if test_name is None:
        test_all()
    else:
        test_func = globals().get(f"test_{test_name}")
        if not test_func:
            print(f"Unknown test: {test_name}")
            sys.exit(1)
        test_func()


if __name__ == "__main__":
    main()
