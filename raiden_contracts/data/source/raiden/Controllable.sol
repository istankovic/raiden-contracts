// SPDX-License-Identifier: MIT
pragma solidity 0.7.6;

contract Controllable {

    address public controller;

    modifier onlyController() {
        require(msg.sender == controller, "Can only be called by controller");
        _;
    }

    /// @notice Changes the controller who is allowed to deprecate or remove limits.
    /// Can only be called by the controller.
    function changeController(address new_controller)
        external
        onlyController
    {
        controller = new_controller;
    }
}
