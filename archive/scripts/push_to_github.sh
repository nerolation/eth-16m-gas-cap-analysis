#!/bin/bash
git remote set-url origin git@github.com:nerolation/eth-16m-gas-cap-analysis.git
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519 -o StrictHostKeyChecking=no" git push -u origin main