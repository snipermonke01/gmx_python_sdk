import logging
import numpy as np

from hexbytes import HexBytes
from web3 import Web3

from ..get.get_markets import Markets
from ..get.get_oracle_prices import OraclePrices
from ..gmx_utils import (
    get_exchange_router_contract, create_connection, contract_map,
    PRECISION, get_execution_price_and_price_impact, order_type as order_types,
    decrease_position_swap_type as decrease_position_swap_types,
    convert_to_checksum_address, check_web3_correct_version
)
from ..gas_utils import get_execution_fee
from ..approve_token_for_spend import check_if_approved

is_newer_version, version = check_web3_correct_version()
if is_newer_version:
    logging.warning(
        f"GMX Python SDK was developed with py web3 version 6.10.0. Current version of py web3 ({version}), may result in errors.")


class Order:

    def __init__(
        self, config: str, market_key: str, collateral_address: str,
        index_token_address: str, is_long: bool, size_delta: float,
        initial_collateral_delta_amount: str, slippage_percent: float,
        swap_path: list, max_fee_per_gas: int = None, auto_cancel: bool = False,
        debug_mode: bool = False, execution_buffer: float = 1.3
    ) -> None:

        self.config = config
        self.market_key = market_key
        self.collateral_address = collateral_address
        self.index_token_address = index_token_address
        self.is_long = is_long
        self.size_delta = size_delta
        self.initial_collateral_delta_amount = initial_collateral_delta_amount
        self.slippage_percent = slippage_percent
        self.swap_path = swap_path
        self.max_fee_per_gas = max_fee_per_gas
        self.debug_mode = debug_mode
        self.auto_cancel = auto_cancel
        self.execution_buffer = execution_buffer

        if self.debug_mode:
            logging.info("Execution buffer set to: {:.2f}%".format(
                (self.execution_buffer - 1) * 100))

        if self.max_fee_per_gas is None:
            block = create_connection(
                config
            ).eth.get_block('latest')
            self.max_fee_per_gas = block['baseFeePerGas'] * 1.35

        self._exchange_router_contract_obj = get_exchange_router_contract(
            config=self.config
        )
        self._connection = create_connection(config)
        self._is_swap = False

        self.log = logging.getLogger(__name__)
        self.log.info("Creating order...")

    def determine_gas_limits(self):
        pass

    def check_for_approval(self):
        """
        Check for Approval
        """
        spender = contract_map[self.config.chain]["syntheticsrouter"]['contract_address']

        check_if_approved(self.config,
                          spender,
                          self.collateral_address,
                          self.initial_collateral_delta_amount,
                          self.max_fee_per_gas,
                          approve=True)

    def _submit_transaction(
        self, user_wallet_address: str, value_amount: float,
        multicall_args: list, gas_limits: dict
    ):
        """
        Submit Transaction
        """
        self.log.info("Building transaction...")
        try:
            wallet_address = Web3.to_checksum_address(user_wallet_address)
        except AttributeError:
            wallet_address = Web3.toChecksumAddress(user_wallet_address)
        nonce = self._connection.eth.get_transaction_count(
            wallet_address
        )

        raw_txn = self._exchange_router_contract_obj.functions.multicall(
            multicall_args
        ).build_transaction(
            {
                'value': value_amount,
                'chainId': self.config.chain_id,

                # TODO - this is NOT correct
                'gas': (
                    self._gas_limits_order_type.call(
                    ) + self._gas_limits_order_type.call()
                ),
                'maxFeePerGas': int(self.max_fee_per_gas),
                'maxPriorityFeePerGas': 0,
                'nonce': nonce
            }
        )

        if not self.debug_mode:
            signed_txn = self._connection.eth.account.sign_transaction(
                raw_txn, self.config.private_key
            )

            try:
                txn = signed_txn.rawTransaction
            except AttributeError:
                txn = signed_txn.raw_transaction

            tx_hash = self._connection.eth.send_raw_transaction(
                txn
            )
            self.log.info("Txn submitted!")
            self.log.info(
                "Check status: https://arbiscan.io/tx/0x{}".format(tx_hash.hex())
            )

            self.log.info("Transaction submitted!")

    def _get_prices(
        self, decimals: float, prices: float, is_open: bool = False,
        is_close: bool = False, is_swap: bool = False
    ):
        """
        Get Prices
        """
        self.log.info("Getting prices...")
        price = np.median(
            [
                float(prices[self.index_token_address]['maxPriceFull']),
                float(prices[self.index_token_address]['minPriceFull'])
            ]
        )

        # Depending on if open/close & long/short, we need to account for
        # slippage in a different way
        if is_open:
            if self.is_long:
                slippage = str(
                    int(float(price) + float(price) * self.slippage_percent)
                )
            else:
                slippage = str(
                    int(float(price) - float(price) * self.slippage_percent)
                )
        elif is_close:
            if self.is_long:
                slippage = str(
                    int(float(price) - float(price) * self.slippage_percent)
                )
            else:
                slippage = str(
                    int(float(price) + float(price) * self.slippage_percent)
                )
        else:
            slippage = 0

        acceptable_price_in_usd = (
            int(slippage) * 10 ** (decimals - PRECISION)
        )

        self.log.info(
            "Mark Price: ${:.4f}".format(price * 10 ** (decimals - PRECISION))
        )

        if acceptable_price_in_usd != 0:
            self.log.info(
                "Acceptable price: ${:.4f}".format(acceptable_price_in_usd)
            )

        return price, int(slippage), acceptable_price_in_usd

    def order_builder(self, is_open=False, is_close=False, is_swap=False):
        """
        Create Order
        """

        self.determine_gas_limits()
        gas_price = self._connection.eth.gas_price
        execution_fee = int(
            get_execution_fee(
                self._gas_limits,
                self._gas_limits_order_type,
                gas_price
            )
        )

        # Dont need to check approval when closing
        if not is_close and not self.debug_mode:
            self.check_for_approval()

        execution_fee = int(execution_fee * self.execution_buffer)

        markets = Markets(self.config).info
        initial_collateral_delta_amount = self.initial_collateral_delta_amount
        prices = OraclePrices(chain=self.config.chain).get_recent_prices()
        size_delta_price_price_impact = self.size_delta

        # when decreasing size delta must be negative
        if is_close:
            size_delta_price_price_impact = size_delta_price_price_impact * -1

        callback_gas_limit = 0
        min_output_amount = 0

        if is_open:
            order_type = order_types['market_increase']
        elif is_close:
            order_type = order_types['market_decrease']
        elif is_swap:
            order_type = order_types['market_swap']

            # Estimate amount of token out using a reader function, necessary
            # for multi swap
            estimated_output = self.estimated_swap_output(
                markets[self.swap_path[0]],
                self.collateral_address,
                initial_collateral_delta_amount
            )

            # this var will help to calculate the cost gas depending on the
            # operation
            self._get_limits_order_type = self._gas_limits['single_swap']
            if len(self.swap_path) > 1:
                estimated_output = self.estimated_swap_output(
                    markets[self.swap_path[1]],
                    "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
                    int(
                        estimated_output[
                            "out_token_amount"
                        ] - estimated_output[
                            "out_token_amount"
                        ] * self.slippage_percent
                    )
                )
                self._get_limits_order_type = self._gas_limits['swap_order']

            min_output_amount = estimated_output["out_token_amount"] - \
                estimated_output["out_token_amount"] * self.slippage_percent

        decrease_position_swap_type = decrease_position_swap_types['no_swap']

        should_unwrap_native_token = True
        referral_code = HexBytes(
            "0x0000000000000000000000000000000000000000000000000000000000000000"
        )
        user_wallet_address = self.config.user_wallet_address
        eth_zero_address = "0x0000000000000000000000000000000000000000"
        ui_ref_address = "0x0000000000000000000000000000000000000000"
        try:
            gmx_market_address = Web3.to_checksum_address(self.market_key)
        except AttributeError:
            gmx_market_address = Web3.toChecksumAddress(self.market_key)

        # parameters using to calculate execution price
        execution_price_parameters = {
            'data_store_address': (
                contract_map[self.config.chain]["datastore"]['contract_address']
            ),
            'market_key': self.market_key,
            'index_token_price': [
                int(prices[self.index_token_address]['maxPriceFull']),
                int(prices[self.index_token_address]['minPriceFull'])
            ],
            'position_size_in_usd': 0,
            'position_size_in_tokens': 0,
            'size_delta': size_delta_price_price_impact,
            'is_long': self.is_long
        }
        decimals = markets[self.market_key]['market_metadata']['decimals']

        price, acceptable_price, acceptable_price_in_usd = self._get_prices(
            decimals,
            prices,
            is_open,
            is_close,
            is_swap
        )

        mark_price = 0

        # mark price should be actual price when opening
        if is_open:
            mark_price = int(price)

        # Market address and acceptable price not important for swap
        if is_swap:
            acceptable_price = 0
            gmx_market_address = "0x0000000000000000000000000000000000000000"

        execution_price_and_price_impact_dict = get_execution_price_and_price_impact(
            self.config,
            execution_price_parameters,
            decimals
        )
        self.log.info(
            "Execution price: ${:.4f}".format(
                execution_price_and_price_impact_dict['execution_price']
            )
        )

        # Prevent txn from being submitted if execution price falls outside acceptable
        if is_open:
            if self.is_long:
                if execution_price_and_price_impact_dict[
                        'execution_price'] > acceptable_price_in_usd:
                    raise Exception("Execution price falls outside acceptable price!")
            elif not self.is_long:
                if execution_price_and_price_impact_dict[
                        'execution_price'] < acceptable_price_in_usd:
                    raise Exception("Execution price falls outside acceptable price!")
        elif is_close:
            if self.is_long:
                if execution_price_and_price_impact_dict[
                        'execution_price'] < acceptable_price_in_usd:
                    raise Exception("Execution price falls outside acceptable price!")
            elif not self.is_long:
                if execution_price_and_price_impact_dict[
                        'execution_price'] > acceptable_price_in_usd:
                    raise Exception("Execution price falls outside acceptable price!")

        user_wallet_address = convert_to_checksum_address(
            self.config,
            user_wallet_address
        )

        cancellation_receiver = user_wallet_address

        eth_zero_address = convert_to_checksum_address(
            self.config,
            eth_zero_address
        )
        ui_ref_address = convert_to_checksum_address(
            self.config,
            ui_ref_address
        )
        collateral_address = convert_to_checksum_address(
            self.config,
            self.collateral_address
        )

        auto_cancel = self.auto_cancel

        arguments = (
            (
                user_wallet_address,
                cancellation_receiver,
                eth_zero_address,
                ui_ref_address,
                gmx_market_address,
                collateral_address,
                self.swap_path
            ),
            (
                self.size_delta,
                self.initial_collateral_delta_amount,
                mark_price,
                acceptable_price,
                execution_fee,
                callback_gas_limit,
                int(min_output_amount),
                0
            ),
            order_type,
            decrease_position_swap_type,
            self.is_long,
            should_unwrap_native_token,
            auto_cancel,
            referral_code
        )

        # If the collateral is not native token (ie ETH/Arbitrum or AVAX/AVAX)
        # need to send tokens to vault

        value_amount = execution_fee
        if self.collateral_address != '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1' and not is_close:

            multicall_args = [
                HexBytes(self._send_wnt(value_amount)),
                HexBytes(
                    self._send_tokens(
                        self.collateral_address,
                        initial_collateral_delta_amount
                    )
                ),
                HexBytes(self._create_order(arguments))
            ]

        else:

            # send start token and execute fee if token is ETH or AVAX
            if is_open or is_swap:

                value_amount = initial_collateral_delta_amount + execution_fee

            multicall_args = [
                HexBytes(self._send_wnt(value_amount)),
                HexBytes(self._create_order(arguments))
            ]

        self._submit_transaction(
            user_wallet_address, value_amount, multicall_args, self._gas_limits
        )

    def _create_order(self, arguments):
        """
        Create Order
        """
        try:
            return self._exchange_router_contract_obj.encodeABI(
                fn_name="createOrder",
                args=[arguments],
            )
        except AttributeError:
            return self._exchange_router_contract_obj.encode_abi(
                abi_element_identifier="createOrder",
                args=[arguments],
            )

    def _send_tokens(self, arguments, amount):
        """
        Send tokens
        """
        try:
            return self._exchange_router_contract_obj.encodeABI(
                fn_name="sendTokens",
                args=(
                    self.collateral_address,
                    '0x31eF83a530Fde1B38EE9A18093A333D8Bbbc40D5',
                    amount
                ),
            )
        except AttributeError:
            return self._exchange_router_contract_obj.encode_abi(
                abi_element_identifier="sendTokens",
                args=(
                    self.collateral_address,
                    '0x31eF83a530Fde1B38EE9A18093A333D8Bbbc40D5',
                    amount
                ),
            )

    def _send_wnt(self, amount):
        """
        Send WNT
        """
        try:
            return self._exchange_router_contract_obj.encodeABI(
                fn_name='sendWnt',
                args=(
                    "0x31eF83a530Fde1B38EE9A18093A333D8Bbbc40D5",
                    amount
                )
            )
        except AttributeError:
            return self._exchange_router_contract_obj.encode_abi(
                abi_element_identifier='sendWnt',
                args=(
                    "0x31eF83a530Fde1B38EE9A18093A333D8Bbbc40D5",
                    amount
                )
            )
