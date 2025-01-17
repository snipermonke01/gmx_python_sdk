import logging

from web3 import Web3

from hexbytes import HexBytes

from ..get.get_markets import Markets
from ..get.get_oracle_prices import OraclePrices

from ..gmx_utils import convert_to_checksum_address, \
    get_exchange_router_contract, create_connection, \
    determine_swap_route, contract_map, \
    get_estimated_withdrawal_amount_out, check_web3_correct_version

from ..approve_token_for_spend import check_if_approved

from ..gas_utils import get_execution_fee

is_newer_version, version = check_web3_correct_version()
if is_newer_version:
    logging.warning(f"Current version of py web3 ({version}), may result in errors.")


class Withdraw:

    def __init__(
        self,
        config,
        market_key: str,
        out_token: str,
        gm_amount: int,
        max_fee_per_gas: int = None,
        debug_mode: bool = False,
        execution_buffer: float = 1.1

    ) -> None:
        self.config = config
        self.market_key = market_key
        self.out_token = out_token
        self.gm_amount = gm_amount
        self.long_token_swap_path = []
        self.short_token_swap_path = []
        self.max_fee_per_gas = max_fee_per_gas
        self.debug_mode = debug_mode
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
            config
        )

        self._connection = create_connection(config)

        self.all_markets_info = Markets(config).get_available_markets()

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
                          self.market_key,
                          self.gm_amount,
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

        nonce = self._connection.eth.get_transaction_count(
            user_wallet_address
        )

        raw_txn = self._exchange_router_contract_obj.functions.multicall(
            multicall_args
        ).build_transaction(
            {
                'value': value_amount,
                'chainId': self.config.chain_id,

                # TODO - this is NOT correct
                'gas': (
                    self._gas_limits_order_type.call() + self._gas_limits_order_type.call()
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
            except TypeError:
                txn = signed_txn.raw_transaction

            tx_hash = self._connection.eth.send_raw_transaction(
                txn
            )
            self.log.info("Txn submitted!")
            self.log.info(
                "Check status: https://arbiscan.io/tx/{}".format(tx_hash.hex())
            )

            self.log.info("Transaction submitted!")

    def create_withdraw_order(self):

        user_wallet_address = self.config.user_wallet_address

        self.determine_gas_limits()
        if not self.debug_mode:
            self.check_for_approval()

        should_unwrap_native_token = True

        eth_zero_address = "0x0000000000000000000000000000000000000000"
        ui_ref_address = "0x0000000000000000000000000000000000000000"

        user_wallet_address = convert_to_checksum_address(
            self.config,
            user_wallet_address
        )
        eth_zero_address = convert_to_checksum_address(
            self.config,
            eth_zero_address
        )
        ui_ref_address = convert_to_checksum_address(
            self.config,
            ui_ref_address
        )

        min_long_token_amount, min_short_token_amount = self._estimate_withdrawal()

        # Giving a 10% buffer here
        execution_fee = int(
            get_execution_fee(
                self._gas_limits,
                self._gas_limits_order_type,
                self._connection.eth.gas_price
            ) * self.execution_buffer
        )

        callback_gas_limit = 0

        self._determine_swap_paths()

        arguments = (
            user_wallet_address,
            eth_zero_address,
            ui_ref_address,
            self.market_key,
            self.long_token_swap_path,
            self.short_token_swap_path,
            min_long_token_amount,
            min_short_token_amount,
            should_unwrap_native_token,
            execution_fee,
            callback_gas_limit
        )

        # Defined empty list to append keccak hash too
        multicall_args = []

        # Send gas to withdrawVault
        multicall_args = multicall_args + [HexBytes(
            self._send_wnt(
                int(execution_fee)
            )
        )]

        # Send GM tokens to withdrawVault
        multicall_args = multicall_args + [HexBytes(
            self._send_tokens(
                self.market_key,
                self.gm_amount
            )
        )]

        # Send parameters for our swap
        multicall_args = multicall_args + [HexBytes(
            self._create_order(
                arguments
            )
        )]

        self._submit_transaction(
            user_wallet_address,
            int(execution_fee),
            multicall_args,
            self._gas_limits
        )

    def _determine_swap_paths(self):
        """
        Calculate swap paths for long and short tokens

        """

        market = self.all_markets_info[self.market_key]

        if market['long_token_address'] != self.out_token:
            try:
                self.long_token_swap_path, requires_multi_swap = determine_swap_route(
                    self.all_markets_info,
                    self.out_token,
                    market['long_token_address']
                )
            except Exception:
                pass

        if market['short_token_address'] != self.out_token:
            try:
                self.short_token_swap_path, requires_multi_swap = determine_swap_route(
                    self.all_markets_info,
                    self.out_token,
                    market['short_token_address']
                )
            except Exception:
                pass

    def _create_order(self, arguments):
        """
        Create Order
        """
        try:
            return self._exchange_router_contract_obj.encodeABI(
                fn_name="createWithdrawal",
                args=[arguments],
            )
        except TypeError:
            return self._exchange_router_contract_obj.encode_abi(
                fn_name="createWithdrawal",
                args=[arguments],
            )

    def _send_wnt(self, amount):
        """
        Send WNT
        """
        try:
            return self._exchange_router_contract_obj.encodeABI(
                fn_name='sendWnt',
                args=(
                    "0x0628D46b5D145f183AdB6Ef1f2c97eD1C4701C55",
                    amount
                )
            )
        except TypeError:
            return self._exchange_router_contract_obj.encode_abi(
                fn_name='sendWnt',
                args=(
                    "0x0628D46b5D145f183AdB6Ef1f2c97eD1C4701C55",
                    amount
                )
            )

    def _send_tokens(self, token_address, amount):
        """
        Send tokens
        """
        try:
            return self._exchange_router_contract_obj.encodeABI(
                fn_name="sendTokens",
                args=(
                    token_address,
                    '0x0628D46b5D145f183AdB6Ef1f2c97eD1C4701C55',
                    amount
                ),
            )
        except TypeError:
            return self._exchange_router_contract_obj.encode_abi(
                fn_name="sendTokens",
                args=(
                    token_address,
                    '0x0628D46b5D145f183AdB6Ef1f2c97eD1C4701C55',
                    amount
                ),
            )

    def _estimate_withdrawal(self):
        """
        Estimate the amount tokens output after burning our GM

        Returns
        -------
        list
            list of amount of long and short tokens.

        """

        data_store_contract_address = contract_map[
            self.config.chain
        ]['datastore']['contract_address']

        market = self.all_markets_info[self.market_key]
        oracle_prices_dict = OraclePrices(chain=self.config.chain).get_recent_prices()

        index_token_address = market['index_token_address']
        long_token_address = market['long_token_address']
        short_token_address = market['short_token_address']

        market_addresses = [self.market_key,
                            index_token_address,
                            long_token_address,
                            short_token_address]
        prices = (
            (
                int(oracle_prices_dict[index_token_address]['minPriceFull']),
                int(oracle_prices_dict[index_token_address]['maxPriceFull'])
            ),
            (
                int(oracle_prices_dict[long_token_address]['minPriceFull']),
                int(oracle_prices_dict[long_token_address]['maxPriceFull'])
            ),
            (
                int(oracle_prices_dict[short_token_address]['minPriceFull']),
                int(oracle_prices_dict[short_token_address]['maxPriceFull'])
            ))

        parameters = {
            "data_store_address": data_store_contract_address,
            "market_addresses": market_addresses,
            "token_prices_tuple": prices,
            "gm_amount": self.gm_amount,
            "ui_fee_receiver": "0x0000000000000000000000000000000000000000"
        }

        return get_estimated_withdrawal_amount_out(self.config, parameters)
