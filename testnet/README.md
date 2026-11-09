# Sepolia validation

This directory validates the narrow on-chain claim made by MinPause: a guardian can
pause the operation selected by the hitting-set policy while leaving borrower
recovery operations callable.

The fixture deliberately models the missing post-action health check associated
with the historical Euler `donateToReserves` pattern. It uses a mock token and no
real funds. It is **not** a replay of Euler's production contracts or historical
state.

## What the experiment proves

1. Without intervention, `donateToReserves` can move the controlled position below
   the liquidation threshold.
2. Pausing only the `donateToReserves(uint256)` selector makes that call revert.
3. `repay(uint256)` and `addCollateral(uint256)` remain callable.
4. The protected position can return to a healthy state.

## Local deterministic test

```bash
cd testnet
npm ci
npm test
```

## Sepolia deployment

Do not paste a private key into source code or chat. Configure these repository
secrets in GitHub:

- `SEPOLIA_RPC_URL`
- `SEPOLIA_DEPLOYER_KEY`

The deployer account must contain enough Sepolia ETH for deployment. The public
testnet script uses that same controlled account as guardian and borrower so no
second secret is needed; the local test suite separately exercises role
separation. Then run the `Sepolia validation` workflow manually. The workflow uploads
`sepolia-validation-evidence`, containing contract addresses, transaction hashes,
block numbers, selectors, and assertion results.

The testnet result supports deployability and function-level enforcement. A
historical claim about Euler still requires a mainnet fork at block 16,817,996.
