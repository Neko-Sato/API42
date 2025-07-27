#!/bin/python3
import re
import argparse
import os

HEADER_PATTERN = re.compile(r'^\s*[#/*\-=\\]{5,}\s*$')
TARGET_EXTENSIONS = {'.c', '.h', '.cpp', '.hpp'}
MAKEFILE_NAMES = {'makefile', 'Makefile'}

def checker(file_path: str, allowed: set[str]):
  try:
    try:
      with open(file_path, 'r', encoding='utf-8') as f:
        header_lines = [f.readline() for _ in range(20)]
        header_text = ''.join(header_lines)
    except:
      raise RuntimeError('Failed to read')
    if HEADER_PATTERN.match(header_lines[0]):
      raise RuntimeError('Header not found')
    msg = []
    by_match = re.search(r'By:\s*([\w]+)', header_text)
    if by_match:
      by = by_match.group(1)
      if by not in allowed:
        msg.append(f'Unauthorized By: {by}')
    else:
      raise RuntimeError(f'By: not found')
    created_match = re.search(r'Created:.*by\s+([\w]+)', header_text)
    if created_match:
      created_by = created_match.group(1)
      if created_by not in allowed:
        msg.append(f'Unauthorized created: {created_by}')
    else:
      raise RuntimeError('Created by not found')
    updated_match = re.search(r'Updated:.*by\s+([\w]+)', header_text)  
    if updated_match:
      updated_by = updated_match.group(1)
      if updated_by not in allowed:
        msg.append(f'Unauthorized updated: {updated_by}')
    else:
      raise RuntimeError('Updated by not found')
  except RuntimeError as e:
    print(f'{file_path}: {e}')
    return False
  else:
    if msg:
      print(f"{file_path}: Error")
      for m in msg:
        print(m)
      return False
    else:
      print(f"{file_path}: OK")
      return True

def main(allowed: set[str], pathes: list[str]) -> int:
  success = True
  for path in pathes:
    if os.path.isfile(path):
      if not checker(path, allowed):
        success = False
    elif os.path.isdir(path):
      for root, _, files in os.walk(path):
        for file in files:
          if os.path.splitext(file)[1] in TARGET_EXTENSIONS or file in MAKEFILE_NAMES:
            if not checker(os.path.join(root, file), allowed):
              success = False
    else:
      print(f'{path}: No such file or directory')
      success = False
  return 0 if success else 1

if __name__ == "__main__":
  import argparse

  parser = argparse.ArgumentParser()
  parser.add_argument('path', nargs='*', type=str, default=["."])
  parser.add_argument('-u', '--login', nargs='+', type=str, default=[])
  args = parser.parse_args()
  exit(main(set(args.login), args.path))