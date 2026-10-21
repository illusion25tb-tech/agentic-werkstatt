from dataclasses import dataclass, field


@dataclass
class Line:
    sku: str
    unit_price: float
    quantity: int = 1

    def total(self) -> float:
        return round(self.unit_price * self.quantity, 2)


@dataclass
class Cart:
    lines: list[Line] = field(default_factory=list)

    def subtotal(self) -> float:
        return round(sum(x.total() for x in self.lines), 2)


cart = Cart([Line("AKS-18", 89.90)])
cart.lines.append(Line("BIT-32", 12.50, quantity=2))
print(cart.lines[1])
print(cart.subtotal())
