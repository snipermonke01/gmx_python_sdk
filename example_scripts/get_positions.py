from utils import _set_paths

_set_paths()

from decimal import Decimal

from gmx_python_sdk.scripts.v2.get.get_markets import Markets

from gmx_python_sdk.scripts.v2.get.get_open_positions import GetOpenPositions
from gmx_python_sdk.scripts.v2.gmx_utils import (
    ConfigManager, find_dictionary_by_key_value, get_tokens_address_dict,
    determine_swap_route
)


def get_positions(config, address: str = None):
    """
    Get open positions for an address on a given network.
    If address is not passed it will take the address from the users config
    file.

    Parameters
    ----------
    chain : str
        arbitrum or avalanche.
    address : str, optional
        address to fetch open positions for. The default is None.

    Returns
    -------
    positions : dict
        dictionary containing all open positions.

    """

    if address is None:
        address = config.user_wallet_address
        if address is None:
            raise Exception("No address passed in function or config!")

    positions = GetOpenPositions(config=config, address=address).get_data()

    if len(positions) > 0:
        print("Open Positions for {}:".format(address))
        for key in positions.keys():
            print(key)

    return positions


def transform_open_position_to_order_parameters(
    config,
    positions: dict,
    market_symbol: str,
    is_long: bool,
    slippage_percent: float,
    out_token,
    amount_of_position_to_close,
    amount_of_collateral_to_remove
):
    """
    Find the user defined trade from market_symbol and is_long in a dictionary
    positions and return a dictionary formatted correctly to close 100% of
    that trade

    Parameters
    ----------
    chain : str
        arbitrum or avalanche.
    positions : dict
        dictionary containing all open positions.
    market_symbol : str
        symbol of market trader.
    is_long : bool
        True for long, False for short.
    slippage_percent : float
        slippage tolerance to close trade as a percentage.

    Raises
    ------
    Exception
        If we can't find the requested trade for the user.

    Returns
    -------
    dict
        order parameters formatted to close the position.

    """
    direction = "short"
    if is_long:
        direction = "long"

    position_dictionary_key = "{}_{}".format(
        market_symbol.upper(),
        direction
    )

    try:
        raw_position_data = positions[position_dictionary_key]
        gmx_tokens = get_tokens_address_dict(config.chain)

        collateral_address = find_dictionary_by_key_value(
            gmx_tokens,
            "symbol",
            raw_position_data['collateral_token']
        )["address"]

        gmx_tokens = get_tokens_address_dict(config.chain)

        index_address = find_dictionary_by_key_value(
            gmx_tokens,
            "symbol",
            raw_position_data['market_symbol'][0]
        )
        out_token_address = find_dictionary_by_key_value(
            gmx_tokens,
            "symbol",
            out_token
        )['address']
        markets = Markets(config=config).info

        swap_path = []

        if collateral_address != out_token_address:
            swap_path = determine_swap_route(
                markets,
                collateral_address,
                out_token_address
            )[0]
        size_delta = int(int(
            (Decimal(raw_position_data['position_size']) * (Decimal(10)**30))
        ) * amount_of_position_to_close)

        return {
            "chain": config.chain,
            "market_key": raw_position_data['market'],
            "collateral_address": collateral_address,
            "index_token_address": index_address["address"],
            "is_long": raw_position_data['is_long'],
            "size_delta": size_delta,
            "initial_collateral_delta": int(int(
                raw_position_data['inital_collateral_amount']
            ) * amount_of_collateral_to_remove
            ),
            "slippage_percent": slippage_percent,
            "swap_path": swap_path
        }
    except KeyError:
        raise Exception(
            "Couldn't find a {} {} for given user!".format(
                market_symbol, direction
            )
        )


if __name__ == "__main__":

    config = ConfigManager(chain='arbitrum')
    config.set_config()

    positions = get_positions(
        config=config,
        address="0x0e9E19E7489E5F13a0940b3b6FcB84B25dc68177"
    )

    # market_symbol = "ETH"
    # is_long = True

    # out_token = "USDC"
    # amount_of_position_to_close = 1
    # amount_of_collateral_to_remove = 1

    # order_params = transform_open_position_to_order_parameters(
    #     config=config,
    #     positions=positions,
    #     market_symbol=market_symbol,
    #     is_long=is_long,
    #     slippage_percent=0.003,
    #     out_token="USDC",
    #     amount_of_position_to_close=amount_of_position_to_close,
    #     amount_of_collateral_to_remove=amount_of_collateral_to_remove
    # )
