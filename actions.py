"""Um único marcador final; payload estrito; nunca executar tags inválidas."""
import json
import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

from business import KINDS

Text = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=1200)]
Preference = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, max_length=500)]
BookingText = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=300)]


class RequestAction(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    tipo: Literal['agendamento', 'reserva', 'encomenda', 'orcamento']
    nome: Text
    descricao: Text
    preferencia: Preference = ''

    @model_validator(mode='after')
    def date_required(self):
        if self.tipo in ('agendamento', 'reserva') and not self.preferencia:
            raise ValueError('Data/preferência obrigatória')
        return self


class BookingAction(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    nome: BookingText
    servico: BookingText
    data_hora: BookingText


def unique_object(pairs):
    data = {}
    for key, value in pairs:
        if key in data:
            raise ValueError('Chave JSON duplicada')
        data[key] = value
    return data


def parse_response(raw, operations):
    fallback = {'reply': 'A nossa equipa dará continuidade ao atendimento.', 'human': True, 'action': None, 'invalid_action': True}
    markers = list(re.finditer(r'\[[^\]\r\n]*\]', raw))
    if not markers:
        if '[' in raw or ']' in raw:
            return fallback
        return {'reply': raw.strip() or fallback['reply'], 'human': False, 'action': None}
    if len(markers) != 1:
        return fallback
    marker = markers[0]
    clean, tail = raw[:marker.start()].strip(), raw[marker.end():].strip()
    if not clean or '[' in clean or ']' in clean:
        return fallback
    tag = marker.group()
    if tag == '[HUMANO]' and not tail:
        return {'reply': clean, 'human': True, 'action': None}
    try:
        data = json.loads(tail, object_pairs_hook=unique_object)
        if tag == '[SOLICITACAO]':
            action = RequestAction.model_validate(data)
            if not operations.get(KINDS[action.tipo]):
                return fallback
        elif tag == '[AGENDAMENTO]':
            action = BookingAction.model_validate(data)
            if not operations.get('agendamentos'):
                return fallback
        else:
            return fallback
    except (ValueError, TypeError):
        return fallback
    return {'reply': clean, 'human': False, 'action': {'tag': tag, 'data': action.model_dump()}}
