import pytest
import brownie
from brownie import network, accounts, LolasGirls, MockERC721, Custody

@pytest.fixture
def rabbits():
    dev = accounts[0]
    max_supply = 10
    rabbits = MockERC721.deploy("Rabbits Test", "RABBITS", max_supply, dev, {'from': dev})
    for i in range(max_supply):
        tx = rabbits.mint(f"Rabbit #{i+1}", {'from': dev})

    rabbits.safeTransferFrom(dev, accounts[1], 8, {'from': dev})
    rabbits.safeTransferFrom(dev, accounts[1], 9, {'from': dev})
    rabbits.safeTransferFrom(dev, accounts[2], 10, {'from': dev})
    return rabbits

@pytest.fixture
def bus(rabbits):
    dev = accounts[0]
    bus = Custody.deploy({'from': dev})
    bus.addContract(rabbits.address,{'from': dev})

    return bus, rabbits

@pytest.fixture
def contracts(bus):
    bus, rabbits = bus
    name = "LolasGirls Test"
    symbol = "LOLASGIRLS"
    base_uri = "base_uri/"
    base_extension = ".json"
    mint_price = 1000000000000000000
    max_supply = 10
    rabbits_address = rabbits.address
    bus_address = bus.address
    admin = accounts[9]
    wallet = accounts[8]
    lolas_girls = LolasGirls.deploy(
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
                            {"from": accounts[0]}
                )
    return lolas_girls, rabbits, bus

def test_initial_state(contracts):
    lolas_girls, rabbits, bus = contracts

    assert accounts[0].balance() == "100 ether"
    assert rabbits.balanceOf(accounts[0]) == 7
    assert rabbits.balanceOf(accounts[1]) == 2
    assert rabbits.balanceOf(accounts[2]) == 1
    for i in range(3, 10):
        assert rabbits.balanceOf(accounts[i]) == 0

def test_valid_mint(contracts):
    lolas_girls, rabbits, _ = contracts
    lolas_girls.setMint(True, {"from": accounts[0]})
    initial_wallet_balance = accounts[8].balance()
    for i in range(3):
        account = accounts[i]
        for j in range(rabbits.balanceOf(account)):
            account_balance = account.balance()
            rabbit_id = rabbits.tokenOfOwnerByIndex(account, j)
            token_id = lolas_girls.tokenIdTracker()
            lolas_girls.mint(rabbit_id, {"from": account, "value": "1 ether"})
            assert lolas_girls.ownerOf(token_id) == account
            assert account.balance() == account_balance - "1 ether"
            assert lolas_girls.tokenURI(token_id) == f"base_uri/{token_id}.json"
    assert accounts[8].balance() == initial_wallet_balance + "10 ether"
    assert lolas_girls.totalSupply() == 10

def test_only_admin(contracts):
    lolas_girls, rabbits, _ = contracts
    admins = [0, 8, 9]
    rabbit_index = 0
    for i in range(10):
        if i in admins:
            lolas_girls.setMint(True, {"from": accounts[i]})
            rabbit_id = rabbits.tokenOfOwnerByIndex(accounts[0], rabbit_index)
            rabbit_index += 1
            lolas_girls.mint(rabbit_id, {"from": accounts[0], "value": "1 ether"})
            lolas_girls.setBaseURI("test/", {"from": accounts[i]})
            lolas_girls.setTokenURI(1, "new tokenURI", {"from": accounts[i]})
            lolas_girls.setPrice("1 ether", {"from": accounts[i]})
        else:
            with brownie.reverts():
                lolas_girls.setMint(True, {"from": accounts[i]})
            with brownie.reverts():
                lolas_girls.setBaseURI("test/", {"from": accounts[i]})
            with brownie.reverts():
                lolas_girls.setTokenURI(1, "new tokenURI", {"from": accounts[i]})
            with brownie.reverts():
                lolas_girls.setPrice("0.5 ether", {"from": accounts[i]})

