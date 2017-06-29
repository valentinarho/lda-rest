from requests import put


def test_models_put():
    return put('http://localhost:5000/models').json()


if __name__ == '__main__':
    result = test_models_put()

    print(result)
