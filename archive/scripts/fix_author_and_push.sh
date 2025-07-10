#!/bin/bash
git config user.email "nerolation@users.noreply.github.com"
git config user.name "nerolation"
git commit --amend --reset-author --no-edit
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519 -o StrictHostKeyChecking=no" git push -u origin main