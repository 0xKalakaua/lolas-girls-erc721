// SPDX-License-Identifier: MIT

/**

    (\ /)   (\ /)   (\ /)
    ( . .)  ( . .)  ( . .)
   C(")(")  C(")(") C(")(")

  Tombheads x FTM DEAD x 0xKupe x 0xKalakaua - LolasGirls - NFT Collection -

*/

pragma solidity 0.8.0;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/access/AccessControlEnumerable.sol";

interface BusInterface {
    function getOwnerOfToken(address tokenContract, uint tokenId)
        external
        view
        returns (address);
}

contract LolasGirls is AccessControlEnumerable, ERC721Enumerable, ERC721URIStorage {
    using Counters for Counters.Counter;
    using Strings for uint;

    Counters.Counter public tokenIdTracker;
    uint public max_supply;
    uint public price;

    mapping(uint => bool) private hasLolasGirl;
    string private _baseTokenURI;
    string private _baseExtension;
    bool private _openMint;
    IERC721 private _degenerabbits;
    BusInterface private _bus;
    address payable private _wallet;

    constructor (
        string memory name,
        string memory symbol, 
        string memory baseURI,
        string memory baseExtension,
        uint mintPrice,
        uint max,
        address rabbitsAddress,
        address busAddress,
        address admin,
        address payable wallet
    )
        ERC721 (name, symbol)
    {
        tokenIdTracker.increment(); // Start collection at 1
        max_supply = max;
        price = mintPrice;
        _baseTokenURI = baseURI;
        _baseExtension = baseExtension;
        _openMint = false;
        _degenerabbits = IERC721(rabbitsAddress);
        _bus = BusInterface(busAddress);
        _wallet = wallet;
        _setupRole(DEFAULT_ADMIN_ROLE, admin);
        _setupRole(DEFAULT_ADMIN_ROLE, wallet);
        _setupRole(DEFAULT_ADMIN_ROLE, msg.sender);
    }

    modifier onlyAdmin() {
        require(hasRole(DEFAULT_ADMIN_ROLE, msg.sender), "LolasGirls: caller is not admin");
        _;
    }

    function setBaseURI(string memory baseURI) external onlyAdmin {
        _baseTokenURI = baseURI;
    }

    function setBaseExtension(string memory baseExtension) external onlyAdmin {
        _baseExtension = baseExtension;
    }

    function setTokenURI(uint tokenId, string memory _tokenURI) external onlyAdmin {
        _setTokenURI(tokenId, _tokenURI);
    }

    function setPrice(uint mintPrice) external onlyAdmin {
        price = mintPrice;
    }

    function setMint(bool openMint) external onlyAdmin {
        _openMint = openMint;
    }

    function mint(uint rabbitTokenId) public payable {
        require(_openMint == true, "LolasGirls: minting is currently not open");
        require(tokenIdTracker.current() <= max_supply, "LolasGirls: all tokens have been minted");
        require(msg.value == price, "LolasGirls: amount sent is incorrect");
        require(
            hasLolasGirl[rabbitTokenId] == false,
            "LolasGirls: this Degenerabbit has already minted a LolasGirl"
        );
        if (_hasRabbitInBus(msg.sender, rabbitTokenId) == false) {
            require(
                _degenerabbits.ownerOf(rabbitTokenId) == msg.sender,
                "LolasGirls: caller is not owner of that Degenerabbit"
            );
        }
        _safeMint(msg.sender, tokenIdTracker.current());
        _setTokenURI(
            tokenIdTracker.current(),
            string(abi.encodePacked(tokenIdTracker.current().toString(), _baseExtension))
        );
        hasLolasGirl[rabbitTokenId] = true;
        tokenIdTracker.increment();

        _wallet.transfer(msg.value);
    }

    function hasDegenerabbitMintedLolasGirl(uint rabbitTokenId) public view returns (bool) {
        return hasLolasGirl[rabbitTokenId];
    }

    function tokenURI(uint tokenId)
        public
        view
        override(ERC721, ERC721URIStorage)
        returns (string memory)
    {
        return ERC721URIStorage.tokenURI(tokenId);
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        virtual override(AccessControlEnumerable, ERC721, ERC721Enumerable)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }

    function _baseURI() internal view virtual override returns (string memory) {
        return _baseTokenURI;
    }

    function _burn(uint tokenId) internal virtual override(ERC721, ERC721URIStorage) {
        return ERC721URIStorage._burn(tokenId);
    }

    function _beforeTokenTransfer(address from, address to, uint tokenId)
        internal
        virtual override(ERC721, ERC721Enumerable)
    {
        super._beforeTokenTransfer(from, to, tokenId);
    }

    function _hasRabbitInBus(address sender, uint rabbitTokenId) private view returns (bool) {
        if (_bus.getOwnerOfToken(address(_degenerabbits), rabbitTokenId) == sender) {
            return true;
        }
        return false;

    }
}
