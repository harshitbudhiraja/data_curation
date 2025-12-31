def remove_digits_from_list(strings):
    return [''.join(char for char in s if not char.isdigit()) for s in strings]


print(remove_digits_from_list(["a123", "a456", "7s89"]))