#!/bin/bash
# This script is used to run GitHub Actions locally using act to build and test pull request builds.
act pull_request --job build-pr --artifact-server-path ./build -P ubuntu-latest=ubuntu:latest -P windows-latest=windows:latest -P macos-latest=ubuntu:latest --verbose