def test_change_mint_price(contracts):
    lolas_girls, rabbits, _ = contracts
    wallet_balance = accounts[8].balance()
    minter_balance = accounts[1].balance()
    lolas_girls.setMint(True, {"from": accounts[0]})
    rabbit_id = rabbits.tokenOfOwnerByIndex(accounts[1], 0)
    lolas_girls.mint(rabbit_id, {"from": accounts[1], "value": "1 ether"})
    lolas_girls.setPrice("0.5 ether", {"from": accounts[8]})
    rabbit_id = rabbits.tokenOfOwnerByIndex(accounts[1], 1)
    with brownie.reverts():
        lolas_girls.mint(rabbit_id, {"from": accounts[1], "value": "1 ether"})
    lolas_girls.mint(rabbit_id, {"from": accounts[1], "value": "0.5 ether"})
    assert accounts[1].balance() == minter_balance - "1.5 ether"
    assert accounts[8].balance() == wallet_balance + "1.5 ether"

def test_minting_closed(contracts):
    lolas_girls, rabbits, _ = contracts
    for i in range(3):
        account = accounts[i]
        for j in range(rabbits.balanceOf(account)):
            rabbit_id = rabbits.tokenOfOwnerByIndex(account, j)
            with brownie.reverts():
                lolas_girls.mint(rabbit_id, {"from": account, "value": "1 ether"})
    assert lolas_girls.totalSupply() == 0
    lolas_girls.setMint(True, {"from": accounts[0]})
    rabbit_id = rabbits.tokenOfOwnerByIndex(accounts[0], 0)
    lolas_girls.mint(rabbit_id, {"from": accounts[0], "value": "1 ether"})
    assert lolas_girls.totalSupply() == 1

def test_invalid_mint_max_reached(contracts):
    lolas_girls, rabbits, _ = contracts
    lolas_girls.setMint(True, {"from": accounts[0]})
    initial_wallet_balance = accounts[8].balance()
    for i in range(3):
        account = accounts[i]
        for j in range(rabbits.balanceOf(account)):
            account_balance = account.balance()
            rabbit_id = rabbits.tokenOfOwnerByIndex(account, j)
            token_id = lolas_girls.tokenIdTracker()
            lolas_girls.mint(rabbit_id, {"from": account, "value": "1 ether"})
            assert lolas_girls.ownerOf(token_id) == account
            assert account.balance() == account_balance - "1 ether"
            assert lolas_girls.tokenURI(token_id) == f"base_uri/{token_id}.json"
    assert accounts[8].balance() == initial_wallet_balance + "10 ether"
    assert lolas_girls.totalSupply() == 10
    with brownie.reverts():
        lolas_girls.mint(1, {"from": accounts[0], "value": "1 ether"})

def test_incorrect_mint_price(contracts):
    lolas_girls, rabbits, _ = contracts
    lolas_girls.setMint(True, {"from": accounts[0]})
    rabbit_id = rabbits.tokenOfOwnerByIndex(accounts[2], 0)
    with brownie.reverts():
        lolas_girls.mint(rabbit_id, {"from": accounts[2], "value": "0.9 ether"})
    with brownie.reverts():
        lolas_girls.mint(rabbit_id, {"from": accounts[2], "value": "1.1 ether"})
    lolas_girls.mint(rabbit_id, {"from": accounts[2], "value": "1 ether"})

def test_rabbit_double_mint(contracts):
    lolas_girls, rabbits, bus = contracts
    lolas_girls.setMint(True, {"from": accounts[0]})
    rabbit_id_one = rabbits.tokenOfOwnerByIndex(accounts[1], 0)
    rabbit_id_two = rabbits.tokenOfOwnerByIndex(accounts[1], 1)
    lolas_girls.mint(rabbit_id_one, {"from": accounts[1], "value": "1 ether"})
    with brownie.reverts():
        lolas_girls.mint(rabbit_id_one, {"from": accounts[1], "value": "1 ether"})
    rabbits.setApprovalForAll(bus.address, True, {'from': accounts[1]})
    bus.deposit(rabbits.address, rabbit_id_one, {'from': accounts[1]})
    bus.deposit(rabbits.address, rabbit_id_two, {'from': accounts[1]})
    assert rabbits.ownerOf(rabbit_id_one) == bus.address 
    assert rabbits.ownerOf(rabbit_id_two) == bus.address
    with brownie.reverts():
        lolas_girls.mint(rabbit_id_one, {"from": accounts[1], "value": "1 ether"})
    lolas_girls.mint(rabbit_id_two, {"from": accounts[1], "value": "1 ether"})
    with brownie.reverts():
        lolas_girls.mint(rabbit_id_two, {"from": accounts[1], "value": "1 ether"})
    assert lolas_girls.balanceOf(accounts[1]) == 2

