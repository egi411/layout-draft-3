#!/bin/sh
# Собирает index.html из draft.html
{
  printf '<!doctype html>\n<html lang="ru">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n<meta name="robots" content="noindex,nofollow">\n<style>body{margin:0}[hidden]{display:none!important}</style>\n</head>\n<body>\n'
  cat draft.html
  printf '\n</body>\n</html>\n'
} > index.html
