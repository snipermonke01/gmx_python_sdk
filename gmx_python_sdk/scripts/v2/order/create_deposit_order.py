from .deposit import Deposit
from ..gas_utils import get_gas_limits
from ..gmx_utils import get_datastore_contract


class DepositOrder(Deposit):
    """
    Open a Deposit order
    Extends base Deposit class
    """

    def __init__(self, *args: list, **kwargs: dict) -> None:
        super().__init__(
            *args, **kwargs
        )

        # Createa a deposit order
        self.create_deposit_order()

    def determine_gas_limits(self):

        datastore = get_datastore_contract(self.config)
        self._gas_limits = get_gas_limits(datastore)
        self._gas_limits_order_type = self._gas_limits["increase_order"]
