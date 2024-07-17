#!/bin/bash

# # Check if Bundler is installed
# if ! command -v bundle &> /dev/null
# then
#     echo "Bundler is not installed. Install Bundler first."
#     exit
# fi

# # Output the current directory
# echo "The current directory is:$(pwd)"

# # Install the necessary gem packages
# bundle install

# Start Jekyll local server
bundle exec jekyll serve
# bundle exec jekyll serve --drafts --incremental &