from app import app


def print_response(label, response):
    try:
        body = response.get_json()
    except Exception:
        body = response.get_data(as_text=True)
    print(label, response.status_code, body)


if __name__ == '__main__':
    client = app.test_client()

    checks = [
        ('health', client.get('/api/health')),
        ('categories', client.get('/api/categories')),
        ('products', client.get('/api/products')),
        ('cart without login', client.get('/api/cart')),
        ('recharge without login', client.post('/api/user/recharge', json={'amount': 'abc'})),
    ]

    for label, response in checks:
        print_response(label, response)
