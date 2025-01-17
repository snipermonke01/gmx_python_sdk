from web3 import Web3

from .order import Order
from ..gas_utils import get_gas_limits
from ..get.get_oracle_prices import OraclePrices
from ..gmx_utils import (
    get_estimated_swap_output, contract_map, get_datastore_contract
)


class SwapOrder(Order):
    """
    Open a swap order
    Extends base Order class
    """

    def __init__(self, start_token: str, out_token: str, *args: list, **kwargs: dict) -> None:
        super().__init__(
            *args, **kwargs
        )
        self.start_token = start_token
        self.out_token = out_token

        # Open an order
        self.order_builder(is_swap=True)

    def determine_gas_limits(self):

        datastore = get_datastore_contract(self.config)
        self._gas_limits = get_gas_limits(datastore)
        self._gas_limits_order_type = self._gas_limits["swap_order"]

    def estimated_swap_output(self, market: dict, in_token: str, in_token_amount: int):
        """
        For a given market, token, and amount, estimate the amount of token returned
        when the in token is swapped through the market.

        Parameters
        ----------
        market : dict
            full market details.
        in_token : str
            contract aaddress of token.
        in_token_amount : int
            amount of token to swap.

        Returns
        -------
        estimated_swap_output : dict
            dict containing amount of tokens and price impact after swap.

        """

        prices = OraclePrices(chain=self.config.chain).get_recent_prices()

        try:
            in_token = Web3.to_checksum_address(in_token)
        except AttributeError:
            in_token = Web3.toChecksumAddress(in_token)

        # For every path we through we need to call this to get the expected
        # output after x number of swaps
        estimated_swap_output_parameters = {
            'data_store_address': (
                contract_map[self.config.chain]["datastore"]['contract_address']
            ),
            'market_addresses': [
                market['gmx_market_address'],
                market['index_token_address'],
                market['long_token_address'],
                market['short_token_address']
            ],
            'token_prices_tuple': [
                [
                    int(prices[market['index_token_address']]['maxPriceFull']),
                    int(prices[market['index_token_address']]['minPriceFull'])
                ],
                [
                    int(prices[market['long_token_address']]['maxPriceFull']),
                    int(prices[market['long_token_address']]['minPriceFull'])
                ],
                [
                    int(prices[market['short_token_address']]['maxPriceFull']),
                    int(prices[market['short_token_address']]['minPriceFull'])
                ],
            ],
            'token_in': in_token,
            'token_amount_in': in_token_amount,
            'ui_fee_receiver': "0x0000000000000000000000000000000000000000"
        }

        estimated_swap_output = get_estimated_swap_output(
            self.config,
            estimated_swap_output_parameters
        )

        return estimated_swap_output
