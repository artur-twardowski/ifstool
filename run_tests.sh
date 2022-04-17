#!/bin/sh

coverage run --branch -m unittest -v
coverage report -m
coverage html

