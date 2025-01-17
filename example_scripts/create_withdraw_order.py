from utils import _set_paths

_set_paths()

from gmx_python_sdk.scripts.v2.order.create_withdrawal_order import (
    WithdrawOrder
)
from gmx_python_sdk.scripts.v2.order.liquidity_argument_parser import (
    LiquidityArgumentParser
)

from gmx_python_sdk.scripts.v2.gmx_utils import (
    ConfigManager
)


config = ConfigManager("arbitrum")
config.set_config()


parameters = {
    "chain": "arbitrum",
    "market_token_symbol": "ETH",
    "out_token_symbol": "USDC",
    "gm_amount": 3
}

output = LiquidityArgumentParser(
    config,
    is_withdrawal=True
).process_parameters_dictionary(
    parameters
)

WithdrawOrder(
    config=config,
    market_key=output["market_key"],
    out_token=output["out_token_address"],
    gm_amount=output["gm_amount"],
    debug_mode=True
)
