class IAdditionService:
    def add(self, a: float, b: float) -> float:
        raise NotImplementedError


class AdditionService(IAdditionService):
    def add(self, a: float, b: float) -> float:
        return a + b
