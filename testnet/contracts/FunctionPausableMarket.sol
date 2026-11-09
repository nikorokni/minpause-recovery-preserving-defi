// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface ITestToken {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

/// @notice A deliberately simplified, test-only lending market.
/// @dev donateToReserves intentionally omits a post-action health check to model
///      the control surface implicated in the Euler incident. No real funds.
contract FunctionPausableMarket {
    ITestToken public immutable asset;
    address public immutable guardian;
    uint256 public constant LIQUIDATION_THRESHOLD_BPS = 8_000;

    mapping(address => uint256) public collateral;
    mapping(address => uint256) public debt;
    mapping(bytes4 => bool) public functionPaused;
    uint256 public reserves;

    event FunctionPauseChanged(bytes4 indexed selector, bool paused);
    event Deposited(address indexed account, uint256 amount);
    event Borrowed(address indexed account, uint256 amount);
    event DonatedToReserves(address indexed account, uint256 amount);
    event Repaid(address indexed account, uint256 amount);
    event CollateralAdded(address indexed account, uint256 amount);

    modifier onlyGuardian() {
        require(msg.sender == guardian, "NOT_GUARDIAN");
        _;
    }

    modifier whenFunctionActive() {
        require(!functionPaused[msg.sig], "FUNCTION_PAUSED");
        _;
    }

    constructor(address asset_, address guardian_) {
        require(asset_ != address(0) && guardian_ != address(0), "ZERO_ADDRESS");
        asset = ITestToken(asset_);
        guardian = guardian_;
    }

    function setFunctionPaused(bytes4 selector, bool paused) external onlyGuardian {
        functionPaused[selector] = paused;
        emit FunctionPauseChanged(selector, paused);
    }

    function deposit(uint256 amount) external whenFunctionActive {
        require(asset.transferFrom(msg.sender, address(this), amount), "TRANSFER_FAILED");
        collateral[msg.sender] += amount;
        emit Deposited(msg.sender, amount);
    }

    function borrow(uint256 amount) external whenFunctionActive {
        debt[msg.sender] += amount;
        require(healthFactorBps(msg.sender) >= 10_000, "UNHEALTHY_BORROW");
        require(asset.transfer(msg.sender, amount), "TRANSFER_FAILED");
        emit Borrowed(msg.sender, amount);
    }

    function donateToReserves(uint256 amount) external whenFunctionActive {
        require(collateral[msg.sender] >= amount, "INSUFFICIENT_COLLATERAL");
        // Deliberate historical-pattern fixture: no health check after donation.
        collateral[msg.sender] -= amount;
        reserves += amount;
        emit DonatedToReserves(msg.sender, amount);
    }

    function repay(uint256 amount) external whenFunctionActive {
        uint256 paid = amount > debt[msg.sender] ? debt[msg.sender] : amount;
        require(asset.transferFrom(msg.sender, address(this), paid), "TRANSFER_FAILED");
        debt[msg.sender] -= paid;
        emit Repaid(msg.sender, paid);
    }

    function addCollateral(uint256 amount) external whenFunctionActive {
        require(asset.transferFrom(msg.sender, address(this), amount), "TRANSFER_FAILED");
        collateral[msg.sender] += amount;
        emit CollateralAdded(msg.sender, amount);
    }

    function withdraw(uint256 amount) external whenFunctionActive {
        require(collateral[msg.sender] >= amount, "INSUFFICIENT_COLLATERAL");
        collateral[msg.sender] -= amount;
        require(debt[msg.sender] == 0 || healthFactorBps(msg.sender) >= 10_000, "UNHEALTHY_WITHDRAW");
        require(asset.transfer(msg.sender, amount), "TRANSFER_FAILED");
    }

    function healthFactorBps(address account) public view returns (uint256) {
        uint256 accountDebt = debt[account];
        if (accountDebt == 0) return type(uint256).max;
        return collateral[account] * LIQUIDATION_THRESHOLD_BPS / accountDebt;
    }
}