def test_caller_is_not_owner_rabbit(contracts):
    lolas_girls, rabbits, bus = contracts
    lolas_girls.setMint(True, {"from": accounts[0]})
    rabbit_id_acc_0 = rabbits.tokenOfOwnerByIndex(accounts[0], 0)
    rabbit_id_acc_1 = rabbits.tokenOfOwnerByIndex(accounts[1], 0)
    rabbits.setApprovalForAll(bus.address, True, {'from': accounts[0]})
    bus.deposit(rabbits.address, rabbit_id_acc_0, {'from': accounts[0]})
    with brownie.reverts():
        lolas_girls.mint(rabbit_id_acc_0, {"from": accounts[2], "value": "1 ether"})
    with brownie.reverts():
        lolas_girls.mint(rabbit_id_acc_1, {"from": accounts[2], "value": "1 ether"})

def test_tokenURI(contracts):
    lolas_girls, rabbits, _ = contracts
    lolas_girls.setMint(True, {"from": accounts[0]})
    for i in range(3):
        rabbit_id = rabbits.tokenOfOwnerByIndex(accounts[i], 0)
        lolas_girls.mint(rabbit_id, {"from": accounts[i], "value": "1 ether"})
    assert lolas_girls.tokenURI(1) == "base_uri/1.json"
    assert lolas_girls.tokenURI(2) == "base_uri/2.json"
    assert lolas_girls.tokenURI(3) == "base_uri/3.json"

    lolas_girls.setTokenURI(1, "new #1", {"from": accounts[9]})
    lolas_girls.setTokenURI(3, "new #3", {"from": accounts[8]})
    assert lolas_girls.tokenURI(1) == "base_uri/" + "new #1"
    assert lolas_girls.tokenURI(3) == "base_uri/" + "new #3"

    lolas_girls.setBaseURI("", {"from": accounts[8]})
    assert lolas_girls.tokenURI(1) == "new #1"
    assert lolas_girls.tokenURI(3) == "new #3"

    with brownie.reverts():
        lolas_girls.setTokenURI(3, "invalid #3", {"from": accounts[2]})

def test_mint_with_rabbit_in_bus(contracts):
    lolas_girls, rabbits, bus = contracts
    lolas_girls.setMint(True, {"from": accounts[0]})
    rabbit_id_acc_0 = rabbits.tokenOfOwnerByIndex(accounts[0], 0)
    rabbit_id_acc_2 = rabbits.tokenOfOwnerByIndex(accounts[2], 0)
    rabbits.setApprovalForAll(bus.address, True, {'from': accounts[0]})
    rabbits.setApprovalForAll(bus.address, True, {'from': accounts[2]})
    bus.deposit(rabbits.address, rabbit_id_acc_0, {'from': accounts[0]})
    bus.deposit(rabbits.address, rabbit_id_acc_2, {'from': accounts[2]})

    assert rabbits.balanceOf(accounts[0]) == 6
    assert rabbits.balanceOf(accounts[1]) == 2
    assert rabbits.balanceOf(accounts[2]) == 0
    assert rabbits.balanceOf(bus) == 2

    token_id = lolas_girls.tokenIdTracker()
    lolas_girls.mint(rabbit_id_acc_0, {"from": accounts[0], "value": "1 ether"})
    assert lolas_girls.ownerOf(token_id) == accounts[0]
    token_id = lolas_girls.tokenIdTracker()
    lolas_girls.mint(rabbit_id_acc_2, {"from": accounts[2], "value": "1 ether"})
    assert lolas_girls.ownerOf(token_id) == accounts[2]
