const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("MinPause function-level response", function () {
  async function deployFixture() {
    const [guardian, user] = await ethers.getSigners();
    const Token = await ethers.getContractFactory("MockERC20");
    const token = await Token.deploy();
    const Market = await ethers.getContractFactory("FunctionPausableMarket");
    const market = await Market.deploy(await token.getAddress(), guardian.address);
    const unit = 10n ** 18n;
    await token.mint(await market.getAddress(), 10_000n * unit);
    await token.mint(user.address, 2_000n * unit);
    await token.connect(user).approve(await market.getAddress(), ethers.MaxUint256);
    await market.connect(user).deposit(1_000n * unit);
    await market.connect(user).borrow(700n * unit);
    return { guardian, user, token, market, unit };
  }

  it("allows the unprotected donation to make the account unhealthy", async function () {
    const { user, market, unit } = await deployFixture();
    await market.connect(user).donateToReserves(800n * unit);
    expect(await market.healthFactorBps(user.address)).to.equal(2_285n);
  });

  it("blocks only donateToReserves and leaves both recovery calls live", async function () {
    const { guardian, user, market, unit } = await deployFixture();
    const selector = market.interface.getFunction("donateToReserves").selector;
    await market.connect(guardian).setFunctionPaused(selector, true);

    await expect(market.connect(user).donateToReserves(800n * unit))
      .to.be.revertedWith("FUNCTION_PAUSED");

    await market.connect(user).repay(100n * unit);
    await market.connect(user).addCollateral(100n * unit);
    expect(await market.debt(user.address)).to.equal(600n * unit);
    expect(await market.collateral(user.address)).to.equal(1_100n * unit);
    expect(await market.healthFactorBps(user.address)).to.equal(14_666n);
  });
});
