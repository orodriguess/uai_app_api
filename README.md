# 🥫 UAI API — Use Antes que Acabe

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-OpenAPI3-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-database-07405E?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/uso-acad%C3%AAmico-blue)](#)

API REST em **Flask + flask-openapi3** que mantém o **saldo de estoque de
itens de consumo pessoal** (alimentos e produtos de higiene/limpeza) e prevê
**quando cada um vai acabar**, a partir das compras registradas e de uma taxa
de consumo que a pessoa ajusta por tipo de produto. Faz parte do MVP da
disciplina **Desenvolvimento Full Stack Básico** da PUC-Rio.

> Chega de descobrir que o café acabou só na hora do café. O UAI calcula a
> data prevista de término de cada item e avisa quando ela está próxima.

---

## 📑 Sumário

- [Visão geral](#-visão-geral)
- [Arquitetura e stack](#-arquitetura-e-stack)
- [Estrutura de pastas](#-estrutura-de-pastas)
- [Como executar](#-como-executar)
- [Documentação interativa (Swagger)](#-documentação-interativa-swagger)
- [Catálogo de tipos de produto](#-catálogo-de-tipos-de-produto)
- [Rotas da API](#-rotas-da-api)
- [Regras de negócio](#-regras-de-negócio)
- [Tratamento de erros](#-tratamento-de-erros)
- [Projeto irmão (front-end)](#-projeto-irmão-front-end)

---

## 🔎 Visão geral

O sistema mantém três conjuntos de dados:

1. **Catálogo fixo** com 21 tipos de produto (alimentos, higiene e limpeza),
   cada um com unidade de medida, consumo **padrão de partida** (por dia,
   semana ou mês)
   e sugestões de descrição/quantidade — usado para agilizar o cadastro no
   front-end.
2. **Taxa de consumo por tipo**, na forma em que a pessoa a informa: uma
   quantidade consumida ao longo de um período (por dia, semana ou mês). A
   taxa diária é sempre derivada de `quantidade / periodo_dias`, nunca
   gravada pronta, para que "30 g de pasta de dente por semana" continue
   legível como foi digitado.
3. **Livro de eventos por tipo** (compra, alteração de taxa e conferência de
   saldo), persistido em SQLite. Cada evento congela o saldo apurado naquele
   instante.

O saldo de um tipo nunca é um número solto: ele nasce do livro. As compras de
um mesmo tipo **somam** em um saldo único, e o saldo de hoje é

```
saldo = saldo_congelado_no_último_evento − taxa_vigente × dias_desde_o_evento
```

com **piso em zero a cada trecho** — de modo que dias sem estoque não viram
dívida descontada da próxima compra. A data prevista de término e os dias
restantes saem daí, calculados sob demanda, sem persistir valores derivados
desatualizados.

Como a alteração de taxa é um evento datado que congela o saldo, ela **não
reescreve o consumo passado**: a taxa nova incide apenas sobre o estoque
restante.

## 🏗 Arquitetura e stack

| Camada | Tecnologia | Papel |
| --- | --- | --- |
| API / rotas | [Flask](https://flask.palletsprojects.com/) + [flask-openapi3](https://luolingchun.github.io/flask-openapi3/) | Roteamento, validação de request/response e geração automática do OpenAPI |
| Validação de dados | [Pydantic](https://docs.pydantic.dev/) | Schemas de entrada/saída (`schemas/`) |
| Persistência | [SQLAlchemy](https://www.sqlalchemy.org/) + SQLite | ORM e armazenamento em `database/db.sqlite3` |
| CORS | [Flask-Cors](https://flask-cors.readthedocs.io/) | Libera o consumo da API a partir do front-end aberto via `file://` |
| Logs | módulo próprio `logger.py` | Log rotativo em `log/` para depuração e auditoria |

O código segue uma separação em camadas inspirada no padrão MVC:

- **`model/`** — entidades de domínio e acesso a dados (SQLAlchemy).
- **`schemas/`** — contratos de entrada/saída da API (Pydantic), incluindo a
  transformação de entidades do modelo em respostas JSON.
- **`app.py`** — camada de rotas/controladores, orquestrando validação,
  regras de negócio simples e chamadas ao modelo.

## 📂 Estrutura de pastas

```
uai_app_api/
├── app.py                 # rotas da API e ponto de entrada Flask
├── logger.py              # configuração de logging
├── requirements.txt       # dependências do projeto
├── database/
│   └── db.sqlite3         # banco SQLite (criado automaticamente)
├── model/
│   ├── __init__.py        # engine, Session e criação das tabelas
│   ├── base.py            # Base declarativa do SQLAlchemy
│   ├── catalogo.py        # catálogo fixo dos 21 tipos de produto
│   ├── taxa_consumo.py    # entidade TaxaConsumo (quantidade por período)
│   ├── evento_estoque.py  # entidade EventoEstoque (livro por tipo)
│   ├── estoque.py         # apuração do livro, saldo, nível e conferência
│   └── exemplos.py        # dados de demonstração carregados na inicialização
├── schemas/
│   ├── __init__.py
│   ├── error.py           # schema padrão de erro
│   └── item.py            # schemas de tipos, itens e apresentação
└── log/                   # arquivos de log gerados em runtime
```

## 🚀 Como executar

Pré-requisitos: **Python 3.10+** e as bibliotecas listadas em
`requirements.txt`. Após clonar o repositório, abra um terminal no diretório
raiz do projeto.

> 💡 É fortemente recomendado o uso de um ambiente virtual, como o
> [virtualenv](https://virtualenv.pypa.io/en/latest/installation.html).

```bash
# 1. crie e ative o ambiente virtual (opcional, mas recomendado)
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/macOS

# 2. instale as dependências
(env)$ pip install -r requirements.txt

# 3. execute a API
(env)$ flask run --host 0.0.0.0 --port 5000
```

Em modo de desenvolvimento, use `--reload` para reiniciar o servidor
automaticamente a cada alteração no código-fonte:

```bash
(env)$ flask run --host 0.0.0.0 --port 5000 --reload
```

A cada inicialização, a API **apaga e recria** as tabelas `evento_estoque`
e `taxa_consumo` em `database/db.sqlite3` e carrega uma despensa de
demonstração (definida em `model/exemplos.py`), sem necessidade de migrações
manuais. As datas dos exemplos são relativas ao dia em que a API sobe, então
a despensa sempre mostra potes cheios, pela metade, perto do fim, vazios e
pedindo conferência, além de um tipo com taxa ajustada e outro já conferido.

> ⚠️ Tudo o que for cadastrado é perdido ao reiniciar a API — inclusive a
> cada reinício automático do modo `--reload`.

O front-end (projeto separado `uai_app_front`) consome esta API em
`http://127.0.0.1:5000`; o CORS já está habilitado para permitir o acesso a
partir do `index.html` aberto diretamente no navegador (`file://`).

## 📘 Documentação interativa (Swagger)

Com a API em execução, abra
[http://localhost:5000/openapi](http://localhost:5000/openapi) no navegador
e acesse o **Swagger UI**, gerado automaticamente pelo `flask-openapi3`,
para testar as rotas diretamente pelo navegador.

Para cada rota, a documentação mostra descrição, método HTTP, schema de
requisição/resposta e códigos de status possíveis.

## 🗂 Catálogo de tipos de produto

O catálogo é fixo (definido em `model/catalogo.py`) e cobre **21 tipos**,
divididos em alimentos e itens de higiene/limpeza — cada um com sua unidade
e consumo padrão (por dia, semana ou mês), usado como estimativa inicial:

<details>
<summary>Ver os 21 tipos suportados</summary>

| Tipo | Unidade | Consumo padrão | Quantidade sugerida |
| --- | --- | --- | --- |
| Café | g | 450 g por mês | 500 g |
| Pão | unidade | 2 un por dia | 10 un |
| Iogurte | unidade | 1 un por dia | 6 un |
| Ovo | unidade | 2 un por dia | 12 un |
| Arroz | kg | 1 kg por semana | 5 kg |
| Feijão | g | 100 g por dia | 1000 g |
| Carne vermelha | g | 1000 g por semana | 1000 g |
| Frango | g | 1000 g por semana | 1000 g |
| Frutas | unidade | 2 un por dia | 7 un |
| Granola | g | 40 g por dia | 500 g |
| Pão de queijo | unidade | 3 un por dia | 20 un |
| Goiabada | g | 500 g por mês | 500 g |
| Pasta de dente | g | 120 g por mês | 90 g |
| Papel higiênico | unidade | 3 un por semana | 12 un |
| Escova de dente | unidade | 0,33 un por mês | 1 un |
| Fio dental | m | 15 m por mês | 50 m |
| Shampoo | ml | 300 ml por mês | 350 ml |
| Sabonete | unidade | 1 un por semana | 6 un |
| Detergente | ml | 500 ml por mês | 500 ml |
| Sabão para roupas | ml | 1000 ml por mês | 1000 ml |
| Amaciante | ml | 500 ml por mês | 1000 ml |

</details>

O consumo padrão do catálogo é apenas o **ponto de partida**: vale enquanto a
pessoa não definir a sua. A partir do momento em que ela informa o próprio
consumo (via `PUT /taxas`) ou confere um saldo, a taxa passa a ser a dela — e
é **única por tipo**, não mais por compra.

## 🛣 Rotas da API

| Método | Rota | Descrição |
| --- | --- | --- |
| GET | `/` | Redireciona para `/openapi` |
| GET | `/tipos-produtos` | Lista os 21 tipos do catálogo, com unidade e sugestões de descrição/quantidade |
| GET | `/despensa` | Lista a despensa, um registro por tipo, com saldo, nível de enchimento e previsão |
| POST | `/item` | Registra uma compra, somando ao saldo do tipo |
| GET | `/itens?tipo=<tipo>` | Lista as compras registradas de um tipo (para corrigir um registro equivocado) |
| PUT | `/item/<id>` | Corrige quantidade, data ou descrição de uma compra e reapura o saldo do tipo |
| DELETE | `/item/<id>` | Remove uma compra e reapura o saldo do tipo |
| PUT | `/taxas` | Altera a taxa de consumo de vários tipos de uma vez |
| POST | `/tipo/<tipo>/conferencia` | Registra o saldo real de um tipo e recalibra a taxa |

### GET `/tipos-produtos`

Resposta (`200`):

```json
{
  "tipos": [
    {
      "tipo": "Café",
      "unidade": "g",
      "descricao_sugerida": "Cafezim é bão dimais, sô",
      "quantidade_sugerida": 500
    }
  ]
}
```

### GET `/despensa`

Um registro por tipo já registrado, ordenado pelo término mais próximo.
Resposta (`200`):

```json
{
  "tipos": [
    {
      "tipo": "Café",
      "descricao": "Café da manhã",
      "saldo": 500.0,
      "unidade": "g",
      "nivel": 1.0,
      "data_prevista": "2026-10-23",
      "dias_restantes": 33,
      "consumo_mensal": 450.0,
      "taxa_quantidade": 450.0,
      "taxa_periodo_dias": 30,
      "pendente_conferencia": false
    }
  ]
}
```

`nivel` é a razão entre o saldo e o consumo de um mês, limitada a `1.0` — é o
quanto o pote aparece cheio no front-end. `pendente_conferencia` fica `true`
quando o saldo chega a 20% ou menos do consumo mensal.

### GET `/itens?tipo=<tipo>`

Resposta (`200`):

```json
{
  "itens": [
    {
      "id": 1,
      "tipo": "Café",
      "quantidade_comprada": 500.0,
      "unidade": "g",
      "data_compra": "2026-09-20",
      "descricao": "Café da manhã"
    }
  ]
}
```

### POST `/item` — registrar uma compra

```
POST /item
Content-Type: application/json

{
  "tipo": "Café",
  "quantidade_comprada": 500,
  "descricao": "Café da manhã"
}
```

Resposta (`200`): a situação atualizada do tipo, no mesmo formato de um item
de `/despensa`.

`data_compra` é opcional — se omitida, assume a data atual. `unidade` vem do
catálogo, e a taxa aplicada é a vigente do tipo. Comprar de novo um tipo que
já tem saldo **soma**: 3 kg mais 5 kg viram 8 kg no mesmo pote.

### PUT `/item/<id>` — corrigir uma compra

```
PUT /item/1
Content-Type: application/json

{
  "quantidade_comprada": 5,
  "data_compra": "2026-09-20",
  "descricao": "Arroz branco tipo 1"
}
```

Aplica as mesmas validações do cadastro (quantidade maior que zero, data não
futura). O **tipo não é alterável**: uma compra do tipo errado deve ser
removida e registrada de novo. Resposta (`200`): a situação atualizada do tipo.

### DELETE `/item/<id>` — remover uma compra equivocada

Resposta (`200`):

```json
{
  "mensagem": "Compra removida",
  "id": 1
}
```

O livro do tipo é reapurado, de modo que o saldo passa a desconsiderar a
quantidade removida.

### PUT `/taxas` — alterar o consumo de vários tipos

```
PUT /taxas
Content-Type: application/json

{
  "taxas": [
    { "tipo": "Arroz", "quantidade": 2, "periodo_dias": 7 },
    { "tipo": "Pasta de dente", "quantidade": 30, "periodo_dias": 7 }
  ]
}
```

`periodo_dias` aceita `1` (por dia), `7` (por semana) ou `30` (por mês). A
validação é **atômica**: um único valor inválido rejeita o lote inteiro sem
gravar nada. Só é registrado evento de alteração para os tipos cuja taxa
efetivamente mudou.

Resposta (`200`): a situação atualizada apenas dos tipos alterados.

### POST `/tipo/<tipo>/conferencia` — conferir o saldo real

```
POST /tipo/Arroz/conferencia
Content-Type: application/json

{
  "quantidade": 0.5
}
```

A conferência substitui o saldo apurado pela quantidade informada e
**recalibra a taxa** a partir do consumo real observado desde o evento
anterior: se o evento anterior congelou 2 kg há 10 dias e sobrou 0,5 kg, o
consumo real foi de 0,15 kg por dia. A taxa nova é gravada no período que o
tipo já usa — para o Arroz, medido por semana, ela passa a 1,05 kg por
semana. Quando não há consumo observável — nenhum dia
decorrido, ou saldo maior que o previsto — a taxa vigente é preservada e só o
saldo é corrigido.

Resposta (`200`): a situação atualizada do tipo.

## ⚖️ Regras de negócio

- Compras do mesmo tipo somam em um **saldo único** por tipo.
- `saldo = saldo_congelado_no_último_evento − taxa_vigente × dias_decorridos`,
  com **piso em zero a cada trecho** do livro: dias sem estoque não descontam
  da compra seguinte.
- `dias_restantes` é a parte inteira de `saldo / taxa_diária`; `data_prevista = hoje + dias_restantes`.
- `nivel = min(1, saldo / (taxa_diária × 30))`.
- A taxa é **única por tipo** e guardada como `quantidade` e `periodo_dias`
  (1, 7 ou 30), nunca como taxa diária pronta; a taxa diária é derivada de
  `quantidade / periodo_dias`.
- Alterar a taxa congela o saldo apurado até ali: a taxa nova incide apenas
  sobre o estoque restante e **não reescreve o passado**.
- A conferência é pedida quando o saldo chega a 20% ou menos do consumo
  mensal, e deixa de ser pedida até uma nova compra levar o saldo acima
  desse limite.
- O `tipo` informado no cadastro deve existir no catálogo fixo.
- A `quantidade_comprada` deve ser maior que zero.
- A `data_compra` não pode ser uma data futura.

## 🚨 Tratamento de erros

Erros de validação e de regra de negócio retornam sempre o mesmo formato,
descrito por `ErrorSchema`:

```json
{
  "mensagem": "Quantidade comprada deve ser maior que zero :/"
}
```

| Código | Quando ocorre |
| --- | --- |
| `400` | Tipo inexistente no catálogo, quantidade inválida, data de compra futura, período fora de 1/7/30 dias ou quantidade negativa na conferência |
| `404` | Compra não encontrada (correção e remoção) ou tipo inexistente (conferência) |

Todas as validações de entrada (tipos, formatos, campos obrigatórios) são
feitas automaticamente pelo Pydantic antes mesmo de chegar à lógica da
rota, retornando `422` com o detalhamento do campo inválido.

## 🔗 Projeto irmão (front-end)

O consumo desta API é feito pelo SPA estático do projeto `uai_app_front`,
mantido em repositório próprio, que também faz parte deste MVP e possui seu
próprio `README.md`.
