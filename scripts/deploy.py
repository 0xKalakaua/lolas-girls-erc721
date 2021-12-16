#!/usr/bin/python3
import os
from brownie import Contraband, accounts, network, config

def main():
    dev = accounts.load("dev")
    admin = accounts.load("admin")
    wallet = dev.address
    print(network.show_active())
    publish_source = True # Not supported on Testnet
    name = "Lolas Girls"
    symbol = "LOLASGIRLS"
    base_uri = ""
    base_extension = ".json"
    # mint_price = 10000000000000000000
    mint_price = 1000000000000000
    max_supply = 150
    rabbits_address = "0x8E7c434B248d49D873D0F8448E0FcEc895b1b92D"
    bus_address = "0xCF4F33773bd0b5F89271143062EEF0C6Dd408063"
    Contraband.deploy(
            name,
            symbol,
            base_uri,
            base_extension,
            mint_price,
            max_supply,
            rabbits_address,
            bus_address,
            admin,
            wallet,
            {"from": dev},
            publish_source=publish_source
    )
