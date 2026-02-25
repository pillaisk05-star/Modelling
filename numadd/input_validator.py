MAX_VALUE = 1e15


class InputValidator:
    def validate(self, a, b) -> bool:
        return self.is_number(a) and self.is_number(b) and \
               self.is_within_range(float(a)) and self.is_within_range(float(b))

    def is_number(self, value) -> bool:
        try:
            float(value)
            return True
        except (TypeError, ValueError):
            return False

    def is_within_range(self, value: float) -> bool:
        return abs(value) <= MAX_VALUE
