def add_numbers(a, b):
    return a + b

if __name__ == "__main__":
    a = float(input("Enter first number: "))
    b = float(input("Enter second number: "))
    result = add_numbers(a, b)
    print(f"Result: {a} + {b} = {result}")
