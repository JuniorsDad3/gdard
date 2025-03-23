// contracts/LandRegistry.sol
pragma solidity ^0.8.0;

contract LandRegistry {
    struct LandRecord {
        address owner;
        uint256 parcelId;
        string location;
        uint256 timestamp;
    }
    
    mapping(uint256 => LandRecord) public records;
    
    event OwnershipTransferred(
        uint256 indexed parcelId,
        address indexed from,
        address indexed to
    );

    function registerLand(uint256 parcelId, string memory location) public {
        records[parcelId] = LandRecord(
            msg.sender,
            parcelId,
            location,
            block.timestamp
        );
    }
    
    function transferOwnership(uint256 parcelId, address newOwner) public {
        require(records[parcelId].owner == msg.sender, "Not owner");
        records[parcelId].owner = newOwner;
        emit OwnershipTransferred(parcelId, msg.sender, newOwner);
    }
}