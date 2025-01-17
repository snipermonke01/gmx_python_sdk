from utils import _set_paths

_set_paths()

from web3 import Web3
from gmx_python_sdk.scripts.v2.get.get_oracle_prices import OraclePrices
from gmx_python_sdk.scripts.v2.get.get_markets import Markets
from gmx_python_sdk.scripts.v2.order.order_argument_parser import (
    OrderArgumentParser
)
from gmx_python_sdk.scripts.v2.gmx_utils import (
    get_estimated_swap_output,
    contract_map,
    determine_swap_route,
    get_tokens_address_dict,
    ConfigManager
)


class EstimateSwapOutput:

    def __init__(self, config):
        self.config = config
        self.markets = Markets(config).get_available_markets()
        self.tokens = get_tokens_address_dict(config.chain)

    def get_swap_output(
            self,
            in_token_symbol: str = None,
            out_token_symbol: str = None,
            token_amount: float = None,
            in_token_address: str = None,
            out_token_address: str = None,
            token_amount_expanded: float = None
    ):
        """
        For a given in token and amount, get the amount of a given out token
        after swap. Can supply ticker/symbol or address for in/out tokens,
        and amount in human readable amount or expanded 10 ^ its decimals

        Parameters
        ----------
        in_token_symbol : str, optional
            ticker or symbol of in token. The default is None.
        out_token_symbol : str, optional
            ticker or symbol of out token. The default is None.
        token_amount : float, optional
            amoutn of token in human readable eg 1 = one. The default is None.
        in_token_address : str, optional
            contract address of in token. The default is None.
        out_token_address : str, optional
            contract address of out token. The default is None.
        token_amount_expanded : float, optional
            Amount of token in expanded form, eg 1 BTC = 10000000.
            The default is None.

        Returns
        -------
        dict
            amount of tokens out and price impact in USD.

        """

        if in_token_address is None:
            in_token_address = OrderArgumentParser(config=self.config).find_key_by_symbol(
                self.tokens,
                in_token_symbol
            )
        if out_token_address is None:
            out_token_address = OrderArgumentParser(config=self.config).find_key_by_symbol(
                self.tokens,
                out_token_symbol
            )
        if token_amount_expanded is None:
            token_amount_expanded = (
                token_amount * 10 ** self.tokens[in_token_address]['decimals']
            )

        swap_route = determine_swap_route(
            self.markets,
            in_token_address,
            out_token_address
        )
        output = self.estimated_swap_output(
            self.markets[swap_route[0][0]],
            in_token_address,
            token_amount_expanded
        )
        output['out_token_actual'] = output['out_token_amount'] / \
            10 ** self.tokens[out_token_address]['decimals']
        output['price_impact'] = output['price_impact_usd'] / \
            10 ** 7

        return output

    def estimated_swap_output(
            self,
            market: dict,
            in_token: str,
            token_amount_expanded: int
    ):
        """
        For a given market, in_token, and token amount get output

        Parameters
        ----------
        market : dict
            Details of market to swap through.
        in_token : str
            contract address of in token.
        token_amount_expanded : int
            expanded amount of tokens to swap.

        Returns
        -------
        dict
            amount of tokens out and price impact in USD.

        """

        prices = OraclePrices(self.config.chain).get_recent_prices()

        token_addresses = [
            market['index_token_address'],
            market['long_token_address'],
            market['short_token_address']
        ]

        token_prices = [
            [
                int(prices[token]['maxPriceFull']),
                int(prices[token]['minPriceFull'])
            ]
            for token in token_addresses
        ]

        estimated_swap_output_parameters = {
            'data_store_address': (
                contract_map[self.config.chain]["datastore"]['contract_address']
            ),
            'market_addresses': [
                market['gmx_market_address']
            ] + token_addresses,
            'token_prices_tuple': token_prices,
            'token_in': Web3.to_checksum_address(in_token),
            'token_amount_in': token_amount_expanded,
            'ui_fee_receiver': "0x0000000000000000000000000000000000000000"
        }

        return get_estimated_swap_output(
            self.config,
            estimated_swap_output_parameters
        )


if __name__ == "__main__":
    import time

    start = time.time()

    in_token_symbol = "GMX"
    out_token_symbol = "USDC"
    token_amount = 10
    in_token_address = None
    out_token_address = None
    token_amount_expanded = None

    config = ConfigManager("arbitrum")
    config.set_config()
    output = EstimateSwapOutput(config=config).get_swap_output(
        in_token_symbol=in_token_symbol,
        out_token_symbol=out_token_symbol,
        token_amount=token_amount,
        in_token_address=in_token_address,
        out_token_address=out_token_address,
        token_amount_expanded=token_amount_expanded
    )

    print(output)
    end = time.time()
    print("Finished. Time taken: {:.02}s".format(end - start))
