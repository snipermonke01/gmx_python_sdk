from .order import Order
from ..gas_utils import get_gas_limits
from ..gmx_utils import get_datastore_contract


class IncreaseOrder(Order):
    """
    Open a buy order
    Extends base Order class
    """

    def __init__(self, *args: list, **kwargs: dict) -> None:
        super().__init__(
            *args, **kwargs
        )

        # Open an order
        self.order_builder(is_open=True)

    def determine_gas_limits(self):
        datastore = get_datastore_contract(self.config)
        self._gas_limits = get_gas_limits(datastore)
        self._gas_limits_order_type = self._gas_limits["increase_order"]
