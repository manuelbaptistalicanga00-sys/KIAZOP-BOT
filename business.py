"""Perfis de negócio validados; um negócio ativo por instalação."""
import unicodedata
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Short = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
Detail = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1200)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Operations(StrictModel):
    agendamentos: bool = True
    reservas: bool = False
    encomendas: bool = False
    orcamentos: bool = True


class Information(StrictModel):
    morada: str = Field(default='', max_length=500)
    horario: str = Field(default='', max_length=500)
    contacto: str = Field(default='', max_length=500)
    servicos: dict[Short, Detail] = Field(default_factory=dict, max_length=100)
    produtos: dict[Short, Detail] = Field(default_factory=dict, max_length=100)
    pagamento: str = Field(default='', max_length=1200)
    entrega: str = Field(default='', max_length=1200)
    politicas: str = Field(default='', max_length=2400)
    perguntas_frequentes: dict[Short, Detail] = Field(default_factory=dict, max_length=100)


class BusinessProfile(StrictModel):
    nome: Short
    setor: Short = 'Geral'
    tom: Short = 'simpático, profissional e direto'
    informacoes: Information = Field(default_factory=Information)
    operacoes: Operations = Field(default_factory=Operations)
    extra: str = Field(default='', max_length=2400)


KINDS = {'agendamento': 'agendamentos', 'reserva': 'reservas', 'encomenda': 'encomendas', 'orcamento': 'orcamentos'}
LABELS = {'agendamento': 'agendamento', 'reserva': 'reserva', 'encomenda': 'encomenda', 'orcamento': 'orçamento'}


def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', text.casefold()) if not unicodedata.combining(c))


def templates():
    """Estruturas sem preços, horários ou condições fictícias."""
    sectors = [
        ('geral', 'Geral / personalizado', ['agendamentos', 'reservas', 'encomendas', 'orcamentos']),
        ('loja', 'Loja / comércio', ['encomendas', 'orcamentos']),
        ('restaurante', 'Restaurante / café', ['reservas', 'encomendas']),
        ('beleza', 'Salão / barbearia / beleza', ['agendamentos', 'orcamentos']),
        ('oficina', 'Oficina / assistência técnica', ['agendamentos', 'orcamentos']),
        ('servicos', 'Serviços / consultoria', ['agendamentos', 'orcamentos']),
        ('ensino', 'Escola / formação', ['agendamentos', 'orcamentos']),
        ('alojamento', 'Hotel / alojamento', ['reservas', 'orcamentos']),
        ('saude', 'Saúde / clínica', ['agendamentos']),
    ]
    return [{'id': key, 'label': label, 'profile': BusinessProfile(
        nome='O meu negócio', setor=label,
        operacoes=Operations(**{k: k in enabled for k in Operations.model_fields}),
    ).model_dump()} for key, label, enabled in sectors]
