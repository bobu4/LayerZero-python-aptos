from aptos_sdk.client import RestClient
from src.uln.uln_signer import UlnSigner


class UlnConfig:
    executor_address = '0x1d8727df513fa2a8785d0834e40b34223daff1affc079574082baadb74b66ee4'
    oracle_address = '0x12e12de0af996d9611b0b78928cd9f4cbf50d94d972043cdd829baa77a78929b'
    layerzero_address = '0x54ad3d30af77b60d939ae356e6606de9a4da67583f02b962d2d3f2e481484e90'
    bridge_address = '0xf22bede237a07e121b56d91a491eb7bcdfd1f5907926a9e58338f964a01b17fa'
    module = f'{layerzero_address}::uln_config'
    module_name = 'layerzero::uln_config'

    def __init__(self, sdk: RestClient):
        self.sdk = sdk
        self.uln_signer = UlnSigner(sdk)

    def get_default_app_config(self, dst_chain_id: int):
        resource = self.sdk.account_resource(
            self.layerzero_address,
            f"{self.module}::DefaultUlnConfig"
        )

        return self.sdk.get_table_item(
            resource['data']['config']['handle'],
            key_type='u64',
            value_type=f'{self.module}::UlnConfig',
            key=str(dst_chain_id),
        )

    def get_app_config(self, ua_address: str, dst_chain_id: int):
        # TODO: RESOLVE IT FOR GET_TABLE_ITEM
        # aptos_sdk.client.ApiError: {"message":"Table Item not found by Table handle(0xf576de3aafdcd17b912476f145c1c839ee34edc71a5fa7633d8267df0b2501c4), Table key({\"ua_address\":\"0xf22bede237a07e121b56d91a491eb7bcdfd1f5907926a9e58338f964a01b17fa\",\"chain_id\":\"110\"}) and Ledger version(169788690)","error_code":"table_item_not_found","vm_error_code":null}
        default_config = self.get_default_app_config(dst_chain_id)  # Do we need to merge it?
        resource = self.sdk.account_resource(
            self.layerzero_address,
            f"{self.module}::UaUlnConfig"
        )

        config = self.sdk.get_table_item(
            resource['data']['config']['handle'],
            key_type=f"{self.module}::UaConfigKey",
            value_type=f"{self.module}::UlnConfig",
            key={
                "ua_address": ua_address,
                "chain_id": dst_chain_id
            }
        )

        # TODO: No merged config

        return config

    def quote_fee(self, ua_address: str, dst_chain_id: int, payload_size: int) -> int:
        config = self.get_app_config(ua_address, dst_chain_id)
        oracle_fee = self.uln_signer.get_fee(self.oracle_address, dst_chain_id)
        relayer_fee = self.uln_signer.get_fee(self.executor_address, dst_chain_id)
        treasury_config_resource = self.sdk.account_resource(
            self.layerzero_address,
            f"{self.layerzero_address}::msglib_v1_0::GlobalStore"
        )
        treasury_fee_bps = treasury_config_resource['data']['treasury_fee_bps']
        total_fee = relayer_fee['base_fee'] + relayer_fee['fee_per_byte'] * payload_size
        total_fee += oracle_fee['base_fee'] + oracle_fee['fee_per_byte'] * payload_size
        total_fee += (treasury_fee_bps * total_fee) / 10000
        return total_fee
