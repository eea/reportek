#!/usr/bin/env bash

rm -f docs/api/*
sphinx-apidoc -o docs/api reportek reportek/core/migrations
