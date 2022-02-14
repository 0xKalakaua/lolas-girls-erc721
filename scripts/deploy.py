#!/usr/bin/python3
import os
from brownie import LolasGirls, accounts, network, config

def main():
    dev = accounts.load("dev")
    admin = "0xbc26d11E8815416B3E3378F0f238299E34E14a4b" # Mandy's wallet
    wallet = dev.address
    print(network.show_active())
    publish_source = False # Not supported on Testnet
    name = "Lolas Girls"
    symbol = "LOLASGIRLS"
    base_uri = ""
    base_extension = ".json"
    not_revealed_uri = "ipfs://bafkreige7nrsacbexly43wwacgcxf5it3q72ae6ojwcp5ehgz2ckb7tw6m"
    mint_price = 5000000000000000000 # 5 ftm
    max_supply = 2000
    rabbits_address = "0x8E7c434B248d49D873D0F8448E0FcEc895b1b92D"
    bus_address = "0xCF4F33773bd0b5F89271143062EEF0C6Dd408063"
    LolasGirls.deploy(
            name,
            symbol,
            base_uri,
            base_extension,
            not_revealed_uri,
            mint_price,
            max_supply,
            rabbits_address,
            bus_address,
            admin,
            wallet,
            {"from": dev},
            publish_source=publish_source
    )
