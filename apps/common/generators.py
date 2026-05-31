import random
import string


def generate_mock_transaction_ref():
    chars = string.ascii_uppercase + string.digits
    suffix = ''.join(random.choices(chars, k=6))
    return f'MOCK-{suffix}'
