// SPDX-License-Identifier: MIT
pragma solidity 0.8.0;

import "@openzeppelin/contracts/token/ERC721/IERC721Receiver.sol";
import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract Custody is IERC721Receiver, Ownable {

    event ContractAdded(address tokenContract);
    event ContractRemoved(address tokenContract);
    event TokenAddedToCustody(address tokenContract, uint tokenId, address onBehalfOf);
    event TokenRemovedFromCustody(address tokenContract, uint tokenId, address onBehalfOf);

    struct CustodyRecord {
        uint custodiedAt; // blockNumber
        uint index; // index in _tokensByContract
        uint ownerIndex; // index in _tokensByContractAndOwner
        address owner; // the wallet that custodied the token
    }

    /**
    * @dev [tokenContract][tokenId]: CustodyRecord
    * so we can confirm a user owns a certain token before w/drawal
    */
    mapping(address => mapping(uint => CustodyRecord)) private _custodyRecords;

    struct ContractRecord {
        bool isActive; // whether the record can be used
        uint index; // the index in our list of contracts
        uint[] tokensInCustody; // array of tokenIds in custody for this contract
        mapping(address => uint[]) tokensByOwner; // [ownerAddress]: array of tokenIds for this contract and owner
    }

    /**
    * @dev [tokenContract]: ContractRecord
    */
    mapping(address => ContractRecord) private _contractRecords;

    /**
    * @dev a list of the NFT contracts we have in custody right now
    * so we can enumerate over each contract
    */
    address[] _tokenContractsInCustody;

    function _popFromIntArray(uint index, uint[] storage array) internal returns (uint) {
        uint lastValue = array[array.length - 1];
        if (index != array.length - 1) {
            array[index] = lastValue;
        }
        array.pop();
        return lastValue;
    }

    /**
    * @dev add a contract to the list that we can custody
    */
    function addContract(address tokenContract) public onlyOwner {
        require(_contractRecords[tokenContract].isActive == false, "Contract already active");
        uint index = _tokenContractsInCustody.length;
        ContractRecord storage contractRecord = _contractRecords[tokenContract];
        contractRecord.index = index;
        contractRecord.isActive = true;
        _tokenContractsInCustody.push(tokenContract);
        emit ContractAdded(tokenContract);
    }

    /**
    * @dev remove a contract from the list that we can custody
    */
    function removeContract(address tokenContract) public onlyOwner {
        require(_contractRecords[tokenContract].isActive == true, "Contract is not currently active");
        require(_contractRecords[tokenContract].tokensInCustody.length == 0, "There are still tokens custodied for this contract");

        uint index = _contractRecords[tokenContract].index;
        if (index != _tokenContractsInCustody.length - 1) {
            address lastContractInList = _tokenContractsInCustody[_tokenContractsInCustody.length - 1];
            _tokenContractsInCustody[index] = lastContractInList;
            _contractRecords[lastContractInList].index = index;
        }
        _tokenContractsInCustody.pop();
        delete _contractRecords[tokenContract];
        emit ContractRemoved(tokenContract);
    }


    /**
    * @dev deposit a single token for a given contract
    */
    function deposit(address tokenContract, uint256 tokenId) public {

        // add the token to our tokensInCustody list
        uint index = _contractRecords[tokenContract].tokensInCustody.length;
        _contractRecords[tokenContract].tokensInCustody.push(tokenId);

        // add the token to our tokensByOwner list
        uint ownerIndex = _contractRecords[tokenContract].tokensByOwner[msg.sender].length;
        _contractRecords[tokenContract].tokensByOwner[msg.sender].push(tokenId);

        // create a new CustodyRecord for this token
        CustodyRecord storage record = _custodyRecords[tokenContract][tokenId];
        record.custodiedAt = block.number;
        record.index = index;
        record.ownerIndex = ownerIndex;
        record.owner = msg.sender;

        // transfer the token in
        IERC721(tokenContract).safeTransferFrom(msg.sender, address(this), tokenId);
        emit TokenAddedToCustody(tokenContract, tokenId, msg.sender);
    }

    /**
    * @dev withdraw a single token for a given contract
    */
    function withdraw(address tokenContract, uint256 tokenId) public {
        require(_custodyRecords[tokenContract][tokenId].owner == msg.sender, "Requestor does not own this token");

        // remove the token from our tokensInCustody list
        uint indexOfRemovedToken = _custodyRecords[tokenContract][tokenId].index;
        uint lastTokenId = _popFromIntArray(indexOfRemovedToken, _contractRecords[tokenContract].tokensInCustody);
        _custodyRecords[tokenContract][lastTokenId].index = indexOfRemovedToken;

        // remove the token from our _tokensByContractAndOwner list
        uint ownerIndexOfRemovedToken = _custodyRecords[tokenContract][tokenId].ownerIndex;
        uint lastTokenIdInOwnerIndex = _popFromIntArray(ownerIndexOfRemovedToken, _contractRecords[tokenContract].tokensByOwner[msg.sender]);
        _custodyRecords[tokenContract][lastTokenIdInOwnerIndex].ownerIndex = ownerIndexOfRemovedToken;

        // remove the CustodyRecord
        delete _custodyRecords[tokenContract][tokenId];

        // transfer the token out
        IERC721(tokenContract).safeTransferFrom(address(this), msg.sender, tokenId);
        emit TokenRemovedFromCustody(tokenContract, tokenId, msg.sender);
    }

    /**
    * @dev get a list of contracts (projects) currently custodied
    */
    function getContractsInCustody() public view returns (address[] memory) {
        return _tokenContractsInCustody;
    }

    /**
    * @dev get a list of tokens currently custodied for a single contract
    */
    function getCustodiedTokensForContract(address tokenContract) public view returns (uint[] memory) {
        return _contractRecords[tokenContract].tokensInCustody;
    }

    /**
    * @dev get a list of tokens currently custodied for a single contract and single owner
    */
    function getCustodiedTokensForOwner(address tokenContract, address owner) public view returns (uint[] memory) {
        return _contractRecords[tokenContract].tokensByOwner[owner];
    }

    /**
    * @dev get the owner of a given token
    */
    function getOwnerOfToken(address tokenContract, uint tokenId) public view returns (address) {
        return _custodyRecords[tokenContract][tokenId].owner;
    }

    /**
    * @dev get the token at a given index in our contract record
    */
    function getTokenIdAtIndex(address tokenContract, uint index) public view returns (uint) {
        return _contractRecords[tokenContract].tokensInCustody[index];
    }

    /**
    * @dev get the token at a given index in our contract record
    */
    function getTokenIdAtOwnerIndex(address tokenContract, uint index, address owner) public view returns (uint) {
        return _contractRecords[tokenContract].tokensByOwner[owner][index];
    }

    function onERC721Received(address operator, address from, uint256 tokenId, bytes calldata data) public override returns (bytes4) {
        return IERC721Receiver(this).onERC721Received.selector;
    }
}
