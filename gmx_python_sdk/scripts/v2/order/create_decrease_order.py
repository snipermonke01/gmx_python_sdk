from .order import Order
from ..gas_utils import get_gas_limits
from ..gmx_utils import get_datastore_contract


class DecreaseOrder(Order):
    """
    Open a sell order
    Extends base Order class
    """

    def __init__(self, *args: list, **kwargs: dict) -> None:
        super().__init__(
            *args, **kwargs
        )

        # Close an order
        self.order_builder(is_close=True)

    def determine_gas_limits(self):
        datastore = get_datastore_contract(self.config)
        self._gas_limits = get_gas_limits(datastore)
        self._gas_limits_order_type = self._gas_limits["decrease_order"]
