def get_annotations(service, text, language='', encoding='UTF32'):
  """Returns the list of annotations from the given text."""
  body = {
      'document': {
          'type': 'PLAIN_TEXT',
          'content': text,
      },
      'features': {
          'extract_syntax': True,
      },
      'encodingType': encoding,
  }

  if language:
    body['document']['language'] = language

  request = service.documents().annotateText(body=body)
  response = request.execute()
  return response.get('tokens', [])

def get_entities(service, text, language='', encoding='UTF32'):
  """Returns the list of annotations from the given text."""
  body = {
      'document': {
          'type': 'PLAIN_TEXT',
          'content': text,
      },
      'encodingType': encoding,
  }

  if language:
    body['document']['language'] = language

  request = service.documents().analyzeEntities(body=body)
  response = request.execute()
  result = []
  for entity in response.get('entities', []):
    mentions = entity.get('mentions', [])
    if not mentions: continue
    entity_text = mentions[0]['text']
    offset = entity_text['beginOffset']
    for word in entity_text['content'].split():
      result.append({'content': word, 'beginOffset': offset})
      offset += len(word)
  return result
