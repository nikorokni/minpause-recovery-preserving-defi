const fs = require("fs");
const path = require("path");
const { ethers, network } = require("hardhat");

async function confirmed(txPromise) {
  const tx = await txPromise;
  const receipt = await tx.wait();
  return { hash: tx.hash, blockNumber: receipt.blockNumber };
}

async function seedPosition(token, market, user, unit) {
  const marketAddress = await market.getAddress();
  const transactions = [];
  transactions.push(await confirmed(token.mint(marketAddress, 10_000n * unit)));
  transactions.push(await confirmed(token.mint(user.address, 2_000n * unit)));
  transactions.push(await confirmed(token.connect(user).approve(marketAddress, ethers.MaxUint256)));
  transactions.push(await confirmed(market.connect(user).deposit(1_000n * unit)));
  transactions.push(await confirmed(market.connect(user).borrow(700n * unit)));
  return transactions;
}

async function main() {
  const [guardian] = await ethers.getSigners();
  if (!guardian) throw new Error("A funded deployer signer is required");
  // The controlled test position deliberately uses the deployer account so the
  // public testnet run needs only one secret key. Role separation is exercised
  // by the deterministic Hardhat test suite.
  const user = guardian;

  const chain = await ethers.provider.getNetwork();
  if (chain.chainId !== 11155111n) throw new Error("Refusing to deploy outside Sepolia");

  const Token = await ethers.getContractFactory("MockERC20");
  const token = await Token.deploy();
  await token.waitForDeployment();
  const Market = await ethers.getContractFactory("FunctionPausableMarket");
  const baseline = await Market.deploy(await token.getAddress(), guardian.address);
  await baseline.waitForDeployment();
  const protectedMarket = await Market.deploy(await token.getAddress(), guardian.address);
  await protectedMarket.waitForDeployment();
  const unit = 10n ** 18n;

  const txs = {
    baselineSeed: await seedPosition(token, baseline, user, unit),
    protectedSeed: await seedPosition(token, protectedMarket, user, unit),
  };

  txs.baselineDonation = await confirmed(
    baseline.connect(user).donateToReserves(800n * unit)
  );
  const baselineHealthAfter = await baseline.healthFactorBps(user.address);

  const donateSelector = protectedMarket.interface.getFunction("donateToReserves").selector;
  txs.pause = await confirmed(protectedMarket.setFunctionPaused(donateSelector, true));
  let blockedDonationHash = null;
  let blockedDonationConfirmed = false;
  try {
    const blockedTx = await protectedMarket.connect(user).donateToReserves(800n * unit);
    blockedDonationHash = blockedTx.hash;
    await blockedTx.wait();
  } catch (error) {
    blockedDonationConfirmed = /FUNCTION_PAUSED|revert/i.test(String(error));
  }
  if (!blockedDonationConfirmed) throw new Error("Protected donation was not proven to revert");

  txs.repay = await confirmed(protectedMarket.connect(user).repay(100n * unit));
  txs.addCollateral = await confirmed(protectedMarket.connect(user).addCollateral(100n * unit));
  const protectedHealthAfterRecovery = await protectedMarket.healthFactorBps(user.address);

  const result = {
    schemaVersion: 1,
    network: network.name,
    chainId: chain.chainId.toString(),
    recordedAt: new Date().toISOString(),
    guardian: guardian.address,
    user: user.address,
    contracts: {
      token: await token.getAddress(),
      baselineMarket: await baseline.getAddress(),
      protectedMarket: await protectedMarket.getAddress(),
    },
    assertions: {
      unprotectedDonationCreatesUnhealthyPosition: baselineHealthAfter < 10_000n,
      donateToReservesBlocked: blockedDonationConfirmed,
      repayRemainsCallable: true,
      addCollateralRemainsCallable: true,
      protectedPositionHealthyAfterRecovery: protectedHealthAfterRecovery >= 10_000n,
    },
    measurements: {
      baselineHealthAfterDonationBps: baselineHealthAfter.toString(),
      protectedHealthAfterRecoveryBps: protectedHealthAfterRecovery.toString(),
      pausedSelector: donateSelector,
    },
    transactions: { ...txs, blockedDonationHash },
    scope: "Controlled Sepolia fixture; not a replay of historical Euler state.",
  };

  const outDir = path.join(__dirname, "..", "results");
  fs.mkdirSync(outDir, { recursive: true });
  const outPath = path.join(outDir, "sepolia-latest.json");
  fs.writeFileSync(outPath, JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
