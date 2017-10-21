# coding: utf-8
from six.moves import input
import budou
import json

TESTCASES_PATH = 'test/cases.ndjson'
DELIMITER = '|'

def colorize(text, color='green'):
  ENDC = '\033[0m'
  colors = {
    'red': '\033[91m',
    'green': '\033[92m',
    'yellow': '\033[93m',
    'blue': '\033[94m',
  }
  return colors[color] + text + ENDC

def main():
  print('Hello, this is an interactive console to add test cases for Budou.')
  print('By following this instruction, new test case will be added and '
        'validated in the future updates.')
  print('Press Ctrl-C to exit.')
  parser = budou.authenticate()

  try:
    while True:
      source = input(
          colorize('Input a source sentence to process: ')).decode('utf-8')
      if not source:
        print(colorize('No test case was provided. Try again.', 'red'))
        continue
      if source == 'exit':
        print('Bye.')
        break
      source = source.strip()
      print('Your input: %s' % (source))
      result = parser.parse(source, use_cache=False, use_entity=False)
      print(colorize('Retrived chunks from current implementation:', 'blue'))
      print(DELIMITER.join([chunk['word'] for chunk in result['chunks']]))
      is_correct = ask_if_correct()
      if is_correct:
        words = [chunk['word'] for chunk in result['chunks']]
      else:
        words = ask_expectation(source)
      add_test_case(source, words, result['tokens'], result['language'])
  except KeyboardInterrupt:
    print('\nBye.')

def ask_if_correct():
  while True:
    response = input(colorize(
        'Is this result expected? Please enter `yes` if it is. (yes/no): '))
    if response in {'y', 'yes'}:
      print('Thanks. the test case will be added as is.\n\n')
      return True
    elif response in {'n', 'no'}:
      return False
    else:
      print('Please enter yes or no. (yes/no)')

def ask_expectation(source):
  print('Uh-oh. Please input the expected result by separating the sentence '
        'with slashes.')
  print('e.g. %s' % (
        DELIMITER.join([u'これは', u'Google ', u'Home と', u'猫です。'])))
  while True:
    response = input(colorize('Input expected result: ')).decode('utf-8')
    if not response:
      print(colorize('No input was provided. Try again.', 'red'))
      continue
    words = response.split(DELIMITER)
    if ''.join(words) != source:
      print(colorize(
        'The input has different words from source input. Please verify if '
        'your input matches with the source.', 'red'))
      continue

    print(colorize('Expected chunks:', 'blue'))
    for word in words:
      print('word: %s' % (word))
    print('Please enter `yes` if this is correct. Press enter `no` if you want '
          'to edit again.')
    while True:
      response = input(colorize('Correct?: '))
      if response in {'y', 'yes'}:
        return words
      elif response in {'n', 'no'}:
        break
      else:
        print('Please enter `yes` or `no`.')

def add_test_case(source, words, tokens, language):
  with open(TESTCASES_PATH) as f:
    cases = [json.loads(row) for row in f.readlines() if row.strip()]
  for case in cases:
    if case['sentence'] == source:
      print('The test case "%s" is already included.' % (source))
      print('Do you want to update the test case with the new configuration? '
            'Enter `yes` to update or `no` to cencel. (y/n)')
      while True:
        response = input(colorize('Update?: '))
      if response in {'y', 'yes'}:
        break
      elif response in {'n', 'no'}:
        return False
      else:
        print('Please enter `yes` or `no`.')
  with open(TESTCASES_PATH, 'a') as f:
    f.write(json.dumps({
      'sentence': source,
      'language': language,
      'tokens': tokens,
      'expected': words,
    }, ensure_ascii=False, sort_keys=True).encode('utf-8') + '\n')
  print('Thank you for submission. Your test case "%s" is added.\n\n' % (
      source))


if __name__ == '__main__':
  main()
