from utils import _set_paths

_set_paths()

from gmx_python_sdk.scripts.v2.order.create_swap_order import SwapOrder
from gmx_python_sdk.scripts.v2.order.order_argument_parser import (
    OrderArgumentParser
)

from gmx_python_sdk.scripts.v2.gmx_utils import ConfigManager

config = ConfigManager(chain='arbitrum')
config.set_config()


parameters = {
    "chain": 'arbitrum',

    # token to use as collateral. Start token swaps into collateral token if
    # different
    "out_token_symbol": "ETH",

    # the token to start with - WETH not supported yet
    "start_token_symbol": "SOL",

    # True for long, False for short
    "is_long": False,

    # Position size in in USD
    "size_delta_usd": 0,

    # if leverage is passed, will calculate number of tokens in
    # start_token_symbol amount
    "initial_collateral_delta": 0.05,

    # as a percentage
    "slippage_percent": 0.03
}


order_parameters = OrderArgumentParser(
    config,
    is_swap=True
).process_parameters_dictionary(
    parameters
)

order = SwapOrder(
    config=config,
    market_key=order_parameters['swap_path'][-1],
    start_token=order_parameters['start_token_address'],
    out_token=order_parameters['out_token_address'],
    collateral_address=order_parameters['start_token_address'],
    index_token_address=order_parameters['out_token_address'],
    is_long=False,
    size_delta=0,
    initial_collateral_delta_amount=(
        order_parameters['initial_collateral_delta']
    ),
    slippage_percent=order_parameters['slippage_percent'],
    swap_path=order_parameters['swap_path'],
    debug_mode=True
)
