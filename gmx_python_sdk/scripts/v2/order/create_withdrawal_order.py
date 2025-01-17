from .withdraw import Withdraw
from ..gas_utils import get_gas_limits
from ..gmx_utils import get_datastore_contract


class WithdrawOrder(Withdraw):
    """
    Open a withdrawal order
    Extends base Withdraw class
    """

    def __init__(self, *args: list, **kwargs: dict) -> None:
        super().__init__(
            *args, **kwargs
        )

        # Open a withdrawal order
        self.create_withdraw_order()

    def determine_gas_limits(self):

        datastore = get_datastore_contract(self.config)
        self._gas_limits = get_gas_limits(datastore)
        self._gas_limits_order_type = self._gas_limits["increase_order"]
