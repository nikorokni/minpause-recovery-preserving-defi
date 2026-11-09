require("@nomicfoundation/hardhat-toolbox");

const rpcUrl = process.env.SEPOLIA_RPC_URL || "http://127.0.0.1:8545";
const deployerKey = process.env.SEPOLIA_DEPLOYER_KEY;

module.exports = {
  solidity: {
    version: "0.8.24",
    settings: { optimizer: { enabled: true, runs: 200 } },
  },
  networks: {
    sepolia: {
      url: rpcUrl,
      chainId: 11155111,
      accounts: deployerKey ? [deployerKey] : [],
    },
  },
};
